<script setup lang="ts">
import { ref, watch } from 'vue'
import PatternTierBadge from '@/components/fusheng/PatternTierBadge.vue'

export type AnalysisBlock = {
  id: string
  title: string
  lead: string
  body: string
  bullets?: string[]
  chips?: string[]
  /** engine | classical | heuristic — heuristic 默认折叠 */
  layer?: 'engine' | 'classical' | 'heuristic' | 'modern_convention'
}

const props = defineProps<{
  blocks: AnalysisBlock[]
  defaultOpenId?: string
  /** 默认折叠 heuristic / modern_convention 层 */
  collapseHeuristic?: boolean
  /** 深读等场景：默认展开全部手风琴块 */
  defaultExpandAll?: boolean
}>()

const collapseHeuristic = props.collapseHeuristic !== false

function isHeuristic(block: AnalysisBlock): boolean {
  return block.layer === 'heuristic' || block.layer === 'modern_convention'
}

function initialOpenIds(): Set<string> {
  if (props.defaultExpandAll && props.blocks.length) {
    return new Set(props.blocks.map((block) => block.id))
  }
  return new Set(props.defaultOpenId ? [props.defaultOpenId] : [])
}

const openIds = ref<Set<string>>(initialOpenIds())
const heuristicExpanded = ref<Set<string>>(
  props.defaultExpandAll
    ? new Set(props.blocks.filter(isHeuristic).map((block) => block.id))
    : new Set(),
)

function isVisible(block: AnalysisBlock): boolean {
  if (!collapseHeuristic || !isHeuristic(block)) return true
  return heuristicExpanded.value.has(block.id)
}

function toggleHeuristic(id: string) {
  const next = new Set(heuristicExpanded.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  heuristicExpanded.value = next
}

function toggle(id: string) {
  const next = new Set(openIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  openIds.value = next
}

watch(
  () => [props.blocks.map((block) => block.id).join('|'), props.defaultExpandAll, props.defaultOpenId] as const,
  () => {
    openIds.value = initialOpenIds()
    if (props.defaultExpandAll) {
      heuristicExpanded.value = new Set(props.blocks.filter(isHeuristic).map((block) => block.id))
    }
  },
)
</script>

<template>
  <section class="analysis-panel">
    <article
      v-for="block in blocks"
      :key="block.id"
      class="analysis-panel__block"
      :class="{
        'analysis-panel__block--classical': block.layer === 'classical',
        'analysis-panel__block--engine': block.layer === 'engine',
        'analysis-panel__block--heuristic': isHeuristic(block),
      }"
    >
      <header v-if="collapseHeuristic && isHeuristic(block) && !heuristicExpanded.has(block.id)" class="analysis-panel__head analysis-panel__head--heuristic">
        <div>
          <h3>{{ block.title }} <PatternTierBadge layer="heuristic" /></h3>
          <p class="analysis-panel__lead analysis-panel__lead--heuristic">启发式 · 非典籍</p>
        </div>
        <button type="button" class="analysis-panel__toggle" @click="toggleHeuristic(block.id)">展开</button>
      </header>
      <template v-else-if="isVisible(block)">
      <header class="analysis-panel__head">
        <div>
          <h3>
            {{ block.title }}
            <PatternTierBadge v-if="block.layer === 'classical'" layer="classical" />
            <PatternTierBadge v-else-if="block.layer === 'engine'" layer="engine" />
            <PatternTierBadge v-else-if="isHeuristic(block)" layer="heuristic" />
          </h3>
          <p class="analysis-panel__lead">{{ block.lead }}</p>
        </div>
        <button type="button" class="analysis-panel__toggle" :aria-expanded="openIds.has(block.id)" @click="toggle(block.id)">
          {{ openIds.has(block.id) ? '收起' : '展开' }}
        </button>
      </header>
      <div v-if="block.chips?.length" class="analysis-panel__chips">
        <span v-for="chip in block.chips" :key="chip" class="chip">{{ chip }}</span>
      </div>
      <div v-show="openIds.has(block.id)" class="analysis-panel__body">
        <p>{{ block.body }}</p>
        <ul v-if="block.bullets?.length">
          <li v-for="(line, idx) in block.bullets" :key="idx">{{ line }}</li>
        </ul>
      </div>
      </template>
    </article>
  </section>
</template>

<style scoped>
.analysis-panel {
  display: grid;
  gap: 12px;
}

.analysis-panel__block {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 16px;
}

.analysis-panel__block--classical {
  border: 2px solid var(--layer-classical-border, #b8894d);
  background: var(--layer-classical-bg, #fffaf5);
  box-shadow: 0 0 0 1px rgba(184, 137, 77, 0.12);
}

.analysis-panel__block--engine {
  background: var(--layer-engine-bg, #f7f1e8);
}

.analysis-panel__block--heuristic:not(.analysis-panel__head--heuristic) {
  background: var(--layer-heuristic-bg, #fefce8);
}

.analysis-panel__lead--heuristic {
  color: var(--brand-cinnabar);
}

.analysis-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.analysis-panel__head h3 {
  margin: 0;
  font-size: 16px;
  font-family: var(--font-cn);
  color: var(--brand-ink);
}

.analysis-panel__lead {
  margin: 6px 0 0;
  color: var(--brand-gold-dark);
  font-size: 14px;
  font-weight: 600;
}

.analysis-panel__toggle {
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--inset-tint);
  color: var(--text-2);
  cursor: pointer;
  flex-shrink: 0;
}

.analysis-panel__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.chip {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
}

.analysis-panel__body {
  margin-top: 12px;
  color: var(--text-2);
  line-height: 1.75;
  font-size: 14px;
}

.analysis-panel__body ul {
  margin: 10px 0 0;
  padding-left: 18px;
}

.layer-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  background: var(--brand-gold-lt);
  color: var(--brand-gold-dark);
  vertical-align: middle;
}

.layer-badge--classical {
  background: var(--surface);
  border: 1px solid var(--brand-gold);
  color: var(--brand-gold-dark);
}

.layer-badge--engine {
  background: var(--surface);
  border: 1px solid var(--border-md);
  color: var(--brand-mist);
}

.analysis-panel__head--heuristic {
  opacity: 0.88;
}
</style>
