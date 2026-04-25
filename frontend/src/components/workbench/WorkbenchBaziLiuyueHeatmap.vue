<script setup lang="ts">
interface LiuyueTrendPoint {
  x: number
  y: number
  color: string
  label: string
}

interface LiuyueTrendData {
  w: number
  h: number
  pts: LiuyueTrendPoint[]
}

interface LiuyueHeatmapItem {
  month: number
  month_ganzhi?: string | null
  month_dizhi?: string | null
  luck_level: string
  heatBar: string
  heatBg: string
  isSelected: boolean
  isCurrent: boolean
  isLinked: boolean
  tip?: string | null
}

interface LiuyueDetailItem {
  month: number
  month_ganzhi?: string | null
  month_dizhi?: string | null
  luck_level: string
  color_hint?: string | null
  dayun_stem?: string | null
  relation_to_rizhu?: string | null
  clash_with?: string | null
  tip?: string | null
  disclaimer?: string | null
}

const props = defineProps<{
  currentYear: number
  heatmapItems: LiuyueHeatmapItem[]
  trendData?: LiuyueTrendData | null
  activeDetail?: LiuyueDetailItem | null
  linkedMonths: number[]
  showCurrentYearLinkHint: boolean
}>()

const emit = defineEmits<{
  (e: 'selectMonth', month: number): void
}>()
</script>

<template>
  <section class="wb-section">
    <h2 class="wb-sec-title">
      流月热力 <span class="wb-sec-note">{{ props.currentYear }}年</span>
      <span class="wb-lm-legend">
        <span class="wb-lm-leg-item wb-lm-leg-good">吉</span>
        <span class="wb-lm-leg-item wb-lm-leg-mid">平</span>
        <span class="wb-lm-leg-item wb-lm-leg-bad">凶</span>
      </span>
    </h2>

    <div v-if="props.trendData" class="wb-lm-trend-wrap">
      <svg
        :width="props.trendData.w"
        :height="props.trendData.h"
        class="wb-lm-trend-svg"
        :viewBox="`0 0 ${props.trendData.w} ${props.trendData.h}`"
      >
        <polyline
          :points="props.trendData.pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')"
          fill="none"
          stroke="var(--border)"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
        <circle
          v-for="(p, i) in props.trendData.pts"
          :key="i"
          :cx="p.x.toFixed(1)"
          :cy="p.y.toFixed(1)"
          r="4"
          :fill="p.color"
          stroke="white"
          stroke-width="1.5"
        >
          <title>{{ p.label }}</title>
        </circle>
      </svg>
    </div>

    <div class="wb-liuyue-grid">
      <button
        v-for="m in props.heatmapItems"
        :key="m.month"
        type="button"
        class="wb-lm-hm-cell"
        :class="{
          'lm-hm-current': m.isCurrent,
          'lm-hm-active': m.isSelected,
          'lm-hm-linked': m.isLinked,
        }"
        :style="{ '--hm-bar': m.heatBar, '--hm-bg': m.heatBg }"
        :title="m.tip ?? ''"
        @click="emit('selectMonth', m.month)"
      >
        <span class="wb-lm-hm-bar" />
        <span class="wb-lm-hm-month">{{ m.month }}月</span>
        <span class="wb-lm-hm-gz">{{ m.month_ganzhi ?? m.month_dizhi }}</span>
        <span class="wb-lm-hm-level">{{ m.luck_level }}</span>
      </button>
    </div>

    <div v-if="props.activeDetail" class="wb-liuyue-detail">
      <div class="wb-liuyue-head">
        <div>
          <div class="wb-liuyue-title">{{ props.activeDetail.month }}月 · {{ props.activeDetail.month_ganzhi ?? props.activeDetail.month_dizhi }}</div>
          <div class="wb-liuyue-meta">
            <span :class="['wb-chip', props.activeDetail.luck_level === '吉' ? 'good' : props.activeDetail.luck_level === '凶' ? 'bad' : '']">{{ props.activeDetail.luck_level }}</span>
            <span v-if="props.linkedMonths.includes(props.activeDetail.month)" class="wb-chip good">流年关键月</span>
            <span v-if="props.activeDetail.color_hint" class="wb-chip">宜色：{{ props.activeDetail.color_hint }}</span>
            <span v-if="props.activeDetail.dayun_stem" class="wb-chip">大运天干：{{ props.activeDetail.dayun_stem }}</span>
          </div>
        </div>
        <div class="wb-liuyue-side">
          <span v-if="props.activeDetail.relation_to_rizhu" class="wb-liuyue-rel">{{ props.activeDetail.relation_to_rizhu }}</span>
          <span v-if="props.activeDetail.clash_with" class="wb-liuyue-clash">冲：{{ props.activeDetail.clash_with }}</span>
        </div>
      </div>
      <div class="wb-liuyue-tip">{{ props.activeDetail.tip || '本月暂无额外提示。' }}</div>
      <div v-if="props.showCurrentYearLinkHint" class="wb-liuyue-disclaimer">当前流月为 {{ props.currentYear }} 年数据；仅当展开 {{ props.currentYear }} 年流年详情时，关键月份会同步高亮。</div>
      <div v-if="props.activeDetail.disclaimer" class="wb-liuyue-disclaimer">{{ props.activeDetail.disclaimer }}</div>
    </div>
  </section>
