<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
  ZiweiResultIntro,
  ZiweiResultOverlays,
  ZiweiSuggestTab,
  ZiweiSummaryAnalysisPanels,
  ZiweiSummaryOverview,
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
    tfColorStyle,
    tfOutlineStyle,
    selectPalace,
    togglePalaceBookmark,
    shiftDay,
    shiftHour,
    returnChart: () => {
      activeTab.value = 'chart'
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

      <!-- 算法设置折叠区 -->
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

    <!-- 结果区 -->
    <template v-if="result">
      <ZiweiResultHeader
        :result="result"
        :ju-colors="JU_COLORS"
        :info-bar-actions-bindings="infoBarActionsBindings"
        :tool-panels-bindings="toolPanelsBindings"
      />

       <ZiweiResultOverlays v-bind="resultOverlaysBindings" />

      <ZiweiResultIntro
        :summary="result.summary ?? null"
        :active-tab="activeTab"
        :has-liunian="Boolean(result.liunian)"
        :has-liuyue="Boolean(result.liuyue?.length)"
        :patterns-count="result.patterns?.length ?? 0"
        :has-flying="Boolean(result.flying)"
        :has-forecast="Boolean(result.forecast)"
        @update:active-tab="activeTab = $event"
      />

      <!-- Tab: 命盘宫位 -->
      <section v-if="activeTab === 'chart'" class="tab-panel chart-tab-panel">
        <ZiweiChartSection v-bind="chartSectionBindings" />
      </section>

      <!-- Tab: 摘要 -->
      <section v-if="activeTab === 'summary'" class="tab-panel">
        <div class="summary-full card">
          <h3 class="section-title">命盘综述</h3>
          <ZiweiSummaryOverview
            v-bind="summaryOverviewBindings"
          />
          
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
          <ZiweiSummaryAnalysisPanels
            v-bind="summaryAnalysisBindings"
            @select-palace="selectPalaceByIndex"
          />
        </div>
      </section>

      <!-- Tab: 逐宫解读 -->
      <section v-if="activeTab === 'palaces'" class="tab-panel">
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
      </section>

      <!-- Tab: 大运 -->
      <section v-if="activeTab === 'dayun'" class="tab-panel">
        <ZiweiDayunTab
          :dayun="result.dayun"
          :current-year="currentYear"
          :dayun-stats="dayunStats"
          :dayun-progress="dayunProgress"
          @locate-current="scrollToCurrentDayun"
        />
      </section>

      <!-- Tab: 流年 -->
      <section v-if="activeTab === 'liunian'" class="tab-panel">
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
      </section>

      <!-- Tab: 流月 -->
      <section v-if="activeTab === 'liuyue'" class="tab-panel">
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
      </section>

      <!-- Tab: 格局 -->
      <section v-if="activeTab === 'patterns'" class="tab-panel">
        <ZiweiPatternsTab :patterns="result.patterns || []" />
      </section>

      <!-- Tab: 飞星 -->
      <section v-if="activeTab === 'flying' && result.flying" class="tab-panel">
        <ZiweiFlyingTab :flying="result.flying" />
      </section>

      <!-- Tab: 运势预测 -->
      <section v-if="activeTab === 'forecast' && result.forecast" class="tab-panel">
        <ZiweiForecastTab
          :forecast="result.forecast"
          :forecast-stats="forecastStats"
          :forecast-monthly-overview="forecastMonthlyOverview"
          :forecast-risk-months="forecastRiskMonths"
          :forecast-score-color="forecastScoreColor"
        />
      </section>

      <!-- Tab: 建议 -->
      <section v-if="activeTab === 'suggest'" class="tab-panel">
        <ZiweiSuggestTab
          :remedies="result.remedies || []"
          :life-suggestions="result.life_suggestions || []"
        />
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

<style scoped>
.wrap.ziwei-view {
  padding-bottom: var(--sp-8);
  flex: 1 1 auto;
  min-height: 0 !important;
  height: 100% !important;
  width: 100% !important;
  overflow-y: auto !important;
  display: flex;
  flex-direction: column;
  max-width: none !important;
}
.page-title { font-size: var(--fs-2xl); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); font-family: var(--font-cn); }

