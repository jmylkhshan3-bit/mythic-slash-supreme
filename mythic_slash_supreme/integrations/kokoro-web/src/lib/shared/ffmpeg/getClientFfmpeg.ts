import { FFmpeg } from "@ffmpeg/ffmpeg";
import { toBlobURL } from "@ffmpeg/util";

let clientFfmpeg: FFmpeg | undefined;
let clientFfmpegLoaded = false;

export async function getClientFfmpeg(): Promise<FFmpeg> {
  if (!clientFfmpeg) clientFfmpeg = new FFmpeg();
  if (!clientFfmpegLoaded) {
    const baseURL = "https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.6/dist/esm";
    const js = `${baseURL}/ffmpeg-core.js`;
    const wasm = `${baseURL}/ffmpeg-core.wasm`;

    await clientFfmpeg.load({
      coreURL: await toBlobURL(js, "text/javascript"),
      wasmURL: await toBlobURL(wasm, "application/wasm"),
    });
    clientFfmpegLoaded = true;
  }

  return clientFfmpeg;
}
