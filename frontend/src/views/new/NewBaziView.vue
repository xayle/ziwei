<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaziReferenceTable from '@/components/new/BaziReferenceTable.vue'
import BaziStructuralRelations from '@/components/fusheng/BaziStructuralRelations.vue'
import BaziLiuriTodayCard from '@/components/fusheng/BaziLiuriTodayCard.vue'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import SummaryStrip from '@/components/fusheng/SummaryStrip.vue'
import AnalysisPanel, { type AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'
import { useFushengReport } from '@/composables/useFushengReport'
import { validateBaziZiweiConsistency } from '@/utils/crossValidation'
import { useEngineTrustDisplay } from '@/composables/useEngineTrustDisplay'
import EngineTrustPanel from '@/components/fusheng/EngineTrustPanel.vue'
import VolumeHead from '@/components/fusheng/VolumeHead.vue'
import DualTrackTable from '@/components/fusheng/DualTrackTable.vue'
import { useProfileStore } from '@/stores/profile'
import { buildBaziColumns } from '@/utils/buildBaziColumns'
import { buildDayunDisplayRow } from '@/utils/dayunDisplay'
import { formatRelationsSummaryText, formatShenshaSummaryText } from '@/utils/formatVol2Summary'
import { truncateText } from '@/utils/truncateText'
import type { BaziResponse } from '@/api/bazi'
import '@/assets/fusheng-page.css'

type DetailBlock = {
  title: string
  lead: string
  body: string
  bullets: string[]
}

const router = useRouter()
const depth = ref<'overview' | 'structure' | 'deep'>('overview')
const profile = useProfileStore()
const { loadingBazi, loadingDayun, error, bazi: result, ziwei, dayunReport, dayunError, loadBazi, loadDayunNarratives, isCacheValid, requestMeta } = useFushengReport()
const {
  missingFields,
  provenanceRows,
  dualTracks,
  dualTrackReference,
  validationLines,
  liuri,
  pillarDetails,
  relations,
  baziStructural,
  strengthFactorLines,
} = useEngineTrustDisplay(result)

const crossValidation = computed(() => validateBaziZiweiConsistency(result.value, ziwei.value))
const showCrossValidationHint = computed(() =>
  Boolean(ziwei.value) && crossValidation.value.overall !== 'pass',
)

const liuriRaw = computed(() => result.value?.liuri_liushi ?? null)

const currentYear = new Date().getFullYear()
const profileLabel = computed(() => profile.activeProfile?.label || '未命名档案')

function textOrMissing(value?: string | null): string {
  const trimmed = value?.trim()
  return trimmed ? trimmed : '缺失'
}

function listOrMissing(values?: Array<string | null | undefined>): string {
  const items = values?.map((item) => item?.trim()).filter((item): item is string => !!item) ?? []
  return items.length ? items.join('、') : '缺失'
}

function pillarSetLabel(key: 'primary' | 'secondary'): string {
  return key === 'primary' ? '主盘' : '副盘'
}

function formatPillarSet(set?: BaziResponse['pillars_primary']): string {
  if (!set) return '缺失'
  return ['year', 'month', 'day', 'hour']
    .map((k) => {
      const p = set[k as keyof typeof set]
      return p?.stem && p?.branch ? `${p.stem}${p.branch}` : '—'
    })
    .join(' ')
}

const caliberBanner = computed(() => {
  const meta = requestMeta.value
  const parts: string[] = []
  if (meta?.precisionLabel) parts.push(meta.precisionLabel)
  parts.push(profile.solarTime ? '真太阳时：已启用' : '真太阳时：未启用')
  const ziRule = profile.ziDayRule ?? 'sxtwl'
  const ziLabels: Record<string, string> = {
    sxtwl: '子时日界：寿星天文历',
    early_zi_prev_day: '子时日界：早子归前日',
    early_zi_same_day: '子时日界：早子归当日',
  }
  parts.push(ziLabels[ziRule] ?? `子时日界：${ziRule}`)
  if (meta?.calendarNote) parts.push(meta.calendarNote.split('。')[0])
  return parts.join(' · ')
})

const timeWarnings = computed(() => {
  const warnings: string[] = []
  const meta = requestMeta.value
  if (meta?.timeRiskHint) warnings.push(meta.timeRiskHint)
  const raw = result.value?.raw as { day_boundary_crossed?: boolean; day_boundary_rule_used?: string } | undefined
  if (raw?.day_boundary_crossed) {
    warnings.push(`日界跨越：${raw.day_boundary_rule_used || 'zi_initial'} 规则已触发换日。`)
  }
  for (const item of result.value?.warnings ?? []) {
    if (item.message) warnings.push(item.message)
  }
  return [...new Set(warnings)]
})

const hiddenContrib = computed(() => {
  const raw = result.value?.scoring?.hidden_contrib_by_ten_god
    ?? (result.value as { hidden_contrib_by_ten_god?: Record<string, number> })?.hidden_contrib_by_ten_god
  return raw && Object.keys(raw).length ? raw : undefined
})

const yongshenNote = computed(() => {
  const primary = listOrMissing(result.value?.yongshen?.favor)
  const secondary = listOrMissing(result.value?.yongshen?.avoid)
  const hasDual = Boolean(result.value?.pillars_secondary)
  const parts = [`用神（${pillarSetLabel('primary')}）：${primary}`, `忌神：${secondary}`]
  if (hasDual) {
    parts.push(`副盘四柱：${formatPillarSet(result.value?.pillars_secondary)}`)
  }
  return parts.join(' · ')
})

const classicRefText = computed(() => textOrMissing(result.value?.geju?.classic_ref))

function scoreOrMissing(value?: number | null, digits = 0): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '缺失'
  return Number.isInteger(value) ? String(value) : value.toFixed(digits)
}

