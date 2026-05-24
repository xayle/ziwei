import { computed, nextTick, ref, type Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'

type StarSearchItem = {
  name: string
  palace: string
  palaceIdx: number
  type: 'main' | 'aux'
  brightness?: string
  transforms?: string[]
}

type UseZiweiStarInteractionsOptions = {
  result: Ref<ZiweiResponse | null>
  selectedPalace: Ref<PalaceResponse | null>
  starInfoMap: Record<string, { nature: string; meaning: string }>
  getChartExportElement: () => HTMLElement | null
}

export function useZiweiStarInteractions(options: UseZiweiStarInteractionsOptions) {
  const showStarSearch = ref(false)
  const starSearchQuery = ref('')
  const hoveredStar = ref<string | null>(null)
  const starTooltipPos = ref({ x: 0, y: 0 })

  const allStarsInChart = computed(() => {
    if (!options.result.value?.palaces) return [] as StarSearchItem[]
    const stars: StarSearchItem[] = []
    options.result.value.palaces.forEach((palace, idx) => {
      palace.main_stars.forEach((star) => {
        stars.push({
          name: star.name,
          palace: palace.name,
          palaceIdx: idx,
          type: 'main',
          brightness: star.brightness,
          transforms: star.transforms,
        })
      })
      palace.aux_stars.forEach((star) => {
        stars.push({
          name: star.name,
          palace: palace.name,
          palaceIdx: idx,
          type: 'aux',
        })
      })
    })
    return stars
  })

  const starSearchResults = computed(() => {
    if (!starSearchQuery.value.trim()) return [] as StarSearchItem[]
    const keyword = starSearchQuery.value.trim().toLowerCase()
    return allStarsInChart.value.filter((item) => item.name.toLowerCase().includes(keyword))
  })

  function openStarSearch() {
    showStarSearch.value = true
    nextTick(() => {
      const input = document.querySelector<HTMLInputElement>('.star-search-input')
      input?.focus()
    })
  }

  function closeStarSearch(resetQuery = false) {
    showStarSearch.value = false
    if (resetQuery) {
      starSearchQuery.value = ''
    }
  }

  function showStarTooltip(starName: string, event: MouseEvent) {
    if (!options.starInfoMap[starName]) return
    hoveredStar.value = starName
    starTooltipPos.value = { x: event.clientX + 10, y: event.clientY + 10 }
  }

  function hideStarTooltip() {
    hoveredStar.value = null
  }

  function selectPalace(palace: PalaceResponse) {
    options.selectedPalace.value = options.selectedPalace.value?.index === palace.index ? null : palace
  }

  function selectPalaceByIndex(idx: number) {
    if (!options.result.value?.palaces) return
    const palace = options.result.value.palaces.find((item) => item.index === idx)
    if (!palace) return
    options.selectedPalace.value = palace
    options.getChartExportElement()?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function closeSelectedPalace() {
    options.selectedPalace.value = null
  }

  function selectSearchResult(palaceIdx: number) {
    if (!options.result.value?.palaces?.[palaceIdx]) return
    selectPalace(options.result.value.palaces[palaceIdx])
    closeStarSearch(true)
  }

  return {
    showStarSearch,
    starSearchQuery,
    starSearchResults,
    openStarSearch,
    closeStarSearch,
    hoveredStar,
    starTooltipPos,
    showStarTooltip,
    hideStarTooltip,
    selectPalace,
    selectPalaceByIndex,
    closeSelectedPalace,
    selectSearchResult,
  }
}
