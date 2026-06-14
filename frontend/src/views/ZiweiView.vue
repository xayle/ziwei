<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useAiStore } from '@/stores/ai'
import { parseZiweiApiErrorMessage, useZiweiCalculationFlow } from '@/composables/useZiweiCalculationFlow'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import { useZiweiWorkflowActions } from '@/composables/useZiweiWorkflowActions'
import { useZiweiChartActions } from '@/composables/useZiweiChartActions'
import { useZiweiChartSectionBindings } from '@/composables/useZiweiChartSectionBindings'
import { useZiweiChartDisplayState } from '@/composables/useZiweiChartDisplayState'
import { useZiweiDayunState } from '@/composables/useZiweiDayunState'
import { useZiweiFormState } from '@/composables/useZiweiFormState'
import { useZiweiOverlayFeedback } from '@/composables/useZiweiOverlayFeedback'
import { useZiweiBaziAnalysis } from '@/composables/useZiweiBaziAnalysis'
import { useZiweiDerivedCollections } from '@/composables/useZiweiDerivedCollections'
import { useZiweiDisplayHelpers } from '@/composables/useZiweiDisplayHelpers'
import { useZiweiInfoBarActionsBindings } from '@/composables/useZiweiInfoBarActionsBindings'
import { useZiweiAlgorithmSettings } from '@/composables/useZiweiAlgorithmSettings'
import { useZiweiInteractionState } from '@/composables/useZiweiInteractionState'
import { useZiweiKeyboardShortcuts } from '@/composables/useZiweiKeyboardShortcuts'
import { useZiweiNarrativeActions } from '@/composables/useZiweiNarrativeActions'
import { useZiweiPalaceLayout } from '@/composables/useZiweiPalaceLayout'
import { useZiweiPalaceGrouping } from '@/composables/useZiweiPalaceGrouping'
import { useZiweiResultOverlaysBindings } from '@/composables/useZiweiResultOverlaysBindings'
import { useZiweiSummarySectionBindings } from '@/composables/useZiweiSummarySectionBindings'
import { useZiweiStarInteractions } from '@/composables/useZiweiStarInteractions'
import { useZiweiTimeOverlays } from '@/composables/useZiweiTimeOverlays'
import { useZiweiTimelineControls } from '@/composables/useZiweiTimelineControls'
import { useZiweiActionMenuBindings } from '@/composables/useZiweiActionMenuBindings'
import { useZiweiToolPanelBindings } from '@/composables/useZiweiToolPanelBindings'
import { useZiweiViewInteractionHelpers } from '@/composables/useZiweiViewInteractionHelpers'
import { useZiweiViewPreferences } from '@/composables/useZiweiViewPreferences'
import { useZiweiBaziMenuState } from '@/composables/useZiweiBaziMenuState'
import { useZiweiPalaceNameMaps } from '@/composables/useZiweiPalaceNameMaps'
import { ZIWEI_STAR_INFO } from '@/constants/ziweiStarInfo'
import { SIHUA_COLORS } from '@/composables/useZiweiPalaceLayout'
import {
  BRANCHES,
  JU_COLORS,
  ZODIAC_ANIMALS,
  getAuxStars,
  getPalaceTransforms,
  getStarBrightnessValue,
  getStarName,
  getStarTransforms,
  tfColorStyle,
  tfOutlineStyle,
} from '@/utils/ziweiViewHelpers'
import { useProfileStore } from '@/stores/profile'
import CityPicker from '@/components/CityPicker.vue'
import {
  ZiweiBaziDetailSection,
  ZiweiChartSection,
  ZiweiDayunTab,
  ZiweiFlyingTab,
  ZiweiForecastTab,
  ZiweiLiunianTab,
  ZiweiLiuyueTab,
  ZiweiPalacesTab,
  ZiweiPatternsTab,
  ZiweiAlgoSettings,
  ZiweiResultHeader,
  ZiweiResultOverlays,
  ZiweiSuggestTab,
  ZiweiSummaryAnalysisPanels,
  ZiweiSummaryOverview,
  ZiweiTimelineBar,
} from '@/components/ziwei'

const route = useRoute()
const router = useRouter()
const ui      = useUiStore()
const ai      = useAiStore()

const profile = useProfileStore()

