<script setup lang="ts">
interface LiunianTimelineItem {
  year: number
  stem: string
  branch: string
  ten_god?: string | null
  annualScore?: number | null
  isCurrent: boolean
  stemColor?: string
  branchColor?: string
  clash?: string
  optimalAction?: string
  tags?: string[]
}

interface LiunianDomainItem {
  key: string
  val: string
}

interface ActiveLiunianItem extends LiunianTimelineItem {}

interface DayunInfoItem {
  ganzhi: string
  startAge?: number | null
  endAge?: number | null
  isActive: boolean
  isPast: boolean
}

interface SparklinePoint {
  x: number
  y: number
  s: number
}

interface SparklineData {
  w: number
  h: number
  pts: SparklinePoint[]
  line: string
  area: string
}

const props = defineProps<{
  currentYear: number
  items: LiunianTimelineItem[]
  activeItem?: ActiveLiunianItem | null
  activeDayunInfo?: DayunInfoItem | null
  activeDomains?: LiunianDomainItem[]
  sparkline?: SparklineData | null
}>()

const emit = defineEmits<{
  (e: 'selectYear', year: number): void
}>()
</script>

<template>
  <section class="wb-section">
    <h2 class="wb-sec-title">流年 <span class="wb-sec-note">近 5 年</span></h2>

    <div v-if="props.activeItem" class="wb-fortune-focus wb-liunian-focus">
      <div class="wb-fortune-focus-head">
        <div>
          <div class="wb-fortune-focus-title">{{ props.activeItem.year }} · {{ props.activeItem.stem }}{{ props.activeItem.branch }}</div>
          <div class="wb-fortune-focus-sub">{{ props.activeItem.ten_god || '—' }}<template v-if="props.activeItem.annualScore != null"> ｜ 年度分：{{ props.activeItem.annualScore }}</template></div>
        </div>
        <span class="wb-fortune-badge" :class="props.activeItem.isCurrent ? 'is-active' : props.activeItem.year < props.currentYear ? 'is-past' : 'is-future'">
          {{ props.activeItem.isCurrent ? '当前流年' : props.activeItem.year < props.currentYear ? '已过流年' : '未来流年' }}
        </span>
      </div>
      <div class="wb-chip-list" style="margin-top: 10px;">
        <span v-if="props.activeItem.clash" class="wb-chip bad">冲克：{{ props.activeItem.clash }}</span>
        <span v-if="props.activeItem.optimalAction" class="wb-chip good">建议：{{ props.activeItem.optimalAction }}</span>
        <span v-for="tag in (props.activeItem.tags ?? []).slice(0, 3)" :key="tag" class="wb-chip">{{ tag }}</span>
      </div>
      <div v-if="props.activeDayunInfo" class="wb-liunian-dayun-ctx">
        <span class="wb-ldc-label">所处大运</span>
        <span class="wb-ldc-gz">{{ props.activeDayunInfo.ganzhi }}</span>
        <span class="wb-ldc-age">{{ props.activeDayunInfo.startAge }}–{{ props.activeDayunInfo.endAge }}岁</span>
        <span v-if="props.activeDayunInfo.isActive" class="wb-ldc-tag">进行中</span>
        <span v-else-if="props.activeDayunInfo.isPast" class="wb-ldc-tag past">已过</span>
        <span v-else class="wb-ldc-tag future">未来</span>
      </div>
      <div v-if="props.activeDomains?.length" class="wb-liunian-domain-row">
        <div v-for="d in props.activeDomains.slice(0, 3)" :key="d.key" class="wb-ldn-item">
          <span class="wb-ldn-key">{{ d.key }}</span>
          <span class="wb-ldn-val">{{ d.val }}</span>
        </div>
      </div>
    </div>

    <div v-if="props.sparkline" class="wb-liunian-sparkline-wrap">
      <svg class="wb-liunian-sparkline" :viewBox="`0 0 ${props.sparkline.w} ${props.sparkline.h}`" preserveAspectRatio="none">
        <path :d="props.sparkline.area" class="wb-spark-area" />
        <path :d="props.sparkline.line" class="wb-spark-line" />
        <circle
          v-for="pt in props.sparkline.pts"
          :key="pt.x"
          :cx="pt.x"
          :cy="pt.y"
          r="3"
          class="wb-spark-dot"
        >
          <title>{{ pt.s }}分</title>
        </circle>
      </svg>
    </div>

    <div class="wb-liunian-grid wb-liunian-grid-rich">
      <button
        v-for="ly in props.items"
        :key="ly.year"
        type="button"
        class="wb-ly-cell"
        :class="{ current: ly.isCurrent, selected: ly.year === props.activeItem?.year }"
        @click="emit('selectYear', ly.year)"
      >
        <span class="wb-ly-year">{{ ly.year }}</span>
        <span class="wb-ly-gz">
          <span :style="{ color: ly.stemColor }">{{ ly.stem }}</span>
          <span :style="{ color: ly.branchColor }">{{ ly.branch }}</span>
        </span>
        <span class="wb-ly-sg">{{ ly.ten_god }}</span>
        <span v-if="ly.annualScore != null" class="wb-ly-score">{{ ly.annualScore }}分</span>
      </button>
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

