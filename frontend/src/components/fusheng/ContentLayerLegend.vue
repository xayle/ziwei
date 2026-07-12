<script setup lang="ts">
import { CONTENT_LAYER_LABELS, type ContentLayer } from '@/types/life-volume'

const layers: ContentLayer[] = ['fact', 'cite', 'inference']
</script>

<template>
  <ul class="layer-legend" aria-label="内容分层图例">
    <li
      v-for="layer in layers"
      :key="layer"
      class="layer-legend__item"
      :data-layer="layer"
    >
      <span class="layer-legend__mark" aria-hidden="true" />
      {{ CONTENT_LAYER_LABELS[layer] }}
    </li>
  </ul>
</template>

<style scoped>
.layer-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.layer-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--brand-mist);
  font-family: var(--font-ui);
}

.layer-legend__mark {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid var(--border-md);
  background: var(--surface);
}

.layer-legend__item[data-layer='cite'] .layer-legend__mark {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
}

.layer-legend__item[data-layer='inference'] .layer-legend__mark {
  border-color: var(--brand-cinnabar);
}
</style>
