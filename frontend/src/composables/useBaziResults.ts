/**
 * useBaziResults.ts — 八字排盘结果的衍生计算与展示状态
 *
 * 提供：
 *  - currentYear             当前年份（常量）
 *  - dayunItems              大运列表
 *  - dayunSelected           选中展开的大运索引（mutable ref）
 *  - dayunActiveIdx          当前大运索引
 *  - pillars                 四柱数组（年月日时）
 *  - wuxingBars              五行柱状图数据
 *  - radarPoints / radarLabels / radarBg / radarBgHalf  五行雷达图
 *  - RADAR_ANGLES / RADAR_CX / RADAR_CY                雷达图常量
 *  - tgColor / wxColor / wxZh / scoreColor              颜色辅助函数
 *  - dayMasterDesc           日主描述文本
 *  - baziSummaryFallback     命局综合总评（含自动生成降级文本）
 *  - currentDayunDesc        当前大运描述文本
 *  - overviewGuideCards / overviewReadingSteps / overviewTerms  导读内容
 *  - rawResultJson           原始结果 JSON 字符串
 */
import { ref, computed, type Ref } from 'vue'
import { STEM_ELEMENT } from '@/data/ganzhi'
import type { BaziResponse, WuxingScore, DayunItem } from '@/api/bazi'

// ── 十神颜色 ─────────────────────────────────────────────────────────────────
const TEN_GOD_COLORS: Record<string, string> = {
  '比肩': '#3b82f6', '劫财': '#6366f1',
  '食神': '#10b981', '伤官': '#f59e0b',
  '正财': '#ef4444', '偏财': '#f97316',
  '正官': '#7c3aed', '七杀': '#dc2626',
  '正印': '#065f46', '偏印': '#0891b2',
}

// ── 五行雷达图常量：12点起顺时针 木→火→土→金→水 ────────────────────────────
const RADAR_ELEMENTS = ['木', '火', '土', '金', '水']
export const RADAR_ANGLES = [270, 342, 54, 126, 198].map(d => (d * Math.PI) / 180)
export const RADAR_CX = 100
export const RADAR_CY = 100
export const RADAR_R  = 72

const WX_ZH: Record<string, string> = {
  wood: '木', fire: '火', earth: '土', metal: '金', water: '水',
  Wood: '木', Fire: '火', Earth: '土', Metal: '金', Water: '水',
  '木': '木', '火': '火', '土': '土', '金': '金', '水': '水',
}

const TIER_ZH: Record<string, string> = {
  strong: '偏旺', very_strong: '极旺', too_strong: '极旺',
  weak: '偏弱',   very_weak: '极弱',  too_weak: '极弱',
  neutral: '中等', balanced: '均衡', pending: '',
}

const TG_ADV: Record<string, string> = {
  '比肩': '人际助力增强，宜拓展合作，但也需防同行竞争与资源分歧。',
  '劫财': '财务易有变动，防合伙纠纷；但行动力与决断力提升，宜果断出击。',
  '食神': '才华展现期，贵人机缘多，事业渐佳；注意劳逸平衡，爱护身体。',
  '伤官': '才智外露，适合创业、艺术、技术突破；官场运偏弱，宜避免与权威正面冲突。',
  '正财': '稳定财运期，职场踏实进取，适合守成积累、稳步晋升。',
  '偏财': '偏财运旺，机遇多变，适合投资、经商；宜把握机遇，注意风险控制。',
  '正官': '官运亨通，仕途顺遂，有晋升机会，利考核与评定，宜遵规守纪。',
  '七杀': '压力与挑战并存，逆境磨砺意志；宜避免正面冲突，寻求化泄消解之道。',
  '正印': '贵人庇护有力，学业与资格考试顺利，适合进修深造、修身养性。',
  '偏印': '直觉敏锐，适合研究、技术类工作；防孤僻与过度内敛，注意开拓社交。',
}

