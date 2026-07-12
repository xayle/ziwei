<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PalaceResponse, StarInfo, ZiweiResponse } from '@/api/ziwei'
import {
  buildOverlayBadges,
  type OverlayLayer,
} from '@/utils/ziweiOverlay'

const BRANCH_CHARS = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const
const GRID_ORDER = [5, 6, 7, 8, 4, -1, -1, 9, 3, -1, -1, 10, 2, 1, 0, 11] as const
const SIHUA_LEGEND = [
  { key: '化禄', color: '#16a34a', label: '禄' },
  { key: '化权', color: '#ea580c', label: '权' },
  { key: '化科', color: '#2563eb', label: '科' },
  { key: '化忌', color: '#dc2626', label: '忌' },
] as const
const SIHUA_COLORS: Record<string, string> = Object.fromEntries(
  SIHUA_LEGEND.map((item) => [item.key, item.color]),
)

const props = withDefaults(defineProps<{
  result: ZiweiResponse
  readonly?: boolean
  showAuxLimit?: number
  /** 是否显示运限叠宫工具栏 */
  showOverlayControls?: boolean
  /** 外部控制的叠宫层（可选） */
  overlayLayer?: OverlayLayer
  /** 手动选定大限命宫地支索引（时间轴点击） */
  selectedDayunBranchIdx?: number | null
  /** 流月序号 1–12（外部控制，默认当前公历月） */
  liuyueMonth?: number
}>(), {
  readonly: true,
  showAuxLimit: 12,
  showOverlayControls: true,
  selectedDayunBranchIdx: null,
  liuyueMonth: undefined,
})

const emit = defineEmits<{
  'update:overlayLayer': [layer: OverlayLayer]
}>()

const internalLayer = ref<OverlayLayer>('natal')
const overlayLayer = computed(() => props.overlayLayer ?? internalLayer.value)

function setOverlayLayer(layer: OverlayLayer) {
  if (props.overlayLayer !== undefined) {
    emit('update:overlayLayer', layer)
  } else {
    internalLayer.value = layer
  }
}
const currentYear = new Date().getFullYear()

const overlayBadges = computed(() => {
  if (overlayLayer.value === 'natal') return new Map<string, string[]>()
  const opts: { dayunBranchIdx?: number; liuyueMonth?: number } = {}
  if (props.selectedDayunBranchIdx != null && props.selectedDayunBranchIdx >= 0) {
    opts.dayunBranchIdx = props.selectedDayunBranchIdx
  }
  if (props.liuyueMonth != null && props.liuyueMonth >= 1) {
    opts.liuyueMonth = props.liuyueMonth
  }
  return buildOverlayBadges(
    props.result,
    overlayLayer.value,
    currentYear,
    Object.keys(opts).length ? opts : undefined,
  )
})

const overlayLayers: { key: OverlayLayer; label: string }[] = [
  { key: 'natal', label: '本命' },
  { key: 'dayun', label: '大限' },
  { key: 'liunian', label: '流年' },
  { key: 'liuyue', label: '流月' },
  { key: 'liuri', label: '流日' },
  { key: 'flying', label: '飞星' },
]

function cellBadges(palace: PalaceResponse): string[] {
  return overlayBadges.value.get(palace.name) ?? []
}

function isOverlayHighlight(palace: PalaceResponse): boolean {
  return cellBadges(palace).some((t) =>
    t.startsWith('大限命') || t.startsWith('流年命') || t.startsWith('流月命') || t.startsWith('流日'))
}

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

function hasBorrowedStars(palace: PalaceResponse): boolean {
  return Boolean(
    palace.borrowed_from_palace
    || palace.is_empty_palace
    || (palace.borrowed_main_stars?.length ?? 0) > 0,
  )
}

function borrowedLabel(palace: PalaceResponse): string {
  if (palace.borrowed_from_palace) return `借星·${palace.borrowed_from_palace.replace('宫', '')}`
  if (palace.is_empty_palace) return '借星·对宫'
  return ''
}

