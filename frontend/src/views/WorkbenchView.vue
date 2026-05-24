<script setup lang="ts">
/**
 * WorkbenchView.vue — CRM 式案例中心
 * 布局：案例列表(320px) | 案例详情+命盘(1fr)
 * 左侧导航已迁移到 AppSidebar.vue
 */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReportStore } from '@/stores/report'
import { useAiStore } from '@/stores/ai'
import { useUiStore } from '@/stores/ui'
import { useNavStore } from '@/stores/nav'
import { useProfileStore } from '@/stores/profile'
import type { CaseOut } from '@/api/report'
import { useWorkbenchCaseCrud } from '@/composables/useWorkbenchCaseCrud'
import { useWorkbenchGuide } from '@/composables/useWorkbenchGuide'
import { useWorkbenchCaseHub } from '@/composables/useWorkbenchCaseHub'
import { useWorkbenchCaseSelection } from '@/composables/useWorkbenchCaseSelection'
import { useWorkbenchInitialization } from '@/composables/useWorkbenchInitialization'
import { useWorkbenchOutputs } from '@/composables/useWorkbenchOutputs'
import { useWorkbenchCaseMeta } from '@/composables/useWorkbenchCaseMeta'
import WorkbenchCaseDialog from '@/components/workbench/WorkbenchCaseDialog.vue'
import { useWorkbenchZiweiPanel } from '@/composables/useWorkbenchZiweiPanel'
import { useWorkbenchBaziPanel } from '@/composables/useWorkbenchBaziPanel'
import { useWorkbenchDualDayunAxis } from '@/composables/useWorkbenchDualDayunAxis'
import { useWorkbenchPageState } from '@/composables/useWorkbenchPageState'
import { useWorkbenchChartLoader } from '@/composables/useWorkbenchChartLoader'
import { useWorkbenchLifecycle } from '@/composables/useWorkbenchLifecycle'
import WorkbenchCaseList from '@/components/workbench/WorkbenchCaseList.vue'
import WorkbenchGuideCard from '@/components/workbench/WorkbenchGuideCard.vue'
import WorkbenchInfoBar from '@/components/workbench/WorkbenchInfoBar.vue'
import WorkbenchBaziSummary from '@/components/workbench/WorkbenchBaziSummary.vue'
import WorkbenchBaziIndicators from '@/components/workbench/WorkbenchBaziIndicators.vue'
import WorkbenchBaziChart from '@/components/workbench/WorkbenchBaziChart.vue'
import WorkbenchBaziDayunTimeline from '@/components/workbench/WorkbenchBaziDayunTimeline.vue'
import WorkbenchBaziLiunianGrid from '@/components/workbench/WorkbenchBaziLiunianGrid.vue'
import WorkbenchBaziLiuyueHeatmap from '@/components/workbench/WorkbenchBaziLiuyueHeatmap.vue'
import WorkbenchBaziInsights from '@/components/workbench/WorkbenchBaziInsights.vue'
import WorkbenchCaseHubPanel from '@/components/workbench/WorkbenchCaseHubPanel.vue'
import WorkbenchStateBlock from '@/components/workbench/WorkbenchStateBlock.vue'
import WorkbenchOnboardPanel from '@/components/workbench/WorkbenchOnboardPanel.vue'
import WorkbenchZiweiSummary from '@/components/workbench/WorkbenchZiweiSummary.vue'
import WorkbenchDualDayunAxis from '@/components/workbench/WorkbenchDualDayunAxis.vue'
import WorkbenchZiweiSelectors from '@/components/workbench/WorkbenchZiweiSelectors.vue'
import WorkbenchZiweiFocus from '@/components/workbench/WorkbenchZiweiFocus.vue'
import WorkbenchZiweiAdvice from '@/components/workbench/WorkbenchZiweiAdvice.vue'
import WorkbenchZiweiOverview from '@/components/workbench/WorkbenchZiweiOverview.vue'

const router     = useRouter()
const route      = useRoute()
const store      = useReportStore()
const ai         = useAiStore()
const ui         = useUiStore()
const nav        = useNavStore()
const profile    = useProfileStore()

const PROFILE_SYNC_TAG = '个人信息同步'
const PROFILE_SYNC_MARK = '[PROFILE_SYNC]'

// ─── 左侧导航菜单 ───────────────────────────────────────────────
// NAV_ITEMS 和 QUICK_ACTIONS 已迁移到 AppSidebar.vue

