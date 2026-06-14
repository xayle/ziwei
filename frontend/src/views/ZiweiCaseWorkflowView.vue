<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchCaseList, deleteCase, type CaseOut } from '@/api/report'
import { listSnapshots, diffSnapshots, type SnapshotOut, type SnapshotDiffResponse } from '@/api/snapshots'
import { searchSimilar, type SimilarResult } from '@/api/similarity'
import {
  clearZiweiCaseWorkflowContext,
  loadZiweiCaseWorkflowContext,
  saveZiweiCaseWorkflowContext,
  type ZiweiCaseWorkflowContext,
  type ZiweiCaseWorkflowInput,
} from '@/utils/ziweiCaseWorkflowContext'
import {
  buildZiweiSimilarityHash,
  buildZiweiWorkflowContext,
  buildZiweiWorkflowSummary,
  saveZiweiChartToLibrary,
} from '@/utils/ziweiCaseLibrary'

const route = useRoute()
const router = useRouter()

const CASES_LIMIT = 10
const context = ref<ZiweiCaseWorkflowContext | null>(loadZiweiCaseWorkflowContext())
const workflowStatus = ref('')

type WorkflowTab = 'cases' | 'snapshots' | 'similar'
const activeTab = ref<WorkflowTab>('cases')

const casesLoading = ref(false)
const casesError = ref('')
const casesKeyword = ref('')
const caseList = ref<CaseOut[]>([])
const casesTotal = ref(0)
const casesOffset = ref(0)

const savingCurrentChart = ref(false)

const snapshotsLoading = ref(false)
const snapshotsError = ref('')
const snapshots = ref<SnapshotOut[]>([])
const snapshotCompareA = ref('')
const snapshotCompareB = ref('')
const snapshotDiffLoading = ref(false)
const snapshotDiffResult = ref<SnapshotDiffResponse | null>(null)
const snapshotDiffError = ref('')

const similarLoading = ref(false)
const similarStatus = ref('')
const similarResults = ref<SimilarResult[]>([])
const similarTotalIndexed = ref(0)
const similarTopK = ref(10)

const entryBanner = computed(() => {
  if (route.query.from !== 'ziwei') return ''
  if (activeTab.value === 'snapshots') return '已从紫微主盘页进入快照工作区，可集中查看案例快照和差异。'
  if (activeTab.value === 'similar') return '已从紫微主盘页进入相似盘工作区，可直接检索或入相似索引库。'
  return '已从紫微主盘页进入案例工作区，可统一处理案例、快照与相似盘流程。'
})

const currentCaseName = computed(() => context.value?.savedCaseName || '未绑定案例')
const currentSnapshotLabel = computed(() => context.value?.currentSnapshotId ? `${context.value.currentSnapshotId.slice(0, 8)}…` : '未绑定快照')
const contextSummary = computed(() => context.value?.summary || '暂无紫微命盘上下文，可先回到紫微主盘页排盘后再进入本页。')
const currentChart = computed(() => context.value?.chartResult || null)
const currentInput = computed(() => context.value?.chartInput || null)
const hasCasePagination = computed(() => casesTotal.value > CASES_LIMIT)
const canSaveCurrentChart = computed(() => Boolean(currentChart.value && currentInput.value && !savingCurrentChart.value))
const canRunSimilarity = computed(() => Boolean(currentChart.value && currentInput.value && !similarLoading.value))
const similarQuerySummary = computed(() => {
  if (!currentChart.value) return '请先从紫微主盘页带入命盘上下文，再进行相似盘检索。'
  return `查询命盘：${currentChart.value.birth_solar} · ${currentChart.value.gender} · 命宫 ${currentChart.value.life_palace_gz} · ${currentChart.value.wuxing_ju_name}`
})

function resolveTab(tab: unknown): WorkflowTab {
  return tab === 'snapshots' || tab === 'similar' ? tab : 'cases'
}

function syncTabQuery(tab: WorkflowTab) {
  if (route.query.tab === tab) return
  router.replace({ query: { ...route.query, tab } })
}

