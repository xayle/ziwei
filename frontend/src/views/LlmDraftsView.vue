<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchDrafts,
  getDraft,
  getLlmConfig,
  interpretGeneric,
  streamInterpretation,
  updateDraft,
  type LlmDraft,
} from '@/api/llm'
import {
  clearZiweiLlmDraftContext,
  loadZiweiLlmDraftContext,
  type ZiweiLlmDraftContext,
} from '@/utils/ziweiLlmDraftContext'

const route = useRoute()
const router = useRouter()

const llmContext = ref<ZiweiLlmDraftContext | null>(null)
const llmConfigLabel = ref('未加载')
const llmStatus = ref('')
const llmLoading = ref(false)
const llmDrafts = ref<LlmDraft[]>([])
const llmFilterStatus = ref('')
const llmCurrentDraft = ref<LlmDraft | null>(null)
const llmCurrentText = ref('')
const llmReviewerNotes = ref('')
const llmCopied = ref(false)

const entryBanner = computed(() => {
  if (route.query.from !== 'ziwei') return ''
  if (llmContext.value) return '已从紫微主盘页带入命盘上下文，可直接生成或流式生成 AI 草稿。'
  return '已从紫微主盘页进入 AI 草稿页，但当前未找到可用上下文。'
})

const contextSummary = computed(() => llmContext.value?.summary || '暂无上下文')
const currentStatusLabel = computed(() => getLlmDraftStatusLabel(llmCurrentDraft.value?.status))
const canGenerate = computed(() => Boolean(llmContext.value && !llmLoading.value))

function parseLlmError(e: unknown, fallback: string): string {
  const message = (e as { message?: string })?.message
  return typeof message === 'string' && message.trim() ? message : fallback
}

function getLlmDraftStatusLabel(status?: string | null): string {
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已驳回'
  if (status === 'pending_review') return '待审核'
  return status || '未生成'
}

function loadStoredContext() {
  llmContext.value = loadZiweiLlmDraftContext()
}

async function loadLlmConfigLabel() {
  try {
    const cfg = await getLlmConfig()
    const provider = typeof cfg.provider === 'string' ? cfg.provider : 'unknown'
    const model = typeof cfg.model === 'string' ? cfg.model : ''
    llmConfigLabel.value = model ? `${provider} / ${model}` : provider
  } catch {
    llmConfigLabel.value = '加载失败'
  }
}

async function loadLlmDraftList() {
  try {
    const data = await fetchDrafts({ limit: 12, status: llmFilterStatus.value || undefined })
    llmDrafts.value = data.items
  } catch {
    llmDrafts.value = []
  }
}

