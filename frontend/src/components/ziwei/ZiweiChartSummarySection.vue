<script setup lang="ts">
import ZiweiChartQuickInsights from './ZiweiChartQuickInsights.vue'
import ZiweiChartSummaryCard from './ZiweiChartSummaryCard.vue'

type ChartQuickInsightItem = {
  label: string
  value: string
  sub?: string
  cls?: string
}

type ChartSummaryStats = {
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

const props = defineProps<{
  quickInsights: ChartQuickInsightItem[]
  summaryStats: ChartSummaryStats | null
}>()
</script>

<template>
  <div v-if="props.quickInsights.length || props.summaryStats" class="chart-summary-section">
    <ZiweiChartQuickInsights :items="props.quickInsights" />
    <ZiweiChartSummaryCard :stats="props.summaryStats" />
  </div>
</template>

<style scoped>
.chart-summary-section {
  display: grid;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}

.chart-summary-section :deep(.chart-quick-insights) {
  margin-bottom: 0;
}

.chart-summary-section :deep(.chart-summary-card) {
  margin-top: 0;
}

@media (min-width: 1180px) {
  .chart-summary-section {
    grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
    align-items: start;
  }
}
</style>