function formatDayunRange(item?: DayunItem): string {
  if (!item) return '缺失'
  const startYear = item.start_year ?? currentYear
  return `${startYear}-${startYear + 9}`
}

type DayunItem = NonNullable<NonNullable<BaziResponse['dayun']>['items']>[number]

const dayunItems = computed(() => result.value?.dayun?.items ?? result.value?.dayun?.cycles ?? [])

function findCurrentDayun(): DayunItem | undefined {
  const items = dayunItems.value
  return items.find((item) => {
    const startYear = item.start_year ?? 0
    const endYear = startYear + 9
    return startYear <= currentYear && currentYear <= endYear
  }) ?? items[0]
}

const currentDayun = computed(() => findCurrentDayun())
const currentLiunian = computed(() => (result.value?.liunian?.items ?? []).find((item) => item.year === currentYear))

const columns = computed(() => buildBaziColumns(result.value, currentYear))
const activeKey = 'day' as const
const topSummary = computed(() => {
  const r = result.value
  if (!r) {
    return truncateText(`当前档案 ${profileLabel.value} 已就绪。可先核对出生时间和出生地，再稍后重试。`)
  }
  const day = r.pillars_primary?.day
  const strength = r.day_master_strength?.tier ?? '缺失'
  const geju = r.geju?.geju_name ?? '缺失'
  const favor = r.yongshen?.favor?.join('、') || '缺失'
  const shishen = r.shishen_summary?.dominant?.slice(0, 2).join('、') || '缺失'
  return truncateText(
    `${profileLabel.value} · 日主 ${day?.stem || '—'}${day?.branch || ''} · 十神 ${shishen} · 格局 ${geju} · 用神 ${favor} · 强弱 ${strength}`,
  )
})

const highlightCards = computed(() => {
  const shishen = result.value?.shishen_summary
  const shishenLabel = shishen?.dominant?.slice(0, 2).join('、')
    || truncateText(shishen?.summary_text || '', 12)
    || '待计算'
  return [
    {
      label: '日主',
      value: result.value?.pillars_primary?.day ? `${result.value.pillars_primary.day.stem}${result.value.pillars_primary.day.branch}` : '待计算',
      note: '四柱核心',
    },
    {
      label: '十神',
      value: shishenLabel,
      note: '结构主导',
    },
    {
      label: '格局',
      value: result.value?.geju?.geju_name || '待计算',
      note: '命局结构',
    },
    {
      label: '强弱',
      value: result.value?.day_master_strength?.tier || '待计算',
      note: '平衡判断',
    },
    {
      label: '用神',
      value: result.value?.yongshen?.favor?.join('、') || '待计算',
      note: '喜用方向',
    },
  ]
})