async function generateLlmDraft() {
  if (!llmContext.value || llmLoading.value) return

  llmLoading.value = true
  llmStatus.value = '生成中…'
  try {
    const draft = await interpretGeneric(llmContext.value)
    llmCurrentDraft.value = draft
    llmCurrentText.value = draft.draft_text || ''
    llmReviewerNotes.value = draft.reviewer_notes || ''
    llmStatus.value = '已生成 AI 草稿。'
    await loadLlmDraftList()
  } catch (e: unknown) {
    llmStatus.value = parseLlmError(e, 'AI 草稿生成失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function streamLlmDraft() {
  if (!llmContext.value || llmLoading.value) return

  llmLoading.value = true
  llmCurrentText.value = ''
  llmStatus.value = '流式生成中…'
  try {
    await streamInterpretation(
      llmContext.value,
      (chunk) => { llmCurrentText.value += chunk },
      (fullText) => {
        llmCurrentText.value = fullText
        llmStatus.value = '流式生成完成。'
      },
      async (savedId) => {
        llmCurrentDraft.value = await getDraft(savedId)
        llmReviewerNotes.value = llmCurrentDraft.value?.reviewer_notes || ''
        await loadLlmDraftList()
      },
    )
  } catch (e: unknown) {
    llmStatus.value = parseLlmError(e, '流式生成失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function openLlmDraft(draftId: number) {
  try {
    const draft = await getDraft(draftId)
    llmCurrentDraft.value = draft
    llmCurrentText.value = draft.draft_text || ''
    llmReviewerNotes.value = draft.reviewer_notes || ''
    llmStatus.value = '已载入历史草稿。'
  } catch (e: unknown) {
    llmStatus.value = parseLlmError(e, '读取草稿失败，请稍后重试')
  }
}

async function copyCurrentLlmDraft() {
  if (!llmCurrentText.value.trim()) return

  try {
    await navigator.clipboard.writeText(llmCurrentText.value)
    llmCopied.value = true
    window.setTimeout(() => {
      llmCopied.value = false
    }, 1400)
  } catch {
    llmStatus.value = '复制失败，请手动复制'
  }
}

async function saveCurrentDraftNotes() {
  if (!llmCurrentDraft.value || llmLoading.value) return

  llmLoading.value = true
  try {
    const updated = await updateDraft(llmCurrentDraft.value.id, {
      reviewer: llmCurrentDraft.value.reviewer || 'reviewer',
      reviewer_notes: llmReviewerNotes.value || '',
    })
    llmCurrentDraft.value = updated
    llmReviewerNotes.value = updated.reviewer_notes || ''
    llmStatus.value = '审核备注已保存。'
    await loadLlmDraftList()
  } catch (e: unknown) {
    llmStatus.value = parseLlmError(e, '保存草稿备注失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

async function reviewCurrentDraft(status: 'approved' | 'rejected') {
  if (!llmCurrentDraft.value || llmLoading.value) return

  llmLoading.value = true
  try {
    const updated = await updateDraft(llmCurrentDraft.value.id, {
      status,
      reviewer: 'reviewer',
      reviewer_notes: llmReviewerNotes.value || '',
    })
    llmCurrentDraft.value = updated
    llmReviewerNotes.value = updated.reviewer_notes || ''
    llmStatus.value = status === 'approved' ? '草稿已通过。' : '草稿已驳回。'
    await loadLlmDraftList()
  } catch (e: unknown) {
    llmStatus.value = parseLlmError(e, '草稿审核失败，请稍后重试')
  } finally {
    llmLoading.value = false
  }
}

function clearContext() {
  clearZiweiLlmDraftContext()
  llmContext.value = null
}

function backToZiwei() {
  router.push({ path: '/ziwei' })
}

onMounted(async () => {
  loadStoredContext()
  await Promise.all([loadLlmConfigLabel(), loadLlmDraftList()])
})
</script>

<template>
  <div class="llm-drafts-view">
    <div class="llm-shell">
      <header class="page-head">
        <div>
          <p class="page-kicker">协同治理 / AI</p>
          <h1 class="page-title">AI 草稿工作区</h1>
          <p class="page-desc">集中处理紫微 AI 解读草稿、历史记录与审核动作。</p>
        </div>
        <div class="page-actions">
          <button class="ghost-btn" @click="backToZiwei">返回紫微</button>
        </div>
      </header>

      <p v-if="entryBanner" class="entry-banner">{{ entryBanner }}</p>

      <section class="context-card card">
        <div class="section-head">
          <div>
            <h2>当前上下文</h2>
            <p>{{ contextSummary }}</p>
          </div>
          <div class="section-actions">
            <button class="primary-btn" :disabled="!canGenerate" @click="generateLlmDraft">生成草稿</button>
            <button class="ghost-btn" :disabled="!canGenerate" @click="streamLlmDraft">流式生成</button>
            <button class="ghost-btn" :disabled="!llmContext" @click="clearContext">清空上下文</button>
          </div>
        </div>
        <div v-if="llmContext" class="context-grid">
          <div class="context-item"><span>命宫</span><strong>{{ llmContext.life_palace_gz || '—' }}</strong></div>
          <div class="context-item"><span>五行局</span><strong>{{ llmContext.wuxing_ju_name || '—' }}</strong></div>
          <div class="context-item"><span>出生信息</span><strong>{{ llmContext.birth_info_summary || '—' }}</strong></div>
          <div class="context-item"><span>格局摘要</span><strong>{{ llmContext.pattern_summary || '—' }}</strong></div>
        </div>
        <div v-else class="empty-box">暂无紫微命盘上下文。可先回到紫微主盘页排盘后再进入本页。</div>
      </section>

      <section class="toolbar card">
        <div class="toolbar-meta">模型：{{ llmConfigLabel }}</div>
        <div class="toolbar-actions">
          <select v-model="llmFilterStatus" class="filter-select" @change="loadLlmDraftList">
            <option value="">全部草稿</option>
            <option value="pending_review">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已驳回</option>
          </select>
          <button class="ghost-btn" @click="loadLlmDraftList">刷新列表</button>
        </div>
      </section>

      <p class="status-line">{{ llmStatus || '可直接查看历史草稿，或使用当前上下文生成新草稿。' }}</p>

      <div class="content-grid">
        <section class="card current-card">
          <div class="section-head compact">
            <div>
              <h2>当前草稿</h2>
              <p>状态：{{ currentStatusLabel }}</p>
            </div>
            <button class="ghost-btn" :disabled="!llmCurrentText || llmLoading" @click="copyCurrentLlmDraft">
              {{ llmCopied ? '已复制' : '复制草稿' }}
            </button>
          </div>
          <pre class="draft-text">{{ llmCurrentText || '尚未生成草稿' }}</pre>
          <textarea
            v-model="llmReviewerNotes"
            class="notes-area"
            rows="4"
            placeholder="reviewer notes：记录审核依据、修改建议或驳回原因"
          />
          <div class="draft-actions">
            <button class="ghost-btn" :disabled="llmLoading || !llmCurrentDraft" @click="saveCurrentDraftNotes">保存备注</button>
            <button v-if="llmCurrentDraft && llmCurrentDraft.status === 'pending_review'" class="success-btn" :disabled="llmLoading" @click="reviewCurrentDraft('approved')">通过草稿</button>
            <button v-if="llmCurrentDraft && llmCurrentDraft.status === 'pending_review'" class="danger-btn" :disabled="llmLoading" @click="reviewCurrentDraft('rejected')">驳回草稿</button>
          </div>
        </section>

        <section class="card history-card">
          <div class="section-head compact">
            <div>
              <h2>历史草稿</h2>
              <p>共 {{ llmDrafts.length }} 条</p>
            </div>
          </div>
          <div v-if="llmDrafts.length === 0" class="empty-box">暂无历史草稿，可先生成一版 AI 解读。</div>
          <div v-else class="history-list">
            <button v-for="draft in llmDrafts" :key="draft.id" class="history-item" @click="openLlmDraft(draft.id)">
              <div class="history-top">
                <span class="status-chip">{{ getLlmDraftStatusLabel(draft.status) }}</span>
                <span class="history-time">{{ draft.created_at.slice(0, 16).replace('T', ' ') }}</span>
              </div>
              <div class="history-preview">{{ draft.draft_text.slice(0, 88) }}{{ draft.draft_text.length > 88 ? '…' : '' }}</div>
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style src="./LlmDraftsView.css" scoped />
