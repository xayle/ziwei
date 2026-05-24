<script setup lang="ts">
defineProps<{
  items: Array<{ label: string; value: string; sub?: string; cls?: string }>
}>()
</script>

<template>
  <div v-if="items.length" class="chart-quick-insights">
    <div v-for="item in items" :key="item.label" :class="['cqi-item', item.cls]">
      <span class="cqi-label">{{ item.label }}</span>
      <span class="cqi-value">{{ item.value }}</span>
      <span v-if="item.sub" class="cqi-sub">{{ item.sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.chart-quick-insights {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}

.cqi-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  min-width: 72px;
}

.cqi-label {
  font-size: 10px;
  color: var(--text-2);
}

.cqi-value {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}

.cqi-sub {
  font-size: 10px;
  color: var(--text-2);
  max-width: 110px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cqi-ji {
  border-color: #c4b5fd;
  background: #f5f3ff;
}

.cqi-ji .cqi-value {
  color: #5b21b6;
}

.cqi-lu {
  border-color: #86efac;
  background: #f0fdf4;
}

.cqi-lu .cqi-value {
  color: #166534;
}

.cqi-dense {
  border-color: #fcd34d;
  background: #fffbeb;
}

.cqi-dense .cqi-value {
  color: #92400e;
}

.cqi-good .cqi-value {
  color: #166534;
}
</style>