const selectedId = ref<string | null>(null)
const caseDetail = ref<CaseOut | null>(null)
const searchQ = ref('')
const simpleView = ref(false)
const showNewbieGuide = ref(true)

function isZiweiSectionId(sectionId: string | null | undefined): boolean {
  return !!sectionId && sectionId.startsWith('ziwei-')
}

function isBaziSection(sectionId: string | null | undefined): boolean {
  return !!sectionId && sectionId.startsWith('bazi-')
}

const currentSectionId = computed(() => nav.currentSectionId)
const isZiweiSection = computed(() => isZiweiSectionId(currentSectionId.value))
const caseCount = computed(() => store.caseList.length)
const activeWorkflowLabel = computed(() => {
  if (!caseDetail.value) return '先选择客户'
  if (route.path.startsWith('/report')) return '整理报告'
  if (isZiweiSection.value) return '查看紫微分析'
  if (currentSectionId.value && isBaziSection(currentSectionId.value)) return '查看八字分析'
  return '确认资料并选择下一步'
})

const workflowHighlights = computed(() => [
  { label: '客户数量', value: `${caseCount.value}` },
  { label: '当前阶段', value: activeWorkflowLabel.value },
  { label: '最终目标', value: caseDetail.value ? '生成报告' : '开始咨询' },
])

const {
  currentGuideStep,
  toggleSimpleView,
  closeNewbieGuide,
  clearGuideDemoTimers,
  focusGuideStep,
  goPrevGuideStep,
  goNextGuideStep,
  playGuideDemo,
  guideProgressPercent,
  newbieGuideSteps,
} = useWorkbenchGuide({
  simpleView,
  showNewbieGuide,
  isZiweiSection,
})

const {
  shareUrl,
  snapshots,
  triggerPrint,
  handleShare,
  handleExportJson,
  handleExportPdf,
  loadSnapshots,
} = useWorkbenchOutputs({
  caseDetail,
})

const {
  localBazi,
  localZiwei,
  baziLoading,
  ziweiLoading,
  baziError,
  ziweiError,
  loadBaziForCase,
  loadZiweiForCase,
} = useWorkbenchChartLoader(new Date().getFullYear())

const {
  ziweiPalaces,
  selectedZiweiPalaceName,
  selectedZiweiDayunIndex,
  selectedZiweiLiuyueMonth,
  activeZiweiPalace,
  currentZiweiDayun,
  activeZiweiDayun,
  currentZiweiLiuyue,
  activeZiweiLiuyue,
  ziweiHighlightedPalaceName,
  ziweiSummaryCards,
  activeZiweiDayunSummary,
  activeZiweiLiuyueSummary,
  activeZiweiRelations,
  activeZiweiRelationGraph,
  selectZiweiPalace,
  selectZiweiDayun,
  selectZiweiLiuyue,
} = useWorkbenchZiweiPanel(localZiwei)

const {
  currentYear,
  selectedIndicatorShensha,
  dayunItems,
  liunianItems,
  pillars,
  geju,
  yongshen,
  summary,
  strength,
  dayStemColor,
  thisYearDetail,
  liunianDetailRows,
  expandedLiunianDetailYear,
  toggleLiunianDetail,
  activeLiuyueMonth,
  activeLiuyueDetail,
  selectLiuyue,
  liuyueHeatmapData,
  liuyueTrendSvg,
  linkedLiuyueMonths,
  selectLiunianMonth,
  dayunTimelineItems,
  activeDayunTimelineItem,
  selectDayun,
  liunianTimelineItems,
  liunianSparkline,
  activeLiunianTimelineItem,
  activeLiunianDayunInfo,
  chartSummaryCards,
  baziKeyIndicators,
  activeIndicatorShensha,
  toggleIndicatorShensha,
  fortSummary,
  activePillarKey,
  activePillarDetail,
  selectPillar,
  wuxing,
  wuxingMax,
  wuxingRadarPoints,
  wuxingRadarAxes,
} = useWorkbenchBaziPanel(localBazi)

const {
  genderLabel,
  currentCaseDayunLabel,
  birthLocalText,
  ziweiCaseSummaryText,
  baziCaseSummaryLine,
} = useWorkbenchCaseMeta({
  caseDetail,
  dayunItems,
  chartSummaryCards,
  isZiweiSection,
  localZiwei,
  activeZiweiDayun,
  currentZiweiDayun,
  activeZiweiLiuyue,
  currentZiweiLiuyue,
})

