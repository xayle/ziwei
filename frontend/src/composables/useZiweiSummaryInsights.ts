import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

type ForecastPeak = { period: string; score: number } | null

type ForecastStats = {
  good: number
  mid: number
  low: number
  avg: number
  best: ForecastPeak
  worst: ForecastPeak
}

type PatternHighlight = {
  name: string
  cls: string
  level?: string
}

type SihuaLike = {
  source: string
  star: string
}

type SummaryQuickFact = {
  label: string
  value: string
}

type SummaryConclusion = {
  title: string
  content: string
  tag: string
  type: 'good' | 'warn' | 'info'
}

type UseZiweiSummaryInsightsOptions = {
  result: Ref<ZiweiResponse | null>
  currentDayunGz: Ref<string>
  forecastStats: Ref<ForecastStats>
  forecastRiskMonths: Ref<string[]>
  detectedCombos: Ref<unknown[]>
  sihuaByType: Ref<Record<string, SihuaLike[]>>
}

export function useZiweiSummaryInsights(options: UseZiweiSummaryInsightsOptions) {
  function patternClass(level: string) {
    const normalized = level?.toLowerCase() ?? ''
    if (normalized.includes('上') || normalized.includes('大') || normalized.includes('high')) return 'level-high'
    if (normalized.includes('中') || normalized.includes('med')) return 'level-med'
    return 'level-low'
  }

  const patternStats = computed(() => {
    const patterns = options.result.value?.patterns ?? []
    if (!patterns.length) return { high: 0, med: 0, low: 0, total: 0 }

    let high = 0
    let med = 0
    let low = 0
    patterns.forEach((pattern) => {
      const cls = patternClass(pattern.level)
      if (cls === 'level-high') high++
      else if (cls === 'level-med') med++
      else low++
    })

    return { high, med, low, total: patterns.length }
  })

  function patternWeight(level: string): number {
    const cls = patternClass(level)
    if (cls === 'level-high') return 3
    if (cls === 'level-med') return 2
    return 1
  }

  const patternHighlights = computed<PatternHighlight[]>(() => {
    const patterns = options.result.value?.patterns ?? []
    return [...patterns]
      .sort((a, b) => {
        const weightDiff = patternWeight(b.level) - patternWeight(a.level)
        if (weightDiff !== 0) return weightDiff
        const aScore = (a.stars?.length || 0) + (a.palaces?.length || 0)
        const bScore = (b.stars?.length || 0) + (b.palaces?.length || 0)
        return bScore - aScore
      })
      .slice(0, 3)
      .map((pattern) => ({
        name: pattern.name,
        cls: patternClass(pattern.level),
        level: pattern.level,
      }))
  })

  const summaryQuickFacts = computed(() => {
    if (!options.result.value) return [] as SummaryQuickFact[]
    const lunar = options.result.value.lunar
    const facts: SummaryQuickFact[] = [
      { label: '公历', value: options.result.value.birth_solar || '-' },
      {
        label: '农历',
        value: lunar
          ? `${lunar.lunar_year}年${lunar.is_leap_month ? '闰' : ''}${lunar.lunar_month}月${lunar.lunar_day}日`
          : '-',
      },
      { label: '模板', value: options.result.value.template_version || 'standard' },
    ]

    if (options.result.value.true_solar_time) {
      facts.push({ label: '真太阳时', value: options.result.value.true_solar_time })
    }
    if (options.currentDayunGz.value) {
      facts.push({ label: '当前大运', value: options.currentDayunGz.value })
    }
    if (options.result.value.liunian?.year_gz) {
      facts.push({
        label: '当前流年',
        value: `${options.result.value.liunian.year} ${options.result.value.liunian.year_gz}`,
      })
    }
    return facts
  })

  const summaryInsightTags = computed(() => {
    if (!options.result.value) return [] as string[]
    const tags: string[] = []

    if (patternStats.value.high >= 2) {
      tags.push(`格局偏强（上格 ${patternStats.value.high}）`)
    } else if (patternStats.value.total > 0) {
      tags.push(`格局分布：上${patternStats.value.high}/中${patternStats.value.med}/普${patternStats.value.low}`)
    }

    if (options.forecastStats.value.avg >= 80) {
      tags.push(`流月均分较高（${options.forecastStats.value.avg}）`)
    } else if (options.forecastStats.value.avg > 0 && options.forecastStats.value.avg < 60) {
      tags.push(`近期波动偏大（均分 ${options.forecastStats.value.avg}）`)
    }

    if (options.detectedCombos.value.length >= 3) {
      tags.push(`检测到 ${options.detectedCombos.value.length} 组星曜组合`)
    }
    if (options.result.value.life_ruler_star) {
      tags.push(`命主星：${options.result.value.life_ruler_star}`)
    }
    if (options.result.value.body_ruler_star) {
      tags.push(`身主星：${options.result.value.body_ruler_star}`)
    }

    return tags.slice(0, 6)
  })

  const summaryKeyConclusions = computed(() => {
    if (!options.result.value) return [] as SummaryConclusion[]
    const items: SummaryConclusion[] = []

    const top = patternHighlights.value[0]
    if (top) {
      const extra = patternStats.value.total > 1 ? `，共 ${patternStats.value.total} 格局` : ''
      items.push({
        title: '命盘格局',
        content: top.name + extra,
        tag: top.cls === 'level-high' ? '上格' : top.cls === 'level-med' ? '中格' : '普格',
        type: top.cls === 'level-high' ? 'good' : 'info',
      })
    }

    const dyParts: string[] = []
    if (options.currentDayunGz.value) dyParts.push(`大运 ${options.currentDayunGz.value}`)
    if (options.result.value.liunian?.year_gz) dyParts.push(`流年 ${options.result.value.liunian.year_gz}`)
    if (options.forecastStats.value.avg > 0) dyParts.push(`均分 ${options.forecastStats.value.avg}`)
    if (dyParts.length) {
      const avg = options.forecastStats.value.avg
      items.push({
        title: '当前运势',
        content: dyParts.join(' · '),
        tag: avg >= 75 ? '旺' : avg >= 55 ? '平' : avg > 0 ? '弱' : '-',
        type: avg >= 75 ? 'good' : avg > 0 && avg < 55 ? 'warn' : 'info',
      })
    }

    const lifeJi = (options.sihuaByType.value['忌'] ?? []).filter((p) => p.source === '命宫')
    if (lifeJi.length) {
      items.push({
        title: '化忌提示',
        content: `${lifeJi.map((p) => p.star).join('、')} 化忌在命宫`,
        tag: '注意',
        type: 'warn',
      })
    } else if (options.forecastRiskMonths.value.length) {
      items.push({
        title: '重点关注',
        content: `低分月：${options.forecastRiskMonths.value.join('、')}`,
        tag: '提示',
        type: 'warn',
      })
    }

    const rulers = [options.result.value.life_ruler_star, options.result.value.body_ruler_star].filter(Boolean).join(' / ')
    if (rulers) {
      items.push({
        title: '命身主星',
        content: rulers,
        tag: '参考',
        type: 'info',
      })
    }

    return items.slice(0, 4)
  })

  return {
    summaryQuickFacts,
    summaryInsightTags,
    summaryKeyConclusions,
  }
}