function starLine(star: StarInfo): string {
  const tf = star.transforms?.[0]
  return `${star.name}${star.brightness ? `(${star.brightness})` : ''}${tf ? `·${tf}` : ''}`
}

function auxStarsText(palace: PalaceResponse): string {
  const stars = palace.aux_stars?.slice(0, props.showAuxLimit).map(starLine).filter(Boolean) ?? []
  return stars.length ? stars.join(' · ') : ''
}

function palaceClass(palace: PalaceResponse): Record<string, boolean> {
  const name = palace.name || ''
  return {
    'fz-cell--life': name.includes('命') && !name.includes('身'),
    'fz-cell--body': isBodyPalace(palace),
    'fz-cell--borrow': hasBorrowedStars(palace) && !palace.main_stars?.length,
  }
}

function transformStyle(star: StarInfo) {
  const tf = star.transforms?.[0]
  if (!tf || !SIHUA_COLORS[tf]) return undefined
  return { color: SIHUA_COLORS[tf] }
}

function displayStars(palace: PalaceResponse): StarInfo[] {
  if (palace.main_stars?.length) return palace.main_stars
  return palace.borrowed_main_stars ?? []
}
</script>

<template>
  <div class="fusheng-ziwei-plate" :class="{ 'is-readonly': readonly }">
    <div v-if="showOverlayControls" class="fusheng-ziwei-plate__toolbar">
      <span class="fz-toolbar__label">叠宫</span>
      <button
        v-for="item in overlayLayers"
        :key="item.key"
        type="button"
        class="fz-toolbar__btn"
        :class="{ 'is-active': overlayLayer === item.key }"
        @click="setOverlayLayer(item.key)"
      >
        {{ item.label }}
      </button>
    </div>
    <div class="fusheng-ziwei-plate__grid">
      <template v-for="(cell, idx) in palaceGrid" :key="idx">
        <div v-if="cell.empty" class="fz-center">
          <p class="fz-center__ju">{{ result.wuxing_ju_name }}</p>
          <p class="fz-center__gz">
            {{ result.lunar.year_gz }}
            {{ result.lunar.jieqi_month_gz || result.lunar.month_gz }}
            {{ result.lunar.day_gz }}
            {{ result.lunar.hour_gz || result.lunar.hour_branch }}
          </p>
          <p class="fz-center__birth">{{ result.birth_solar }}</p>
          <p class="fz-center__meta">命·{{ result.life_ruler_star || '—' }} 身·{{ result.body_ruler_star || '—' }}</p>
        </div>
        <div
          v-else
          class="fz-cell"
          :class="[palaceClass(cell.palace), { 'fz-cell--overlay': isOverlayHighlight(cell.palace) }]"
        >
          <div class="fz-cell__head">
            <span class="fz-cell__name">
              {{ cell.palace.name.replace('宫', '') }}
              <span v-if="isBodyPalace(cell.palace)" class="fz-badge fz-badge--body">身宫</span>
            </span>
            <span class="fz-cell__gz">{{ cell.palace.stem }}{{ cell.palace.branch }}</span>
          </div>
          <p v-if="cellBadges(cell.palace).length" class="fz-cell__overlay">
            <span v-for="(tag, tIdx) in cellBadges(cell.palace)" :key="tIdx" class="fz-overlay-tag">{{ tag }}</span>
          </p>
          <p v-if="hasBorrowedStars(cell.palace) && !cell.palace.main_stars?.length" class="fz-cell__borrow">
            {{ borrowedLabel(cell.palace) }}
          </p>
          <p class="fz-cell__stars">
            <span
              v-for="(star, sIdx) in displayStars(cell.palace)"
              :key="`m-${sIdx}`"
              class="fz-star"
              :class="{ 'fz-star--borrowed': hasBorrowedStars(cell.palace) && !cell.palace.main_stars?.length }"
              :style="transformStyle(star)"
            >{{ starLine(star) }}</span>
          </p>
          <p v-if="auxStarsText(cell.palace)" class="fz-cell__aux">{{ auxStarsText(cell.palace) }}</p>
        </div>
      </template>
    </div>
    <div class="fusheng-ziwei-plate__legend">
      <span class="fz-legend__label">四化</span>
      <span v-for="item in SIHUA_LEGEND" :key="item.key" class="fz-legend__chip">
        <i class="fz-legend__dot" :style="{ background: item.color }" />
        {{ item.label }}
      </span>
      <span class="fz-legend__note">庙旺利陷已标注；借星以虚线显示</span>
    </div>
  </div>