// 从个人信息 store 解析出年月日时分
const _bd = profile.parseBirthDt()

const {
  year,
  month,
  day,
  hour,
  minute,
  gender,
  liunianYear,
  longitude,
  initCity,
  showForm,
  setFormValues,
} = useZiweiFormState({
  birth: _bd,
  gender: profile.gender,
  longitude: profile.lon,
  cityName: profile.cityName,

})

// ── 核心状态 refs ──────────────────────────────────────────────
const currentYear    = new Date().getFullYear()
const currentMonth   = new Date().getMonth() + 1
const loading        = ref(false)
const error          = ref('')
const result         = ref<ZiweiResponse | null>(null)
const activeTab      = ref<'chart' | 'summary' | 'palaces' | 'dayun' | 'liunian' | 'liuyue' | 'patterns' | 'flying' | 'forecast' | 'suggest'>('chart')
const selectedPalace = ref<PalaceResponse | null>(null)
const flyingExplain  = ref<{
  title: string; subtitle: string; huaColor: string; body: string; palaceDesc: string
} | null>(null)

// ── 视图 Tab（4 个顶层 Tab，UI 层控制）────────────────────────
const VIEW_TABS = [
  { key: 'natal',    label: '命盘' },
  { key: 'analysis', label: '格局·宫位' },
  { key: 'timeline', label: '时间线' },
  { key: 'predict',  label: '预测·建议' },
] as const
type ViewTabKey = typeof VIEW_TABS[number]['key']
const viewTab = ref<ViewTabKey>('natal')

// activeTab（供 composable 内部使用）→ viewTab 自动映射
const TAB_TO_VIEW: Record<string, ViewTabKey> = {
  chart: 'natal',    summary: 'natal',
  palaces: 'analysis', patterns: 'analysis', flying: 'analysis',
  dayun: 'timeline', liunian: 'timeline',    liuyue: 'timeline',
  forecast: 'predict', suggest: 'predict',
}
// viewTab → activeTab 反向映射（保持 composable 内部逻辑一致）
const VIEW_TO_TAB = {
  natal: 'chart',
  analysis: 'palaces',
  timeline: 'dayun',
  predict: 'forecast',
} as const
watch(activeTab, (v) => {
  const mapped = TAB_TO_VIEW[v]
  if (mapped) viewTab.value = mapped
}, { flush: 'sync' })
watch(viewTab, (v) => {
  activeTab.value = VIEW_TO_TAB[v]
}, { flush: 'sync' })

// ── 八字菜单本地状态 ───────────────────────────────────────────
const {
  baziMenuActive,
  baziDayunFocusIdx,
  baziCopyDone,
  baziMenuItems,
} = useZiweiBaziMenuState()

// ── 算法设置 ──────────────────────────────────────────────────
const {
  showAlgoSettings,
  algoLateZishi,
  algoLeapMethod,
  algoKuiyue,
  algoTianma,
  algoTiankong,
  algoBrightness,
  algoJiukong,
  algoTianshang,
  algoMingzhu,
  algoLiunianSihua,
  algoChangsheng,
  sihuaJia, sihuaWu, sihuaGeng, sihuaXin, sihuaRen, sihuaGui,
  hasCustomAlgoSettings,
  buildSihuaIndices,
  resetAlgoSettings,
  applyPreset,
} = useZiweiAlgorithmSettings()

// ── 大运状态 ──────────────────────────────────────────────────
const {
  currentDayun,
  currentDayunGz,
  dayunStats,
  dayunProgress,
} = useZiweiDayunState({ result, currentYear })

// ── 时间轴控制 ────────────────────────────────────────────────
const {
  selectedDaxianIdx,
  selectedLiunianYear,
  selectedLiuyueMonth,
  showYearPicker,
  liunianYears,
  allLiunianYears,
  yearPickerList,
  scrollToCurrentDayun,
  scrollToCurrentLiuyue,
  toggleSelectedDaxian,
  setSelectedLiunianYearValue,
  stepSelectedLiunianYear,
  toggleYearPicker,
  closeYearPicker,
  selectYearFromPicker,
} = useZiweiTimelineControls({
  result,
  liunianYear,
  currentYear,
  triggerRecalculate: () => doCalculate(),
})

