import { getModel } from "$lib/shared/resources";
import type { LangId, ModelId } from "$lib/shared/resources";
import { detectWebGPU } from "$lib/client/utils";
import { combineVoices } from "./combineVoices";
import { preprocessText, type TextProcessorChunk } from "./textProcessor";
import { trimWaveform } from "./trimWaveform";
import { getOnnxRuntime } from "./getOnnxRuntime";
import { modifyWavSpeed, wavToMp3 } from "../ffmpeg";
import { createWavBuffer } from "./createWavBuffer";
import { parseVoiceFormula } from "./voiceFormula";

const MODEL_CONTEXT_WINDOW = 512;
const SAMPLE_RATE = 24000; // sample rate in Hz

/**
 * Generates a voice from a given text.
 *
 * The raw text is preprocessed so that silence markers are detected before phonemization.
 * For text segments the phonemizer is called, then punctuation splitting and token generation are applied.
 * Silence chunks produce silent waveforms.
 *
 * The voice formula is parsed into an array of voice weights.
 *
 * @param params - Generation parameters.
 * @param params.text - The input text.
 * @param params.lang - The language ID (for phonemization).
 * @param params.voiceFormula - The voice formula.
 * @param params.model - The model ID.
 * @param params.speed - The speed factor.
 * @param params.format - The output format.
 * @param params.acceleration - "cpu" or "webgpu" to select acceleration.
 * @returns Concatenated waveform.
 */
export async function generateVoice(params: {
  text: string;
  lang: LangId | string;
  voiceFormula: string;
  model: ModelId | string;
  speed: number;
  format: "wav" | "mp3";
  acceleration: "cpu" | "webgpu";
}): Promise<{ buffer: ArrayBuffer; mimeType: string }> {
  if (params.acceleration === "webgpu" && !detectWebGPU()) {
    throw new Error("WebGPU is not supported in this environment");
  }
  if (params.speed < 0.1 || params.speed > 5) {
    throw new Error("Speed must be between 0.1 and 5");
  }

  const ort = await getOnnxRuntime();

  const tokensPerChunk = MODEL_CONTEXT_WINDOW - 2;
  const chunks: TextProcessorChunk[] = await preprocessText(
    params.text,
    params.lang,
    tokensPerChunk,
  );

  const modelBuffer = await getModel(params.model);
  const voices = parseVoiceFormula(params.voiceFormula);
  const combinedVoice = await combineVoices(voices);

  const session = await ort.InferenceSession.create(modelBuffer, {
    executionProviders: [params.acceleration],
  });

  const waveforms: Float32Array[] = [];
  let waveformsLen = 0;

  // Process each chunk based on its type.
  for (const chunk of chunks) {
    if (chunk.type === "silence") {
      console.log(chunk);

      const silenceLength = Math.floor(chunk.durationSeconds * SAMPLE_RATE);
      const silenceWave = new Float32Array(silenceLength);
      waveforms.push(silenceWave);
      waveformsLen += silenceLength;
    }

    if (chunk.type === "text") {
      const tokensLength = chunk.tokens?.length ?? 0;
      if (tokensLength < 1) {
        console.log("Skipping chunk with no tokens");
        continue;
      }

      console.log({ type: chunk.type, content: chunk.content });

      const tokens = chunk.tokens;
      const ref_s = combinedVoice[tokens.length - 1][0];
      const paddedTokens = [0, ...tokens, 0];
      const input_ids = new ort.Tensor("int64", paddedTokens, [
        1,
        paddedTokens.length,
      ]);
      const style = new ort.Tensor("float32", ref_s, [1, ref_s.length]);
      // Fixed speed because speed should be implemented as post-processing
      // instead of being a model input to get better results.
      const speed = new ort.Tensor("float32", [1], [1]);

      // Get the raw waveform and trim extra silence duration.
      const result = await session.run({ input_ids, style, speed });
      let waveform = (await result.waveform.getData()) as Float32Array;
      waveform = trimWaveform(waveform);

      waveforms.push(waveform);
      waveformsLen += waveform.length;
    }
  }

  if (waveforms.length === 0) {
    throw new Error("No waveforms generated");
  }

  const finalWaveform = new Float32Array(waveformsLen);
  let offset = 0;
  for (const waveform of waveforms) {
    finalWaveform.set(waveform, offset);
    offset += waveform.length;
  }

  let wavBuffer = await createWavBuffer(finalWaveform, SAMPLE_RATE);
  if (params.speed !== 1) {
    wavBuffer = await modifyWavSpeed(wavBuffer, params.speed);
  }

  if (params.format === "wav") {
    return { buffer: wavBuffer, mimeType: "audio/wav" };
  }

  return { buffer: await wavToMp3(wavBuffer), mimeType: "audio/mpeg" };
}
