import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { CANG_GAN, NAYIN_MAP } from '@/data/ganzhi'
import type {
  WorkbenchBaziDayunItem,
  WorkbenchCurrentFortuneSummaryLike,
  WorkbenchDayMasterStrengthLike,
  WorkbenchGejuLike,
  WorkbenchBaziLiunianDetailItem,
  WorkbenchBaziLiunianItem,
  WorkbenchBaziLike,
  WorkbenchBaziShenshaItem,
  WorkbenchMonthlyFortuneItem,
  WorkbenchPillarKey,
  WorkbenchYongshenLike,
} from './workbenchTypes'

type TrendMeta = {
  text: string
  cls: 'up' | 'down' | 'flat'
}

type ScoreToneClass = 'c-good' | 'c-warn' | 'c-bad' | ''

type WuxingItem = {
  key: '木' | '火' | '土' | '金' | '水'
  val: number
}

type WuxingRadarAxis = {
  label: string
  x: number
  y: number
  color: string
}

type PillarItem = {
  key: WorkbenchPillarKey
  label: string
  stem: string
  branch: string
  shishen: string
  isDay: boolean
  stemColor: string
  branchColor: string
}

type LiunianDetailRow = {
  year: number
  ganzhi: string
  annualScore: number
  tenGod: string
  flowWuxing: string
  clash: string
  domains: Array<{ key: string; val: string }>
  taiSuiRelations: string[]
  clashPillars: string[]
  notableMonths: number[]
  optimalAction: string
  interpretationText: string
  tags: string[]
  isCurrent: boolean
}

type LiuyueHeatmapItem = WorkbenchMonthlyFortuneItem & {
  score: number
  heatBar: string
  heatBg: string
  isSelected: boolean
  isCurrent: boolean
  isLinked: boolean
}

type LiuyueTrendSvg = {
  w: number
  h: number
  pts: Array<{ x: number; y: number; color: string; label: string }>
}

type DayunTimelineItem = WorkbenchBaziDayunItem & {
  startYear: number | null
  endYear: number | null
  startAge: number | null
  endAge: number | null
  isActive: boolean
  isPast: boolean
  progress: number
  ganzhi: string
  stemColor: string
  branchColor: string
}

type LiunianTimelineItem = WorkbenchBaziLiunianItem & {
  annualScore: number | null
  clash: string
  optimalAction: string
  tags: string[]
  isCurrent: boolean
  stemColor: string
  branchColor: string
}

type LiunianSparkline = {
  w: number
  h: number
  pts: Array<{ x: number; y: number; s: number }>
  line: string
  area: string
}

export type ChartSummaryCards = {
  dayunGz: string
  dayunYearsLeft: number | null
  lyGz: string
  lyShishen: string
  lyAnnualScore: number | null
  lyTrend: TrendMeta
  lyueGz: string
  lyueLuck: string
  lyueTrend: TrendMeta
  balanceScore: number | null
  balanceText: string
  weakList: string
  strongList: string
  wscore: WorkbenchBaziLike['wuxing_score']
  balanceTone: ScoreToneClass
}

type BaziKeyIndicators = {
  geju: string
  gejuLevel: string
  yongshen: string
  yongshenStar: string
  topGoodShensha: WorkbenchBaziShenshaItem[]
  topBadShensha: WorkbenchBaziShenshaItem[]
  weakList: string
}

type IndicatorShenshaItem = {
  key: string
  name: string
  pillar?: string
  isBeneficial: boolean
  meaning: string
  advice: string
}

type ShenshaByPillarItem = {
  key: WorkbenchPillarKey
  label: string
  good: WorkbenchBaziShenshaItem[]
  bad: WorkbenchBaziShenshaItem[]
}

type CangganNayinRow = {
  key: WorkbenchPillarKey
  label: string
  canggan: string
  nayin: string
}

type ActivePillarDetail = PillarItem & {
  canggan: string
  nayin: string
  stemWx: string
  branchWx: string
  goodShensha: WorkbenchBaziShenshaItem[]
  badShensha: WorkbenchBaziShenshaItem[]
}

