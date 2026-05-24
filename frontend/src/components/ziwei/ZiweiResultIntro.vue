<script setup lang="ts">
import ZiweiTabsNav from './ZiweiTabsNav.vue'

type ZiweiTabKey = 'chart' | 'summary' | 'palaces' | 'dayun' | 'liunian' | 'liuyue' | 'patterns' | 'flying' | 'forecast' | 'suggest'

const props = defineProps<{
  summary: string | null
  activeTab: string
  hasLiunian: boolean
  hasLiuyue: boolean
  patternsCount: number
  hasFlying: boolean
  hasForecast: boolean
}>()

const emit = defineEmits<{
  'update:activeTab': [tab: ZiweiTabKey]
}>()
</script>

<template>
  <div class="result-intro">
    <p v-if="props.summary" class="summary-block">{{ props.summary }}</p>

    <ZiweiTabsNav
      :active-tab="props.activeTab"
      :has-liunian="props.hasLiunian"
      :has-liuyue="props.hasLiuyue"
      :patterns-count="props.patternsCount"
      :has-flying="props.hasFlying"
      :has-forecast="props.hasForecast"
      @update:active-tab="emit('update:activeTab', $event)"
    />
  </div>
</template>

<style scoped>
.summary-block {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.7;
  margin-bottom: var(--sp-5);
  padding: var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

@media print {
  .summary-block {
    font-size: 10pt;
    line-height: 1.6;
    border: none;
    background: transparent !important;
    padding: 8px 0;
  }
}
</style>
