<script setup lang="ts">
/**
 * AppRightPanel.vue — 右栏面板
 * 上半区：当前课题内容（TopicPanel）
 * 下半区：AI 对话助手
 * 宽度 340px，通过 useUiStore() 响应式控制
 */
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useAiStore } from '@/stores/ai'
import { useNavStore } from '@/stores/nav'
import { fetchDrafts, type LlmDraft } from '@/api/llm'
import TopicPanel from '@/components/TopicPanel.vue'

const ui  = useUiStore()
const ai  = useAiStore()
const nav = useNavStore()

// 当前 tab：'topic'（当前重点）| 'chat'（咨询助手）| 'drafts'（参考草稿）
const activeTab = ref<'topic' | 'chat' | 'drafts'>('topic')

// 当 nav 有选中小节时，自动切到 topic tab
watch(() => nav.currentSectionId, (v) => {
  if (v) activeTab.value = 'topic'
})

/* ── AI 对话 ──────────────────────────────────────────────────── */
const inputText  = ref('')
const messagesEl = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}
watch(() => ai.messages.length, scrollToBottom)
watch(() => ai.messages[ai.messages.length - 1]?.text, scrollToBottom)

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || ai.streaming) return
  inputText.value = ''
  activeTab.value = 'chat'
  await ai.sendMessage(text)
}
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
}

/* ── 快捷模板 ─────────────────────────────────────────────────── */
const TEMPLATES = [
  { module: 'career_detail',       label: '事业详解' },
  { module: 'marriage_detail',     label: '婚恋详解' },
  { module: 'wealth_detail',       label: '财富详解' },
  { module: 'dayun_narrative',     label: '大运叙述' },
  { module: 'liunian_advice',      label: '流年建议' },
  { module: 'fengshui_suggestion', label: '风水建议' },
  { module: 'western_summary',     label: '西方占星解读' },
]

/* ── 草稿 ─────────────────────────────────────────────────────── */
const recentDrafts = ref<LlmDraft[]>([])
const draftLoadError = ref<string | null>(null)

type BackendUnavailableDetail = { status?: number | null; path?: string }

function onBackendUnavailable(evt: Event) {
  const detail = (evt as CustomEvent<BackendUnavailableDetail>).detail
  const statusText = typeof detail?.status === 'number' ? `（HTTP ${detail.status}）` : ''
  draftLoadError.value = `后端连接异常${statusText}，请确认后端服务已启动`
}

async function loadRecentDrafts() {
  draftLoadError.value = null
  try {
    const res = await fetchDrafts({ limit: 5 })
    recentDrafts.value = res.items
  } catch (e: unknown) {
    const msg = (e as { message?: string })?.message ?? ''
    if (msg.includes('后端连接失败')) {
      draftLoadError.value = msg
      return
    }
    if (msg.startsWith('401:') || msg.startsWith('403:')) return
    draftLoadError.value = '草稿加载失败，请稍后重试'
  }
}

onMounted(() => {
  window.addEventListener('app:backend-unavailable', onBackendUnavailable as EventListener)
  loadRecentDrafts()
})

onBeforeUnmount(() => {
  window.removeEventListener('app:backend-unavailable', onBackendUnavailable as EventListener)
})

watch(() => ui.rightPanelVisible, (v) => { if (v) loadRecentDrafts() })

function fmtTime(iso: string): string {
  try {
    const d = new Date(iso)
    const diff = Math.floor((Date.now() - d.getTime()) / 1000)
    if (diff < 60)    return `${diff}秒前`
    if (diff < 3600)  return `${Math.floor(diff / 60)}分钟前`
    if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
    return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
  } catch { return '' }
}
function statusLabel(s: string) {
  return s === 'approved' ? '已审核' : s === 'rejected' ? '已拒绝' : '待审核'
}

const panelSummary = {
  topic: {
    title: '当前重点',
    desc: '这里集中显示你当前正在处理的课题与关键提醒，不再强调系统分栏。',
  },
  chat: {
    title: '咨询助手',
    desc: '可直接向 AI 追问表达方式、补充说明与常用解读角度。',
  },
  drafts: {
    title: '参考草稿',
    desc: '查看最近生成的可参考表达，帮助你整理最终交付内容。',
  },
} as const

</script>