type UseWorkbenchBaziPanelReturn = {
  currentYear: number
  selectedIndicatorShensha: Ref<string | null>
  dayunItems: ComputedRef<WorkbenchBaziDayunItem[]>
  liunianItems: ComputedRef<WorkbenchBaziLiunianItem[]>
  wuxing: ComputedRef<WuxingItem[]>
  wuxingMax: ComputedRef<number>
  wuxingRadarPoints: ComputedRef<string>
  wuxingRadarAxes: ComputedRef<WuxingRadarAxis[]>
  pillars: ComputedRef<PillarItem[]>
  geju: ComputedRef<WorkbenchGejuLike | null | undefined>
  yongshen: ComputedRef<WorkbenchYongshenLike | null | undefined>
  summary: ComputedRef<string | null>
  strength: ComputedRef<WorkbenchDayMasterStrengthLike | null | undefined>
  dayStemColor: ComputedRef<string>
  thisYearDetail: ComputedRef<WorkbenchBaziLiunianDetailItem | null>
  liunianDetailRows: ComputedRef<LiunianDetailRow[]>
  activeLiunianDetailYear: Ref<number | null>
  expandedLiunianDetailYear: ComputedRef<number | null>
  activeLiunianDetail: ComputedRef<LiunianDetailRow | null>
  toggleLiunianDetail: (year: number) => void
  activeLiuyueMonth: Ref<number | null>
  activeLiuyueDetail: ComputedRef<WorkbenchMonthlyFortuneItem | null>
  selectLiuyue: (month: number) => void
  liuyueHeatmapData: ComputedRef<LiuyueHeatmapItem[]>
  liuyueTrendSvg: ComputedRef<LiuyueTrendSvg | null>
  linkedLiuyueMonths: ComputedRef<number[]>
  selectLiunianMonth: (year: number, month: number) => void
  dayunTimelineItems: ComputedRef<DayunTimelineItem[]>
  activeDayunTimelineItem: ComputedRef<DayunTimelineItem | null>
  selectDayun: (startYear: number | null) => void
  liunianTimelineItems: ComputedRef<LiunianTimelineItem[]>
  liunianSparkline: ComputedRef<LiunianSparkline | null>
  activeLiunianTimelineItem: ComputedRef<LiunianTimelineItem | null>
  activeLiunianDayunInfo: ComputedRef<DayunTimelineItem | null>
  chartSummaryCards: ComputedRef<ChartSummaryCards | null>
  baziKeyIndicators: ComputedRef<BaziKeyIndicators | null>
  indicatorShenshaItems: ComputedRef<IndicatorShenshaItem[]>
  activeIndicatorShensha: ComputedRef<IndicatorShenshaItem | null>
  toggleIndicatorShensha: (itemKey: string) => void
  fortSummary: ComputedRef<WorkbenchCurrentFortuneSummaryLike | null | undefined>
  shenshaByPillar: ComputedRef<ShenshaByPillarItem[]>
  cangganNayinRows: ComputedRef<CangganNayinRow[]>
  activePillarKey: Ref<WorkbenchPillarKey>
  activePillarDetail: ComputedRef<ActivePillarDetail | null>
  selectPillar: (key: WorkbenchPillarKey) => void
}

const STEM_WX: Record<string, string> = {
  甲: '木', 乙: '木',
  丙: '火', 丁: '火',
  戊: '土', 己: '土',
  庚: '金', 辛: '金',
  壬: '水', 癸: '水',
}

const BRANCH_WX: Record<string, string> = {
  子: '水', 丑: '土', 寅: '木', 卯: '木', 辰: '土', 巳: '火',
  午: '火', 未: '土', 申: '金', 酉: '金', 戌: '土', 亥: '水',
}

const LUCK_RANK: Record<string, number> = { '吉': 1, '平': 0, '凶': -1 }
const LIUYUE_SCORE: Record<string, number> = { '吉': 100, '平': 50, '凶': 0 }
const PILLAR_LABELS = ['年柱', '月柱', '日柱', '时柱'] as const

