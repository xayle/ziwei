<script setup lang="ts">
import { ref } from 'vue'
import type { LiuyueItem, PeriodForecastResponse } from '@/api/ziwei'

interface LiuyueRow {
  month: LiuyueItem
  forecast: PeriodForecastResponse | null
}

interface LiuyueSummary {
  total: number
  withSihua: number
  withForecast: number
  avg: number
  riskMonths: string[]
}

const props = defineProps<{
  liuyueRows: LiuyueRow[]
  liuyueSummary: LiuyueSummary
  currentYear: number
  currentMonth: number
  liunianYear?: number | null
  forecastScoreColor: (score: number) => string
  tfColorStyle: (transform: string) => string | Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'locate-current'): void
}>()

const expandedLiuyue = ref<number | null>(null)

function isCurrentMonth(month: number) {
  return month === props.currentMonth && props.liunianYear === props.currentYear
}

function toggleLiuyue(idx: number) {
  expandedLiuyue.value = expandedLiuyue.value === idx ? null : idx
}

function handleLocateCurrent() {
  emit('locate-current')
}
</script>

<template>
  <div v-if="liuyueRows.length">
    <div class="liuyue-toolbar">
      <div class="liuyue-stats">
        <span class="lys-item">共 <b>{{ liuyueSummary.total }}</b> 月</span>
        <span class="lys-item">有四化 <b>{{ liuyueSummary.withSihua }}</b></span>
        <span v-if="liuyueSummary.withForecast" class="lys-item">有运势 <b>{{ liuyueSummary.withForecast }}</b></span>
      </div>
      <button v-if="liunianYear === currentYear" class="liuyue-locate-btn" title="定位到本月" @click="handleLocateCurrent">
        📍 定位本月
      </button>
    </div>

    <div class="liuyue-summary-cards">
      <div class="lysc-item">
        <span class="lysc-label">运势均分</span>
        <span class="lysc-value" :style="{ color: forecastScoreColor(liuyueSummary.avg || 50) }">{{ liuyueSummary.avg || '-' }}</span>
      </div>
      <div class="lysc-item">
        <span class="lysc-label">重点月份</span>
        <span class="lysc-value">{{ liuyueSummary.riskMonths.length ? liuyueSummary.riskMonths.join('、') : '整体平稳' }}</span>
      </div>
    </div>

    <div class="liuyue-quick-nav">
      <button
        v-for="(row, idx) in liuyueRows"
        :key="row.month.month"
        :class="['lyq-btn', { 'lyq-cur': isCurrentMonth(row.month.month), 'lyq-active': expandedLiuyue === idx }]"
        @click="toggleLiuyue(idx)"
      >
        {{ row.month.month_name?.replace('月', '') || row.month.month }}
      </button>
    </div>

    <div class="liuyue-grid">
      <div
        v-for="(row, idx) in liuyueRows"
        :key="row.month.month"
        :class="['liuyue-item', { 'liuyue-expanded': expandedLiuyue === idx, 'liuyue-cur': isCurrentMonth(row.month.month) }]"
        @click="toggleLiuyue(idx)"
      >
        <div class="liuyue-head">
          <span class="liuyue-month">{{ row.month.month_name }}</span>
          <span class="liuyue-gz">{{ row.month.month_gz }}</span>
          <span v-if="isCurrentMonth(row.month.month)" class="liuyue-cur-badge">本月</span>
          <span class="liuyue-expand-icon">{{ expandedLiuyue === idx ? '▴' : '▾' }}</span>
        </div>
        <div class="liuyue-palace">{{ row.month.palace_name }}</div>
        <div v-if="Object.keys(row.month.sihua).length" class="liuyue-sihua">
          <span
            v-for="(val, star) in row.month.sihua"
            :key="star"
            class="pc-tf liuyue-tf"
            :style="tfColorStyle(val)"
          >
            {{ star }}{{ val.slice(1) }}
          </span>
        </div>
        <div v-if="expandedLiuyue === idx && row.forecast" class="liuyue-detail">
          <div v-if="row.forecast.events?.length" class="liuyue-events">
            <div v-for="(ev, ei) in row.forecast.events" :key="ei" class="liuyue-event">
              <span class="liuyue-ev-cat">{{ ev.category }}</span>
              <span class="liuyue-ev-desc">{{ ev.description }}</span>
            </div>
          </div>
          <div v-if="row.forecast.details && Object.keys(row.forecast.details).length" class="liuyue-dimensions">
            <div v-for="(text, domain) in row.forecast.details" :key="domain" class="liuyue-dim">
              <span class="liuyue-dim-label">{{ domain }}</span>
              <span class="liuyue-dim-text">{{ text }}</span>
            </div>
          </div>
          <p v-if="row.forecast.advice" class="liuyue-advice">💡 {{ row.forecast.advice }}</p>
          <p v-if="row.forecast.overall" class="liuyue-overall">{{ row.forecast.overall }}</p>
          <div v-if="row.forecast.score" class="liuyue-score">
            运势评分：<span :style="{ color: forecastScoreColor(row.forecast.score || 50) }">{{ row.forecast.score }}分</span>
          </div>
        </div>
        <div v-else-if="expandedLiuyue === idx" class="liuyue-detail">
          <p class="muted">暂无该月运势详情</p>
        </div>
      </div>
    </div>
  </div>
  <p v-else class="muted">无流月数据</p>
