/**
 * Detects if the browser supports WebGPU in a synchronous way.
 * This checks if both the WebGPU API and the requestAdapter function are available,
 * which is a good indication of WebGPU support without making async calls.
 */
export function detectWebGPU(): boolean {
  const nav = navigator as any;
  return !!nav.gpu && typeof nav.gpu.requestAdapter === "function";
}
