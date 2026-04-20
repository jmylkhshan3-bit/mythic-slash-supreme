import { browser } from "$app/environment";
import { toaster } from "$lib/client/toaster";

/**
 * Fetches a file from the given url, caching it if possible.
 *
 * @param url The url to be fetched
 */
export async function getFileFromUrl(url: string): Promise<ArrayBuffer> {
  console.log("Downloading URL:", url);
  return browser ? getFileFromUrlClient(url) : getFileFromUrlServer(url);
}

async function getFileFromUrlClient(url: string): Promise<ArrayBuffer> {
  const fileName = url.split("/").pop()?.split("?")[0] || "file";
  let cache: Cache | null = null;

  try {
    cache = await caches.open("kokoro-web-resources");
    const cached = await cache.match(url);
    if (cached) {
      console.log("Downloaded from cache");
      return await cached.arrayBuffer();
    }
  } catch (err) {
    console.warn("Can't open cache:", err);
  }

  toaster.success(
    `Downloading ${fileName} (Will be downloaded once and saved for future use)`,
  );

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch: ${res.status}`);
  }

  const buf = await res.arrayBuffer();
  if (!cache) return buf;

  try {
    await cache.put(url, new Response(buf, { headers: res.headers }));
  } catch (err) {
    console.warn("Can't cache:", err);
  }

  console.log("Downloaded from network");
  return buf;
}

async function getFileFromUrlServer(url: string): Promise<ArrayBuffer> {
  const fs = await import("fs/promises");
  const path = await import("path");
  const crypto = await import("crypto");

  const cacheDir = "/kokoro/cache";
  const hash = crypto.createHash("md5").update(url).digest("hex");
  const filePath = path.join(cacheDir, hash);

  try {
    await fs.access(cacheDir);
  } catch {
    await fs.mkdir(cacheDir, { recursive: true });
  }
  try {
    const data = await fs.readFile(filePath);
    console.log("Downloaded from cache");
    return new Uint8Array(data).buffer;
  } catch {}

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch: ${res.status}`);
  }

  const buf = await res.arrayBuffer();
  await fs.writeFile(filePath, Buffer.from(buf));

  console.log("Downloaded from network");
  return buf;
}
