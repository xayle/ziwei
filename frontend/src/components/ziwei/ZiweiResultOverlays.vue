<script setup lang="ts">
import ZiweiStarSearchModal from './ZiweiStarSearchModal.vue'
import ZiweiStarTooltip from './ZiweiStarTooltip.vue'

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

const props = defineProps<{
  showStarSearch: boolean
  starSearchQuery: string
  starSearchResults: StarSearchItem[]
  hoveredStar: string | null
  starInfoMap: Record<string, ZiweiStarInfo>
  starTooltipPos: { x: number; y: number }
}>()

const emit = defineEmits<{
  closeStarSearch: []
  'update:starSearchQuery': [value: string]
  selectSearchResult: [palaceIdx: number]
}>()
</script>

<template>
  <ZiweiStarSearchModal
    :visible="props.showStarSearch"
    :query="props.starSearchQuery"
    :results="props.starSearchResults"
    @close="emit('closeStarSearch')"
    @update:query="emit('update:starSearchQuery', $event)"
    @select="emit('selectSearchResult', $event)"
  />

  <ZiweiStarTooltip
    :hovered-star="props.hoveredStar ?? undefined"
    :star-info-map="props.starInfoMap"
    :position="props.starTooltipPos"
  />
</template>
