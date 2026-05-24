<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PatternResponse } from '@/api/ziwei'

type PatternViewMode = 'list' | 'group'

type PatternGroupKey = 'high' | 'med' | 'low'

type PatternGroup = Record<PatternGroupKey, PatternResponse[]>

const props = defineProps<{
  patterns: PatternResponse[]
}>()

const patternViewMode = ref<PatternViewMode>('group')

function patternClass(level: string) {
  const normalized = level?.toLowerCase() ?? ''
  if (normalized.includes('上') || normalized.includes('大') || normalized.includes('high')) return 'level-high'
  if (normalized.includes('中') || normalized.includes('med')) return 'level-med'
  return 'level-low'
}

const patternStats = computed(() => {
  if (!props.patterns.length) return { high: 0, med: 0, low: 0, total: 0 }

  let high = 0
  let med = 0
  let low = 0
  props.patterns.forEach((pattern) => {
    const cls = patternClass(pattern.level)
    if (cls === 'level-high') high++
    else if (cls === 'level-med') med++
    else low++
  })

  return { high, med, low, total: props.patterns.length }
})

const groupedPatterns = computed<PatternGroup>(() => {
  const groups: PatternGroup = { high: [], med: [], low: [] }
  props.patterns.forEach((pattern) => {
    const cls = patternClass(pattern.level)
    if (cls === 'level-high') groups.high.push(pattern)
    else if (cls === 'level-med') groups.med.push(pattern)
    else groups.low.push(pattern)
  })
  return groups
})

function patternWeight(level: string): number {
  const cls = patternClass(level)
  if (cls === 'level-high') return 3
  if (cls === 'level-med') return 2
  return 1
}

const sortedPatterns = computed(() =>
  [...props.patterns].sort((a, b) => {
    const weightDiff = patternWeight(b.level) - patternWeight(a.level)
    if (weightDiff !== 0) return weightDiff
    const aScore = (a.stars?.length || 0) + (a.palaces?.length || 0)
    const bScore = (b.stars?.length || 0) + (b.palaces?.length || 0)
    return bScore - aScore
  }),
)

const patternHighlights = computed(() =>
  sortedPatterns.value.slice(0, 3).map((pattern) => ({
    name: pattern.name,
    cls: patternClass(pattern.level),
  })),
)

const groupedSections = computed(() => [
  { key: 'high', icon: '⭐', title: '上等格局', items: groupedPatterns.value.high, itemClass: 'level-high', groupClass: 'pg-high' },
  { key: 'med', icon: '✦', title: '中等格局', items: groupedPatterns.value.med, itemClass: 'level-med', groupClass: 'pg-med' },
  { key: 'low', icon: '◆', title: '一般格局', items: groupedPatterns.value.low, itemClass: 'level-low', groupClass: 'pg-low' },
])
</script>

<template>
  <div v-if="patterns.length" class="patterns-list">
    <div class="pattern-toolbar">
      <div class="pattern-stats">
        <span class="pattern-stat total">共 <b>{{ patternStats.total }}</b> 个格局</span>
        <span v-if="patternStats.high" class="pattern-stat high">上格 <b>{{ patternStats.high }}</b></span>
        <span v-if="patternStats.med" class="pattern-stat med">中格 <b>{{ patternStats.med }}</b></span>
        <span v-if="patternStats.low" class="pattern-stat low">普通 <b>{{ patternStats.low }}</b></span>
      </div>
      <div class="pattern-view-toggle">
        <button :class="['pvt-btn', { active: patternViewMode === 'group' }]" @click="patternViewMode = 'group'">分组</button>
        <button :class="['pvt-btn', { active: patternViewMode === 'list' }]" @click="patternViewMode = 'list'">列表</button>
      </div>
    </div>

    <div v-if="patternHighlights.length" class="pattern-focus-strip">
      <span class="pfs-label">重点格局</span>
      <span v-for="item in patternHighlights" :key="item.name" :class="['pfs-item', item.cls]">
        {{ item.name }}
      </span>
    </div>

    <template v-if="patternViewMode === 'group'">
      <div v-for="section in groupedSections" v-show="section.items.length" :key="section.key" :class="['pattern-group', section.groupClass]">
        <div class="pg-header">
          <span class="pg-icon">{{ section.icon }}</span>
          <span class="pg-title">{{ section.title }}</span>
          <span class="pg-count">{{ section.items.length }}</span>
        </div>
        <div class="pg-items">
          <div v-for="(pattern, index) in section.items" :key="`${section.key}-${index}`" :class="['pattern-item', section.itemClass]">
            <div class="pattern-header">
              <span class="pattern-name">{{ pattern.name }}</span>
              <span class="pattern-level">{{ pattern.level }}</span>
            </div>
            <p v-if="pattern.description" class="pattern-desc">{{ pattern.description }}</p>
            <div v-if="pattern.palaces?.length || pattern.stars?.length" class="pattern-meta">
              <span v-if="pattern.palaces?.length" class="pattern-palaces">
                <span class="meta-label">宫位</span>
                <span v-for="palace in pattern.palaces" :key="palace" class="meta-tag palace-tag">{{ palace }}</span>
              </span>
              <span v-if="pattern.stars?.length" class="pattern-stars">
                <span class="meta-label">星曜</span>
                <span v-for="star in pattern.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
              </span>
            </div>
            <p v-if="pattern.source" class="pattern-source">📖 {{ pattern.source }}</p>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div v-for="(pattern, index) in sortedPatterns" :key="index" :class="['pattern-item', patternClass(pattern.level)]">
        <div class="pattern-header">
          <span class="pattern-name">{{ pattern.name }}</span>
          <span class="pattern-level">{{ pattern.level }}</span>
        </div>
        <p v-if="pattern.description" class="pattern-desc">{{ pattern.description }}</p>
        <div v-if="pattern.palaces?.length || pattern.stars?.length" class="pattern-meta">
          <span v-if="pattern.palaces?.length" class="pattern-palaces">
            <span class="meta-label">宫位</span>
            <span v-for="palace in pattern.palaces" :key="palace" class="meta-tag palace-tag">{{ palace }}</span>
          </span>
          <span v-if="pattern.stars?.length" class="pattern-stars">
            <span class="meta-label">星曜</span>
            <span v-for="star in pattern.stars" :key="star" class="meta-tag star-tag">{{ star }}</span>
          </span>
        </div>
        <p v-if="pattern.source" class="pattern-source">📖 {{ pattern.source }}</p>
      </div>
    </template>
  </div>
  <p v-else class="muted">未命中特定格局</p>