function parseWorkflowError(error: unknown, fallback: string): string {
  const message = (error as { response?: { data?: { detail?: unknown } }; message?: string })?.response?.data?.detail
  if (typeof message === 'string' && message.trim()) return message
  if (Array.isArray(message)) {
    const first = message.find((item) => typeof item === 'string' && item.trim())
    if (typeof first === 'string') return first
  }
  const direct = (error as { message?: string })?.message
  return typeof direct === 'string' && direct.trim() ? direct : fallback
}

function buildSimilarityHash(): string {
  if (!currentChart.value || !currentInput.value) return ''
  return buildZiweiSimilarityHash(currentInput.value, currentChart.value)
}

function buildContextSummary(result = currentChart.value, input = currentInput.value, savedCaseName = context.value?.savedCaseName || ''): string {
  return buildZiweiWorkflowSummary(result, input, savedCaseName)
}

function updateContext(next: ZiweiCaseWorkflowContext | null) {
  context.value = next
  if (next) saveZiweiCaseWorkflowContext(next)
  else clearZiweiCaseWorkflowContext()
}

function buildChartInputFromSnapshot(input: Record<string, unknown> | null | undefined, fallback?: ZiweiCaseWorkflowInput | null): ZiweiCaseWorkflowInput | null {
  const base = fallback ?? null
  const year = Number(input?.year ?? base?.year)
  const month = Number(input?.month ?? base?.month)
  const day = Number(input?.day ?? base?.day)
  const hour = Number(input?.hour ?? base?.hour)
  const minute = Number(input?.minute ?? base?.minute ?? 0)
  const genderRaw = input?.gender ?? base?.gender ?? '男'
  const gender = genderRaw === '女' || genderRaw === 'female' ? '女' : '男'
  const longitudeRaw = input?.longitude ?? base?.longitude ?? null
  const liunianRaw = input?.liunian_year ?? base?.liunian_year ?? null
  if (![year, month, day, hour, minute].every((item) => Number.isFinite(item))) return null

  return {
    year,
    month,
    day,
    hour,
    minute,
    gender,
    longitude: typeof longitudeRaw === 'number' && Number.isFinite(longitudeRaw) ? longitudeRaw : null,
    liunian_year: typeof liunianRaw === 'number' && Number.isFinite(liunianRaw) ? liunianRaw : null,
    template_version: typeof input?.template_version === 'string'
      ? input.template_version
      : base?.template_version ?? null,
    city_name: typeof input?.city_name === 'string'
      ? input.city_name
      : base?.city_name ?? null,
  }
}

function hydrateContextFromSnapshot(snapshot: SnapshotOut, item?: Pick<CaseOut, 'id' | 'name' | 'city'> | null) {
  const output = snapshot.output_json ?? null
  if (!output || typeof output !== 'object') {
    throw new Error('该案例暂无可用快照，请重新排盘后再保存一次')
  }

  const nextInput = buildChartInputFromSnapshot(snapshot.input_json, currentInput.value)
  const savedCaseName = item?.name ?? context.value?.savedCaseName ?? ''
  updateContext(buildZiweiWorkflowContext({
    input: nextInput,
    chart: output as ZiweiCaseWorkflowContext['chartResult'],
    savedCaseId: item?.id ?? context.value?.savedCaseId ?? snapshot.case_id,
    savedCaseName,
    currentSnapshotId: snapshot.id,
  }))
}

function clearSnapshotCompareState() {
  snapshotCompareA.value = ''
  snapshotCompareB.value = ''
  snapshotDiffResult.value = null
  snapshotDiffError.value = ''
}

async function loadCases(offset = 0) {
  if (casesLoading.value) return
  casesLoading.value = true
  casesError.value = ''
  casesOffset.value = offset
  try {
    const data = await fetchCaseList({
      limit: CASES_LIMIT,
      offset,
      q: casesKeyword.value.trim() || undefined,
      order: 'updated_at',
      dir: 'desc',
    })
    caseList.value = data.items
    casesTotal.value = data.total
  } catch (error: unknown) {
    casesError.value = parseWorkflowError(error, '案例库加载失败，请稍后重试')
  } finally {
    casesLoading.value = false
  }
}

async function searchCases() {
  await loadCases(0)
}

