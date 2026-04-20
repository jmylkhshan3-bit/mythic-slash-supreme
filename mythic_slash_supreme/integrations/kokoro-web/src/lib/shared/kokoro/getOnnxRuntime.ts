import { browser } from "$app/environment";

import * as ortweb from "onnxruntime-web/webgpu";
// This should match the version of onnxruntime-web in the package.json
ortweb.env.wasm.wasmPaths =
  "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.21.0-dev.20250206-d981b153d3/dist/";

/**
 *  Returns the onnx runtime web or node depending on the environment.
 */
export async function getOnnxRuntime(): Promise<typeof ortweb> {
  if (browser) {
    return ortweb;
  }

  //@ts-ignore
  const ortnode = await import("onnxruntime-node");
  return ortnode;
}
