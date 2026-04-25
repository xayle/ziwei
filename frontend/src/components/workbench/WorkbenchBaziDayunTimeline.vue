<script setup lang="ts">
interface DayunTimelineItem {
  stem?: string | null
  branch?: string | null
  ganzhi: string
  startYear?: number | null
  endYear?: number | null
  startAge?: number | null
  endAge?: number | null
  isActive: boolean
  isPast: boolean
  progress: number
  ten_god?: string | null
  flow_wuxing?: string | null
  wealth_hint?: string | null
  love_hint?: string | null
  health_hint?: string | null
  narrative?: string | null
  stemColor?: string
  branchColor?: string
}

const props = defineProps<{
  items: DayunTimelineItem[]
  activeItem?: DayunTimelineItem | null
}>()

const emit = defineEmits<{
  (e: 'selectDayun', startYear: number | null): void
}>()
</script>

<template>
  <section class="wb-section">
    <h2 class="wb-sec-title">大运时间轴</h2>

    <div v-if="props.activeItem" class="wb-fortune-focus wb-dayun-focus">
      <div class="wb-fortune-focus-head">
        <div>
          <div class="wb-fortune-focus-title">{{ props.activeItem.ganzhi }}</div>
          <div class="wb-fortune-focus-sub">
            {{ props.activeItem.startYear ?? '—' }}<template v-if="props.activeItem.endYear != null"> - {{ props.activeItem.endYear }}</template>
            ｜ {{ props.activeItem.startAge ?? '—' }}<template v-if="props.activeItem.endAge != null"> - {{ props.activeItem.endAge }}</template> 岁
          </div>
        </div>
        <span class="wb-fortune-badge" :class="props.activeItem.isActive ? 'is-active' : props.activeItem.isPast ? 'is-past' : 'is-future'">
          {{ props.activeItem.isActive ? '当前大运' : props.activeItem.isPast ? '已走过' : '未来大运' }}
        </span>
      </div>
      <div class="wb-chip-list" style="margin-top: 10px;">
        <span v-if="props.activeItem.ten_god" class="wb-chip">十神：{{ props.activeItem.ten_god }}</span>
        <span v-if="props.activeItem.flow_wuxing" class="wb-chip good">五行：{{ props.activeItem.flow_wuxing }}</span>
        <span v-if="props.activeItem.wealth_hint" class="wb-chip">财运：{{ props.activeItem.wealth_hint }}</span>
        <span v-if="props.activeItem.love_hint" class="wb-chip">情感：{{ props.activeItem.love_hint }}</span>
        <span v-if="props.activeItem.health_hint" class="wb-chip bad">健康：{{ props.activeItem.health_hint }}</span>
      </div>
      <div v-if="props.activeItem.narrative" class="wb-fortune-focus-copy">{{ props.activeItem.narrative }}</div>
    </div>

    <div class="wb-dayun-axis wb-dayun-axis-rich">
      <button
        v-for="(d, i) in props.items"
        :key="i"
        type="button"
        class="wb-dayun-cell"
        :class="{
          active: d.isActive,
          past: d.isPast,
          future: !d.isActive && !d.isPast,
          selected: d.startYear === props.activeItem?.startYear,
        }"
        @click="emit('selectDayun', d.startYear ?? null)"
      >
        <div class="wb-dayun-dot" />
        <div class="wb-dayun-gz">
          <span :style="{ color: d.stemColor }">{{ d.stem }}</span>
          <span :style="{ color: d.branchColor }">{{ d.branch }}</span>
        </div>
        <div class="wb-dayun-year">{{ d.startYear ?? '—' }}<template v-if="d.endYear != null">-{{ d.endYear }}</template></div>
        <div class="wb-dayun-age">{{ d.startAge ?? '—' }}岁起</div>
        <div class="wb-dayun-progress"><span :style="{ width: `${d.progress}%` }" /></div>
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

.wb-fortune-focus-copy {
  margin-top: 10px;
  color: var(--text-2);
  line-height: 1.8;
  font-family: var(--font-cn);
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

.wb-dayun-axis {
  display: flex;
  gap: 0;
  overflow-x: auto;
}

.wb-dayun-axis-rich {
  padding: 8px 0 2px;
}

.wb-dayun-cell {
  appearance: none;
  flex: 1;
  min-width: 118px;
  border: 1px solid var(--border);
  border-right: none;
  background: var(--surface);
  padding: 14px 10px 12px;
  text-align: center;
  cursor: pointer;
  transition: background var(--dur-fast), transform var(--dur-fast), box-shadow var(--dur-fast);
  position: relative;
}

.wb-dayun-cell:last-child { border-right: 1px solid var(--border); }
.wb-dayun-cell.active {
  background: var(--accent-lt);
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
  position: relative;
  z-index: 1;
}

.wb-dayun-cell.selected { transform: translateY(-2px); }
.wb-dayun-cell.past { background: #f8fafc; }
.wb-dayun-cell.future { background: #fcfcfd; }

.wb-dayun-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--border);
  position: absolute;
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.wb-dayun-cell.active .wb-dayun-dot { background: var(--accent); box-shadow: 0 0 0 4px var(--accent-glow); }
.wb-dayun-gz { font-size: 18px; font-weight: 700; font-family: var(--font-cn); line-height: 1.2; }
.wb-dayun-year { font-size: 10px; color: var(--text-3); font-family: var(--font-mono); margin-top: 4px; }
.wb-dayun-age { font-size: 11px; color: var(--accent-dark); margin-top: 2px; }

.wb-dayun-progress {
  width: 100%;
  height: 4px;
  border-radius: 999px;
  background: rgba(148,163,184,.2);
  margin-top: 10px;
  overflow: hidden;
}

.wb-dayun-progress > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #818cf8, #6366f1);
}

@media (max-width: 840px) {
  .wb-fortune-focus-head { flex-direction: column; }
  .wb-dayun-cell { min-width: 102px; }
}
</style>
