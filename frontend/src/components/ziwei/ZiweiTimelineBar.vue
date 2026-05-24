<script setup lang="ts">
import { computed } from 'vue'
import type { DayunItem } from '@/api/ziwei'

const props = defineProps<{
  items: DayunItem[]
  currentDayunGanzhi?: string | null
  selectedDaxianIdx: number
  selectedLiunianYear: number
  allLiunianYears: number[]
  liunianYears: number[]
  currentYear: number
  birthYear: number
}>()

const emit = defineEmits<{
  (e: 'toggle-daxian', index: number): void
  (e: 'update:selected-liunian-year', year: number): void
  (e: 'step-liunian', delta: number): void
}>()

const selectedYearModel = computed({
  get: () => props.selectedLiunianYear,
  set: (value: number) => emit('update:selected-liunian-year', value),
})
</script>

<template>
  <div v-if="items.length" class="timeline-bar">
    <div class="tl-section">
      <span class="tl-label">大限</span>
      <div class="tl-track">
        <button
          v-for="(item, index) in items"
          :key="item.ganzhi"
          :class="['tl-item tl-dayun', {
            'tl-current': currentDayunGanzhi === item.ganzhi && selectedDaxianIdx === -1,
            'tl-selected': selectedDaxianIdx === index,
          }]"
          :title="`${item.ganzhi} (${item.start_year}年起)`"
          @click="emit('toggle-daxian', index)"
        >
          <span class="tl-gz">{{ item.ganzhi }}</span>
          <span class="tl-age">{{ item.start_age }}~{{ item.end_age }}岁</span>
          <span class="tl-year-info">{{ item.start_year }}年</span>
        </button>
      </div>
    </div>

    <div class="tl-section">
      <span class="tl-label">流年</span>
      <select v-model="selectedYearModel" class="tl-select">
        <option v-for="yr in allLiunianYears" :key="yr" :value="yr">{{ yr }}年</option>
      </select>
      <div class="tl-track tl-liunian">
        <button
          v-for="yr in liunianYears"
          :key="yr"
          :class="['tl-item tl-year', {
            'tl-current': yr === currentYear,
            'tl-selected': yr === selectedLiunianYear,
          }]"
          :title="`${yr}年 · ${yr - birthYear}岁`"
          @click="emit('update:selected-liunian-year', yr)"
        >
          <span class="tl-yr-num">{{ yr }}</span>
          <span class="tl-yr-age">{{ yr - birthYear }}岁</span>
        </button>
      </div>
      <div class="tl-nav">
        <button class="tl-nav-btn" @click="emit('step-liunian', -1)">◀</button>
        <button class="tl-nav-btn" @click="emit('step-liunian', 1)">▶</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-bar {
  margin-top: var(--sp-5);
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tl-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tl-label {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text-2);
  min-width: 36px;
  font-family: var(--font-cn);
}

.tl-track {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: 4px;
  flex: 1;
}

.tl-track::-webkit-scrollbar { height: 4px; }
.tl-track::-webkit-scrollbar-track { background: var(--surface-2); border-radius: 2px; }
.tl-track::-webkit-scrollbar-thumb { background: var(--border-md); border-radius: 2px; }

.tl-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  transition: all var(--dur-fast);
  white-space: nowrap;
  flex-shrink: 0;
}

.tl-item:hover { border-color: var(--accent); background: var(--surface-2); }

.tl-item.tl-current {
  border-color: #f97316;
  background: #fff7ed;
}

.tl-item.tl-selected {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}

.tl-item.tl-selected .tl-gz,
.tl-item.tl-selected .tl-age { color: #fff; }

.tl-gz {
  font-size: var(--fs-md);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.tl-age {
  font-size: 10px;
  color: var(--text-3);
  margin-top: 2px;
}

.tl-item.tl-dayun {
  min-width: 58px;
}

.tl-year-info {
  font-size: 9px;
  color: #6b7280;
  margin-top: 1px;
}

.tl-item.tl-selected .tl-year-info { color: rgba(255,255,255,.8); }

.tl-year {
  flex-direction: column;
  padding: 5px 10px;
  min-width: 50px;
}

.tl-yr-num {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  font-weight: 600;
}

.tl-yr-age {
  font-size: 9px;
  color: var(--text-3);
  margin-top: 1px;
}

.tl-item.tl-selected .tl-yr-num,
.tl-item.tl-selected .tl-yr-age { color: #fff; }

.tl-nav {
  display: flex;
  gap: 4px;
}

.tl-nav-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 11px;
  color: var(--text-2);
  transition: all var(--dur-fast);
}

.tl-nav-btn:hover { border-color: var(--accent); color: var(--accent); }

.tl-select {
  padding: 6px 24px 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: var(--fs-sm);
  font-family: var(--font-mono);
  color: var(--text);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
  flex-shrink: 0;
}

.tl-select:hover { border-color: var(--accent); }
.tl-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(217,119,6,.15); }
</style>
