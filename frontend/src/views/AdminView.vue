<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  getDashboard, getAuditLogs, getCases, deleteCase,
  listReviews, getReviewStats, updateReview, deleteReview,
  listExperiments, deleteExperiment, getExperimentResults,
  listApiKeys, createApiKey, revokeApiKey,
  getRules, updateRules, getRemediesRules, updateRemediesRules,
} from '@/api/admin'
import { getEventStats, listEvents } from '@/api/events'
import { getGoldenCases } from '@/api/bazi'
import { getGlossary, updateGlossaryTerm } from '@/api/static-data'
import type {
  DashboardResponse, AuditLogItem, CaseItem,
  ChartReviewResponse, ReviewStats,
  ExperimentResponse, ExperimentResults,
  ApiKeyResponse, ApiKeyCreateResponse,
} from '@/api/admin'
import type { EventResponse, EventStatsResponse } from '@/api/events'
import type { GoldenCasesResponse } from '@/api/bazi'
import type { GlossaryItem } from '@/api/static-data'

// ── Tab 状态 ──────────────────────────────────────────────
const activeTab = ref<'dashboard' | 'cases' | 'events' | 'glossary' | 'golden' | 'audit' | 'reviews' | 'experiments' | 'apikeys' | 'rules'>('dashboard')

// ── 仪表盘 ────────────────────────────────────────────────
const dashboard = ref<DashboardResponse | null>(null)
const dashLoading = ref(false)
const dashError = ref('')

async function loadDashboard() {
  if (dashboard.value) return   // 已加载则跳过
  dashLoading.value = true
  dashError.value = ''
  try {
    dashboard.value = await getDashboard()
  } catch {
    dashError.value = '加载失败，请稍后重试'
  } finally {
    dashLoading.value = false
  }
}

// 7日活跃度 最大值（用于柱高百分比）
const maxActivity = computed(() =>
  Math.max(1, ...(dashboard.value?.daily_activity.map(d => d.count) ?? [0]))
)

// ── 案例列表 ──────────────────────────────────────────────
const cases = ref<CaseItem[]>([])
const casesTotal = ref(0)
const casesNext = ref<string | null>(null)
const casesLoading = ref(false)
const casesError = ref('')
const casesLoaded = ref(false)

async function loadCases(reset = false) {
  if (casesLoading.value) return
  casesLoading.value = true
  casesError.value = ''
  try {
    const params: Record<string, unknown> = { limit: 20 }
    if (!reset && casesNext.value) params.before_created_at = casesNext.value
    const res = await getCases(params)
    if (reset) {
      cases.value = res.items
    } else {
      cases.value.push(...res.items)
    }
    casesTotal.value = res.total
    casesNext.value = res.next_cursor
    casesLoaded.value = true
  } catch {
    casesError.value = '案例加载失败'
  } finally {
    casesLoading.value = false
  }
}

// ── 事件统计 ──────────────────────────────────────────────
const eventStats = ref<EventStatsResponse | null>(null)
const eventRows = ref<EventResponse[]>([])
const eventsLoading = ref(false)
const eventsLoaded = ref(false)
const eventsError = ref('')
const eventFilter = ref('')

const maxEventCount = computed(() => {
  const entries = eventStats.value?.by_type ?? []
  return Math.max(1, ...entries.map(item => item.count))
})

async function loadEventsPanel() {
  if (eventsLoading.value) return
  eventsLoading.value = true
  eventsError.value = ''
  try {
    const [stats, list] = await Promise.all([
      getEventStats(),
      listEvents({ limit: 20, event_type: eventFilter.value || undefined }),
    ])
    eventStats.value = stats
    eventRows.value = list.items
    eventsLoaded.value = true
  } catch {
    eventsError.value = '事件统计加载失败'
  } finally {
    eventsLoading.value = false
  }
}

function applyEventFilter() {
  eventsLoaded.value = false
  loadEventsPanel()
}

// ── 黄金案例 ──────────────────────────────────────────────
const goldenCases = ref<Array<Record<string, unknown>>>([])
const goldenTotal = ref(0)
const goldenLoading = ref(false)
const goldenLoaded = ref(false)
const goldenError = ref('')

async function loadGoldenCasesPanel() {
  if (goldenLoading.value) return
  goldenLoading.value = true
  goldenError.value = ''
  try {
    const res: GoldenCasesResponse = await getGoldenCases({ limit: 20 })
    goldenCases.value = res.cases ?? []
    goldenTotal.value = res.total ?? goldenCases.value.length
    goldenLoaded.value = true
  } catch {
    goldenError.value = '黄金案例加载失败'
  } finally {
    goldenLoading.value = false
  }
}

// ── 词汇管理 ──────────────────────────────────────────────
const glossaryItems = ref<GlossaryItem[]>([])
const glossaryLoading = ref(false)
const glossaryLoaded = ref(false)
const glossaryError = ref('')
const glossarySearch = ref('')
const glossaryDialogOpen = ref(false)
const glossarySaving = ref(false)
const glossarySaveError = ref('')
const editingGlossary = ref<GlossaryItem | null>(null)
const glossaryForm = ref({
  term: '',
  definition: '',
  pinyin: '',
  classic_source: '',
})

