import { computed, type Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import { useZiweiPageBridge } from '@/composables/useZiweiPageBridge'
import { useZiweiToolPanels } from '@/composables/useZiweiToolPanels'

type CompareForm = {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
}

type UseZiweiToolPanelBindingsOptions = {
  result: Ref<ZiweiResponse | null>
  showHotkeyPanel: Ref<boolean>
  selectPalace: (palace: PalaceResponse) => void
  selectPalaceByIndex: (index: number) => void
  showBookmarksPanel: Ref<boolean>
  bookmarkedPalaces: Ref<PalaceResponse[]>
  togglePalaceBookmark: (index: number) => void
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  minute: Ref<number>
  gender: Ref<'男' | '女'>
  longitude: Ref<number | undefined>
  getMonthForecast: (month: number) => { score?: number } | null | undefined
}

export function useZiweiToolPanelBindings(options: UseZiweiToolPanelBindingsOptions) {
  const bridge = useZiweiPageBridge({
    result: options.result,
    showHotkeyPanel: options.showHotkeyPanel,
    selectPalace: options.selectPalace,
  })

  const toolPanels = useZiweiToolPanels({
    result: options.result,
    year: options.year,
    month: options.month,
    day: options.day,
    hour: options.hour,
    minute: options.minute,
    gender: options.gender,
    longitude: options.longitude,
    getMonthForecast: options.getMonthForecast,
  })

  const compareForm = computed<CompareForm>({
    get: () => ({
      year: toolPanels.compareYear.value,
      month: toolPanels.compareMonth.value,
      day: toolPanels.compareDay.value,
      hour: toolPanels.compareHour.value,
      minute: toolPanels.compareMinute.value,
      gender: toolPanels.compareGender.value,
    }),
    set: (value) => {
      toolPanels.compareYear.value = value.year
      toolPanels.compareMonth.value = value.month
      toolPanels.compareDay.value = value.day
      toolPanels.compareHour.value = value.hour
      toolPanels.compareMinute.value = value.minute
      toolPanels.compareGender.value = value.gender
    },
  })

  function updateCompareForm(value: CompareForm) {
    compareForm.value = value
  }

  const centerOverlayPanelBindings = computed(() => ({
    showSharePanel: toolPanels.showSharePanel.value,
    shareLink: toolPanels.shareLink.value,
    showCalendarView: toolPanels.showCalendarView.value,
    calendarViewYear: toolPanels.calendarViewYear.value,
    calendarViewMonth: toolPanels.calendarViewMonth.value,
    calendarGrid: toolPanels.calendarGrid.value,
    getDayFortuneClass: toolPanels.getDayFortuneClass,
    showComparePanel: toolPanels.showComparePanel.value,
    compareForm: compareForm.value,
    compareTarget: toolPanels.compareTarget.value,
    showBookmarksPanel: options.showBookmarksPanel.value,
    bookmarkedPalaces: options.bookmarkedPalaces.value,
    onCloseSharePanel: toolPanels.closeSharePanel,
    onCopyShareLink: toolPanels.copyShareLink,
    onPrevCalendarMonth: toolPanels.prevCalendarMonth,
    onNextCalendarMonth: toolPanels.nextCalendarMonth,
    onCloseCalendarView: toolPanels.closeCalendarView,
    onCloseComparePanel: toolPanels.closeComparePanel,
    'onUpdate:compareForm': updateCompareForm,
    onClearCompareTarget: toolPanels.clearCompareTarget,
    onSetCompareTarget: toolPanels.setCompareTarget,
    onCloseBookmarksPanel: () => {
      options.showBookmarksPanel.value = false
    },
    onSelectBookmarkedPalace: (index: number) => {
      options.selectPalaceByIndex(index)
      options.showBookmarksPanel.value = false
    },
    onTogglePalaceBookmark: options.togglePalaceBookmark,
  }))

  return {
    bridge,
    centerOverlayPanelBindings,
    toggleSharePanel: toolPanels.toggleSharePanel,
    toggleComparePanel: toolPanels.toggleComparePanel,
    toggleCalendarView: toolPanels.toggleCalendarView,
  }
}