<template>
  <div class="right-panel" :class="{ hidden: !ui.rightPanelVisible, compact: ui.isCompactLayout || ui.isMobileLayout }">

    <!-- ── 顶部标签栏 ── -->
    <div class="panel-header">
      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'topic' }"
          @click="activeTab = 'topic'"
        >
          <span>📋</span>
          <span class="tab-label">重点</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'chat' }"
          @click="activeTab = 'chat'"
        >
          <span>🤖</span>
          <span class="tab-label">助手</span>
          <span v-if="ai.messages.length" class="msg-badge">{{ ai.messages.length }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'drafts' }"
          @click="activeTab = 'drafts'; loadRecentDrafts()"
        >
          <span>📌</span>
          <span class="tab-label">草稿</span>
        </button>
      </div>
      <button class="close-btn" @click="ui.toggleRightPanel" title="关闭">×</button>
    </div>

    <div class="panel-intro">
      <div class="panel-intro-kicker">咨询辅助面板</div>
      <div class="panel-intro-title">{{ panelSummary[activeTab].title }}</div>
      <p class="panel-intro-desc">{{ panelSummary[activeTab].desc }}</p>
    </div>

    <!-- ── Tab 1：课题内容 ── -->
    <div v-show="activeTab === 'topic'" class="tab-content">
      <TopicPanel />
    </div>

    <!-- ── Tab 2：AI 对话 ── -->
    <div v-show="activeTab === 'chat'" class="tab-content chat-tab">

      <!-- 快捷模板 -->
      <div class="templates-strip">
        <button
          v-for="tpl in TEMPLATES"
          :key="tpl.module"
          class="tpl-chip"
          :disabled="ai.streaming || !ai.currentCaseId"
          @click="ai.sendModuleRequest(tpl.module, tpl.label)"
          :title="!ai.currentCaseId ? '请先在案例中心选择案例' : tpl.label"
        >{{ tpl.label }}</button>
      </div>
      <p v-if="!ai.currentCaseId" class="no-case-hint">请先在咨询流程页选择客户，再向助手追问。</p>

      <!-- 消息列表 -->
      <div class="chat-messages" ref="messagesEl">
        <div v-if="ai.messages.length === 0" class="chat-empty">
          <div class="chat-empty-icon">🤖</div>
          <div>先输入问题，或直接点上方常用提问开始整理话术。</div>
        </div>
        <div
          v-for="(msg, i) in ai.messages"
          :key="i"
          class="chat-message"
          :class="msg.role"
        >
          <div class="msg-bubble">
            <span v-if="msg.streaming" class="msg-text">{{ msg.text }}<span class="cursor">▍</span></span>
            <span v-else class="msg-text">{{ msg.text }}</span>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="chat-input-wrap">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="例如：帮我整理这位客户的咨询重点…"
          rows="2"
          :disabled="ai.streaming"
          @keydown="handleKeydown"
        />
        <button
          class="send-btn"
          :disabled="ai.streaming || !inputText.trim()"
          @click="handleSend"
        >{{ ai.streaming ? '⏳' : '发送' }}</button>
      </div>
    </div>

    <!-- ── Tab 3：草稿记录 ── -->
    <div v-show="activeTab === 'drafts'" class="tab-content drafts-tab">
      <div v-if="draftLoadError" class="drafts-error">
        <span>{{ draftLoadError }}</span>
        <button type="button" class="drafts-error-retry" @click="loadRecentDrafts">重试</button>
      </div>
      <div v-if="!draftLoadError && recentDrafts.length === 0" class="empty-hint">暂无可参考草稿，可先在咨询助手中生成。</div>
      <div
        v-for="d in recentDrafts"
        :key="d.id"
        class="draft-item"
      >
        <div class="draft-top">
          <span class="draft-status" :class="d.status">{{ statusLabel(d.status) }}</span>
          <span class="draft-time">{{ fmtTime(d.created_at) }}</span>
        </div>
        <div class="draft-text">{{ d.draft_text.slice(0, 100) }}{{ d.draft_text.length > 100 ? '…' : '' }}</div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ── 根容器 ───────────────────────────────────────────────────── */
.right-panel {
  width: 340px;
  height: 100vh;
  background: var(--color-bg-primary);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  transition: width var(--transition-base);
}
.right-panel.hidden {
  width: 0;
  border-left: none;
  overflow: hidden;
}

.right-panel.compact {
  width: 0;
  border-left: none;
}

/* ── 顶部标签栏 ───────────────────────────────────────────────── */
.panel-header {
  height: 48px;
  padding: 0 8px 0 0;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  flex-shrink: 0;
  gap: 4px;
}