async function saveCurrentChartToLibrary() {
  if (!currentChart.value || !currentInput.value || savingCurrentChart.value) return

  savingCurrentChart.value = true
  workflowStatus.value = '保存到案例库中…'
  try {
    const saved = await saveZiweiChartToLibrary({
      input: currentInput.value,
      chart: currentChart.value,
      existingCaseId: context.value?.savedCaseId,
      existingCaseName: context.value?.savedCaseName,
      cityName: currentInput.value.city_name || null,
      longitudeFallback: 120,
      sourceLabel: 'spa-ziwei-case-workflow',
    })

    updateContext(buildZiweiWorkflowContext({
      input: currentInput.value,
      chart: currentChart.value,
      savedCaseId: saved.caseId,
      savedCaseName: saved.caseName,
      currentSnapshotId: saved.snapshotId,
    }))
    workflowStatus.value = `已保存到案例库：${saved.caseName}`
    if (activeTab.value === 'snapshots') {
      await loadCaseSnapshots()
    }
  } catch (error: unknown) {
    workflowStatus.value = parseWorkflowError(error, '保存命盘失败，请稍后重试')
  } finally {
    savingCurrentChart.value = false
  }
}

async function loadCaseIntoContext(item: CaseOut) {
  try {
    const snapshotList = await listSnapshots(item.id, { limit: 1, offset: 0 })
    const latest = snapshotList[0]
    if (!latest) {
      workflowStatus.value = '该案例暂无可用快照，请重新排盘后再保存一次。'
      return
    }
    hydrateContextFromSnapshot(latest, item)
    workflowStatus.value = `已载入案例：${item.name}`
    if (activeTab.value === 'snapshots') {
      await loadCaseSnapshots()
    }
  } catch (error: unknown) {
    workflowStatus.value = parseWorkflowError(error, '载入案例失败，请稍后重试')
  }
}

async function removeCase(item: CaseOut) {
  if (!window.confirm(`确认删除案例「${item.name}」吗？`)) return

  try {
    await deleteCase(item.id)
    if (context.value?.savedCaseId === item.id) {
      updateContext(context.value ? {
        ...context.value,
        savedCaseId: '',
        savedCaseName: '',
        currentSnapshotId: '',
        summary: buildContextSummary(context.value.chartResult, context.value.chartInput, ''),
        createdAt: new Date().toISOString(),
      } : null)
      snapshots.value = []
      clearSnapshotCompareState()
    }
    const nextOffset = caseList.value.length === 1 && casesOffset.value > 0
      ? Math.max(0, casesOffset.value - CASES_LIMIT)
      : casesOffset.value
    workflowStatus.value = `已删除案例：${item.name}`
    await loadCases(nextOffset)
  } catch (error: unknown) {
    workflowStatus.value = parseWorkflowError(error, '删除案例失败，请稍后重试')
  }
}

function prevCasesPage() {
  if (casesOffset.value <= 0) return
  void loadCases(Math.max(0, casesOffset.value - CASES_LIMIT))
}

function nextCasesPage() {
  if (casesOffset.value + CASES_LIMIT >= casesTotal.value) return
  void loadCases(casesOffset.value + CASES_LIMIT)
}

async function loadCaseSnapshots() {
  const caseId = context.value?.savedCaseId
  if (!caseId) {
    snapshots.value = []
    snapshotsError.value = '请先保存当前命盘，或从案例库载入一个案例。'
    return
  }

  snapshotsLoading.value = true
  snapshotsError.value = ''
  clearSnapshotCompareState()
  try {
    const data = await listSnapshots(caseId, { limit: 10, offset: 0 })
    snapshots.value = data
    if (data[0]) snapshotCompareA.value = data[0].id
    if (data[1]) snapshotCompareB.value = data[1].id
    else if (data[0]) snapshotCompareB.value = data[0].id
  } catch (error: unknown) {
    snapshotsError.value = parseWorkflowError(error, '快照列表加载失败，请稍后重试')
  } finally {
    snapshotsLoading.value = false
  }
}