const { dualDayunAxis } = useWorkbenchDualDayunAxis({
  currentYear,
  dayunTimelineItems,
  localZiwei,
  selectDayun,
  selectZiweiDayun,
})

const {
  filteredList,
  reloadCurrentCase,
  fmtDate,
} = useWorkbenchPageState({
  store,
  searchQ,
  caseDetail,
  currentSectionId,
  isZiweiSectionId,
  loadBaziForCase,
  loadZiweiForCase,
})

// ─── 选择案例 ────────────────────────────────────────────────────
const {
  selectCase,
  ensureProfileSyncedCase,
  syncProfileToWorkbenchCase,
} = useWorkbenchCaseSelection({
  store,
  ai,
  nav,
  ui,
  profile,
  router,
  selectedId,
  caseDetail,
  localBazi,
  localZiwei,
  ziweiError,
  selectedZiweiPalaceName,
  selectedZiweiDayunIndex,
  selectedZiweiLiuyueMonth,
  selectedIndicatorShensha,
  loadBaziForCase,
  loadZiweiForCase,
  isZiweiSectionId,
  profileSyncTag: PROFILE_SYNC_TAG,
  profileSyncMark: PROFILE_SYNC_MARK,
})

const { initializeWorkbench } = useWorkbenchInitialization({
  store,
  nav,
  ui,
  simpleView,
  showNewbieGuide,
  selectedId,
  ensureProfileSyncedCase,
  selectCase,
})

useWorkbenchLifecycle({
  currentSectionId,
  caseDetail,
  localBazi,
  localZiwei,
  isZiweiSectionId,
  isBaziSection,
  loadBaziForCase,
  loadZiweiForCase,
  initializeWorkbench,
  clearGuideDemoTimers,
})

const {
  showCreateDialog,
  showEditDialog,
  formData,
  formSaving,
  openCreateDialog,
  openEditDialog,
  submitCreate,
  submitEdit,
  handleDeleteCase,
  closeCaseDialog,
} = useWorkbenchCaseCrud({
  store,
  caseDetail,
  selectedId,
})

const {
  isCaseHubView,
  caseHubSummary,
  caseHubStatusItems,
  caseHubActions,
  delegatedSectionTitle,
  delegatedSectionSummary,
  caseHubOnboardActions,
  delegatedSectionActions,
  openCaseHubAction,
  handleCaseHubOnboardAction,
  handleDelegatedSectionAction,
} = useWorkbenchCaseHub({
  route,
  router,
  nav,
  caseDetail,
  birthLocalText,
  baziCaseSummaryLine,
  ziweiCaseSummaryText,
  genderLabel,
  isBaziSection,
  isZiweiSectionId,
  openCreateDialog,
  syncProfileToWorkbenchCase,
  openEditDialog,
})

</script>

