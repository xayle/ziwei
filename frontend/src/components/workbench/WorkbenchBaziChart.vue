<script setup lang="ts">
type PillarKey = 'year' | 'month' | 'day' | 'hour'

interface PillarItem {
  key: PillarKey
  label: string
  stem: string
  branch: string
  shishen: string
  isDay?: boolean
  stemColor?: string
  branchColor?: string
}

interface StrengthItem {
  score: number
  tier: string
}

interface ShenshaItem {
  name: string
}

interface ActivePillarDetail extends PillarItem {
  nayin?: string
  canggan?: string
  stemWx?: string
  branchWx?: string
  goodShensha: ShenshaItem[]
  badShensha: ShenshaItem[]
}

interface WuxingItem {
  key: string
  val: number
}

interface RadarAxisItem {
  label: string
  x: number
  y: number
  color: string
}

const props = defineProps<{
  pillars: PillarItem[]
  activePillarKey: PillarKey
  activePillarDetail?: ActivePillarDetail | null
  strength?: StrengthItem | null
  strengthBarColor: string
  wuxing: WuxingItem[]
  wuxingMax: number
  wuxingRadarPoints?: string
  wuxingRadarAxes: RadarAxisItem[]
}>()

const emit = defineEmits<{
  (e: 'selectPillar', key: PillarKey): void
}>()
</script>

<template>
  <div class="wb-section wb-bazi-chart-section">
    <h2 class="wb-sec-title">命盘可视化</h2>
    <div class="wb-pillars-row">
      <div class="wb-pillar-table-wrap">
        <table class="wb-pillar-table">
          <thead>
            <tr>
              <td class="wb-pt-head"></td>
              <th
                v-for="p in props.pillars"
                :key="p.label"
                :class="[{ 'day-col': p.isDay, active: p.key === props.activePillarKey }, 'wb-pt-clickable']"
                @click="emit('selectPillar', p.key)"
              >
                {{ p.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="wb-pt-head">天干</td>
              <td
                v-for="p in props.pillars"
                :key="p.label + '-stem'"
                class="wb-pt-cell stem"
                :class="[{ 'day-col': p.isDay, active: p.key === props.activePillarKey }, 'wb-pt-clickable']"
                :style="{ color: p.stemColor }"
                @click="emit('selectPillar', p.key)"
              >
                {{ p.stem }}
              </td>
            </tr>
            <tr>
              <td class="wb-pt-head">地支</td>
              <td
                v-for="p in props.pillars"
                :key="p.label + '-branch'"
                class="wb-pt-cell branch"
                :class="[{ 'day-col': p.isDay, active: p.key === props.activePillarKey }, 'wb-pt-clickable']"
                :style="{ color: p.branchColor }"
                @click="emit('selectPillar', p.key)"
              >
                {{ p.branch }}
              </td>
            </tr>
            <tr>
              <td class="wb-pt-head">十神</td>
              <td
                v-for="p in props.pillars"
                :key="p.label + '-sh'"
                class="wb-pt-cell shishen"
                :class="[{ 'day-col': p.isDay, active: p.key === props.activePillarKey }, 'wb-pt-clickable']"
                @click="emit('selectPillar', p.key)"
              >
                {{ p.shishen }}
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="props.strength" class="wb-strength-row">
          <span class="wb-str-label">日主强度</span>
          <div class="wb-str-bar-wrap">
            <div class="wb-str-bar" :style="{ width: `${props.strength.score}%`, background: props.strengthBarColor }" />
          </div>
          <span class="wb-str-tier">{{ props.strength.tier }}</span>
          <span class="wb-str-score">{{ props.strength.score }}</span>
        </div>

        <div v-if="props.activePillarDetail" class="wb-pillar-detail-card">
          <div class="wb-pillar-detail-head">
            <div>
              <div class="wb-pillar-detail-title">{{ props.activePillarDetail.label }} · {{ props.activePillarDetail.stem }}{{ props.activePillarDetail.branch }}</div>
              <div class="wb-pillar-detail-sub">十神：{{ props.activePillarDetail.shishen }} ｜ 纳音：{{ props.activePillarDetail.nayin }}</div>
            </div>
            <span class="wb-fortune-badge is-active">当前查看</span>
          </div>
          <div class="wb-chip-list" style="margin-top: 10px;">
            <span class="wb-chip">天干五行：{{ props.activePillarDetail.stemWx }}</span>
            <span class="wb-chip">地支五行：{{ props.activePillarDetail.branchWx }}</span>
            <span class="wb-chip good">藏干：{{ props.activePillarDetail.canggan }}</span>
          </div>
          <div v-if="props.activePillarDetail.goodShensha.length || props.activePillarDetail.badShensha.length" class="wb-chip-list" style="margin-top: 10px;">
            <span v-for="s in props.activePillarDetail.goodShensha" :key="`g-${s.name}`" class="wb-chip good">吉 · {{ s.name }}</span>
            <span v-for="s in props.activePillarDetail.badShensha" :key="`b-${s.name}`" class="wb-chip bad">凶 · {{ s.name }}</span>
          </div>
        </div>
      </div>

      <div class="wb-wuxing-wrap">
        <div class="wb-wuxing-chart">
          <div class="wb-wx-title">五行分布</div>
          <div v-for="w in props.wuxing" :key="w.key" class="wb-wx-row">
            <span class="wb-wx-key">{{ w.key }}</span>
            <div class="wb-wx-bar-bg">
              <div
                class="wb-wx-bar"
                :style="{ width: `${(w.val / props.wuxingMax) * 100}%`, background: w.key === '木' ? 'var(--wx-wood)' : w.key === '火' ? 'var(--wx-fire)' : w.key === '土' ? 'var(--wx-earth)' : w.key === '金' ? 'var(--wx-metal)' : 'var(--wx-water)' }"
              />
            </div>
            <span class="wb-wx-val">{{ w.val }}</span>
          </div>
        </div>

        <div v-if="props.wuxingRadarPoints" class="wb-wx-radar-wrap">
          <svg class="wb-wx-radar" viewBox="0 0 140 140">
            <polygon
              v-for="level in [0.25, 0.5, 0.75, 1]"
              :key="level"
              :points="props.wuxing.map((_, i) => {
                const a = (-90 + (360 / props.wuxing.length) * i) * Math.PI / 180
                return `${70 + 54 * level * Math.cos(a)},${70 + 54 * level * Math.sin(a)}`
              }).join(' ')"
              class="wb-wx-radar-grid"
            />
            <line v-for="ax in props.wuxingRadarAxes" :key="ax.label" x1="70" y1="70" :x2="ax.x" :y2="ax.y" class="wb-wx-radar-axis" />
            <polygon :points="props.wuxingRadarPoints" class="wb-wx-radar-poly" />
            <text
              v-for="ax in props.wuxingRadarAxes"
              :key="`l${ax.label}`"
              :x="ax.x"
              :y="ax.y + 1"
              :fill="ax.color"
              text-anchor="middle"
              dominant-baseline="middle"
              class="wb-wx-radar-label"
            >{{ ax.label }}</text>
          </svg>
        </div>
      </div>
    </div>
  </div>
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

