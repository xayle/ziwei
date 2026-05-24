import { computed, ref, type Ref } from 'vue'
import type { Router } from 'vue-router'
import { createReview } from '@/api/admin'
import type { ZiweiResponse } from '@/api/ziwei'
import { buildPatternSummaryText } from '@/utils/ziweiNarrative'
import { saveZiweiLlmDraftContext } from '@/utils/ziweiLlmDraftContext'
import {
  clearZiweiCaseWorkflowContext,
  saveZiweiCaseWorkflowContext,
  type ZiweiCaseWorkflowContext,
  type ZiweiCaseWorkflowInput,
} from '@/utils/ziweiCaseWorkflowContext'
import {
  buildZiweiCaseName,
  buildZiweiSimilarityHash,
  buildZiweiWorkflowContext,
  buildZiweiWorkflowSummary,
  saveZiweiChartToLibrary,
} from '@/utils/ziweiCaseLibrary'

type UseZiweiWorkflowActionsOptions = {
  router: Router
  result: Ref<ZiweiResponse | null>
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  minute: Ref<number>
  gender: Ref<'男' | '女'>
  longitude: Ref<number | undefined>
  liunianYear: Ref<number | undefined>
  initCity: Ref<string>
  getProfileCityName: () => string | null | undefined
  getProfileLongitude: () => number | null | undefined
  parseApiError: (error: unknown, fallback: string) => string
}

