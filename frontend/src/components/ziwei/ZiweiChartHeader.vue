<script setup lang="ts">
import type { DayunItem, PalaceResponse } from '@/api/ziwei'
import type { ZiweiChartTheme, ZiweiFontSizeLevel } from '@/composables/useZiweiViewPreferences'
import ZiweiChartControls from './ZiweiChartControls.vue'
import ZiweiCurrentDayunTip from './ZiweiCurrentDayunTip.vue'
import ZiweiChartSummarySection from './ZiweiChartSummarySection.vue'
import ZiweiPalaceQuickNav from './ZiweiPalaceQuickNav.vue'

type ChartMode = 'feixing' | 'sanhe' | 'sihua'

type StarDisplayOptions = {
  showMainStars: boolean
  showAuxStars: boolean
  showTransforms: boolean
  showBrightness: boolean
  showChangsheng: boolean
  showBoshi: boolean
  showJiangSui: boolean
}

type OverlayDisplayOptions = {
  showDaxian: boolean
  showLiunian: boolean
  showLiuyue: boolean
  showXiaoxian: boolean
}

type LiuyueOption = {
  month: number
  month_name: string
  month_gz: string
}

type ChartQuickInsightItem = {
  label: string
  value: string
  sub?: string
  cls?: string
}

type ChartSummaryStats = {
  totalMainStars: number
  totalAuxStars: number
  totalTransforms: number
  luCount: number
  quanCount: number
  keCount: number
  jiCount: number
  brightStars: number
  weakStars: number
  shaCount: number
  jiStarCount: number
  patternsCount: number
}

const props = defineProps<{
  chartMode: ChartMode
  showSihuaLines: boolean
  showLiunianOverlay: boolean
  selectedLiuyueMonth: number
  liuyueOptions: LiuyueOption[]
  starDisplayOpts: StarDisplayOptions
  overlayOpts: OverlayDisplayOptions
  showThemePanel: boolean
  chartTheme: ZiweiChartTheme
  fontSizeLevel: ZiweiFontSizeLevel
  chartThemes: Array<{ id: ZiweiChartTheme; name: string; desc: string; colors: { primary: string; bg: string } }>
  fontSizeOptions: Array<{ id: ZiweiFontSizeLevel; label: string; scale: number }>
  currentDayun: DayunItem | null
  quickInsights: ChartQuickInsightItem[]
  summaryStats: ChartSummaryStats | null
  palaces: PalaceResponse[]
  selectedPalace: PalaceResponse | null
  palaceHasTransform: (palace: PalaceResponse, transform: string) => boolean
  getPalaceQuickInfo: (palace: PalaceResponse) => string
}>()

const emit = defineEmits<{
  'update:chartMode': [value: ChartMode]
  'update:showSihuaLines': [value: boolean]
  'update:showLiunianOverlay': [value: boolean]
  'update:selectedLiuyueMonth': [value: number]
  'update:starDisplayOpts': [value: StarDisplayOptions]
  'update:overlayOpts': [value: OverlayDisplayOptions]
  toggleThemePanel: []
  closeThemePanel: []
  setChartTheme: [value: ZiweiChartTheme]
  setFontSize: [value: ZiweiFontSizeLevel]
  select: [palace: PalaceResponse]
}>()
</script>

<template>
  <div class="chart-header">
    <ZiweiChartControls
      :chart-mode="props.chartMode"
      :show-sihua-lines="props.showSihuaLines"
      :show-liunian-overlay="props.showLiunianOverlay"
      :selected-liuyue-month="props.selectedLiuyueMonth"
      :liuyue-options="props.liuyueOptions"
      :star-display-opts="props.starDisplayOpts"
      :overlay-opts="props.overlayOpts"
      :show-theme-panel="props.showThemePanel"
      :chart-theme="props.chartTheme"
      :font-size-level="props.fontSizeLevel"
      :chart-themes="props.chartThemes"
      :font-size-options="props.fontSizeOptions"
      @update:chart-mode="emit('update:chartMode', $event)"
      @update:show-sihua-lines="emit('update:showSihuaLines', $event)"
      @update:show-liunian-overlay="emit('update:showLiunianOverlay', $event)"
      @update:selected-liuyue-month="emit('update:selectedLiuyueMonth', $event)"
      @update:star-display-opts="emit('update:starDisplayOpts', $event)"
      @update:overlay-opts="emit('update:overlayOpts', $event)"
      @toggle-theme-panel="emit('toggleThemePanel')"
      @close-theme-panel="emit('closeThemePanel')"
      @set-chart-theme="emit('setChartTheme', $event)"
      @set-font-size="emit('setFontSize', $event)"
    />

    <ZiweiCurrentDayunTip :current-dayun="props.currentDayun" />

    <ZiweiChartSummarySection :quick-insights="props.quickInsights" :summary-stats="props.summaryStats" />

    <ZiweiPalaceQuickNav
      :palaces="props.palaces"
      :selected-palace="props.selectedPalace"
      :palace-has-transform="props.palaceHasTransform"
      :get-palace-quick-info="props.getPalaceQuickInfo"
      @select="emit('select', $event)"
    />
  </div>
</template>
