<script setup lang="ts">
import { computed } from 'vue'
import { patternLayerForRule } from '@/utils/buildZiweiInsightBlocks'

const props = withDefaults(defineProps<{
  layer?: 'classical' | 'engine' | 'heuristic' | 'modern_convention'
  ruleId?: string | null
  label?: string
}>(), {
  layer: undefined,
  ruleId: undefined,
  label: undefined,
})

const resolvedLayer = computed(() => {
  if (props.layer) return props.layer
  if (props.ruleId) return patternLayerForRule(props.ruleId)
  return 'heuristic'
})

const text = computed(() => {
  if (props.label) return props.label
  switch (resolvedLayer.value) {
    case 'classical': return '全书口径'
    case 'engine': return '引擎'
    case 'modern_convention': return '现代约定'
    default: return '启发式'
  }
})
</script>

<template>
  <span
    class="pattern-tier-badge"
    :class="`pattern-tier-badge--${resolvedLayer}`"
    :data-layer="resolvedLayer"
    :title="ruleId ? `rule: ${ruleId}` : undefined"
  >
    {{ text }}
  </span>
</template>

<style scoped>
.pattern-tier-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
}

.pattern-tier-badge--classical {
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
  border: 1px solid var(--brand-gold);
}

.pattern-tier-badge--engine {
  background: var(--layer-engine-bg);
  color: var(--brand-mist);
  border: 1px solid var(--border-md);
}

.pattern-tier-badge--heuristic,
.pattern-tier-badge--modern_convention {
  background: var(--layer-heuristic-bg);
  color: #854d0e;
  border: 1px solid #fde68a;
}
</style>