</template>

<style scoped>
.liuyue-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: 8px;
}

.liuyue-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
  flex: 1;
}

.liuyue-stats .lys-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.liuyue-stats .lys-item b {
  font-weight: 700;
  color: var(--accent);
}

.liuyue-locate-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--primary);
  color: #fff;
  font-size: var(--fs-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.liuyue-locate-btn:hover {
  filter: brightness(1.1);
}

.liuyue-summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}

.lysc-item {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.lysc-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
}

.lysc-value {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}

.liuyue-quick-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
}

.lyq-btn {
  padding: 5px 10px;
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}

.lyq-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.lyq-btn.lyq-cur {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
  font-weight: 600;
}

.lyq-btn.lyq-active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.liuyue-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--sp-3);
}

.liuyue-item {
  cursor: pointer;
  transition: all var(--dur-fast);
  padding: var(--sp-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.liuyue-item:hover {
  border-color: var(--accent);
}

.liuyue-cur {
  border-color: #ea580c !important;
  background: rgba(234, 88, 12, 0.06) !important;
}

.liuyue-expanded {
  grid-column: 1 / -1;
  border-color: var(--accent);
  background: rgba(217, 119, 6, 0.04);
}

.liuyue-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}

.liuyue-month {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.liuyue-gz {
  font-size: var(--fs-sm);
  color: var(--text-3);
}

.liuyue-cur-badge {
  background: #ea580c;
  color: #fff;
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.liuyue-expand-icon {
  margin-left: auto;
  font-size: 10px;
  color: var(--text-3);
}

.liuyue-palace {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin-bottom: var(--sp-2);
}

.liuyue-sihua {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.liuyue-tf {
  font-size: var(--fs-xs);
}

.liuyue-detail {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
}

.liuyue-events {
  margin-bottom: var(--sp-3);
}

.liuyue-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.liuyue-ev-cat {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: 8px;
  color: var(--text-2);
  flex-shrink: 0;
}

.liuyue-ev-desc {
  font-size: var(--fs-sm);
  color: var(--text);
}

.liuyue-dimensions {
  margin-bottom: var(--sp-3);
}

.liuyue-dim {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  font-size: var(--fs-sm);
}

.liuyue-dim-label {
  color: var(--text-3);
  flex-shrink: 0;
  min-width: 50px;
}

.liuyue-dim-text {
  color: var(--text);
}

.liuyue-advice {
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  background: rgba(217, 119, 6, 0.08);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  margin: 0;
}

.liuyue-overall {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin: var(--sp-2) 0 0;
}

.liuyue-score {
  margin-top: var(--sp-3);
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-weight: 600;
}
</style>