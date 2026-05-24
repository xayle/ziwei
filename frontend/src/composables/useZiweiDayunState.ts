import { computed, type Ref } from 'vue'
import type { DayunItem, ZiweiResponse } from '@/api/ziwei'

type UseZiweiDayunStateOptions = {
  result: Ref<ZiweiResponse | null>
  currentYear: number
}

export function useZiweiDayunState(options: UseZiweiDayunStateOptions) {
  const currentDayun = computed(() => {
    if (!options.result.value?.dayun?.items) return null
    return options.result.value.dayun.items.find(
      (item) => item.start_year <= options.currentYear && (item.start_year + 10) > options.currentYear,
    ) ?? null
  })

  const currentDayunGz = computed(() => {
    if (!options.result.value?.dayun?.items?.length) return ''
    const current = options.result.value.dayun.items.find(
      (item) => item.start_year <= options.currentYear && (item.start_year + 10) > options.currentYear,
    )
    return current?.ganzhi || ''
  })

  const dayunStats = computed(() => {
    const items = options.result.value?.dayun?.items ?? []
    let past = 0
    let current = 0
    let future = 0

    items.forEach((item) => {
      if ((item.start_year + 10) <= options.currentYear) past++
      else if (item.start_year <= options.currentYear) current++
      else future++
    })

    return {
      total: items.length,
      past,
      current,
      future,
      startYear: items[0]?.start_year ?? 0,
      endYear: items.length ? items[items.length - 1].start_year + 9 : 0,
    }
  })

  const dayunProgress = computed(() => {
    const current = currentDayun.value
    if (!current) return null
    const yearsIn = options.currentYear - current.start_year
    const pct = Math.min(100, Math.round((yearsIn / 10) * 100))
    return {
      yearsIn,
      yearsLeft: 10 - yearsIn,
      pct,
      ganzhi: current.ganzhi,
    }
  })

  return {
    currentDayun,
    currentDayunGz,
    dayunStats,
    dayunProgress,
  }
}
