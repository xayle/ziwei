<script setup lang="ts">
import { computed } from 'vue'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'

const props = defineProps<{
  volumeId?: LifeVolumeId
  eyebrow?: string
  title: string
  desc?: string
  /** ZW-01：壳层已有 h1 时用 p，避免双标题 */
  titleTag?: 'h1' | 'p'
}>()

const volumeEyebrow = computed(() => {
  if (props.eyebrow?.trim()) return props.eyebrow.trim()
  if (props.volumeId) return LIFE_VOLUME_LABELS[props.volumeId]
  return ''
})

const titleEl = computed(() => props.titleTag === 'p' ? 'p' : 'h1')
</script>

<template>
  <header class="fs-page-head volume-head" :data-volume-id="volumeId">
    <div class="volume-head__copy">
      <p v-if="volumeEyebrow" class="fs-page-head__eyebrow">{{ volumeEyebrow }}</p>
      <component :is="titleEl" class="fs-page-head__title">{{ title }}</component>
      <p v-if="desc" class="fs-page-head__desc">{{ desc }}</p>
    </div>
    <div v-if="$slots.actions" class="fs-page-actions volume-head__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.volume-head {
  flex-wrap: wrap;
}

.volume-head__copy {
  flex: 1 1 240px;
  min-width: 0;
}

.volume-head__actions {
  flex: 0 0 auto;
}
</style>