<template>

        <WorkbenchStateBlock
          v-if="!baziLoading && !ziweiLoading && !baziError && !ziweiError && !localBazi && !(isZiweiSection && localZiwei)"
          state="empty"
          title="暂无可展示的命盘内容"
          description="请先点击“重算”，或切换到其他案例后再返回当前案例。"
          retry-label="重新加载命盘"
          @retry="reloadCurrentCase()"
        />
  <div class="wb-layout">

    <section class="wb-page-hero">
      <div class="wb-page-hero-main">
        <div class="wb-page-kicker">咨询流程工作台</div>
        <h1 class="wb-page-title">先确认客户资料，再进入分析、解读与交付。</h1>
        <p class="wb-page-desc">
          这里不再把案例页做成案件中枢，而是把它收敛为命理师的咨询流程页：选客户、校对资料、进入分析，最后回到报告交付。
        </p>
        <div class="wb-page-actions">
          <button class="wb-btn-accent" @click="openCreateDialog()">新建咨询</button>
          <button class="wb-btn-ghost" @click="router.push('/report')">进入报告区</button>
        </div>
      </div>
      <div class="wb-page-hero-side">
        <div v-for="item in workflowHighlights" :key="item.label" class="wb-page-stat">
          <span class="wb-page-stat-label">{{ item.label }}</span>
          <strong class="wb-page-stat-value">{{ item.value }}</strong>
        </div>
      </div>
    </section>

    <!-- ══════ 中央区域 ══════ -->
    <main class="wb-main">

      <!-- ── 左子列：案例列表 ── -->
      <WorkbenchCaseList
        v-model="searchQ"
        :cases="filteredList"
        :selected-id="selectedId"
        :profile-sync-tag="PROFILE_SYNC_TAG"
        :current-dayun-label="currentCaseDayunLabel"
        :ziwei-summary-text="ziweiCaseSummaryText"
        :bazi-summary-line="baziCaseSummaryLine"
        @create="openCreateDialog()"
        @select-case="selectCase"
      />

      <!-- ── 右子列：案例详情 ── -->
      <section class="wb-detail" v-if="caseDetail && !currentSectionId?.startsWith('bazi-')">

        <!-- ① 顶部：基本信息 -->
        <WorkbenchInfoBar
          :case-detail="caseDetail"
          :simple-view="simpleView"
          :share-url="shareUrl"
          @toggle-view="toggleSimpleView()"
          @sync-profile="syncProfileToWorkbenchCase()"
          @open-report="router.push(`/report/${caseDetail.id}`)"
          @reload="reloadCurrentCase()"
          @edit="openEditDialog()"
          @share="handleShare()"
          @export-json="handleExportJson()"
          @export-pdf="handleExportPdf()"
          @print="triggerPrint()"
          @snapshots="loadSnapshots()"
          @delete-case="handleDeleteCase()"
        />

        <WorkbenchCaseHubPanel
          v-if="isCaseHubView"
          :summary="caseHubSummary"
          :case-name="caseDetail.name"
          :birth-local-text="birthLocalText"
          :location-text="caseDetail.city || caseDetail.tz || '地点待补充'"
          :profile-synced="!!caseDetail.tags?.includes(PROFILE_SYNC_TAG)"
          :status-items="caseHubStatusItems"
          :actions="caseHubActions"
          @open-route="openCaseHubAction"
          @edit-case="openEditDialog"
        />

        <WorkbenchGuideCard
          v-if="showNewbieGuide && !isCaseHubView"
          :current-step="currentGuideStep"
          :progress-percent="guideProgressPercent"
          :steps="newbieGuideSteps"
          @prev="goPrevGuideStep"
          @next="goNextGuideStep"
          @play="playGuideDemo"
          @close="closeNewbieGuide"
          @focus-step="focusGuideStep"
        />

        <template v-if="!isCaseHubView">

        <!-- 加载中 / 错误 -->
        <WorkbenchStateBlock
          v-if="isZiweiSection ? ziweiLoading : baziLoading"
          state="loading"
        />
        <WorkbenchStateBlock
          v-else-if="isZiweiSection ? !!ziweiError : !!baziError"
          state="error"
          :message="isZiweiSection ? ziweiError : baziError"
          @retry="reloadCurrentCase()"
        />
        <WorkbenchStateBlock
          v-else-if="!isZiweiSection && !localBazi"
          state="empty"
          title="八字结果尚未加载"
          description="当前未在加载中，也没有错误提示。请点击重试重新拉取命盘。"
          retry-label="重新加载命盘"
          @retry="reloadCurrentCase()"
        />

        <template v-else-if="isZiweiSection && localZiwei">

          <div v-if="simpleView" class="wb-simple-hint">已开启简洁视图：仅展示核心命盘与关键走势，可点击右上角切换到完整视图。</div>

          <WorkbenchZiweiSummary
            v-if="ziweiSummaryCards"
            :summary="ziweiSummaryCards"
          />

          <!-- 双盘大运对照条 -->
          <WorkbenchDualDayunAxis
            v-if="dualDayunAxis"
            :axis="dualDayunAxis"
            :selected-bazi-start-year="activeDayunTimelineItem?.startYear"
            :selected-ziwei-index="activeZiweiDayun?.index ?? currentZiweiDayun?.index"
          />

          <WorkbenchZiweiOverview
            v-if="!simpleView"
            :summary="localZiwei.summary"
            :patterns="localZiwei.patterns ?? []"
            :lunar-text="`${localZiwei.lunar?.lunar_year ?? '—'}年${localZiwei.lunar?.lunar_month ?? '—'}月${localZiwei.lunar?.lunar_day ?? '—'}日`"
            :template-version="localZiwei.template_version"
            :true-solar-time="localZiwei.true_solar_time"
            :engine-version="localZiwei.engine_version"
          />

          <WorkbenchZiweiFocus
            :palaces="ziweiPalaces"
            :active-palace="activeZiweiPalace"
            :highlighted-palace-name="ziweiHighlightedPalaceName"
            :relations="activeZiweiRelations"
            :relation-graph="activeZiweiRelationGraph"
            @select-palace="selectZiweiPalace"
          />

          <div v-if="!simpleView" class="wb-section wb-zw-bottom-grid">
            <WorkbenchZiweiSelectors
              :dayun-items="localZiwei.dayun?.items?.slice(0, 6) ?? []"
              :liuyue-items="localZiwei.liuyue?.slice(0, 6) ?? []"
              :active-dayun-index="activeZiweiDayun?.index ?? currentZiweiDayun?.index"
              :active-liuyue-month="activeZiweiLiuyue?.month ?? currentZiweiLiuyue?.month"
              :active-dayun-summary="activeZiweiDayunSummary"
              :active-liuyue-summary="activeZiweiLiuyueSummary"
              @select-dayun="selectZiweiDayun"
              @select-liuyue="selectZiweiLiuyue"
            />
            <WorkbenchZiweiAdvice
              :remedies="localZiwei.remedies ?? []"
              :suggestions="localZiwei.life_suggestions ?? []"
            />
          </div>
        </template>

        <!-- ② 命盘可视化 -->
        <template v-else-if="localBazi">

          <div v-if="simpleView" class="wb-simple-hint">已开启简洁视图：保留四柱/五行/大运流年核心模块，其他扩展分析暂时收起。</div>

          <!-- 命盘顶部速览 -->
          <WorkbenchBaziSummary
            v-if="chartSummaryCards"
            :summary="chartSummaryCards"
            :current-year="currentYear"
          />
          <WorkbenchBaziIndicators
            :key-indicators="baziKeyIndicators"
            :active-indicator="activeIndicatorShensha"
            :geju="geju"
            :yongshen="yongshen"
            :strength="strength"
            :day-stem="pillars[2]?.stem ?? '—'"
            :day-stem-color="dayStemColor"
            @toggle-indicator-shensha="toggleIndicatorShensha"
          />

          <!-- 四柱主表 + 五行横条 -->
          <WorkbenchBaziChart
            :pillars="pillars"
            :active-pillar-key="activePillarKey"
            :active-pillar-detail="activePillarDetail"
            :strength="strength"
            :strength-bar-color="dayStemColor"
            :wuxing="wuxing"
            :wuxing-max="wuxingMax"
            :wuxing-radar-points="wuxingRadarPoints"
            :wuxing-radar-axes="wuxingRadarAxes"
            @select-pillar="selectPillar"
          />

          <!-- 大运时间轴 -->
          <WorkbenchBaziDayunTimeline
            v-if="dayunItems.length"
            :items="dayunTimelineItems"
            :active-item="activeDayunTimelineItem"
            @select-dayun="selectDayun"
          />

          <!-- 流年网格 -->
          <WorkbenchBaziLiunianGrid
            v-if="liunianItems.length"
            :current-year="currentYear"
            :items="liunianTimelineItems"
            :active-item="activeLiunianTimelineItem"
            :active-dayun-info="activeLiunianDayunInfo"
            :active-domains="activeLiunianDetail?.domains ?? []"
            :sparkline="liunianSparkline"
            @select-year="toggleLiunianDetail"
          />

          <!-- 流月运势 -->
          <WorkbenchBaziLiuyueHeatmap
            v-if="localBazi?.monthly_fortune?.length"
            :current-year="currentYear"
            :heatmap-items="liuyueHeatmapData"
            :trend-data="liuyueTrendSvg"
            :active-detail="activeLiuyueDetail"
            :linked-months="linkedLiuyueMonths"
            :show-current-year-link-hint="activeLiunianDetail?.year !== currentYear"
            @select-month="selectLiuyue"
          />

        </template>

        <!-- ③ 解读区 -->
        <template v-if="localBazi && !baziLoading">
          <WorkbenchBaziInsights
            :current-year="currentYear"
            :simple-view="simpleView"
            :summary="summary"
            :bazi-data="localBazi"
            :this-year-detail="thisYearDetail"
            :fort-summary="fortSummary"
            :liunian-detail-rows="liunianDetailRows"
            :expanded-liunian-detail-year="expandedLiunianDetailYear"
            :active-liuyue-month="activeLiuyueMonth"
            :geju="geju"
            :yongshen="yongshen"
            @toggle-liunian-detail="toggleLiunianDetail"
            @select-liunian-month="({ year, month }) => selectLiunianMonth(year, month)"
          />

        </template>

        <!-- ④ 快照历史 -->
        <div v-if="snapshots.length && !simpleView" class="wb-section">
          <h2 class="wb-sec-title">快照历史</h2>
          <div class="wb-snapshot-list">
            <div v-for="snap in snapshots" :key="snap.id" class="wb-snapshot-item">
              <span class="wb-snap-kind">{{ snap.kind }}</span>
              <span class="wb-snap-ver">{{ snap.api_version ?? '—' }}</span>
              <span class="wb-snap-date">{{ fmtDate(snap.created_at) }}</span>
              <span v-if="snap.note" class="wb-snap-note">{{ snap.note }}</span>
            </div>
          </div>
        </div>

        </template>

      </section>

      <!-- 未选中占例时：按当前课题显示中间内容，而不是留白 -->
      <section v-else :class="['wb-detail', { 'wb-no-select': !caseDetail }]">
        <template v-if="isCaseHubView">
          <WorkbenchOnboardPanel
            icon="🗂️"
            title="咨询流程从选择客户开始"
            subtitle="先建立或选中客户，再进入八字、紫微、报告或辅助草稿等页面继续完成本次咨询。"
            label="开始咨询"
            description="这里优先承担客户选择、资料校对与下一步分发，不再把整套分析内容堆叠在案例首页。"
            :actions="caseHubOnboardActions"
            @action="handleCaseHubOnboardAction"
          />
        </template>

        <template v-if="currentSectionId">
          <WorkbenchOnboardPanel
            icon="🧭"
            :title="delegatedSectionTitle"
            :subtitle="delegatedSectionSummary"
            label="继续本次咨询"
            description="先在左侧确认客户，再进入对应独立页继续分析、阅读和输出。这里本身只保留流程分发与资料校对。"
            :actions="delegatedSectionActions"
            @action="handleDelegatedSectionAction"
          />
        </template>
      </section>

    </main>

    <!-- ═══ 新建/编辑案例弹窗 ═══ -->
    <WorkbenchCaseDialog
      :show-create-dialog="showCreateDialog"
      :show-edit-dialog="showEditDialog"
      :form-data="formData"
      :form-saving="formSaving"
      @update:form-data-name="formData.name = $event"
      @update:form-data-birth-dt-local="formData.birth_dt_local = $event"
      @update:form-data-gender="formData.gender = $event"
      @update:form-data-solar-time-enabled="formData.solar_time_enabled = $event"
      @close="closeCaseDialog()"
      @submit="showEditDialog ? submitEdit() : submitCreate()"
    />
  </div>
