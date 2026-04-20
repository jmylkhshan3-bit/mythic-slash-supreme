import { describe, it, expect } from "vitest";
import { parseVoiceFormula, serializeVoiceFormula } from "./voiceFormula";

describe("parseVoiceFormula", () => {
  it("should parse a valid formula with two voices", () => {
    const formula = "voice1*0.5 + voice2*0.5";
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([
      { voiceId: "voice1", weight: 0.5 },
      { voiceId: "voice2", weight: 0.5 },
    ]);
  });

  it("should parse a valid formula with multiple voices", () => {
    const formula = "v1*0.3+ v2*0.3 +v3*0.4";
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([
      { voiceId: "v1", weight: 0.3 },
      { voiceId: "v2", weight: 0.3 },
      { voiceId: "v3", weight: 0.4 },
    ]);
  });

  it("should parse a single voice without weight as 100%", () => {
    const formula = "voice1";
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([{ voiceId: "voice1", weight: 1 }]);
  });

  it("should parse voice IDs with hyphens and underscores", () => {
    const formula = "voice-1*0.4 + voice_2*0.6";
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([
      { voiceId: "voice-1", weight: 0.4 },
      { voiceId: "voice_2", weight: 0.6 },
    ]);
  });

  it("should throw an error for an empty formula", () => {
    expect(() => parseVoiceFormula("   ")).toThrow();
  });

  it("should throw an error when a term is missing an asterisk", () => {
    const formula = "voice1*0.5+voice20.5";
    expect(() => parseVoiceFormula(formula)).toThrow();
  });

  it("should throw an error for a formula with invalid characters", () => {
    const formula = "voice1*0.5+voice2*0.5$";
    expect(() => parseVoiceFormula(formula)).toThrow();
  });

  it("should throw an error when a weight is not a valid number", () => {
    const formula = "voice1*abc+voice2*0.5";
    expect(() => parseVoiceFormula(formula)).toThrow();
  });

  it("should throw an error when weights do not sum exactly to 1", () => {
    const formula = "voice1*0.3 + voice2*0.3";
    expect(() => parseVoiceFormula(formula)).toThrow();
  });

  it("should handle extra whitespace gracefully", () => {
    const formula = "  voice1*0.7   +   voice2*0.3  ";
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([
      { voiceId: "voice1", weight: 0.7 },
      { voiceId: "voice2", weight: 0.3 },
    ]);
  });

  it("should round weights to the nearest 0.1", () => {
    const formula = "voice2*0.667 + voice1*0.333";
    // 0.333 rounds to 0.3 and 0.667 rounds to 0.7 (total 1.0)
    const result = parseVoiceFormula(formula);
    expect(result).toEqual([
      { voiceId: "voice2", weight: 0.7 },
      { voiceId: "voice1", weight: 0.3 },
    ]);
  });
});

describe("serializeVoiceFormula", () => {
  it("should serialize a single voice correctly", () => {
    const voiceWeights = [{ voiceId: "voice1", weight: 1 }];
    const formula = serializeVoiceFormula(voiceWeights);
    expect(formula).toBe("voice1*1");
  });

  it("should serialize multiple voices correctly", () => {
    const voiceWeights = [
      { voiceId: "voice1", weight: 0.3 },
      { voiceId: "voice2", weight: 0.7 },
    ];
    const formula = serializeVoiceFormula(voiceWeights);
    expect(formula).toBe("voice2*0.7 + voice1*0.3");
  });

  it("should produce a formula that round-trips with parseVoiceFormula", () => {
    const voiceWeights = [
      { voiceId: "voice-1", weight: 0.4 },
      { voiceId: "voice_2", weight: 0.6 },
    ];
    const formula = serializeVoiceFormula(voiceWeights);
    const parsed = parseVoiceFormula(formula);
    expect(parsed).toEqual(voiceWeights);
  });

  it("should round weights to the nearest 0.1", () => {
    const voiceWeights = [
      { voiceId: "voice1", weight: 0.333 },
      { voiceId: "voice2", weight: 0.667 },
    ];
    const formula = serializeVoiceFormula(voiceWeights);
    expect(formula).toBe("voice2*0.7 + voice1*0.3");
  });

  it("should remove voices with weight 0 or less", () => {
    const voiceWeights = [
      { voiceId: "voice1", weight: 0 },
      { voiceId: "voice2", weight: 0.5 },
      { voiceId: "voice3", weight: -0.5 },
    ];
    const formula = serializeVoiceFormula(voiceWeights);
    expect(formula).toBe("voice2*0.5");
  });
});