function restoreSnapshotToContext(snapshot: SnapshotOut) {
  try {
    hydrateContextFromSnapshot(snapshot, context.value?.savedCaseId
      ? {
          id: context.value.savedCaseId,
          name: context.value.savedCaseName,
          city: currentInput.value?.city_name || null,
        }
      : null)
    workflowStatus.value = `已载入快照：${snapshot.id.slice(0, 8)}…`
  } catch (error: unknown) {
    workflowStatus.value = parseWorkflowError(error, '载入快照失败，请稍后重试')
  }
}

async function compareSnapshotsNow() {
  if (!snapshotCompareA.value || !snapshotCompareB.value) {
    snapshotDiffError.value = '请选择两个快照后再比较'
    return
  }
  if (snapshotCompareA.value === snapshotCompareB.value) {
    snapshotDiffError.value = '请至少选择两个不同的快照'
    return
  }

  snapshotDiffLoading.value = true
  snapshotDiffError.value = ''
  snapshotDiffResult.value = null
  try {
    snapshotDiffResult.value = await diffSnapshots(snapshotCompareA.value, snapshotCompareB.value)
  } catch (error: unknown) {
    snapshotDiffError.value = parseWorkflowError(error, '快照对比失败，请稍后重试')
  } finally {
    snapshotDiffLoading.value = false
  }
}

function getSimilarityPercent(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value * 100)))
}

function getSimilarityLevel(value: number): string {
  const pct = getSimilarityPercent(value)
  if (pct >= 80) return '高度相似'
  if (pct >= 60) return '中度相似'
  return '低度相似'
}

function formatSimilarityPatterns(item: SimilarResult): string {
  const patterns = Array.isArray(item.case.patterns) ? item.case.patterns : []
  const labels = patterns
    .map((pattern) => {
      if (!pattern || typeof pattern !== 'object') return ''
      const name = typeof pattern.name === 'string' ? pattern.name : ''
      const level = typeof pattern.level === 'string' ? pattern.level : ''
      return [name, level].filter(Boolean).join(' ')
    })
    .filter(Boolean)
  return labels.length ? labels.slice(0, 3).join('、') : '无明显格局标签'
}

async function runSimilarSearch() {
  if (!currentChart.value || !currentInput.value || similarLoading.value) return

  similarLoading.value = true
  similarStatus.value = '检索中…'
  similarResults.value = []
  try {
    const data = await searchSimilar({
      chart_hash: buildSimilarityHash(),
      life_palace_gz: currentChart.value.life_palace_gz,
      wuxing_ju_name: currentChart.value.wuxing_ju_name,
      gender: currentChart.value.gender,
      birth_year: currentInput.value.year,
      patterns: JSON.stringify(buildSimilarityPatternPayload()),
      top_k: similarTopK.value,
    })
    similarResults.value = data.results
    similarTotalIndexed.value = data.total_indexed
    similarStatus.value = data.results.length
      ? `找到 ${data.results.length} 条相似命盘，当前索引库共 ${data.total_indexed} 条。`
      : `未找到相似命盘，当前索引库共 ${data.total_indexed} 条。`
  } catch (error: unknown) {
    similarStatus.value = parseWorkflowError(error, '相似盘检索失败，请稍后重试')
  } finally {
    similarLoading.value = false
  }
}

async function indexCurrentForSimilarity() {
  if (!currentChart.value || !currentInput.value || similarLoading.value) return

  similarLoading.value = true
  similarStatus.value = '入相似库中…'
  try {
    await indexChart({
      chart_hash: buildSimilarityHash(),
      birth_solar: currentChart.value.birth_solar,
      birth_year: currentInput.value.year,
      birth_month: currentInput.value.month,
      birth_day: currentInput.value.day,
      birth_hour: currentInput.value.hour,
      gender: currentInput.value.gender,
      wuxing_ju_name: currentChart.value.wuxing_ju_name,
      life_palace_gz: currentChart.value.life_palace_gz,
      patterns: buildSimilarityPatternPayload(),
      source_label: 'spa-ziwei-case-workflow',
    })
    similarStatus.value = '当前命盘已加入相似盘索引库。'
  } catch (error: unknown) {
    similarStatus.value = parseWorkflowError(error, '当前命盘入相似库失败，请稍后重试')
  } finally {
    similarLoading.value = false
  }
}