const detailBlocks = computed<DetailBlock[]>(() => {
  const geju = result.value?.geju
  const gejuName = geju?.geju_name || '待计算'
  const gejuBody = geju?.classic_ref?.trim() || geju?.geju_detail || '暂无典籍句式。'
  const strength = result.value?.day_master_strength?.tier || '待计算'
  const balanceScore = scoreOrMissing(result.value?.wuxing_balance_score)
  const wuxing = result.value?.wuxing_score
  const shishen = result.value?.shishen_summary
  const palace = result.value?.palace
  const fortune = result.value?.current_fortune_summary
  const warnings = (result.value?.warnings ?? []).map((item) => item.message).filter(Boolean)
  const ruleMatches = (result.value?.rule_matches ?? []).slice(0, 4).map((item) => `${item.name}${item.flags?.length ? `：${item.flags.join('、')}` : ''}`)

  return [
    {
      title: '命局摘要',
      lead: gejuName,
      body: gejuBody,
      bullets: [
        `日主：${result.value?.pillars_primary?.day ? `${result.value.pillars_primary.day.stem}${result.value.pillars_primary.day.branch}` : '待计算'}`,
        `强弱：${strength}`,
        `引擎格：${gejuName}${geju?.is_broken ? '（破格）' : ''}`,
        geju?.derived_geju && geju.derived_geju !== gejuName ? `衍生格：${geju.derived_geju}` : '',
        geju?.recorded_geju && geju.recorded_geju !== gejuName ? `古籍口径：${geju.recorded_geju}` : '',
        geju?.dual_track_note ? `双轨：${geju.dual_track_note}` : '',
        `典籍：${classicRefText.value}`,
        yongshenNote.value,
      ].filter(Boolean),
    },
    {
      title: '五行与平衡',
      lead: `平衡分 ${balanceScore}`,
      body: result.value?.balance_advice || result.value?.geju?.geju_detail || '暂无平衡建议。',
      bullets: [
        `木 ${scoreOrMissing(wuxing?.wood)}`,
        `火 ${scoreOrMissing(wuxing?.fire)}`,
        `土 ${scoreOrMissing(wuxing?.earth)}`,
        `金 ${scoreOrMissing(wuxing?.metal)}`,
        `水 ${scoreOrMissing(wuxing?.water)}`,
        `偏弱：${listOrMissing(result.value?.wuxing_weak)}`,
        `偏强：${listOrMissing(result.value?.wuxing_strong)}`,
      ],
    },
    {
      title: '十神结构',
      lead: shishen?.summary_text || '待计算',
      body: shishen?.day_stem ? `日主 ${shishen.day_stem}，总分 ${scoreOrMissing(shishen.score_total)}` : '暂无十神摘要。',
      bullets: [
        `主导：${listOrMissing(shishen?.dominant)}`,
        `六亲：${listOrMissing(shishen?.liuqin_summary)}`,
        `分布：${Object.keys(shishen?.score_share ?? {}).length ? Object.entries(shishen?.score_share ?? {}).map(([k, v]) => `${k} ${scoreOrMissing(v, 1)}`).join(' · ') : '缺失'}`,
      ],
    },
    {
      title: '宫位信息',
      lead: palace?.ming_gong?.palace_name || '待计算',
      body: palace?.interpretation_text || '暂无宫位说明。',
      bullets: [
        `命宫：${palace?.ming_gong ? `${palace.ming_gong.palace_name} / ${palace.ming_gong.dizhi}` : '缺失'}`,
        `身宫：${palace?.shen_gong ? `${palace.shen_gong.palace_name} / ${palace.shen_gong.dizhi}` : '缺失'}`,
        `十二宫：${palace?.twelve_palaces?.length ? `${palace.twelve_palaces.length} 个` : '缺失'}`,
      ],
    },
    {
      title: '当前运势',
      lead: fortune?.current_dayun || currentDayun.value?.ten_god || '待计算',
      body: fortune
        ? `当前大运剩余 ${scoreOrMissing(fortune.dayun_years_remaining)} 年，当前流年 ${fortune.current_liunian}。`
        : '暂无当前运势摘要。',
      bullets: [
        `当前大运：${currentDayun.value ? `${currentDayun.value.stem || ''}${currentDayun.value.branch || ''}`.trim() || '缺失' : '缺失'}`,
        `流年：${currentLiunian.value?.year ? `${currentLiunian.value.year} · ${currentLiunian.value.stem || ''}${currentLiunian.value.branch || ''}`.trim() : '缺失'}`,
        `行动建议：${fortune?.top3_actions?.length ? fortune.top3_actions.join('；') : '缺失'}`,
      ],
    },
    {
      title: '规则与提示',
      lead: timeWarnings.value[0] || warnings[0] || ruleMatches[0] || '待计算',
      body: timeWarnings.value.length
        ? timeWarnings.value.join('。')
        : warnings.length
          ? warnings.join('。')
          : '暂无警告或规则提示。',
      bullets: [
        `典籍出处：${classicRefText.value}`,
        `主盘：${formatPillarSet(result.value?.pillars_primary)}`,
        `副盘：${result.value?.pillars_secondary ? formatPillarSet(result.value.pillars_secondary) : '无'}`,
        `警告：${warnings.length ? warnings.join('；') : '无'}`,
        `命中：${ruleMatches.length ? ruleMatches.join('；') : '无'}`,
      ],
    },
  ]
})

