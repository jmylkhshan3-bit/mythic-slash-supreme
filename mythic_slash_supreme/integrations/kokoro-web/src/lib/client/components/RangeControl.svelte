<script lang="ts">
  interface Props {
    title?: string;
    titleClass?: string;
    inputClass?: string;
    helpText?: string;
    helpTextClass?: string;
    hideValue?: boolean;
    value?: any;
    oninput?: (newVal: any) => void;
    [key: string]: unknown;
  }

  let {
    title,
    titleClass,
    inputClass,
    helpText,
    helpTextClass,
    hideValue,
    value = $bindable(),
    oninput,
    ...others
  }: Props = $props();

  let titleValue = $derived.by(() => {
    if (!title && !value) return "";
    if (title && hideValue) return title;

    if (!title && value) return value;
    if (title && !value) return title;
    return `${title} - ${value}`;
  });
</script>

<fieldset class="fieldset">
  <legend class="fieldset-legend {titleClass}">{titleValue}</legend>
  <input
    type="range"
    class="range {inputClass ?? ''}"
    bind:value
    {...others}
    oninput={(e) =>
      oninput && oninput((e.currentTarget as HTMLInputElement).value)}
  />
  {#if helpText}
    <span class="fieldset-label {helpTextClass}">{helpText}</span>
  {/if}
</fieldset>
