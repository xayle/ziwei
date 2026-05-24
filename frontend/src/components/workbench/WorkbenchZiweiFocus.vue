<script setup lang="ts">
interface ZiweiStar {
  name: string
  brightness?: string
  transforms?: string[]
}

interface ZiweiPalace {
  name: string
  stem?: string
  branch?: string
  changsheng?: string
  aux_stars?: { name: string; brightness?: string; brightness_val?: number }[]
  main_stars: ZiweiStar[]
  analysis?: string
  explanation?: string
  tooltip?: string
  suggestion?: string
}

interface ZiweiRelationItem {
  transform: string
  target?: string
  src?: string
}

interface ZiweiRelations {
  opposite: string
  flyingOutEntries: Array<ZiweiRelationItem & { target: string }>
  receiving: Array<ZiweiRelationItem & { src: string }>
}

interface ZiweiRelationLink {
  from: string
  to: string
  label: string
  kind: 'opposite' | 'out' | 'in'
  d: string
  labelX: number
  labelY: number
}

interface ZiweiRelationNode {
  id: string
  displayLabel: { line1: string; line2: string }
  fullLabel: string
  x: number
  y: number
  kind: 'active' | 'opposite' | 'out' | 'in'
  palaceName?: string
}

interface ZiweiRelationGraph {
  width: number
  height: number
  centerX: number
  centerY: number
  innerRadius: number
  outerRadius: number
  nodes: ZiweiRelationNode[]
  links: ZiweiRelationLink[]
}

const props = defineProps<{
  palaces: ZiweiPalace[]
  activePalace: ZiweiPalace | null
  highlightedPalaceName: string
  relations: ZiweiRelations | null
  relationGraph: ZiweiRelationGraph | null
}>()

const emit = defineEmits<{
  selectPalace: [name: string]
}>()

function handleSelectPalace(name?: string) {
  if (name) emit('selectPalace', name)
}
</script>