export function useBaziResults(result: Ref<BaziResponse | null>) {
  const currentYear = new Date().getFullYear()
  const WX_LIST = [
    { key: 'wood',  label: '木', color: 'var(--wx-wood)' },
    { key: 'fire',  label: '火', color: 'var(--wx-fire)' },
    { key: 'earth', label: '土', color: 'var(--wx-earth)' },
    { key: 'metal', label: '金', color: 'var(--wx-metal)' },
    { key: 'water', label: '水', color: 'var(--wx-water)' },
  ]

  // 大运选中（展开详情）
  const dayunSelected = ref(-1)

  // ── 颜色辅助 ───────────────────────────────────────────────────────────────
  function tgColor(tg: string): string {
    return TEN_GOD_COLORS[tg] ?? 'var(--text-3)'
  }

  function wxColor(el: string): string {
    const wx: Record<string, string> = {
      '木': 'var(--wx-wood)', '火': 'var(--wx-fire)', '土': 'var(--wx-earth)',
      '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
    }
    return wx[el] ?? 'currentColor'
  }

  function wxZh(s: string): string {
    return WX_ZH[s] ?? s
  }

  function scoreColor(score: number): string {
    if (score >= 80) return '#15803d'
    if (score >= 60) return '#d97706'
    return '#dc2626'
  }

  // ── 四柱 ──────────────────────────────────────────────────────────────────
  const pillars = computed(() => {
    const pp = result.value?.pillars_primary
    if (!pp) return []
    const tg = result.value?.ten_gods ?? {}
    return [
      { label: '年柱', data: pp.year,  shishen: tg.year  ?? '', isDay: false },
      { label: '月柱', data: pp.month, shishen: tg.month ?? '', isDay: false },
      { label: '日柱', data: pp.day,   shishen: '日元',          isDay: true  },
      { label: '时柱', data: pp.hour,  shishen: tg.hour  ?? '', isDay: false },
    ]
  })

  // ── 大运 ──────────────────────────────────────────────────────────────────
  const dayunItems = computed((): DayunItem[] => result.value?.dayun?.items ?? [])

  const dayunActiveIdx = computed((): number =>
    dayunItems.value.findIndex(
      c => c.start_year != null && c.start_year <= currentYear && (c.start_year + 10) > currentYear
    )
  )

  // ── 五行柱状图 ──────────────────────────────────────────────────────────────
  const wuxingBars = computed(() => {
    const wx = result.value?.wuxing_score as WuxingScore | undefined
    if (!wx) return []
    const total = WX_LIST.reduce((s, e) => s + (wx[e.key] || 0), 0) || 1
    return WX_LIST.map(e => ({
      ...e,
      val: wx[e.key] || 0,
      pct: Math.round((wx[e.key] || 0) / total * 100),
    }))
  })

  // ── 五行雷达图 ──────────────────────────────────────────────────────────────
  const radarBg = RADAR_ANGLES.map(a =>
    `${(RADAR_CX + RADAR_R * Math.cos(a)).toFixed(1)},${(RADAR_CY + RADAR_R * Math.sin(a)).toFixed(1)}`
  ).join(' ')

  const radarBgHalf = RADAR_ANGLES.map(a =>
    `${(RADAR_CX + RADAR_R * 0.5 * Math.cos(a)).toFixed(1)},${(RADAR_CY + RADAR_R * 0.5 * Math.sin(a)).toFixed(1)}`
  ).join(' ')

  const radarPoints = computed(() => {
    const s = result.value?.wuxing_score
    if (!s) return radarBg
    const vals = [s.wood, s.fire, s.earth, s.metal, s.water]
    const maxVal = Math.max(...vals, 1)
    return RADAR_ANGLES.map((angle, i) => {
      const r = RADAR_R * (vals[i] / maxVal)
      return `${(RADAR_CX + r * Math.cos(angle)).toFixed(1)},${(RADAR_CY + r * Math.sin(angle)).toFixed(1)}`
    }).join(' ')
  })

  const radarLabels = computed(() => {
    const s = result.value?.wuxing_score
    const vals = s ? [s.wood, s.fire, s.earth, s.metal, s.water] : [0,0,0,0,0]
    return RADAR_ANGLES.map((angle, i) => {
      const lr = RADAR_R + 18
      return {
        el:    RADAR_ELEMENTS[i],
        val:   vals[i],
        color: wxColor(RADAR_ELEMENTS[i]),
        x:     +(RADAR_CX + lr * Math.cos(angle)).toFixed(1),
        y:     +(RADAR_CY + lr * Math.sin(angle)).toFixed(1),
      }
    })
  })

  // ── 文字解读 ──────────────────────────────────────────────────────────────
  const dayMasterDesc = computed((): string => {
    const r = result.value
    if (!r?.day_master_strength) return ''
    const tier    = r.day_master_strength.tier ?? ''
    const score   = r.day_master_strength.score ?? 0
    const dayStem = (r.pillars_primary as any)?.day?.stem ?? ''
    const el      = STEM_ELEMENT[dayStem] ?? ''
    const tierZh  = TIER_ZH[tier] ?? tier
    const ADV: Record<string, string> = {
      '偏旺': `日元${el}气偏旺（评分 ${score.toFixed(1)}），宜以克泄耗之神调顺气机，接触克制${el}或消耗${el}的五行，避免同类继续助旺。`,
      '极旺': `日元${el}气极旺（评分 ${score.toFixed(1)}），须强力克泄化解，否则性格易固执，难以变通，宜积极疏泄。`,
      '偏弱': `日元${el}气偏弱（评分 ${score.toFixed(1)}），须借生助之神扶持，勿轻易耗损，保护日主元气为先。`,
      '极弱': `日元${el}气极弱（评分 ${score.toFixed(1)}），以生扶为主，切忌克耗，命局宜顺势、借力打力。`,
      '中等': `日元${el}气中和（评分 ${score.toFixed(1)}），命局较为平衡，取用灵活，运势起伏不大，贵在稳健。`,
      '均衡': `日元${el}气平和（评分 ${score.toFixed(1)}），阴阳调顺，适合多方向发展，稳中求进。`,
    }
    return ADV[tierZh] || (el ? `日主属${el}行（${tierZh || tier}），评分 ${score.toFixed(1)}，影响用神与忌神的取舍方向。` : '')
  })

  const baziSummaryFallback = computed((): string => {
    const r = result.value
    if (!r) return ''
    if (r.bazi_summary) return r.bazi_summary
    const dayStem   = (r.pillars_primary as any)?.day?.stem ?? ''
    const el        = STEM_ELEMENT[dayStem] ?? ''
    const score     = r.day_master_strength?.score ?? 0
    const tierZh    = TIER_ZH[r.day_master_strength?.tier ?? ''] ?? (r.day_master_strength?.tier ?? '')
    const gejuName  = r.geju?.geju_name  ?? ''
    const gejuLevel = r.geju?.geju_level ?? ''
    const favor     = (r.yongshen?.favor ?? []).map(wxZh).join('、') || '—'
    const avoid     = (r.yongshen?.avoid ?? []).map(wxZh).join('、') || '—'
    const weak      = (r.wuxing_weak   ?? []).join('、')
    const strong    = (r.wuxing_strong ?? []).join('、')
    let text = ''
    if (el)       text += `此命日主为${dayStem}（${el}行），日元${tierZh}，命局评分 ${score.toFixed(1)}。`
    if (gejuName) text += `格局为「${gejuName}」${gejuLevel ? `（${gejuLevel}）` : ''}，决定命主的性格底色与人生主要应对方式。`
    if (favor !== '—') text += `用神为${favor}，忌神为${avoid}；日常宜接触用神五行对应的方位、颜色与行业，并适度规避忌神方向的投入与决策。`
    if (weak)  text += `五行中${weak}偏缺，宜适当补充相应能量。`
    if (strong) text += `${strong}偏旺，须注意疏泄平衡，防物极必反。`
    return text
  })

  const currentDayunDesc = computed((): string => {
    if (dayunActiveIdx.value < 0) return ''
    const item = dayunItems.value[dayunActiveIdx.value]
    if (!item) return ''
    if (item.narrative) return item.narrative
    const gz       = (item.stem ?? '') + (item.branch ?? '')
    const tg       = item.ten_god ?? ''
    const ageRange = `${item.start_age ?? '?'}–${(item.start_age ?? 0) + 9}岁`
    const tgDesc   = TG_ADV[tg] ? `「${tg}」主导：${TG_ADV[tg]}` : (tg ? `当前天干十神为${tg}。` : '')
    return `行 ${gz} 大运（${ageRange}）。${tgDesc}`.trim()
  })

  // ── 命盘导读 ──────────────────────────────────────────────────────────────
  const overviewGuideCards = computed(() => {
    const hasSummary = !!result.value?.bazi_summary
    const hasFortune = !!result.value?.current_fortune_summary
    const favor      = result.value?.yongshen?.favor?.join('、') || '待计算'
    const gejuName   = result.value?.geju?.geju_name || '待计算'
    return [
      {
        label: '先看哪里',
        value: hasSummary
          ? '先读命局综合总评，再看用神、格局与当前运势。'
          : '先看用神、日元强弱与格局三张卡，先抓主线。',
      },
      {
        label: '当前主线',
        value: `用神倾向：${favor} ｜ 格局：${gejuName}`,
      },
      {
        label: '下一步',
        value: hasFortune
          ? '继续切到"大运"或"运势预测"，把静态命盘放进时间线里理解。'
          : '继续切到"大运"，确认阶段变化与年份重点。',
      },
    ]
  })

  const overviewReadingSteps = computed(() => [
    '先看综合总评，确认这张盘的核心结论，不必一开始就逐条解术语。',
    '再看用神、日元强弱和格局，理解结论背后的命局结构。',
    '最后进入大运或运势页，把命盘解释转换成阶段判断和行动建议。',
  ])

  const overviewTerms = computed(() => {
    const terms = [
      '日主',
      '用神',
      '格局',
      '大运',
      result.value?.geju?.geju_name,
      ...(result.value?.yongshen?.favor ?? []).slice(0, 2),
    ]
      .filter((item): item is string => !!item)
      .slice(0, 6)
    return [...new Set(terms)]
  })

  const rawResultJson = computed(() => {
    if (!result.value) return ''
    return JSON.stringify(result.value, null, 2)
  })

  return {
    currentYear,
    dayunSelected,
    dayunItems,
    dayunActiveIdx,
    pillars,
    wuxingBars,
    RADAR_ANGLES,
    RADAR_CX,
    RADAR_CY,
    RADAR_R,
    radarBg,
    radarBgHalf,
    radarPoints,
    radarLabels,
    tgColor,
    wxColor,
    wxZh,
    scoreColor,
    dayMasterDesc,
    baziSummaryFallback,
    currentDayunDesc,
    overviewGuideCards,
    overviewReadingSteps,
    overviewTerms,
    rawResultJson,
  }
}
