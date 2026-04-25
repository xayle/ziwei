<script setup lang="ts">
interface ZiweiDayunItem {
  index: number
  ganzhi?: string
  start_age?: number
  end_age?: number
  start_year?: number
}

interface ZiweiLiuyueItem {
  month: number
  month_name?: string
  month_gz?: string
}

const props = defineProps<{
  dayunItems: ZiweiDayunItem[]
  liuyueItems: ZiweiLiuyueItem[]
  activeDayunIndex: number | null | undefined
  activeLiuyueMonth: number | null | undefined
  activeDayunSummary?: string
  activeLiuyueSummary?: string
}>()

const emit = defineEmits<{
  selectDayun: [index: number]
  selectLiuyue: [month: number]
}>()
</script>

<template>
  <section class="zw-card">
    <h2 class="zw-title">大限 / 流月</h2>

    <div class="zw-list-panel">
      <button
        v-for="item in props.dayunItems"
        :key="item.index"
        type="button"
        class="zw-list-item zw-select-item"
        :class="{ active: item.index === props.activeDayunIndex }"
        @click="emit('selectDayun', item.index)"
      >
        <span>{{ item.ganzhi }} · {{ item.start_age }}-{{ item.end_age }}岁</span>
        <span class="zw-select-meta">{{ item.start_year }}起</span>
      </button>
    </div>

    <div v-if="props.activeDayunSummary" class="zw-inline-summary">当前选择：{{ props.activeDayunSummary }}</div>

    <div v-if="props.liuyueItems.length" class="zw-chip-list">
      <button
        v-for="item in props.liuyueItems"
        :key="item.month"
        type="button"
        class="zw-chip"
        :class="{ active: item.month === props.activeLiuyueMonth }"
        @click="emit('selectLiuyue', item.month)"
      >{{ item.month_name }} {{ item.month_gz }}</button>
    </div>

    <div v-if="props.activeLiuyueSummary" class="zw-inline-summary">{{ props.activeLiuyueSummary }}</div>
  </section>
</template>

<style scoped>
.zw-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 14px 16px;
}

.zw-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  letter-spacing: .01em;
}

.zw-list-panel {
  display: grid;
  gap: 8px;
}

.zw-list-item {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-2, #f8fafc);
  padding: 10px 12px;
  color: var(--text-1);
}

.zw-select-item {
  appearance: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: transform .12s, box-shadow .12s, border-color .12s;
  text-align: left;
  font-family: var(--font-cn);
}

.zw-select-item:hover,
.zw-select-item.active {
  transform: translateY(-1px);
  border-color: #a78bfa;
  box-shadow: 0 8px 16px rgba(124,77,171,.10);
}

.zw-select-meta {
  color: var(--text-3);
  font-size: 12px;
  font-family: var(--font-cn);
}

.zw-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.zw-chip {
  appearance: none;
  border: none;
  cursor: pointer;
  transition: transform .12s, box-shadow .12s;
  padding: 6px 10px;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-cn);
}

.zw-chip:hover,
.zw-chip.active {
  transform: translateY(-1px);
  box-shadow: 0 0 0 2px rgba(21,128,61,.18);
}

.zw-inline-summary {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.7;
  font-family: var(--font-cn);
}
</style>