/* 表单折叠控制栏 */
.form-toggle-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.btn-toggle-form {
  padding: 5px 14px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.btn-toggle-form:hover { border-color: var(--accent); color: var(--accent); }
.current-params { font-size: var(--fs-sm); color: var(--text-3); }

.chart-tab-panel {
  position: relative;
}

/* 卡片 */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-5); box-shadow: var(--shadow); margin-bottom: var(--sp-5); }

/* 表单 */
.form-grid { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-4); }
.form-row { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.form-row > label:first-child { width: 60px; font-size: var(--fs-md); color: var(--text-2); flex-shrink: 0; }
.form-row > label[style] { font-size: var(--fs-md); color: var(--text-2); }
.form-row input[type="number"] { padding: 7px 10px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); }
.form-row input:focus { outline: none; border-color: var(--accent); }
.radio-opt { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: var(--fs-md); }
.hint { font-size: var(--fs-xs); color: var(--text-3); }

.form-actions { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }

.btn-primary { padding: 9px 22px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; transition: background var(--dur-fast); }
.btn-primary:hover { background: var(--accent-dark); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-sec { padding: 9px 18px; background: var(--surface); color: var(--text-2); border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; transition: border-color var(--dur-fast); }
.btn-sec:hover { border-color: var(--accent); color: var(--accent); }
.btn-sec:disabled { opacity: .5; cursor: not-allowed; }
.error-msg { color: var(--danger-dark); font-size: var(--fs-sm); }

/* 骨架屏 */
.skeleton-wrap { padding: var(--sp-5); }
.skel-line { height: 16px; background: var(--border); border-radius: 4px; margin-bottom: var(--sp-3); animation: shimmer 1.2s infinite; }
.skel-box { background: var(--border); border-radius: var(--radius-sm); margin-top: var(--sp-4); animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

.highlight-input {
  animation: highlight-pulse 0.5s ease-in-out 3;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.3) !important;
}
@keyframes highlight-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(217, 119, 6, 0.15); }
}

/* 宫位详情 */

