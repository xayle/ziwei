<script setup lang="ts">
import type { PalaceResponse } from '@/api/ziwei'
import type { ZiweiCompareTarget, ZiweiDayFortune } from '@/composables/useZiweiToolPanels'

type CompareForm = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
}

const props = defineProps<{
  showSharePanel: boolean
  shareLink: string
  showCalendarView: boolean
  calendarViewYear: number
  calendarViewMonth: number
  calendarGrid: Array<ZiweiDayFortune | null>
  getDayFortuneClass: (score: number) => string
  showComparePanel: boolean
  compareForm: CompareForm
  compareTarget: ZiweiCompareTarget | null
  showBookmarksPanel: boolean
  bookmarkedPalaces: PalaceResponse[]
}>()

const emit = defineEmits<{
  closeSharePanel: []
  copyShareLink: []
  prevCalendarMonth: []
  nextCalendarMonth: []
  closeCalendarView: []
  closeComparePanel: []
  'update:compareForm': [value: CompareForm]
  clearCompareTarget: []
  setCompareTarget: []
  closeBookmarksPanel: []
  selectBookmarkedPalace: [index: number]
  togglePalaceBookmark: [index: number]
}>()

function updateCompareForm<K extends keyof CompareForm>(key: K, value: CompareForm[K]) {
  emit('update:compareForm', {
    ...props.compareForm,
    [key]: value,
  })
}
</script>

<template>
  <div v-if="props.showSharePanel" class="share-panel">
    <div class="sp-header">
      <span>分享命盘</span>
      <button class="sp-close" @click="emit('closeSharePanel')">✕</button>
    </div>
    <div class="sp-content">
      <input type="text" readonly :value="props.shareLink" class="sp-link-input" @click="($event.target as HTMLInputElement).select()" />
      <button class="sp-copy-btn" @click="emit('copyShareLink')">复制链接</button>
    </div>
    <p class="sp-hint">他人打开链接后将自动计算相同命盘</p>
  </div>

  <div v-if="props.showCalendarView" class="calendar-panel">
    <div class="cal-header">
      <button class="cal-nav" @click="emit('prevCalendarMonth')">◀</button>
      <span class="cal-title">{{ props.calendarViewYear }}年{{ props.calendarViewMonth }}月 运势日历</span>
      <button class="cal-nav" @click="emit('nextCalendarMonth')">▶</button>
      <button class="cal-close" @click="emit('closeCalendarView')">✕</button>
    </div>
    <div class="cal-weekdays">
      <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
    </div>
    <div class="cal-grid">
      <div
        v-for="(item, index) in props.calendarGrid"
        :key="index"
        :class="['cal-day', item ? props.getDayFortuneClass(item.score) : 'cal-empty']"
      >
        <template v-if="item">
          <span class="cal-day-num">{{ item.day }}</span>
          <span class="cal-day-fortune">{{ item.brief }}</span>
        </template>
      </div>
    </div>
    <div class="cal-legend">
      <span class="fortune-great">大吉</span>
      <span class="fortune-good">吉</span>
      <span class="fortune-normal">平</span>
      <span class="fortune-bad">凶</span>
      <span class="fortune-terrible">大凶</span>
    </div>
  </div>

  <div v-if="props.showComparePanel" class="compare-panel">
    <div class="cmp-header">
      <span>命盘对比设置</span>
      <button class="cmp-close" @click="emit('closeComparePanel')">✕</button>
    </div>
    <div class="cmp-content">
      <p class="cmp-hint">输入第二人资料进行对比分析</p>
      <div class="cmp-form">
        <div class="cmp-row">
          <label>年</label>
          <input type="number" :value="props.compareForm.year" min="1900" max="2100" @input="updateCompareForm('year', Number(($event.target as HTMLInputElement).value))" />
          <label>月</label>
          <input type="number" :value="props.compareForm.month" min="1" max="12" @input="updateCompareForm('month', Number(($event.target as HTMLInputElement).value))" />
          <label>日</label>
          <input type="number" :value="props.compareForm.day" min="1" max="31" @input="updateCompareForm('day', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="cmp-row">
          <label>时</label>
          <input type="number" :value="props.compareForm.hour" min="0" max="23" @input="updateCompareForm('hour', Number(($event.target as HTMLInputElement).value))" />
          <label>分</label>
          <input type="number" :value="props.compareForm.minute" min="0" max="59" @input="updateCompareForm('minute', Number(($event.target as HTMLInputElement).value))" />
          <label>性别</label>
          <select :value="props.compareForm.gender" @change="updateCompareForm('gender', ($event.target as HTMLSelectElement).value as '男' | '女')">
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
        </div>
      </div>
      <div class="cmp-btns">
        <button v-if="props.compareTarget" class="cmp-clear" @click="emit('clearCompareTarget')">清除对比</button>
        <button class="cmp-set" @click="emit('setCompareTarget')">设置对比</button>
      </div>
      <div v-if="props.compareTarget" class="cmp-status">
        当前对比: {{ props.compareTarget.year }}/{{ props.compareTarget.month }}/{{ props.compareTarget.day }}
        {{ props.compareTarget.hour }}:{{ String(props.compareTarget.minute).padStart(2, '0') }} {{ props.compareTarget.gender }}
      </div>
    </div>
  </div>

  <div v-if="props.showBookmarksPanel" class="bookmarks-panel">
    <div class="bkm-header">
      <span>已收藏宫位 ({{ props.bookmarkedPalaces.length }})</span>
      <button class="bkm-close" @click="emit('closeBookmarksPanel')">✕</button>
    </div>
    <div class="bkm-content">
      <div v-if="props.bookmarkedPalaces.length" class="bkm-list">
        <div
          v-for="palace in props.bookmarkedPalaces"
          :key="palace.index"
          class="bkm-item"
          @click="emit('selectBookmarkedPalace', palace.index)"
        >
          <span class="bkm-palace-name">{{ palace.name }}</span>
          <span class="bkm-palace-gz">{{ palace.stem }}{{ palace.branch }}</span>
          <span class="bkm-palace-stars">{{ palace.main_stars?.map((item) => item.name).join('、') || '无主星' }}</span>
          <button class="bkm-remove" @click.stop="emit('togglePalaceBookmark', palace.index)">✕</button>
        </div>
      </div>
      <div v-else class="bkm-empty">
        暂无收藏，点击宫位中的☆可收藏
      </div>
    </div>
  </div>
