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
  /** 命局神煞清单，用于册页神煞行对齐对照 */
  chartShensha?: Array<{ name?: string | null; priority?: string | null }>
}>(), {
  activeKey: 'day',
  showDetailRows: true,
  variant: 'default',
  chartShensha: () => [],
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

const inkGlyphs = computed(() => props.variant === 'spread')

function glyphStemStyle(stem?: string): Record<string, string> | undefined {
  if (inkGlyphs.value) return undefined
  return { color: stemColor(stem) }
}

function glyphBranchStyle(branch?: string): Record<string, string> | undefined {
  if (inkGlyphs.value) return undefined
  return { color: branchColor(branch) }
}

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

function isMissing(value?: string | null): boolean {
  return !value?.trim()
}

function stemColor(stem?: string): string {
  return stem ? (STEM_COLORS[stem] || '#6b7280') : '#9ca3af'
}

function branchColor(branch?: string): string {
  return branch ? (BRANCH_COLORS[branch] || '#6b7280') : '#9ca3af'
}

function shenshaChipClass(polarity?: string | null): string {
  if (polarity === '+') return 'shensha-item--auspicious'
  if (polarity === '-') return 'shensha-item--inauspicious'
  return 'shensha-item--neutral'
}

function displayShensha(items?: ShenshaChip[]): ShenshaChip[] {
  const seen = new Set<string>()
  const out: ShenshaChip[] = []
  for (const item of items ?? []) {
    const name = item.name.trim()
    if (!name || name === '缺失' || seen.has(name)) continue
    seen.add(name)
    out.push({ name, polarity: item.polarity ?? null })
  }
  return out
}

type ShenshaMatrixRow = {
  name: string
  present: boolean
  polarity?: string | null
}

function shenshaPriorityRank(priority?: string | null): number {
  if (priority === 'A') return 0
  if (priority === 'B') return 1
  if (priority === 'C') return 2
  return 3
}

const shenshaCatalog = computed(() => {
  const catalog = new Map<string, { priority?: string | null }>()

  for (const item of props.chartShensha ?? []) {
    const name = item.name?.trim()
    if (!name || name === '缺失') continue
    catalog.set(name, { priority: item.priority ?? null })
  }

  for (const col of props.columns) {
    for (const item of displayShensha(col.shensha)) {
      if (!catalog.has(item.name)) {
        catalog.set(item.name, { priority: null })
      }
    }
  }

  return [...catalog.entries()]
    .sort((a, b) => {
      const rankDiff = shenshaPriorityRank(a[1].priority) - shenshaPriorityRank(b[1].priority)
      if (rankDiff !== 0) return rankDiff
      return a[0].localeCompare(b[0], 'zh-CN')
    })
    .map(([name]) => name)
})

function shenshaMatrixRows(col: BaziColumn): ShenshaMatrixRow[] {
  const present = new Map(
    displayShensha(col.shensha).map((item) => [item.name, item.polarity ?? null]),
  )
  return shenshaCatalog.value.map((name) => ({
    name,
    present: present.has(name),
    polarity: present.get(name) ?? null,
  }))
}

function shenshaItemClass(row: ShenshaMatrixRow): string[] {
  if (!row.present) return ['shensha-item--absent']
  return ['shensha-item--present', shenshaChipClass(row.polarity)]
}

function registerCellText(value?: string | null): string {
  if (props.variant === 'spread' && isMissing(value)) return '—'
  return textOrMissing(value)
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

    <div class="bazi-card__table-wrap" :class="{ 'bazi-register-wrap': variant === 'spread' }">
      <table class="bazi-table bazi-ref-table" :class="{ 'bazi-table--register': variant === 'spread' }">
        <colgroup v-if="variant === 'spread'">
          <col class="bazi-table__label-col" />
          <col span="6" class="bazi-table__data-col" />
        </colgroup>
        <colgroup v-else>
          <col class="bazi-table__label-col" />
          <col class="bazi-table__flow-col" />
          <col class="bazi-table__flow-col" />
          <col span="4" class="bazi-table__pillar-col" />
        </colgroup>
        <thead>
          <tr class="bazi-table__row bazi-table__row--head">
            <th class="bazi-table__corner">{{ variant === 'spread' ? '列' : '日期' }}</th>
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
          <tr class="bazi-table__row bazi-table__row--main">
            <th class="bazi-table__row-label">主星</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-mainStar`"
              class="bazi-table__cell bazi-table__cell--main"
              :class="{ 'is-active': col.key === props.activeKey, 'bazi-table__missing': isMissing(col.mainStar) }"
            >
              {{ registerCellText(col.mainStar) }}
            </td>
          </tr>

          <tr class="bazi-table__row bazi-table__row--glyph">
            <th class="bazi-table__row-label">天干</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-stem`"
              class="bazi-table__cell bazi-table__cell--stem"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <span
                class="bazi-table__glyph"
                :class="{ 'bazi-table__missing': isMissing(col.stem) }"
                :style="glyphStemStyle(col.stem)"
              >
                {{ registerCellText(col.stem) }}
              </span>
            </td>
          </tr>

          <tr class="bazi-table__row bazi-table__row--glyph bazi-table__row--glyph-last">
            <th class="bazi-table__row-label">地支</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-branch`"
              class="bazi-table__cell bazi-table__cell--branch"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <span
                class="bazi-table__glyph"
                :class="{ 'bazi-table__missing': isMissing(col.branch) }"
                :style="glyphBranchStyle(col.branch)"
              >
                {{ registerCellText(col.branch) }}
              </span>
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--hidden">
            <th class="bazi-table__row-label">藏干</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-hidden`"
              class="bazi-table__cell bazi-table__cell--hidden"
              :class="{ 'is-active': col.key === props.activeKey }"
            >
              <div v-if="col.hiddenStems?.length" class="hidden-list">
                <div v-for="line in col.hiddenStems" :key="`${col.key}-${line.stem}-${line.tenGod}`" class="hidden-line">
                  <span
                    class="hidden-line__stem"
                    :style="inkGlyphs ? undefined : { color: stemColor(line.stem) }"
                  >{{ line.stem }}</span>
                  <span class="hidden-line__sep" aria-hidden="true">·</span>
                  <span class="hidden-line__god">{{ line.tenGod || '—' }}</span>
                </div>
              </div>
              <span v-else class="bazi-table__missing">—</span>
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--meta">
            <th class="bazi-table__row-label">星运</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-xingyun`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey, 'bazi-table__missing': isMissing(col.xingyun) }"
            >
              {{ registerCellText(col.xingyun) }}
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--meta">
            <th class="bazi-table__row-label">自坐</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-selfSeat`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey, 'bazi-table__missing': isMissing(col.selfSeat) }"
            >
              {{ registerCellText(col.selfSeat) }}
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--meta">
            <th class="bazi-table__row-label">空亡</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-void`"
              class="bazi-table__cell"
              :class="{ 'is-active': col.key === props.activeKey, 'bazi-table__missing': isMissing(col.void) }"
            >
              {{ registerCellText(col.void) }}
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--meta">
            <th class="bazi-table__row-label">纳音</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-nayin`"
              class="bazi-table__cell bazi-table__cell--nayin"
              :class="{ 'is-active': col.key === props.activeKey, 'bazi-table__missing': isMissing(col.nayin) }"
            >
              {{ registerCellText(col.nayin) }}
            </td>
          </tr>

          <tr v-if="showDetailRows" class="bazi-table__row bazi-table__row--shensha">
            <th class="bazi-table__row-label">神煞</th>
            <td
              v-for="col in props.columns"
              :key="`${col.key}-shensha`"
              class="bazi-table__cell bazi-table__cell--shensha"
              :class="{ 'is-active': col.key === props.activeKey }"
              :style="variant === 'spread' && shenshaCatalog.length ? { '--shensha-rows': shenshaCatalog.length } : undefined"
            >
              <ul v-if="variant === 'spread' && shenshaCatalog.length" class="shensha-stack shensha-stack--matrix">
                <li
                  v-for="row in shenshaMatrixRows(col)"
                  :key="`${col.key}-${row.name}`"
                  class="shensha-item"
                  :class="shenshaItemClass(row)"
                  :aria-hidden="!row.present"
                >
                  {{ row.name }}
                </li>
              </ul>
              <ul v-else-if="displayShensha(col.shensha).length" class="shensha-stack">
                <li
                  v-for="item in displayShensha(col.shensha)"
                  :key="`${col.key}-${item.name}`"
                  class="shensha-item shensha-item--present"
                  :class="shenshaChipClass(item.polarity)"
                >
                  {{ item.name }}
                </li>
              </ul>
              <span v-else class="bazi-table__missing">—</span>
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

.bazi-register-wrap {
  background: var(--surface);
}

.bazi-table--register {
  min-width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  background: var(--surface);
}

.bazi-table--register th,
.bazi-table--register td {
  border: 1px solid var(--border);
  padding: 0;
  margin: 0;
  background: var(--surface);
  text-align: center;
  vertical-align: middle;
}

.bazi-table--register .bazi-table__label-col {
  width: 56px;
}

.bazi-table--register .bazi-table__data-col {
  width: calc((100% - 56px) / 6);
}

.bazi-table--register .bazi-table__corner,
.bazi-table--register .bazi-table__row-label {
  width: 56px;
  color: var(--register-muted);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.14em;
  writing-mode: horizontal-tb;
}

.bazi-table--register .bazi-table__head {
  color: var(--register-muted);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.12em;
  line-height: 1.2;
}

.bazi-table--register .bazi-table__head.is-active {
  color: var(--register-ink);
  font-weight: 600;
}

.bazi-table--register .bazi-table__head.is-active .bazi-table__head-label::after {
  content: '';
  display: block;
  width: 10px;
  height: 2px;
  margin: 3px auto 0;
  background: var(--brand-cinnabar);
}

.bazi-table--register .bazi-table__head-badge {
  display: block;
  margin: 1px auto 0;
  font-family: var(--font-display);
  font-size: 9px;
  letter-spacing: 0.16em;
  color: var(--brand-cinnabar);
  font-weight: 500;
}

.bazi-table--register .bazi-table__cell.is-active .bazi-table__glyph:not(.bazi-table__missing) {
  color: var(--register-ink);
  font-weight: 700;
}

.bazi-table--register .bazi-table__cell {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--register-ink);
  letter-spacing: 0.04em;
}