export function useZiweiWorkflowActions(options: UseZiweiWorkflowActionsOptions) {
  const savedCaseId = ref('')
  const savedCaseName = ref('')
  const currentSnapshotId = ref('')
  const isSavingCase = ref(false)
  const reviewSubmitting = ref(false)

  const canSaveCurrentChart = computed(() => Boolean(options.result.value) && !isSavingCase.value)
  const glossarySuggestedTerms = computed(() => {
    if (!options.result.value) return [] as string[]

    const terms = [
      ...options.result.value.patterns.map((item) => item.name),
      options.result.value.life_ruler_star,
      options.result.value.body_ruler_star,
      ...options.result.value.palaces.flatMap((palace) => palace.main_stars.map((star) => star.name)),
    ]

    return Array.from(new Set(terms.filter((item): item is string => Boolean(item && item.trim())))).slice(0, 8)
  })

  function buildCurrentWorkflowInput(): ZiweiCaseWorkflowInput {
    return {
      year: options.year.value,
      month: options.month.value,
      day: options.day.value,
      hour: options.hour.value,
      minute: options.minute.value,
      gender: options.gender.value,
      longitude: options.longitude.value ?? null,
      liunian_year: options.liunianYear.value ?? null,
      template_version: options.result.value?.template_version ?? 'standard',
      city_name: options.initCity.value || options.getProfileCityName() || null,
    }
  }

  function buildSimilarityHash(): string {
    return buildZiweiSimilarityHash(buildCurrentWorkflowInput(), options.result.value)
  }

  function clearSavedCaseState() {
    savedCaseId.value = ''
    savedCaseName.value = ''
    currentSnapshotId.value = ''
  }

  function applySavedCaseState(context?: Pick<ZiweiCaseWorkflowContext, 'savedCaseId' | 'savedCaseName' | 'currentSnapshotId'> | null) {
    savedCaseId.value = context?.savedCaseId || ''
    savedCaseName.value = context?.savedCaseName || ''
    currentSnapshotId.value = context?.currentSnapshotId || ''
  }

  async function saveCurrentChart(silent = false) {
    if (!options.result.value || isSavingCase.value) return

    isSavingCase.value = true
    try {
      const caseInput = buildCurrentWorkflowInput()
      const saved = await saveZiweiChartToLibrary({
        input: caseInput,
        chart: options.result.value,
        existingCaseId: savedCaseId.value,
        existingCaseName: savedCaseName.value,
        cityName: options.getProfileCityName() || options.initCity.value || null,
        longitudeFallback: options.getProfileLongitude() ?? 120,
        sourceLabel: 'spa-ziwei',
      })

      savedCaseId.value = saved.caseId
      savedCaseName.value = saved.caseName
      currentSnapshotId.value = saved.snapshotId

      if (!silent) {
        alert(`已保存到案例库：${saved.caseName || buildZiweiCaseName(caseInput, options.result.value)}`)
      }
    } catch (error: unknown) {
      const message = options.parseApiError(error, '保存命盘失败，请稍后重试')
      if (!silent) alert(message)
    } finally {
      isSavingCase.value = false
    }
  }

  function toggleReviewPanel() {
    options.router.push({
      path: '/admin',
      query: {
        tab: 'reviews',
        from: 'ziwei',
        context: 'review',
      },
    })
  }

  async function submitCurrentReview() {
    if (!options.result.value || reviewSubmitting.value) return

    reviewSubmitting.value = true
    try {
      const created = await createReview({
        case_id: savedCaseId.value || undefined,
        chart_hash: buildSimilarityHash(),
        chart_type: 'ziwei',
      })
      options.router.push({
        path: '/admin',
        query: {
          tab: 'reviews',
          from: 'ziwei',
          context: 'review-submit',
          createdReviewId: String(created.id),
        },
      })
    } catch (error: unknown) {
      alert(options.parseApiError(error, '提交审核失败，请稍后重试'))
    } finally {
      reviewSubmitting.value = false
    }
  }

  function openCaseWorkflow(targetTab: 'cases' | 'snapshots' | 'similar') {
    if (options.result.value) {
      saveZiweiCaseWorkflowContext(buildZiweiWorkflowContext({
        input: buildCurrentWorkflowInput(),
        chart: options.result.value,
        savedCaseId: savedCaseId.value,
        savedCaseName: savedCaseName.value,
        currentSnapshotId: currentSnapshotId.value,
      }))
    } else {
      clearZiweiCaseWorkflowContext()
    }

    options.router.push({
      path: '/ziwei/cases',
      query: {
        from: 'ziwei',
        tab: targetTab,
      },
    })
  }

  function toggleLlmPanel() {
    const chart = options.result.value
    if (chart) {
      saveZiweiLlmDraftContext({
        chart_hash: buildSimilarityHash(),
        life_palace_gz: chart.life_palace_gz,
        wuxing_ju_name: chart.wuxing_ju_name,
        pattern_summary: buildPatternSummaryText(chart),
        birth_info_summary: `${chart.birth_solar} ${chart.gender}`,
        summary: buildZiweiWorkflowSummary(chart, buildCurrentWorkflowInput()),
        createdAt: new Date().toISOString(),
      })
    }
    options.router.push({
      path: '/llm/drafts',
      query: { from: 'ziwei' },
    })
  }

  function toggleOpsPanel() {
    options.router.push({
      path: '/admin',
      query: {
        tab: 'experiments',
        from: 'ziwei',
        context: 'ops',
      },
    })
  }

  function toggleBatchPanel() {
    options.router.push({
      path: '/ziwei/batch',
      query: { from: 'ziwei' },
    })
  }

  function toggleGlossaryPanel() {
    options.router.push({
      path: '/glossary',
      query: glossarySuggestedTerms.value.length
        ? { from: 'ziwei', suggested: glossarySuggestedTerms.value }
        : { from: 'ziwei' },
    })
  }

  function toggleMultiCompatPanel() {
    options.router.push({
      path: '/compat/team',
      query: {
        from: 'ziwei',
        base_year: String(options.year.value),
        base_month: String(options.month.value),
        base_day: String(options.day.value),
        base_hour: String(options.hour.value),
        base_minute: String(options.minute.value),
        base_gender: options.gender.value,
        base_longitude: String(options.longitude.value),
      },
    })
  }

  function toggleFengshuiPanel() {
    options.router.push({
      path: '/fengshui',
      query: {
        birth_year: String(options.year.value),
        gender: options.gender.value,
      },
    })
  }

  return {
    savedCaseId,
    savedCaseName,
    currentSnapshotId,
    isSavingCase,
    canSaveCurrentChart,
    reviewSubmitting,
    glossarySuggestedTerms,
    buildCurrentWorkflowInput,
    clearSavedCaseState,
    applySavedCaseState,
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
  }
}