<script lang="ts">
  import VoicePickerSimple from "./VoicePickerSimple.svelte";
  import VoicePickerAdvanced from "./VoicePickerAdvanced.svelte";
  import { voicesByLang, type LangId } from "$lib/shared/resources";
  import { profile } from "./store.svelte";

  let isSimpleMode = $derived(profile.voiceMode === "simple");

  function toggleMode() {
    profile.voiceMode = profile.voiceMode === "simple" ? "advanced" : "simple";
  }

  // Order voices by language, with the selected language first.
  let orderedVoices = $derived.by(() => {
    let langVoices = voicesByLang[profile.lang];
    let combinedVoices = [langVoices];

    let otherVoices = { ...voicesByLang };
    delete otherVoices[profile.lang];

    for (let voices of Object.values(otherVoices)) {
      combinedVoices.push(voices);
    }

    return combinedVoices;
  });
</script>

<div>
  <div class="flex items-end justify-between">
    <span class="text-xs font-semibold">
      {isSimpleMode ? "Voice (quality)" : "Voice formula"}
    </span>

    <label class="flex items-center space-x-2">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        checked={profile.voiceMode == "advanced"}
        onclick={toggleMode}
      />
      <span>Advanced Mode</span>
    </label>
  </div>

  {#if isSimpleMode}
    <VoicePickerSimple {orderedVoices} />
  {:else}
    <VoicePickerAdvanced {orderedVoices} />
  {/if}
</div>