.bazi-table--register .bazi-table__cell.bazi-table__missing {
  color: var(--register-muted);
  font-weight: 300;
  opacity: 0.45;
}

.bazi-table--register .bazi-table__row--head th {
  height: 42px;
}

.bazi-table--register .bazi-table__row--main th,
.bazi-table--register .bazi-table__row--main td {
  height: 34px;
}

.bazi-table--register .bazi-table__row--glyph th,
.bazi-table--register .bazi-table__row--glyph td {
  height: 46px;
}

.bazi-table--register .bazi-table__row--glyph-last th,
.bazi-table--register .bazi-table__row--glyph-last td {
  border-bottom-color: var(--border-md);
}

.bazi-table--register .bazi-table__row--hidden th,
.bazi-table--register .bazi-table__row--hidden td {
  height: 66px;
}

.bazi-table--register .bazi-table__row--meta th,
.bazi-table--register .bazi-table__row--meta td {
  height: 34px;
}

.bazi-table--register .bazi-table__row--shensha th,
.bazi-table--register .bazi-table__row--shensha td {
  height: auto;
  min-height: max(78px, calc(var(--shensha-rows, 4) * 18px + 16px));
}

.bazi-table--register .bazi-table__cell--main {
  font-family: var(--font-display);
  font-size: 12px;
  letter-spacing: 0.06em;
  color: var(--register-ink);
  font-weight: 500;
}

