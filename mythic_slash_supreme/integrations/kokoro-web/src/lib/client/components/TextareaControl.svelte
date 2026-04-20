<script lang="ts">
  interface Props {
    title?: string;
    titleClass?: string;
    helpText?: string;
    helpTextClass?: string;
    textareaClass?: string;
    value?: any;
    [key: string]: unknown;
  }

  let {
    title = "",
    titleClass = "",
    helpText = "",
    helpTextClass = "",
    textareaClass = "",
    value = $bindable(),
    ...others
  }: Props = $props();
</script>

<fieldset class="fieldset">
  {#if title}
    <legend class="fieldset-legend {titleClass}">{title}</legend>
  {/if}
  <textarea class="textarea {textareaClass ?? ''}" bind:value {...others}>
  </textarea>
  {#if helpText}
    <span class="fieldset-label {helpTextClass}">{helpText}</span>
  {/if}
</fieldset>