const vol2Summary = computed(() => ({
  relations: formatRelationsSummaryText(result.value),
  shensha: formatShenshaSummaryText(result.value),
}))

const summaryItems = computed(() => highlightCards.value.map((card) => ({ label: card.label, value: card.value })))

const analysisBlocks = computed<AnalysisBlock[]>(() => {
  const layers: Array<AnalysisBlock['layer']> = [
    'classical',
    'engine',
    'engine',
    'engine',
    'heuristic',
    'heuristic',
  ]
  return detailBlocks.value.map((block, index) => ({
    id: `bazi-${index}`,
    title: block.title,
    lead: block.lead,
    body: block.body,
    bullets: block.bullets,
    layer: layers[index],
  }))
})

const dayunAnalysisBlocks = computed<AnalysisBlock[]>(() =>
  dayunNarrativeRows.value.map((row, idx) => ({
    id: `dayun-narrative-${idx}`,
    title: `${row.ganzhi} · 大运叙事`,
    lead: row.start_age != null && row.end_age != null ? `${row.start_age}–${row.end_age}岁` : '大运周期',
    body: row.narrative || '缺失',
    layer: 'heuristic' as const,
  })),
)

const dayunEngineBlocks = computed<AnalysisBlock[]>(() =>
  dayunEngineRows.value.map((row, idx) => ({
    id: `dayun-engine-${idx}`,
    title: `${row.ganzhi} · ${row.range}`,
    lead: row.tenGod || '大运',
    body: [row.gejuImpact, row.yongshenShiftLabel].filter(Boolean).join(' ') || '暂无引擎提示。',
    bullets: row.wealthHint ? [`财运（启发式）：${row.wealthHint}`] : undefined,
    layer: 'engine' as const,
  })),
)

const explainBlocks = computed(() => [
  ...analysisBlocks.value,
  ...dayunEngineBlocks.value,
  ...dayunAnalysisBlocks.value,
])

async function load() {
  await loadBazi()
}

async function loadDayunOnDemand() {
  await loadDayunNarratives(true)
}

const dayunNarrativeRows = computed(() => {
  const items = dayunReport.value?.items ?? []
  return items.slice(0, 3)
})

const dayunEngineRows = computed(() => {
  const items = dayunItems.value.slice(0, 5)
  return items.map((item) => buildDayunDisplayRow(item, {
    range: formatDayunRange(item),
    tenGod: item.ten_god,
  })).filter((row) => row.hasEngineHints || row.hasHeuristicHints)
})

function retryLoad() {
  void loadBazi(true)
}

function goZiwei() {
  router.push('/new/ziwei')
}

function goReport() {
  router.push('/report')
}

onMounted(() => {
  void load()
})
</script>

