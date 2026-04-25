<script setup lang="ts">
interface TrendInfo {
  cls: string
  text: string
}

interface ZiweiSummaryCardData {
  lifePalace: string
  bodyPalace: string
  wuxingJu: string
  rulers: string
  dayun: string
  liunian: string
  yearlyScore: number | null
  yearlyTone: string
  liuyue: string
  liuyuePalace: string
  currentMonthScore: number | null
  liuyueTrend: TrendInfo
  liuyueTone: string
}

const props = defineProps<{
  summary: ZiweiSummaryCardData
}>()
</script>

<template>
  <div class="wb-chart-summary wb-chart-summary-ziwei">
    <div class="wb-csum-card">
      <div class="wb-csum-icon">🏮</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">命宫 / 身宫</div>
        <div class="wb-csum-value">{{ props.summary.lifePalace }}</div>
        <div class="wb-csum-sub">身宫：{{ props.summary.bodyPalace }}</div>
      </div>
      <div class="wb-csum-tip">命宫与身宫用于概览先天主轴与后天行为重心，数据来自紫微排盘基础宫位。</div>
    </div>

    <div class="wb-csum-card">
      <div class="wb-csum-icon">✨</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">五行局 / 命主身主</div>
        <div class="wb-csum-value">{{ props.summary.wuxingJu }}</div>
        <div class="wb-csum-sub">{{ props.summary.rulers }}</div>
      </div>
      <div class="wb-csum-tip">五行局、命主、身主来自紫微主盘核心设定，用于判断整盘的基础结构与主导星曜。</div>
    </div>

    <div class="wb-csum-card" :class="props.summary.yearlyTone">
      <div class="wb-csum-icon">🛤️</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">当前大限 / 流年</div>
        <div class="wb-csum-value">{{ props.summary.dayun }}</div>
        <div class="wb-csum-sub">
          {{ props.summary.liunian }}
          <span v-if="props.summary.yearlyScore != null" class="wb-csum-score">{{ props.summary.yearlyScore }}分</span>
        </div>
      </div>
      <div class="wb-csum-tip">流年评分取自紫微 forecast.yearly.score；卡片底色按高/中/低分段显示。</div>
    </div>

    <div class="wb-csum-card" :class="props.summary.liuyueTone">
      <div class="wb-csum-icon">📅</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">本月流月</div>
        <div class="wb-csum-value">{{ props.summary.liuyue }}</div>
        <div class="wb-csum-sub">
          落宫：{{ props.summary.liuyuePalace }}
          <span v-if="props.summary.currentMonthScore != null" class="wb-csum-score">{{ props.summary.currentMonthScore }}分</span>
        </div>
        <div class="wb-csum-trend" :class="`is-${props.summary.liuyueTrend.cls}`">{{ props.summary.liuyueTrend.text }} vs 月均</div>
      </div>
      <div class="wb-csum-tip">本月趋势为当前月分数对比全年月均分，帮助快速识别本月偏强或偏弱。</div>
    </div>
  </div>
</template>

<style scoped>
.wb-chart-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 4px;
}
.wb-csum-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  transition: box-shadow .15s;
  position: relative;
  overflow: visible;
}
.wb-csum-card:hover { box-shadow: 0 4px 16px rgba(15,23,42,.08); }
.wb-csum-card.c-good { border-color: #16a34a; background: #f0fdf4; }
.wb-csum-card.c-warn { border-color: #f59e0b; background: #fffbeb; }
.wb-csum-card.c-bad  { border-color: #dc2626; background: #fff5f5; }
.wb-csum-icon {
  font-size: 20px;
  line-height: 1;
  margin-top: 2px;
  flex-shrink: 0;
}
.wb-csum-body { min-width: 0; }
.wb-csum-label {
  font-size: 10px;
  color: var(--text-3);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: .05em;
  margin-bottom: 3px;
}
.wb-csum-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wb-chart-summary-ziwei .wb-csum-value { font-size: 16px; }
.wb-csum-sub {
  font-size: 11px;
  color: var(--text-3);
  margin-top: 4px;
  font-family: var(--font-cn);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wb-csum-score {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(99,102,241,.10);
  color: #4f46e5;
  font-size: 10px;
  font-weight: 700;
  vertical-align: middle;
}
.wb-csum-trend {
  margin-top: 6px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-cn);
}
.wb-csum-trend.is-up { color: #16a34a; }
.wb-csum-trend.is-down { color: #dc2626; }
.wb-csum-trend.is-flat { color: var(--text-3); }
.wb-csum-tip {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: calc(100% + 8px);
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(15,23,42,.94);
  color: #fff;
  font-size: 11px;
  line-height: 1.6;
  font-family: var(--font-cn);
  box-shadow: 0 10px 24px rgba(15,23,42,.18);
  opacity: 0;
  pointer-events: none;
  transform: translateY(4px);
  transition: opacity .14s, transform .14s;
  z-index: 12;
}
.wb-csum-card:hover .wb-csum-tip {
  opacity: 1;
  transform: translateY(0);
}

@media print {
  .wb-chart-summary { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
  .wb-csum-card { border: 1px solid #ccc; padding: 10px; border-radius: 6px; flex: 1; min-width: 200px; }
  .wb-csum-card .wb-csum-tip { display: none; }
}

@media (max-width: 1280px) {
  .wb-chart-summary { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .wb-chart-summary { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .wb-csum-card { padding: 10px 12px; }
  .wb-csum-value { font-size: 16px; }
  .wb-csum-sub { white-space: normal; }
}

@media (max-width: 560px) {
  .wb-chart-summary { grid-template-columns: 1fr; }
  .wb-csum-card { gap: 8px; }
}
</style>
