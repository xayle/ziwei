import { computed, type Ref } from 'vue'
import type { ZiweiChartHistoryItem } from '@/composables/useZiweiViewPreferences'

type HotkeyItem = {
  key: string
  desc: string
}

type BrightnessLegendItem = {
  level: string
  desc: string
  color: string
}

type CaseWorkflowTarget = 'cases' | 'snapshots' | 'similar'

type UseZiweiActionMenuBindingsOptions = {
  hasResult: () => boolean
  savedCaseId: Ref<string>
  reviewSubmitting: Ref<boolean>
  historyCount: Ref<number>
  openCaseWorkflow: (target: CaseWorkflowTarget) => void
  submitCurrentReview: () => void
  toggleReviewPanel: () => void
  toggleLlmPanel: () => void
  toggleOpsPanel: () => void
  toggleBatchPanel: () => void
  toggleGlossaryPanel: () => void
  toggleMultiCompatPanel: () => void
  toggleFengshuiPanel: () => void
  showHotkeyPanel: Ref<boolean>
  hotkeyList: readonly HotkeyItem[]
  showBrightnessLegend: Ref<boolean>
  brightnessLegend: readonly BrightnessLegendItem[]
  showHistoryPanel: Ref<boolean>
  chartHistory: Ref<ZiweiChartHistoryItem[]>
  formatHistoryTime: (timestamp: number) => string
  toggleHistoryPanel: () => void
  clearHistory: () => void
  restoreFromHistory: (item: ZiweiChartHistoryItem) => void
  openStarSearch: () => void
}

export function useZiweiActionMenuBindings(options: UseZiweiActionMenuBindingsOptions) {
  function toggleHotkeyPanel() {
    options.showHotkeyPanel.value = !options.showHotkeyPanel.value
  }

  function closeHotkeyPanel() {
    options.showHotkeyPanel.value = false
  }

  function toggleBrightnessLegend() {
    options.showBrightnessLegend.value = !options.showBrightnessLegend.value
  }

  function closeBrightnessLegend() {
    options.showBrightnessLegend.value = false
  }

  function closeHistoryPanel() {
    options.showHistoryPanel.value = false
  }

  const actionMenuBindings = computed(() => ({
    hasResult: options.hasResult(),
    hasSavedCase: Boolean(options.savedCaseId.value),
    reviewSubmitting: options.reviewSubmitting.value,
    historyCount: options.historyCount.value,
    onOpenCaseWorkflow: options.openCaseWorkflow,
    onSubmitCurrentReview: options.submitCurrentReview,
    onToggleReviewPanel: options.toggleReviewPanel,
    onToggleLlmPanel: options.toggleLlmPanel,
    onToggleOpsPanel: options.toggleOpsPanel,
    onToggleBatchPanel: options.toggleBatchPanel,
    onToggleGlossaryPanel: options.toggleGlossaryPanel,
    onToggleMultiCompatPanel: options.toggleMultiCompatPanel,
    onToggleFengshuiPanel: options.toggleFengshuiPanel,
    onOpenStarSearch: options.openStarSearch,
    onToggleBrightnessLegend: toggleBrightnessLegend,
    onToggleHotkeyPanel: toggleHotkeyPanel,
    onToggleHistoryPanel: options.toggleHistoryPanel,
  }))

  const toolPanelsBindings = computed(() => ({
    showHotkeyPanel: options.showHotkeyPanel.value,
    hotkeyList: [...options.hotkeyList],
    showBrightnessLegend: options.showBrightnessLegend.value,
    brightnessLegend: [...options.brightnessLegend],
    showHistoryPanel: options.showHistoryPanel.value,
    historyItems: options.chartHistory.value,
    formatHistoryTime: options.formatHistoryTime,
    onCloseHotkeyPanel: closeHotkeyPanel,
    onCloseBrightnessLegend: closeBrightnessLegend,
    onClearHistory: options.clearHistory,
    onCloseHistoryPanel: closeHistoryPanel,
    onRestoreHistory: options.restoreFromHistory,
  }))

  return {
    actionMenuBindings,
    toolPanelsBindings,
    toggleHotkeyPanel,
  }
}
