import { computed, type Ref } from 'vue'
import type { PalaceResponse, StarInfo, ZiweiResponse } from '@/api/ziwei'
import { useZiweiChartMetrics } from '@/composables/useZiweiChartMetrics'
import { useZiweiSummaryInsights } from '@/composables/useZiweiSummaryInsights'

type StarLike = string | Partial<StarInfo>

type ForecastStatsLike = {
  good: number
  mid: number
  low: number
  avg: number
  best: { period: string; score: number } | null
  worst: { period: string; score: number } | null
}

type SihuaPathLike = {
  type: string
  star: string
  source: string
  sourcePalaceIdx: number
}

type UseZiweiSummarySectionBindingsOptions = {
  result: Ref<ZiweiResponse | null>
  currentDayunGz: Ref<string>
  forecastStats: Ref<ForecastStatsLike>
  forecastRiskMonths: Ref<string[]>
  sihuaPathList: Ref<SihuaPathLike[]>
  sihuaByType: Ref<Record<string, SihuaPathLike[]>>
  getAuxStars: (palace: PalaceResponse) => StarLike[]
  getStarTransforms: (star: StarLike) => string[]
  getStarName: (star: StarLike) => string
  getStarBrightnessValue: (star?: Partial<StarInfo>) => number
  juColors: Record<number | string, string>
}

export function useZiweiSummarySectionBindings(options: UseZiweiSummarySectionBindingsOptions) {
  const {
    lifePalaceMainStars,
    lifePalaceAuxStars,
    starDistribution,
    maxStarsInPalace,
    wuxingDistribution,
    maxWuxingCount,
    detectedCombos,
    chartQuickInsights,
    chartSummaryStats,
  } = useZiweiChartMetrics({
    result: options.result,
    sihuaByType: options.sihuaByType,
    getAuxStars: options.getAuxStars,
    getStarTransforms: options.getStarTransforms,
    getStarName: options.getStarName,
    getStarBrightnessValue: options.getStarBrightnessValue,
  })

  const {
    summaryQuickFacts,
    summaryInsightTags,
    summaryKeyConclusions,
  } = useZiweiSummaryInsights({
    result: options.result,
    currentDayunGz: options.currentDayunGz,
    forecastStats: options.forecastStats,
    forecastRiskMonths: options.forecastRiskMonths,
    detectedCombos,
    sihuaByType: options.sihuaByType,
  })

  const summaryOverviewBindings = computed(() => {
    const result = options.result.value
    return {
      summary: result?.summary ?? null,
      quickFacts: summaryQuickFacts.value,
      insightTags: summaryInsightTags.value,
      keyConclusions: summaryKeyConclusions.value,
      wuxingJu: result?.wuxing_ju ?? '',
      wuxingJuName: result?.wuxing_ju_name ?? '',
      juColors: options.juColors,
      lifePalaceGz: result?.life_palace_gz ?? '',
      bodyPalaceGz: result?.body_palace_gz ?? '',
      lifeRulerStar: result?.life_ruler_star ?? null,
      bodyRulerStar: result?.body_ruler_star ?? null,
      dayunStartText: result?.dayun
        ? (result.dayun.start_age_text || `${result.dayun.start_age}岁`)
        : null,
    }
  })

  const summaryAnalysisBindings = computed(() => {
    const result = options.result.value
    return {
      analysis: result?.analysis ?? null,
      lifePalaceMainStars: lifePalaceMainStars.value,
      lifePalaceAuxStars: lifePalaceAuxStars.value,
      sihuaPathList: options.sihuaPathList.value,
      sihuaByType: options.sihuaByType.value,
      starDistribution: starDistribution.value,
      maxStarsInPalace: maxStarsInPalace.value,
      wuxingDistribution: wuxingDistribution.value,
      maxWuxingCount: maxWuxingCount.value,
      wuxingJu: result?.wuxing_ju ?? '',
      wuxingJuName: result?.wuxing_ju_name ?? null,
      juColors: options.juColors,
      detectedCombos: detectedCombos.value,
    }
  })

  const chartSummarySectionBindings = computed(() => ({
    quickInsights: chartQuickInsights.value,
    summaryStats: chartSummaryStats.value,
  }))

  return {
    chartSummarySectionBindings,
    summaryOverviewBindings,
    summaryAnalysisBindings,
  }
}