</template>

<style scoped>
.patterns-list { display: flex; flex-direction: column; gap: var(--sp-4); }
.pattern-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
}
.pattern-stats { display: flex; flex-wrap: wrap; gap: 8px; }
.pattern-stat {
  font-size: var(--fs-sm);
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
  border: 1px solid var(--border);
}
.pattern-stat.total b { color: var(--text); }
.pattern-stat.high { color: #991b1b; background: #fee2e2; border-color: #fca5a5; }
.pattern-stat.med { color: #92400e; background: #fef3c7; border-color: #fcd34d; }
.pattern-stat.low { color: #334155; background: #f1f5f9; border-color: #cbd5e1; }
.pattern-view-toggle {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.pvt-btn {
  padding: 5px 12px;
  font-size: var(--fs-sm);
  border: none;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.pvt-btn:hover { background: var(--surface-2); }
.pvt-btn.active { background: var(--accent); color: #fff; }
.pattern-focus-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.pfs-label { font-size: var(--fs-xs); color: var(--text-2); }
.pfs-item {
  font-size: var(--fs-xs);
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  color: var(--text-2);
}
.pfs-item.level-high { color: #991b1b; background: #fee2e2; border-color: #fca5a5; }
.pfs-item.level-med { color: #92400e; background: #fef3c7; border-color: #fcd34d; }
.pfs-item.level-low { color: #334155; background: #f1f5f9; border-color: #cbd5e1; }
.pattern-group {
  border-radius: var(--radius-md);
  overflow: hidden;
}
.pg-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  font-weight: 600;
}
.pg-high .pg-header { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e; }
.pg-med .pg-header { background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); color: #3730a3; }
.pg-low .pg-header { background: var(--surface-2); color: var(--text-2); }
.pg-icon { font-size: var(--fs-lg); }
.pg-title { flex: 1; }
.pg-count {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: rgba(255,255,255,.82);
  border-radius: 10px;
}
.pg-items {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: none;
}
.pattern-item {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.pattern-item.level-high { border-color: rgba(220, 38, 38, 0.25); }
.pattern-item.level-med { border-color: rgba(217, 119, 6, 0.25); }
.pattern-item.level-low { border-color: var(--border); }
.pattern-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.pattern-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.pattern-level {
  font-size: var(--fs-xs);
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  color: var(--text-2);
}
.pattern-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; margin: 0; }
.pattern-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-top: var(--sp-2); }
.pattern-palaces, .pattern-stars { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.meta-label { font-size: 10px; color: var(--text-2); }
.meta-tag { font-size: 10px; padding: 1px 6px; border-radius: 8px; }
.palace-tag { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }
.star-tag { background: rgba(217, 119, 6, 0.1); color: #d97706; }
.pattern-source { font-size: var(--fs-xs); color: var(--text-2); margin-top: 4px; }
.muted { color: var(--text-3); font-size: var(--fs-sm); }
</style>
