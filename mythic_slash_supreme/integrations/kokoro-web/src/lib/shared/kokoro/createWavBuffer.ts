import { browser } from "$app/environment";
import * as wavefileclient from "wavefile";

/**
 * Importing wavefile from server and client is different, so we need
 * this wrapper to handle the differences.
 */

/**
 * Create a WAV buffer from a waveform array.
 */
export function createWavBuffer(
  waveform: Float32Array<ArrayBuffer>,
  sampleRate: number,
): Promise<ArrayBuffer> {
  return browser
    ? createWavBufferClient(waveform, sampleRate)
    : createWavBufferServer(waveform, sampleRate);
}

function createWavBufferClient(
  waveform: Float32Array<ArrayBuffer>,
  sampleRate: number,
): Promise<ArrayBuffer> {
  let wav = new wavefileclient.WaveFile();
  wav.fromScratch(1, sampleRate, "32f", waveform);

  return new Promise((resolve) => {
    resolve(wav.toBuffer().buffer as ArrayBuffer);
  });
}

async function createWavBufferServer(
  waveform: Float32Array<ArrayBuffer>,
  sampleRate: number,
): Promise<ArrayBuffer> {
  const { default: wavefileserver } = await import("wavefile");

  let wav = new wavefileserver.WaveFile();
  wav.fromScratch(1, sampleRate, "32f", waveform);

  return wav.toBuffer().buffer as ArrayBuffer;
}
