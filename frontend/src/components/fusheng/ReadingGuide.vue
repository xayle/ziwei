<script setup lang="ts">
import { computed } from 'vue'
import type { DisclaimerBlock } from '@/types/life-volume'
import ContentLayerLegend from '@/components/fusheng/ContentLayerLegend.vue'
import TrustDegradedBanner from '@/components/fusheng/TrustDegradedBanner.vue'
import { DEFAULT_READING_GUIDE_PARAGRAPHS } from '@/utils/extractReadingGuideParagraphs'

const props = defineProps<{
  disclaimer: DisclaimerBlock
  resumeVolumeId?: string | null
  resumeLabel?: string | null
  showLayerLegend?: boolean
  readingParagraphs?: string[]
  readingLoading?: boolean
  readingFailed?: boolean
  usingDynamicReading?: boolean
}>()

const emit = defineEmits<{
  resume: []
}>()

const displayParagraphs = computed(() => (
  props.readingParagraphs?.length ? props.readingParagraphs : [...DEFAULT_READING_GUIDE_PARAGRAPHS]
))
</script>

<template>
  <aside class="reading-guide fs-card" role="complementary" aria-label="读法导览">
    <h2 class="reading-guide__title">读法导览</h2>

    <p v-if="readingLoading" class="reading-guide__text" data-testid="reading-guide-loading">
      正在加载读法导览…
    </p>
    <template v-else>
      <div v-if="readingFailed" data-testid="reading-guide-fallback">
        <TrustDegradedBanner
          message="读法导览暂不可用，以下为默认说明。"
          status="warn"
        />
      </div>
      <p
        v-for="(paragraph, index) in displayParagraphs"
        :key="index"
        class="reading-guide__text"
        :data-testid="usingDynamicReading ? 'reading-guide-dynamic' : undefined"
      >
        {{ paragraph }}
      </p>
    </template>

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
