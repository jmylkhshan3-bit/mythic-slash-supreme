<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { ExternalLink, TriangleAlert } from "lucide-svelte";
  import { VERSION } from "$lib/shared/version";

  let latestVersion = $state("");
  let hasNewerVersion = $state(false);
  let loading = $state(true);

  // Cache configuration
  const CACHE_KEY = "kokoro-latest-version";
  const CACHE_EXPIRY_KEY = "kokoro-latest-version-expiry";
  const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

  onMount(async () => {
    if (browser) {
      await checkVersion();
    }
  });

  async function checkVersion() {
    // Check for cached version first
    const cachedVersion = localStorage.getItem(CACHE_KEY);
    const cacheExpiry = localStorage.getItem(CACHE_EXPIRY_KEY);

    if (cachedVersion && cacheExpiry && parseInt(cacheExpiry) > Date.now()) {
      latestVersion = cachedVersion;
      compareVersions();
      loading = false;
      return;
    }

    try {
      // Fetch latest release from GitHub API
      const response = await fetch(
        "https://api.github.com/repos/eduardolat/kokoro-web/releases/latest",
      );

      if (!response.ok) {
        throw new Error("Failed to fetch latest version");
      }

      const data = await response.json();
      latestVersion = data.tag_name;

      // Cache the result
      localStorage.setItem(CACHE_KEY, latestVersion);
      localStorage.setItem(
        CACHE_EXPIRY_KEY,
        (Date.now() + CACHE_DURATION).toString(),
      );

      compareVersions();
    } catch (error) {
      console.error("Error checking for newer version:", error);
    } finally {
      loading = false;
    }
  }

  function compareVersions() {
    // Remove 'v' prefix if present for comparison
    const currentClean = VERSION.replace(/^v/, "");
    const latestClean = latestVersion.replace(/^v/, "");

    // Compare versions (basic semver comparison)
    hasNewerVersion = latestClean > currentClean;
  }
</script>

{#if hasNewerVersion && !loading}
  <div role="alert" class="alert alert-warning mb-4">
    <TriangleAlert />
    <span>
      A new version ({latestVersion}) is available! Your current version is {VERSION}.
    </span>
    <a
      href="https://github.com/eduardolat/kokoro-web/releases"
      target="_blank"
      class="btn btn-sm"
    >
      View releases
      <ExternalLink class="ml-1 size-4" />
    </a>
  </div>
{/if}
