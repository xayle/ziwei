<script setup lang="ts">
import { ref } from 'vue'
import type { ForecastResultResponse } from '@/api/ziwei'

interface ForecastStats {
  good: number
  mid: number
  low: number
  avg: number
  best: { period: string; score: number } | null
  worst: { period: string; score: number } | null
}

interface ForecastMonthlyOverviewItem {
  index: number
  score: number
  level: 'good' | 'mid' | 'low'
  periodShort: string
}

const props = defineProps<{
  forecast: ForecastResultResponse
  forecastStats: ForecastStats
  forecastMonthlyOverview: ForecastMonthlyOverviewItem[]
  forecastRiskMonths: string[]
  forecastScoreColor: (score: number) => string
}>()

const expandedForecastMonth = ref<number | null>(null)

function toggleExpandedMonth(index: number) {
  expandedForecastMonth.value = expandedForecastMonth.value === index ? null : index
}

function monthLevel(score: number) {
  if (score >= 80) return 'fm-good'
  if (score >= 50) return 'fm-mid'
  return 'fm-low'
}
</script>

<template>
  <div v-if="forecast.monthly?.length" class="forecast-stats">
    <div class="forecast-stat-main">
      <span class="fs-label">年均评分</span>
      <span class="fs-value" :style="{ color: forecastScoreColor(forecastStats.avg) }">{{ forecastStats.avg }}</span>
    </div>
    <div class="forecast-stat-dist">
      <span class="fs-item good">吉月 <b>{{ forecastStats.good }}</b></span>
      <span class="fs-item mid">平月 <b>{{ forecastStats.mid }}</b></span>
      <span class="fs-item low">凶月 <b>{{ forecastStats.low }}</b></span>
    </div>
    <div v-if="forecastStats.best" class="forecast-stat-peak">
      <span class="fs-peak best">最佳：{{ forecastStats.best.period?.replace(/\(.+?\)/, '') }} <b>{{ forecastStats.best.score }}分</b></span>
      <span v-if="forecastStats.worst" class="fs-peak worst">注意：{{ forecastStats.worst.period?.replace(/\(.+?\)/, '') }} <b>{{ forecastStats.worst.score }}分</b></span>
    </div>
    <div v-if="forecastRiskMonths.length" class="forecast-risk-tags">
      <span class="frt-label">重点关注</span>
      <span v-for="item in forecastRiskMonths" :key="item" class="frt-item">{{ item }}</span>
    </div>
  </div>

  <div v-if="forecastMonthlyOverview.length" class="forecast-heatmap card">
    <h3 class="section-title">月度评分分布</h3>
    <div class="fhm-grid">
      <button
        v-for="bar in forecastMonthlyOverview"
        :key="bar.index"
        :class="['fhm-item', `fhm-${bar.level}`, { 'fhm-active': expandedForecastMonth === bar.index }]"
        @click="toggleExpandedMonth(bar.index)"
      >
        <span class="fhm-period">{{ bar.periodShort || `第${bar.index + 1}月` }}</span>
        <span class="fhm-score">{{ bar.score }}</span>
        <span class="fhm-bar"><i :style="{ width: `${bar.score}%` }"></i></span>
      </button>
    </div>
  </div>

  <div v-if="forecast.yearly" class="forecast-yearly card">
    <div class="fy-head">
      <span class="fy-gz">{{ forecast.yearly.ganzhi }}</span>
      <span class="fy-period">{{ forecast.yearly.period }}</span>
      <span v-if="forecast.yearly.score" class="fy-score" :style="{ color: forecastScoreColor(forecast.yearly.score) }">
        {{ forecast.yearly.score }}分
      </span>
    </div>
    <p v-if="forecast.yearly.overall" class="fy-overall">{{ forecast.yearly.overall }}</p>
    <div v-if="forecast.yearly.details && Object.keys(forecast.yearly.details).length" class="fy-details">
      <div v-for="(text, domain) in forecast.yearly.details" :key="domain" class="fyd-item">
        <span class="fyd-domain">{{ domain }}</span>
        <span class="fyd-text">{{ text }}</span>
      </div>
    </div>
    <div v-if="forecast.yearly.events?.length" class="fy-events">
      <div v-for="(ev, i) in forecast.yearly.events" :key="i" :class="['fye-item', `fye-${ev.level}`]" :title="ev.source || ''">
        <span class="fye-cat">{{ ev.category }}</span>
        <span class="fye-desc">{{ ev.description }}</span>
      </div>
    </div>
    <p v-if="forecast.yearly.advice" class="fy-advice">💡 {{ forecast.yearly.advice }}</p>
  </div>

  <div v-if="forecast.current_month" class="forecast-curmonth card">
    <div class="fcm-head">
      <span class="fcm-label">本月运势</span>
      <span class="fcm-gz">{{ forecast.current_month.ganzhi }}</span>
      <span v-if="forecast.current_month.score" class="fy-score" :style="{ color: forecastScoreColor(forecast.current_month.score) }">
        {{ forecast.current_month.score }}分
      </span>
    </div>
    <p v-if="forecast.current_month.overall" class="fy-overall">{{ forecast.current_month.overall }}</p>
    <p v-if="forecast.current_month.advice" class="fy-advice">💡 {{ forecast.current_month.advice }}</p>
  </div>

  <div v-if="forecast.monthly?.length" class="section-block">
    <h3 class="section-title">月度运势概览 <small class="forecast-month-note">(点击展开详情)</small></h3>
    <div class="forecast-monthly-grid">
      <div
        v-for="(month, mi) in forecast.monthly"
        :key="month.period"
        :class="['fm-item', monthLevel(month.score), { 'fm-expanded': expandedForecastMonth === mi }]"
        @click="toggleExpandedMonth(mi)"
      >
        <div class="fm-period">{{ month.period }}</div>
        <div class="fm-gz">{{ month.ganzhi }}</div>
        <div v-if="month.score" class="fm-score" :style="{ color: forecastScoreColor(month.score) }">{{ month.score }}</div>
        <div v-if="month.score" class="fm-score-bar"><i :style="{ width: `${Math.max(0, Math.min(100, Number(month.score))) || 0}%` }"></i></div>
        <div v-if="month.palace_name" class="fm-palace">{{ month.palace_name }}</div>
        <div v-if="month.overall" class="fm-overall">{{ month.overall }}</div>

        <template v-if="expandedForecastMonth === mi">
          <div v-if="month.details && Object.keys(month.details).length" class="fm-details">
            <div v-for="(text, domain) in month.details" :key="domain" class="fmd-item">
              <span class="fmd-domain">{{ domain }}</span>
              <span class="fmd-text">{{ text }}</span>
            </div>
          </div>
          <div v-if="month.events?.length" class="fm-events">
            <div v-for="(ev, ei) in month.events" :key="ei" :class="['fme-item', `fme-${ev.level}`]" :title="ev.source || ''">
              <span class="fme-cat">{{ ev.category }}</span>
              <span class="fme-desc">{{ ev.description }}</span>
            </div>
          </div>
          <p v-if="month.advice" class="fm-advice">💡 {{ month.advice }}</p>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forecast-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4);
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1px solid #86efac;
  border-radius: var(--radius-md);
  margin-bottom: var(--sp-5);
}

