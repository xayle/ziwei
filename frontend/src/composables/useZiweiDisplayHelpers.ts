import { computed, type Ref } from 'vue'
import type { DayunItem, PalaceResponse, ZiweiResponse } from '@/api/ziwei'

type UseZiweiDisplayHelpersOptions = {
  result: Ref<ZiweiResponse | null>
  selectedDaxianIdx: Ref<number>
  currentDayun: Ref<DayunItem | null>
  getPalaceTransforms: (palace: PalaceResponse) => string[]
}

export function useZiweiDisplayHelpers(options: UseZiweiDisplayHelpersOptions) {
  function palaceHasTransform(palace: PalaceResponse, transform: string): boolean {
    const allTransforms = options.getPalaceTransforms(palace)
    return allTransforms.includes(transform)
  }

  function getPalaceQuickInfo(palace: PalaceResponse): string {
    const mainNames = palace.main_stars?.map((s) => s.name).join('、') || '无主星'
    const transforms = options.getPalaceTransforms(palace)
    const tfStr = transforms.length ? `｜${transforms.join(' ')}` : ''
    return `${palace.name}：${mainNames}${tfStr}`
  }

  function forecastScoreColor(score: number): string {
    if (score >= 80) return '#15803d'
    if (score >= 60) return '#d97706'
    return '#dc2626'
  }

  function getMonthForecast(month: number) {
    if (!options.result.value?.forecast?.monthly) return null
    const monthNames = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']
    const monthName = monthNames[month - 1]
    return options.result.value.forecast.monthly.find((m) => {
      return m.period?.includes(monthName + '月')
    }) ?? options.result.value.forecast.monthly[month - 1] ?? null
  }

  const liuyueRows = computed(() => {
    const months = options.result.value?.liuyue ?? []
    return months.map((month) => ({
      month,
      forecast: getMonthForecast(month.month),
    }))
  })

  const liuyueSummary = computed(() => {
    const rows = liuyueRows.value
    const withForecast = rows.filter((row) => row.forecast?.score != null)
    const scores = withForecast.map((row) => Number(row.forecast?.score || 0)).filter((score) => score > 0)
    const avg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0
    const riskMonths = withForecast
      .filter((row) => Number(row.forecast?.score || 0) < 50)
      .map((row) => row.month.month_name)
      .slice(0, 3)

    return {
      total: rows.length,
      withSihua: rows.filter((row) => Object.keys(row.month.sihua || {}).length > 0).length,
      withForecast: withForecast.length,
      avg,
      riskMonths,
    }
  })

  const daxianSihuaMap = computed(() => {
    if (!options.result.value?.dayun?.items) return {} as Record<string, string>
    const activeDayun = options.selectedDaxianIdx.value >= 0
      ? options.result.value.dayun.items[options.selectedDaxianIdx.value]
      : options.currentDayun.value
    return activeDayun?.sihua || {}
  })

  const liunianSihuaMap = computed(() => {
    if (!options.result.value?.liunian) return {} as Record<string, string>
    return options.result.value.liunian.sihua || {}
  })

  const liunianSihuaWithPalace = computed(() => {
    const sihua = options.result.value?.liunian?.sihua || {}
    const palaces = options.result.value?.palaces || []
    return Object.entries(sihua).map(([star, transform]) => {
      const palace = palaces.find((p) =>
        p.main_stars.some((s) => s.name === star) || p.aux_stars.some(s => s.name === star),
      )
      return { star, transform, palaceName: palace?.name || '' }
    })
  })

  return {
    palaceHasTransform,
    getPalaceQuickInfo,
    forecastScoreColor,
    getMonthForecast,
    liuyueRows,
    liuyueSummary,
    daxianSihuaMap,
    liunianSihuaMap,
    liunianSihuaWithPalace,
  }
}