.bazi-table--register .bazi-table__cell--main.bazi-table__missing {
  font-weight: 400;
}

.bazi-table--register .bazi-table__glyph {
  font-family: var(--font-display);
  font-size: clamp(22px, 2.2vw, 26px);
  font-weight: 600;
  line-height: 1;
  color: var(--register-ink);
}

.bazi-table--register .hidden-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 100%;
  padding: 4px 2px;
}

.bazi-table--register .hidden-line {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
}

.bazi-table--register .hidden-line__stem {
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--register-ink);
}

.bazi-table--register .hidden-line__sep {
  color: var(--register-muted);
  font-size: 10px;
  opacity: 0.7;
}

.bazi-table--register .hidden-line__god {
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--register-muted);
  font-weight: 400;
}

.bazi-table--register .bazi-table__cell--nayin {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--register-ink);
  letter-spacing: 0.04em;
}

.bazi-table--register .shensha-stack {
  list-style: none;
  margin: 0;
  padding: 6px 4px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.bazi-table--register .shensha-stack--matrix {
  gap: 1px;
  justify-content: flex-start;
  padding-top: 8px;
  padding-bottom: 8px;
}

.bazi-table--register .shensha-item--present {
  color: var(--register-ink);
  font-weight: 600;
  opacity: 1;
}

.bazi-table--register .shensha-item--present.shensha-item--inauspicious {
  color: var(--brand-cinnabar);
}

.bazi-table--register .shensha-item--absent {
  color: var(--register-muted);
  font-weight: 300;
  opacity: 0.16;
  user-select: none;
}

.bazi-table--register .shensha-item {
  font-family: var(--font-display);
  font-size: 11px;
  line-height: 1.35;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.bazi-table--register .shensha-item--neutral,
.bazi-table--register .shensha-item--auspicious {
  color: inherit;
}

.bazi-table--register .bazi-table__missing {
  font-family: var(--font-display);
  font-size: 13px;
  color: var(--register-muted);
  font-weight: 300;
  opacity: 0.45;
  letter-spacing: 0;
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
  background: var(--brand-gold);
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
