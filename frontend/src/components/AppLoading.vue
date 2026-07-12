<script setup lang="ts">
</script>

<template>
  <div class="app-loading">
    <div class="loading-spinner" />
    <p class="loading-text">加载中…</p>
  </div>
</template>

<style scoped>
.app-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  gap: var(--sp-4);
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
.loading-text {
  color: var(--text-3);
  font-size: var(--fs-sm);
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>