.panel-intro {
  padding: 14px 14px 12px;
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(180deg, rgba(245, 158, 11, 0.08), rgba(255, 255, 255, 0));
}

.panel-intro-kicker {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.panel-intro-title {
  margin-top: 6px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.panel-intro-desc {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}
.tab-bar {
  flex: 1;
  display: flex;
  align-items: stretch;
  height: 100%;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  border-bottom: 2px solid transparent;
  transition: color var(--transition-fast), border-color var(--transition-fast);
  font-family: var(--font-ui);
  white-space: nowrap;
  position: relative;
}
.tab-btn:hover { color: var(--color-text-primary); }
.tab-btn.active {
  color: var(--color-brand);
  border-bottom-color: var(--color-brand);
}
.tab-label { font-weight: 600; }
.msg-badge {
  background: var(--color-brand);
  color: #fff;
  font-size: 0.5625rem;
  padding: 1px 4px;
  border-radius: 99px;
  font-weight: 700;
}
.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 18px;
  line-height: 1;
  display: grid;
  place-items: center;
  border-radius: 4px;
  transition: background var(--transition-fast), color var(--transition-fast);
  flex-shrink: 0;
}
.close-btn:hover { background: var(--color-bg-tertiary); color: var(--color-text-primary); }

/* ── Tab 通用容器 ─────────────────────────────────────────────── */
.tab-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── AI 对话 Tab ──────────────────────────────────────────────── */
.chat-tab { overflow: hidden; }

.templates-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  padding: 10px 12px 6px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.tpl-chip {
  padding: 4px 9px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  font-size: 0.6875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-ui);
}
.tpl-chip:hover:not(:disabled) {
  background: var(--color-brand-light);
  border-color: var(--color-brand);
  color: var(--color-brand);
}
.tpl-chip:disabled { opacity: 0.5; cursor: not-allowed; }

.no-case-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
  padding: 6px 12px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 34px;
  color: var(--color-text-muted);
  font-size: 0.8125rem;
  text-align: center;
}
.chat-empty-icon { font-size: 32px; opacity: .3; }

.chat-message { display: flex; }
.chat-message.user { justify-content: flex-end; }
.chat-message.ai   { justify-content: flex-start; }

.msg-bubble {
  max-width: 88%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.8125rem;
  line-height: 1.55;
}
.chat-message.user .msg-bubble {
  background: var(--color-brand);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.chat-message.ai .msg-bubble {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}
.msg-text { white-space: pre-wrap; word-break: break-word; }

@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
.cursor { animation: blink 0.8s infinite; font-weight: 700; color: var(--color-brand); }

.chat-input-wrap {
  padding: 8px 12px;
  display: flex;
  gap: 7px;
  align-items: flex-end;
  flex-shrink: 0;
  border-top: 1px solid var(--color-border);
}
.chat-input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  color: var(--color-text-primary);
  background: var(--color-bg-secondary);
  resize: none;
  outline: none;
  transition: border-color var(--transition-fast);
  line-height: 1.5;
}
.chat-input:focus { border-color: var(--color-brand); }
.chat-input:disabled { opacity: 0.6; }
.chat-input::placeholder { color: var(--color-text-muted); }

.send-btn {
  padding: 7px 13px;
  background: var(--color-brand);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
  white-space: nowrap;
}
.send-btn:hover:not(:disabled) { background: var(--color-brand-hover); }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── 草稿 Tab ─────────────────────────────────────────────────── */
.drafts-tab {
  overflow-y: auto;
  padding: 10px 12px;
  scrollbar-width: thin;
}

.drafts-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.75rem;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
}

.drafts-error-retry {
  border: 1px solid #fca5a5;
  background: #fff;
  color: #b91c1c;
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.6875rem;
}
.empty-hint {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  text-align: center;
  padding: 24px 0;
}
.draft-item {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-bg-secondary);
  margin-bottom: 10px;
}
.draft-item:last-child { margin-bottom: 0; }
.draft-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.draft-status {
  font-size: 0.6875rem;
  padding: 1px 7px;
  border-radius: 99px;
  font-weight: 600;
}
.draft-status.pending_review { background: #fef3c7; color: #92400e; }
.draft-status.approved       { background: #dcfce7; color: #166534; }
.draft-status.rejected       { background: #fee2e2; color: #991b1b; }
.draft-time { font-size: 0.6875rem; color: var(--color-text-muted); }
.draft-text {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 1279px) {
  .right-panel {
    width: 0;
    border-left: none;
  }
}
</style>
