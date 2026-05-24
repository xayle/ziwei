<script setup lang="ts">
import type { ForecastResultResponse, LiunianResponse } from '@/api/ziwei'

defineOptions({ inheritAttrs: false })

type LiunianSihuaWithPalaceItem = {
  star: string
  transform: string
  palaceName?: string
}

const props = defineProps<{
  liunian: LiunianResponse | null
  forecast: ForecastResultResponse | null
  currentYear: number
  currentMonth: number
  currentDayunGz?: string | null
  branches: string[]
  zodiacAnimals: string[]
  showYearPicker: boolean
  yearPickerList: number[]
  liunianSihuaWithPalace: LiunianSihuaWithPalaceItem[]
  forecastScoreColor: (score: number) => string
  tfColorStyle: (transform: string) => string | Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'select-year', year: number): void
  (e: 'toggle-year-picker'): void
  (e: 'close-year-picker'): void
}>()

function getZodiac(yearGz: string) {
  const branch = yearGz?.charAt(1) || ''
  const index = props.branches.indexOf(branch)
  return index >= 0 ? props.zodiacAnimals[index] : '-'
}
</script>

<template>
  <template v-if="liunian">
    <div class="liunian-toolbar">
      <div class="liunian-year-picker">
        <button class="lyp-btn" title="上一年" @click="emit('select-year', liunian.year - 1)">◀</button>
        <button class="lyp-current" @click="emit('toggle-year-picker')">
          {{ liunian.year }}年
          <span v-if="liunian.year === currentYear" class="lyp-cur-badge">今年</span>
        </button>
        <button class="lyp-btn" title="下一年" @click="emit('select-year', liunian.year + 1)">▶</button>
        <button
          v-if="liunian.year !== currentYear"
          class="lyp-reset"
          title="回到今年"
          @click="emit('select-year', currentYear)"
        >
          📍 今年
        </button>
      </div>

      <div v-if="showYearPicker" class="year-picker-panel">
        <div class="ypp-header">
          <span>选择年份</span>
          <button class="ypp-close" @click="emit('close-year-picker')">✕</button>
        </div>
        <div class="ypp-grid">
          <button
            v-for="yr in yearPickerList"
            :key="yr"
            :class="['ypp-item', { 'ypp-selected': yr === liunian.year, 'ypp-current': yr === currentYear }]"
            @click="emit('select-year', yr)"
          >
            {{ yr }}
          </button>
        </div>
      </div>
    </div>

    <div class="liunian-hero card">
      <div class="lnh-left">
        <div class="lnh-gz">
          {{ liunian.year_gz }}年
          <span v-if="liunian.year === currentYear" class="liunian-cur-badge">今年</span>
        </div>
        <div class="lnh-sub">{{ liunian.year }}年</div>
        <div class="lnh-meta">
          <span v-if="liunian.life_palace_branch >= 0">
            流年命宫 <b>{{ branches[liunian.life_palace_branch] }}宫</b>
          </span>
          <span v-if="currentDayunGz">所在大运 <b>{{ currentDayunGz }}</b></span>
        </div>
        <div class="lnh-attrs">
          <div class="la-item">
            <span class="la-label">年干</span>
            <span class="la-value">{{ liunian.year_gz?.charAt(0) }}</span>
          </div>
          <div class="la-item">
            <span class="la-label">年支</span>
            <span class="la-value">{{ liunian.year_gz?.charAt(1) }}</span>
          </div>
          <div class="la-item">
            <span class="la-label">生肖</span>
            <span class="la-value">{{ getZodiac(liunian.year_gz) }}</span>
          </div>
          <div class="la-item">
            <span class="la-label">太岁</span>
            <span class="la-value la-value-sm">{{ liunian.year_gz?.charAt(1) }}年</span>
          </div>
        </div>
      </div>

      <div v-if="forecast?.yearly?.score" class="lnh-score-ring">
        <svg viewBox="0 0 80 80" class="score-ring-svg">
          <circle cx="40" cy="40" r="34" fill="none" stroke="var(--surface-2)" stroke-width="7" />
          <circle
            cx="40"
            cy="40"
            r="34"
            fill="none"
            :stroke="forecastScoreColor(forecast.yearly.score)"
            stroke-width="7"
            stroke-linecap="round"
            :stroke-dasharray="`${(forecast.yearly.score / 100) * 213.6} 213.6`"
            transform="rotate(-90 40 40)"
          />
          <text
            x="40"
            y="45"
            text-anchor="middle"
            font-size="20"
            font-weight="bold"
            :fill="forecastScoreColor(forecast.yearly.score)"
          >
            {{ forecast.yearly.score }}
          </text>
        </svg>
        <div class="score-ring-label">年度评分</div>
      </div>
    </div>

    <div v-if="forecast?.yearly" class="liunian-forecast-full card">
      <h3 class="section-title">年度运势详情</h3>
      <p v-if="forecast.yearly.overall" class="lfy-overall">{{ forecast.yearly.overall }}</p>
      <div v-if="forecast.yearly.details && Object.keys(forecast.yearly.details).length" class="lfy-details">
        <div v-for="(text, domain) in forecast.yearly.details" :key="String(domain)" class="lfyd-item">
          <span class="lfyd-domain">{{ domain }}</span>
          <span class="lfyd-text">{{ text }}</span>
        </div>
      </div>
      <div v-if="forecast.yearly.events?.length" class="lfy-events">
        <div v-for="(ev, ei) in forecast.yearly.events" :key="ei" :class="['lfye-item', `fye-${ev.level}`]" :title="ev.source || ''">
          <span class="fye-cat">{{ ev.category }}</span>
          <span class="fye-desc">{{ ev.description }}</span>
        </div>
      </div>
      <p v-if="forecast.yearly.advice" class="lfy-advice">💡 {{ forecast.yearly.advice }}</p>
    </div>

    <div v-if="liunianSihuaWithPalace.length" class="liunian-sihua-section card">
      <h3 class="section-title">流年四化</h3>
      <div class="liunian-sihua-grid lsg-enhanced">
        <div v-for="item in liunianSihuaWithPalace" :key="item.star" class="liunian-sihua-card lsc-enhanced">
          <div class="lsc-top">
            <span class="lss-star">{{ item.star }}</span>
            <span class="lss-tf" :style="tfColorStyle(item.transform)">{{ item.transform }}</span>
          </div>
          <span v-if="item.palaceName" class="lss-palace">{{ item.palaceName }}</span>
        </div>
      </div>
    </div>

    <div v-if="forecast?.monthly?.length" class="liunian-monthly-chart card">
      <h3 class="section-title">十二月运势概览</h3>
      <div class="lmc-bars">
        <div v-for="(month, idx) in forecast.monthly" :key="idx" :class="['lmc-col', { 'lmc-cur': liunian.year === currentYear && idx + 1 === currentMonth }]">
          <div class="lmc-bar-wrap">
            <span v-if="month.score" class="lmc-score">{{ month.score }}</span>
            <div
              class="lmc-bar"
              :style="{ height: `${month.score ? Math.max(6, month.score) : 6}%`, background: month.score ? forecastScoreColor(month.score) : 'var(--border)' }"
            ></div>
          </div>
          <div class="lmc-label">{{ month.ganzhi || `${idx + 1}月` }}</div>
        </div>
      </div>
    </div>

    <div v-if="liunian.year === currentYear && forecast?.current_month" class="liunian-curmonth card">
      <div class="lcm-head">
        <span class="lcm-badge">本月</span>
        <span class="lcm-gz">{{ forecast.current_month.ganzhi }}</span>
        <span class="lcm-period">{{ forecast.current_month.period }}</span>
        <span v-if="forecast.current_month.score" class="lcm-score" :style="{ color: forecastScoreColor(forecast.current_month.score) }">
          {{ forecast.current_month.score }}分
        </span>
      </div>
      <p v-if="forecast.current_month.overall" class="lcm-overall">{{ forecast.current_month.overall }}</p>
      <div v-if="forecast.current_month.details && Object.keys(forecast.current_month.details).length" class="lfy-details">
        <div v-for="(text, domain) in forecast.current_month.details" :key="String(domain)" class="lfyd-item">
          <span class="lfyd-domain">{{ domain }}</span>
          <span class="lfyd-text">{{ text }}</span>
        </div>
      </div>
      <p v-if="forecast.current_month.advice" class="lcm-advice">💡 {{ forecast.current_month.advice }}</p>
    </div>
  </template>

  <p v-else class="muted">无流年数据</p>
