<script setup lang="ts">
defineProps<{
  message: string
  status?: 'degraded' | 'warn'
}>()
</script>

<template>
  <div
    class="trust-degraded-banner"
    role="status"
    :data-status="status || 'degraded'"
    data-testid="trust-degraded-banner"
  >
    <p>{{ message }}</p>
  </div>
</template>

<style scoped>
.trust-degraded-banner {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--trust-alert-border);
  background: var(--surface);
  color: var(--brand-cinnabar);
  font-size: 13px;
  line-height: 1.6;
}

.trust-degraded-banner p {
  margin: 0;
}
</style>
