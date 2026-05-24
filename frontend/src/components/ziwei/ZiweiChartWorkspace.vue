<script setup lang="ts">
import type { DayunItem, PalaceResponse } from '@/api/ziwei'
import type { ZiweiChartCanvasBindings } from '@/composables/useZiweiChartCanvasBindings'
import ZiweiChartCanvas from './ZiweiChartCanvas.vue'
import ZiweiPalaceDetailPanel from './ZiweiPalaceDetailPanel.vue'
import ZiweiTimelineBar from './ZiweiTimelineBar.vue'

type ZiweiTimelineBindings = {
  items: DayunItem[]
  currentDayunGanzhi: string | null
  selectedDaxianIdx: number
  selectedLiunianYear: number
  allLiunianYears: number[]
  liunianYears: number[]
  currentYear: number
  birthYear: number
  onToggleDaxian: (index: number) => void
  'onUpdate:selectedLiunianYear': (year: number) => void
  onStepLiunian: (delta: number) => void
}

type ZiweiPalaceDetailBindings = {
  selectedPalace: PalaceResponse | null
  starredStarsDistribution: Array<{ star: string; palaces: string[] }>
  showStarTooltip: (starName: string, event: MouseEvent) => void
  hideStarTooltip: () => void
  toggleStarStar: (starName: string) => void
  isStarStarred: (starName: string) => boolean
  tfColorStyle: (transform: string) => Record<string, string>
  onClose: () => void
}

const props = defineProps<{
  chartCanvasBindings: ZiweiChartCanvasBindings
  timelineBindings: ZiweiTimelineBindings
  palaceDetailBindings: ZiweiPalaceDetailBindings
}>()
</script>

<template>
  <div class="chart-workspace">
    <ZiweiChartCanvas v-bind="props.chartCanvasBindings" />

    <!-- 四化图例：说明各层叠化来源，避免"多处化权"视觉误解 -->
    <div class="sihua-legend">
      <span class="sl-label">四化说明：</span>
      <span class="sl-item">
        <span class="sl-tf sl-tf-ming">生禄</span>
        本命
      </span>
      <span class="sl-sep">·</span>
      <span class="sl-item">
        <span class="sl-tf sl-tf-daxian">限禄</span>
        大限
      </span>
      <span class="sl-sep">·</span>
      <span class="sl-item">
        <span class="sl-tf sl-tf-liunian">年禄</span>
        流年
      </span>
      <span class="sl-sep">·</span>
      <span class="sl-item">
        <span class="sl-tf sl-tf-liuyue">月禄</span>
        流月
      </span>
      <span class="sl-note">（同星多处标注为正常叠化现象）</span>
    </div>

    <ZiweiTimelineBar v-if="props.timelineBindings.items.length" v-bind="props.timelineBindings" />
    <ZiweiPalaceDetailPanel v-bind="props.palaceDetailBindings" />
  </div>
</template>

<style scoped>
.sihua-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 6px;
  font-size: 10px;
  color: #78716c;
  padding: 4px 8px;
  background: #faf9f7;
  border-top: 1px solid #e5e0d8;
  border-bottom: 1px solid #e5e0d8;
  margin-bottom: 4px;
  line-height: 1.4;
}

.sl-label {
  font-weight: 600;
  color: #57534e;
  margin-right: 2px;
}

.sl-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.sl-sep {
  color: #d1ccc4;
  user-select: none;
}

.sl-note {
  color: #a8a29e;
  font-size: 9px;
  margin-left: 4px;
}

/* 本命四化 — 实心绿色（化禄示例） */
.sl-tf {
  font-size: 9px;
  font-weight: 800;
  padding: 0 3px;
  border-radius: 2px;
  line-height: 1.5;
}

.sl-tf-ming {
  background: #16a34a;
  color: #fff;
}

/* 大限四化 — 虚线框绿色（化禄示例） */
.sl-tf-daxian {
  border: 1px dashed #166534;
  color: #166534;
  background: transparent;
}

/* 流年四化 — 点线框绿色 */
.sl-tf-liunian {
  border: 1px dotted #166534;
  color: #166534;
  background: transparent;
}

/* 流月四化 — 细线框绿色 */
.sl-tf-liuyue {
  border: 1px solid #166534;
  border-radius: 3px;
  color: #166534;
  background: transparent;
}
</style>
