<script setup lang="ts">
import { computed, type PropType } from 'vue'

type ZiweiStarInfo = {
  nature: string
  meaning: string
}

const props = defineProps({
  hoveredStar: {
    type: String,
    default: null,
  },
  starInfoMap: {
    type: Object as PropType<Record<string, ZiweiStarInfo>>,
    required: true,
  },
  position: {
    type: Object as PropType<{ x: number; y: number }>,
    required: true,
  },
})

const starInfo = computed(() => {
  if (!props.hoveredStar) return null
  return props.starInfoMap[props.hoveredStar] ?? null
})
</script>

<template>
  <transition name="fade">
    <div
      v-if="props.hoveredStar && starInfo"
      class="star-tooltip no-print"
      :style="{ left: `${props.position.x}px`, top: `${props.position.y}px` }"
    >
      <div class="st-name">{{ props.hoveredStar }}</div>
      <div class="st-nature">性质：{{ starInfo.nature }}</div>
      <div class="st-meaning">{{ starInfo.meaning }}</div>
    </div>
  </transition>
</template>

<style scoped>
.star-tooltip {
  position: fixed;
  z-index: 1200;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 140px;
  max-width: 200px;
  pointer-events: none;
}

.st-name {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-cn);
  margin-bottom: 4px;
}

.st-nature {
  font-size: var(--fs-xs);
  color: var(--text-2);
  margin-bottom: 2px;
}

.st-meaning {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.4;
}
</style>