const SHENSHA_BRIEF_MAP: Record<string, { meaning: string; goodAdvice: string; badAdvice: string }> = {
  天乙贵人: { meaning: '主遇贵扶持、逢难有解。', goodAdvice: '适合推进合作、求助权威资源。', badAdvice: '避免依赖他人，重要决策仍需自证。' },
  文昌贵人: { meaning: '主学习、考试、文书表达。', goodAdvice: '适合考试申报、写作汇报与复盘。', badAdvice: '避免文书疏漏，关键条款需复核。' },
  桃花: { meaning: '主人缘、社交与情感活跃。', goodAdvice: '适合拓展关系与公共沟通。', badAdvice: '边界优先，谨防情绪与关系消耗。' },
  驿马: { meaning: '主变动、奔波、出行迁移。', goodAdvice: '适合外出拓展、跑动项目。', badAdvice: '控制节奏，避免频繁变动导致失焦。' },
  羊刃: { meaning: '主刚烈与冲劲，易激进。', goodAdvice: '可用于攻坚，但需设风险阈值。', badAdvice: '避免硬碰硬，先稳后动。' },
  劫煞: { meaning: '主争夺与损耗风险。', goodAdvice: '加强边界管理与资源盘点。', badAdvice: '避免高杠杆与冲动投入。' },
  灾煞: { meaning: '主突发阻滞与杂务干扰。', goodAdvice: '预留缓冲时间和备选方案。', badAdvice: '不宜冒险推进高不确定事项。' },
  白虎: { meaning: '主冲突、伤灾与高压事件。', goodAdvice: '流程合规、风险检查前置。', badAdvice: '减少对抗情境与危险场景暴露。' },
}

function wxColor(key: string): string {
  const WX_COLOR: Record<string, string> = {
    wood: 'var(--wx-wood)',
    fire: 'var(--wx-fire)',
    earth: 'var(--wx-earth)',
    metal: 'var(--wx-metal)',
    water: 'var(--wx-water)',
    木: 'var(--wx-wood)',
    火: 'var(--wx-fire)',
    土: 'var(--wx-earth)',
    金: 'var(--wx-metal)',
  }
  return WX_COLOR[key] ?? 'var(--text-2)'
}

function trendMeta(diff: number | null | undefined): TrendMeta {
  if (diff == null || Number.isNaN(diff) || diff === 0) return { text: '→ 持平', cls: 'flat' }
  if (diff > 0) return { text: `↑ ${Math.abs(diff).toFixed(0)}`, cls: 'up' }
  return { text: `↓ ${Math.abs(diff).toFixed(0)}`, cls: 'down' }
}

function scoreToneClass(score: number | null | undefined): ScoreToneClass {
  if (score == null || Number.isNaN(score)) return ''
  if (score >= 80) return 'c-good'
  if (score >= 60) return 'c-warn'
  return 'c-bad'
}

