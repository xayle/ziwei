import { computed, type ComputedRef, type Ref } from 'vue'

type OverlayFeedbackType = 'success' | 'info' | 'error'
type CaseWorkflowTarget = 'cases' | 'snapshots' | 'similar'

type ActionMenuBindings = {
  hasResult: boolean
  hasSavedCase: boolean
  reviewSubmitting: boolean
  historyCount: number
  onOpenCaseWorkflow: (target: CaseWorkflowTarget) => void
  onSubmitCurrentReview: () => void
  onToggleReviewPanel: () => void
  onToggleLlmPanel: () => void
  onToggleOpsPanel: () => void
  onToggleBatchPanel: () => void
  onToggleGlossaryPanel: () => void
  onToggleMultiCompatPanel: () => void
  onToggleFengshuiPanel: () => void
  onOpenStarSearch: () => void
  onToggleBrightnessLegend: () => void
  onToggleHotkeyPanel: () => void
  onToggleHistoryPanel: () => void
}

type OverlayFeedbackState = {
  panel: string
  type: OverlayFeedbackType
  message: string
}

type UseZiweiInfoBarActionsBindingsOptions = {
  overlayFeedback: Ref<OverlayFeedbackState | null>
  isOverlayFeedbackVisible: (panel: string) => boolean
  isExportingImage: Ref<boolean>
  canSaveCurrentChart: Ref<boolean>
  isSavingCase: Ref<boolean>
  savedCaseId: Ref<string>
  exportPDF: () => void
  exportChartAsImage: () => void
  gotoZeri: () => void
  gotoAi: () => void
  saveCurrentChart: () => void
  actionMenuBindings: ComputedRef<ActionMenuBindings>
}

export function useZiweiInfoBarActionsBindings(options: UseZiweiInfoBarActionsBindingsOptions) {
  const infoBarActionsBindings = computed(() => ({
    feedbackVisible: options.isOverlayFeedbackVisible('chart'),
    feedbackMessage: options.overlayFeedback.value?.message ?? '',
    feedbackType: options.overlayFeedback.value?.type ?? null,
    isExportingImage: options.isExportingImage.value,
    canSaveCurrentChart: options.canSaveCurrentChart.value,
    isSavingCase: options.isSavingCase.value,
    hasSavedCase: Boolean(options.savedCaseId.value),
    onExportPdf: options.exportPDF,
    onExportChartAsImage: options.exportChartAsImage,
    onGotoZeri: options.gotoZeri,
    onGotoAi: options.gotoAi,
    onSaveCurrentChart: options.saveCurrentChart,
    actionMenuBindings: options.actionMenuBindings.value,
  }))

  return {
    infoBarActionsBindings,
  }
}
