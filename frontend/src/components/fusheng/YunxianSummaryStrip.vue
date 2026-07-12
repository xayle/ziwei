<script setup lang="ts">
import { computed } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'
import { findDayunForYear, findLiuyueForMonth, type OverlayLayer } from '@/utils/ziweiOverlay'

const props = defineProps<{
  ziwei: ZiweiResponse
  activeLayer: OverlayLayer
  targetDate?: string
  liuyueMonth?: number
}>()

const emit = defineEmits<{
  selectLayer: [layer: OverlayLayer]
}>()

const refYear = computed(() => {
  if (props.targetDate) {
    const parsed = new Date(props.targetDate.includes('T') ? props.targetDate : `${props.targetDate}T12:00:00`)
    if (!Number.isNaN(parsed.getTime())) return parsed.getFullYear()
  }
  return new Date().getFullYear()
})

const dayunCell = computed(() => {
  const dy = findDayunForYear(props.ziwei.dayun, refYear.value)
  if (!dy) return { label: '大限', value: '—', hint: '' }
  return {
    label: '大限',
    value: dy.ganzhi || '—',
    hint: dy.start_age != null ? `${dy.start_age} 岁起` : '',
  }
})

const liunianCell = computed(() => {
  const ln = props.ziwei.liunian
  if (!ln) return { label: '流年', value: '—', hint: '' }
  return {
    label: '流年',
    value: ln.year_gz || `${ln.year}`,
    hint: `${ln.year} 年`,
  }
})

const liuyueCell = computed(() => {
  const month = props.liuyueMonth ?? new Date().getMonth() + 1
  const ly = findLiuyueForMonth(props.ziwei.liuyue, month)
  return {
    label: '流月',
    value: ly?.month_gz || ly?.month_name || `${month}月`,
    hint: ly?.palace_name || '',
  }
})

const liuriCell = computed(() => {
  const lr = props.ziwei.liuri_liushi?.liuri
  if (!lr) return { label: '流日', value: '—', hint: '' }
  return {
    label: '流日',
    value: `${lr.branch}日`,
    hint: lr.palace_name || '',
  }
})

const cells = computed(() => [
  { key: 'dayun' as OverlayLayer, ...dayunCell.value },
  { key: 'liunian' as OverlayLayer, ...liunianCell.value },
  { key: 'liuyue' as OverlayLayer, ...liuyueCell.value },
  { key: 'liuri' as OverlayLayer, ...liuriCell.value },
])

function onSelect(layer: OverlayLayer) {
  emit('selectLayer', layer)
}
</script>

<template>
  <div class="yunxian-strip" data-testid="yunxian-summary-strip">
    <button
      v-for="cell in cells"
      :key="cell.key"
      type="button"
      class="yunxian-strip__cell"
      :class="{ 'is-active': activeLayer === cell.key }"
      :data-layer="cell.key"
      @click="onSelect(cell.key)"
    >
      <span class="yunxian-strip__label">{{ cell.label }}</span>
      <strong class="yunxian-strip__value">{{ cell.value }}</strong>
      <span v-if="cell.hint" class="yunxian-strip__hint">{{ cell.hint }}</span>
    </button>
  </div>
</template>

<style scoped>
.yunxian-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.yunxian-strip__cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border-soft, var(--border));
  background: var(--surface);
  cursor: pointer;
  text-align: left;
  font: inherit;
}

.yunxian-strip__cell:hover {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
}

.yunxian-strip__cell.is-active {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
}

.yunxian-strip__label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-3, #78716c);
}

.yunxian-strip__value {
  font-size: 15px;
  font-family: var(--font-cn);
  color: var(--brand-ink);
}

.yunxian-strip__hint {
  font-size: 11px;
  color: var(--text-3, #78716c);
}

@media (max-width: 640px) {
  .yunxian-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
