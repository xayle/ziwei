<script setup lang="ts">
const props = withDefaults(defineProps<{
  state: 'loading' | 'error' | 'empty'
  message?: string | null
  title?: string
  description?: string
  retryLabel?: string
  skeletonCount?: number
}>(), {
  message: '',
  title: '',
  description: '',
  retryLabel: '重试',
  skeletonCount: 4,
})

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div v-if="props.state === 'loading'" class="wb-loading-bar">
    <div class="skel" v-for="i in props.skeletonCount" :key="i" />
  </div>

  <div v-else-if="props.state === 'error'" class="wb-error-card">
    {{ props.message }}
    <button @click="emit('retry')">{{ props.retryLabel }}</button>
  </div>

  <div v-else class="wb-empty-card">
    <div class="wb-empty-title">{{ props.title }}</div>
    <div class="wb-empty-desc">{{ props.description }}</div>
    <button class="wb-empty-btn" type="button" @click="emit('retry')">{{ props.retryLabel }}</button>
  </div>
</template>

<style scoped>
.wb-loading-bar { display: flex; flex-direction: column; gap: 12px; padding: 24px; }
.skel {
  height: 80px; border-radius: 10px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px;
  animation: shimmer 1.2s infinite;
}
@keyframes shimmer { from { background-position: -400px 0; } to { background-position: 400px 0; } }

.wb-error-card {
  margin: 20px 24px; padding: 20px;
  background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 10px; font-size: 13px; color: #dc2626;
  display: flex; gap: 12px; align-items: center;
}
.wb-error-card button {
  padding: 4px 10px; border: 1px solid #fca5a5; border-radius: 6px;
  background: transparent; color: #dc2626; cursor: pointer; font-size: 12px;
}

.wb-empty-card {
  margin: 20px 24px;
  padding: 18px 20px;
  border-radius: 10px;
  border: 1px dashed var(--border);
  background: var(--surface);
  display: grid;
  gap: 8px;
}

.wb-empty-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-1);
}

.wb-empty-desc {
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.6;
}

.wb-empty-btn {
  justify-self: start;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-1);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

@media print {
  .wb-loading-bar, .wb-error-card { display: none; }
}
</style>
