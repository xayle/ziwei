<script setup lang="ts">
import type { ZiweiResponse } from '@/api/ziwei'
import type { ZiweiChartHistoryItem } from '@/composables/useZiweiViewPreferences'
import ZiweiInfoBarActions from './ZiweiInfoBarActions.vue'
import ZiweiInfoBarMeta from './ZiweiInfoBarMeta.vue'
import ZiweiToolPanels from './ZiweiToolPanels.vue'

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

type InfoBarActionsBindings = {
  feedbackVisible: boolean
  feedbackMessage: string
  feedbackType: OverlayFeedbackType | null
  isExportingImage: boolean
  canSaveCurrentChart: boolean
  isSavingCase: boolean
  hasSavedCase: boolean
  onExportPdf: () => void
  onExportChartAsImage: () => void
  onGotoZeri: () => void
  onGotoAi: () => void
  onSaveCurrentChart: () => void
  actionMenuBindings: ActionMenuBindings
}

type HotkeyItem = {
  key: string
  desc: string
}

type BrightnessLegendItem = {
  level: string
  desc: string
  color: string
}

type ToolPanelsBindings = {
  showHotkeyPanel: boolean
  hotkeyList: HotkeyItem[]
  showBrightnessLegend: boolean
  brightnessLegend: BrightnessLegendItem[]
  showHistoryPanel: boolean
  historyItems: ZiweiChartHistoryItem[]
  formatHistoryTime: (timestamp: number) => string
  onCloseHotkeyPanel: () => void
  onCloseBrightnessLegend: () => void
  onClearHistory: () => void
  onCloseHistoryPanel: () => void
  onRestoreHistory: (item: ZiweiChartHistoryItem) => void
}

const props = defineProps<{
  result: ZiweiResponse
  juColors: Record<number | string, string>
  infoBarActionsBindings: InfoBarActionsBindings
  toolPanelsBindings: ToolPanelsBindings
}>()
</script>

<template>
  <div class="result-header">
    <div class="info-bar card">
      <ZiweiInfoBarMeta :result="props.result" :ju-colors="props.juColors" />
      <ZiweiInfoBarActions v-bind="props.infoBarActionsBindings" />
    </div>

    <ZiweiToolPanels v-bind="props.toolPanelsBindings" />
  </div>
</template>

<style scoped>
.info-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
}

@media print {
  .info-bar {
    border: none;
    padding: 8px 0;
    flex-wrap: wrap;
    justify-content: flex-start;
    gap: 12px;
    background: transparent !important;
  }
}
</style>
