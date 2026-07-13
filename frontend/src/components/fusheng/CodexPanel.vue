<script setup lang="ts">
defineProps<{
  compact?: boolean
}>()
</script>

<template>
  <section
    class="fs-codex-panel"
    :class="{ 'fs-codex-panel--compact': compact }"
  >
    <slot />
  </section>
</template>
