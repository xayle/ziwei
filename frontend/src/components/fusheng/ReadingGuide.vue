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
  showTitle?: boolean
  showResume?: boolean
  variant?: 'card' | 'plain'
  readingParagraphs?: string[]
  readingLoading?: boolean
  readingFailed?: boolean
  usingDynamicReading?: boolean
}>()

const emit = defineEmits<{
  resume: []
}>()

const isPlain = computed(() => props.variant === 'plain')
const showHeading = computed(() => props.showTitle !== false && !isPlain.value)
const showResumeLink = computed(() => props.showResume === true || props.showResume === undefined)

const displayParagraphs = computed(() => (
  props.readingParagraphs?.length ? props.readingParagraphs : [...DEFAULT_READING_GUIDE_PARAGRAPHS]
))
</script>

<template>
  <aside
    class="reading-guide"
    :class="{ 'fs-card': !isPlain, 'reading-guide--plain': isPlain }"
    role="complementary"
    aria-label="读法导览"
    data-testid="reading-guide"
  >
    <p v-if="isPlain" class="reading-guide__eyebrow">读法</p>
    <h2 v-if="showHeading" class="reading-guide__title">读法导览</h2>

    <p v-if="readingLoading" class="reading-guide__text" data-testid="reading-guide-loading">
      正在加载读法导览…
    </p>
    <template v-else>
      <div v-if="readingFailed" data-testid="reading-guide-fallback">
        <TrustDegradedBanner
          v-if="!isPlain"
          message="读法导览暂不可用，以下为默认说明。"
          status="warn"
        />
        <p v-else class="reading-guide__fallback">
          读法导览暂不可用，以下为默认说明。
        </p>
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

    <ContentLayerLegend v-if="showLayerLegend !== false && !isPlain" />
    <p class="reading-guide__disclaimer">{{ disclaimer.text }}</p>
    <p v-if="showResumeLink && resumeVolumeId && resumeLabel" class="reading-guide__resume">
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

.reading-guide--plain {
  gap: 8px;
}

.reading-guide__eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.28em;
  color: var(--brand-gold);
  font-family: var(--font-display);
}

.reading-guide__title {
  margin: 0;
  font-size: 16px;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.reading-guide__text,
.reading-guide__disclaimer,
.reading-guide__fallback {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.reading-guide--plain .reading-guide__text,
.reading-guide--plain .reading-guide__disclaimer,
.reading-guide--plain .reading-guide__fallback {
  font-family: var(--font-display);
  letter-spacing: 0.04em;
}

.reading-guide__fallback {
  font-size: 12px;
  color: var(--text-3);
}

.reading-guide__disclaimer {
  padding-top: 8px;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.reading-guide--plain .reading-guide__disclaimer {
  padding-top: 12px;
  margin-top: 4px;
  color: var(--text-3);
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