</template>

<style scoped>
.liunian-toolbar {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: 8px;
}
.liunian-year-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}
.lyp-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.lyp-btn:hover {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.lyp-current {
  padding: 6px 16px;
  border: 2px solid var(--primary);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-md);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.lyp-current:hover { background: var(--primary-bg); }
.lyp-cur-badge {
  font-size: 10px;
  padding: 1px 4px;
  background: var(--primary);
  color: #fff;
  border-radius: 3px;
}
.lyp-reset {
  padding: 6px 10px;
  border: 1px solid var(--green);
  border-radius: 6px;
  background: var(--green);
  color: #fff;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: all 0.2s;
}
.lyp-reset:hover { filter: brightness(1.1); }
.year-picker-panel {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 320px;
  max-height: 300px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  overflow: hidden;
}
.ypp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}
.ypp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
  font-size: 14px;
}
.ypp-close:hover { color: var(--danger); }
.ypp-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  padding: 8px;
  max-height: 240px;
  overflow-y: auto;
}
.ypp-item {
  padding: 6px 4px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: var(--fs-sm);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
}
.ypp-item:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}
.ypp-item.ypp-selected {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.ypp-item.ypp-current {
  border-color: var(--green);
  font-weight: 600;
}
.ypp-item.ypp-current:not(.ypp-selected) { background: rgba(34, 197, 94, 0.1); }
.liunian-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.lnh-left { flex: 1; min-width: 0; }
.lnh-gz {
  font-size: var(--fs-2xl);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}
.liunian-cur-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: #dc2626;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
}
.lnh-sub { font-size: var(--fs-md); color: var(--text-2); margin-top: var(--sp-1); }
.lnh-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.lnh-meta b { color: var(--text); font-weight: 600; }
.lnh-attrs {
  display: flex;
  gap: var(--sp-4);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-top: var(--sp-3);
  flex-wrap: wrap;
}
.la-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}
.la-label { font-size: var(--fs-xs); color: var(--text-3); }
.la-value { font-size: var(--fs-lg); font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.la-value-sm { font-size: var(--fs-sm); }
.lnh-score-ring {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-1);
}
.score-ring-svg { width: 84px; height: 84px; }
.score-ring-label { font-size: var(--fs-xs); color: var(--text-3); text-align: center; }
.liunian-forecast-full { margin-bottom: var(--sp-4); }
.lfy-overall {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.7;
  margin-bottom: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.lfy-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
@media (max-width: 480px) {
  .lfy-details { grid-template-columns: 1fr; }
}
.lfyd-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.lfyd-domain {
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--text-3);
  letter-spacing: 0.04em;
}
.lfyd-text { font-size: var(--fs-sm); color: var(--text); line-height: 1.5; }
.lfy-events {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--sp-3);
}
.lfye-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  padding: 6px var(--sp-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}
.fye-high { border-left: 3px solid #dc2626; }
.fye-mid { border-left: 3px solid #d97706; }
.fye-low { border-left: 3px solid #64748b; }
.fye-cat {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: 8px;
  color: var(--text-2);
  flex-shrink: 0;
}
.fye-desc { font-size: var(--fs-sm); color: var(--text); }
.lfy-advice {
  font-size: var(--fs-sm);
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  padding: var(--sp-3);
  margin: 0;
}
.liunian-sihua-section { margin-bottom: var(--sp-4); }
.liunian-sihua-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.liunian-sihua-card {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.lss-star { font-size: var(--fs-md); font-weight: 600; font-family: var(--font-cn); }
.lss-tf { font-size: var(--fs-sm); font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.lsg-enhanced { gap: var(--sp-3); }
.lsc-enhanced {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: var(--sp-3);
  min-width: 80px;
}
.lsc-top { display: flex; align-items: center; gap: var(--sp-2); }
.lss-palace { font-size: var(--fs-xs); color: var(--text-3); }
.liunian-monthly-chart { margin-bottom: var(--sp-4); }
.lmc-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 110px;
  padding-top: var(--sp-2);
  padding-bottom: 28px;
  position: relative;
}
.lmc-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  position: relative;
}
.lmc-col.lmc-cur .lmc-bar { outline: 2px solid var(--accent); outline-offset: 1px; }
.lmc-col.lmc-cur .lmc-label { color: var(--accent); font-weight: 700; }
.lmc-bar-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 80px;
  gap: 2px;
}
.lmc-bar {
  width: 100%;
  border-radius: 3px 3px 0 0;
  min-height: 6px;
  transition: height 0.3s ease;
}
.lmc-score {
  font-size: 9px;
  color: var(--text-3);
  line-height: 1;
  text-align: center;
}
.lmc-label {
  position: absolute;
  bottom: 0;
  font-size: 9px;
  color: var(--text-3);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}
.liunian-curmonth {
  margin-bottom: var(--sp-4);
  border-left: 3px solid var(--accent);
}
.lcm-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
  flex-wrap: wrap;
}
.lcm-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: #dc2626;
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}
.lcm-gz {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}
.lcm-period { font-size: var(--fs-sm); color: var(--text-2); flex: 1; }
.lcm-score { font-size: var(--fs-md); font-weight: 700; }
.lcm-overall {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}
.lcm-advice {
  font-size: var(--fs-sm);
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  margin: var(--sp-2) 0 0;
}
</style>
