<script setup lang="ts">
type CaseWorkflowTarget = 'cases' | 'snapshots' | 'similar'

const props = defineProps<{
  hasResult: boolean
  hasSavedCase: boolean
  reviewSubmitting: boolean
  historyCount: number
}>()

const emit = defineEmits<{
  openCaseWorkflow: [target: CaseWorkflowTarget]
  submitCurrentReview: []
  toggleReviewPanel: []
  toggleLlmPanel: []
  toggleOpsPanel: []
  toggleBatchPanel: []
  toggleGlossaryPanel: []
  toggleMultiCompatPanel: []
  toggleFengshuiPanel: []
  openStarSearch: []
  toggleBrightnessLegend: []
  toggleHotkeyPanel: []
  toggleHistoryPanel: []
}>()
</script>

<template>
  <div class="ziwei-action-menus no-print">
    <details class="ziwei-action-menu">
      <summary class="btn-cases">📚 案例工作流</summary>
      <div class="ziwei-menu-panel">
        <button class="ziwei-menu-item" @click="emit('openCaseWorkflow', 'cases')">📚 案例工作区</button>
        <button class="ziwei-menu-item" :disabled="!props.hasSavedCase" @click="emit('openCaseWorkflow', 'snapshots')">📸 快照工作区</button>
        <button class="ziwei-menu-item" :disabled="!props.hasResult" @click="emit('openCaseWorkflow', 'similar')">🧭 相似盘工作区</button>
      </div>
    </details>

    <details class="ziwei-action-menu">
      <summary class="btn-review">🧾 协同治理</summary>
      <div class="ziwei-menu-panel">
        <button class="ziwei-menu-item" :disabled="!props.hasResult || props.reviewSubmitting" @click="emit('submitCurrentReview')">
          {{ props.reviewSubmitting ? '🧾 提交中…' : '🧾 提交当前审核' }}
        </button>
        <button class="ziwei-menu-item" @click="emit('toggleReviewPanel')">🗂 审查管理页</button>
        <button class="ziwei-menu-item" :disabled="!props.hasResult" @click="emit('toggleLlmPanel')">✍ AI 草稿页</button>
        <button class="ziwei-menu-item" @click="emit('toggleOpsPanel')">📊 实验管理页</button>
        <button class="ziwei-menu-item" @click="emit('toggleBatchPanel')">📦 批量排盘页</button>
        <button class="ziwei-menu-item" @click="emit('toggleGlossaryPanel')">📖 术语词库</button>
        <button class="ziwei-menu-item" :disabled="!props.hasResult" @click="emit('toggleMultiCompatPanel')">👥 多人合盘页</button>
        <button class="ziwei-menu-item" @click="emit('toggleFengshuiPanel')">🧭 风水助手</button>
      </div>
    </details>

    <details class="ziwei-action-menu">
      <summary class="btn-tool-summary">🛠 工具</summary>
      <div class="ziwei-menu-panel ziwei-menu-panel-tools">
        <button class="ziwei-menu-item" @click="emit('openStarSearch')">🔍 搜索星曜</button>
        <button class="ziwei-menu-item" @click="emit('toggleBrightnessLegend')">💡 亮度图例</button>
        <button class="ziwei-menu-item" @click="emit('toggleHotkeyPanel')">⌨ 快捷键面板</button>
        <button class="ziwei-menu-item" @click="emit('toggleHistoryPanel')">
          <span>📋 历史记录</span>
          <span v-if="props.historyCount" class="history-badge">{{ props.historyCount }}</span>
        </button>
      </div>
    </details>
  </div>
</template>

<style scoped>
.ziwei-action-menus {
  display: contents;
}

.ziwei-action-menu { position: relative; }
.ziwei-action-menu summary { list-style: none; }
.ziwei-action-menu summary::-webkit-details-marker { display: none; }
.ziwei-action-menu[open] > summary { box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.18); }

.btn-cases,
.btn-review,
.btn-tool-summary {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--dur-fast);
}

.btn-cases {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1.5px solid #93c5fd;
}

.btn-cases:hover {
  background: #dbeafe;
}

.btn-review {
  background: #f0fdf4;
  color: #166534;
  border: 1.5px solid #86efac;
}

.btn-review:hover:not(:disabled) {
  background: #dcfce7;
}

.btn-review:disabled {
  opacity: .6;
  cursor: not-allowed;
}

.btn-tool-summary {
  padding-inline: 12px;
  border: 1.5px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
}

.btn-tool-summary:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.ziwei-menu-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 20;
}

.ziwei-menu-panel-tools { min-width: 156px; }

.ziwei-menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  padding: 9px 10px;
  border-radius: 8px;
  color: var(--text-2);
  font-size: var(--fs-sm);
  cursor: pointer;
}

.ziwei-menu-item:hover:not(:disabled) {
  background: var(--surface-2);
  color: var(--accent-dark);
}

.ziwei-menu-item:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.history-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 10px;
  background: var(--accent);
  color: #fff;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
</style>
