<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminDashboard } from '@/composables/useAdminDashboard'
import { useAdminCases } from '@/composables/useAdminCases'
import { useAdminEvents } from '@/composables/useAdminEvents'
import { useAdminGlossary } from '@/composables/useAdminGlossary'
import { useAdminAudit } from '@/composables/useAdminAudit'
import { useAdminSystem } from '@/composables/useAdminSystem'

type AdminTab = 'dashboard' | 'cases' | 'events' | 'glossary' | 'golden' | 'audit' | 'reviews' | 'experiments' | 'apikeys' | 'rules'

const route = useRoute()
const router = useRouter()
const ADMIN_TABS: AdminTab[] = ['dashboard', 'cases', 'events', 'glossary', 'golden', 'audit', 'reviews', 'experiments', 'apikeys', 'rules']

// ── Tab 状态 ──────────────────────────────────────────────
const activeTab = ref<AdminTab>('dashboard')
const entryBanner = computed(() => {
  if (route.query.from !== 'ziwei') return ''
  const createdReviewId = typeof route.query.createdReviewId === 'string' ? route.query.createdReviewId : ''
  if (activeTab.value === 'reviews' && createdReviewId) {
    return `审核单 #${createdReviewId} 已从紫微主盘页提交，现已进入审查管理。`
  }
  if (activeTab.value === 'experiments') return '已从紫微主盘页进入实验管理，运营与实验治理能力已收口到管理后台。'
  if (activeTab.value === 'reviews') return '已从紫微主盘页进入审查管理，审核队列与治理动作已收口到管理后台。'
  return '已从紫微主盘页进入管理后台。'
})

function resolveAdminTab(tab: unknown): AdminTab {
  return typeof tab === 'string' && ADMIN_TABS.includes(tab as AdminTab) ? (tab as AdminTab) : 'dashboard'
}

function syncAdminQuery(tab: AdminTab) {
  const nextQuery = { ...route.query } as Record<string, unknown>
  if (tab === 'dashboard') delete nextQuery.tab
  else nextQuery.tab = tab
  router.replace({ query: nextQuery })
}

// ── 各 Tab 组合函数 ────────────────────────────────────────
const { dashboard, dashLoading, dashError, loadDashboard, maxActivity } = useAdminDashboard()
const { cases, casesTotal, casesNext, casesLoading, casesError, casesLoaded, loadCases, handleDeleteCase } = useAdminCases()
const {
  eventStats, eventRows, eventsLoading, eventsLoaded, eventsError, eventFilter, maxEventCount,
  loadEventsPanel, applyEventFilter,
  goldenCases, goldenTotal, goldenLoading, goldenLoaded, goldenError, loadGoldenCasesPanel,
} = useAdminEvents()
const {
  glossaryItems, glossaryLoading, glossaryLoaded, glossaryError, glossarySearch,
  glossaryDialogOpen, glossarySaving, glossarySaveError, editingGlossary, glossaryForm,
  loadGlossaryPanel, applyGlossaryFilter, openGlossaryDialog, closeGlossaryDialog, saveGlossary,
} = useAdminGlossary()
const {
  auditLogs, auditTotal, auditNext, auditLoading, auditError, auditLoaded, auditFilter,
  loadAudit, applyAuditFilter,
  reviews, reviewsTotal, reviewsLoading, reviewsLoaded, reviewStats,
  loadReviews, handleApproveReview, handleRejectReview, handleDeleteReview,
} = useAdminAudit()
const {
  experiments, experimentsTotal, experimentsLoading, experimentsLoaded, expResults,
  loadExperiments, handleDeleteExperiment, handleViewResults,
  apiKeys, apiKeysLoading, apiKeysLoaded, newKeyName, newKeyResult,
  loadApiKeys, handleCreateApiKey, handleRevokeApiKey,
  rulesData, remediesData, rulesLoading, rulesLoaded, rulesEditJson, remediesEditJson, rulesSaving,
  loadRules, saveRules, saveRemedies,
} = useAdminSystem()

// ── Tab 点击 ──────────────────────────────────────────────
function applyTab(tab: AdminTab) {
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

function switchTab(tab: AdminTab) {
  applyTab(tab)
  syncAdminQuery(tab)
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

watch(
  () => route.query.tab,
  (tab) => {
    const nextTab = resolveAdminTab(tab)
    if (nextTab !== activeTab.value) {
      applyTab(nextTab)
    }
  },
)

onMounted(() => {
  applyTab(resolveAdminTab(route.query.tab))
})
</script>

<template>
  <div class="wrap admin-view">
    <h1 class="page-title">管理后台</h1>
    <p v-if="entryBanner" class="entry-banner">{{ entryBanner }}</p>

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
        <div class="toolbar">
          <span class="total-hint">共 {{ reviewsTotal }} 条审核单</span>
          <button class="btn-sec btn-sm" @click="loadReviews()">刷新</button>
        </div>
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

<style src="./AdminView.css" scoped />