// ── 宫位布局 ──────────────────────────────────────────────────
const {
  palaceGrid,
  palaceDayunMap,
  sihuaLines,
  getPalaceCenter,
  getCurvedPath,
  getCurvedMidpoint,
} = useZiweiPalaceLayout({
  getResult:           () => result.value,
  getSelectedPalace:   () => selectedPalace.value,
  isSihuaLinesVisible: () => showSihuaLines.value,
})

// ── 显示辅助函数 ──────────────────────────────────────────────
const {
  palaceHasTransform,
  getPalaceQuickInfo,
  getMonthForecast,
  liuyueRows,
  liuyueSummary,
  forecastScoreColor,
  liunianSihuaWithPalace,
} = useZiweiDisplayHelpers({
  result,
  selectedDaxianIdx,
  currentDayun,
  getPalaceTransforms,
})

// ── 大限/流年四化及宫名映射 ──────────────────────────────────
const {
  palaceDaxianNames,
  daxianSihuaMap,
  liunianSihuaMap,
} = useZiweiPalaceNameMaps({ result, selectedDaxianIdx, currentDayun })

const {
  forecastStats,
  forecastMonthlyOverview,
  forecastRiskMonths,
  sihuaPathList,
  sihuaByType,
} = useZiweiDerivedCollections({
  getResult: () => result.value,
  getAuxStars,
  getStarTransforms,
  getStarName,
})

const {
  chartSummarySectionBindings,
  summaryOverviewBindings,
  summaryAnalysisBindings,
} = useZiweiSummarySectionBindings({
  result,
  currentDayunGz,
  forecastStats,
  forecastRiskMonths,
  sihuaPathList,
  sihuaByType,
  getAuxStars,
  getStarTransforms,
  getStarName,
  getStarBrightnessValue,
  juColors: JU_COLORS,
})

const {
  palaceFilter,
  palacesStats,
  filteredPalaces,
  palaceGroupExpanded,
  togglePalaceGroup,
  groupedFilteredPalaces,
} = useZiweiPalaceGrouping({
  result,
})

const {
  showHotkeyPanel,
  HOTKEY_LIST,
  showBrightnessLegend,
  BRIGHTNESS_LEGEND,
  chartMode,
  showSihuaLines,
  showLiunianOverlay,
  starDisplayOpts,
  overlayOpts,
} = useZiweiChartDisplayState()

const {
  showHistoryPanel,
  showThemePanel,
  chartHistory,
  historyCount,
  chartTheme,
  fontSizeLevel,
  saveToHistory,
  restoreFromHistory,
  clearHistory,
  formatHistoryTime,
  toggleHistoryPanel,
  setChartTheme,
  toggleThemePanel,
  closeThemePanel,
  setFontSize,
  CHART_THEMES,
  FONT_SIZE_OPTIONS,
} = useZiweiViewPreferences({
  result,
  year,
  month,
  day,
  hour,
  minute,
  gender,
  longitude,
  setFormValues,
  triggerRecalculate: () => doCalculate(),
})

const {
  showNotesPanel,
  showBookmarksPanel,
  chartNotes,
  editingNote,
  noteInput,
  noteTarget,
  noteTargetName,
  addNote,
  updateNote,
  startEditNote,
  cancelEditNote,
  deleteNote,
  toggleNotesPanel,
  toggleBookmarksPanel,
  togglePalaceBookmark,
  isPalaceBookmarked,
  bookmarkedPalaces,
  toggleStarStar,
  isStarStarred,
  starredStarsDistribution,
} = useZiweiInteractionState({
  result,
  selectedPalace,
})

const {
  bridge: toolPanelBridge,
  centerOverlayPanelBindings,
  toggleSharePanel,
  toggleComparePanel,
  toggleCalendarView,
} = useZiweiToolPanelBindings({
  result,
  showHotkeyPanel,
  selectPalace: (palace) => selectPalace(palace),
  selectPalaceByIndex: (idx: number) => selectPalaceByIndex(idx),
  showBookmarksPanel,
  bookmarkedPalaces,
  togglePalaceBookmark,
  year,
  month,
  day,
  hour,
  minute,
  gender,
  longitude,
  getMonthForecast,
})

const {
  overlayFeedback,
  showOverlayFeedback,
  clearOverlayFeedback,
  isOverlayFeedbackVisible,
} = useZiweiOverlayFeedback()