/* 格局 */
.patterns-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.pattern-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-2);
}
.pattern-stat { font-size: var(--fs-sm); color: var(--text-2); }
.pattern-stat b { font-weight: 700; }
.pattern-stat.high b { color: #dc2626; }
.pattern-stat.med b { color: #d97706; }
.pattern-stat.low b { color: #64748b; }
.pattern-item { padding: var(--sp-4); border-radius: var(--radius-sm); border-left: 4px solid var(--border-md); background: var(--surface-2); }
.pattern-item.level-high { border-left-color: #dc2626; }
.pattern-item.level-med  { border-left-color: #d97706; }
.pattern-item.level-low  { border-left-color: #64748b; }
.pattern-header { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-2); }
.pattern-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.pattern-level { font-size: var(--fs-xs); padding: 1px 8px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border-md); color: var(--text-2); }
.pattern-desc { font-size: var(--fs-sm); color: var(--text); line-height: 1.6; }
.pattern-meta { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-top: var(--sp-2); }
.pattern-palaces, .pattern-stars { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.meta-label { font-size: 10px; color: var(--text-2); }
.meta-tag { font-size: 10px; padding: 1px 6px; border-radius: 8px; }
.palace-tag { background: rgba(124, 58, 237, 0.1); color: #7c3aed; }
.star-tag { background: rgba(217, 119, 6, 0.1); color: #d97706; }
.pattern-source { font-size: var(--fs-xs); color: var(--text-2); margin-top: 4px; }

/* 建议 */
.section-block { margin-bottom: var(--sp-6); }
.section-title { font-size: var(--fs-lg); font-weight: 600; margin-bottom: var(--sp-4); color: var(--text); }
.remedies-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.remedy-item { display: flex; flex-direction: column; gap: var(--sp-2); padding: var(--sp-3); background: var(--surface-2); border-radius: var(--radius-sm); }
.remedy-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); }
.remedy-priority { font-size: var(--fs-xs); padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.remedy-priority.priority-1 { background: #dc2626; color: #fff; }
.remedy-priority.priority-2 { background: #f59e0b; color: #fff; }
.remedy-priority.priority-3 { background: #3b82f6; color: #fff; }
.remedy-priority.priority-4, .remedy-priority.priority-5 { background: #6b7280; color: #fff; }
.remedy-cat { font-size: var(--fs-xs); padding: 2px 8px; background: var(--accent); color: #fff; border-radius: 10px; font-weight: 600; flex-shrink: 0; }
.remedy-name { font-weight: 600; color: var(--text); }
.remedy-scope { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.remedy-actions { display: flex; flex-direction: column; gap: 2px; padding-left: var(--sp-3); }
.remedy-step { font-size: var(--fs-sm); color: var(--text-2); }
.remedy-reason { font-size: var(--fs-sm); color: var(--text-3); font-style: italic; }
.suggest-overview {
  padding: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.sov-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
.sov-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.sov-num { font-size: var(--fs-xl); font-weight: 700; color: var(--text); }
.sov-label { font-size: var(--fs-xs); color: var(--text-2); }
.sov-remedy .sov-num { color: #92400e; }
.sov-p1 .sov-num { color: #991b1b; }
.sov-filter { display: flex; flex-wrap: wrap; gap: 6px; }
.sov-cat-btn {
  font-size: var(--fs-xs);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.sov-cat-btn.active,
.sov-cat-btn:hover {
  border-color: var(--accent);
  background: rgba(217,119,6,.10);
  color: #78350f;
}
.suggest-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.suggest-stat { font-size: var(--fs-sm); color: var(--text-2); }
.suggest-stat b { font-weight: 700; color: var(--accent); }

/* ── 流年Tab增强样式 ────────────────────── */
.liunian-summary-card {
  margin-bottom: var(--sp-4);
}
.liunian-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}
.liunian-main {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
}
.liunian-gz {
  font-size: var(--fs-2xl);
  font-weight: 800;
  font-family: var(--font-cn);
  color: var(--accent);
}
.liunian-year { font-size: var(--fs-md); color: var(--text-2); }
.liunian-cur-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: #dc2626;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
}
.liunian-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}
.liunian-meta-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.liunian-meta-item b { color: var(--text); font-weight: 600; }

.liunian-attrs {
  display: flex;
  gap: var(--sp-4);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.liunian-insights {
  margin-top: var(--sp-3);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.liunian-insight-tag {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 3px 8px;
}
.liunian-forecast-link {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
}
.lfl-hint { font-size: var(--fs-sm); color: #92400e; margin: 0; }
.lfl-score { font-size: var(--fs-sm); font-weight: 600; color: #78350f; }
.lfl-score span { font-size: var(--fs-lg); font-weight: 800; }


/* ══════════════════════════════════════════════════════════════════
   过渡动画
   ══════════════════════════════════════════════════════════════════ */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.muted { color: var(--text-3); font-size: var(--fs-sm); }

/* 结果页脚版本信息 */
.result-footer {
  display: flex;
  justify-content: center;
  gap: var(--sp-4);
  padding: var(--sp-4) 0;
  margin-top: var(--sp-6);
  border-top: 1px solid var(--border);
  font-size: var(--fs-xs);
  color: var(--text-3);
}
.ver-item { opacity: 0.7; }
.ver-item::before { content: "•"; margin-right: 4px; }
.ver-item:first-child::before { content: ""; margin-right: 0; }

/* 高亮闪烁动画 */
@keyframes highlight-blink {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  25%, 75% { box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.2); }
}
.highlight-blink {
  animation: highlight-blink 0.5s ease-in-out 3;
}



/* ══════════════════════════════════════════════════════════════════
   四化追踪
   ══════════════════════════════════════════════════════════════════ */
/* ══════════════════════════════════════════════════════════════════
   分享面板
   ══════════════════════════════════════════════════════════════════ */


.ops-panel-zw {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  width: 420px;
  max-height: 72vh;
  display: flex;
  flex-direction: column;
  margin-top: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.ozp-exp-variants {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

/* ══════════════════════════════════════════════════════════════════
   打印样式优化
   ══════════════════════════════════════════════════════════════════ */
@media print {
  .no-print { display: none !important; }
  .form-card { display: none !important; }
  .tabs { display: none !important; }
  .palace-grid { break-inside: avoid; }
  
  /* 页面设置 */
  @page {
    size: A4 portrait;
    margin: 15mm;
  }
  
  /* 隐藏不必要的元素 */
  .chart-mode-bar,
  .info-bar button,
  .palace-detail,
  .hotkey-panel,
  .brightness-legend,
  .star-search-modal,
  .history-panel,
  .star-tooltip { display: none !important; }
  
  /* 基础样式调整 */
  body {
    font-size: 11pt;
    color: #000 !important;
    background: #fff !important;
  }
  
  .ziwei-page {
    padding: 0;
    max-width: 100%;
  }
  
  .card {
    box-shadow: none !important;
    border: 1px solid #ccc;
  }
  
  /* 命盘网格打印优化 */
  .palace-grid-pro {
    border: 2px solid #333;
  }
  
  .pc-center {
    background: #fff !important;
    border-color: #333;
  }
  
  /* 宫位名称 */
  .pc-pname {
    font-size: 11pt;
    font-weight: bold;
    color: #000;
  }
  
  /* 干支 */
  .pc-gzhi {
    font-size: 9pt;
    color: #333;
  }
  
  /* 主星 */
  .pc-sn {
    font-size: 10pt;
    font-weight: bold;
    color: #000;
  }
  
  /* 亮度 */
  .pc-sbr {
    font-size: 8pt;
    color: #666;
  }
  
  /* 四化标签 */
  .pc-tf {
    font-size: 8pt !important;
    padding: 1px 3px !important;
    border: 1px solid #333;
  }
  
  /* 辅星 */
  .pc-aux {
    font-size: 8pt;
    color: #666;
  }
  
  /* 大限年龄 */
  .pc-da {
    font-size: 8pt;
    color: #333;
  }
  
  /* 长生 */
  .pc-cs {
    font-size: 8pt;
  }
  
  /* 中宫 */
  .pc-cj {
    font-size: 14pt;
    font-weight: bold;
  }
  
  .pc-cb, .pc-cl {
    font-size: 9pt;
    color: #333;
  }
  
  /* 方位 */
  .compass-side, .compass-n, .compass-s {
    color: #666;
    font-size: 9pt;
  }
  
  /* 分页控制 */
  .tab-panel {
    page-break-inside: avoid;
  }
  
  h3.section-title {
    page-break-after: avoid;
  }
  
  /* 友好的链接处理 */
  a { color: #000; text-decoration: none; }
}

@media (max-width: 600px) {
  .pc-center { }
  .pc-cj { font-size: var(--fs-lg); }
  .compass-side, .compass-n, .compass-s { font-size: 9px; width: 18px; }
}


/* ── 流年 tab ───────────────────────────── */
.liunian-wrap { padding: var(--sp-5); background: var(--surface-2); border-radius: var(--radius-sm); }
.liunian-head { display: flex; align-items: baseline; gap: var(--sp-3); margin-bottom: var(--sp-4); flex-wrap: wrap; }
.liunian-gz { font-size: var(--fs-2xl); font-weight: 800; font-family: var(--font-cn); color: var(--accent); }
.liunian-year { font-size: var(--fs-sm); color: var(--text-3); }
.liunian-cur-badge {
  background: #7c3aed;
  color: #fff;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.liunian-lp { font-size: var(--fs-sm); color: var(--text-2); border: 1px solid var(--border-md); border-radius: 10px; padding: 1px 8px; }
.liunian-sihua-wrap { }
.sec-label { font-size: var(--fs-sm); color: var(--text-3); margin-bottom: var(--sp-3); font-weight: 500; }
.liunian-sihua { display: flex; flex-wrap: wrap; gap: var(--sp-3); }
.sihua-row { display: flex; align-items: center; gap: 6px; padding: var(--sp-2) var(--sp-4); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); min-width: 90px; }
.sihua-star-name { font-size: var(--fs-md); font-weight: 700; font-family: var(--font-cn); }
.sihua-tf-badge { font-size: var(--fs-sm) !important; padding: 2px 7px !important; }


/* ═══════════════════════════════════════════════════════════════════
   C-1: 盘面类型切换按钮组样式
   ═══════════════════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════════════════
   C-7: 底部时间轴样式
   ═══════════════════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════════════════
   新增：摘要Tab样式
   ═══════════════════════════════════════════════════════════════════ */
.summary-full { padding: var(--sp-5); }
/* ═══════════════════════════════════════════════════════════════════
   命盘批注/笔记功能样式
   ═══════════════════════════════════════════════════════════════════ */


/* ═══════════════════════════════════════════════════════════════════
   运势日历样式
   ═══════════════════════════════════════════════════════════════════ */


.calendar-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 360px;
  padding: 12px;
  max-height: 60vh;
  overflow-y: auto;
}
.cal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.cal-nav {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 12px;
}
.cal-nav:hover { border-color: var(--accent); color: var(--accent); }
.cal-title {
  flex: 1;
  text-align: center;
  font-weight: 600;
  color: var(--text);
}
.cal-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}
.cal-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: default;
}
.cal-empty { background: transparent; }
.cal-day-num { font-weight: 600; }
.cal-day-fortune { font-size: 9px; margin-top: 2px; }

.fortune-great { background: #dcfce7; color: #166534; }
.fortune-good { background: #d1fae5; color: #047857; }
.fortune-normal { background: #f3f4f6; color: #6b7280; }
.fortune-bad { background: #fee2e2; color: #b91c1c; }
.fortune-terrible { background: #fecaca; color: #991b1b; }

.cal-legend {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.cal-legend span {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 8px;
}

/* ═══════════════════════════════════════════════════════════════════
   命盘对比样式
   ═══════════════════════════════════════════════════════════════════ */


.compare-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 340px;
  overflow: hidden;
  max-height: 60vh;
  overflow-y: auto;
}
.cmp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #f97316;
}
.cmp-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.cmp-content { padding: 14px; }
.cmp-hint {
  font-size: var(--fs-sm);
  color: var(--text-2);
  margin: 0 0 12px;
}
.cmp-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.cmp-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.cmp-row label {
  font-size: var(--fs-sm);
  color: var(--text-2);
  min-width: 20px;
}
.cmp-row input, .cmp-row select {
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  width: 60px;
}
.cmp-row select { width: 52px; }
.cmp-btns {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}
.cmp-set {
  flex: 1;
  padding: 8px;
  background: #f97316;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
  font-weight: 500;
}
.cmp-set:hover { background: #ea580c; }
.cmp-clear {
  padding: 8px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}
.cmp-status {
  margin-top: 12px;
  padding: 8px 10px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  color: #c2410c;
}

/* ═══════════════════════════════════════════════════════════════════
   已收藏宫位面板样式
   ═══════════════════════════════════════════════════════════════════ */


.bookmarks-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 320px;
  max-height: 360px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}
.bkm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #d97706;
}
.bkm-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}
.bkm-content {
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}
.bkm-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bkm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.bkm-item:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}
.bkm-palace-name {
  font-weight: 600;
  color: var(--text);
  min-width: 40px;
}
.bkm-palace-gz {
  font-size: 11px;
  color: var(--text-3);
  font-family: var(--font-mono);
}
.bkm-palace-stars {
  flex: 1;
  font-size: 11px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bkm-remove {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--text-3);
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.bkm-remove:hover {
  background: var(--danger);
  color: #fff;
}
.bkm-empty {
  text-align: center;
  color: var(--text-3);
  font-size: var(--fs-sm);
  padding: 30px 10px;
}


/* ═══════════════════════════════════════════════════════════════════
   命盘统计汇总卡片样式
   ═══════════════════════════════════════════════════════════════════ */
/* ── 可读性修正（浅底文字对比增强）──────────────────── */
.sqf-label,
.frt-label,
.fhm-period,
.forecast-stat-main .fs-label,
.dt-age,
.dt-node.dt-past .dt-label,
.liunian-year,
.sec-label,
.fy-period,
.fm-period,
.muted,
.dsc-prog-meta,
.dsc-prog-labels,
.dayun-year,
.csc-label {
  color: var(--text-2);
}

.cqi-label,
.cqi-sub {
  color: var(--text-2);
}

/* ── 可读性修正（第二层：表单/详情/流月常见灰字）────────────── */
.current-params,
.hint,
.algo-label,
.detail-branch,
.close-btn,
.star-br,
.la-label,
.detail-sec-label,
.boshi-tag,
.pi-br,
.pi-explanation strong {
  color: var(--text-2);
}

.lyq-btn.lyq-cur {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #991b1b;
  font-weight: 700;
}
</style>
