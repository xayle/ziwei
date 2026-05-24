<script setup lang="ts">
interface ChartSummaryStats {
  totalMainStars: number
  totalAuxStars: number
  totalTransforms: number
  luCount: number
  quanCount: number
  keCount: number
  jiCount: number
  brightStars: number
  weakStars: number
  shaCount: number
  jiStarCount: number
  patternsCount: number
}

defineProps<{
  stats: ChartSummaryStats | null
}>()
</script>

<template>
  <div v-if="stats" class="chart-summary-card">
    <div class="csc-row">
      <span class="csc-label">主星</span>
      <span class="csc-value">{{ stats.totalMainStars }}</span>
      <span class="csc-label">辅星</span>
      <span class="csc-value">{{ stats.totalAuxStars }}</span>
      <span class="csc-label">庙旺</span>
      <span class="csc-value csc-good">{{ stats.brightStars }}</span>
      <span class="csc-label">陷落</span>
      <span class="csc-value csc-bad">{{ stats.weakStars }}</span>
    </div>
    <div class="csc-row">
      <span class="csc-label">禄</span>
      <span class="csc-value csc-lu">{{ stats.luCount }}</span>
      <span class="csc-label">权</span>
      <span class="csc-value csc-quan">{{ stats.quanCount }}</span>
      <span class="csc-label">科</span>
      <span class="csc-value csc-ke">{{ stats.keCount }}</span>
      <span class="csc-label">忌</span>
      <span class="csc-value csc-ji">{{ stats.jiCount }}</span>
    </div>
    <div class="csc-row">
      <span class="csc-label">吉星</span>
      <span class="csc-value csc-good">{{ stats.jiStarCount }}</span>
      <span class="csc-label">煞星</span>
      <span class="csc-value csc-bad">{{ stats.shaCount }}</span>
      <span class="csc-label">格局</span>
      <span class="csc-value">{{ stats.patternsCount }}</span>
    </div>
  </div>
</template>

<style scoped>
.chart-summary-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 14px;
  background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  margin-top: 8px;
}

.csc-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.csc-label {
  font-size: 11px;
  color: var(--text-2);
}

.csc-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--font-mono);
  min-width: 18px;
  text-align: center;
}

.csc-good { color: #15803d; }
.csc-bad { color: #dc2626; }
.csc-lu { color: #15803d; }
.csc-quan { color: #d97706; }
.csc-ke { color: #2563eb; }
.csc-ji { color: #dc2626; }
</style>
