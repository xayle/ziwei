<script setup lang="ts">
import type { PalaceStructuredRow } from '@/utils/buildEngineTrustDisplay'

withDefaults(defineProps<{
  rows: PalaceStructuredRow[]
  emptyMessage?: string
  /** 命宫/财帛/官禄等优先展示 */
  priorityNames?: string[]
}>(), {
  emptyMessage: '暂无结构化宫论，请确认引擎返回 analysis_structured。',
  priorityNames: () => ['命宫', '财帛', '官禄', '夫妻', '迁移', '福德'],
})

function sortRows(rows: PalaceStructuredRow[], priority: string[]) {
  const rank = new Map(priority.map((name, idx) => [name, idx]))
  return [...rows].sort((a, b) => {
    const ra = rank.get(a.name) ?? 99
    const rb = rank.get(b.name) ?? 99
    if (ra !== rb) return ra - rb
    return a.name.localeCompare(b.name, 'zh-CN')
  })
}
</script>

<template>
  <div class="palace-grid" data-testid="palace-analysis-grid">
    <article v-for="row in sortRows(rows, priorityNames)" :key="row.name" class="palace-grid__row">
      <header class="palace-grid__head">
        <h3>{{ row.name }}</h3>
        <span v-for="tag in row.tags" :key="`${row.name}-${tag}`" class="palace-grid__tag">{{ tag }}</span>
      </header>
      <p class="palace-grid__conclusion"><strong>结论</strong> — {{ row.conclusion || '缺失' }}</p>
      <p v-if="row.explanation" class="palace-grid__body">{{ row.explanation }}</p>
      <p v-if="row.suggestion" class="palace-grid__hint">建议：{{ row.suggestion }}</p>
    </article>
    <p v-if="!rows.length" class="palace-grid__empty">{{ emptyMessage }}</p>
  </div>
</template>

<style scoped>
.palace-grid {
  display: grid;
  gap: 14px;
}

.palace-grid__row {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
}

.palace-grid__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.palace-grid__head h3 {
  margin: 0;
  font-family: var(--font-cn);
  font-size: 15px;
  color: var(--brand-ink);
}

.palace-grid__tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.palace-grid__conclusion,
.palace-grid__body {
  margin: 0 0 6px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text);
}

.palace-grid__hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-2);
}

.palace-grid__empty {
  margin: 0;
  color: var(--text-3);
  font-size: 14px;
  font-style: italic;
}
</style>