.wb-fortune-focus {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(99,102,241,.05), transparent 52%), var(--surface);
  padding: 14px 16px;
  margin-bottom: 12px;
}

.wb-fortune-focus-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.wb-fortune-focus-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}

.wb-fortune-focus-sub {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 4px;
}

.wb-fortune-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.wb-fortune-badge.is-active { background: #e0e7ff; color: #4338ca; }
.wb-fortune-badge.is-past { background: #f1f5f9; color: #475569; }
.wb-fortune-badge.is-future { background: #ecfeff; color: #0f766e; }

.wb-chip-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

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

.wb-liunian-dayun-ctx {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 10px;
  background: var(--surface-2, #f8fafc);
  border-radius: 8px;
  border: 1px solid var(--border);
  font-size: 12px;
  font-family: var(--font-cn);
}

.wb-ldc-label { color: var(--text-3); font-size: 11px; }
.wb-ldc-gz { font-weight: 700; color: var(--text-1); }
.wb-ldc-age { color: var(--text-3); font-size: 11px; }
.wb-ldc-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1e40af;
}
.wb-ldc-tag.past { background: #f3f4f6; color: var(--text-3); }
.wb-ldc-tag.future { background: #f0fdf4; color: #166534; }

.wb-liunian-domain-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.wb-ldn-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-width: 80px;
  flex: 1;
}

.wb-ldn-key { font-size: 10px; color: var(--text-3); font-weight: 700; }
.wb-ldn-val { font-size: 12px; color: var(--text-1); font-family: var(--font-cn); line-height: 1.5; }

.wb-liunian-sparkline-wrap {
  margin-bottom: 12px;
  padding: 6px 10px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.wb-liunian-sparkline { width: 100%; height: 36px; display: block; overflow: visible; }
.wb-spark-area { fill: rgba(99,102,241,.1); }
.wb-spark-line { fill: none; stroke: #6366f1; stroke-width: 1.8; stroke-linejoin: round; stroke-linecap: round; }
.wb-spark-dot { fill: #6366f1; }

.wb-liunian-grid-rich { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.wb-ly-cell {
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 14px 10px;
  text-align: center;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: transform var(--dur-fast), box-shadow var(--dur-fast), border-color var(--dur-fast);
}
.wb-ly-cell.current {
  border-color: var(--accent);
  background: linear-gradient(180deg, rgba(99,102,241,.05), transparent 60%), var(--surface);
}
.wb-ly-cell.selected { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(99,102,241,.14); }
.wb-ly-year { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); }
.wb-ly-gz { font-size: 18px; font-weight: 700; font-family: var(--font-cn); }
.wb-ly-sg { font-size: 11px; color: var(--text-3); }
.wb-ly-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: #4338ca;
  background: #eef2ff;
  align-self: center;
}

@media (max-width: 1280px) {
  .wb-liunian-grid-rich { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 840px) {
  .wb-fortune-focus-head { flex-direction: column; }
  .wb-liunian-grid-rich { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .wb-liunian-grid-rich { grid-template-columns: 1fr; }
}
</style>
