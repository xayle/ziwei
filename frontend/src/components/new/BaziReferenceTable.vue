<script setup lang="ts">
import { computed } from 'vue'

type PillarKey = 'liunian' | 'dayun' | 'year' | 'month' | 'day' | 'hour'

type HiddenStemLine = {
  stem: string
  tenGod: string
}

type ShenshaChip = {
  name: string
  polarity?: string | null
}

type BaziColumn = {
  key: PillarKey
  label: string
  mainStar?: string
  stem?: string
  branch?: string
  stemColor?: string
  branchColor?: string
  hiddenStems?: HiddenStemLine[]
  xingyun?: string
  selfSeat?: string
  void?: string
  nayin?: string
  shensha?: ShenshaChip[]
}

const props = withDefaults(defineProps<{
  columns: BaziColumn[]
  activeKey?: PillarKey
  hiddenContribByTenGod?: Record<string, number>
  showDetailRows?: boolean
  variant?: 'default' | 'spread'
}>(), {
  activeKey: 'day',
  showDetailRows: true,
  variant: 'default',
})

const hiddenContribRows = computed(() => {
  const src = props.hiddenContribByTenGod
  if (!src) return []
  return Object.entries(src)
    .filter(([, v]) => typeof v === 'number' && Number.isFinite(v))
    .sort((a, b) => b[1] - a[1])
})

const hiddenContribMax = computed(() => {
  const scores = hiddenContribRows.value.map(([, score]) => score)
  return scores.length ? Math.max(...scores) : 1
})

const STEM_COLORS: Record<string, string> = {
  甲: '#3d6b48',
  乙: '#4a7a54',
  丙: '#9a4a38',
  丁: '#a65a42',
  戊: '#7a6348',
  己: '#8b7354',
  庚: '#8b6924',
  辛: '#9a7830',
  壬: '#3d5a78',
  癸: '#4a6890',
}

const BRANCH_COLORS: Record<string, string> = {
  子: '#4a6890',
  丑: '#8b7354',
  寅: '#3d6b48',
  卯: '#4a7a54',
  辰: '#7a6348',
  巳: '#a65a42',
  午: '#9a4a38',
  未: '#8b7354',
  申: '#9a7830',
  酉: '#8b6924',
  戌: '#7a6348',
  亥: '#3d5a78',
}

function textOrMissing(value?: string | null): string {
  const trimmed = value?.trim()
  return trimmed ? trimmed : '缺失'
}

function stemColor(stem?: string): string {
  return stem ? (STEM_COLORS[stem] || '#6b7280') : '#9ca3af'
}

function branchColor(branch?: string): string {
  return branch ? (BRANCH_COLORS[branch] || '#6b7280') : '#9ca3af'
}

function shenshaChipClass(polarity?: string | null): string {
  if (polarity === '+') return 'shensha-chip--auspicious'
  if (polarity === '-') return 'shensha-chip--inauspicious'
  return 'shensha-chip--neutral'
}
</script>

