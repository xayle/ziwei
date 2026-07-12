<script setup lang="ts">
import { computed } from 'vue'
import type { PalaceResponse, StarInfo, ZiweiResponse } from '@/api/ziwei'

const SIHUA_LEGEND = [
  { key: '化禄', color: '#16a34a', label: '禄' },
  { key: '化权', color: '#ea580c', label: '权' },
  { key: '化科', color: '#2563eb', label: '科' },
  { key: '化忌', color: '#dc2626', label: '忌' },
] as const

const BRANCH_CHARS = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const
const GRID_ORDER = [5, 6, 7, 8, 4, -1, -1, 9, 3, -1, -1, 10, 2, 1, 0, 11] as const

const props = defineProps<{
  result: ZiweiResponse
}>()

type GridCell = { empty: true } | { empty: false; palace: PalaceResponse }

const palaceGrid = computed(() => {
  const branchToPalace = new Map<number, PalaceResponse>()
  for (const palace of props.result.palaces ?? []) {
    const branchIdx = BRANCH_CHARS.indexOf(palace.branch as (typeof BRANCH_CHARS)[number])
    if (branchIdx >= 0) branchToPalace.set(branchIdx, palace)
  }

  let centerAdded = false
  return GRID_ORDER.map((branchIdx) => {
    if (branchIdx === -1) {
      if (centerAdded) return null
      centerAdded = true
      return { empty: true } as GridCell
    }
    const palace = branchToPalace.get(branchIdx)
    if (!palace) return null
    return { empty: false, palace } as GridCell
  }).filter((cell): cell is GridCell => cell !== null)
})

function isBodyPalace(palace: PalaceResponse): boolean {
  if (palace.is_body_palace) return true
  const gz = `${palace.stem}${palace.branch}`
  return gz === props.result.body_palace_gz
}

function starLine(star: StarInfo): string {
  const tf = star.transforms?.[0]
  return `${star.name}${star.brightness ? `(${star.brightness})` : ''}${tf ? `·${tf}` : ''}`
}

function mainStarsText(palace: PalaceResponse): string {
  const stars = palace.main_stars?.map(starLine).filter(Boolean) ?? []
  return stars.length ? stars.join('、') : '无主星'
}

function auxStarsText(palace: PalaceResponse): string {
  const stars = palace.aux_stars?.slice(0, 6).map(starLine).filter(Boolean) ?? []
  return stars.length ? stars.join('·') : ''
}
</script>

<template>
  <div class="report-ziwei-chart">
    <div class="report-ziwei-chart__legend">
      <span v-for="item in SIHUA_LEGEND" :key="item.key" class="rz-legend" :style="{ borderColor: item.color }">
        {{ item.label }}
      </span>
      <span class="rz-legend rz-legend--body">身宫</span>
    </div>
    <div class="report-ziwei-chart__grid">
      <template v-for="(cell, idx) in palaceGrid" :key="idx">
        <div v-if="cell.empty" class="rz-center">
          <p class="rz-center__ju">{{ result.wuxing_ju_name }}</p>
          <p class="rz-center__gz">{{ result.lunar.year_gz }} {{ result.lunar.jieqi_month_gz || result.lunar.month_gz }} {{ result.lunar.day_gz }} {{ result.lunar.hour_gz }}</p>
          <p class="rz-center__birth">{{ result.birth_solar }}</p>
          <p class="rz-center__meta">命·{{ result.life_ruler_star || '—' }} 身·{{ result.body_ruler_star || '—' }}</p>
        </div>
        <div
          v-else
          class="rz-cell"
          :class="{
            'rz-cell--life': cell.palace.name.includes('命'),
            'rz-cell--body': cell.palace.name.includes('身'),
          }"
        >
          <div class="rz-cell__head">
            <span class="rz-cell__name">
              {{ cell.palace.name.replace('宫', '') }}
              <span v-if="isBodyPalace(cell.palace)" class="rz-badge rz-badge--body">身宫</span>
            </span>
            <span class="rz-cell__gz">{{ cell.palace.stem }}{{ cell.palace.branch }}</span>
          </div>
          <p class="rz-cell__stars">{{ mainStarsText(cell.palace) }}</p>
          <p v-if="auxStarsText(cell.palace)" class="rz-cell__aux">{{ auxStarsText(cell.palace) }}</p>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.report-ziwei-chart {
  margin-top: 16px;
  overflow-x: auto;
}

.report-ziwei-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.rz-legend {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border: 2px solid #a8a29e;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #44403c;
}

.rz-legend--body {
  border-color: #2563eb;
  color: #2563eb;
}

.rz-badge {
  display: inline-block;
  margin-left: 4px;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 8px;
  font-weight: 700;
  vertical-align: middle;
}

.rz-badge--body {
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.report-ziwei-chart__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(88px, 1fr));
  border: 1.5px solid #c9b99a;
  background: #e8dcc8;
  min-width: 360px;
}

.rz-cell,
.rz-center {
  min-height: 96px;
  padding: 6px;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
  background: #fffdf7;
}

.rz-center {
  grid-column: span 2;
  grid-row: span 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 4px;
  background: var(--surface);
}

.rz-center__ju {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #8b5e34;
  font-family: var(--font-cn);
}

.rz-center__gz,
.rz-center__birth,
.rz-center__meta {
  margin: 0;
  font-size: 10px;
  color: #57534e;
}

.rz-cell--life {
  border-top: 3px solid #dc2626;
}

.rz-cell--body {
  border-top: 3px solid #2563eb;
}

.rz-cell__head {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.rz-cell__name {
  font-size: 10px;
  color: #78716c;
  font-weight: 600;
}

.rz-cell__gz {
  font-size: 11px;
  font-weight: 700;
  color: #44403c;
}

.rz-cell__stars {
  margin: 6px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: #1a1410;
  font-family: var(--font-cn);
  line-height: 1.3;
}

.rz-cell__aux {
  margin: 4px 0 0;
  font-size: 9px;
  color: #a8a29e;
  line-height: 1.4;
}

@media print {
  .report-ziwei-chart {
    overflow: visible;
  }

  .report-ziwei-chart__grid {
    min-width: 100%;
  }

  .rz-cell {
    min-height: 110px;
  }
}
</style>
