import { computed, type Ref } from 'vue'
import type { PalaceResponse, StarInfo, ZiweiResponse } from '@/api/ziwei'

type StarLike = string | Partial<StarInfo>

type SihuaLike = {
  type: string
  star: string
  source: string
  sourcePalaceIdx: number
}

interface StarDistribution {
  palaceName: string
  palaceIdx: number
  mainCount: number
  auxCount: number
  total: number
  hasLu: boolean
  hasJi: boolean
}

interface WuxingDistribution {
  element: string
  count: number
  color: string
  stars: string[]
}

interface StarCombo {
  name: string
  stars: string[]
  palace: string
  desc: string
  type: 'auspicious' | 'inauspicious' | 'neutral'
}

const WUXING_MAP: Record<string, string> = {
  '紫微': '土', '天机': '木', '太阳': '火', '武曲': '金', '天同': '水',
  '廉贞': '火', '天府': '土', '太阴': '水', '贪狼': '水', '巨门': '水',
  '天相': '水', '天梁': '土', '七杀': '金', '破军': '水',
  '文昌': '金', '文曲': '水', '左辅': '土', '右弼': '水',
  '天魁': '火', '天钺': '火', '禄存': '土', '天马': '火',
  '擎羊': '金', '陀罗': '金', '火星': '火', '铃星': '火',
  '地空': '火', '地劫': '火',
}

const WUXING_COLORS: Record<string, string> = {
  '金': '#d97706', '木': '#16a34a', '水': '#2563eb', '火': '#dc2626', '土': '#78716c',
}

const STAR_COMBOS: Array<{ name: string; stars: string[]; desc: string; type: 'auspicious' | 'inauspicious' | 'neutral' }> = [
  { name: '紫府同宫', stars: ['紫微', '天府'], desc: '帝星与库星同宫，贵气重重', type: 'auspicious' },
  { name: '日月同宫', stars: ['太阳', '太阴'], desc: '日月双辉，阴阳调和', type: 'auspicious' },
  { name: '机月同梁', stars: ['天机', '太阴', '天同', '天梁'], desc: '四星会照，适合文职公职', type: 'auspicious' },
  { name: '府相朝垣', stars: ['天府', '天相'], desc: '双贵会照，官禄亨通', type: 'auspicious' },
  { name: '昌曲夹命', stars: ['文昌', '文曲'], desc: '双文夹命，才华出众', type: 'auspicious' },
  { name: '左右夹拱', stars: ['左辅', '右弼'], desc: '贵人相助，逢凶化吉', type: 'auspicious' },
  { name: '魁钺夹命', stars: ['天魁', '天钺'], desc: '贵人星夹命，遇难呈祥', type: 'auspicious' },
  { name: '禄马交驰', stars: ['禄存', '天马'], desc: '财禄流动，利于经商', type: 'auspicious' },
  { name: '杀破狼格', stars: ['七杀', '破军', '贪狼'], desc: '变动星曜，开创格局', type: 'neutral' },
  { name: '火贪格', stars: ['火星', '贪狼'], desc: '暴发之兆，宜把握时机', type: 'neutral' },
  { name: '铃贪格', stars: ['铃星', '贪狼'], desc: '偏财运佳，宜投机取巧', type: 'neutral' },
  { name: '羊陀夹命', stars: ['擎羊', '陀罗'], desc: '刑克星夹命，多是非', type: 'inauspicious' },
  { name: '火铃夹命', stars: ['火星', '铃星'], desc: '煞星夹命，性急躁', type: 'inauspicious' },
  { name: '空劫夹命', stars: ['地空', '地劫'], desc: '空亡星夹命，损失多', type: 'inauspicious' },
]

type UseZiweiChartMetricsOptions = {
  result: Ref<ZiweiResponse | null>
  sihuaByType: Ref<Record<string, SihuaLike[]>>
  getAuxStars: (palace: PalaceResponse) => StarLike[]
  getStarTransforms: (star: StarLike) => string[]
  getStarName: (star: StarLike) => string
  getStarBrightnessValue: (star?: Partial<StarInfo>) => number
}

