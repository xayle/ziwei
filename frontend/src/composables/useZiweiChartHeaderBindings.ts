import { computed, type ComputedRef, type Ref } from 'vue'
import type { DayunItem, PalaceResponse } from '@/api/ziwei'
import type { ZiweiChartTheme, ZiweiFontSizeLevel } from '@/composables/useZiweiViewPreferences'

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

type UseZiweiChartHeaderBindingsOptions = {
  chartMode: Ref<ChartMode>
  showSihuaLines: Ref<boolean>
  showLiunianOverlay: Ref<boolean>
  selectedLiuyueMonth: Ref<number>
  liuyueOptions: ComputedRef<LiuyueOption[]>
  starDisplayOpts: StarDisplayOptions
  overlayOpts: OverlayDisplayOptions
  showThemePanel: Ref<boolean>
  chartTheme: Ref<ZiweiChartTheme>
  fontSizeLevel: Ref<ZiweiFontSizeLevel>
  chartThemes: Array<{ id: ZiweiChartTheme; name: string; desc: string; colors: { primary: string; bg: string } }>
  fontSizeOptions: Array<{ id: ZiweiFontSizeLevel; label: string; scale: number }>
  currentDayun: Ref<DayunItem | null>
  chartSummarySectionBindings: ComputedRef<{
    quickInsights: ChartQuickInsightItem[]
    summaryStats: ChartSummaryStats | null
  }>
  palaces: ComputedRef<PalaceResponse[]>
  selectedPalace: Ref<PalaceResponse | null>
  palaceHasTransform: (palace: PalaceResponse, transform: string) => boolean
  getPalaceQuickInfo: (palace: PalaceResponse) => string
  toggleThemePanel: () => void
  closeThemePanel: () => void
  setChartTheme: (value: ZiweiChartTheme) => void
  setFontSize: (value: ZiweiFontSizeLevel) => void
  selectPalace: (palace: PalaceResponse) => void
}

export type ZiweiChartHeaderBindings = {
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
  'onUpdate:chartMode': (value: ChartMode) => void
  'onUpdate:showSihuaLines': (value: boolean) => void
  'onUpdate:showLiunianOverlay': (value: boolean) => void
  'onUpdate:selectedLiuyueMonth': (value: number) => void
  'onUpdate:starDisplayOpts': (value: StarDisplayOptions) => void
  'onUpdate:overlayOpts': (value: OverlayDisplayOptions) => void
  onToggleThemePanel: () => void
  onCloseThemePanel: () => void
  onSetChartTheme: (value: ZiweiChartTheme) => void
  onSetFontSize: (value: ZiweiFontSizeLevel) => void
  onSelect: (palace: PalaceResponse) => void
}

export function useZiweiChartHeaderBindings(options: UseZiweiChartHeaderBindingsOptions) {
  const chartHeaderBindings = computed<ZiweiChartHeaderBindings>(() => ({
    chartMode: options.chartMode.value,
    showSihuaLines: options.showSihuaLines.value,
    showLiunianOverlay: options.showLiunianOverlay.value,
    selectedLiuyueMonth: options.selectedLiuyueMonth.value,
    liuyueOptions: options.liuyueOptions.value,
    starDisplayOpts: options.starDisplayOpts,
    overlayOpts: options.overlayOpts,
    showThemePanel: options.showThemePanel.value,
    chartTheme: options.chartTheme.value,
    fontSizeLevel: options.fontSizeLevel.value,
    chartThemes: options.chartThemes,
    fontSizeOptions: options.fontSizeOptions,
    currentDayun: options.currentDayun.value,
    quickInsights: options.chartSummarySectionBindings.value.quickInsights,
    summaryStats: options.chartSummarySectionBindings.value.summaryStats,
    palaces: options.palaces.value,
    selectedPalace: options.selectedPalace.value,
    palaceHasTransform: options.palaceHasTransform,
    getPalaceQuickInfo: options.getPalaceQuickInfo,
    'onUpdate:chartMode': (value: ChartMode) => {
      options.chartMode.value = value
    },
    'onUpdate:showSihuaLines': (value: boolean) => {
      options.showSihuaLines.value = value
    },
    'onUpdate:showLiunianOverlay': (value: boolean) => {
      options.showLiunianOverlay.value = value
    },
    'onUpdate:selectedLiuyueMonth': (value: number) => {
      options.selectedLiuyueMonth.value = value
    },
    'onUpdate:starDisplayOpts': (value: StarDisplayOptions) => {
      Object.assign(options.starDisplayOpts, value)
    },
    'onUpdate:overlayOpts': (value: OverlayDisplayOptions) => {
      Object.assign(options.overlayOpts, value)
    },
    onToggleThemePanel: options.toggleThemePanel,
    onCloseThemePanel: options.closeThemePanel,
    onSetChartTheme: options.setChartTheme,
    onSetFontSize: options.setFontSize,
    onSelect: options.selectPalace,
  }))

  return {
    chartHeaderBindings,
  }
}
