<script lang="ts">
  import { WandSparkles, Loader } from "lucide-svelte";

  interface Props {
    loading: boolean;
    onclick: () => void;
  }

  let { loading, onclick }: Props = $props();
</script>

<button
  class={{
    "rounded-field flex cursor-pointer": true,
    "bg-base-300 cursor-wait": loading,
    "button-wrapper bg-gradient-to-r": !loading,
    "from-purple-400 via-green-400 to-blue-400": !loading,
  }}
  onclick={() => onclick()}
  disabled={loading}
>
  <div
    class={{
      "bg-base-300/80 rounded-field m-1 flex flex-grow backdrop-blur-md": true,
      "items-center justify-center space-x-2 px-4 py-2 text-xl": true,
    }}
  >
    <span>Generate Voice</span>
    {#if loading}
      <Loader class="size-5 animate-spin" />
    {:else}
      <WandSparkles class="size-5" />
    {/if}
  </div>
</button>

<style>
  .button-wrapper {
    background-size: 500% 500%;
    animation: gradient 5s ease-in-out infinite;
  }

  @keyframes gradient {
    0% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0% 50%;
    }
  }
</style>
