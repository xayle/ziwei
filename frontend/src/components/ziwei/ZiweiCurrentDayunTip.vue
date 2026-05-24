<script setup lang="ts">
import type { DayunItem } from '@/api/ziwei'

defineProps<{
  currentDayun: DayunItem | null
}>()
</script>

<template>
  <div v-if="currentDayun" class="cur-dayun-tip">
    当前大运：<b>{{ currentDayun.ganzhi }}</b>（{{ currentDayun.start_age }}~{{ currentDayun.end_age }}岁，{{ currentDayun.start_year }}年起）
    <span v-if="Object.keys(currentDayun.sihua).length">
      ·
      <span v-for="(val, star) in currentDayun.sihua" :key="star" class="sihua-badge">{{ star }}{{ val }}</span>
    </span>
  </div>
</template>

<style scoped>
.cur-dayun-tip {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin-bottom: var(--sp-4);
  padding: var(--sp-2) var(--sp-4);
  background: rgba(217,119,6,.08);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

.sihua-badge {
  display: inline-block;
  padding: 1px 6px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: 10px;
  font-size: var(--fs-xs);
  margin-left: 4px;
}
</style>