</template>

<style scoped>
/* ══════════════════════════════════════════════════════════
   WorkbenchView 样式
   布局：caselist(320) | detail(1fr)
   侧边导航已迁移到 AppSidebar.vue
   ══════════════════════════════════════════════════════════ */

/* ─── 根布局 ──────────────────────────────────────────────── */
.wb-layout {
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.wb-page-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.85fr);
  gap: 18px;
  padding: 24px 26px;
  border-radius: 24px;
  border: 1px solid #e7e5e4;
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.92));
  box-shadow: 0 12px 28px rgba(28, 25, 23, 0.05);
}

.wb-page-hero-main {
  min-width: 0;
}

.wb-page-kicker {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #b45309;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.wb-page-title {
  margin: 14px 0 0;
  font-size: 34px;
  line-height: 1.18;
  color: #1c1917;
}

.wb-page-desc {
  margin: 12px 0 0;
  max-width: 760px;
  font-size: 14px;
  line-height: 1.85;
  color: #57534e;
}

.wb-page-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

.wb-page-hero-side {
  display: grid;
  gap: 12px;
}

.wb-page-stat {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid #e7e5e4;
  background: rgba(255, 255, 255, 0.8);
}

.wb-page-stat-label {
  font-size: 12px;
  color: #78716c;
}

