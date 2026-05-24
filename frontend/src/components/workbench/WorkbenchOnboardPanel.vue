<script setup lang="ts">
export type WorkbenchOnboardAction = {
  key: string
  label: string
  tone?: 'accent' | 'ghost'
}

withDefaults(defineProps<{
  icon?: string
  title: string
  subtitle: string
  label: string
  description: string
  actions?: WorkbenchOnboardAction[]
}>(), {
  icon: '🧭',
  actions: () => [],
})

const emit = defineEmits<{
  action: [key: string]
}>()
</script>

<template>
  <div class="wb-onboard-panel">
    <div class="wb-onboard-hero">
      <div class="wb-onboard-icon">{{ icon }}</div>
      <div>
        <h1 class="wb-onboard-title">{{ title }}</h1>
        <p class="wb-onboard-sub">{{ subtitle }}</p>
      </div>
    </div>

    <div class="wb-onboard-card">
      <div class="wb-onboard-label">{{ label }}</div>
      <p class="wb-onboard-desc">{{ description }}</p>
      <div v-if="actions.length" class="wb-onboard-actions">
        <button
          v-for="item in actions"
          :key="item.key"
          :class="['wb-onboard-btn', item.tone === 'accent' ? 'is-accent' : 'is-ghost']"
          type="button"
          @click="emit('action', item.key)"
        >
          {{ item.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wb-onboard-panel {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.wb-onboard-hero {
  display: flex;
  gap: 16px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 24px;
}

.wb-onboard-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-size: 30px;
  background: var(--accent-lt);
}

.wb-onboard-title {
  margin: 0;
  font-size: 26px;
  color: var(--text);
  font-family: var(--font-cn);
}

.wb-onboard-sub {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--text-2);
}

.wb-onboard-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
}

.wb-onboard-label {
  font-size: 10px;
  color: var(--text-3);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: .05em;
}

.wb-onboard-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-2);
}

.wb-onboard-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.wb-onboard-btn {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.wb-onboard-btn.is-accent {
  background: var(--accent);
  color: #fff;
  border: none;
}

.wb-onboard-btn.is-accent:hover {
  background: var(--accent-dark);
}

.wb-onboard-btn.is-ghost {
  background: transparent;
  border: 1px solid var(--border-md);
  color: var(--text-2);
}

.wb-onboard-btn.is-ghost:hover {
  border-color: var(--accent);
  color: var(--accent);
}

@media (max-width: 768px) {
  .wb-onboard-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .wb-onboard-actions {
    flex-direction: column;
  }
}
</style>
