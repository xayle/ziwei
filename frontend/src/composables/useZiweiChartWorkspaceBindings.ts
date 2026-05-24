import { computed, type ComputedRef, type Ref } from 'vue'
import type { DayunItem, PalaceResponse } from '@/api/ziwei'
import type { ZiweiChartCanvasBindings } from '@/composables/useZiweiChartCanvasBindings'

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

type UseZiweiChartWorkspaceBindingsOptions = {
  chartCanvasBindings: ComputedRef<ZiweiChartCanvasBindings>
  dayunItems: ComputedRef<DayunItem[]>
  currentDayunGanzhi: ComputedRef<string | null>
  selectedDaxianIdx: Ref<number>
  selectedLiunianYear: Ref<number>
  allLiunianYears: ComputedRef<number[]>
  liunianYears: ComputedRef<number[]>
  currentYear: number
  birthYear: Ref<number>
  toggleSelectedDaxian: (index: number) => void
  setSelectedLiunianYearValue: (year: number) => void
  stepSelectedLiunianYear: (delta: number) => void
  selectedPalace: Ref<PalaceResponse | null>
  starredStarsDistribution: ComputedRef<Array<{ star: string; palaces: string[] }>>
  showStarTooltip: (starName: string, event: MouseEvent) => void
  hideStarTooltip: () => void
  toggleStarStar: (starName: string) => void
  isStarStarred: (starName: string) => boolean
  tfColorStyle: (transform: string) => Record<string, string>
  closeSelectedPalace: () => void
}

export type ZiweiChartWorkspaceBindings = {
  chartCanvasBindings: ZiweiChartCanvasBindings
  timelineBindings: ZiweiTimelineBindings
  palaceDetailBindings: ZiweiPalaceDetailBindings
}

export function useZiweiChartWorkspaceBindings(options: UseZiweiChartWorkspaceBindingsOptions) {
  const timelineBindings = computed<ZiweiTimelineBindings>(() => ({
    items: options.dayunItems.value,
    currentDayunGanzhi: options.currentDayunGanzhi.value,
    selectedDaxianIdx: options.selectedDaxianIdx.value,
    selectedLiunianYear: options.selectedLiunianYear.value,
    allLiunianYears: options.allLiunianYears.value,
    liunianYears: options.liunianYears.value,
    currentYear: options.currentYear,
    birthYear: options.birthYear.value,
    onToggleDaxian: options.toggleSelectedDaxian,
    'onUpdate:selectedLiunianYear': options.setSelectedLiunianYearValue,
    onStepLiunian: options.stepSelectedLiunianYear,
  }))

  const palaceDetailBindings = computed<ZiweiPalaceDetailBindings>(() => ({
    selectedPalace: options.selectedPalace.value,
    starredStarsDistribution: options.starredStarsDistribution.value,
    showStarTooltip: options.showStarTooltip,
    hideStarTooltip: options.hideStarTooltip,
    toggleStarStar: options.toggleStarStar,
    isStarStarred: options.isStarStarred,
    tfColorStyle: options.tfColorStyle,
    onClose: options.closeSelectedPalace,
  }))

  const chartWorkspaceBindings = computed<ZiweiChartWorkspaceBindings>(() => ({
    chartCanvasBindings: options.chartCanvasBindings.value,
    timelineBindings: timelineBindings.value,
    palaceDetailBindings: palaceDetailBindings.value,
  }))

  return {
    chartWorkspaceBindings,
  }
}