async function loadGlossaryPanel() {
  if (glossaryLoading.value) return
  glossaryLoading.value = true
  glossaryError.value = ''
  try {
    glossaryItems.value = await getGlossary({ q: glossarySearch.value || undefined, limit: 50 })
    glossaryLoaded.value = true
  } catch {
    glossaryError.value = '词汇管理加载失败'
  } finally {
    glossaryLoading.value = false
  }
}

function applyGlossaryFilter() {
  glossaryLoaded.value = false
  loadGlossaryPanel()
}

function openGlossaryDialog(item: GlossaryItem) {
  editingGlossary.value = item
  glossaryForm.value = {
    term: item.term,
    definition: item.definition,
    pinyin: item.pinyin || '',
    classic_source: item.classic_source || '',
  }
  glossarySaveError.value = ''
  glossaryDialogOpen.value = true
}

function closeGlossaryDialog() {
  glossaryDialogOpen.value = false
  glossarySaveError.value = ''
}

async function saveGlossary() {
  if (!editingGlossary.value) return
  if (!glossaryForm.value.definition.trim()) {
    glossarySaveError.value = '定义不能为空'
    return
  }
  glossarySaving.value = true
  glossarySaveError.value = ''
  try {
    const updated = await updateGlossaryTerm(editingGlossary.value.term, {
      definition: glossaryForm.value.definition.trim(),
      pinyin: glossaryForm.value.pinyin.trim() || undefined,
      classic_source: glossaryForm.value.classic_source.trim() || undefined,
    })
    glossaryItems.value = glossaryItems.value.map(item => item.term === updated.term ? updated : item)
    closeGlossaryDialog()
  } catch {
    glossarySaveError.value = '词汇保存失败'
  } finally {
    glossarySaving.value = false
  }
}

async function handleDeleteCase(id: string) {
  if (!confirm('确认删除该案例？此操作不可恢复。')) return
  try {
    await deleteCase(id)
    cases.value = cases.value.filter(c => c.id !== id)
    casesTotal.value--
  } catch {
    alert('删除失败，请稍后重试')
  }
}

// ── 审计日志 ──────────────────────────────────────────────
const auditLogs = ref<AuditLogItem[]>([])
const auditTotal = ref(0)
const auditNext = ref<number | null>(null)
const auditLoading = ref(false)
const auditError = ref('')
const auditLoaded = ref(false)
const auditFilter = ref('')

async function loadAudit(reset = false) {
  if (auditLoading.value) return
  auditLoading.value = true
  auditError.value = ''
  try {
    const params: Record<string, unknown> = { limit: 50 }
    if (!reset && auditNext.value) params.before_id = auditNext.value
    if (auditFilter.value) params.action = auditFilter.value
    const res = await getAuditLogs(params)
    if (reset) {
      auditLogs.value = res.items
    } else {
      auditLogs.value.push(...res.items)
    }
    auditTotal.value = res.total
    auditNext.value = res.next_cursor
    auditLoaded.value = true
  } catch {
    auditError.value = '审计日志加载失败'
  } finally {
    auditLoading.value = false
  }
}

function applyAuditFilter() {
  auditNext.value = null
  auditLogs.value = []
  auditLoaded.value = false
  loadAudit(true)
}

// ── 审查管理 ──────────────────────────────────────────────
const reviews = ref<ChartReviewResponse[]>([])
const reviewsTotal = ref(0)
const reviewsLoading = ref(false)
const reviewsLoaded = ref(false)
const reviewStats = ref<ReviewStats | null>(null)

async function loadReviews() {
  if (reviewsLoading.value) return
  reviewsLoading.value = true
  try {
    const [list, stats] = await Promise.all([listReviews({ page_size: 30 }), getReviewStats()])
    reviews.value = list.items
    reviewsTotal.value = list.total
    reviewStats.value = stats
    reviewsLoaded.value = true
  } catch { /* ignore */ }
  finally { reviewsLoading.value = false }
}

async function handleApproveReview(id: number) {
  try {
    await updateReview(id, { status: 'approved', reviewer: 'admin' })
    await loadReviews()
  } catch { alert('操作失败') }
}

async function handleRejectReview(id: number) {
  const reason = prompt('驳回原因：')
  if (!reason) return
  try {
    await updateReview(id, { status: 'rejected', reviewer: 'admin', reject_reason: reason })
    await loadReviews()
  } catch { alert('操作失败') }
}

async function handleDeleteReview(id: number) {
  if (!confirm('确认删除？')) return
  try { await deleteReview(id); await loadReviews() } catch { alert('删除失败') }
}

// ── 实验管理 ──────────────────────────────────────────────
const experiments = ref<ExperimentResponse[]>([])
const experimentsTotal = ref(0)
const experimentsLoading = ref(false)
const experimentsLoaded = ref(false)
const expResults = ref<ExperimentResults | null>(null)

