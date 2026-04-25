<script setup lang="ts">
const WUXING_COLORS: Record<string, string> = {
  木: '#66bb6a',
  火: '#ef5350',
  土: '#ab47bc',
  金: '#ffb74d',
  水: '#29b6f6',
}

type PillarKey = 'year' | 'month' | 'day' | 'hour'

interface PillarItem {
  key: PillarKey
  label: string
  stem: string
  branch: string
  shishen?: string
  stemColor?: string
  branchColor?: string
}

interface StrengthInfo {
  score?: number | null
  tier?: string | null
}

interface ActivePillarDetail {
  label?: string
  canggan?: string | null
  nayin?: string | null
}

interface WuxingItem {
  key: string
  val: number
}

interface CangganNayinRow {
  label: string
  canggan?: string | null
  nayin?: string | null
}

interface DayunItem {
  start_year?: number | null
  stem?: string
  branch?: string
}

const props = withDefaults(defineProps<{
  mode?: 'overview' | 'hotfix'
  caseName?: string
  birthLocalText: string
  genderText?: string
  city?: string | null
  tz?: string | null
  lon?: number | string | null
  summaryText?: string | null
  pillars: PillarItem[]
  activePillarKey?: PillarKey | null
  strength?: StrengthInfo | null
  tenGodsText?: string | null
  activePillarDetail?: ActivePillarDetail | null
  wuxing: WuxingItem[]
  wuxingMax: number
  cangganNayinRows?: CangganNayinRow[]
  zodiacText?: string | null
  gejuName?: string | null
  favorText?: string | null
  avoidText?: string | null
  shenshaSummaryText?: string | null
  dayunItems: DayunItem[]
}>(), {
  mode: 'overview',
  caseName: '',
  genderText: '',
  city: '',
  tz: '',
  lon: null,
  summaryText: '',
  activePillarKey: null,
  strength: null,
  tenGodsText: '',
  activePillarDetail: null,
  cangganNayinRows: () => [],
  zodiacText: '',
  gejuName: '',
  favorText: '',
  avoidText: '',
  shenshaSummaryText: '',
})

const emit = defineEmits<{
  (e: 'selectPillar', key: PillarKey): void
}>()

function getWuxingColor(key: string) {
  return WUXING_COLORS[key] ?? '#94a3b8'
}

function formatLon(value: number | string | null | undefined) {
  return value === null || value === undefined || value === '' ? '—' : `${value}° E`
}
</script>