<template>
  <section class="bazi-card" :class="{ 'bazi-card--spread': variant === 'spread' }">
    <div v-if="variant !== 'spread'" class="bazi-card__head">
      <div>
        <p class="bazi-card__eyebrow">八字基础信息</p>
        <h2 class="bazi-card__title">盘面骨架</h2>
      </div>
      <div class="bazi-card__legend">
        <span>核心顺序：流年 / 大运 / 年柱 / 月柱 / 日柱 / 时柱</span>
        <span>缺失项统一标注为“缺失”</span>
      </div>
    </div>

    <div class="bazi-card__table-wrap">
      <table class="bazi-table bazi-ref-table" :class="{ 'bazi-table--register': variant === 'spread' }">
        <colgroup>
          <col class="bazi-table__label-col" />
          <col class="bazi-table__flow-col" />
          <col class="bazi-table__flow-col" />
          <col span="4" class="bazi-table__pillar-col" />
        </colgroup>
        <thead>
          <tr>
            <th class="bazi-table__corner">日期</th>
            <th
              v-for="col in props.columns"
              :key="`${col.key}-head`"
              class="bazi-table__head"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <span class="bazi-table__head-label">{{ col.label }}</span>
              <span v-if="col.key === props.activeKey" class="bazi-table__head-badge">日主</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th class="bazi-table__row-label">主星</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-mainStar`"
              class="bazi-table__cell bazi-table__cell--main"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              {{ textOrMissing(col.mainStar) }}
            </td>
          </tr>

          <tr>
            <th class="bazi-table__row-label">天干</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-stem`"
              class="bazi-table__cell bazi-table__cell--stem"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <span class="bazi-table__glyph" :style="{ color: stemColor(col.stem) }">
                {{ textOrMissing(col.stem) }}
              </span>
            </td>
          </tr>

          <tr>
            <th class="bazi-table__row-label">地支</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-branch`"
              class="bazi-table__cell bazi-table__cell--branch"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <span class="bazi-table__glyph" :style="{ color: branchColor(col.branch) }">
                {{ textOrMissing(col.branch) }}
              </span>
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">藏干</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-hidden`"
              class="bazi-table__cell bazi-table__cell--hidden"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <div v-if="col.hiddenStems?.length" class="hidden-list">
                <div v-for="line in col.hiddenStems" :key="`${col.key}-${line.stem}-${line.tenGod}`" class="hidden-line">
                  <span class="hidden-line__stem" :style="{ color: stemColor(line.stem) }">{{ line.stem }}</span>
                  <span class="hidden-line__god">{{ line.tenGod || '缺失' }}</span>
                </div>
              </div>
              <span v-else class="bazi-table__missing">缺失</span>
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">星运</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-xingyun`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              {{ textOrMissing(col.xingyun) }}
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">自坐</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-selfSeat`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              {{ textOrMissing(col.selfSeat) }}
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">空亡</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-void`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              {{ textOrMissing(col.void) }}
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">纳音</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-nayin`"
              class="bazi-table__cell bazi-table__cell--nayin"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              {{ textOrMissing(col.nayin) }}
            </td>
          </tr>

          <tr v-if="showDetailRows">
            <th class="bazi-table__row-label">神煞</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-shensha`"
              class="bazi-table__cell bazi-table__cell--shensha"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <div v-if="col.shensha?.length" class="shensha-list">
                <span
                  v-for="item in col.shensha"
                  :key="`${col.key}-${item.name}`"
                  class="shensha-chip"
                  :class="shenshaChipClass(item.polarity)"
                >
                  {{ item.name }}
                </span>
              </div>
              <span v-else class="bazi-table__missing">缺失</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="hiddenContribRows.length" class="bazi-card__contrib" data-testid="bazi-hidden-contrib">
      <h3 class="bazi-card__contrib-title">藏干十神贡献</h3>
      <div class="contrib-bars">
        <div v-for="[god, score] in hiddenContribRows" :key="god" class="contrib-bar">
          <span class="contrib-bar__label">{{ god }}</span>
          <div class="contrib-bar__track" aria-hidden="true">
            <span
              class="contrib-bar__fill"
              :style="{ width: `${Math.max(8, (score / hiddenContribMax) * 100)}%` }"
            />
          </div>
          <span class="contrib-bar__value">{{ score.toFixed(2) }}</span>
        </div>
      </div>
    </div>
    <p v-else-if="hiddenContribByTenGod !== undefined" class="bazi-card__contrib-empty">藏干十神贡献：缺失</p>
  </section>
</template>

<style scoped>
.bazi-card {
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: none;
}

.bazi-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px 12px;
  border-bottom: 1px solid var(--border);
}

.bazi-card__eyebrow {
  margin: 0;
  color: var(--text-2);
  letter-spacing: 0.24em;
  font-size: 12px;
  text-transform: uppercase;
}

.bazi-card__title {
  margin: 8px 0 0;
  font-size: 22px;
  line-height: 1.1;
  color: var(--brand-ink);
}

.bazi-card__legend {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  padding-top: 6px;
  color: var(--text-2);
  font-size: 12px;
  line-height: 1.5;
}

.bazi-card__table-wrap {
  overflow-x: auto;
}

.bazi-table {
  width: 100%;
  min-width: 940px;
  border-collapse: collapse;
  table-layout: fixed;
}

.bazi-table__label-col {
  width: 84px;
}

.bazi-table th,
.bazi-table td {
  border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border);
  text-align: center;
  vertical-align: middle;
}

.bazi-table tr:last-child th,
.bazi-table tr:last-child td {
  border-bottom: 0;
}

.bazi-table th:last-child,
.bazi-table td:last-child {
  border-right: 0;
}

.bazi-table__corner,
.bazi-table__row-label {
  width: 84px;
  background: var(--inset-tint);
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-ui);
  letter-spacing: 0.06em;
}

.bazi-table__corner {
  padding: 18px 10px;
}

.bazi-table__row-label {
  padding: 14px 10px;
}

.bazi-table__label-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.bazi-table__arrow {
  display: inline-block;
  font-size: 12px;
  opacity: 0.72;
  transform: translateY(1px);
}

.bazi-table__head {
  position: relative;
  padding: 14px 8px;
  background: var(--inset-tint);
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-ui);
  letter-spacing: 0.06em;
}

.bazi-table__head.is-active,
.bazi-table__cell.is-active {
  background: rgba(240, 224, 199, 0.35);
}

.bazi-table__head-badge {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: var(--brand-gold-dark);
  background: var(--brand-gold-lt);
  border: 1px solid rgba(184, 137, 77, 0.35);
}

.bazi-table__cell {
  padding: 14px 10px;
  background: var(--surface);
  color: var(--text);
  font-size: 15px;
  font-family: var(--font-ui);
}

.bazi-table__cell--main {
  font-size: 14px;
  color: var(--brand-ink);
}

.bazi-table__cell--stem,
.bazi-table__cell--branch {
  padding: 8px 10px 10px;
}

.bazi-table__glyph {
  display: inline-block;
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.02em;
  font-family: var(--font-display);
  font-variant-numeric: tabular-nums;
}

.bazi-table__cell--hidden {
  padding: 12px 10px;
}

.hidden-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-start;
  justify-content: center;
  min-height: 84px;
}

.hidden-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 16px;
  line-height: 1.1;
  white-space: nowrap;
}

.hidden-line__stem {
  font-size: 16px;
  font-weight: 700;
}

.hidden-line__god {
  color: var(--text-2);
  font-size: 13px;
}

.bazi-table__cell--nayin {
  font-size: 14px;
  color: var(--text-2);
}

.bazi-table__cell--shensha {
  padding: 14px 10px;
}

.shensha-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.shensha-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 13px;
  border: 1px solid var(--border);
}

.shensha-chip--neutral {
  background: var(--inset-tint);
  color: var(--text-2);
}

.shensha-chip--auspicious {
  color: var(--brand-ink);
  background: var(--surface);
  border-color: var(--border-md);
  border-left: 2px solid var(--brand-gold);
}

.shensha-chip--inauspicious {
  color: var(--brand-cinnabar);
  background: var(--surface);
  border-color: var(--border-md);
  border-left: 2px solid var(--brand-cinnabar);
}

.bazi-table__missing {
  color: var(--text-3);
  font-size: 14px;
}

.bazi-card__contrib {
  padding: 12px 18px 18px;
  border-top: 1px solid var(--border);
}

.bazi-card--spread {
  border: none;
  border-radius: 0;
  background: transparent;
}

.bazi-card--spread .bazi-table {
  min-width: 100%;
}

.bazi-table--register {
  table-layout: fixed;
}

.bazi-table--register .bazi-table__label-col {
  width: 72px;
}

.bazi-table--register .bazi-table__flow-col {
  width: 10%;
}

.bazi-table--register .bazi-table__pillar-col {
  width: 15%;
}

.bazi-table--register .bazi-table__corner,
.bazi-table--register .bazi-table__row-label {
  width: 72px;
  background: var(--surface-2);
  color: var(--brand-mist);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1em;
}

.bazi-table--register .bazi-table__head {
  background: var(--surface-2);
  color: var(--brand-mist);
  font-family: var(--font-display);
  font-size: 12px;
  letter-spacing: 0.1em;
  border-bottom: 1px solid var(--border-md);
}

.bazi-table--register .bazi-table__head.is-active {
  background: rgba(240, 224, 199, 0.45);
  box-shadow: inset 0 2px 0 var(--brand-gold);
  color: var(--brand-ink);
}

.bazi-table--register .bazi-table__head-badge {
  display: block;
  margin: 6px auto 0;
  width: fit-content;
  border-radius: 2px;
  font-family: var(--font-display);
  letter-spacing: 0.08em;
}

.bazi-table--register .bazi-table__cell.is-active {
  background: rgba(240, 224, 199, 0.22);
}

.bazi-table--register .bazi-table__cell--main {
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.bazi-table--register .bazi-table__glyph {
  font-size: clamp(26px, 2.6vw, 30px);
  font-weight: 600;
}

.bazi-table--register .hidden-list {
  align-items: center;
  min-height: 72px;
}

.bazi-table--register .hidden-line {
  font-size: 14px;
}

.bazi-table--register .hidden-line__stem {
  font-family: var(--font-display);
  font-weight: 600;
}

.bazi-table--register .hidden-line__god {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--brand-mist);
}

.bazi-table--register .bazi-table__cell--nayin {
  font-family: var(--font-display);
  font-size: 13px;
}

.bazi-table--register .shensha-list {
  justify-content: center;
  gap: 6px;
  padding: 2px 0;
}

.bazi-table--register .shensha-chip {
  border-radius: 2px;
  padding: 1px 7px;
  font-size: 11px;
  font-family: var(--font-display);
  letter-spacing: 0.06em;
  background: var(--surface);
}

.bazi-table--register .shensha-chip--neutral {
  color: var(--brand-mist);
  border: 1px solid var(--border);
}

.bazi-table--register .shensha-chip--auspicious {
  color: var(--brand-ink);
  border: 1px solid var(--border-md);
  border-left: 2px solid var(--brand-gold);
}

.bazi-table--register .shensha-chip--inauspicious {
  color: var(--brand-cinnabar);
  border: 1px solid var(--border-md);
  border-left: 2px solid var(--brand-cinnabar);
}

.bazi-table--register .bazi-table__missing {
  font-family: var(--font-display);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.bazi-card--spread .bazi-card__contrib {
  padding: 14px 4px 4px;
  border-top: 1px dashed var(--border-md);
}

.contrib-bars {
  display: grid;
  gap: 10px;
}

.contrib-bar {
  display: grid;
  grid-template-columns: 4.5em minmax(0, 1fr) 3em;
  align-items: center;
  gap: 10px;
}

.contrib-bar__label {
  font-size: 13px;
  color: var(--brand-ink);
  font-family: var(--font-display);
  letter-spacing: 0.04em;
}

.contrib-bar__track {
  height: 8px;
  border-radius: 999px;
  background: var(--inset-tint);
  overflow: hidden;
}

.contrib-bar__fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--brand-gold-lt), var(--brand-gold));
}

.contrib-bar__value {
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--brand-gold-dark);
  text-align: right;
}

.bazi-card__contrib-title {
  margin: 0 0 12px;
  font-size: 12px;
  letter-spacing: 0.1em;
  font-family: var(--font-display);
  color: var(--brand-gold-dark);
  font-weight: 600;
}

.bazi-card__contrib-empty {
  margin: 0;
  padding: 0 18px 14px;
  color: var(--text-3);
  font-size: 13px;
  font-style: italic;
}

@media (max-width: 960px) {
  .bazi-card__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .bazi-card__legend {
    align-items: flex-start;
  }
}
</style>