<template>
  <div class="zw-section">
    <h2 class="zw-sec-title">十二宫与主星</h2>
    <div class="zw-layout">
      <div class="zw-grid">
        <button
          v-for="palace in props.palaces"
          :key="palace.name"
          type="button"
          class="zw-cell"
          :class="{ active: palace.name === props.activePalace?.name, highlighted: palace.name === props.highlightedPalaceName }"
          @click="handleSelectPalace(palace.name)"
        >
          <div class="zw-cell-head">
            <span class="zw-cell-name">{{ palace.name }}</span>
            <span class="zw-cell-gz">{{ palace.stem }}{{ palace.branch }}</span>
          </div>
          <div class="zw-cell-stars">{{ palace.main_stars?.map(s => s.name).join('、') || '无主星' }}</div>
          <div class="zw-cell-foot">
            <span>{{ palace.changsheng || '—' }}</span>
            <span>{{ palace.aux_stars?.length ?? 0 }} 辅星</span>
          </div>
          <div v-if="palace.name === props.highlightedPalaceName" class="zw-cell-tag">本月落宫</div>
        </button>
      </div>

      <div v-if="props.activePalace" class="zw-focus">
        <div class="zw-focus-title">{{ props.activePalace.name }} · {{ props.activePalace.stem }}{{ props.activePalace.branch }}</div>
        <div class="zw-star-list">
          <div v-for="star in props.activePalace.main_stars" :key="star.name" class="zw-star-item">
            <span class="zw-star-name">{{ star.name }}</span>
            <span class="zw-star-meta">{{ star.brightness }}<template v-if="star.transforms?.length"> · {{ star.transforms.join(' / ') }}</template></span>
          </div>
        </div>
        <div v-if="props.activePalace.aux_stars?.length" class="chip-list" style="margin-top:10px;">
          <span v-for="star in props.activePalace.aux_stars" :key="star.name" class="chip">{{ star.name }}</span>
        </div>
        <div class="zw-focus-copy">
          <p>{{ props.activePalace.analysis || props.activePalace.explanation || props.activePalace.tooltip || '暂无宫位说明。' }}</p>
          <p v-if="props.activePalace.suggestion" class="zw-suggestion">建议：{{ props.activePalace.suggestion }}</p>
        </div>

        <div v-if="props.relations" class="zw-relations">
          <div v-if="props.relationGraph" class="zw-rel-graph-wrap">
            <svg class="zw-rel-graph" :viewBox="`0 0 ${props.relationGraph.width} ${props.relationGraph.height}`" role="img" aria-label="紫微宫位关系图">
              <defs>
                <marker id="zw-rel-arrow-out" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L8,4 L0,8 z" class="zw-rel-arrow out" />
                </marker>
                <marker id="zw-rel-arrow-in" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L8,4 L0,8 z" class="zw-rel-arrow in" />
                </marker>
              </defs>
              <circle :cx="props.relationGraph.centerX" :cy="props.relationGraph.centerY" :r="props.relationGraph.innerRadius" class="zw-rel-ring inner" />
              <circle :cx="props.relationGraph.centerX" :cy="props.relationGraph.centerY" :r="props.relationGraph.outerRadius" class="zw-rel-ring outer" />
              <g v-for="link in props.relationGraph.links" :key="`${link.kind}-${link.from}-${link.to}-${link.label}`">
                <path :d="link.d" :class="['zw-rel-line', `is-${link.kind}`]" :marker-end="link.kind === 'opposite' ? undefined : `url(#zw-rel-arrow-${link.kind})`" />
                <text :x="link.labelX" :y="link.labelY" :class="['zw-rel-line-label', `is-${link.kind}`]" text-anchor="middle">{{ link.label }}</text>
              </g>
              <g
                v-for="node in props.relationGraph.nodes"
                :key="node.id"
                :class="['zw-rel-node', `is-${node.kind}`]"
                @click="handleSelectPalace(node.palaceName)"
              >
                <circle :cx="node.x" :cy="node.y" :r="node.kind === 'active' ? 25 : 19" />
                <text :x="node.x" :y="node.y + 2" text-anchor="middle" :title="node.fullLabel">
                  <title>{{ node.fullLabel }}</title>
                  <tspan :x="node.x" :dy="0">{{ node.displayLabel.line1 }}</tspan>
                  <tspan v-if="node.displayLabel.line2" :x="node.x" :dy="14">{{ node.displayLabel.line2 }}</tspan>
                </text>
              </g>
            </svg>
          </div>

          <div class="zw-rel-row">
            <span class="zw-rel-label">对宫</span>
            <span class="zw-rel-oppo">{{ props.relations.opposite }}</span>
          </div>
          <div v-if="props.relations.flyingOutEntries.length" class="zw-rel-row">
            <span class="zw-rel-label">飞出</span>
            <div class="zw-rel-links">
              <button
                v-for="item in props.relations.flyingOutEntries"
                :key="`out-${item.transform}-${item.target}`"
                type="button"
                class="zw-link-chip out"
                @click="handleSelectPalace(item.target)"
              >
                {{ item.transform }} → {{ item.target }}
              </button>
            </div>
          </div>
          <div v-if="props.relations.receiving.length" class="zw-rel-row">
            <span class="zw-rel-label">流入</span>
            <div class="zw-rel-links">
              <button
                v-for="item in props.relations.receiving"
                :key="`in-${item.src}-${item.transform}`"
                type="button"
                class="zw-link-chip in"
                @click="handleSelectPalace(item.src)"
              >
                {{ item.src }} → {{ item.transform }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.zw-section {
  padding: 16px 24px;
}
.zw-sec-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  letter-spacing: .01em;
}
.zw-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 1fr);
  gap: 14px;
}
.zw-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.zw-cell {
  appearance: none;
  width: 100%;
  text-align: left;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 12px;
  padding: 10px 11px;
  cursor: pointer;
  transition: transform .12s, box-shadow .12s, border-color .12s;
}
.zw-cell:hover,
.zw-cell.active {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(124,77,171,.10);
  border-color: #c4b5fd;
}
.zw-cell.highlighted {
  border-color: #22c55e;
  box-shadow: 0 0 0 2px rgba(34,197,94,.16);
}
.zw-cell-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.zw-cell-name { font-size: 12px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.zw-cell-gz { font-size: 11px; color: var(--text-3); font-family: var(--font-cn); }
.zw-cell-stars {
  margin-top: 8px;
  min-height: 42px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-2);
  font-family: var(--font-cn);
}
.zw-cell-foot {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-3);
}
.zw-cell-tag {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dcfce7;
  color: #15803d;
  font-size: 10px;
  font-weight: 700;
}
.zw-focus {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 14px 16px;
}
.zw-focus-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}
.zw-star-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}
.zw-star-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: var(--surface-2, #f8fafc);
}
.zw-star-name { font-size: 13px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.zw-star-meta { font-size: 11px; color: var(--text-3); text-align: right; }
.zw-focus-copy {
  margin-top: 12px;
  color: var(--text-2);
  line-height: 1.8;
  font-family: var(--font-cn);
}
.zw-suggestion {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
  color: var(--text);
}
.zw-relations {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
  display: flex;
  flex-direction: column;
  font-family: var(--font-cn);
}
.zw-rel-graph-wrap { margin-bottom: 12px; }
.zw-rel-graph {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(124,77,171,.04), rgba(99,102,241,.02));
}
.zw-rel-ring {
  fill: none;
  stroke-width: 1.5;
}
.zw-rel-ring.inner { stroke: rgba(124,77,171,.2); }
.zw-rel-ring.outer { stroke: rgba(99,102,241,.16); }
.zw-rel-line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .9;
}
.zw-rel-line.is-opposite { stroke: #7c3aed; stroke-dasharray: 4 4; }
.zw-rel-line.is-out { stroke: #4f46e5; }
.zw-rel-line.is-in { stroke: #0f766e; }
.zw-rel-arrow { stroke: none; }
.zw-rel-arrow.out { fill: #4f46e5; }
.zw-rel-arrow.in { fill: #0f766e; }
.zw-rel-line-label {
  font-size: 10px;
  font-weight: 700;
  paint-order: stroke;
  stroke: rgba(255,255,255,.92);
  stroke-width: 3px;
  font-family: var(--font-cn);
}
.zw-rel-line-label.is-opposite { fill: #7c3aed; }
.zw-rel-line-label.is-out { fill: #4f46e5; }
.zw-rel-line-label.is-in { fill: #0f766e; }
.zw-rel-node { cursor: pointer; }
.zw-rel-node circle {
  stroke-width: 2;
  transition: transform .12s, filter .12s;
}
.zw-rel-node.is-active circle { transform: scale(1.03); }
.zw-rel-node text {
  font-size: 11px;
  font-weight: 700;
  fill: #fff;
  font-family: var(--font-cn);
  pointer-events: none;
}
.zw-rel-node:hover circle { filter: brightness(1.04); }
.zw-rel-node.is-active circle { fill: #7c3aed; stroke: #5b21b6; }
.zw-rel-node.is-opposite circle { fill: #a78bfa; stroke: #7c3aed; }
.zw-rel-node.is-out circle { fill: #818cf8; stroke: #4f46e5; }
.zw-rel-node.is-in circle { fill: #2dd4bf; stroke: #0f766e; }
.zw-rel-row {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 10px;
  align-items: start;
}
.zw-rel-label {
  font-size: 11px;
  color: var(--text-3);
  font-weight: 700;
  padding-top: 5px;
}
.zw-rel-oppo {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f5f3ff;
  color: #6d28d9;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-cn);
  width: fit-content;
}
.zw-rel-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.zw-link-chip {
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-2, #f8fafc);
  color: var(--text-2);
  padding: 6px 10px;
  font-size: 12px;
  font-family: var(--font-cn);
  cursor: pointer;
  transition: transform .12s, box-shadow .12s, border-color .12s;
}
.zw-link-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(15,23,42,.08);
}
.zw-link-chip.out {
  background: #eef2ff;
  color: #4338ca;
  border-color: #c7d2fe;
}
.zw-link-chip.in {
  background: #ecfeff;
  color: #0f766e;
  border-color: #a5f3fc;
}
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

@media (max-width: 900px) {
  .zw-layout { grid-template-columns: 1fr; }
  .zw-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .zw-grid { grid-template-columns: repeat(2, 1fr); }
  .zw-star-item { flex-direction: column; align-items: flex-start; }
  .zw-star-meta { text-align: left; }
  .zw-rel-row { grid-template-columns: 1fr; gap: 6px; }
}

@media (max-width: 560px) {
  .zw-grid { grid-template-columns: 1fr; }
  .zw-sec-title { flex-wrap: wrap; gap: 6px; }
}
</style>
