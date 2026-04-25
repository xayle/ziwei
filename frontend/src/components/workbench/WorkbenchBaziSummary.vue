<script setup lang="ts">
interface TrendInfo {
  cls: string
  text: string
}

interface BaziSummaryCardData {
  dayunGz: string
  dayunYearsLeft: number | null
  lyAnnualScore: number | null
  lyGz: string
  lyShishen: string
  lyTrend: TrendInfo
  lyueLuck: string
  lyueGz: string
  lyueTrend: TrendInfo
  balanceTone: string
  balanceScore: number | null
  strongList: string
  weakList: string
  balanceText: string
}

const props = defineProps<{
  summary: BaziSummaryCardData
  currentYear: number
}>()

function annualTone(score: number | null) {
  if (score == null) return ''
  if (score >= 80) return 'c-good'
  if (score >= 60) return 'c-warn'
  return 'c-bad'
}

function monthTone(luck: string) {
  if (luck === '吉') return 'c-good'
  if (luck === '凶') return 'c-bad'
  return ''
}
</script>

<template>
  <div class="wb-chart-summary">
    <div class="wb-csum-card">
      <div class="wb-csum-icon">☯</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">当前大运</div>
        <div class="wb-csum-value">{{ props.summary.dayunGz }}</div>
        <div v-if="props.summary.dayunYearsLeft != null" class="wb-csum-sub">剩 {{ props.summary.dayunYearsLeft }} 年</div>
      </div>
      <div class="wb-csum-tip">当前大运按当前年份落入的大运区间计算；剩余年数为该区间结束前年数。</div>
    </div>

    <div class="wb-csum-card" :class="annualTone(props.summary.lyAnnualScore)">
      <div class="wb-csum-icon">🌀</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">{{ props.currentYear }} 流年</div>
        <div class="wb-csum-value">{{ props.summary.lyGz }}</div>
        <div v-if="props.summary.lyShishen" class="wb-csum-sub">
          {{ props.summary.lyShishen }}
          <span v-if="props.summary.lyAnnualScore != null" class="wb-csum-score">{{ props.summary.lyAnnualScore }}分</span>
        </div>
        <div v-if="props.summary.lyAnnualScore != null" class="wb-csum-trend" :class="`is-${props.summary.lyTrend.cls}`">
          {{ props.summary.lyTrend.text }} vs 去年
        </div>
      </div>
      <div class="wb-csum-tip">流年分数取自 `liunian_detail.annual_score`；趋势为本年对比上一年差值。</div>
    </div>

    <div class="wb-csum-card" :class="monthTone(props.summary.lyueLuck)">
      <div class="wb-csum-icon">🌙</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">本月流月</div>
        <div class="wb-csum-value">{{ props.summary.lyueGz }}</div>
        <div v-if="props.summary.lyueLuck" class="wb-csum-sub">{{ props.summary.lyueLuck }}</div>
        <div class="wb-csum-trend" :class="`is-${props.summary.lyueTrend.cls}`">{{ props.summary.lyueTrend.text }} vs 上月</div>
      </div>
      <div class="wb-csum-tip">流月趋势以吉/平/凶做序位比较，仅用于快速观察本月相较上月的变化方向。</div>
    </div>

    <div class="wb-csum-card" :class="props.summary.balanceTone">
      <div class="wb-csum-icon">⚖</div>
      <div class="wb-csum-body">
        <div class="wb-csum-label">五行平衡</div>
        <div v-if="props.summary.balanceScore != null" class="wb-csum-value">{{ props.summary.balanceScore }}<span class="wb-csum-unit">分</span></div>
        <div class="wb-csum-sub">旺：{{ props.summary.strongList }} ｜ 弱：{{ props.summary.weakList }}</div>
        <div v-if="props.summary.balanceText" class="wb-csum-trend is-flat">{{ props.summary.balanceText }}</div>
      </div>
      <div class="wb-csum-tip">五行平衡分数越高表示结构越均衡；旺/弱列表来自五行强弱判定结果。</div>
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
.wb-csum-unit { font-size: 12px; font-weight: 400; color: var(--text-3); margin-left: 2px; }
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