export function useZiweiChartMetrics(options: UseZiweiChartMetricsOptions) {
  const lifePalaceMainStars = computed(() => {
    if (!options.result.value?.palaces) return []
    const lifePalace = options.result.value.palaces.find((p) => p.name.includes('命'))
    return lifePalace?.main_stars ?? []
  })

  const lifePalaceAuxStars = computed<string[]>(() => {
    if (!options.result.value?.palaces) return []
    const lifePalace = options.result.value.palaces.find((p) => p.name.includes('命'))
    return (lifePalace?.aux_stars ?? []).map(s => s.name)
  })

  const starDistribution = computed((): StarDistribution[] => {
    if (!options.result.value?.palaces) return []
    return options.result.value.palaces.map((p, idx) => {
      const mainStars = p.main_stars || []
      const auxStars = options.getAuxStars(p)
      const allTransforms = [
        ...mainStars.flatMap((s) => options.getStarTransforms(s)),
        ...auxStars.flatMap((s) => options.getStarTransforms(s)),
      ]
      return {
        palaceName: p.name,
        palaceIdx: idx,
        mainCount: mainStars.length,
        auxCount: auxStars.length,
        total: mainStars.length + auxStars.length,
        hasLu: allTransforms.includes('禄'),
        hasJi: allTransforms.includes('忌'),
      }
    })
  })

  const maxStarsInPalace = computed(() => Math.max(...starDistribution.value.map((d) => d.total), 1))

  const wuxingDistribution = computed((): WuxingDistribution[] => {
    if (!options.result.value?.palaces) return []
    const counts: Record<string, string[]> = { '金': [], '木': [], '水': [], '火': [], '土': [] }

    options.result.value.palaces.forEach((p) => {
      p.main_stars?.forEach((s) => {
        const wx = WUXING_MAP[s.name]
        if (wx && counts[wx]) counts[wx].push(s.name)
      })
    })

    return ['金', '木', '水', '火', '土'].map((el) => ({
      element: el,
      count: counts[el].length,
      color: WUXING_COLORS[el],
      stars: counts[el],
    }))
  })

  const maxWuxingCount = computed(() => Math.max(...wuxingDistribution.value.map((d) => d.count), 1))

  const detectedCombos = computed((): StarCombo[] => {
    if (!options.result.value?.palaces) return []
    const combos: StarCombo[] = []

    options.result.value.palaces.forEach((p) => {
      const allStars = [
        ...(p.main_stars?.map((s) => s.name) || []),
        ...(p.aux_stars?.map(s => s.name) || []),
      ]

      STAR_COMBOS.forEach((combo) => {
        const allPresent = combo.stars.every((s) => allStars.includes(s))
        const presentCount = combo.stars.filter((s) => allStars.includes(s)).length

        if (allPresent || (combo.stars.length >= 3 && presentCount >= 2 && !allPresent && combo.stars.length === presentCount + 1)) {
          if (!combos.find((c) => c.name === combo.name && c.palace === p.name)) {
            combos.push({
              name: combo.name,
              stars: combo.stars.filter((s) => allStars.includes(s)),
              palace: p.name,
              desc: combo.desc,
              type: combo.type,
            })
          }
        }
      })
    })

    return combos
  })

  const chartQuickInsights = computed(() => {
    if (!options.result.value) return [] as Array<{ label: string; value: string; sub?: string; cls?: string }>
    const items: Array<{ label: string; value: string; sub?: string; cls?: string }> = []

    const totalJi = (options.sihuaByType.value['忌'] ?? []).length
    if (totalJi > 0) {
      const jiPalaces = (options.sihuaByType.value['忌'] ?? []).map((p) => p.source).join('、')
      items.push({ label: '化忌', value: `${totalJi}颗`, sub: jiPalaces, cls: 'cqi-ji' })
    }

    const totalLu = (options.sihuaByType.value['禄'] ?? []).length
    if (totalLu > 0) {
      const luStars = (options.sihuaByType.value['禄'] ?? []).map((p) => p.star).join('、')
      items.push({ label: '化禄', value: `${totalLu}颗`, sub: luStars, cls: 'cqi-lu' })
    }

    const topDist = [...starDistribution.value].sort((a, b) => b.total - a.total)[0]
    if (topDist) {
      items.push({ label: '星曜最密', value: topDist.palaceName.replace('宫', ''), sub: `${topDist.total}颗星`, cls: 'cqi-dense' })
    }

    const lifeMainBright = lifePalaceMainStars.value.filter((s) => options.getStarBrightnessValue(s) >= 3).length
    const lifeMainTotal = lifePalaceMainStars.value.length
    if (lifeMainTotal > 0) {
      items.push({
        label: '命宫旺星',
        value: `${lifeMainBright}/${lifeMainTotal}`,
        sub: '主星庙旺',
        cls: lifeMainBright >= lifeMainTotal ? 'cqi-good' : 'cqi-normal',
      })
    }

    return items
  })

  const chartSummaryStats = computed(() => {
    if (!options.result.value?.palaces?.length) return null

    let totalMainStars = 0
    let totalAuxStars = 0
    let totalTransforms = 0
    let luCount = 0
    let quanCount = 0
    let keCount = 0
    let jiCount = 0
    let brightStars = 0
    let weakStars = 0

    options.result.value.palaces.forEach((p) => {
      const mainStars = p.main_stars || []
      const auxStars = p.aux_stars || []

      totalMainStars += mainStars.length
      totalAuxStars += auxStars.length

      mainStars.forEach((s) => {
        if (options.getStarBrightnessValue(s) >= 3) brightStars++
        if (options.getStarBrightnessValue(s) <= 1) weakStars++

        options.getStarTransforms(s).forEach((t) => {
          totalTransforms++
          if (t.includes('禄')) luCount++
          if (t.includes('权')) quanCount++
          if (t.includes('科')) keCount++
          if (t.includes('忌')) jiCount++
        })
      })

      options.getAuxStars(p).forEach((s) => {
        options.getStarTransforms(s).forEach((t) => {
          totalTransforms++
          if (t.includes('禄')) luCount++
          if (t.includes('权')) quanCount++
          if (t.includes('科')) keCount++
          if (t.includes('忌')) jiCount++
        })
      })
    })

    const SHA_STARS = ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫']
    let shaCount = 0
    options.result.value.palaces.forEach((p) => {
      const allStars = [...(p.main_stars || []), ...options.getAuxStars(p)]
      allStars.forEach((s) => {
        if (SHA_STARS.includes(options.getStarName(s))) shaCount++
      })
    })

    const JI_STARS = ['天魁', '天钺', '左辅', '右弼', '文昌', '文曲']
    let jiStarCount = 0
    options.result.value.palaces.forEach((p) => {
      const allStars = [...(p.main_stars || []), ...options.getAuxStars(p)]
      allStars.forEach((s) => {
        if (JI_STARS.includes(options.getStarName(s))) jiStarCount++
      })
    })

    return {
      totalMainStars,
      totalAuxStars,
      totalTransforms,
      luCount,
      quanCount,
      keCount,
      jiCount,
      brightStars,
      weakStars,
      shaCount,
      jiStarCount,
      patternsCount: options.result.value.patterns?.length || 0,
    }
  })

  return {
    lifePalaceMainStars,
    lifePalaceAuxStars,
    starDistribution,
    maxStarsInPalace,
    wuxingDistribution,
    maxWuxingCount,
    detectedCombos,
    chartQuickInsights,
    chartSummaryStats,
  }
}