const workflowActions = useZiweiWorkflowActions({
  router,
  result,
  year,
  month,
  day,
  hour,
  minute,
  gender,
  longitude,
  liunianYear,
  initCity,
  getProfileCityName: () => profile.cityName || null,
  getProfileLongitude: () => profile.lon ?? null,
  parseApiError: parseZiweiApiErrorMessage,
})

const {
  savedCaseId,
  savedCaseName,
  currentSnapshotId,
  isSavingCase,
  canSaveCurrentChart,
  reviewSubmitting,
  glossarySuggestedTerms,
  saveCurrentChart,
  toggleReviewPanel,
  submitCurrentReview,
  openCaseWorkflow,
  toggleLlmPanel,
  toggleOpsPanel,
  toggleBatchPanel,
  toggleGlossaryPanel,
  toggleMultiCompatPanel,
  toggleFengshuiPanel,
} = workflowActions

const {
  isExportingImage,
  showAdjustModal,
  exportPDF,
  exportChartAsImage,
  copyChartInfo,
} = useZiweiChartActions({
  result,
  activeTab,
  getChartExportElement: toolPanelBridge.getChartExportElement,
  toggleSharePanel,
  toggleNotesPanel,
  toggleCalendarView,
  toggleComparePanel,
  toggleBookmarksPanel,
  showOverlayFeedback,
})

const {
  doCalculate,
  doDemo,
  resetForm,
  loadFromUrlParams,
  initializeFromProfileAndRoute,
} = useZiweiCalculationFlow({
  route,
  router,
  profile,
  workflowActions,
  result,
  loading,
  error,
  activeTab,
  selectedPalace,
  showForm,
  year,
  month,
  day,
  hour,
  minute,
  gender,
  liunianYear,
  longitude,
  initCity,
  algoLateZishi,
  algoLeapMethod,
  algoKuiyue,
  algoTianma,
  algoTiankong,
  algoBrightness,
  algoJiukong,
  algoTianshang,
  algoMingzhu,
  algoLiunianSihua,
  algoChangsheng,
  buildSihuaIndices,
  saveToHistory,
})

onMounted(() => {
  loadFromUrlParams()
})

const {
  showStarSearch,
  starSearchQuery,
  starSearchResults,
  openStarSearch,
  closeStarSearch,
  hoveredStar,
  starTooltipPos,
  showStarTooltip,
  hideStarTooltip,
  selectPalace,
  selectPalaceByIndex,
  closeSelectedPalace,
  selectSearchResult,
} = useZiweiStarInteractions({
  result,
  selectedPalace,
  starInfoMap: ZIWEI_STAR_INFO,
  getChartExportElement: toolPanelBridge.getChartExportElement,
})

const {
  resultOverlaysBindings,
} = useZiweiResultOverlaysBindings({
  showStarSearch,
  starSearchQuery,
  starSearchResults,
  closeStarSearch,
  selectSearchResult,
  hoveredStar,
  starInfoMap: ZIWEI_STAR_INFO,
  starTooltipPos,
})

const {
  actionMenuBindings,
  toolPanelsBindings,
  toggleHotkeyPanel,
} = useZiweiActionMenuBindings({
  hasResult: () => Boolean(result.value),
  savedCaseId,
  reviewSubmitting,
  historyCount,
  openCaseWorkflow,
  submitCurrentReview,
  toggleReviewPanel,
  toggleLlmPanel,
  toggleOpsPanel,
  toggleBatchPanel,
  toggleGlossaryPanel,
  toggleMultiCompatPanel,
  toggleFengshuiPanel,
  showHotkeyPanel,
  hotkeyList: HOTKEY_LIST,
  showBrightnessLegend,
  brightnessLegend: BRIGHTNESS_LEGEND,
  showHistoryPanel,
  chartHistory,
  formatHistoryTime,
  toggleHistoryPanel,
  clearHistory,
  restoreFromHistory,
  openStarSearch: () => openStarSearch(),
})

useZiweiKeyboardShortcuts({
  activeTab,
  hasResult: () => Boolean(result.value),
  palaceCount: () => result.value?.palaces.length ?? 0,
  selectPalaceByOrder: toolPanelBridge.selectPalaceByOrder,
  closeSelectedPalace,
  toggleHotkeyPanel,
})

