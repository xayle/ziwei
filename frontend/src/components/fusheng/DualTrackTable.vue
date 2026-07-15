<script setup lang="ts">
import { formatDualTrackCaseLabel } from '@/utils/buildEngineTrustDisplay'

export type DualTrackReferenceRow = {
  id: string
  topic?: string
  recorded: string
  engine: string
  note?: string
}

withDefaults(defineProps<{
  rows: DualTrackReferenceRow[]
  title?: string
  variant?: 'reference' | 'simple'
}>(), {
  title: '执业双轨对照表',
  variant: 'reference',
})

function caseLabel(row: DualTrackReferenceRow): string {
  return row.topic || formatDualTrackCaseLabel(row.id)
}
</script>

<template>
  <div class="dual-track-table" data-testid="dual-track-table">
    <h3 v-if="title">{{ title }}</h3>
    <p v-if="variant === 'reference'" class="dual-track-table__caption">
      以下为典籍与引擎对照样例，非当前命盘即时计算。
    </p>
    <p class="dual-track-table__scroll-hint" data-testid="dual-track-scroll-hint">
      窄屏可左右滑动查看对照表。
    </p>
    <div class="dual-track-table__scroll" tabindex="0" role="region" aria-label="双轨对照表">
      <table class="dual-track-table__grid">
        <thead>
          <tr>
            <th>用例</th>
            <th>古籍/对照</th>
            <th>引擎</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" :data-case-id="row.id">
            <td>{{ caseLabel(row) }}</td>
            <td>{{ row.recorded }}</td>
            <td>{{ row.engine }}</td>
            <td>{{ row.note || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!rows.length" class="dual-track-table__empty">暂无双轨登记项。</p>
  </div>
</template>

<style scoped>
.dual-track-table h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: var(--brand-gold-dark);
}

.dual-track-table__caption {
  margin: 0 0 10px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.5;
}

.dual-track-table__scroll-hint {
  display: none;
  margin: 0 0 8px;
  color: var(--text-3);
  font-size: 12px;
}

.dual-track-table__scroll {
  min-width: 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.dual-track-table__grid {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;
  font-size: 13px;
}

@media (max-width: 640px) {
  .dual-track-table__scroll-hint {
    display: block;
  }
}

.dual-track-table__grid th,
.dual-track-table__grid td {
  border: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}

.dual-track-table__grid th {
  background: var(--inset-tint);
  color: var(--brand-gold-dark);
}

.dual-track-table__empty {
  margin: 8px 0 0;
  color: var(--text-3);
  font-size: 13px;
  font-style: italic;
}
</style>
