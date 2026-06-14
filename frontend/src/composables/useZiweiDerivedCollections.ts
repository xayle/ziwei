import { computed } from 'vue'
import type { PalaceResponse, StarInfo, ZiweiResponse } from '@/api/ziwei'

type StarLike = string | Partial<StarInfo>

type SihuaPath = {
  type: '禄' | '权' | '科' | '忌'
  star: string
  source: string
  target?: string
  sourcePalaceIdx: number
}

type UseZiweiDerivedCollectionsOptions = {
  getResult: () => ZiweiResponse | null
  getAuxStars: (palace: PalaceResponse) => StarLike[]
  getStarTransforms: (star: StarLike) => string[]
  getStarName: (star: StarLike) => string
}

export function useZiweiDerivedCollections(options: UseZiweiDerivedCollectionsOptions) {
  const forecastStats = computed(() => {
    const result = options.getResult()
    if (!result?.forecast?.monthly?.length) {
      return {
        good: 0,
        mid: 0,
        low: 0,
        avg: 0,
        best: null as { period: string; score: number } | null,
        worst: null as { period: string; score: number } | null,
      }
    }

    let good = 0
    let mid = 0
    let low = 0
    let sum = 0
    let count = 0
    let best = { period: '', score: 0 }
    let worst = { period: '', score: 100 }

    result.forecast.monthly.forEach((item) => {
      if (item.score == null) return
      if (item.score >= 80) good++
      else if (item.score >= 50) mid++
      else low++
      sum += item.score
      count++
      if (item.score > best.score) best = { period: item.period, score: item.score }
      if (item.score < worst.score) worst = { period: item.period, score: item.score }
    })

    return {
      good,
      mid,
      low,
      avg: count > 0 ? Math.round(sum / count) : 0,
      best: best.period ? best : null,
      worst: worst.period ? worst : null,
    }
  })

  const forecastMonthlyOverview = computed(() => {
    const monthly = options.getResult()?.forecast?.monthly ?? []
    return monthly.map((item, index) => {
      const score = Number(item.score ?? 0)
      const scoreClamped = Math.max(0, Math.min(100, score))
      let level: 'good' | 'mid' | 'low' = 'low'
      if (scoreClamped >= 80) level = 'good'
      else if (scoreClamped >= 50) level = 'mid'
      return {
        index,
        score: scoreClamped,
        level,
        periodShort: (item.period || '').replace(/\(.+?\)/g, '').replace(/\s+/g, ''),
      }
    })
  })

  const forecastRiskMonths = computed(() =>
    forecastMonthlyOverview.value
      .filter((item) => item.score > 0 && item.score < 50)
      .map((item) => item.periodShort)
      .slice(0, 4),
  )

  const sihuaPathList = computed((): SihuaPath[] => {
    const palaces = options.getResult()?.palaces
    if (!palaces) return []

    const paths: SihuaPath[] = []
    palaces.forEach((palace, palaceIdx) => {
      palace.main_stars?.forEach((star) => {
        star.transforms?.forEach((transform) => {
          paths.push({
            // transforms[] 值为 "化禄" 等，SihuaPath.type 为 '禄'/'权'，需去掉前缀
            type: transform.replace('化', '') as SihuaPath['type'],
            star: star.name,
            source: palace.name,
            sourcePalaceIdx: palaceIdx,
          })
        })
      })

      options.getAuxStars(palace).forEach((star) => {
        options.getStarTransforms(star).forEach((transform) => {
          paths.push({
            type: transform.replace('化', '') as SihuaPath['type'],
            star: options.getStarName(star),
            source: palace.name,
            sourcePalaceIdx: palaceIdx,
          })
        })
      })
    })

    return paths
  })

  const sihuaByType = computed(() => {
    const groups: Record<string, SihuaPath[]> = { '禄': [], '权': [], '科': [], '忌': [] }
    sihuaPathList.value.forEach((path) => {
      if (groups[path.type]) groups[path.type].push(path)
    })
    return groups
  })

  return {
    forecastStats,
    forecastMonthlyOverview,
    forecastRiskMonths,
    sihuaPathList,
    sihuaByType,
  }
}
