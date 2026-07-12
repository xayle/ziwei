<script setup lang="ts">
import type { DisclaimerBlock } from '@/types/life-volume'
import ContentLayerLegend from '@/components/fusheng/ContentLayerLegend.vue'

defineProps<{
  disclaimer: DisclaimerBlock
  resumeVolumeId?: string | null
  resumeLabel?: string | null
  showLayerLegend?: boolean
}>()

const emit = defineEmits<{
  resume: []
}>()
</script>

<template>
  <aside class="reading-guide fs-card">
    <h2 class="reading-guide__title">读法导览</h2>
    <p class="reading-guide__text">
      六卷辑录按分层阅读；卷五推断默认折叠，卷六问书需主动展开。
    </p>
    <ContentLayerLegend v-if="showLayerLegend !== false" />
    <p class="reading-guide__disclaimer">{{ disclaimer.text }}</p>
    <p v-if="resumeVolumeId && resumeLabel" class="reading-guide__resume">
      续读：
      <button
        type="button"
        class="reading-guide__resume-btn"
        data-testid="reading-guide-resume"
        @click="emit('resume')"
      >
        {{ resumeLabel }}
      </button>
    </p>
  </aside>
</template>

<style scoped>
.reading-guide {
  display: grid;
  gap: 10px;
}

.reading-guide__title {
  margin: 0;
  font-size: 16px;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.reading-guide__text,
.reading-guide__disclaimer {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.reading-guide__disclaimer {
  padding-top: 8px;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.reading-guide__resume-btn {
  border: none;
  background: none;
  padding: 0;
  color: var(--brand-gold-dark);
  text-decoration: underline;
  cursor: pointer;
  font: inherit;
}
</style>
