import { browser } from "$app/environment";
import { getClientFfmpeg } from "./getClientFfmpeg";

export async function wavToMp3(wavBuffer: ArrayBuffer): Promise<ArrayBuffer> {
  return browser ? wavToMp3Client(wavBuffer) : wavToMp3Server(wavBuffer);
}

async function wavToMp3Client(wavBuffer: ArrayBuffer): Promise<ArrayBuffer> {
  const ffmpeg = await getClientFfmpeg();
  const inputName = `input-${crypto.randomUUID()}.wav`;
  const outputName = `output-${crypto.randomUUID()}.mp3`;

  ffmpeg.writeFile(inputName, new Uint8Array(wavBuffer));
  await ffmpeg.exec(["-i", inputName, "-b:a", "192k", outputName]);

  const data = await ffmpeg.readFile(outputName, "binary");
  if (typeof data === "string") throw new Error("Expected binary data");

  return data.buffer as ArrayBuffer;
}

async function wavToMp3Server(wavBuffer: ArrayBuffer): Promise<ArrayBuffer> {
  const fs = await import("fs/promises");
  const path = await import("path");
  const os = await import("os");
  const ffmpeg = (await import("fluent-ffmpeg")).default;

  const tmpDir = os.tmpdir();
  const inputPath = path.join(tmpDir, `input-${crypto.randomUUID()}.wav`);
  const outputPath = path.join(tmpDir, `output-${crypto.randomUUID()}.mp3`);

  await fs.writeFile(inputPath, Buffer.from(wavBuffer));

  await new Promise<void>((resolve, reject) => {
    ffmpeg(inputPath)
      .audioBitrate("192k")
      .output(outputPath)
      .on("end", () => resolve())
      .on("error", (err) => reject(err))
      .run();
  });

  const data = await fs.readFile(outputPath);

  // Cleanup temp files
  fs.unlink(inputPath).catch(() => {});
  fs.unlink(outputPath).catch(() => {});

  return new Uint8Array(data).buffer;
}
