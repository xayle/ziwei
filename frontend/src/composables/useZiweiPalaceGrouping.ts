import { computed, ref, type Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'

const PALACE_GROUPS = [
  { key: 'core', title: '核心宫位', names: ['命宫', '身宫'] },
  { key: 'career', title: '事业财禄', names: ['官禄宫', '财帛宫', '田宅宫', '福德宫'] },
  { key: 'relation', title: '关系家庭', names: ['夫妻宫', '子女宫', '兄弟宫', '父母宫'] },
  { key: 'movement', title: '迁移健康', names: ['迁移宫', '疾厄宫', '仆役宫', '交友宫'] },
] as const

type PalaceGroupItem = {
  key: string
  title: string
  items: PalaceResponse[]
}

type UseZiweiPalaceGroupingOptions = {
  result: Ref<ZiweiResponse | null>
}

export function useZiweiPalaceGrouping(options: UseZiweiPalaceGroupingOptions) {
  const palaceFilter = ref('')

  const palacesStats = computed(() => {
    if (!options.result.value?.palaces?.length) return { total: 0, withMain: 0, withConclusion: 0 }
    let withMain = 0
    let withConclusion = 0
    options.result.value.palaces.forEach((p) => {
      if (p.main_stars.length > 0) withMain++
      if (p.conclusion || p.analysis) withConclusion++
    })
    return { total: options.result.value.palaces.length, withMain, withConclusion }
  })

  const filteredPalaces = computed(() => {
    if (!options.result.value?.palaces?.length) return [] as PalaceResponse[]
    if (!palaceFilter.value) return options.result.value.palaces
    const kw = palaceFilter.value.toLowerCase()
    return options.result.value.palaces.filter((p) =>
      p.name.toLowerCase().includes(kw) ||
      p.main_stars.some((s) => s.name.includes(kw)),
    )
  })

  const palaceGroupExpanded = ref<Record<string, boolean>>({
    core: true,
    career: true,
    relation: true,
    movement: true,
    other: true,
  })

  function togglePalaceGroup(groupKey: string) {
    palaceGroupExpanded.value[groupKey] = !palaceGroupExpanded.value[groupKey]
  }

  const groupedFilteredPalaces = computed(() => {
    const source = filteredPalaces.value
    const used = new Set<number>()
    const groups: PalaceGroupItem[] = PALACE_GROUPS.map((group) => {
      const items = source.filter((p) => group.names.includes(p.name as never))
      items.forEach((p) => used.add(p.index))
      return {
        key: group.key,
        title: group.title,
        items,
      }
    })
    const otherItems = source.filter((p) => !used.has(p.index))
    if (otherItems.length) {
      groups.push({
        key: 'other',
        title: '其他宫位',
        items: otherItems,
      })
    }
    return groups.filter((group) => group.items.length > 0)
  })

  return {
    palaceFilter,
    palacesStats,
    filteredPalaces,
    palaceGroupExpanded,
    togglePalaceGroup,
    groupedFilteredPalaces,
  }
}
