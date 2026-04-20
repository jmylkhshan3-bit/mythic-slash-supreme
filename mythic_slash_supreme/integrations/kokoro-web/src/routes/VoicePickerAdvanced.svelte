<script lang="ts">
  import { adjustVoiceWeights } from "$lib/client/utils/adjustVoiceWeights";
  import RangeControl from "$lib/client/components/RangeControl.svelte";
  import { type Voice } from "$lib/shared/resources";
  import type { VoiceWeight } from "$lib/shared/kokoro/combineVoices";
  import { parseVoiceFormula, serializeVoiceFormula } from "$lib/shared/kokoro";
  import { Settings2, X } from "lucide-svelte";
  import { profile } from "./store.svelte";

  interface Props {
    orderedVoices: Voice[][];
  }
  let { orderedVoices }: Props = $props();

  // Advanced mode selections: mapping voiceId to its weight.
  let advancedSelections = $state<Record<string, number>>({});

  // Set weights from the profile's when it changes.
  let lastLoadedName = $state("");
  $effect(() => {
    if (profile.name === lastLoadedName) return;

    const parsed = parseVoiceFormula(profile.voiceFormula);

    advancedSelections = {};
    for (const { voiceId, weight } of parsed) {
      advancedSelections[voiceId] = weight;
    }

    lastLoadedName = profile.name;
  });

  // Update the weight of a voice and adjust others if necessary.
  function updateVoiceWeight(voiceId: string, newWeight: number) {
    advancedSelections = adjustVoiceWeights(
      advancedSelections,
      voiceId,
      newWeight,
    );

    const selections: VoiceWeight[] = Object.entries(advancedSelections).map(
      ([voiceId, weight]) => ({ voiceId, weight }),
    );
    profile.voiceFormula = serializeVoiceFormula(selections);
  }
</script>

<button
  class="mt-[10px] flex w-full space-x-2"
  onclick={() => (window as any).formula_editor.showModal()}
>
  <input
    type="text"
    bind:value={profile.voiceFormula}
    readonly
    class="input flex-grow"
    placeholder="E.g. af_heart*0.4 + am_santa*0.6"
  />
  <div class="tooltip tooltip-left inline-block" data-tip="Formula editor">
    <div class="btn btn-square btn-soft">
      <Settings2 class="size-5" />
    </div>
  </div>
</button>

<dialog id="formula_editor" class="modal">
  <div class="modal-box flex h-screen max-h-[90dvh] flex-col overflow-hidden">
    <form method="dialog">
      <button class="btn btn-sm btn-circle btn-ghost absolute top-2 right-2">
        <X />
      </button>
    </form>

    <h3 class="text-lg font-bold">Formula editor</h3>
    <p class="py-2">
      A voice formula blends multiple voices, each with a weight from 0% to 100%
      <i>(0.0 to 1.0)</i>. Higher weights mean more influence, and all weights
      must add up to 1.
    </p>

    <div class="h-full space-y-4 overflow-x-hidden overflow-y-auto">
      {#each orderedVoices as langVoices}
        <fieldset
          class="fieldset bg-base-200 border-base-300 rounded-box border p-4"
        >
          <legend class="fieldset-legend">
            {langVoices[0].lang.name} voices
          </legend>
          {#each langVoices as vo}
            <RangeControl
              value={advancedSelections[vo.id] ?? 0}
              title={advancedSelections[vo.id]
                ? `${vo.name} (${vo.overallGrade}) - ${vo.id} - Weight ${Math.round(advancedSelections[vo.id] * 100)}%`
                : `${vo.name} (${vo.overallGrade}) - ${vo.id} - Weight 0%`}
              hideValue={true}
              min="0"
              max="1"
              step="0.1"
              oninput={(newValue) =>
                updateVoiceWeight(vo.id, parseFloat(newValue))}
              inputClass="w-full"
            />
          {/each}
        </fieldset>
      {/each}
    </div>

    <div class="mt-2 flex items-end space-x-2">
      <label class="flex-grow">
        <span class="text-xs font-semibold">Formula preview</span>
        <input
          type="text"
          class="input mt-1 w-full"
          bind:value={profile.voiceFormula}
          readonly
          placeholder="Make changes above"
        />
      </label>
      <form method="dialog">
        <button class="btn btn-primary">OK</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
