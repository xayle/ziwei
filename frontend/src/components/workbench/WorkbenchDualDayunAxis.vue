<script setup lang="ts">
interface AxisSegment {
  label: string
  left: number
  width: number
  isActive: boolean
  isPast: boolean
  startYear: number | null
  index?: number
  onSelect: ((index?: number) => void) | (() => void)
}

interface DualDayunAxisData {
  baziSegments: AxisSegment[]
  zwSegments: AxisSegment[]
  nowPct: number
  minYear: number
  maxYear: number
}

const props = defineProps<{
  axis: DualDayunAxisData
  selectedBaziStartYear: number | null | undefined
  selectedZiweiIndex: number | null | undefined
}>()

function selectBazi(seg: AxisSegment) {
  ;(seg.onSelect as () => void)()
}

function selectZiwei(seg: AxisSegment) {
  ;(seg.onSelect as (index: number) => void)(seg.index ?? -1)
}
</script>

<template>
  <div class="wb-section wb-dual-axis-section">
    <h2 class="wb-sec-title">双盘大运对照 <span class="wb-sec-note">{{ props.axis.minYear }}–{{ props.axis.maxYear }}</span></h2>
    <div class="wb-dual-axis">
      <div class="wb-dual-now" :style="{ left: props.axis.nowPct + '%' }">
        <span class="wb-dual-now-label">今</span>
      </div>

      <div class="wb-dual-row">
        <span class="wb-dual-row-label">八字</span>
        <div class="wb-dual-track">
          <button
            v-for="seg in props.axis.baziSegments"
            :key="seg.startYear ?? seg.label"
            type="button"
            class="wb-dual-seg"
            :class="{ active: seg.isActive, past: seg.isPast, selected: seg.startYear === props.selectedBaziStartYear }"
            :style="{ left: seg.left + '%', width: seg.width + '%' }"
            :title="seg.label + ' ' + seg.startYear"
            @click="selectBazi(seg)"
          >{{ seg.label }}</button>
        </div>
      </div>

      <div class="wb-dual-row">
        <span class="wb-dual-row-label">紫微</span>
        <div class="wb-dual-track">
          <button
            v-for="seg in props.axis.zwSegments"
            :key="seg.startYear ?? seg.label"
            type="button"
            class="wb-dual-seg is-zw"
            :class="{ active: seg.isActive, past: seg.isPast, selected: seg.index === props.selectedZiweiIndex }"
            :style="{ left: seg.left + '%', width: seg.width + '%' }"
            :title="seg.label + ' ' + seg.startYear"
            @click="selectZiwei(seg)"
          >{{ seg.label }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wb-dual-axis-section { padding: 0; }
.wb-dual-axis {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0 4px 52px;
}
.wb-dual-now {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(239,68,68,.55);
  z-index: 3;
  pointer-events: none;
}
.wb-dual-now-label {
  position: absolute;
  top: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 700;
  color: #ef4444;
  white-space: nowrap;
}
.wb-dual-row {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px;
}
.wb-dual-row-label {
  position: absolute;
  left: 0;
  width: 44px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-3);
  text-align: right;
  padding-right: 4px;
}
.wb-dual-track {
  position: relative;
  flex: 1;
  height: 28px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.wb-dual-seg {
  position: absolute;
  top: 2px;
  bottom: 2px;
  border-radius: 4px;
  border: 1px solid rgba(99,102,241,.3);
  background: #eef2ff;
  color: #4338ca;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-cn);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  transition: filter .12s, box-shadow .12s;
  min-width: 4px;
  box-sizing: border-box;
}
.wb-dual-seg:hover { filter: brightness(.95); box-shadow: 0 2px 6px rgba(0,0,0,.1); z-index: 2; }
.wb-dual-seg.active { background: #6366f1; color: #fff; border-color: #4f46e5; z-index: 1; }
.wb-dual-seg.past { background: #f3f4f6; color: var(--text-3); border-color: var(--border); }
.wb-dual-seg.selected { outline: 2px solid #6366f1; outline-offset: 1px; z-index: 2; }
.wb-dual-seg.is-zw { background: #f5f3ff; color: #7c3aed; border-color: rgba(124,58,237,.3); }
.wb-dual-seg.is-zw.active { background: #7c3aed; color: #fff; border-color: #6d28d9; }
.wb-dual-seg.is-zw.selected { outline-color: #7c3aed; }

@media (max-width: 1280px) {
  .wb-dual-axis { padding-left: 46px; }
  .wb-dual-row-label { width: 40px; font-size: 10px; }
}

@media (max-width: 900px) {
  .wb-dual-axis { padding-left: 0; gap: 10px; }
  .wb-dual-row { height: auto; align-items: stretch; flex-direction: column; gap: 4px; }
  .wb-dual-row-label { position: static; width: auto; text-align: left; padding-right: 0; }
  .wb-dual-track { height: 30px; }
}

@media (max-width: 560px) {
  .wb-dual-seg { font-size: 9px; padding: 0 2px; }
  .wb-dual-now-label { font-size: 9px; top: -16px; }
}
</style>
