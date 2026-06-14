import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
const LIUNIAN_PREFIX = ['年命', '年兄', '年夫', '年子', '年财', '年疾', '年迁', '年友', '年官', '年田', '年福', '年父']
const LIUYUE_PREFIX = ['月命', '月兄', '月夫', '月子', '月财', '月疾', '月迁', '月友', '月官', '月田', '月福', '月父']
const XIAOXIAN_PREFIX = ['小命', '小兄', '小夫', '小子', '小财', '小疾', '小迁', '小友', '小官', '小田', '小福', '小父']

/**
 * 十天干标准四化表（《紫微斗数全书》正统版本，索引0方案）
 * 格式：{ [天干]: { [星名]: '化禄' | '化权' | '化科' | '化忌' } }
 */
const STEM_SIHUA_TABLE: Record<string, Record<string, string>> = {
  '甲': { '廉贞': '化禄', '破军': '化权', '武曲': '化科', '太阳': '化忌' },
  '乙': { '天机': '化禄', '天梁': '化权', '紫微': '化科', '太阴': '化忌' },
  '丙': { '天同': '化禄', '天机': '化权', '文昌': '化科', '廉贞': '化忌' },
  '丁': { '太阴': '化禄', '天同': '化权', '天机': '化科', '巨门': '化忌' },
  '戊': { '贪狼': '化禄', '太阴': '化权', '右弼': '化科', '天机': '化忌' },
  '己': { '武曲': '化禄', '贪狼': '化权', '天梁': '化科', '文曲': '化忌' },
  '庚': { '太阳': '化禄', '武曲': '化权', '太阴': '化科', '天同': '化忌' },
  '辛': { '巨门': '化禄', '太阳': '化权', '文曲': '化科', '文昌': '化忌' },
  '壬': { '天梁': '化禄', '紫微': '化权', '左辅': '化科', '武曲': '化忌' },
  '癸': { '破军': '化禄', '巨门': '化权', '太阴': '化科', '贪狼': '化忌' },
}

type UseZiweiTimeOverlaysOptions = {
  result: Ref<ZiweiResponse | null>
  year: Ref<number>
  gender: Ref<'男' | '女'>
  selectedLiunianYear: Ref<number>
  selectedLiuyueMonth: Ref<number>
}

export function useZiweiTimeOverlays(options: UseZiweiTimeOverlaysOptions) {
  const selectedLiuyueData = computed(() => {
    if (!options.result.value?.liuyue?.length || options.selectedLiuyueMonth.value <= 0) return null
    return options.result.value.liuyue.find((m) => m.month === options.selectedLiuyueMonth.value) || null
  })

  const palaceLiunianInfo = computed(() => {
    if (!options.result.value?.palaces) return {} as Record<number, { age: number; year: number }>
    const map: Record<number, { age: number; year: number }> = {}
    const birthYear = options.year.value
    const lifePalaceIdx = options.result.value.life_palace_branch_idx

    options.result.value.palaces.forEach((p, idx) => {
      const branchIdx = BRANCHES.indexOf(p.branch)
      if (branchIdx < 0) return

      const selectedYear = options.selectedLiunianYear.value
      const yearsToCheck: number[] = []
      for (let y = birthYear; y <= 2100; y++) {
        const liunianBranchOffset = (y - birthYear) % 12
        const liunianBranchIdx = (lifePalaceIdx + liunianBranchOffset) % 12
        if (liunianBranchIdx === branchIdx) {
          yearsToCheck.push(y)
        }
      }

      const closestYear = yearsToCheck.reduce(
        (closest, y) => (Math.abs(y - selectedYear) < Math.abs(closest - selectedYear) ? y : closest),
        yearsToCheck[0] || selectedYear,
      )

      if (closestYear) {
        map[idx] = {
          age: closestYear - birthYear,
          year: closestYear,
        }
      }
    })
    return map
  })

  const liunianLifePalaceIdx = computed(() => {
    if (!options.result.value?.palaces) return -1

    const lifePalaceIdx = options.result.value.life_palace_branch_idx
    const yearOffset = options.selectedLiunianYear.value - options.year.value
    const liunianBranchIdx = (lifePalaceIdx + yearOffset + 120) % 12
    const targetBranch = BRANCHES[liunianBranchIdx]

    return options.result.value.palaces.findIndex((p) => p.branch === targetBranch)
  })

  const palaceLiunianNames = computed(() => {
    const map: Record<number, string> = {}
    if (!options.result.value?.palaces || liunianLifePalaceIdx.value < 0) return map

    for (let i = 0; i < 12; i++) {
      const targetIdx = (liunianLifePalaceIdx.value + i) % 12
      map[targetIdx] = LIUNIAN_PREFIX[i]
    }

    return map
  })

  const liuyueLifePalaceIdx = computed(() => {
    if (!options.result.value?.palaces || !selectedLiuyueData.value) return -1

    const branchIdx = selectedLiuyueData.value.life_palace_branch
    if (branchIdx < 0 || branchIdx > 11) return -1

    const targetBranch = BRANCHES[branchIdx]
    return options.result.value.palaces.findIndex((p) => p.branch === targetBranch)
  })

  const palaceLiuyueNames = computed(() => {
    const map: Record<number, string> = {}
    if (!options.result.value?.palaces || liuyueLifePalaceIdx.value < 0) return map

    for (let i = 0; i < 12; i++) {
      const targetIdx = (liuyueLifePalaceIdx.value + i) % 12
      map[targetIdx] = LIUYUE_PREFIX[i]
    }

    return map
  })

  const liuyueSihuaMap = computed(() => {
    if (!selectedLiuyueData.value) return {} as Record<string, string>
    return selectedLiuyueData.value.sihua || {}
  })

  const currentLiunianAge = computed(() => options.selectedLiunianYear.value - options.year.value)

  const xiaoxianPalaceIdx = computed(() => {
    if (!options.result.value?.palaces || currentLiunianAge.value < 1) return -1

    const targetAge = currentLiunianAge.value
    return options.result.value.palaces.findIndex(
      (p) => p.xiaoxian_ages && p.xiaoxian_ages.includes(targetAge),
    )
  })

  const palaceXiaoxianNames = computed(() => {
    const map: Record<number, string> = {}
    if (!options.result.value?.palaces || xiaoxianPalaceIdx.value < 0) return map

    const forward = options.gender.value === '男'
    for (let i = 0; i < 12; i++) {
      const targetIdx = forward
        ? (xiaoxianPalaceIdx.value + i) % 12
        : (xiaoxianPalaceIdx.value - i + 12) % 12
      map[targetIdx] = XIAOXIAN_PREFIX[i]
    }

    return map
  })

  /**
   * 小限四化 map（星名 → 四化类型）
   * 依据小限命宫（xiaoxianPalaceIdx 对应的宫位）的天干，查四化表获得
   */
  const xiaoxianSihuaMap = computed((): Record<string, string> => {
    if (!options.result.value?.palaces || xiaoxianPalaceIdx.value < 0) return {}
    const palace = options.result.value.palaces[xiaoxianPalaceIdx.value]
    if (!palace?.stem) return {}
    return STEM_SIHUA_TABLE[palace.stem] ?? {}
  })

  return {
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
  }
}
