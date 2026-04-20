<script lang="ts">
  import { Copy, FilePlus, Save, Trash } from "lucide-svelte";
  import { onMount } from "svelte";
  import {
    defaultProfile,
    loadProfile,
    profile,
    type ProfileData,
  } from "./store.svelte";
  import { toaster } from "$lib/client/toaster";

  const localStorageProfilesKey = "kokoro-web-profiles";
  const newProfileIndex = -1;

  let profiles = $state<ProfileData[]>([]);
  let selectedProfileIndex = $state(newProfileIndex);
  let isNewProfile = $derived(selectedProfileIndex === newProfileIndex);

  $effect(() => {
    updateSelection(selectedProfileIndex);
  });

  onMount(() => {
    loadProfiles();
  });

  function loadProfiles() {
    const stored = localStorage.getItem(localStorageProfilesKey);
    profiles = stored ? JSON.parse(stored) : [];
  }

  function saveProfiles() {
    localStorage.setItem(localStorageProfilesKey, JSON.stringify(profiles));
  }

  function updateSelection(index: number) {
    if (index >= 0 && index < profiles.length) {
      loadProfile(profiles[index]);
    } else {
      loadProfile(defaultProfile);
    }
  }

  function saveProfile() {
    if (isNewProfile) {
      const newName = window.prompt("Enter a new profile name:");

      if (!newName) return;
      if (profiles.some((prof) => prof.name === newName)) {
        toaster.error("Profile name already exists");
        return;
      }

      profiles.push({ ...profile, name: newName });
      saveProfiles();

      selectedProfileIndex = profiles.length - 1;
    } else {
      profiles[selectedProfileIndex] = { ...profile };
      saveProfiles();
    }

    toaster.success("Profile saved");
  }

  function duplicateProfile() {
    if (isNewProfile) return;

    const currentProfile = profiles[selectedProfileIndex];
    const suggestedName = currentProfile.name + " copy";
    const newName = window.prompt(
      "Enter a name for the new profile:",
      suggestedName,
    );

    if (!newName) return;
    if (profiles.some((prof) => prof.name === newName)) {
      toaster.error("Profile name already exists");
      return;
    }

    const duplicatedProfile = { ...currentProfile, name: newName };
    profiles.push(duplicatedProfile);
    saveProfiles();

    selectedProfileIndex = profiles.length - 1;
    toaster.success("Profile duplicated");
  }

  function deleteProfile() {
    if (isNewProfile) return;

    if (!window.confirm("Are you sure you want to delete this profile?")) {
      return;
    }

    profiles.splice(selectedProfileIndex, 1);
    saveProfiles();

    selectedProfileIndex = newProfileIndex;
    toaster.success("Profile deleted");
  }
</script>

<fieldset class="fieldset w-full">
  <legend class="fieldset-legend">Profile</legend>

  <div class="flex items-center space-x-2">
    <select class="select w-full" bind:value={selectedProfileIndex}>
      <option value={newProfileIndex}>&lt;new profile&gt;</option>
      {#each profiles as prof, index}
        <option value={index}>{prof.name}</option>
      {/each}
    </select>

    <div
      class="tooltip tooltip-left inline-block"
      data-tip={isNewProfile
        ? "Save current changes to a new profile"
        : "Save profile changes"}
    >
      <button onclick={saveProfile} class="btn btn-soft btn-square">
        {#if isNewProfile}
          <FilePlus class="size-5" />
        {:else}
          <Save class="size-5" />
        {/if}
      </button>
    </div>

    {#if !isNewProfile}
      <div
        class="tooltip tooltip-left inline-block"
        data-tip="Duplicate this profile"
      >
        <button onclick={duplicateProfile} class="btn btn-soft btn-square">
          <Copy class="size-5" />
        </button>
      </div>

      <div
        class="tooltip tooltip-left inline-block"
        data-tip="Delete this profile"
      >
        <button onclick={deleteProfile} class="btn btn-soft btn-square">
          <Trash class="size-5" />
        </button>
      </div>
    {/if}
  </div>

  <span class="fieldset-label">
    Profiles are saved settings that can be loaded later, they are stored in
    your browser.
  </span>
</fieldset>