async function loadExperiments() {
  if (experimentsLoading.value) return
  experimentsLoading.value = true
  try {
    const res = await listExperiments({ limit: 30 })
    experiments.value = res.items
    experimentsTotal.value = res.total
    experimentsLoaded.value = true
  } catch { /* ignore */ }
  finally { experimentsLoading.value = false }
}

async function handleDeleteExperiment(id: number) {
  if (!confirm('确认删除实验？')) return
  try { await deleteExperiment(id); await loadExperiments() } catch { alert('删除失败') }
}

async function handleViewResults(id: number) {
  try { expResults.value = await getExperimentResults(id) } catch { alert('获取结果失败') }
}

// ── API 密钥管理 ─────────────────────────────────────────
const apiKeys = ref<ApiKeyResponse[]>([])
const apiKeysLoading = ref(false)
const apiKeysLoaded = ref(false)
const newKeyName = ref('')
const newKeyResult = ref<ApiKeyCreateResponse | null>(null)

async function loadApiKeys() {
  if (apiKeysLoading.value) return
  apiKeysLoading.value = true
  try {
    const res = await listApiKeys({ limit: 50 })
    apiKeys.value = res.items
    apiKeysLoaded.value = true
  } catch { /* ignore */ }
  finally { apiKeysLoading.value = false }
}

async function handleCreateApiKey() {
  if (!newKeyName.value.trim()) return
  try {
    newKeyResult.value = await createApiKey({ name: newKeyName.value.trim() })
    newKeyName.value = ''
    await loadApiKeys()
  } catch { alert('创建失败') }
}

async function handleRevokeApiKey(id: number) {
  if (!confirm('确认吊销此密钥？')) return
  try { await revokeApiKey(id); await loadApiKeys() } catch { alert('吊销失败') }
}

// ── 规则管理 ─────────────────────────────────────────────
const rulesData = ref<Array<Record<string, unknown>>>([])
const remediesData = ref<Array<Record<string, unknown>>>([])
const rulesLoading = ref(false)
const rulesLoaded = ref(false)
const rulesEditJson = ref('')
const remediesEditJson = ref('')
const rulesSaving = ref(false)

async function loadRules() {
  if (rulesLoading.value) return
  rulesLoading.value = true
  try {
    const [r, rem] = await Promise.all([getRules(), getRemediesRules()])
    rulesData.value = r
    remediesData.value = rem
    rulesEditJson.value = JSON.stringify(r, null, 2)
    remediesEditJson.value = JSON.stringify(rem, null, 2)
    rulesLoaded.value = true
  } catch { /* ignore */ }
  finally { rulesLoading.value = false }
}

async function saveRules() {
  rulesSaving.value = true
  try {
    const parsed = JSON.parse(rulesEditJson.value)
    await updateRules(parsed)
    alert('生活建议规则已保存')
  } catch (e: unknown) { alert('保存失败: ' + (e as Error).message) }
  finally { rulesSaving.value = false }
}

async function saveRemedies() {
  rulesSaving.value = true
  try {
    const parsed = JSON.parse(remediesEditJson.value)
    await updateRemediesRules(parsed)
    alert('化解建议规则已保存')
  } catch (e: unknown) { alert('保存失败: ' + (e as Error).message) }
  finally { rulesSaving.value = false }
}

// ── Tab 点击 ──────────────────────────────────────────────
function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'dashboard') loadDashboard()
  else if (tab === 'cases' && !casesLoaded.value) loadCases(true)
  else if (tab === 'events' && !eventsLoaded.value) loadEventsPanel()
  else if (tab === 'glossary' && !glossaryLoaded.value) loadGlossaryPanel()
  else if (tab === 'golden' && !goldenLoaded.value) loadGoldenCasesPanel()
  else if (tab === 'audit' && !auditLoaded.value) loadAudit(true)
  else if (tab === 'reviews' && !reviewsLoaded.value) loadReviews()
  else if (tab === 'experiments' && !experimentsLoaded.value) loadExperiments()
  else if (tab === 'apikeys' && !apiKeysLoaded.value) loadApiKeys()
  else if (tab === 'rules' && !rulesLoaded.value) loadRules()
}