</template>

<style scoped>
.fusheng-ziwei-plate {
  margin-top: 16px;
  overflow-x: auto;
}

.fusheng-ziwei-plate__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.fz-toolbar__label {
  font-size: 11px;
  font-weight: 700;
  color: #57534e;
}

.fz-toolbar__btn {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #d6c9b3;
  background: #fffdf7;
  font-size: 11px;
  cursor: pointer;
  color: #44403c;
}

.fz-toolbar__btn.is-active {
  background: #8b5e34;
  border-color: #8b5e34;
  color: #fff;
}

.fz-cell--overlay {
  box-shadow: inset 0 0 0 2px #f59e0b;
  background: #fffbeb;
}

.fz-cell__overlay {
  margin: 4px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.fz-overlay-tag {
  display: inline-block;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 8px;
  font-weight: 700;
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
  line-height: 1.5;
}

.fusheng-ziwei-plate__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(96px, 1fr));
  border: 1.5px solid #c9b99a;
  background: #e8dcc8;
  min-width: 400px;
}

.fz-cell,
.fz-center {
  min-height: 108px;
  padding: 6px;
  border-right: 1px solid #d6c9b3;
  border-bottom: 1px solid #d6c9b3;
  background: #fffdf7;
}

.fz-center {
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

.fz-center__ju {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #8b5e34;
  font-family: var(--font-cn);
}

.fz-center__gz,
.fz-center__birth,
.fz-center__meta {
  margin: 0;
  font-size: 10px;
  color: #57534e;
}

.fz-cell--life { border-top: 3px solid #dc2626; }
.fz-cell--body { border-top: 3px solid #2563eb; }
.fz-cell--borrow { background: #faf8f3; }

.fz-cell__head {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  align-items: flex-start;
}

.fz-cell__name {
  font-size: 10px;
  color: #78716c;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.fz-badge {
  display: inline-block;
  padding: 0 4px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  line-height: 1.5;
}

.fz-badge--body {
  color: var(--brand-gold-dark);
  background: var(--brand-gold-lt);
}

.fz-cell__borrow {
  margin: 2px 0 0;
  font-size: 9px;
  color: #78716c;
}

.fz-cell__gz {
  font-size: 11px;
  font-weight: 700;
  color: #44403c;
}

.fz-cell__stars {
  margin: 6px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  font-family: var(--font-cn);
  line-height: 1.35;
}

.fz-star {
  color: #1a1410;
}

.fz-star--borrowed {
  text-decoration: underline;
  text-decoration-style: dashed;
  text-decoration-color: #a8a29e;
  text-underline-offset: 2px;
}

.fz-cell__aux {
  margin: 4px 0 0;
  font-size: 9px;
  color: #78716c;
  line-height: 1.45;
}

.fusheng-ziwei-plate__legend {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 10px;
  color: var(--text-3, #78716c);
}

.fz-legend__label {
  font-weight: 700;
  color: #57534e;
}

.fz-legend__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.fz-legend__dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.fz-legend__note {
  opacity: 0.85;
}

@media print {
  .fusheng-ziwei-plate { overflow: visible; }
  .fusheng-ziwei-plate__grid { min-width: 100%; }
  .fz-cell { min-height: 120px; }
}
</style>
