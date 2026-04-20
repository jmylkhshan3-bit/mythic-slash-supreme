// Use rounding to one decimal place (steps of 0.1)
const round = (num: number): number => Math.round(num * 10) / 10;

export function adjustVoiceWeights(
  selections: Record<string, number>,
  changedVoiceId: string,
  newWeight: number,
): Record<string, number> {
  const updated = { ...selections, [changedVoiceId]: round(newWeight) };
  let total = Object.values(updated).reduce((sum, w) => sum + w, 0);

  // If total exceeds 1, subtract 0.1 from a random eligible voice until total <= 1.
  if (total > 1) {
    while (total > 1) {
      // Get the list of other voices with at least 0.1 weight to reduce.
      const others = Object.keys(updated).filter(
        (key) => key !== changedVoiceId && updated[key] >= 0.1,
      );
      if (others.length === 0) {
        updated[changedVoiceId] = 1;
        break;
      }
      const randomIndex = Math.floor(Math.random() * others.length);
      const key = others[randomIndex];
      updated[key] = round(Math.max(0, updated[key] - 0.1));
      total = Object.values(updated).reduce((sum, w) => sum + w, 0);
    }
  }

  return updated;
}
