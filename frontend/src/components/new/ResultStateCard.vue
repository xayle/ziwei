<script setup lang="ts">
defineProps<{
  title: string
  message: string
  actionLabel?: string
  tone?: 'light' | 'dark'
  compact?: boolean
}>()

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="result-state" :class="[`result-state--${tone || 'light'}`, { 'result-state--compact': compact }]">
    <strong class="result-state__title">{{ title }}</strong>
    <span class="result-state__message">{{ message }}</span>
    <button v-if="actionLabel" class="result-state__action" @click="$emit('action')">
      {{ actionLabel }}
    </button>
  </div>
</template>

<style scoped>
.result-state {
  padding: 24px;
  border-radius: 18px;
  margin-top: 16px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow);
}

.result-state--compact {
  padding: 18px 20px;
  margin-top: 12px;
}

.result-state--dark {
  background: var(--surface);
  border-color: var(--border);
  border-left: 3px solid var(--brand-gold);
}

.result-state__title {
  display: block;
  margin-bottom: 6px;
  color: var(--brand-ink);
}

.result-state__message {
  display: block;
  line-height: 1.7;
  color: var(--text-2);
}

.result-state__action {
  min-height: 38px;
  margin-top: 14px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid var(--accent);
  background: #fff;
  color: var(--accent);
  cursor: pointer;
}
</style>