export function useWorkbenchBaziPanel(localBazi: Ref<WorkbenchBaziLike | null>): UseWorkbenchBaziPanelReturn {
  const currentYear = new Date().getFullYear()
  const B = localBazi
  const selectedIndicatorShensha = ref<string | null>(null)

  const dayunItems = computed(() => {
    const items = localBazi.value?.dayun?.items ?? []
    return items.slice(0, 8)
  })

  const liunianItems = computed(() => {
    const items = localBazi.value?.liunian?.items ?? []
    const idx = items.findIndex((item: { year: number }) => item.year === currentYear)
    const start = Math.max(0, idx - 2)
    return items.slice(start, start + 5)
  })

  const wuxing = computed<WuxingItem[]>(() => {
    const score = localBazi.value?.wuxing_score
    if (!score) return []
    return [
      { key: '木', val: score.wood },
      { key: '火', val: score.fire },
      { key: '土', val: score.earth },
      { key: '金', val: score.metal },
      { key: '水', val: score.water },
    ]
  })

  const wuxingMax = computed(() => Math.max(...wuxing.value.map(item => item.val), 1))

  const wuxingRadarPoints = computed(() => {
    const list = wuxing.value
    if (!list.length) return ''
    const max = wuxingMax.value
    const cx = 70
    const cy = 70
    const radius = 54
    const toRad = (deg: number) => (deg * Math.PI) / 180
    return list.map((item, index) => {
      const angle = toRad(-90 + (360 / list.length) * index)
      const valueRadius = (item.val / max) * radius
      return `${cx + valueRadius * Math.cos(angle)},${cy + valueRadius * Math.sin(angle)}`
    }).join(' ')
  })

  const wuxingRadarAxes = computed(() => {
    const list = wuxing.value
    const cx = 70
    const cy = 70
    const radius = 54
    const toRad = (deg: number) => (deg * Math.PI) / 180
    return list.map((item, index) => {
      const angle = toRad(-90 + (360 / list.length) * index)
      return {
        label: item.key,
        x: cx + (radius + 16) * Math.cos(angle),
        y: cy + (radius + 16) * Math.sin(angle),
        color: wxColor(item.key),
      }
    })
  })

  const pillars = computed(() => {
    const primary = B.value?.pillars_primary
    const tenGods = B.value?.ten_gods
    if (!primary || !tenGods) return []
    const keys = ['year', 'month', 'day', 'hour'] as const
    return keys.map((key, index) => ({
      key,
      label: PILLAR_LABELS[index],
      stem: primary[key].stem,
      branch: primary[key].branch,
      shishen: key === 'day' ? '日主' : (tenGods[key] ?? '—'),
      isDay: key === 'day',
      stemColor: wxColor(STEM_WX[primary[key].stem] ?? ''),
      branchColor: wxColor(BRANCH_WX[primary[key].branch] ?? ''),
    }))
  })

  const geju = computed(() => B.value?.geju)
  const yongshen = computed(() => B.value?.yongshen)
  const summary = computed(() => B.value?.bazi_summary ?? null)
  const strength = computed(() => B.value?.day_master_strength)
  const dayStemColor = computed(() => wxColor(STEM_WX[pillars.value[2]?.stem ?? ''] ?? ''))
  const thisYearDetail = computed(() =>
    (B.value?.liunian_detail ?? []).find((item: { year: number }) => item.year === currentYear) ?? null,
  )

  const liunianDetailRows = computed(() => {
    const items = (B.value?.liunian_detail ?? []) as WorkbenchBaziLiunianDetailItem[]
    if (!items.length) return []
    const idx = items.findIndex(item => item.year === currentYear)
    const start = Math.max(0, (idx >= 0 ? idx : 0) - 2)
    return items.slice(start, start + 5).map(item => ({
      year: item.year,
      ganzhi: item.ganzhi ?? '—',
      annualScore: item.annual_score ?? 0,
      tenGod: item.ten_god ?? '',
      flowWuxing: item.flow_wuxing ?? '',
      clash: item.clash ?? '',
      domains: Object.entries(item.domain_forecasts ?? {}).map(([key, val]) => ({ key, val })),
      taiSuiRelations: item.tai_sui_relations ?? [],
      clashPillars: item.clash_pillars ?? [],
      notableMonths: item.notable_months ?? [],
      optimalAction: item.optimal_action ?? '',
      interpretationText: item.interpretation_text ?? '',
      tags: item.inference_tags ?? [],
      isCurrent: item.year === currentYear,
    }))
  })

  const activeLiunianDetailYear = ref<number | null>(currentYear)
  const expandedLiunianDetailYear = computed(() =>
    activeLiunianDetailYear.value
    ?? liunianDetailRows.value.find(item => item.isCurrent)?.year
    ?? liunianDetailRows.value[0]?.year
    ?? null,
  )
  const activeLiunianDetail = computed(() =>
    liunianDetailRows.value.find(item => item.year === expandedLiunianDetailYear.value) ?? null,
  )

  const activeLiuyueMonth = ref<number | null>(new Date().getMonth() + 1)

  function toggleLiunianDetail(year: number) {
    activeLiunianDetailYear.value = year
    const detail = liunianDetailRows.value.find(item => item.year === year)
    if (detail?.year === currentYear && detail.notableMonths.length) {
      if (!detail.notableMonths.includes(activeLiuyueMonth.value ?? -1)) {
        activeLiuyueMonth.value = detail.notableMonths[0] ?? activeLiuyueMonth.value
      }
    }
  }

  const activeLiuyueDetail = computed(() => {
    const rows = (B.value?.monthly_fortune ?? []) as WorkbenchMonthlyFortuneItem[]
    const currentMonth = new Date().getMonth() + 1
    return rows.find(item => item.month === activeLiuyueMonth.value)
      ?? rows.find(item => item.month === currentMonth)
      ?? rows[0]
      ?? null
  })

  function selectLiuyue(month: number) {
    activeLiuyueMonth.value = month
  }

  const linkedLiuyueMonths = computed(() =>
    activeLiunianDetail.value?.year === currentYear ? activeLiunianDetail.value.notableMonths : [],
  )

  const liuyueHeatmapData = computed(() => {
    const rows = (B.value?.monthly_fortune ?? []) as WorkbenchMonthlyFortuneItem[]
    const thisMonth = new Date().getMonth() + 1
    return rows.map(item => {
      const color = item.color_hint || (item.luck_level === '吉' ? '#2E8B57' : item.luck_level === '凶' ? '#DC1432' : '#888888')
      const opHex = item.luck_level === '平' ? '18' : '2e'
      return {
        ...item,
        score: LIUYUE_SCORE[item.luck_level] ?? 50,
        heatBar: color,
        heatBg: `${color}${opHex}`,
        isSelected: item.month === activeLiuyueMonth.value,
        isCurrent: item.month === thisMonth,
        isLinked: linkedLiuyueMonths.value.includes(item.month),
      }
    })
  })

  const liuyueTrendSvg = computed(() => {
    const items = liuyueHeatmapData.value
    if (items.length < 2) return null
    const w = 360
    const h = 28
    const pad = 6
    const pts = items.map((item, index) => ({
      x: pad + ((w - pad * 2) / (items.length - 1)) * index,
      y: pad + (h - pad * 2) * (1 - (LIUYUE_SCORE[item.luck_level] ?? 50) / 100),
      color: item.heatBar,
      label: `${item.month}月 ${item.luck_level}`,
    }))
    return { w, h, pts }
  })

  function selectLiunianMonth(year: number, month: number) {
    activeLiunianDetailYear.value = year
    if (year === currentYear) {
      activeLiuyueMonth.value = month
    }
  }

  const dayunTimelineItems = computed(() =>
    dayunItems.value.map((item: { stem?: string; branch?: string; start_year?: number; start_age?: number; ten_god?: string; flow_wuxing?: string; wealth_hint?: string; love_hint?: string; health_hint?: string; narrative?: string }, index: number, arr: Array<{ start_year?: number; start_age?: number }>) => {
      const startYear = item.start_year ?? null
      const nextStartYear = arr[index + 1]?.start_year ?? null
      const endYear = nextStartYear ? nextStartYear - 1 : null
      const startAge = item.start_age ?? null
      const nextStartAge = arr[index + 1]?.start_age ?? null
      const endAge = nextStartAge ? nextStartAge - 1 : null
      const isActive = startYear != null && startYear <= currentYear && (endYear == null || endYear >= currentYear)
      const isPast = endYear != null && endYear < currentYear
      const progress = isActive && startYear != null && endYear != null && endYear >= startYear
        ? Math.max(8, Math.min(100, ((currentYear - startYear + 1) / (endYear - startYear + 1)) * 100))
        : isPast ? 100 : 0
      return {
        ...item,
        startYear,
        endYear,
        startAge,
        endAge,
        isActive,
        isPast,
        progress,
        ganzhi: `${item.stem ?? ''}${item.branch ?? ''}` || '—',
        stemColor: wxColor(STEM_WX[item.stem ?? ''] ?? ''),
        branchColor: wxColor(BRANCH_WX[item.branch ?? ''] ?? ''),
      }
    }),
  )

  const activeDayunStartYear = ref<number | null>(null)
  const activeDayunTimelineItem = computed(() =>
    dayunTimelineItems.value.find((item: { startYear: number | null }) => item.startYear === activeDayunStartYear.value)
    ?? dayunTimelineItems.value.find((item: { isActive: boolean }) => item.isActive)
    ?? dayunTimelineItems.value[0]
    ?? null,
  )

  function selectDayun(startYear: number | null) {
    activeDayunStartYear.value = startYear
  }

  const liunianTimelineItems = computed(() => {
    const detailMap = new Map<number, WorkbenchBaziLiunianDetailItem>(((B.value?.liunian_detail ?? []) as WorkbenchBaziLiunianDetailItem[]).map(item => [item.year, item]))
    return liunianItems.value.map((item: { year: number; stem: string; branch: string; ten_god?: string; clash?: string | null }) => {
      const detail = detailMap.get(item.year)
      return {
        ...item,
        annualScore: detail?.annual_score ?? null,
        clash: detail?.clash ?? item.clash ?? '',
        optimalAction: detail?.optimal_action ?? '',
        tags: detail?.inference_tags ?? [],
        isCurrent: item.year === currentYear,
        stemColor: wxColor(STEM_WX[item.stem] ?? ''),
        branchColor: wxColor(BRANCH_WX[item.branch] ?? ''),
      }
    })
  })

  const liunianSparkline = computed(() => {
    const scores = liunianTimelineItems.value
      .map((item: { annualScore: number | null }) => item.annualScore)
      .filter((score: number | null): score is number => score != null)
    if (scores.length < 2) return null
    const w = 220
    const h = 36
    const pad = 4
    const min = Math.min(...scores)
    const max = Math.max(...scores, min + 1)
    const pts = scores.map((score: number, index: number) => ({
      x: pad + ((w - pad * 2) / (scores.length - 1)) * index,
      y: pad + (h - pad * 2) * (1 - (score - min) / (max - min)),
      s: score,
    }))
    const line = pts.map((point: { x: number; y: number }, index: number) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ')
    const area = `${line} L ${pts[pts.length - 1].x.toFixed(1)} ${h} L ${pts[0].x.toFixed(1)} ${h} Z`
    return { w, h, pts, line, area }
  })

  const activeLiunianTimelineItem = computed(() =>
    liunianTimelineItems.value.find((item: { year: number }) => item.year === expandedLiunianDetailYear.value)
    ?? liunianTimelineItems.value.find((item: { isCurrent: boolean }) => item.isCurrent)
    ?? liunianTimelineItems.value[0]
    ?? null,
  )

  const activeLiunianDayunInfo = computed(() => {
    const year = expandedLiunianDetailYear.value
    if (!year) return null
    return dayunTimelineItems.value.find((item: { startYear: number | null; endYear: number | null }) =>
      item.startYear != null && item.startYear <= year && (item.endYear == null || item.endYear >= year),
    ) ?? null
  })

  const chartSummaryCards = computed<ChartSummaryCards | null>(() => {
    if (!B.value) return null
    const dayun = B.value.dayun
    const currentDayun = dayun?.items?.find((item: { start_year?: number; end_year?: number }) =>
      (item.start_year ?? 0) <= currentYear && (item.end_year ?? 9999) >= currentYear,
    ) ?? dayun?.items?.[0]
    const dayunGz = currentDayun ? `${currentDayun.stem ?? ''}${currentDayun.branch ?? ''}` : '—'
    const dayunYearsLeft = currentDayun?.end_year ? currentDayun.end_year - currentYear : null

    const liunianItem = liunianItems.value.find((item: { year: number }) => item.year === currentYear)
    const liunianGz = liunianItem ? `${liunianItem.stem ?? ''}${liunianItem.branch ?? ''}` : '—'
    const liunianShishen = liunianItem?.ten_god ?? ''
    const liunianDetail = (B.value.liunian_detail ?? []).find((item: { year?: number }) => item.year === currentYear)
    const prevLiunianDetail = (B.value.liunian_detail ?? []).find((item: { year?: number }) => item.year === currentYear - 1)
    const liunianAnnualScore = liunianDetail?.annual_score ?? null
    const liunianTrend = trendMeta(
      liunianAnnualScore != null && prevLiunianDetail?.annual_score != null
        ? liunianAnnualScore - prevLiunianDetail.annual_score
        : null,
    )

    const nowMonth = new Date().getMonth() + 1
    const monthlyFortune = B.value.monthly_fortune ?? []
    const currentMonth = monthlyFortune.find((item: { month: number }) => item.month === nowMonth)
    const prevMonth = monthlyFortune.find((item: { month: number }) => item.month === nowMonth - 1)
    const liuyueGz = currentMonth ? (currentMonth.month_ganzhi ?? currentMonth.month_dizhi ?? '—') : '—'
    const liuyueLuck = currentMonth?.luck_level ?? ''
    const liuyueTrend = trendMeta(
      currentMonth && prevMonth
        ? (LUCK_RANK[currentMonth.luck_level] ?? 0) - (LUCK_RANK[prevMonth.luck_level] ?? 0)
        : null,
    )

    const wuxingScore = B.value.wuxing_score
    const balanceScore = B.value.wuxing_balance_score
    const balanceText = B.value.balance_advice ?? ''
    const weakList = (B.value.wuxing_weak ?? []).join('、') || '无'
    const strongList = (B.value.wuxing_strong ?? []).join('、') || '无'
    const balanceTone = scoreToneClass(balanceScore)

    return {
      dayunGz,
      dayunYearsLeft,
      lyGz: liunianGz,
      lyShishen: liunianShishen,
      lyAnnualScore: liunianAnnualScore,
      lyTrend: liunianTrend,
      lyueGz: liuyueGz,
      lyueLuck: liuyueLuck,
      lyueTrend: liuyueTrend,
      balanceScore: balanceScore ?? null,
      balanceText,
      weakList,
      strongList,
      wscore: wuxingScore,
      balanceTone,
    }
  })

  const baziKeyIndicators = computed(() => {
    if (!B.value) return null
    const shensha = (B.value.shensha ?? []) as WorkbenchBaziShenshaItem[]
    return {
      geju: (B.value.geju?.name ?? '') as string,
      gejuLevel: (B.value.geju?.level ?? '') as string,
      yongshen: (B.value.yongshen?.god_element ?? B.value.yongshen?.element ?? '') as string,
      yongshenStar: (B.value.yongshen?.star ?? B.value.yongshen?.name ?? '') as string,
      topGoodShensha: shensha.filter(item => item.is_beneficial).slice(0, 2),
      topBadShensha: shensha.filter(item => !item.is_beneficial).slice(0, 2),
      weakList: ((B.value.wuxing_weak ?? []) as string[]).join('、') || '',
    }
  })

  const indicatorShenshaItems = computed(() => {
    const indicators = baziKeyIndicators.value
    if (!indicators) return [] as IndicatorShenshaItem[]
    const all = [
      ...indicators.topGoodShensha.map(item => ({ ...item, isBeneficial: true })),
      ...indicators.topBadShensha.map(item => ({ ...item, isBeneficial: false })),
    ]
    return all
      .filter(item => !!item.name)
      .map(item => {
        const name = item.name as string
        const brief = SHENSHA_BRIEF_MAP[name]
        return {
          key: `${item.isBeneficial ? 'good' : 'bad'}-${name}`,
          name,
          pillar: item.pillar,
          isBeneficial: item.isBeneficial,
          meaning: brief?.meaning ?? '该神煞用于补充判断气机倾向，需结合四柱与大运流年综合解读。',
          advice: item.isBeneficial
            ? (brief?.goodAdvice ?? '可顺势借力，在优势场景放大收益。')
            : (brief?.badAdvice ?? '建议先控风险与节奏，再推进关键动作。'),
        }
      })
  })

  const activeIndicatorShensha = computed(() => {
    const items = indicatorShenshaItems.value
    if (!items.length) return null
    return items.find(item => item.key === selectedIndicatorShensha.value) ?? items[0]
  })

  function toggleIndicatorShensha(itemKey: string) {
    selectedIndicatorShensha.value = selectedIndicatorShensha.value === itemKey ? null : itemKey
  }

  const fortSummary = computed(() => B.value?.current_fortune_summary)
  const shenshaItems = computed<WorkbenchBaziShenshaItem[]>(() => B.value?.shensha ?? [])

  const shenshaByPillar = computed<ShenshaByPillarItem[]>(() => {
    const labels: Array<{ key: WorkbenchPillarKey; label: string }> = [
      { key: 'year', label: '年柱' },
      { key: 'month', label: '月柱' },
      { key: 'day', label: '日柱' },
      { key: 'hour', label: '时柱' },
    ]
    const normalize = (value: string | undefined) => (value ?? '').toLowerCase()
    return labels.map(({ key, label }) => {
      const items = shenshaItems.value.filter((item: { pillar?: string; is_beneficial: boolean }) => {
        const pillar = normalize(item.pillar)
        return pillar.includes(key) || pillar.includes(label)
      })
      return {
        key,
        label,
        good: items.filter((item: { is_beneficial: boolean }) => item.is_beneficial).slice(0, 4),
        bad: items.filter((item: { is_beneficial: boolean }) => !item.is_beneficial).slice(0, 4),
      }
    })
  })

  const cangganNayinRows = computed(() => {
    const primary = B.value?.pillars_primary
    if (!primary) return []
    const keys = ['year', 'month', 'day', 'hour'] as const
    return keys.map((key, index) => {
      const stem = primary[key].stem
      const branch = primary[key].branch
      return {
        key,
        label: PILLAR_LABELS[index],
        canggan: (CANG_GAN[branch] ?? []).join(' / '),
        nayin: NAYIN_MAP[stem + branch] ?? '—',
      }
    })
  })

  const activePillarKey = ref<WorkbenchPillarKey>('day')
  const activePillarDetail = computed(() => {
    const pillar = pillars.value.find(item => item.key === activePillarKey.value)
    const meta = cangganNayinRows.value.find(item => item.key === activePillarKey.value)
    const shensha = shenshaByPillar.value.find(item => item.key === activePillarKey.value)
    if (!pillar || !meta) return null
    return {
      ...pillar,
      canggan: meta.canggan || '—',
      nayin: meta.nayin || '—',
      stemWx: STEM_WX[pillar.stem] ?? '—',
      branchWx: BRANCH_WX[pillar.branch] ?? '—',
      goodShensha: shensha?.good ?? [],
      badShensha: shensha?.bad ?? [],
    }
  })

  function selectPillar(key: WorkbenchPillarKey) {
    activePillarKey.value = key
  }

  return {
    currentYear,
    selectedIndicatorShensha,
    dayunItems,
    liunianItems,
    wuxing,
    wuxingMax,
    wuxingRadarPoints,
    wuxingRadarAxes,
    pillars,
    geju,
    yongshen,
    summary,
    strength,
    dayStemColor,
    thisYearDetail,
    liunianDetailRows,
    activeLiunianDetailYear,
    expandedLiunianDetailYear,
    activeLiunianDetail,
    toggleLiunianDetail,
    activeLiuyueMonth,
    activeLiuyueDetail,
    selectLiuyue,
    liuyueHeatmapData,
    liuyueTrendSvg,
    linkedLiuyueMonths,
    selectLiunianMonth,
    dayunTimelineItems,
    activeDayunTimelineItem,
    selectDayun,
    liunianTimelineItems,
    liunianSparkline,
    activeLiunianTimelineItem,
    activeLiunianDayunInfo,
    chartSummaryCards,
    baziKeyIndicators,
    indicatorShenshaItems,
    activeIndicatorShensha,
    toggleIndicatorShensha,
    fortSummary,
    shenshaByPillar,
    cangganNayinRows,
    activePillarKey,
    activePillarDetail,
    selectPillar,
  }
}
