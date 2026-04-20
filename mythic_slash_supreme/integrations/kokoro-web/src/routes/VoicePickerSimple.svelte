<script lang="ts">
  interface Props {
    orderedVoices: Voice[][];
  }
  let { orderedVoices }: Props = $props();

  import { type Voice } from "$lib/shared/resources";
  import SelectControl from "$lib/client/components/SelectControl.svelte";
  import { profile } from "./store.svelte";

  // Every time the selected language changes, select the first voice.
  $effect(() => {
    let firstVoice = orderedVoices[0][0];
    profile.voiceFormula = firstVoice.id;
  });
</script>

<SelectControl bind:value={profile.voiceFormula} selectClass="w-full mt-[6px]">
  {#each orderedVoices as voicesArr}
    <optgroup label={voicesArr[0].lang.name}>
      {#each voicesArr as vo}
        <option value={vo.id}>{vo.name} ({vo.overallGrade})</option>
      {/each}
    </optgroup>
  {/each}
</SelectControl>
