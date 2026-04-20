<script lang="ts">
  interface Props {
    title?: string;
    titleClass?: string;
    helpText?: string;
    helpTextClass?: string;
    selectClass?: string;
    value?: any;
    children?: any;
    [key: string]: unknown;
  }

  let {
    title,
    titleClass,
    helpText,
    helpTextClass,
    selectClass,
    value = $bindable(),
    children,
    ...others
  }: Props = $props();
</script>

<fieldset class="fieldset w-full">
  {#if title}
    <legend class="fieldset-legend {titleClass}">{title}</legend>
  {/if}
  <select class="select {selectClass ?? ''}" bind:value {...others}>
    {#if children}
      {@render children()}
    {/if}
  </select>
  {#if helpText}
    <span class="fieldset-label {helpTextClass}">{helpText}</span>
  {/if}
</fieldset>
