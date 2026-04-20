<script lang="ts">
  import "../app.css";
  import { fade } from "svelte/transition";
  import ThemeSelect from "$lib/client/components/ThemeSelect.svelte";
  import { ExternalLink, Menu, X, Github } from "lucide-svelte";
  import type { LayoutProps } from "./$types";
  import { onMount } from "svelte";
  import umami from "$lib/client/umami";
  import { VERSION } from "$lib/shared/version";

  let { children }: LayoutProps = $props();

  let isOpen = $state(false);

  onMount(() => {
    umami.loadScript();
    umami.identify({ hostname: window.location.hostname });
  });
</script>

<div class="bg-base-100 h-screen w-screen overflow-x-hidden overflow-y-auto">
  <div class="mx-auto w-full overflow-hidden md:max-w-7xl">
    <header
      class="border-base-content/10 flex w-full items-center justify-between border-b p-4"
    >
      <div class="flex items-center space-x-2">
        <img
          src="/logo.png"
          alt="Kokoro Web Logo"
          class="size-[40px] rounded-full shadow-sm md:size-[50px]"
        />
        <div class="text-nowrap">
          <h1 class="text-xl font-bold md:text-3xl">Kokoro Web</h1>
          <h2 class="text-sm font-semibold md:text-base">
            Free AI Voice Generator
          </h2>
        </div>
      </div>
      <nav class="hidden md:flex md:items-center md:justify-end">
        <a
          href="https://huggingface.co/hexgrad/Kokoro-82M"
          target="_blank"
          class="btn btn-ghost"
          data-umami-event="click-model-header"
        >
          <ExternalLink class="size-[16px]" />
          <span>Model 🤗</span>
        </a>
        <a
          href="/api/v1/index.html"
          target="_blank"
          class="btn btn-ghost"
          data-umami-event="click-api-docs-header"
        >
          <ExternalLink class="size-[16px]" />
          <span>API Docs</span>
        </a>
        <a
          href="https://github.com/eduardolat/kokoro-web"
          target="_blank"
          class="btn btn-ghost"
          data-umami-event="click-star-on-github-header"
        >
          <Github class="size-[16px]" />
          <span>Star on GitHub</span>
          <img
            alt="GitHub Repo stars"
            src="https://img.shields.io/github/stars/eduardolat/kokoro-web?style=plastic&label=%20"
          />
        </a>
        <div class="ml-2">
          <ThemeSelect />
        </div>
      </nav>
      <button
        class="btn btn-ghost btn-square md:hidden"
        onclick={() => (isOpen = !isOpen)}
      >
        <Menu class="size-[24px]" />
      </button>
    </header>

    {#if isOpen}
      <nav
        class="
          bg-base-200 fixed top-0 z-50 h-screen w-screen space-y-2 overflow-x-hidden
          overflow-y-auto p-4 md:hidden
        "
        transition:fade={{ duration: 100 }}
      >
        <div class="mb-4 flex justify-end">
          <button
            class="btn btn-ghost btn-square md:hidden"
            onclick={() => (isOpen = !isOpen)}
          >
            <X class="size-[24px]" />
          </button>
        </div>

        <a
          href="https://huggingface.co/hexgrad/Kokoro-82M"
          target="_blank"
          class="btn btn-soft flex w-full items-center justify-start space-x-1"
          data-umami-event="click-model-header"
        >
          <ExternalLink class="size-[16px]" />
          <span>Model 🤗</span>
        </a>
        <a
          href="/api/v1/index.html"
          target="_blank"
          class="btn btn-soft flex w-full items-center justify-start space-x-1"
          data-umami-event="click-api-docs-header"
        >
          <ExternalLink class="size-[16px]" />
          <span>API Docs</span>
        </a>
        <a
          href="https://github.com/eduardolat/kokoro-web"
          target="_blank"
          class="btn btn-soft flex w-full items-center justify-start space-x-1"
          data-umami-event="click-star-on-github-header"
        >
          <Github class="size-[16px]" />
          <span>Star on GitHub</span>
          <img
            alt="GitHub Repo stars"
            src="https://img.shields.io/github/stars/eduardolat/kokoro-web?style=plastic&label=%20"
          />
        </a>
        <ThemeSelect class="w-full" />
      </nav>
    {/if}

    <main class="mb-[30px] w-full p-4">
      {@render children()}
    </main>

    <footer class="border-base-content/10 border-t px-4 py-[50px]">
      <div class="container mx-auto text-center">
        <div class="mb-4">
          <p class="text-lg font-bold">Kokoro Web {VERSION}</p>
          <p class="text-sm opacity-80">
            100% Free & Open Source AI Voice Generator
          </p>
        </div>

        <div class="mb-4 flex flex-wrap justify-center gap-4">
          <a
            href="https://huggingface.co/hexgrad/Kokoro-82M"
            target="_blank"
            class="flex items-center gap-1 text-sm hover:underline"
            data-umami-event="click-model-footer"
          >
            <ExternalLink class="size-[14px]" />
            <span>Powered by Kokoro 82M</span>
          </a>

          <a
            href="https://github.com/eduardolat/kokoro-web"
            target="_blank"
            class="flex items-center gap-1 text-sm hover:underline"
            data-umami-event="click-github-footer"
          >
            <Github class="size-[14px]" />
            <span>Self-hostable</span>
          </a>

          <a
            href="/api/v1/index.html"
            target="_blank"
            class="flex items-center gap-1 text-sm hover:underline"
            data-umami-event="click-api-docs-footer"
          >
            <ExternalLink class="size-[14px]" />
            <span>OpenAI Compatible API</span>
          </a>
        </div>

        <p class="text-xs opacity-70">
          Kokoro Web
          <span class="mx-1">•</span>
          Free for personal and commercial use
          <span class="mx-1">•</span>
          <a
            href="https://eduardo.lat?utm_source=kokoro&utm_medium=web&utm_campaign=footer_link"
            target="_blank"
            class="link"
            data-umami-event="click-author-website"
          >
            Created by Eduardo Lat
          </a>
        </p>
      </div>
    </footer>
  </div>
</div>