<template>
  <div class="wb-merged-stack">
    <template v-if="props.mode === 'overview'">
      <div class="wb-data-panel">
        <h2 class="wb-section-title">1.1 生辰数据</h2>
        <div class="wb-info-row"><span class="wb-label">案例姓名</span><span class="wb-value">{{ props.caseName || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">出生时间</span><span class="wb-value">{{ props.birthLocalText }}</span></div>
        <div class="wb-info-row"><span class="wb-label">性别</span><span class="wb-value">{{ props.genderText || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">城市 / 时区</span><span class="wb-value">{{ props.city || '—' }} / {{ props.tz || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">经度</span><span class="wb-value">{{ formatLon(props.lon) }}</span></div>
        <div class="wb-info-row"><span class="wb-label">摘要</span><span class="wb-value">{{ props.summaryText || '命盘已加载，可继续查看四柱与五行。' }}</span></div>
      </div>
    </template>

    <template v-else>
      <div class="wb-data-panel">
        <h2 class="wb-section-title">基础信息</h2>
        <div class="wb-info-row"><span class="wb-label">出生时间</span><span class="wb-value">{{ props.birthLocalText }}</span></div>
        <div class="wb-info-row"><span class="wb-label">城市 / 时区</span><span class="wb-value">{{ props.city || '—' }} / {{ props.tz || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">经度</span><span class="wb-value">{{ formatLon(props.lon) }}</span></div>
        <div class="wb-info-row"><span class="wb-label">格局</span><span class="wb-value">{{ props.gejuName || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">用神</span><span class="wb-value">{{ props.favorText || '—' }}</span></div>
      </div>
    </template>

    <div class="wb-data-panel">
      <h2 class="wb-section-title">四柱与十神</h2>
      <div v-if="props.pillars.length" class="wb-pillars-grid">
        <button
          v-for="p in props.pillars"
          :key="`${props.mode}-${p.key}`"
          type="button"
          class="wb-pillar-card"
          :class="{ active: p.key === props.activePillarKey }"
          @click="emit('selectPillar', p.key)"
        >
          <div class="wb-pillar-label">{{ p.label }}</div>
          <div class="wb-pillar-main">
            <span :style="{ color: p.stemColor }" class="wb-stem">{{ p.stem }}</span>
            <span :style="{ color: p.branchColor }" class="wb-branch">{{ p.branch }}</span>
          </div>
          <div class="wb-pillar-shishen">{{ p.shishen }}</div>
        </button>
      </div>
      <div v-else class="wb-empty-hint">暂无四柱数据</div>
      <div class="wb-info-row" style="margin-top:10px;"><span class="wb-label">日主强弱</span><span class="wb-value">{{ props.strength ? `${props.strength.score}（${props.strength.tier}）` : '—' }}</span></div>
      <div class="wb-info-row"><span class="wb-label">十神概览</span><span class="wb-value">{{ props.tenGodsText || '—' }}</span></div>
      <div v-if="props.mode === 'overview' && props.activePillarDetail" class="wb-pillar-inline-note">当前查看：{{ props.activePillarDetail.label }} · 藏干 {{ props.activePillarDetail.canggan }} · 纳音 {{ props.activePillarDetail.nayin }}</div>
    </div>

    <div class="wb-data-panel">
      <h2 class="wb-section-title">{{ props.mode === 'overview' ? '1.3 五行与藏干' : '五行分布' }}</h2>
      <div v-if="props.wuxing.length" class="wb-wuxing-bars">
        <div v-for="w in props.wuxing" :key="`${props.mode}-${w.key}`" class="wb-wuxing-item">
          <div class="wb-wuxing-label">{{ w.key }}</div>
          <div class="wb-wuxing-bar-container"><div class="wb-wuxing-bar" :style="{ width: `${(w.val / props.wuxingMax) * 100}%`, backgroundColor: getWuxingColor(w.key) }" /></div>
          <div class="wb-wuxing-value">{{ w.val }}</div>
        </div>
      </div>
      <div v-else class="wb-empty-hint">暂无五行数据</div>

      <template v-if="props.mode === 'overview'">
        <div class="wb-list-panel">
          <div v-for="(row, idx) in props.cangganNayinRows" :key="idx" class="wb-list-item">{{ row.label }} · 藏干：{{ row.canggan || '—' }} · 纳音：{{ row.nayin }}</div>
        </div>
        <div class="wb-info-row" style="margin-top:10px;"><span class="wb-label">生肖</span><span class="wb-value">{{ props.zodiacText || '—' }}</span></div>
      </template>
    </div>

    <div class="wb-data-panel">
      <h2 class="wb-section-title">{{ props.mode === 'overview' ? '1.4 格局与大运' : '大运摘要' }}</h2>
      <template v-if="props.mode === 'overview'">
        <div class="wb-info-row"><span class="wb-label">格局</span><span class="wb-value">{{ props.gejuName || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">用神</span><span class="wb-value">{{ props.favorText || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">忌神</span><span class="wb-value">{{ props.avoidText || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">神煞概览</span><span class="wb-value">{{ props.shenshaSummaryText || '—' }}</span></div>
      </template>
      <template v-else>
        <div class="wb-info-row"><span class="wb-label">神煞概览</span><span class="wb-value">{{ props.shenshaSummaryText || '—' }}</span></div>
        <div class="wb-info-row"><span class="wb-label">运势摘要</span><span class="wb-value">{{ props.summaryText || '—' }}</span></div>
      </template>
      <div v-if="props.dayunItems.length" class="wb-dayun-list" style="margin-top: 10px;">
        <div v-for="(d, idx) in props.dayunItems.slice(0, 6)" :key="`${props.mode}-dayun-${idx}`" class="wb-dayun-item">
          <span class="wb-dayun-label">{{ d.start_year ? `${d.start_year}年起` : '起运' }}</span>
          <span class="wb-dayun-value">{{ d.stem }}{{ d.branch }}</span>
        </div>
      </div>
      <div v-else class="wb-empty-hint">暂无大运数据</div>
    </div>
  </div>
</template>

<style scoped>
.wb-merged-stack {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.wb-data-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px 28px;
}

.wb-section-title {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: var(--text);
  font-family: var(--font-cn);
  font-weight: 600;
}

.wb-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.wb-info-row:last-child { border-bottom: none; }

.wb-label {
  color: var(--text-3);
  font-weight: 500;
  min-width: 90px;
  font-family: var(--font-cn);
}

.wb-value {
  color: var(--text);
  flex: 1;
  font-family: var(--font-cn);
}

.wb-pillars-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.wb-pillar-card {
  appearance: none;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform var(--dur-fast), box-shadow var(--dur-fast), border-color var(--dur-fast);
}
.wb-pillar-card:hover,
.wb-pillar-card.active {
  transform: translateY(-2px);
  border-color: #a5b4fc;
  box-shadow: 0 8px 16px rgba(99,102,241,.12);
}

.wb-pillar-label {
  font-size: 11px;
  color: var(--text-3);
  font-weight: 500;
  font-family: var(--font-cn);
}

.wb-pillar-main {
  display: flex;
  gap: 4px;
}

.wb-stem,
.wb-branch {
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-cn);
}

.wb-pillar-shishen {
  font-size: 12px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.wb-pillar-inline-note {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.7;
  font-family: var(--font-cn);
}

.wb-empty-hint {
  text-align: center;
  padding: 40px 16px;
  font-size: 13px;
  color: var(--text-3);
}

.wb-wuxing-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0;
}

.wb-wuxing-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.wb-wuxing-label {
  font-size: 13px;
  color: var(--text);
  font-weight: 600;
  width: 20px;
  font-family: var(--font-cn);
}

.wb-wuxing-bar-container {
  flex: 1;
  height: 18px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 9px;
  overflow: hidden;
}

.wb-wuxing-bar {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 9px;
}

.wb-wuxing-value {
  font-size: 13px;
  color: var(--text-3);
  width: 40px;
  text-align: right;
  font-family: var(--font-mono);
}

.wb-dayun-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wb-dayun-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.wb-dayun-label {
  font-size: 13px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.wb-dayun-value {
  font-size: 16px;
  color: var(--text);
  font-weight: 600;
  font-family: var(--font-cn);
}

.wb-list-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.wb-list-item {
  border: 1px solid var(--border);
  background: var(--surface-2);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

@media (max-width: 768px) {
  .wb-data-panel { padding: 18px 16px; }
  .wb-section-title { font-size: 18px; }
  .wb-pillars-grid { grid-template-columns: repeat(2, 1fr); }
  .wb-info-row { align-items: flex-start; }
}

@media (max-width: 560px) {
  .wb-pillars-grid { grid-template-columns: 1fr; }
  .wb-info-row { flex-direction: column; gap: 6px; }
  .wb-label { min-width: 0; }
}
</style>