function fmtDate(s: string) {
  return new Date(s).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function statusBadge(s: string) {
  const MAP: Record<string, string> = {
    success: 'badge-ok', failed: 'badge-err', error: 'badge-err',
  }
  return MAP[s] ?? 'badge-info'
}

onMounted(loadDashboard)
</script>

<template>
  <div class="wrap admin-view">
    <h1 class="page-title">管理后台</h1>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'dashboard' }]"
              @click="switchTab('dashboard')">仪表盘</button>
      <button :class="['tab-btn', { active: activeTab === 'cases' }]"
              @click="switchTab('cases')">案例管理</button>
            <button :class="['tab-btn', { active: activeTab === 'events' }]"
              @click="switchTab('events')">事件统计</button>
                  <button :class="['tab-btn', { active: activeTab === 'glossary' }]"
                    @click="switchTab('glossary')">词汇管理</button>
            <button :class="['tab-btn', { active: activeTab === 'golden' }]"
              @click="switchTab('golden')">黄金案例</button>
      <button :class="['tab-btn', { active: activeTab === 'audit' }]"
              @click="switchTab('audit')">审计日志</button>
      <button :class="['tab-btn', { active: activeTab === 'reviews' }]"
              @click="switchTab('reviews')">审查管理</button>
      <button :class="['tab-btn', { active: activeTab === 'experiments' }]"
              @click="switchTab('experiments')">实验管理</button>
      <button :class="['tab-btn', { active: activeTab === 'apikeys' }]"
              @click="switchTab('apikeys')">API 密钥</button>
      <button :class="['tab-btn', { active: activeTab === 'rules' }]"
              @click="switchTab('rules')">规则管理</button>
    </div>

    <!-- ── 仪表盘 Tab ───────────────────────────────────── -->
    <section v-if="activeTab === 'dashboard'" class="tab-panel">
      <div v-if="dashLoading" class="loading-msg">加载中…</div>
      <p v-else-if="dashError" class="error-msg">{{ dashError }}</p>
      <template v-else-if="dashboard">
        <!-- 统计卡 -->
        <div class="stat-grid">
          <div class="stat-card stat-1">
            <div class="stat-num">{{ dashboard.cases_total }}</div>
            <div class="stat-label">总案例数</div>
            <div class="stat-sub">本月新增 {{ dashboard.cases_this_month }}</div>
          </div>
          <div class="stat-card stat-2">
            <div class="stat-num">{{ dashboard.snapshots_total }}</div>
            <div class="stat-label">总快照数</div>
            <div class="stat-sub">本月新增 {{ dashboard.snapshots_this_month }}</div>
          </div>
          <div class="stat-card stat-3">
            <div class="stat-num">{{ dashboard.reviews_pending }}</div>
            <div class="stat-label">待审核</div>
            <div class="stat-sub">已通过 {{ dashboard.reviews_approved }}</div>
          </div>
          <div class="stat-card stat-4">
            <div class="stat-num">{{ dashboard.reviews_rejected }}</div>
            <div class="stat-label">已驳回</div>
            <div class="stat-sub">已修订 {{ dashboard.reviews_revised }}</div>
          </div>
        </div>

        <!-- 7日活跃度柱状图 -->
        <div class="card chart-card">
          <div class="card-title">最近 7 天操作活跃度</div>
          <div class="bar-chart">
            <div
              v-for="day in dashboard.daily_activity"
              :key="day.date"
              class="bar-col"
            >
              <div
                class="bar-fill"
                :style="{ height: (day.count / maxActivity * 80) + 'px' }"
                :title="`${day.date}: ${day.count} 次`"
              ></div>
              <div class="bar-label">{{ day.date.slice(5) }}</div>
            </div>
          </div>
        </div>

        <!-- 最近案例 -->
        <div class="card">
          <div class="card-title">最近创建的案例</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>案例名</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in dashboard.recent_cases" :key="c.case_id">
                <td>{{ c.name }}</td>
                <td>{{ fmtDate(c.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <!-- ── 案例管理 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'cases'" class="tab-panel">
      <div v-if="casesLoading && !casesLoaded" class="loading-msg">加载中…</div>
      <p v-else-if="casesError" class="error-msg">{{ casesError }}</p>
      <template v-else>
        <div class="toolbar">
          <span class="total-hint">共 {{ casesTotal }} 个案例</span>
          <button class="btn-sec btn-sm" @click="loadCases(true)">刷新</button>
        </div>
        <div class="card table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>案例名</th>
                <th>标签</th>
                <th>创建时间</th>
                <th>最后快照</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in cases" :key="c.id">
                <td class="case-name">{{ c.name }}</td>
                <td>
                  <span v-for="t in c.tags" :key="t" class="tag-badge">{{ t }}</span>
                  <span v-if="!c.tags?.length" class="text-muted">—</span>
                </td>
                <td>{{ fmtDate(c.created_at) }}</td>
                <td>{{ c.last_snapshot_at ? fmtDate(c.last_snapshot_at) : '—' }}</td>
                <td>
                  <button class="btn-danger btn-sm" @click="handleDeleteCase(c.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="casesNext" class="load-more-row">
          <button class="btn-sec" :disabled="casesLoading" @click="loadCases(false)">
            {{ casesLoading ? '加载中…' : '加载更多' }}
          </button>
        </div>
      </template>
    </section>

    <!-- ── 事件统计 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'events'" class="tab-panel">
      <div class="toolbar">
        <input
          v-model="eventFilter"
          class="filter-input"
          placeholder="按事件类型过滤，如 marriage"
          @keydown.enter="applyEventFilter"
        />
        <button class="btn-sec btn-sm" @click="applyEventFilter">筛选</button>
        <span class="total-hint">共 {{ eventStats?.total ?? 0 }} 条事件</span>
      </div>
      <div v-if="eventsLoading && !eventsLoaded" class="loading-msg">加载中…</div>
      <p v-else-if="eventsError" class="error-msg">{{ eventsError }}</p>
      <template v-else>
        <div class="card" style="margin-bottom: 16px">
          <div class="card-title">事件类型分布</div>
          <div v-if="eventStats?.by_type?.length" class="event-stat-list">
            <div v-for="item in eventStats.by_type" :key="item.event_type" class="event-stat-row">
              <div class="event-stat-type">{{ item.event_type }}</div>
              <div class="event-stat-bar-wrap">
                <div class="event-stat-bar" :style="{ width: (item.count / maxEventCount * 100) + '%' }"></div>
              </div>
              <div class="event-stat-count">{{ item.count }}</div>
            </div>
          </div>
          <p v-else class="text-muted">暂无事件统计</p>
        </div>

        <div class="card table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ID</th><th>事件名</th><th>类型</th><th>成员</th><th>时间</th></tr>
            </thead>
            <tbody>
              <tr v-for="event in eventRows" :key="event.id">
                <td class="log-id">{{ event.id }}</td>
                <td class="case-name">{{ event.name }}</td>
                <td>{{ event.event_type }}</td>
                <td>{{ event.member_id }}</td>
                <td>{{ fmtDate(event.created_at) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!eventRows.length" class="loading-msg">暂无事件记录</div>
        </div>
      </template>
    </section>

    <!-- ── 词汇管理 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'glossary'" class="tab-panel">
      <div class="toolbar">
        <input
          v-model="glossarySearch"
          class="filter-input"
          placeholder="搜索术语，如 七杀"
          @keydown.enter="applyGlossaryFilter"
        />
        <button class="btn-sec btn-sm" @click="applyGlossaryFilter">查询</button>
        <span class="total-hint">共 {{ glossaryItems.length }} 条词汇</span>
      </div>
      <div v-if="glossaryLoading && !glossaryLoaded" class="loading-msg">加载中…</div>
      <p v-else-if="glossaryError" class="error-msg">{{ glossaryError }}</p>
      <div v-else class="card table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>术语</th><th>分类</th><th>定义</th><th>典籍来源</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in glossaryItems" :key="item.term">
              <td class="case-name">{{ item.term }}</td>
              <td>{{ item.category || '—' }}</td>
              <td class="glossary-def-cell">{{ item.definition || '—' }}</td>
              <td class="log-resid">{{ item.classic_source || '—' }}</td>
              <td><button class="btn-sec btn-sm" @click="openGlossaryDialog(item)">编辑</button></td>
            </tr>
          </tbody>
        </table>
        <div v-if="!glossaryItems.length" class="loading-msg">暂无词汇</div>
      </div>
    </section>

    <!-- ── 黄金案例 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'golden'" class="tab-panel">
      <div class="toolbar">
        <span class="total-hint">共 {{ goldenTotal }} 条黄金案例</span>
        <button class="btn-sec btn-sm" @click="loadGoldenCasesPanel">刷新</button>
      </div>
      <div v-if="goldenLoading && !goldenLoaded" class="loading-msg">加载中…</div>
      <p v-else-if="goldenError" class="error-msg">{{ goldenError }}</p>
      <div v-else class="card table-wrap">
        <table class="data-table">
          <thead>
            <tr><th>ID</th><th>出生时间</th><th>性别</th><th>经度</th><th>备注</th><th>创建日</th></tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in goldenCases" :key="String(item.id ?? item.case_id ?? index)">
              <td class="log-id">{{ String(item.id ?? item.case_id ?? '—').slice(0, 12) }}</td>
              <td>{{ String(item.birth_dt_local ?? '—') }}</td>
              <td>{{ item.gender === 'male' ? '男' : item.gender === 'female' ? '女' : '—' }}</td>
              <td>{{ String(item.lon ?? '—') }}</td>
              <td class="log-resid">{{ String(item.note ?? item.label ?? '—') }}</td>
              <td>{{ item.created_at ? fmtDate(String(item.created_at)) : '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!goldenCases.length" class="loading-msg">暂无黄金案例</div>
      </div>
    </section>

    <!-- ── 审计日志 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'audit'" class="tab-panel">
      <div class="toolbar">
        <input
          v-model="auditFilter"
          class="filter-input"
          placeholder="按操作类型过滤，如 create_case"
          @keydown.enter="applyAuditFilter"
        />
        <button class="btn-sec btn-sm" @click="applyAuditFilter">筛选</button>
        <span class="total-hint">共 {{ auditTotal }} 条</span>
      </div>
      <div v-if="auditLoading && !auditLoaded" class="loading-msg">加载中…</div>
      <p v-else-if="auditError" class="error-msg">{{ auditError }}</p>
      <template v-else>
        <div class="card table-wrap">
          <table class="data-table audit-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>操作</th>
                <th>资源类型</th>
                <th>资源 ID</th>
                <th>状态</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in auditLogs" :key="log.id">
                <td class="log-id">{{ log.id }}</td>
                <td class="log-action">{{ log.action }}</td>
                <td>{{ log.resource_type }}</td>
                <td class="log-resid">{{ log.resource_id ?? '—' }}</td>
                <td>
                  <span :class="['status-badge', statusBadge(log.status)]">
                    {{ log.status }}
                  </span>
                </td>
                <td>{{ fmtDate(log.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="auditNext" class="load-more-row">
          <button class="btn-sec" :disabled="auditLoading" @click="loadAudit(false)">
            {{ auditLoading ? '加载中…' : '加载更多（50 条/次）' }}
          </button>
        </div>
      </template>
    </section>

    <!-- ── 审查管理 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'reviews'" class="tab-panel">
      <div v-if="reviewsLoading && !reviewsLoaded" class="loading-msg">加载中…</div>
      <template v-else>
        <div v-if="reviewStats" class="stat-grid" style="grid-template-columns: repeat(5,1fr)">
          <div class="stat-card"><div class="stat-num">{{ reviewStats.total }}</div><div class="stat-label">总数</div></div>
          <div class="stat-card stat-3"><div class="stat-num">{{ reviewStats.pending }}</div><div class="stat-label">待审</div></div>
          <div class="stat-card stat-1"><div class="stat-num">{{ reviewStats.approved }}</div><div class="stat-label">通过</div></div>
          <div class="stat-card stat-4"><div class="stat-num">{{ reviewStats.rejected }}</div><div class="stat-label">驳回</div></div>
          <div class="stat-card stat-2"><div class="stat-num">{{ reviewStats.revised }}</div><div class="stat-label">修订</div></div>
        </div>
        <div class="card table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ID</th><th>状态</th><th>类型</th><th>审查人</th><th>创建时间</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in reviews" :key="r.id">
                <td class="log-id">{{ r.id }}</td>
                <td><span :class="['status-badge', r.status === 'approved' ? 'badge-ok' : r.status === 'rejected' ? 'badge-err' : 'badge-info']">{{ r.status }}</span></td>
                <td>{{ r.chart_type ?? '—' }}</td>
                <td>{{ r.reviewer ?? '—' }}</td>
                <td>{{ fmtDate(r.created_at) }}</td>
                <td class="action-cell">
                  <button v-if="r.status === 'pending'" class="btn-sm btn-sec" @click="handleApproveReview(r.id)">通过</button>
                  <button v-if="r.status === 'pending'" class="btn-sm btn-danger" @click="handleRejectReview(r.id)">驳回</button>
                  <button class="btn-sm btn-danger" @click="handleDeleteReview(r.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <!-- ── 实验管理 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'experiments'" class="tab-panel">
      <div v-if="experimentsLoading && !experimentsLoaded" class="loading-msg">加载中…</div>
      <template v-else>
        <div class="toolbar">
          <span class="total-hint">共 {{ experimentsTotal }} 个实验</span>
          <button class="btn-sec btn-sm" @click="loadExperiments()">刷新</button>
        </div>
        <div class="card table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ID</th><th>名称</th><th>状态</th><th>指标</th><th>假设</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="exp in experiments" :key="exp.id">
                <td class="log-id">{{ exp.id }}</td>
                <td class="case-name">{{ exp.name }}</td>
                <td><span :class="['status-badge', exp.status === 'active' ? 'badge-ok' : 'badge-info']">{{ exp.status }}</span></td>
                <td>{{ exp.target_metric }}</td>
                <td class="log-resid">{{ exp.hypothesis }}</td>
                <td class="action-cell">
                  <button class="btn-sm btn-sec" @click="handleViewResults(exp.id)">结果</button>
                  <button class="btn-sm btn-danger" @click="handleDeleteExperiment(exp.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- 实验结果弹出 -->
        <div v-if="expResults" class="card" style="margin-top: 16px">
          <div class="card-title">实验结果: {{ expResults.experiment_name }}
            <button class="btn-sm btn-sec" style="margin-left:12px" @click="expResults = null">关闭</button>
          </div>
          <p>状态: {{ expResults.status }} · 总分配: {{ expResults.total_assigned }} · 赢家: {{ expResults.winner ?? '待定' }}</p>
          <table class="data-table" style="margin-top:8px">
            <thead><tr><th>变体</th><th>分配</th><th>转化</th><th>转化率</th></tr></thead>
            <tbody>
              <tr v-for="v in expResults.variants" :key="v.variant">
                <td>{{ v.variant }}</td><td>{{ v.assigned }}</td><td>{{ v.conversions }}</td><td>{{ (v.conversion_rate * 100).toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <!-- ── API 密钥 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'apikeys'" class="tab-panel">
      <div v-if="apiKeysLoading && !apiKeysLoaded" class="loading-msg">加载中…</div>
      <template v-else>
        <div class="toolbar">
          <input v-model="newKeyName" class="filter-input" placeholder="新密钥名称" @keydown.enter="handleCreateApiKey" />
          <button class="btn-sec btn-sm" @click="handleCreateApiKey">创建</button>
        </div>
        <div v-if="newKeyResult" class="card" style="margin-bottom:12px; background:#dcfce7; padding:12px 16px">
          <strong>密钥已创建！请立即复制（仅显示一次）：</strong>
          <code style="display:block; margin-top:6px; word-break:break-all">{{ newKeyResult.plaintext_key }}</code>
          <button class="btn-sm btn-sec" style="margin-top:8px" @click="newKeyResult = null">关闭</button>
        </div>
        <div class="card table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>ID</th><th>名称</th><th>前缀</th><th>创建时间</th><th>最后使用</th><th>过期</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="k in apiKeys" :key="k.id">
                <td class="log-id">{{ k.id }}</td>
                <td class="case-name">{{ k.name }}</td>
                <td class="log-action">{{ k.key_prefix }}…</td>
                <td>{{ fmtDate(k.created_at) }}</td>
                <td>{{ k.last_used_at ? fmtDate(k.last_used_at) : '—' }}</td>
                <td>{{ k.expires_at ? fmtDate(k.expires_at) : '永不' }}</td>
                <td>
                  <button v-if="!k.revoked_at" class="btn-sm btn-danger" @click="handleRevokeApiKey(k.id)">吊销</button>
                  <span v-else class="text-muted">已吊销</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <!-- ── 规则管理 Tab ─────────────────────────────────── -->
    <section v-if="activeTab === 'rules'" class="tab-panel">
      <div v-if="rulesLoading && !rulesLoaded" class="loading-msg">加载中…</div>
      <template v-else>
        <div class="card" style="margin-bottom: 16px">
          <div class="card-title">生活建议规则 ({{ rulesData.length }} 条)</div>
          <textarea v-model="rulesEditJson" class="rules-editor" rows="16"></textarea>
          <div style="margin-top:8px; text-align:right">
            <button class="btn-sec" :disabled="rulesSaving" @click="saveRules">{{ rulesSaving ? '保存中…' : '保存规则' }}</button>
          </div>
        </div>
        <div class="card">
          <div class="card-title">化解建议规则 ({{ remediesData.length }} 条)</div>
          <textarea v-model="remediesEditJson" class="rules-editor" rows="16"></textarea>
          <div style="margin-top:8px; text-align:right">
            <button class="btn-sec" :disabled="rulesSaving" @click="saveRemedies">{{ rulesSaving ? '保存中…' : '保存规则' }}</button>
          </div>
        </div>
      </template>
    </section>

    <Teleport to="body">
      <div v-if="glossaryDialogOpen" class="admin-modal-mask" @click.self="closeGlossaryDialog">
        <div class="admin-modal">
          <h2 class="admin-modal-title">编辑词汇定义</h2>
          <div class="admin-form-grid">
            <label class="admin-form-item">
              <span class="admin-form-label">术语</span>
              <input :value="glossaryForm.term" class="admin-form-input" readonly />
            </label>
            <label class="admin-form-item">
              <span class="admin-form-label">拼音</span>
              <input v-model="glossaryForm.pinyin" class="admin-form-input" placeholder="可选" />
            </label>
            <label class="admin-form-item admin-form-item-full">
              <span class="admin-form-label">定义</span>
              <textarea v-model="glossaryForm.definition" class="admin-form-textarea" rows="5"></textarea>
            </label>
            <label class="admin-form-item admin-form-item-full">
              <span class="admin-form-label">典籍来源</span>
              <input v-model="glossaryForm.classic_source" class="admin-form-input" placeholder="可选" />
            </label>
          </div>
          <p v-if="glossarySaveError" class="error-msg" style="padding: 0">{{ glossarySaveError }}</p>
          <div class="admin-modal-actions">
            <button class="btn-sec" @click="closeGlossaryDialog">取消</button>
            <button class="btn-sec" :disabled="glossarySaving" @click="saveGlossary">{{ glossarySaving ? '保存中…' : '保存' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-view { padding-bottom: var(--sp-8); }

.tabs {
  display: flex;
  gap: var(--sp-1);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-5);
}

.tab-btn {
  padding: var(--sp-2) var(--sp-5);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--text-2);
  font-size: var(--fs-md);
  font-weight: 500;
  cursor: pointer;
  transition: color var(--dur-fast), border-color var(--dur-fast);
  margin-bottom: -1px;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--accent-dark); border-bottom-color: var(--accent); }

/* 统计卡 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-4);
  margin-bottom: var(--sp-5);
}
@media (max-width: 700px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }

.stat-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: var(--sp-5) var(--sp-4);
  box-shadow: var(--shadow);
  border-top: 3px solid var(--border);
}
.stat-1 { border-top-color: var(--accent); }
.stat-2 { border-top-color: var(--success-dark); }
.stat-3 { border-top-color: var(--info-dark); }
.stat-4 { border-top-color: var(--danger-dark); }

.stat-num  { font-size: var(--fs-2xl); font-weight: 700; color: var(--text); }
.stat-label{ font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-top: 2px; }
.stat-sub  { font-size: var(--fs-xs); color: var(--text-3); margin-top: var(--sp-1); }

/* 柱状图 */
.chart-card { padding: var(--sp-4); margin-bottom: var(--sp-5); }
.card-title { font-size: var(--fs-md); font-weight: 600; margin-bottom: var(--sp-4); }
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: var(--sp-2);
  height: 100px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.bar-fill {
  width: 100%;
  min-height: 4px;
  background: var(--accent);
  border-radius: 3px 3px 0 0;
  transition: height var(--dur-mid);
}
.bar-label { font-size: var(--fs-2xs); color: var(--text-3); }

/* 事件统计 */
.event-stat-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.event-stat-row {
  display: grid;
  grid-template-columns: 160px 1fr 56px;
  gap: 12px;
  align-items: center;
}
.event-stat-type {
  font-size: var(--fs-sm);
  color: var(--text-2);
  word-break: break-all;
}
.event-stat-bar-wrap {
  height: 12px;
  border-radius: 999px;
  background: var(--surface-2);
  overflow: hidden;
}
.event-stat-bar {
  height: 100%;
  min-width: 6px;
  background: linear-gradient(90deg, var(--accent), #f59e0b);
  border-radius: 999px;
}
.event-stat-count {
  font-size: var(--fs-sm);
  color: var(--text-2);
  text-align: right;
}

.glossary-def-cell {
  max-width: 320px;
  color: var(--text-2);
  line-height: 1.7;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
  flex-wrap: wrap;
}
.total-hint { font-size: var(--fs-sm); color: var(--text-2); margin-left: auto; }
.filter-input {
  padding: var(--sp-1) var(--sp-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  background: var(--surface);
  color: var(--text);
  width: 240px;
}
.filter-input:focus { outline: 2px solid var(--accent); border-color: var(--accent); }

/* 表格 */
.table-wrap { padding: 0; overflow-x: auto; }
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
}
.data-table th {
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  font-weight: 600;
  color: var(--text-2);
  text-align: left;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.data-table td {
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border);
  color: var(--text);
  vertical-align: middle;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--accent-lt); }

.case-name  { font-weight: 500; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-id     { color: var(--text-3); font-size: var(--fs-xs); }
.log-action { font-weight: 500; font-size: var(--fs-xs); }
.log-resid  { font-size: var(--fs-xs); color: var(--text-2); max-width: 120px; overflow: hidden; text-overflow: ellipsis; }

/* 徽章 */
.tag-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--accent-lt);
  color: var(--accent-dark);
  font-size: var(--fs-2xs);
  font-weight: 500;
  margin-right: 3px;
}
.status-badge {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: var(--fs-2xs);
  font-weight: 600;
}
.badge-ok   { background: #dcfce7; color: var(--success-dark); }
.badge-err  { background: #fee2e2; color: var(--danger-dark); }
.badge-info { background: var(--surface-2); color: var(--text-2); }

/* 按钮 */
.btn-sec {
  background: transparent;
  border: 1.5px solid var(--accent);
  color: var(--accent-dark);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-4);
  font-size: var(--fs-md);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--dur-fast);
}
.btn-sec:hover { background: var(--accent-lt); }
.btn-sec:disabled { opacity: 0.45; pointer-events: none; }

.btn-sm { padding: 4px 10px; font-size: var(--fs-xs); }

.btn-danger {
  background: transparent;
  border: 1px solid var(--danger-dark);
  color: var(--danger-dark);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font-size: var(--fs-xs);
  cursor: pointer;
  transition: background var(--dur-fast);
}
.btn-danger:hover { background: #fee2e2; }

/* 加载更多 */
.load-more-row { text-align: center; margin-top: var(--sp-4); }

/* 加载 / 错误 */
.loading-msg { text-align: center; padding: var(--sp-8); color: var(--text-2); font-size: var(--fs-md); }
.error-msg { color: var(--danger-dark); padding: var(--sp-3); }
.text-muted { color: var(--text-3); }

/* 操作列 */
.action-cell { display: flex; gap: 4px; flex-wrap: wrap; }

/* 规则编辑器 */
.rules-editor {
  width: 100%; box-sizing: border-box;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  resize: vertical;
}
.rules-editor:focus { outline: 2px solid var(--accent); border-color: var(--accent); }

/* 词汇弹窗 */
.admin-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.42);
}
.admin-modal {
  width: min(100%, 680px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.2);
  padding: 20px;
}
.admin-modal-title {
  margin: 0 0 16px;
  font-size: var(--fs-xl);
  font-weight: 700;
}
.admin-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.admin-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.admin-form-item-full { grid-column: 1 / -1; }
.admin-form-label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-weight: 600;
}
.admin-form-input,
.admin-form-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-sm);
}
.admin-form-input:focus,
.admin-form-textarea:focus {
  outline: 2px solid var(--accent);
  border-color: var(--accent);
}
.admin-form-textarea {
  resize: vertical;
  min-height: 120px;
}
.admin-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

/* Tabs 自适应 */
.tabs { flex-wrap: wrap; }
</style>