const {
  sanfangIndices,
  shiftDay,
  shiftHour,
  gotoZeri,
} = useZiweiViewInteractionHelpers({
  router,
  result,
  selectedPalace,
  year,
  month,
  day,
  hour,
  doCalculate,
})

const {
  baziDetails,
  shiShenAnalyze,
  cangganNayin,
  baziShenshaList,
  baziRelationAnalyze,
  baziGejuYongshen,
  baziLuckOverview,
  baziDayunFocusDetail,
  baziFocusedDayunSihuaStars,
  baziRelatedLiuyueMap,
  baziTenGodUsage,
  baziWuxingCount,
} = useZiweiBaziAnalysis({
  result,
  currentDayunGz,
  baziDayunFocusIdx,
})

const {
  gotoAi,
  copyBaziSectionSummary,
} = useZiweiNarrativeActions({
  result,
  ui,
  ai,
  baziMenuActive,
  baziMenuItems,
  baziDetails,
  shiShenAnalyze,
  cangganNayin,
  baziShenshaList,
  baziRelationAnalyze,
  baziGejuYongshen,
  baziLuckOverview,
  baziDayunFocusDetail,
  baziTenGodUsage,
  baziCopyDone,
  baziWuxingCount,
})

const {
  infoBarActionsBindings,
} = useZiweiInfoBarActionsBindings({
  overlayFeedback,
  isOverlayFeedbackVisible,
  isExportingImage,
  canSaveCurrentChart,
  isSavingCase,
  savedCaseId,
  exportPDF,
  exportChartAsImage,
  gotoZeri,
  gotoAi,
  saveCurrentChart,
  actionMenuBindings,
})

const {
  selectedLiuyueData,
  palaceLiunianInfo,
  liunianLifePalaceIdx,
  palaceLiunianNames,
  liuyueLifePalaceIdx,
  palaceLiuyueNames,
  liuyueSihuaMap,
  currentLiunianAge,
  xiaoxianPalaceIdx,
  palaceXiaoxianNames,
  xiaoxianSihuaMap,
} = useZiweiTimeOverlays({
  result,
  year,
  gender,
  selectedLiunianYear,
  selectedLiuyueMonth,
})

const { chartSectionBindings } = useZiweiChartSectionBindings({
  header: {
    chartMode,
    showSihuaLines,
    showLiunianOverlay,
    selectedLiuyueMonth,
    liuyueOptions: computed(() => result.value?.liuyue ?? []),
    starDisplayOpts,
    overlayOpts,
    showThemePanel,
    chartTheme,
    fontSizeLevel,
    chartThemes: CHART_THEMES,
    fontSizeOptions: FONT_SIZE_OPTIONS,
    currentDayun,
    chartSummarySectionBindings,
    palaces: computed(() => result.value?.palaces ?? []),
    selectedPalace,
    palaceHasTransform,
    getPalaceQuickInfo,
    toggleThemePanel,
    closeThemePanel,
    setChartTheme,
    setFontSize,
    selectPalace,
  },
  canvas: {
    result,
    currentYear,
    juColors: JU_COLORS,
    showNotesPanel,
    chartNotes,
    editingNote,
    noteInput,
    noteTarget,
    noteTargetName,
    addNote,
    updateNote,
    startEditNote,
    cancelEditNote,
    deleteNote,
    centerOverlayPanelBindings,
    palaceGrid,
    selectedPalace,
    sanfangIndices,
    liunianLifePalaceIdx,
    liuyueLifePalaceIdx,
    xiaoxianLifePalaceIdx: xiaoxianPalaceIdx,
    isPalaceBookmarked,
    palaceDayunMap,
    palaceLiunianInfo,
    palaceDaxianNames,
    palaceLiunianNames,
    palaceLiuyueNames,
    palaceXiaoxianNames,
    starDisplayOpts,
    overlayOpts,
    daxianSihuaMap,
    liunianSihuaMap,
    liuyueSihuaMap,
    xiaoxianSihuaMap,
    tfColorStyle,
    tfOutlineStyle,
    selectPalace,
    togglePalaceBookmark,
    shiftDay,
    shiftHour,
    returnChart: () => {
      activeTab.value = 'chart'
      viewTab.value = 'natal'
    },
    showSihuaLines,
    chartMode,
    sihuaLines,
    sihuaColors: SIHUA_COLORS,
    getPalaceCenter,
    getCurvedPath,
    getCurvedMidpoint,
  },
  workspace: {
    dayunItems: computed(() => result.value?.dayun?.items ?? []),
    currentDayunGanzhi: computed(() => currentDayun.value?.ganzhi ?? null),
    selectedDaxianIdx,
    selectedLiunianYear,
    allLiunianYears,
    liunianYears,
    currentYear,
    birthYear: year,
    toggleSelectedDaxian,
    setSelectedLiunianYearValue,
    stepSelectedLiunianYear,
    selectedPalace,
    starredStarsDistribution,
    showStarTooltip,
    hideStarTooltip,
    toggleStarStar,
    isStarStarred,
    tfColorStyle,
    closeSelectedPalace,
  },
})

