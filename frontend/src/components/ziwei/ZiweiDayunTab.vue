<script setup lang="ts">
import type { DayunItem, DayunResponse } from '@/api/ziwei'

interface DayunStats {
  total: number
  past: number
  current: number
  future: number
  startYear: number
  endYear: number
}

interface DayunProgress {
  yearsIn: number
  yearsLeft: number
  pct: number
  ganzhi: string
}

const props = defineProps<{
  dayun: DayunResponse
  currentYear: number
  dayunStats: DayunStats
  dayunProgress: DayunProgress | null
}>()

const emit = defineEmits<{
  (e: 'locate-current'): void
}>()

function isCurrentDayun(item: DayunItem) {
  return item.start_year <= props.currentYear && (item.start_year + 10) > props.currentYear
}

function isPastDayun(item: DayunItem) {
  return (item.start_year + 10) <= props.currentYear
}
</script>

<template>
  <div class="dayun-stats-card card">
    <div class="dsc-grid">
      <div class="dsc-item">
        <span class="dsc-label">运行方向</span>
        <span class="dsc-value">{{ dayun.forward ? '顺运' : '逆运' }}</span>
      </div>
      <div class="dsc-item">
        <span class="dsc-label">起运年龄</span>
        <span class="dsc-value">{{ dayun.start_age }}岁</span>
      </div>
      <div class="dsc-item">
        <span class="dsc-label">居历年限</span>
        <span class="dsc-value">{{ dayunStats.past }}步</span>
      </div>
      <div class="dsc-item">
        <span class="dsc-label">尚待年限</span>
        <span class="dsc-value">{{ dayunStats.future }}步</span>
      </div>
      <div class="dsc-item">
        <span class="dsc-label">共计局数</span>
        <span class="dsc-value">{{ dayunStats.total }}局</span>
      </div>
      <div class="dsc-item">
        <span class="dsc-label">跨度年份</span>
        <span class="dsc-value">{{ dayunStats.startYear }}–{{ dayunStats.endYear }}</span>
      </div>
    </div>

    <div v-if="dayunProgress" class="dsc-progress">
      <div class="dsc-prog-head">
        <span class="dsc-prog-title">当前大运：{{ dayunProgress.ganzhi }}</span>
        <span class="dsc-prog-meta">已进 {{ dayunProgress.yearsIn }} 年，剩 {{ dayunProgress.yearsLeft }} 年</span>
      </div>
      <div class="dsc-prog-bar">
        <div class="dsc-prog-fill" :style="{ width: `${dayunProgress.pct}%` }"></div>
      </div>
      <div class="dsc-prog-labels">
        <span>起始</span>
        <span>{{ dayunProgress.pct }}%</span>
        <span>终首</span>
      </div>
    </div>
  </div>

  <div class="dayun-toolbar">
    <div class="dayun-summary-bar">
      <p class="dayun-info">
        {{ dayun.forward ? '顺运' : '逆运' }}，
        起运 <b>{{ dayun.start_age }} 岁</b>
        （{{ dayun.start_age_text }}）
      </p>
      <p v-if="dayun.items.length" class="dayun-range">
        大运跨度：<b>{{ dayun.items[0]?.start_year }}</b> ~ <b>{{ dayun.items[dayun.items.length - 1]?.start_year + 9 }}</b> 年
      </p>
    </div>
    <button class="dayun-locate-btn" title="定位到当前大运" @click="emit('locate-current')">
      📍 定位当前
    </button>
  </div>

  <div class="dayun-timeline">
    <div class="dt-line"></div>
    <div
      v-for="item in dayun.items"
      :key="item.index"
      :class="['dt-node', { 'dt-cur': isCurrentDayun(item), 'dt-past': isPastDayun(item) }]"
    >
      <div class="dt-marker"></div>
      <div class="dt-label">{{ item.ganzhi }}</div>
      <div class="dt-age">{{ item.start_age }}岁</div>
      <div v-if="isCurrentDayun(item)" class="dt-cur-badge">当前</div>
    </div>
  </div>

  <div class="dayun-list">
    <div
      v-for="item in dayun.items"
      :key="item.index"
      :class="['dayun-item', { cur: isCurrentDayun(item) }]"
    >
      <span v-if="isCurrentDayun(item)" class="dayun-cur-badge">当前</span>
      <div class="dayun-gz">{{ item.ganzhi }}</div>
      <div class="dayun-age">{{ item.start_age }}～{{ item.end_age }}岁</div>
      <div class="dayun-year">{{ item.start_year }}年</div>
      <div v-if="Object.keys(item.sihua).length" class="dayun-sihua">
        <span v-for="(val, star) in item.sihua" :key="star" class="sihua-badge">{{ star }}{{ val }}</span>
      </div>
      <div v-if="Object.keys(item.boshi_stars || {}).length" class="dayun-boshi">
        <span v-for="(branch, star) in item.boshi_stars" :key="star" class="boshi-tag">{{ star }}·{{ branch }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dayun-stats-card {
  padding: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.dsc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}

.dsc-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.dsc-label {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.dsc-value {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}

.dsc-progress {
  margin-top: var(--sp-2);
}

.dsc-prog-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}

.dsc-prog-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text);
}

