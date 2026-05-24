import { computed, type Ref } from 'vue'

type StarSearchItem = {
  name: string
  palace: string
  palaceIdx: number
  type: 'main' | 'aux'
  brightness?: string
  transforms?: string[]
}

type ZiweiStarInfo = {
  nature: string
  meaning: string
}

type UseZiweiResultOverlaysBindingsOptions = {
  showStarSearch: Ref<boolean>
  starSearchQuery: Ref<string>
  starSearchResults: Ref<StarSearchItem[]>
  closeStarSearch: () => void
  selectSearchResult: (palaceIdx: number) => void
  hoveredStar: Ref<string | null>
  starInfoMap: Record<string, ZiweiStarInfo>
  starTooltipPos: Ref<{ x: number; y: number }>
}

export function useZiweiResultOverlaysBindings(options: UseZiweiResultOverlaysBindingsOptions) {
  const resultOverlaysBindings = computed(() => ({
    showStarSearch: options.showStarSearch.value,
    starSearchQuery: options.starSearchQuery.value,
    starSearchResults: options.starSearchResults.value,
    hoveredStar: options.hoveredStar.value,
    starInfoMap: options.starInfoMap,
    starTooltipPos: options.starTooltipPos.value,
    onCloseStarSearch: options.closeStarSearch,
    'onUpdate:starSearchQuery': (value: string) => {
      options.starSearchQuery.value = value
    },
    onSelectSearchResult: options.selectSearchResult,
  }))

  return {
    resultOverlaysBindings,
  }
}