</template>

<style scoped>
.wb-section {
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.88));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: var(--shadow-xs);
}

.wb-sec-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 800;
  margin: 0 0 14px;
  color: var(--text-1);
}

.wb-sec-note { font-size: 11px; color: var(--text-3); font-weight: 400; }

.wb-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  border-radius: 999px;
  padding: 0 10px;
  font-size: 12px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  font-family: var(--font-cn);
}

.wb-chip.good { color: #166534; background: #ecfdf5; border-color: #bbf7d0; }
.wb-chip.bad { color: #991b1b; background: #fef2f2; border-color: #fecaca; }

.wb-liuyue-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.wb-lm-trend-wrap {
  margin-bottom: 12px;
  padding: 8px 10px 4px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.wb-lm-trend-svg { display: block; width: 100%; max-width: 360px; height: 28px; }

.wb-lm-legend {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.wb-lm-leg-item {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 10px;
  border: 1px solid var(--border);
}

.wb-lm-leg-good { color: #166534; background: #ecfdf5; border-color: #bbf7d0; }
.wb-lm-leg-mid { color: #92400e; background: #fffbeb; border-color: #fde68a; }
.wb-lm-leg-bad { color: #991b1b; background: #fef2f2; border-color: #fecaca; }

.wb-lm-hm-cell {
  position: relative;
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: linear-gradient(180deg, var(--hm-bg, rgba(99,102,241,.08)), rgba(255,255,255,.94));
  padding: 12px 10px 10px;
  min-height: 82px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: transform var(--dur-fast), box-shadow var(--dur-fast), border-color var(--dur-fast);
}

.wb-lm-hm-cell:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.wb-lm-hm-cell.lm-hm-current { border-color: var(--hm-bar, var(--accent)); box-shadow: 0 0 0 2px color-mix(in srgb, var(--hm-bar, var(--accent)) 30%, transparent); }
.wb-lm-hm-cell.lm-hm-active { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,.15); border-color: var(--hm-bar, var(--accent)); }
.wb-lm-hm-cell.lm-hm-linked { border-style: dashed; border-color: var(--accent); }
.wb-lm-hm-cell.lm-hm-linked::after {
  content: '●';
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10px;
  color: var(--accent);
}

.wb-lm-hm-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 12px 12px 0 0;
  background: var(--hm-bar, var(--accent));
}

.wb-lm-hm-month { font-size: 12px; color: var(--text-3); margin-top: 2px; }
.wb-lm-hm-gz { font-size: 13px; font-weight: 700; font-family: var(--font-cn); color: var(--text-1); }
.wb-lm-hm-level { font-size: 11px; font-weight: 700; color: var(--text-2); }

.wb-liuyue-detail {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(99,102,241,.05), transparent 55%), var(--surface);
}

.wb-liuyue-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.wb-liuyue-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-1);
  font-family: var(--font-cn);
}

.wb-liuyue-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.wb-liuyue-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.wb-liuyue-rel,
.wb-liuyue-clash {
  font-size: 12px;
  border-radius: 999px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.wb-liuyue-tip {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.wb-liuyue-disclaimer {
  margin-top: 10px;
  font-size: 11px;
  color: var(--text-3);
  line-height: 1.7;
}

@media (max-width: 1280px) {
  .wb-liuyue-grid { grid-template-columns: repeat(4, 1fr); }
  .wb-lm-trend-svg { max-width: 100%; }
  .wb-lm-legend { margin-left: 4px; }
}

@media (max-width: 840px) {
  .wb-liuyue-grid { grid-template-columns: repeat(3, 1fr); }
  .wb-liuyue-head { flex-direction: column; }
  .wb-liuyue-side { align-items: flex-start; }
}

@media (max-width: 640px) {
  .wb-liuyue-detail { padding: 12px; }
}

@media (max-width: 520px) {
  .wb-liuyue-grid { grid-template-columns: repeat(2, 1fr); }
  .wb-lm-legend { width: 100%; margin-left: 0; }
  .wb-lm-trend-wrap { margin-bottom: 8px; }
  .wb-lm-trend-svg { height: 24px; }
}
</style>