.wb-page-stat-value {
  display: block;
  margin-top: 8px;
  font-size: 20px;
  line-height: 1.3;
  color: #1c1917;
}

.wb-case-dayun,
.wb-case-ziwei,
.wb-case-bazi-summary {
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wb-btn-ghost.is-active {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.10);
  color: #1e40af;
}

.wb-simple-hint {
  margin: 10px 0 12px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(16, 185, 129, 0.28);
  background: rgba(16, 185, 129, 0.08);
  color: #065f46;
  font-size: 12px;
  line-height: 1.45;
}

.wb-guide-focus-target {
  animation: wb-guide-focus-pulse 1.8s ease;
}

@keyframes wb-guide-focus-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    outline: 0 solid rgba(37, 99, 235, 0);
  }
  25% {
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.18);
    outline: 2px solid rgba(37, 99, 235, 0.45);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(37, 99, 235, 0);
    outline: 0 solid rgba(37, 99, 235, 0);
  }
}
.wb-btn-accent {
  padding: 8px 16px;
  background: var(--accent); color: #fff; border: none;
  border-radius: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background var(--dur-fast);
  white-space: nowrap;
}
.wb-btn-accent:hover { background: var(--accent-dark); }
.wb-btn-ghost {
  padding: 8px 14px;
  background: transparent; border: 1px solid var(--border-md);
  border-radius: 8px; font-size: 13px; color: var(--text-2);
  cursor: pointer; transition: all var(--dur-fast);
  white-space: nowrap;
}
.wb-btn-ghost:hover { border-color: var(--accent); color: var(--accent); }