function clearContext() {
  updateContext(null)
  snapshots.value = []
  similarResults.value = []
  workflowStatus.value = '已清空当前上下文。'
}

function openAdminCases() {
  router.push({
    path: '/admin',
    query: {
      tab: 'cases',
      from: 'ziwei',
      context: 'case-workflow',
    },
  })
}

function backToZiwei() {
  if (context.value) saveZiweiCaseWorkflowContext(context.value)
  router.push({
    path: '/ziwei',
    query: context.value?.chartResult ? { context: 'case-workflow', from: 'case-workflow' } : undefined,
  })
}

async function applyTab(tab: WorkflowTab) {
  activeTab.value = tab
  syncTabQuery(tab)

  if (tab === 'cases') {
    await loadCases(casesOffset.value)
    return
  }
  if (tab === 'snapshots') {
    await loadCaseSnapshots()
    return
  }
  similarStatus.value = currentChart.value
    ? '点击“开始检索”查看相似命盘。'
    : '请先从紫微主盘页带入命盘上下文，再使用相似盘检索。'
}

watch(
  () => route.query.tab,
  (tab) => {
    void applyTab(resolveTab(tab))
  },
  { immediate: true },
)
</script>

<template>
  <div class="ziwei-case-workflow-view">
    <div class="workflow-shell">
      <header class="page-head">
        <div>
          <p class="page-kicker">紫微 / 案例工作流</p>
          <h1 class="page-title">紫微案例工作区</h1>
          <p class="page-desc">集中承接案例库、快照历史与相似盘检索，继续为紫微主盘页减负。</p>
        </div>
        <div class="page-actions">
          <button class="ghost-btn" @click="openAdminCases">管理后台案例页</button>
          <button class="primary-btn" @click="backToZiwei">返回紫微</button>
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
            <button class="primary-btn" :disabled="!canSaveCurrentChart" @click="saveCurrentChartToLibrary">
              {{ savingCurrentChart ? '保存中…' : '保存到案例库' }}
            </button>
            <button class="ghost-btn" :disabled="!context" @click="clearContext">清空上下文</button>
          </div>
        </div>
        <div v-if="context" class="context-grid">
          <div class="context-item"><span>当前案例</span><strong>{{ currentCaseName }}</strong></div>
          <div class="context-item"><span>当前快照</span><strong>{{ currentSnapshotLabel }}</strong></div>
          <div class="context-item"><span>命宫</span><strong>{{ currentChart?.life_palace_gz || '—' }}</strong></div>
          <div class="context-item"><span>五行局</span><strong>{{ currentChart?.wuxing_ju_name || '—' }}</strong></div>
        </div>
        <div v-else class="empty-box">暂无紫微命盘上下文，但仍可先浏览案例库。</div>
      </section>

      <nav class="tab-nav card">
        <button :class="['tab-btn', { active: activeTab === 'cases' }]" @click="applyTab('cases')">案例库</button>
        <button :class="['tab-btn', { active: activeTab === 'snapshots' }]" @click="applyTab('snapshots')">快照历史</button>
        <button :class="['tab-btn', { active: activeTab === 'similar' }]" @click="applyTab('similar')">相似盘检索</button>
      </nav>

      <p class="status-line">{{ workflowStatus || '可在本页统一处理案例、快照与相似盘动作。' }}</p>

      <section v-if="activeTab === 'cases'" class="card workflow-card">
        <div class="panel-head">
          <div>
            <h2>案例库</h2>
            <p>可搜索、载入并删除历史紫微案例。</p>
          </div>
        </div>
        <div class="cp-toolbar">
          <input
            v-model="casesKeyword"
            type="text"
            class="cp-search-input"
            placeholder="搜索案例名称"
            @keydown.enter.prevent="searchCases"
          />
          <button class="cp-search-btn" @click="searchCases">搜索</button>
        </div>
        <div class="cp-summary">
          <span>共 {{ casesTotal }} 条</span>
          <span v-if="context?.savedCaseName" class="cp-current">当前：{{ context.savedCaseName }}</span>
        </div>
        <div v-if="casesLoading" class="cp-state">加载中…</div>
        <div v-else-if="casesError" class="cp-state cp-error">{{ casesError }}</div>
        <div v-else-if="caseList.length === 0" class="cp-state">暂无案例</div>
        <div v-else class="cp-list">
          <div v-for="item in caseList" :key="item.id" class="cp-item">
            <div class="cp-item-main" @click="loadCaseIntoContext(item)">
              <div class="cp-name-row">
                <span class="cp-name">{{ item.name }}</span>
                <span v-if="context?.savedCaseId === item.id" class="cp-badge">当前</span>
              </div>
              <div class="cp-meta">
                <span>{{ item.birth_dt_local.replace('T', ' ').slice(0, 16) }}</span>
                <span>{{ item.gender === 'female' ? '女' : item.gender === 'male' ? '男' : '—' }}</span>
              </div>
              <div class="cp-meta cp-meta-muted">
                <span>{{ item.last_snapshot_at ? `最近快照 ${item.last_snapshot_at.replace('T', ' ').slice(0, 16)}` : '暂无快照' }}</span>
              </div>
            </div>
            <div class="cp-actions">
              <button class="cp-load-btn" @click="loadCaseIntoContext(item)">载入</button>
              <button class="cp-del-btn" @click="removeCase(item)">删除</button>
            </div>
          </div>
        </div>
        <div v-if="hasCasePagination" class="cp-pagination">
          <button class="cp-page-btn" :disabled="casesOffset <= 0" @click="prevCasesPage">上一页</button>
          <span>{{ Math.floor(casesOffset / CASES_LIMIT) + 1 }} / {{ Math.max(1, Math.ceil(casesTotal / CASES_LIMIT)) }}</span>
          <button class="cp-page-btn" :disabled="casesOffset + CASES_LIMIT >= casesTotal" @click="nextCasesPage">下一页</button>
        </div>
      </section>

      <section v-else-if="activeTab === 'snapshots'" class="card workflow-card">
        <div class="panel-head">
          <div>
            <h2>快照历史</h2>
            <p>查看当前案例最近快照，并对比两次保存差异。</p>
          </div>
          <div class="panel-actions">
            <button class="ghost-btn" :disabled="!context?.savedCaseId" @click="loadCaseSnapshots">刷新快照</button>
          </div>
        </div>
        <div class="snp-summary">
          <span>案例：{{ currentCaseName }}</span>
          <span>当前快照：{{ currentSnapshotLabel }}</span>
        </div>
        <div v-if="snapshotsLoading" class="snp-state">加载中…</div>
        <div v-else-if="snapshotsError" class="snp-state snp-error">{{ snapshotsError }}</div>
        <div v-else-if="snapshots.length === 0" class="snp-state">暂无快照</div>
        <template v-else>
          <div class="snp-list">
            <div v-for="snap in snapshots" :key="snap.id" class="snp-item">
              <div class="snp-item-main">
                <div class="snp-item-row">
                  <span class="snp-kind">{{ snap.kind }}</span>
                  <span v-if="context?.currentSnapshotId === snap.id" class="snp-current">当前</span>
                </div>
                <div class="snp-meta">{{ snap.created_at.replace('T', ' ').slice(0, 16) }} · API {{ snap.api_version ?? '—' }}</div>
                <div v-if="snap.note" class="snp-note">{{ snap.note }}</div>
              </div>
              <button class="snp-load-btn" @click="restoreSnapshotToContext(snap)">载入到上下文</button>
            </div>
          </div>

          <div class="snp-compare-box">
            <div class="snp-compare-title">快照对比</div>
            <div class="snp-compare-controls">
              <select v-model="snapshotCompareA" class="snp-select">
                <option value="">选择快照 A</option>
                <option v-for="snap in snapshots" :key="`a-${snap.id}`" :value="snap.id">
                  {{ snap.created_at.replace('T', ' ').slice(0, 16) }} · {{ snap.id.slice(0, 8) }}
                </option>
              </select>
              <select v-model="snapshotCompareB" class="snp-select">
                <option value="">选择快照 B</option>
                <option v-for="snap in snapshots" :key="`b-${snap.id}`" :value="snap.id">
                  {{ snap.created_at.replace('T', ' ').slice(0, 16) }} · {{ snap.id.slice(0, 8) }}
                </option>
              </select>
              <button class="snp-compare-btn" :disabled="snapshotDiffLoading" @click="compareSnapshotsNow">
                {{ snapshotDiffLoading ? '对比中…' : '开始对比' }}
              </button>
            </div>
            <div v-if="snapshotDiffError" class="snp-diff-error">{{ snapshotDiffError }}</div>
            <div v-else-if="snapshotDiffResult" class="snp-diff-result">
              <div class="snp-diff-summary">共 {{ snapshotDiffResult.total_changes }} 处变更</div>
              <div v-if="snapshotDiffResult.changed_fields.length" class="snp-diff-list">
                <div v-for="field in snapshotDiffResult.changed_fields.slice(0, 8)" :key="field.field" class="snp-diff-item">
                  <span class="snp-diff-field">{{ field.field }}</span>
                  <span class="snp-diff-values">{{ String(field.value_a) }} → {{ String(field.value_b) }}</span>
                </div>
              </div>
              <div v-if="snapshotDiffResult.added_fields.length" class="snp-diff-extra">
                新增：{{ snapshotDiffResult.added_fields.slice(0, 5).join('、') }}
              </div>
              <div v-if="snapshotDiffResult.removed_fields.length" class="snp-diff-extra">
                移除：{{ snapshotDiffResult.removed_fields.slice(0, 5).join('、') }}
              </div>
            </div>
          </div>
        </template>
      </section>

      <section v-else class="card workflow-card">
        <div class="panel-head">
          <div>
            <h2>相似盘检索</h2>
            <p>基于当前紫微命盘上下文进行检索，或将当前命盘写入相似索引库。</p>
          </div>
        </div>
        <div class="simp-query">{{ similarQuerySummary }}</div>
        <div class="simp-toolbar">
          <label class="simp-topk">
            <span>返回数量</span>
            <select v-model.number="similarTopK">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="15">15</option>
            </select>
          </label>
          <button class="simp-btn" :disabled="!canRunSimilarity" @click="runSimilarSearch">
            {{ similarLoading ? '检索中…' : '开始检索' }}
          </button>
          <button class="simp-btn simp-btn-soft" :disabled="!canRunSimilarity" @click="indexCurrentForSimilarity">
            当前命盘入库
          </button>
        </div>
        <div class="simp-status">{{ similarStatus || '—' }}</div>
        <div v-if="similarResults.length" class="simp-badge">已索引 {{ similarTotalIndexed }} 张命盘</div>
        <div v-if="similarResults.length === 0" class="simp-empty">
          暂无相似结果。若当前命盘较新，可先点击“当前命盘入库”。
        </div>
        <div v-else class="simp-list">
          <div v-for="item in similarResults" :key="`${item.case.id}-${item.case.chart_hash}`" class="simp-card">
            <div :class="['simp-score', getSimilarityPercent(item.similarity) >= 80 ? 'is-high' : getSimilarityPercent(item.similarity) >= 60 ? 'is-mid' : 'is-low']">
              {{ getSimilarityPercent(item.similarity) }}%
            </div>
            <div class="simp-main">
              <div class="simp-title-row">
                <span class="simp-title">{{ item.case.life_palace_gz }} 命宫 · {{ item.case.wuxing_ju_name }} · {{ item.case.gender }}</span>
                <span class="simp-level">{{ getSimilarityLevel(item.similarity) }}</span>
              </div>
              <div class="simp-meta">
                出生：{{ item.case.birth_year }}-{{ String(item.case.birth_month).padStart(2, '0') }}-{{ String(item.case.birth_day).padStart(2, '0') }} {{ String(item.case.birth_hour).padStart(2, '0') }}:00
              </div>
              <div class="simp-meta">来源：{{ item.case.source_label || '未知' }}</div>
              <div class="simp-patterns">格局：{{ formatSimilarityPatterns(item) }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style src="./ZiweiCaseWorkflowView.css" scoped />
