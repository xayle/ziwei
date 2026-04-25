<script setup lang="ts">
import { computed, ref } from 'vue'
import { useReportStore } from '@/stores/report'
import { exportCasePdf, downloadBlob } from '@/api/export'

const store = useReportStore()

const caseData = computed(() => store.caseData)
const genderLabel = computed(() => {
  if (!caseData.value?.gender) return ''
  return caseData.value.gender === 'female' ? '女' : '男'
})

const birthSummary = computed(() => {
  if (!caseData.value) return ''
  const dt = caseData.value.birth_dt_local
  const [datePart, timePart] = dt.split('T')
  const [y, m, d] = datePart.split('-')
  const [h, mi] = (timePart ?? '00:00').split(':')
  return `${y}年${m}月${d}日 ${h}:${mi} · ${caseData.value.city ?? caseData.value.tz}`
})

const baziCacheAge = computed(() => store.cacheAge('bazi'))

// ─── PDF 导出 ────────────────────────────────────────────────
const pdfPhase = ref<'idle' | 'prepare' | 'download' | 'error'>('idle')
const pdfError = ref<string | null>(null)

async function exportPdf() {
  if (!store.caseId) return
  pdfError.value = null

  // 1. 预加载主要章节数据（保证 #cr 内容可见）
  pdfPhase.value = 'prepare'
  try {
    await Promise.all([
      store.loadChapterData(2),   // 八字
      store.loadChapterData(3),   // 紫微
      store.loadChapterData(4),   // 姓名
    ])
  } catch {
    // 即使部分失败也继续导出
  }

  // 2. 调用后端 PDF 端点，触发下载
  pdfPhase.value = 'download'
  try {
    const blob = await exportCasePdf(store.caseId)
    downloadBlob(blob, `${caseData.value?.name ?? 'report'}.pdf`)
    pdfPhase.value = 'idle'
  } catch (e) {
    pdfError.value = (e as Error).message ?? '导出失败'
    pdfPhase.value = 'error'
    setTimeout(() => { pdfPhase.value = 'idle'; pdfError.value = null }, 4000)
  }
}

const pdfLabel = computed(() => {
  if (pdfPhase.value === 'prepare')  return '⟳ 准备数据…'
  if (pdfPhase.value === 'download') return '⟳ 生成PDF…'
  if (pdfPhase.value === 'error')    return '✗ 导出失败'
  return '📄 导出PDF'
})

async function recompute() {
  // 清除所有章节缓存，使各章节下次访问时强制重新请求
  store.clearAllCache()
  // 重算当前章节
  const key = store.currentChapterDef.apiKey ?? store.currentChapterDef.key
  if (key) await store.applyParamsAndRecompute(key)
}
</script>

<template>
  <header class="topbar">
    <!-- 左: 案例名 + 性别 -->
    <div class="topbar-left">
      <span class="case-name">{{ caseData?.name ?? '—' }}</span>
      <span v-if="genderLabel" class="gender-badge">{{ genderLabel }}</span>
      <span v-if="baziCacheAge" class="cache-age">上次计算: {{ baziCacheAge }}</span>
    </div>

    <!-- 中: 出生时间摘要 -->
    <div class="topbar-mid">
      <span class="birth-summary">{{ birthSummary }}</span>
    </div>

    <!-- 右: 操作按钮 -->
    <div class="topbar-right">
      <button class="btn-text" @click="recompute" title="用当前参数重新计算">
        🔄 重新计算
      </button>
      <button
        class="btn-text"
        :class="{ 'btn-loading': pdfPhase !== 'idle', 'btn-error': pdfPhase === 'error' }"
        :disabled="pdfPhase !== 'idle'"
        :title="pdfError ?? '导出 PDF 报告'"
        @click="exportPdf"
      >
        {{ pdfLabel }}
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: 48px;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: 0 var(--sp-6);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 0;
}

.case-name {
  font-weight: 700;
  font-size: var(--fs-md);
  color: var(--text);
  white-space: nowrap;
}

.gender-badge {
  font-size: var(--fs-xs);
  padding: 2px 7px;
  border-radius: 99px;
  background: var(--accent-lt);
  color: var(--accent-dark);
  border: 1px solid var(--accent-glow);
}

.cache-age {
  font-size: var(--fs-xs);
  color: var(--text-3);
  white-space: nowrap;
}

.topbar-mid {
  flex: 1;
  text-align: center;
  overflow: hidden;
}

.birth-summary {
  font-size: var(--fs-sm);
  color: var(--text-2);
  white-space: nowrap;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-shrink: 0;
}

.btn-text {
  padding: 5px 10px;
  font-size: var(--fs-sm);
  background: transparent;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-2);
  transition: all var(--dur-fast);
}
.btn-text:hover {
  background: var(--accent-glow);
  color: var(--accent-dark);
  border-color: var(--accent);
}
.btn-text.btn-loading {
  opacity: 0.7;
  cursor: not-allowed;
  animation: pulse 1.2s ease-in-out infinite;
}
.btn-text.btn-error {
  border-color: var(--danger-dark);
  color: var(--danger-dark);
  opacity: 1;
}
@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}
</style>
