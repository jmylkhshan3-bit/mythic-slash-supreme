/**
 * Trims the input waveform by removing silence at the beginning and end.
 *
 * This function uses a sliding window algorithm. The waveform is divided into fixed-size windows (256 samples),
 * and the average absolute amplitude of each window is computed. A dynamic threshold is then set at 5% of the
 * maximum window amplitude. The function finds the first and last samples that exceed this threshold and returns
 * the waveform between these two points, adding a buffer margin to ensure that actual audio is not cut off.
 *
 * @param waveform - The input waveform as a Float32Array.
 * @returns A new Float32Array containing the trimmed waveform with a buffer margin.
 */
export function trimWaveform(waveform: Float32Array): Float32Array {
  const windowSize = 256;
  const bufferSamples = 256;
  const numWindows = Math.ceil(waveform.length / windowSize);
  const windowAmplitudes = new Float32Array(numWindows);
  let maxWindowAmp = 0;

  // Compute average amplitude for each window and track the maximum value.
  for (let i = 0; i < numWindows; i++) {
    const start = i * windowSize;
    const end = Math.min(start + windowSize, waveform.length);
    let sum = 0;
    for (let j = start; j < end; j++) {
      sum += Math.abs(waveform[j]);
    }
    const avg = sum / (end - start);
    windowAmplitudes[i] = avg;
    if (avg > maxWindowAmp) maxWindowAmp = avg;
  }

  // Define the dynamic threshold as 5% of the maximum window amplitude.
  const threshold = maxWindowAmp * 0.05;

  // Find the first sample index exceeding the threshold.
  let startSample = 0;
  for (let i = 0; i < numWindows; i++) {
    if (windowAmplitudes[i] > threshold) {
      const winStart = i * windowSize;
      const winEnd = Math.min(winStart + windowSize, waveform.length);
      for (let j = winStart; j < winEnd; j++) {
        if (Math.abs(waveform[j]) > threshold) {
          startSample = j;
          break;
        }
      }
      break;
    }
  }

  // Find the last sample index exceeding the threshold.
  let endSample = waveform.length;
  for (let i = numWindows - 1; i >= 0; i--) {
    if (windowAmplitudes[i] > threshold) {
      const winStart = i * windowSize;
      const winEnd = Math.min(winStart + windowSize, waveform.length);
      for (let j = winEnd - 1; j >= winStart; j--) {
        if (Math.abs(waveform[j]) > threshold) {
          endSample = j + 1;
          break;
        }
      }
      break;
    }
  }

  // Add buffer margin to avoid cutting actual audio.
  startSample = Math.max(0, startSample - bufferSamples);
  endSample = Math.min(waveform.length, endSample + bufferSamples);

  return waveform.slice(startSample, endSample);
}
