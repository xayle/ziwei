<script setup lang="ts">
interface SihuaColorConfig {
  color: string
  label: string
}

interface SihuaLineItem {
  fromBranchIdx: number
  toBranchIdx: number
  starName: string
  transform: string
  color: string
  label: string
  isSelfHua: boolean
}

const props = defineProps<{
  visible: boolean
  chartMode: string
  lines: SihuaLineItem[]
  colors: Record<string, SihuaColorConfig>
  getPalaceCenter: (branchIdx: number) => { x: number; y: number }
  getCurvedPath: (fromIdx: number, toIdx: number, curveOffset?: number) => string
  getCurvedMidpoint: (fromIdx: number, toIdx: number, curveOffset?: number) => { x: number; y: number }
}>()
</script>

<template>
  <svg
    v-if="visible && lines.length && chartMode === 'sihua'"
    class="sihua-lines-svg"
    viewBox="0 0 100 100"
    preserveAspectRatio="none"
  >
    <defs>
      <marker
        v-for="[transform, config] in Object.entries(colors)"
        :id="`arrow-${config.label}`"
        :key="transform"
        markerWidth="6"
        markerHeight="6"
        refX="5"
        refY="3"
        orient="auto"
        markerUnits="strokeWidth"
      >
        <path d="M0,0 L6,3 L0,6 Z" :fill="config.color" />
      </marker>
    </defs>

    <template v-for="(line, index) in lines" :key="`${line.starName}-${line.transform}-${index}`">
      <g v-if="line.isSelfHua" class="sihua-self">
        <circle
          :cx="getPalaceCenter(line.fromBranchIdx).x"
          :cy="getPalaceCenter(line.fromBranchIdx).y - 8"
          r="5"
          fill="none"
          :stroke="line.color"
          stroke-width="0.8"
          stroke-dasharray="2,1"
        />
        <text
          :x="getPalaceCenter(line.fromBranchIdx).x"
          :y="getPalaceCenter(line.fromBranchIdx).y - 14"
          class="sihua-label"
          :fill="line.color"
        >
          {{ line.label }}
        </text>
      </g>

      <g v-else class="sihua-line">
        <path
          :d="getCurvedPath(line.fromBranchIdx, line.toBranchIdx, 0.12 + index * 0.03)"
          fill="none"
          :stroke="line.color"
          stroke-width="0.6"
          :stroke-dasharray="line.transform === '化忌' ? '2,1' : 'none'"
          :marker-end="`url(#arrow-${line.label})`"
        />
        <circle
          :cx="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + index * 0.03).x"
          :cy="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + index * 0.03).y"
          r="3"
          :fill="line.color"
        />
        <text
          :x="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + index * 0.03).x"
          :y="getCurvedMidpoint(line.fromBranchIdx, line.toBranchIdx, 0.12 + index * 0.03).y + 1"
          class="sihua-label"
          fill="#fff"
        >
          {{ line.label }}
        </text>
      </g>
    </template>

    <g class="sihua-legend" transform="translate(38, 38)">
      <text x="0" y="4" class="sihua-legend-text">自化图示:</text>
      <text x="0" y="10" class="sihua-legend-text">
        <tspan fill="#22c55e">→禄</tspan>
        <tspan fill="#f97316">→权</tspan>
        <tspan fill="#3b82f6">→科</tspan>
        <tspan fill="#ef4444">→忌</tspan>
      </text>
    </g>
  </svg>
</template>

<style scoped>
.sihua-lines-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.sihua-lines-svg .sihua-label {
  font-size: 2.5px;
  font-weight: 700;
  text-anchor: middle;
  dominant-baseline: middle;
  font-family: var(--font-cn);
}

.sihua-lines-svg .sihua-legend-text {
  font-size: 2px;
  fill: var(--text-3);
  font-family: var(--font-cn);
}

.sihua-lines-svg line {
  opacity: 0.85;
  transition: opacity 0.2s ease;
}

.sihua-lines-svg g:hover line,
.sihua-lines-svg g:hover circle {
  opacity: 1;
  stroke-width: 1;
}
</style>