.forecast-stat-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-right: var(--sp-4);
  border-right: 1px solid #86efac;
}

.forecast-stat-main .fs-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
}

.forecast-stat-main .fs-value {
  font-size: var(--fs-2xl);
  font-weight: 800;
}

.forecast-stat-dist {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}

.forecast-stat-dist .fs-item {
  font-size: var(--fs-sm);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: #fff;
  border: 1px solid var(--border);
}

.forecast-stat-dist .fs-item b {
  font-weight: 700;
  margin-left: 4px;
}

.forecast-stat-dist .fs-item.good { color: #15803d; border-color: #86efac; }
.forecast-stat-dist .fs-item.mid { color: #d97706; border-color: #fcd34d; }
.forecast-stat-dist .fs-item.low { color: #dc2626; border-color: #fca5a5; }

.forecast-stat-peak {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-left: auto;
}

.forecast-stat-peak .fs-peak {
  font-size: var(--fs-xs);
  padding: 3px 8px;
  border-radius: 6px;
}

.forecast-stat-peak .fs-peak.best { background: #dcfce7; color: #166534; }
.forecast-stat-peak .fs-peak.worst { background: #fef2f2; color: #991b1b; }
.forecast-stat-peak .fs-peak b { font-weight: 700; margin-left: 3px; }

.forecast-risk-tags {
  width: 100%;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.frt-label { font-size: var(--fs-xs); color: var(--text-2); }

.frt-item {
  font-size: var(--fs-xs);
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 999px;
  padding: 3px 8px;
}

.forecast-heatmap { margin-bottom: var(--sp-4); padding: var(--sp-4); }

.fhm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}

.fhm-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  cursor: pointer;
}

.fhm-period { font-size: var(--fs-xs); color: var(--text-2); }
.fhm-score { font-size: var(--fs-sm); font-weight: 700; }

.fhm-bar {
  display: block;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0,0,0,.08);
  overflow: hidden;
}

.fhm-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: currentColor;
}

.fhm-good { color: #15803d; border-color: #86efac; }
.fhm-mid { color: #b45309; border-color: #fcd34d; }
.fhm-low { color: #b91c1c; border-color: #fca5a5; }
.fhm-active { box-shadow: 0 0 0 2px rgba(217,119,6,.2) inset; }

.forecast-yearly,
.forecast-curmonth { margin-bottom: var(--sp-4); }

.fy-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.fy-gz { font-size: var(--fs-xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.fy-period { font-size: var(--fs-sm); color: var(--text-3); }
.fy-score { font-size: var(--fs-sm); font-weight: 700; }
.fy-overall { font-size: var(--fs-md); color: var(--text); line-height: 1.7; margin-bottom: var(--sp-3); }
.fy-details { display: flex; flex-direction: column; gap: 6px; margin-bottom: var(--sp-3); }
.fyd-item { display: flex; gap: var(--sp-3); align-items: baseline; }
.fyd-domain { font-size: var(--fs-xs); padding: 1px 8px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 10px; color: var(--text-2); flex-shrink: 0; }
.fyd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; }
.fy-events { display: flex; flex-direction: column; gap: 5px; margin-bottom: var(--sp-3); }
.fye-item { display: flex; gap: 8px; align-items: center; padding: 5px 10px; border-radius: var(--radius-sm); background: var(--surface-2); }
.fye-high { border-left: 3px solid #dc2626; }
.fye-mid { border-left: 3px solid #d97706; }
.fye-low { border-left: 3px solid #64748b; }
.fye-cat { font-size: var(--fs-xs); padding: 1px 6px; background: var(--surface); border: 1px solid var(--border-md); border-radius: 8px; color: var(--text-2); flex-shrink: 0; }
.fye-desc { font-size: var(--fs-sm); color: var(--text); }
.fy-advice { font-size: var(--fs-sm); color: var(--accent-dark); background: rgba(217,119,6,.08); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); }

.fcm-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-3); flex-wrap: wrap; }
.fcm-label { font-size: var(--fs-xs); padding: 2px 8px; background: var(--accent); color: #fff; border-radius: 10px; font-weight: 600; }
.fcm-gz { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); }

.forecast-month-note { font-weight: 400; color: var(--text-3); font-size: var(--fs-sm); }

.forecast-monthly-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: var(--sp-3);
}

.fm-item {
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--border-md);
  cursor: pointer;
  transition: all var(--dur-fast);
}

.fm-good { border-left-color: #16a34a; }
.fm-mid { border-left-color: #d97706; }
.fm-low { border-left-color: #dc2626; }
.fm-period { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: 2px; }
.fm-gz { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.fm-score { font-size: var(--fs-lg); font-weight: 800; margin: 2px 0; }

.fm-score-bar {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(0,0,0,.08);
  overflow: hidden;
  margin: 2px 0 6px;
}

.fm-score-bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: currentColor;
}

.fm-palace { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: 3px; }
.fm-overall { font-size: var(--fs-xs); color: var(--text); line-height: 1.5; margin-top: 3px; }
.fm-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.fm-expanded { grid-column: 1 / -1; background: var(--surface); border-width: 2px; }
.fm-details { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); padding-top: var(--sp-3); border-top: 1px dashed var(--border); }
.fmd-item { display: flex; flex-direction: column; flex: 1 1 140px; }
.fmd-domain { font-size: var(--fs-xs); color: var(--accent); font-weight: 600; }
.fmd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }
.fm-events { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); }
.fme-item { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 10px; font-size: var(--fs-xs); }
.fme-强, .fme-item.fme-强 { background: rgba(239, 68, 68, 0.15); color: #b91c1c; }
.fme-中, .fme-item.fme-中 { background: rgba(245, 158, 11, 0.15); color: #b45309; }
.fme-弱, .fme-item.fme-弱 { background: rgba(59, 130, 246, 0.15); color: #1d4ed8; }
.fme-cat { font-weight: 600; }
.fme-desc { color: inherit; opacity: 0.9; }
.fm-advice { font-size: var(--fs-sm); color: var(--text-2); margin-top: var(--sp-3); padding: var(--sp-2); background: var(--surface-2); border-radius: var(--radius-sm); }
</style>