.wb-pillars-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  align-items: start;
}

.wb-pillar-table-wrap { overflow-x: auto; }

.wb-pillar-table {
  border-collapse: collapse;
  font-family: var(--font-cn);
  min-width: 360px;
}

.wb-pillar-table th,
.wb-pillar-table td {
  border: 1px solid var(--border);
  padding: 8px 16px;
  text-align: center;
  font-size: 14px;
  background: var(--surface);
}

.wb-pillar-table thead th {
  font-size: 12px;
  color: var(--text-2);
  background: var(--surface-2);
  font-family: var(--font-ui);
}

.wb-pt-head {
  font-size: 12px;
  color: var(--text-3);
  background: var(--surface-2) !important;
  font-family: var(--font-ui);
}

.wb-pt-clickable {
  cursor: pointer;
  transition: background var(--dur-fast), box-shadow var(--dur-fast);
}

.wb-pillar-table th.active,
.wb-pillar-table td.active {
  box-shadow: inset 0 0 0 2px rgba(99,102,241,.28);
  background: #eef2ff !important;
}

.wb-pt-cell.stem { font-size: 22px; font-weight: 700; }
.wb-pt-cell.branch { font-size: 20px; font-weight: 600; }
.wb-pt-cell.shishen { font-size: 12px; color: var(--text-2); font-family: var(--font-ui); }
.day-col { background: #fffbeb !important; }

.wb-strength-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0 0;
}

.wb-str-label { font-size: 11px; color: var(--text-3); width: 52px; flex-shrink: 0; }
.wb-str-bar-wrap { flex: 1; height: 6px; background: var(--border); border-radius: 99px; overflow: hidden; }
.wb-str-bar { height: 100%; border-radius: 99px; transition: width .4s; }
.wb-str-tier { font-size: 11px; color: var(--text-2); background: var(--surface-2); padding: 1px 8px; border-radius: 99px; border: 1px solid var(--border); }
.wb-str-score { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }

.wb-pillar-detail-card {
  margin-top: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(99,102,241,.04), transparent 46%), var(--surface);
  padding: 12px 14px;
}

.wb-pillar-detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.wb-pillar-detail-title { font-size: 18px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.wb-pillar-detail-sub { font-size: 12px; color: var(--text-3); margin-top: 4px; }

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

.wb-fortune-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid var(--border);
  color: var(--text-2);
  background: var(--surface-2);
}

.wb-fortune-badge.is-active {
  color: #3730a3;
  background: #eef2ff;
  border-color: #c7d2fe;
}

.wb-wuxing-wrap { display: flex; align-items: flex-start; gap: 14px; }
.wb-wuxing-chart { min-width: 150px; flex: 1; }
.wb-wx-title { font-size: 11px; color: var(--text-3); margin-bottom: 10px; }
.wb-wx-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.wb-wx-key { width: 16px; font-size: 13px; font-family: var(--font-cn); font-weight: 700; }
.wb-wx-bar-bg { flex: 1; height: 8px; background: var(--border); border-radius: 99px; overflow: hidden; }
.wb-wx-bar { height: 100%; border-radius: 99px; transition: width .4s; }
.wb-wx-val { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); width: 26px; text-align: right; }
.wb-wx-radar-wrap { width: 140px; flex-shrink: 0; }
.wb-wx-radar { width: 100%; height: auto; display: block; }
.wb-wx-radar-grid { fill: none; stroke: var(--border); stroke-width: 1; }
.wb-wx-radar-axis { stroke: var(--border); stroke-width: 1; }
.wb-wx-radar-poly { fill: rgba(99,102,241,.18); stroke: #6366f1; stroke-width: 1.8; stroke-linejoin: round; }
.wb-wx-radar-label { font-size: 11px; font-weight: 700; font-family: var(--font-cn); }

@media (max-width: 1280px) {
  .wb-wx-radar-wrap { width: 124px; }
}

@media (max-width: 900px) {
  .wb-wuxing-wrap { flex-direction: column; gap: 10px; }
  .wb-wx-radar-wrap { width: 150px; align-self: center; }
}

@media (max-width: 768px) {
  .wb-wx-radar-wrap { width: 136px; }
}
</style>
