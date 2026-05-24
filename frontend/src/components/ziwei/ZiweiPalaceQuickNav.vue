<script setup lang="ts">
import type { PalaceResponse } from '@/api/ziwei'

const props = defineProps<{
  palaces: PalaceResponse[]
  selectedPalace: PalaceResponse | null
  palaceHasTransform: (palace: PalaceResponse, transform: string) => boolean
  getPalaceQuickInfo: (palace: PalaceResponse) => string
}>()

const emit = defineEmits<{
  select: [palace: PalaceResponse]
}>()
</script>

<template>
  <div class="palace-quick-nav-panel">
    <div class="pqnp-row">
      <button
        v-for="palace in props.palaces"
        :key="palace.index"
        :class="['pqnp-btn', {
          'pqnp-selected': props.selectedPalace?.index === palace.index,
          'pqnp-life': palace.name.includes('命'),
          'pqnp-body': palace.name.includes('身'),
          'pqnp-has-lu': props.palaceHasTransform(palace, '禄'),
          'pqnp-has-ji': props.palaceHasTransform(palace, '忌'),
        }]"
        :title="props.getPalaceQuickInfo(palace)"
        @click="emit('select', palace)"
      >
        <span class="pqnp-name">{{ palace.name.replace('宫', '') }}</span>
        <span class="pqnp-count">{{ (palace.main_stars?.length || 0) + (palace.aux_stars?.length || 0) }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.palace-quick-nav-panel {
  margin: 12px 0;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.pqnp-row {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.pqnp-btn {
  flex: 1;
  padding: 6px 4px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  position: relative;
}

.pqnp-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}

.pqnp-btn.pqnp-selected {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.pqnp-btn.pqnp-life {
  border-left: 3px solid var(--danger);
}

.pqnp-btn.pqnp-body {
  border-left: 3px solid var(--primary);
}

.pqnp-btn.pqnp-has-lu::after {
  content: '禄';
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 8px;
  color: #22c55e;
}

.pqnp-btn.pqnp-has-ji::before {
  content: '忌';
  position: absolute;
  top: 2px;
  left: 2px;
  font-size: 8px;
  color: #ef4444;
}

.pqnp-name {
  display: block;
  font-size: var(--fs-sm);
  font-weight: 500;
}

.pqnp-count {
  display: block;
  font-size: 10px;
  color: var(--text-2);
  margin-top: 2px;
}

.pqnp-btn.pqnp-selected .pqnp-count {
  color: rgba(255,255,255,0.8);
}
</style>