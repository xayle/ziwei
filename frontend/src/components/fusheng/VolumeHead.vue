<script setup lang="ts">
import { computed } from 'vue'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'

const props = defineProps<{
  volumeId?: LifeVolumeId
  eyebrow?: string
  title: string
  desc?: string
}>()

const volumeEyebrow = computed(() => {
  if (props.eyebrow?.trim()) return props.eyebrow.trim()
  if (props.volumeId) return LIFE_VOLUME_LABELS[props.volumeId]
  return ''
})
</script>

<template>
  <header class="fs-page-head volume-head" :data-volume-id="volumeId">
    <div class="volume-head__copy">
      <p v-if="volumeEyebrow" class="fs-page-head__eyebrow">{{ volumeEyebrow }}</p>
      <h1 class="fs-page-head__title">{{ title }}</h1>
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
