<script setup lang="ts">
import ZiweiActionMenus from './ZiweiActionMenus.vue'

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

const props = defineProps<{
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
}>()
</script>

<template>
  <div class="info-bar-actions">
    <div v-if="props.feedbackVisible" :class="['panel-feedback', props.feedbackType, 'no-print']">
      {{ props.feedbackMessage }}
    </div>

    <button class="btn-export no-print" @click="props.onExportPdf">⬇ 导出 PDF</button>
    <button class="btn-export no-print" :disabled="props.isExportingImage" @click="props.onExportChartAsImage">
      {{ props.isExportingImage ? 'PNG 导出中…' : '🖼 导出 PNG' }}
    </button>
    <button class="btn-zeri no-print" @click="props.onGotoZeri">📅 择日</button>
    <button class="btn-ai no-print" @click="props.onGotoAi">🤖 AI 解读</button>
    <button class="btn-save-case no-print" :disabled="!props.canSaveCurrentChart" @click="props.onSaveCurrentChart">
      {{ props.isSavingCase ? '保存中…' : props.hasSavedCase ? '✅ 已保存' : '💾 保存命盘' }}
    </button>

    <ZiweiActionMenus v-bind="props.actionMenuBindings" />
  </div>
</template>

<style scoped>
.info-bar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

.btn-export,
.btn-zeri,
.btn-ai,
.btn-save-case {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast);
}

.btn-export {
  background: var(--surface);
  color: var(--accent);
  border: 1.5px solid var(--accent);
}

.btn-export:hover {
  background: var(--accent);
  color: #fff;
}

.btn-zeri {
  background: var(--surface);
  color: #d97706;
  border: 1.5px solid #fbbf24;
}

.btn-zeri:hover {
  background: #fef3c7;
}

.btn-ai {
  background: var(--surface);
  color: #7c3aed;
  border: 1.5px solid #a78bfa;
}

.btn-ai:hover {
  background: #ede9fe;
}

.btn-save-case {
  background: #ecfdf5;
  color: #047857;
  border: 1.5px solid #6ee7b7;
}

.btn-save-case:hover:not(:disabled) {
  background: #d1fae5;
}

.btn-ai:disabled,
.btn-save-case:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .info-bar-actions {
    margin-left: 0;
    width: 100%;
  }
}
</style>
