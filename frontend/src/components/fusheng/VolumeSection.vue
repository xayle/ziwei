<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AnalysisBlock, VolumeSection } from '@/types/life-volume'
import { CONTENT_LAYER_LABELS } from '@/types/life-volume'

function blockLayerLabel(block: AnalysisBlock): string {
  if (block.layer === 'cite' && block.classic_id) return CONTENT_LAYER_LABELS.cite
  if (block.layer === 'cite') return '待校勘'
  return CONTENT_LAYER_LABELS[block.layer]
}

const props = defineProps<{
  section: VolumeSection
  volumeId?: string
}>()

const expanded = ref(!props.section.collapsed_default)

const isInference = computed(() => props.section.layer === 'inference')
</script>

<template>
  <section
    class="volume-section"
    :class="{ 'volume-section--inference': isInference }"
    :data-volume="volumeId"
    :data-section="section.id"
  >
    <header class="volume-section__head">
      <div>
        <h3 class="volume-section__heading">{{ section.heading }}</h3>
        <span v-if="!section.blocks.length" class="volume-section__layer" :data-layer="section.layer">
          {{ CONTENT_LAYER_LABELS[section.layer] }}
        </span>
      </div>
      <button
        v-if="section.collapsed_default"
        type="button"
        class="volume-section__toggle fs-btn fs-btn--ghost"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        {{ expanded ? '收起' : '展开' }}
        <span v-if="isInference" class="volume-section__badge">推断</span>
      </button>
    </header>
    <div v-show="expanded || !section.collapsed_default" class="volume-section__body">
      <p
        v-for="(blk, idx) in section.blocks"
        :key="idx"
        class="volume-section__block"
        :data-layer="blk.layer"
      >
        <span class="volume-section__block-label" :data-layer="blk.layer">{{ blockLayerLabel(blk) }}</span>
        {{ blk.text }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.volume-section {
  display: grid;
  gap: 10px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.volume-section__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.volume-section__heading {
  margin: 0;
  font-size: 15px;
  font-family: var(--font-display);
  color: var(--brand-ink);
}

.volume-section__layer {
  font-size: 11px;
  color: var(--brand-mist);
  letter-spacing: 0.08em;
}

.volume-section__badge {
  margin-left: 6px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 10px;
  color: var(--brand-cinnabar);
  border: 1px solid var(--brand-cinnabar);
}

.volume-section__block {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--text);
}

.volume-section__block-label {
  display: inline-block;
  margin-right: 8px;
  font-size: 11px;
  color: var(--brand-mist);
}

.volume-section__block[data-layer='cite'] {
  padding-left: 12px;
  border-left: 3px solid var(--brand-gold);
  color: var(--brand-ink);
  font-family: var(--font-display);
  font-size: 15px;
  line-height: 1.65;
}

.volume-section__block-label[data-layer='cite'] {
  color: var(--brand-gold-dark);
}

.volume-section--inference .volume-section__block {
  color: var(--brand-mist);
}
</style>