.dsc-prog-meta {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.dsc-prog-bar {
  height: 8px;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}

.dsc-prog-fill {
  height: 100%;
  background: linear-gradient(90deg, #d97706, #f59e0b);
  border-radius: 999px;
  transition: width 0.4s ease;
}

.dsc-prog-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-2);
  margin-top: 3px;
}

.dayun-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: 8px;
}

.dayun-summary-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.dayun-info {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin-bottom: var(--sp-4);
}

.dayun-range {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.dayun-range b {
  color: var(--accent);
  font-weight: 600;
}

.dayun-locate-btn {
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

.dayun-locate-btn:hover {
  filter: brightness(1.1);
}

.dayun-timeline {
  position: relative;
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding: var(--sp-4) 0 var(--sp-6);
  margin-bottom: var(--sp-4);
}

.dt-line {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--border-md), var(--accent), var(--border-md));
  z-index: 0;
}

.dt-node {
  position: relative;
  flex: 1;
  min-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.dt-marker {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid var(--border-md);
  margin-top: 26px;
  transition: all 0.2s;
}

.dt-node.dt-cur .dt-marker {
  width: 18px;
  height: 18px;
  background: var(--accent);
  border-color: var(--accent);
  margin-top: 24px;
  box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.2);
}

.dt-node.dt-past .dt-marker {
  background: var(--accent);
  border-color: var(--accent);
  opacity: 0.6;
}

.dt-label {
  margin-top: 10px;
  font-size: var(--fs-sm);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.dt-node.dt-cur .dt-label {
  color: var(--accent);
}

.dt-node.dt-past .dt-label,
.dt-age,
.dayun-year,
.boshi-tag {
  color: var(--text-2);
}

.dt-age {
  font-size: var(--fs-xs);
}

.dt-cur-badge {
  position: absolute;
  top: 0;
  font-size: 9px;
  padding: 1px 5px;
  background: var(--accent);
  color: #fff;
  border-radius: 4px;
  font-weight: 600;
}

.dayun-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}

.dayun-item {
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  text-align: center;
  min-width: 90px;
  position: relative;
}

.dayun-item.cur {
  border-color: var(--accent);
  background: rgba(217, 119, 6, 0.06);
}

.dayun-cur-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #d97706;
  color: #fff;
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.dayun-gz {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
}

.dayun-age {
  font-size: var(--fs-xs);
  color: var(--text-2);
  margin-top: 3px;
}

.dayun-year {
  font-size: var(--fs-xs);
}

.dayun-sihua,
.dayun-boshi {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  margin-top: 6px;
}

.sihua-badge,
.boshi-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1.2;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid var(--border);
}

.sihua-badge {
  color: var(--text);
  font-weight: 600;
}
</style>