@keyframes wb-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ② 命盘区块 */
.wb-section {
  padding: 20px 24px 0;
}
.wb-sec-title {
  font-size: 14px; font-weight: 700; color: var(--text);
  margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
}
.wb-sec-note { font-size: 11px; color: var(--text-3); font-weight: 400; }

.wb-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 16px; min-width: 100px;
}
.wb-card-label { font-size: 10px; color: var(--text-3); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .05em; }
/* ─── 打印样式 ────────────────────────────────────────────── */
@media print {
  .wb-layout { grid-template-columns: 1fr; }
  .wb-caselist { display: none; }
  .wb-detail { height: auto; overflow: visible; background: white; }
  .wb-section { page-break-inside: avoid; padding: 16px 24px; }
  .wb-sec-title { font-size: 16px; margin-bottom: 12px; border-bottom: 1px solid #ccc; padding-bottom: 6px; }
  .wb-btn-ghost, .wb-btn-accent { display: none; }
  .wb-search-wrap { display: none; }
  .wb-modal { display: none; }
  body { background: white; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  table th, table td { border: 1px solid #333; padding: 6px; text-align: center; font-size: 11px; }
}

/* 空选中态 */
.wb-no-select {
  justify-content: center; align-items: center; gap: 16px;
  padding: 28px;
}

.wb-onboard {
}

/* 最后一个 section 加底部 padding */
.wb-section:last-child { padding-bottom: 32px; }

/* 快照列表 */
.wb-snapshot-list { display: flex; flex-direction: column; gap: 6px; }
.wb-snapshot-item {
  display: flex; gap: 12px; align-items: center;
  padding: 8px 14px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px;
  font-size: 12px; color: var(--text-2);
}
.wb-snap-kind { font-weight: 600; color: var(--accent-dark); padding: 1px 8px; background: var(--accent-lt); border-radius: 99px; }
.wb-snap-ver { color: var(--text-3); font-family: var(--font-mono); }
.wb-snap-date { color: var(--text-3); font-family: var(--font-mono); }
.wb-snap-note { color: var(--text-2); flex: 1; }

.wb-tips {
  font-size: 13px;
  color: var(--text-3);
  margin: 0 0 12px 0;
  line-height: 1.6;
  font-family: var(--font-cn);
}

/* ─── 紫微概览 ─────────────────────────────────────────────── */
.wb-zw-bottom-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 12px;
}

/* ─── 响应式 ──────────────────────────────────────────────── */
@media (max-width: 1280px) {
  .wb-page-hero { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  .wb-layout { grid-template-columns: 240px 1fr; }
  .wb-zw-bottom-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .wb-pillar-detail-head { flex-direction: column; }
}
@media (max-width: 560px) {
  .wb-page-title { font-size: 28px; }
  .wb-sec-title { flex-wrap: wrap; gap: 6px; }
}
</style>