</template>

<style scoped>
.share-panel {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  margin-top: 8px;
}

.sp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}

.sp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}

.sp-close:hover {
  color: var(--danger);
}

.sp-content {
  padding: 12px;
  display: flex;
  gap: 8px;
}

.sp-link-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: var(--fs-xs);
  background: var(--bg);
  color: var(--text);
}

.sp-copy-btn {
  padding: 8px 12px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: var(--fs-xs);
  cursor: pointer;
  white-space: nowrap;
}

.sp-copy-btn:hover {
  filter: brightness(1.1);
}

.sp-hint {
  padding: 0 14px 12px;
  font-size: 11px;
  color: var(--text-2);
  margin: 0;
}

.calendar-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 360px;
  padding: 12px;
  max-height: 60vh;
  overflow-y: auto;
}

.cal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.cal-nav {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 12px;
}

.cal-nav:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.cal-title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  color: var(--text);
}

.cal-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}

.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: default;
}

.cal-empty {
  background: transparent;
}

.cal-day-num {
  font-weight: 600;
}

.cal-day-fortune {
  font-size: 9px;
  margin-top: 2px;
}

.fortune-great { background: #dcfce7; color: #166534; }
.fortune-good { background: #d1fae5; color: #047857; }
.fortune-normal { background: #f3f4f6; color: #6b7280; }
.fortune-bad { background: #fee2e2; color: #b91c1c; }
.fortune-terrible { background: #fecaca; color: #991b1b; }

.cal-legend {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.cal-legend span {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
}

.compare-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 340px;
  overflow: hidden;
  max-height: 60vh;
  overflow-y: auto;
}

.cmp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #f97316;
}

.cmp-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}

.cmp-content {
  padding: 14px;
}

.cmp-hint {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin: 0 0 12px;
}

.cmp-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cmp-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.cmp-row label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  min-width: 20px;
}

.cmp-row input,
.cmp-row select {
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  width: 60px;
}

.cmp-row select {
  width: 52px;
}

.cmp-btns {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.cmp-set {
  flex: 1;
  padding: 8px;
  background: #f97316;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
  font-weight: 500;
}

.cmp-set:hover {
  background: #ea580c;
}

.cmp-clear {
  padding: 8px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}

.cmp-status {
  margin-top: 12px;
  padding: 8px 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  color: #c2410c;
}

.bookmarks-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 320px;
  max-height: 360px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}

.bkm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #d97706;
}

.bkm-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}

.bkm-content {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}

.bkm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bkm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}

.bkm-item:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}

.bkm-palace-name {
  font-weight: 600;
  color: var(--text);
  min-width: 40px;
}

.bkm-palace-gz {
  font-size: 11px;
  color: var(--text-3);
  font-family: var(--font-mono);
}

.bkm-palace-stars {
  flex: 1;
  font-size: 11px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bkm-remove {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-3);
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.bkm-remove:hover {
  background: var(--danger);
  color: #fff;
}

.bkm-empty {
  text-align: center;
  color: var(--text-3);
  font-size: var(--fs-sm);
  padding: 30px 10px;
}
</style>