<template>
  <main class="fs-page bazi-page">
    <VolumeHead
      volume-id="vol1"
      :title="profileLabel"
      :desc="topSummary"
    >
      <template #actions>
        <button type="button" class="fs-btn fs-btn--ghost" @click="goZiwei">查看紫微</button>
        <button type="button" class="fs-btn fs-btn--primary" @click="goReport">进入报告</button>
      </template>
    </VolumeHead>

    <p v-if="caliberBanner" class="fs-caliber-banner" data-testid="bazi-caliber-banner">
      {{ caliberBanner }}
    </p>
    <p v-if="isCacheValid" class="fs-hint fs-hint--cache">已复用本次会话中的排盘结果。</p>
    <p v-if="timeWarnings.length" class="fs-hint fs-hint--warn">{{ timeWarnings.join(' · ') }}</p>

    <ResultStateCard
      v-if="loadingBazi"
      compact
      title="正在载入命盘"
      message="请稍候。"
    />
    <template v-else>
      <ResultStateCard
        v-if="error"
        title="当前八字服务暂时不可用。"
        :message="error"
        action-label="重新计算"
        @action="retryLoad"
      />

      <template v-if="result">
        <section data-testid="bazi-layer-summary">
          <SummaryStrip :items="summaryItems" />
        </section>

        <section
          v-if="depth === 'overview' && (missingFields.length || provenanceRows.length)"
          class="fs-card fs-card--flat"
          data-testid="bazi-trust-overview"
        >
          <EngineTrustPanel
            compact
            :missing-fields="missingFields"
            :provenance-rows="provenanceRows.slice(0, 4)"
          />
        </section>

        <div class="bazi-page__depth-row" role="group" aria-label="阅读深度">
          <div class="fs-depth-toggle" data-testid="bazi-depth-toggle">
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'overview' }"
              @click="depth = 'overview'"
            >
              速览
            </button>
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'structure' }"
              @click="depth = 'structure'"
            >
              结构
            </button>
            <button
              type="button"
              class="fs-depth-toggle__btn"
              :class="{ 'is-active': depth === 'deep' }"
              @click="depth = 'deep'"
            >
              深读
            </button>
          </div>
        </div>

        <section class="bazi-hero" data-testid="bazi-layer-structure">
          <div class="bazi-hero__chart fs-card--hero">
            <BaziReferenceTable
              :columns="columns"
              :active-key="activeKey"
              :hidden-contrib-by-ten-god="depth !== 'overview' ? hiddenContrib : undefined"
              :show-detail-rows="depth !== 'overview'"
            />
          </div>

          <aside class="bazi-hero__aside">
            <div class="fs-card fs-card--flat">
              <BaziLiuriTodayCard :liuri="liuriRaw" />
            </div>
            <div v-if="depth !== 'overview'" class="fs-card fs-card--flat">
              <BaziStructuralRelations
                :relations="relations"
                :pillar-details="pillarDetails"
              />
            </div>
          </aside>
        </section>

        <section v-if="depth !== 'overview'" class="fs-card" data-testid="bazi-vol2-block">
          <h2>卷二·业之象</h2>
          <p class="fs-codex-line"><strong>干支关系</strong> — {{ vol2Summary.relations }}</p>
          <p class="fs-codex-line"><strong>神煞摘要</strong> — {{ vol2Summary.shensha }}</p>
        </section>

        <section
          v-if="depth === 'structure' && dualTrackReference.length"
          class="fs-card fs-card--flat"
          data-testid="bazi-dual-track-block"
        >
          <DualTrackTable :rows="dualTrackReference" title="格局双轨对照" variant="reference" />
        </section>

        <section class="fs-trust-footnote" v-if="depth !== 'overview'" data-testid="bazi-layer-trust">
          <EngineTrustPanel
            compact
            :missing-fields="missingFields"
            :provenance-rows="provenanceRows"
            :dual-tracks="dualTracks"
            :validation-lines="validationLines"
            :liuri="liuri"
            :strength-factor-lines="strengthFactorLines"
            :bazi-structural="baziStructural"
            :cross-validation-items="showCrossValidationHint ? crossValidation.items : undefined"
          />
        </section>

        <section v-if="depth === 'deep'" class="fs-card" data-testid="bazi-layer-explain">
          <h2>卷一·命之根（深读）</h2>
          <AnalysisPanel :blocks="explainBlocks" default-open-id="bazi-0" />

          <div v-if="depth === 'deep'" class="fs-codex-line">
            <h2>大运叙事</h2>
            <button
              v-if="!dayunReport?.items?.length && !loadingDayun"
              type="button"
              class="fs-btn fs-btn--ghost"
              data-testid="bazi-load-dayun"
              @click="loadDayunOnDemand"
            >
              加载大运叙事（需主动触发）
            </button>
            <p v-if="loadingDayun" class="fs-hint fs-hint--cache">正在加载大运叙事…</p>
            <p v-else-if="dayunError" class="fs-hint fs-hint--warn">{{ dayunError }}</p>
          </div>
        </section>
      </template>
    </template>
  </main>
</template>

<style scoped>
.bazi-page {
  gap: var(--sp-6);
  min-width: 0;
  overflow-x: clip;
}

.bazi-page h2 {
  margin: 0 0 14px;
  font-family: var(--font-ui);
  font-size: 15px;
  font-weight: 600;
  color: var(--brand-ink);
}
</style>
