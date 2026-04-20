import { browser } from "$app/environment";
import { getClientFfmpeg } from "./getClientFfmpeg";
import { buildAtempoChain } from "./utils";

export async function modifyWavSpeed(
  wavBuffer: ArrayBuffer,
  velocity: number,
): Promise<ArrayBuffer> {
  if (velocity === 1) return wavBuffer;

  return browser
    ? modifyWavSpeedClient(wavBuffer, velocity)
    : modifyWavSpeedServer(wavBuffer, velocity);
}

async function modifyWavSpeedClient(
  wavBuffer: ArrayBuffer,
  velocity: number,
): Promise<ArrayBuffer> {
  const ffmpeg = await getClientFfmpeg();
  const inputName = `input-${crypto.randomUUID()}.wav`;
  const outputName = `output-${crypto.randomUUID()}.mp3`;

  ffmpeg.writeFile(inputName, new Uint8Array(wavBuffer));

  const filter = buildAtempoChain(velocity);
  await ffmpeg.exec(["-i", inputName, "-filter:a", filter, outputName]);

  const data = await ffmpeg.readFile(outputName, "binary");
  if (typeof data === "string") throw new Error("Se esperaba datos binarios");
  return data.buffer as ArrayBuffer;
}

async function modifyWavSpeedServer(
  wavBuffer: ArrayBuffer,
  velocity: number,
): Promise<ArrayBuffer> {
  const fs = await import("fs/promises");
  const path = await import("path");
  const os = await import("os");
  const ffmpeg = (await import("fluent-ffmpeg")).default;

  const tmpDir = os.tmpdir();
  const inputPath = path.join(tmpDir, `input-${crypto.randomUUID()}.wav`);
  const outputPath = path.join(tmpDir, `output-${crypto.randomUUID()}.wav`);

  await fs.writeFile(inputPath, Buffer.from(wavBuffer));

  const filter = buildAtempoChain(velocity);

  await new Promise<void>((resolve, reject) => {
    ffmpeg(inputPath)
      .output(outputPath)
      .noVideo()
      .audioFilters(filter)
      .on("end", () => resolve())
      .on("error", (err) => reject(err))
      .run();
  });

  const data = await fs.readFile(outputPath);
  fs.unlink(inputPath).catch(() => {});
  fs.unlink(outputPath).catch(() => {});

  return new Uint8Array(data).buffer;
}