</script>

<template>
  <div class="wrap ziwei-view">
    <h1 class="page-title">紫微斗数</h1>

    <!-- 表单折叠控制栏 -->
    <div class="form-toggle-bar">
      <button class="btn-toggle-form" @click="showForm = !showForm">
        {{ showForm ? '▴ 收起参数' : '▾ 修改参数' }}
      </button>
      <span v-if="!showForm && result" class="current-params">
        {{ year }}/{{ String(month).padStart(2,'0') }}/{{ String(day).padStart(2,'0') }} {{ String(hour).padStart(2,'0') }}:{{ String(minute).padStart(2,'0') }} · {{ gender }}
      </span>
    </div>

    <!-- 输入表单 -->
    <section v-show="showForm" class="card form-card">
      <div class="form-grid">
        <div class="form-row">
          <label>出生年</label>
          <input type="number" v-model.number="year" min="1900" max="2100" style="width:90px" />
          <label style="width:auto">月</label>
          <input type="number" v-model.number="month" min="1" max="12" style="width:60px" />
          <label style="width:auto">日</label>
          <input type="number" v-model.number="day" min="1" max="31" style="width:60px" />
          <label style="width:auto">时</label>
          <input type="number" v-model.number="hour" min="0" max="23" style="width:60px" />
          <label style="width:auto">分</label>
          <input type="number" v-model.number="minute" min="0" max="59" style="width:60px" />
        </div>
        <div class="form-row">
          <label>性别</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="女" />女</label>
          <label class="radio-opt"><input type="radio" v-model="gender" value="男" />男</label>
        </div>
        <div class="form-row">
          <label>流年</label>
          <input type="number" v-model.number="liunianYear" placeholder="今年" style="width:90px" />
        </div>
        <div class="form-row">
          <CityPicker v-model="longitude" :optional="true" :initial-city="initCity" />
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-primary" :disabled="loading" @click="doCalculate">
          {{ loading ? '排盘中…' : '排　盘' }}
        </button>
        <button class="btn-sec" :disabled="loading" @click="doDemo">演示盘</button>
        <button class="btn-sec" @click="resetForm">重置</button>
        <span v-if="error" class="error-msg">{{ error }}</span>
      </div>
    </section>

    <!-- 骨架屏 -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skel-line" style="width:50%"></div>
      <div class="skel-box" style="height:200px"></div>
    </div>

    <!-- 算法设置 Drawer（⚙ 按钮触发，全局生效，排盘前后均可访问） -->
    <ZiweiAlgoSettings
      v-model:show-algo-settings="showAlgoSettings"
      v-model:algo-late-zishi="algoLateZishi"
      v-model:algo-leap-method="algoLeapMethod"
      v-model:algo-kuiyue="algoKuiyue"
      v-model:algo-tianma="algoTianma"
      v-model:algo-tiankong="algoTiankong"
      v-model:algo-brightness="algoBrightness"
      v-model:algo-jiukong="algoJiukong"
      v-model:algo-tianshang="algoTianshang"
      v-model:algo-mingzhu="algoMingzhu"
      v-model:algo-liunian-sihua="algoLiunianSihua"
      v-model:algo-changsheng="algoChangsheng"
      v-model:sihua-jia="sihuaJia"
      v-model:sihua-wu="sihuaWu"
      v-model:sihua-geng="sihuaGeng"
      v-model:sihua-xin="sihuaXin"
      v-model:sihua-ren="sihuaRen"
      v-model:sihua-gui="sihuaGui"
      :has-custom-algo-settings="hasCustomAlgoSettings"
      @reset="resetAlgoSettings"
      @apply-preset="applyPreset"
    />

    <!-- 结果区 -->
    <template v-if="result">
      <ZiweiResultHeader
        :result="result"
        :ju-colors="JU_COLORS"
        :info-bar-actions-bindings="infoBarActionsBindings"
        :tool-panels-bindings="toolPanelsBindings"
      />

       <ZiweiResultOverlays v-bind="resultOverlaysBindings" />

      <!-- 算法设置 Drawer（⚙ 按钮触发，全局生效） -->
      <!-- 已移至表单区下方，此处仅保留占位注释 -->

      <!-- 4-Tab 顶部导航栏 -->
      <div class="ziwei-view-tabs">
        <button
          v-for="tab in VIEW_TABS"
          :key="tab.key"
          :class="['vt-btn', { active: viewTab === tab.key }]"
          @click="viewTab = tab.key"
        >{{ tab.label }}</button>
        <button class="vt-algo-btn" @click="showAlgoSettings = !showAlgoSettings" title="算法设置">⚙</button>
      </div>

      <!-- Tab 1: 命盘 -->
      <section v-if="viewTab === 'natal'" class="tab-panel chart-tab-panel">
        <p v-if="result.summary" class="summary-block">{{ result.summary }}</p>
        <div class="ziwei-card">
          <ZiweiChartSection v-bind="chartSectionBindings" />
        </div>
        <div class="ziwei-cards">
          <div class="ziwei-card">
            <ZiweiSummaryOverview v-bind="summaryOverviewBindings" />
          </div>
          <div class="ziwei-card">
            <ZiweiBaziDetailSection
              :active-menu="baziMenuActive"
              :menu-items="baziMenuItems"
              :bazi-copy-done="baziCopyDone"
              :bazi-details="baziDetails"
              :shi-shen-analyze="shiShenAnalyze"
              :canggan-nayin="cangganNayin"
              :bazi-shensha-list="baziShenshaList"
              :bazi-relation-analyze="baziRelationAnalyze"
              :bazi-geju-yongshen="baziGejuYongshen"
              :bazi-luck-overview="baziLuckOverview"
              :bazi-dayun-focus-detail="baziDayunFocusDetail"
              :bazi-related-liuyue-map="baziRelatedLiuyueMap"
              :bazi-focused-dayun-sihua-stars="baziFocusedDayunSihuaStars"
              :bazi-ten-god-usage="baziTenGodUsage"
              :bazi-wuxing-count="baziWuxingCount"
              @update:active-menu="baziMenuActive = $event"
              @copy-section="copyBaziSectionSummary"
              @set-dayun-focus="baziDayunFocusIdx = $event"
            />
          </div>
        </div>
        <div class="ziwei-card">
          <ZiweiSummaryAnalysisPanels
            v-bind="summaryAnalysisBindings"
            @select-palace="selectPalaceByIndex"
          />
        </div>
      </section>

      <!-- Tab 2: 格局·宫位 -->
      <section v-if="viewTab === 'analysis'" class="tab-panel">
        <div class="ziwei-cards">
          <div class="ziwei-card">
            <ZiweiPatternsTab :patterns="result.patterns || []" />
          </div>
          <div v-if="result.flying" class="ziwei-card">
            <ZiweiFlyingTab :flying="result.flying" @explain="flyingExplain = $event" />
          </div>
          <div v-if="result.flying" class="ziwei-card explain-panel" :class="{ 'explain-empty': !flyingExplain }">
            <template v-if="flyingExplain">
              <button class="explain-close" title="关闭讲解" @click="flyingExplain = null">×</button>
              <span class="explain-badge" :style="{ background: flyingExplain.huaColor }">{{ flyingExplain.title }}</span>
              <p class="explain-subtitle">{{ flyingExplain.subtitle }}</p>
              <p class="explain-body">{{ flyingExplain.body }}</p>
              <p v-if="flyingExplain.palaceDesc" class="explain-palace">{{ flyingExplain.palaceDesc }}</p>
            </template>
            <div v-else class="explain-hint-wrap">
              <span class="explain-hint-text">← 点击左侧飞化条目<br>查看讲解</span>
            </div>
          </div>
        </div>
        <div class="ziwei-card">
          <ZiweiPalacesTab
            :palaces="result.palaces"
            :palaces-stats="palacesStats"
            :palace-filter="palaceFilter"
            :grouped-filtered-palaces="groupedFilteredPalaces"
            :palace-group-expanded="palaceGroupExpanded"
            :filtered-palaces-count="filteredPalaces.length"
            @update:palace-filter="palaceFilter = $event"
            @toggle-group="togglePalaceGroup"
          />
        </div>
      </section>

      <!-- Tab 3: 时间线 -->
      <section v-if="viewTab === 'timeline'" class="tab-panel">
        <ZiweiTimelineBar
          v-if="result.dayun?.items?.length"
          :items="result.dayun?.items ?? []"
          :current-dayun-ganzhi="currentDayun?.ganzhi ?? null"
          :selected-daxian-idx="selectedDaxianIdx"
          :selected-liunian-year="selectedLiunianYear"
          :all-liunian-years="allLiunianYears"
          :liunian-years="liunianYears"
          :current-year="currentYear"
          :birth-year="year"
          @toggle-daxian="toggleSelectedDaxian"
          @update:selected-liunian-year="setSelectedLiunianYearValue"
          @step-liunian="stepSelectedLiunianYear"
        />
        <div class="ziwei-card">
          <ZiweiDayunTab
            :dayun="result.dayun"
            :current-year="currentYear"
            :dayun-stats="dayunStats"
            :dayun-progress="dayunProgress"
            @locate-current="scrollToCurrentDayun"
          />
        </div>
        <div class="ziwei-cards">
          <div class="ziwei-card">
            <ZiweiLiunianTab
              :liunian="result.liunian"
              :forecast="result.forecast"
              :current-year="currentYear"
              :current-month="currentMonth"
              :current-dayun-gz="currentDayunGz"
              :branches="BRANCHES"
              :zodiac-animals="ZODIAC_ANIMALS"
              :show-year-picker="showYearPicker"
              :year-picker-list="yearPickerList"
              :liunian-sihua-with-palace="liunianSihuaWithPalace"
              :forecast-score-color="forecastScoreColor"
              :tf-color-style="tfColorStyle"
              @select-year="selectYearFromPicker"
              @toggle-year-picker="toggleYearPicker()"
              @close-year-picker="closeYearPicker()"
            />
          </div>
          <div class="ziwei-card">
            <ZiweiLiuyueTab
              :liuyue-rows="liuyueRows"
              :liuyue-summary="liuyueSummary"
              :current-year="currentYear"
              :current-month="currentMonth"
              :liunian-year="result.liunian?.year"
              :forecast-score-color="forecastScoreColor"
              :tf-color-style="tfColorStyle"
              @locate-current="scrollToCurrentLiuyue"
            />
          </div>
        </div>
      </section>

      <!-- Tab 4: 预测·建议 -->
      <section v-if="viewTab === 'predict'" class="tab-panel">
        <div class="ziwei-cards">
          <div v-if="result.forecast" class="ziwei-card">
            <ZiweiForecastTab
              :forecast="result.forecast"
              :forecast-stats="forecastStats"
              :forecast-monthly-overview="forecastMonthlyOverview"
              :forecast-risk-months="forecastRiskMonths"
              :forecast-score-color="forecastScoreColor"
            />
          </div>
          <div class="ziwei-card">
            <ZiweiSuggestTab
              :remedies="result.remedies || []"
              :life-suggestions="result.life_suggestions || []"
            />
          </div>
        </div>
      </section>

      <!-- 版本信息脚注 -->
      <footer v-if="result.engine_version || result.algorithm_version" class="result-footer">
        <span v-if="result.engine_version" class="ver-item">引擎 {{ result.engine_version }}</span>
        <span v-if="result.algorithm_version" class="ver-item">算法 {{ result.algorithm_version }}</span>
        <span v-if="result.template_version" class="ver-item">模板 {{ result.template_version }}</span>
      </footer>
    </template>
  </div>
</template>

<style src="./ZiweiView.css" scoped />
