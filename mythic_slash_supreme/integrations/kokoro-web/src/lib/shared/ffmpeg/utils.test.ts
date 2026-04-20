import { describe, it, expect } from "vitest";
import { buildAtempoChain } from "./utils";

describe("buildAtempoChain", () => {
  it("returns 'atempo=1' for velocity = 1", () => {
    expect(buildAtempoChain(1)).toBe("atempo=1");
  });

  it("returns 'atempo=0.75' for velocity = 0.75", () => {
    expect(buildAtempoChain(0.75)).toBe("atempo=0.75");
  });

  it("returns 'atempo=0.5,atempo=0.5' for velocity = 0.25", () => {
    expect(buildAtempoChain(0.25)).toBe("atempo=0.5,atempo=0.5");
  });

  it("returns 'atempo=1.5' for velocity = 1.5", () => {
    expect(buildAtempoChain(1.5)).toBe("atempo=1.5");
  });

  it("returns 'atempo=2,atempo=2' for velocity = 4", () => {
    expect(buildAtempoChain(4)).toBe("atempo=2,atempo=2");
  });

  it("returns 'atempo=2,atempo=1.25' for velocity = 2.5", () => {
    expect(buildAtempoChain(2.5)).toBe("atempo=2,atempo=1.25");
  });

  it("returns 'atempo=2' for velocity = 2", () => {
    expect(buildAtempoChain(2)).toBe("atempo=2");
  });

  it("returns 'atempo=0.5,atempo=0.5,atempo=0.5,atempo=0.8' for velocity = 0.1", () => {
    expect(buildAtempoChain(0.1)).toBe(
      "atempo=0.5,atempo=0.5,atempo=0.5,atempo=0.8",
    );
  });

  it("returns 'atempo=0.5' for velocity = 0.5", () => {
    expect(buildAtempoChain(0.5)).toBe("atempo=0.5");
  });

  it("returns 'atempo=0.9' for velocity = 0.9", () => {
    expect(buildAtempoChain(0.9)).toBe("atempo=0.9");
  });

  it("returns 'atempo=2,atempo=1.5' for velocity = 3", () => {
    expect(buildAtempoChain(3)).toBe("atempo=2,atempo=1.5");
  });

  it("returns 'atempo=2,atempo=2,atempo=1.25' for velocity = 5", () => {
    expect(buildAtempoChain(5)).toBe("atempo=2,atempo=2,atempo=1.25");
  });
});
