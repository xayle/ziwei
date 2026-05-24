import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
const LIUNIAN_PREFIX = ['年命', '年兄', '年夫', '年子', '年财', '年疾', '年迁', '年友', '年官', '年田', '年福', '年父']
const LIUYUE_PREFIX = ['月命', '月兄', '月夫', '月子', '月财', '月疾', '月迁', '月友', '月官', '月田', '月福', '月父']
const XIAOXIAN_PREFIX = ['小命', '小兄', '小夫', '小子', '小财', '小疾', '小迁', '小友', '小官', '小田', '小福', '小父']

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
  }
}
