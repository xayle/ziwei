import type { BaziResponse } from '@/api/bazi'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import type { ExplainBatchResponse } from '@/api/explain'
import {
  LIFE_VOLUME_LABELS,
  type AnalysisBlock,
  type ContentLayer,
  type LifeVolume,
  type LifeVolumeId,
  type LifeVolumeResponse,
  type VolumeSection,
} from '@/types/life-volume'
import { buildBaziModuleCards } from '@/utils/buildBaziModuleCards'
import { buildPatternAnalysisBlocks } from '@/utils/buildZiweiInsightBlocks'
import { DAYMASTER_CLASSIC_REFS } from '@/constants/daymasterClassicRefs'
import { DAYUN_CLASSIC_REFS } from '@/constants/dayunClassicRefs'
import { HEALTH_CLASSIC_REFS } from '@/constants/healthClassicRefs'
import { LIUNIAN_CLASSIC_REFS } from '@/constants/liunianClassicRefs'
import { MARRIAGE_CLASSIC_REFS } from '@/constants/marriageClassicRefs'
import { SHISHEN_CLASSIC_REFS } from '@/constants/shishenClassicRefs'
import { WUXING_CLASSIC_REFS } from '@/constants/wuxingClassicRefs'
import { YONGSHEN_CLASSIC_REFS } from '@/constants/yongshenClassicRefs'
import { buildColophonSummary, defaultDisclaimerBlock } from '@/utils/buildColophonSummary'
import { truncateText } from '@/utils/truncateText'
import {
  formatRelationsFactText,
  formatRelationsImpactText,
  formatShenshaPolarityTexts,
  buildShenshaClassicQuoteBlocks,
  buildRelationsClassicQuoteBlocks,
  pickRelationsVerifiedCites,
  enrichVol2BlockText,
  enrichVolumeBlockText,
} from '@/utils/formatVol2Summary'
import { LLM_MODULES } from '@/api/llm'
import { PREFACE_READING_GUIDE_BLOCKS } from '@/utils/extractReadingGuideParagraphs'
import {
  buildDayunVolumeText,
  formatDayunAgeRange,
} from '@/utils/dayunDisplay'
import { DEMO_LOCKED_VOLUME_IDS, demoVolumeLocksEnabled } from '@/constants/volumePaywall'
import { formatWxList } from '@/utils/buildEngineTrustDisplay'

export interface BuildLifeVolumesInput {
  caseId: string
  chartHash: string
  bazi: BaziResponse | null
  ziwei: ZiweiResponse | null
  profileLabel?: string
  explain?: ExplainBatchResponse | null
  trustLevel?: 'full' | 'degraded'
  missingFields?: string[]
  iztroAdvisory?: string
  wenmoAdvisory?: string
  engineLabel?: string
  generatedAt?: string
}

const VOLUME_ORDER: LifeVolumeId[] = [
  'preface', 'vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6', 'colophon',
]

/**
 * @deprecated T081 — W16+ 生产权威为 `GET /api/v1/life/volumes`（`fetchLifeVolumes`）。
 * 仅保留：无 remote 时的本地回退、Vitest fixture、联调对比。
 * Report 在 remote 已成功时不得再调用本函数（见 `ReportView` / `shouldBuildLifeVolumesAdapter`）。
 */
export function buildLifeVolumes(input: BuildLifeVolumesInput): LifeVolumeResponse {
  const volumes = VOLUME_ORDER.map((id) => buildVolume(id, input))
  return {
    schema_version: 'life-volume@1.0',
    case_id: input.caseId,
    chart_hash: input.chartHash,
    rule_version: input.bazi?.rule_version ?? input.ziwei?.rule_version,
    content_versions: input.explain?.content_versions ?? {},
    disclaimer_block: input.explain?.disclaimer_block
      ? {
          text: input.explain.disclaimer_block.text,
          version: input.explain.disclaimer_block.version,
          jurisdiction: input.explain.disclaimer_block.jurisdiction,
        }
      : defaultDisclaimerBlock(),
    trust_level: input.trustLevel ?? 'full',
    volumes,
    colophon: buildColophonSummary({
      missingFields: input.missingFields,
      iztroAdvisory: input.iztroAdvisory,
      wenmoAdvisory: input.wenmoAdvisory ?? input.explain?.wenmo_advisory,
      engineLabel: input.engineLabel,
      generatedAt: input.generatedAt,
    }),
  }
}

function buildVolume(id: LifeVolumeId, input: BuildLifeVolumesInput): LifeVolume {
  const builders: Record<LifeVolumeId, () => VolumeSection[]> = {
    preface: () => buildPrefaceSections(input),
    vol1: () => buildVol1Sections(input),
    vol2: () => buildVol2Sections(input),
    vol3: () => buildVol3Sections(input),
    vol4: () => buildVol4Sections(input),
    vol5: () => buildVol5Sections(input),
    vol6: () => buildVol6Sections(input),
    colophon: () => buildColophonVolumeSections(input),
  }
  return {
    id,
    title: LIFE_VOLUME_LABELS[id],
    // ENT-demo：演示锁卷时 Adapter 写出 locked，供 Report 付费墙识别
    locked: demoVolumeLocksEnabled() && (DEMO_LOCKED_VOLUME_IDS as LifeVolumeId[]).includes(id),
    sections: builders[id](),
  }
}

function block(text: string, layer: ContentLayer, extra: Partial<AnalysisBlock> = {}): AnalysisBlock {
  return { text: truncateText(text, 500), layer, ...extra }
}

function section(
  id: string,
  heading: string,
  layer: ContentLayer,
  blocks: AnalysisBlock[],
  collapsed_default = false,
): VolumeSection {
  return { id, heading, layer, blocks, collapsed_default }
}

function buildPrefaceSections(input: BuildLifeVolumesInput): VolumeSection[] {
  // 与 BE preface 同源：reading-guide 始终写入，供 volumes 回退与 ReadingGuide 抽取。
  // explain 的 reading 仍优先（resolveReadingGuideParagraphs），不挡动态读法。
  const sections: VolumeSection[] = [
    section('reading-guide', '读法导览', 'fact', PREFACE_READING_GUIDE_BLOCKS.map((text) => block(text, 'fact'))),
  ]
  const explainReading = input.explain?.sections.find((s) => s.section_id === 'reading')
  if (explainReading?.blocks.length) {
    sections.push(section('bazi-reading', '八字读法', 'cite', explainReading.blocks.map((b) => ({
      text: truncateText(b.text),
      layer: b.layer,
      classic_id: b.classic_id,
    }))))
  }
  if (input.profileLabel) {
    sections.unshift(section('archive-label', '辑录对象', 'fact', [
      block(input.profileLabel, 'fact'),
    ]))
  }
  return sections
}

function formatPillarLine(
  label: string,
  p?: { stem?: string | null; branch?: string | null; ganzhi?: string | null } | null,
): string {
  if (!p) return `${label} —`
  const gz = (p.ganzhi?.trim() || `${p.stem ?? ''}${p.branch ?? ''}`.trim()) || '—'
  return `${label} ${gz}`
}

function buildVol1Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const b = input.bazi
  if (!b) {
    return [section('vol1-empty', '命盘根气', 'fact', [block('八字数据待载入。', 'fact')])]
  }
  const day = b.pillars_primary?.day
  const geju = b.geju
  const pillars = b.pillars_primary
  const sections: VolumeSection[] = [
    section('pillars', '四柱根气', 'fact', [
      block(
        enrichVolumeBlockText(
          '卷一四柱根气',
          [
            formatPillarLine('年柱', pillars?.year),
            formatPillarLine('月柱', pillars?.month),
            formatPillarLine('日柱', pillars?.day),
            formatPillarLine('时柱', pillars?.hour),
            `日主 ${day?.stem ?? '—'}${day?.branch ?? '—'}；格局 ${geju?.geju_name ?? '待分析'}`,
          ].join('。'),
        ),
        'fact',
      ),
    ]),
  ]
  const gejuBits = [geju?.geju_detail, geju?.interpretation_text]
    .map((s) => (s || '').trim())
    .filter(Boolean)
  const gejuUnique = [...new Set(gejuBits)]
  if (gejuUnique.length || geju?.geju_name) {
    const parts = [
      geju?.geju_name ? `格局取「${geju.geju_name}」` : '',
      ...gejuUnique,
    ].filter(Boolean)
    let body = parts.join('。')
    if (geju?.geju_level) body = `${body}（等级 ${geju.geju_level}）`
    sections.push(section('geju', '格局', 'fact', [
      block(enrichVolumeBlockText('卷一格局', body), 'fact'),
    ]))
  }
  // E-01：软模板不得以 cite/典籍依据入库；走 inference
  const classic = geju?.classic_ref?.trim()
  if (classic) {
    sections.push(
      section('geju-heuristic', '格局启发式', 'inference', [block(classic, 'inference')]),
    )
  }
  const y = b.yongshen
  if (y?.favor?.length || y?.avoid?.length) {
    const yongBody = (
      `喜用 ${formatWxList(y.favor)}；忌 ${formatWxList(y.avoid)}。` +
      '用神须与格局、日主强弱同参：得令得助则宜顺用神拓展，失令受克则先避忌神、再谈进取。'
    )
    sections.push(section('yongshen', '用神', 'fact', [
      block(enrichVolumeBlockText('卷一用神', yongBody), 'fact'),
    ]))
    const yongCite = YONGSHEN_CLASSIC_REFS.slice(0, 2).map((ref) =>
      block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
    )
    if (yongCite.length) {
      sections.push(section('yongshen-cite', '典籍句式', 'cite', yongCite))
    }
  }
  const strength = b.day_master_strength
  if (strength && (strength.tier || strength.score != null)) {
    const factors = (strength.factors ?? strength.strength_factors ?? [])
      .slice(0, 4)
      .map((f) => {
        const name = f.name?.trim()
        const reason = f.reason?.trim()
        if (name && reason) return `${name}（${reason}）`
        return name || ''
      })
      .filter(Boolean)
    let strengthText = `日主强弱：${strength.tier || '—'}（评分 ${strength.score ?? '—'}）`
    if (factors.length) strengthText = `${strengthText}。主要因子：${factors.join('；')}`
    sections.push(section('strength', '日主强弱', 'fact', [
      block(enrichVolumeBlockText('卷一强弱', strengthText), 'fact'),
    ]))
    sections.push(section(
      'daymaster-cite',
      '典籍句式',
      'cite',
      DAYMASTER_CLASSIC_REFS.slice(0, 2).map((ref) =>
        block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
      ),
    ))
  }
  sections.push(section(
    'wuxing-cite',
    '五行典籍句式',
    'cite',
    WUXING_CLASSIC_REFS.slice(0, 2).map((ref) =>
      block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
    ),
  ))
  sections.push(section(
    'shishen-cite',
    '十神典籍句式',
    'cite',
    SHISHEN_CLASSIC_REFS.slice(0, 2).map((ref) =>
      block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
    ),
  ))
  const fortune = b.current_fortune_summary
  if (fortune) {
    // 控 vol1 trunc：域摘要节选，把篇幅留给格局/用神完整句
    const domainBits = Object.entries(fortune.this_year_domains ?? {})
      .slice(0, 2)
      .map(([k, v]) => `${k}：${truncateText(String(v), 72)}`)
    const bits = [
      fortune.current_dayun ? `当前大运 ${fortune.current_dayun}` : '',
      fortune.current_liunian ? `流年 ${fortune.current_liunian}` : '',
      fortune.dayun_years_remaining != null ? `大运余 ${fortune.dayun_years_remaining} 年` : '',
      ...domainBits,
      (fortune.top3_actions ?? []).length
        ? `宜行： ${(fortune.top3_actions ?? []).slice(0, 2).map((a) => truncateText(String(a), 72)).join('；')}`
        : '',
    ].filter(Boolean)
    if (bits.length) {
      sections.push(section('current-fortune', '当下运势摘要', 'fact', [
        block(truncateText(bits.join(' · '), 360), 'fact'),
      ]))
    }
  }
  if (b.bazi_summary?.trim()) {
    sections.push(section('summary-inference', '综合总评', 'inference', [
      block(truncateText(b.bazi_summary, 360), 'inference'),
    ], true))
  }
  const explainGeju = input.explain?.sections.find((s) => s.section_id === 'geju')
  if (explainGeju?.blocks.length) {
    sections.push(section('geju-explain', '格局讲解', 'cite', explainGeju.blocks.map((blk) => ({
      text: truncateText(blk.text, 500),
      layer: blk.layer,
      classic_id: blk.classic_id,
    }))))
  }
  return sections
}

function buildVol2Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const b = input.bazi
  const relationText = formatRelationsFactText(b)
  const impactText = formatRelationsImpactText(b)
  const { auspicious, caution } = formatShenshaPolarityTexts(b)
  const sections: VolumeSection[] = [
    section('relations', '干支关系', 'fact', [block(enrichVol2BlockText('干支关系', relationText), 'fact')]),
    section('relations-reading', '关系读法', 'inference', [block(impactText, 'inference')]),
    section('shensha-auspicious', '吉神', 'fact', [block(enrichVol2BlockText('吉神', auspicious), 'fact')]),
    section('shensha-caution', '慎神', 'fact', [block(enrichVol2BlockText('慎神', caution), 'fact')]),
  ]
  const explainRelations = input.explain?.sections.find((s) => s.section_id === 'relations')
  const explainBlocks = explainRelations?.blocks ?? []
  // 仅 layer=cite 进典籍句式；带 classic_id 的 soft 不得冒充 cite（E-01）
  const citeFromExplain = explainBlocks.filter((blk) => blk.layer === 'cite')
  const explainSoft = explainBlocks.filter((blk) => blk.layer === 'inference')
  const explainFact = explainBlocks.filter((blk) => blk.layer !== 'cite' && blk.layer !== 'inference')
  if (explainFact.length) {
    sections.push(section('relations-explain', '关系讲解', 'fact', explainFact.map((blk) => ({
      text: truncateText(blk.text, 500),
      layer: blk.layer,
      classic_id: blk.classic_id,
    }))))
  }
  if (citeFromExplain.length) {
    sections.push(section('relations-cite', '典籍句式', 'cite', citeFromExplain.slice(0, 3).map((blk) => ({
      text: truncateText(blk.text, 500),
      layer: 'cite' as ContentLayer,
      classic_id: blk.classic_id,
    }))))
  } else {
    const verified = pickRelationsVerifiedCites(b, 2)
    if (verified.length) {
      sections.push(section('relations-cite', '典籍句式', 'cite', verified.map((q) => ({
        text: q.text,
        layer: 'cite' as ContentLayer,
        classic_id: q.classic_id,
      }))))
    }
  }
  const relSoft = explainSoft.length
    ? explainSoft.slice(0, 3).map((blk) => ({
        text: truncateText(blk.text, 500),
        layer: 'inference' as ContentLayer,
        classic_id: blk.classic_id,
      }))
    : buildRelationsClassicQuoteBlocks(b).map((q) => ({
        text: q.text,
        layer: 'inference' as ContentLayer,
        classic_id: q.classic_id,
      }))
  if (relSoft.length) {
    sections.push(section('relations-classic-soft', '关系典籍软提示', 'inference', relSoft))
  }
  const quotes = buildShenshaClassicQuoteBlocks(b)
  if (quotes.length) {
    const citeQ = quotes.filter((q) => q.layer === 'cite')
    const softQ = quotes.filter((q) => q.layer !== 'cite')
    if (citeQ.length) {
      sections.push(section('shensha-cite', '典籍句式', 'cite', citeQ.map((q) => ({
        text: q.text,
        layer: 'cite' as ContentLayer,
        classic_id: q.classic_id,
      }))))
    }
    if (softQ.length) {
      sections.push(section('shensha-classic-soft', '神煞典籍软提示', 'inference', softQ.map((q) => ({
        text: q.text,
        layer: 'inference' as ContentLayer,
        classic_id: q.classic_id,
      }))))
    }
  }
  if (!citeFromExplain.length && !quotes.length && !relSoft.length) {
    const hasRelationsCite = sections.some((s) => s.id === 'relations-cite')
    if (!hasRelationsCite) {
      sections.push(section('vol2-cite-pending', '典籍句式', 'cite', [
        block(
          '卷二典籍句式待校勘：关系与神煞的古籍正文尚未挂载。阅读时以排盘事实、关系读法与吉神/慎神分列为准，把神煞当旁证；典籍句式补齐后再对照引用。在此之前，不作断语，也不用口语替代典籍。校勘进度见卷末跋；若 explain 已挂 cite，本注会被典籍句式节替换。',
          'cite',
        ),
      ]))
    }
  }
  return sections
}

function buildVol3Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const b = input.bazi
  const z = input.ziwei
  const sections: VolumeSection[] = []
  const dayunItems = b?.dayun?.items ?? b?.dayun?.cycles ?? []
  if (dayunItems.length) {
    sections.push(section(
      'dayun',
      '大运序列',
      'fact',
      dayunItems.slice(0, 8).map((item, idx) => block(
        buildDayunVolumeText(item, idx, dayunItems),
        item.narrative?.trim() ? 'inference' : 'fact',
      )),
    ))
    sections.push(section(
      'dayun-cite',
      '典籍句式',
      'cite',
      DAYUN_CLASSIC_REFS.slice(0, 2).map((ref) =>
        block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
      ),
    ))
  }
  const ziweiDayun = z?.dayun?.items ?? []
  if (ziweiDayun.length) {
    sections.push(section('ziwei-dayun', '紫微大运', 'fact', ziweiDayun.slice(0, 8).map((item, idx) => {
      const palace = 'palace_name' in item ? String((item as { palace_name?: string }).palace_name ?? '').trim() : ''
      const sihua = Object.entries(item.sihua ?? {})
        .map(([star, trans]) => `${star}${trans}`)
        .join('、')
      const line = [
        `${idx + 1}. ${item.ganzhi}`,
        formatDayunAgeRange(item.start_age, item.end_age),
        item.start_year ? `${item.start_year}–${item.start_year + Math.max(0, item.end_age - item.start_age)}年` : '',
        palace ? `应宫 ${palace}` : '',
        sihua ? `四化 ${sihua}` : '',
      ].filter(Boolean).join(' · ')
      return block(enrichVolumeBlockText('紫微大运节选', line), 'fact')
    })))
  }
  // BZ-Month：八字月运进卷三（勿放进卷五域分析）
  const monthly = b?.monthly_fortune ?? []
  if (monthly.length) {
    sections.push(section(
      'monthly-fortune',
      '月运（当年）',
      'fact',
      monthly.slice(0, 12).map((m) => {
        const gz = m.month_ganzhi?.trim() || `${m.month_dizhi || ''}`.trim()
        const clash = m.clash_with?.trim() ? ` · 冲 ${m.clash_with}` : ''
        return block(
          `${m.month}月${gz ? ` · ${gz}` : ''} · ${m.luck_level} · ${truncateText(m.tip || '—', 80)}${clash}`,
          'fact',
        )
      }),
    ))
  }
  // CNT-03：流年节选进卷三，减轻「仅大运骨架」空感
  const liunianItems = b?.liunian?.items ?? []
  if (liunianItems.length) {
    const year = new Date().getFullYear()
    const nearby = liunianItems
      .filter((it) => typeof it.year === 'number' && Math.abs(it.year - year) <= 2)
      .slice(0, 5)
    const pick = nearby.length ? nearby : liunianItems.slice(0, 5)
    sections.push(section(
      'liunian',
      '流年节选',
      'fact',
      pick.map((it) => {
        const gz = `${it.stem ?? ''}${it.branch ?? ''}`.trim()
        const extra = [
          it.ten_god,
          it.xingyun ? `星运 ${it.xingyun}` : '',
          it.nayin ? `纳音 ${it.nayin}` : '',
          it.clash ? `冲 ${it.clash}` : '',
        ].filter(Boolean).join(' · ')
        return block(
          enrichVolumeBlockText(
            '流年节选',
            `${it.year ?? '—'} · ${gz || '—'}${extra ? ` · ${extra}` : ''}`,
          ),
          'fact',
        )
      }),
    ))
    sections.push(section(
      'liunian-cite',
      '典籍句式',
      'cite',
      LIUNIAN_CLASSIC_REFS.slice(0, 2).map((ref) =>
        block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
      ),
    ))
  }
  if (!sections.length) {
    sections.push(section('vol3-empty', '运波', 'fact', [block('运限数据待载入。', 'fact')]))
  }
  return sections
}

function findPalaceByExplainText(text: string, palaces: PalaceResponse[]): PalaceResponse | undefined {
  const trimmed = text.trim()
  return palaces.find((p) => trimmed.includes(p.name))
}

function buildPalaceSupplement(p: PalaceResponse): string {
  const parts: string[] = []
  const aux = p.aux_stars?.slice(0, 4).map((s) => s.name).join('、')
  if (aux) parts.push(`辅煞 ${aux}`)
  const tags = p.analysis_tags?.slice(0, 3).join('、')
  if (tags) parts.push(`要点 ${tags}`)
  if (p.is_body_palace) parts.push('身宫所在')
  if (p.is_empty_palace) parts.push('空宫借星')
  if (p.borrowed_main_stars?.length) {
    parts.push(`借星 ${p.borrowed_main_stars.map((s) => s.name).join('、')}`)
  }
  return parts.join('；')
}

function buildPalaceVolumeText(p: PalaceResponse): string {
  const stars = p.main_stars?.map((s) => s.name).join('、') || '无主星'
  const head = `${p.name} ${p.stem ?? ''}${p.branch ?? ''}：主星 ${stars}`
  const narrative = (p.conclusion || p.analysis || p.explanation || p.suggestion || '').trim()
  const supplement = buildPalaceSupplement(p)
  if (narrative.length >= 40) {
    return `${head}。${truncateText(narrative, 220)}`
  }
  const parts = [head]
  if (supplement) parts.push(supplement)
  if (narrative) parts.push(narrative)
  return parts.join('；')
}

function enrichPalaceExplainText(explainText: string, palace?: PalaceResponse): string {
  const base = explainText.trim()
  if (!palace) return base || '宫位待补'
  if (base.length >= 40) return base
  const enriched = buildPalaceVolumeText(palace)
  if (!base) return enriched
  if (base.length >= 20) return `${base}。${buildPalaceSupplement(palace)}`
  return enriched
}

function buildVol4Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const z = input.ziwei
  if (!z) {
    return [section('vol4-empty', '宫图', 'fact', [block('紫微数据待载入。', 'fact')])]
  }
  const sections: VolumeSection[] = [
    section('ziwei-meta', '命盘概要', 'fact', [
      block(
        `卷四命盘概要：五行局 ${z.wuxing_ju_name ?? '—'}；命宫 ${z.life_palace_gz ?? '—'}；身宫 ${z.body_palace_gz ?? '—'}。`
        + '以下宫图与格局均围绕命身轴展开，勿先扫十二宫再回头找主轴。',
        'fact',
      ),
    ]),
    section('ziwei-reading', '宫图读法', 'inference', [
      block(
        '先看命身轴：命宫看主星气质与一生底色，身宫看行运着力与身心投注处；两宫同参，才谈得上格局高低。'
        + '再看三方四正（命、财帛、官禄与对宫），把握事业、财帛与压力来源，比逐宫平铺更易抓住主线。'
        + '然后才扫各宫主星、辅星与四化；格局条文用来印证命身轴，不代替「先轴后方」的阅读顺序。',
        'inference',
      ),
    ]),
  ]
  const patterns = buildPatternAnalysisBlocks(z.patterns, 4)
  if (patterns.length) {
    sections.push(section('patterns', '格局', 'fact', patterns.map((p) => block(
      enrichVolumeBlockText('紫微格局', `${p.title}：${p.body}`),
      'fact',
    ))))
  }
  const explainPalaces = input.explain?.sections.find((s) => s.section_id === 'palaces')
  const palaces = z.palaces ?? []
  if (explainPalaces?.blocks.length) {
    sections.push(section('palaces-explain', '宫图与星曜要点', 'fact', explainPalaces.blocks.map((b, idx) => {
      const matched = findPalaceByExplainText(b.text, palaces) ?? palaces[idx]
      return {
        text: truncateText(enrichPalaceExplainText(b.text, matched), 500),
        layer: b.layer as ContentLayer,
      }
    })))
  } else if (palaces.length) {
    sections.push(section('palaces', '十二宫（节选）', 'fact', palaces.slice(0, 8).map((p) => block(buildPalaceVolumeText(p), 'fact'))))
  }
  return sections
}

function buildVol5Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const citeTail: VolumeSection[] = [
    section(
      'marriage-cite',
      '婚恋典籍句式',
      'cite',
      MARRIAGE_CLASSIC_REFS.slice(0, 2).map((ref) =>
        block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
      ),
      true,
    ),
    section(
      'health-cite',
      '健康典籍句式',
      'cite',
      HEALTH_CLASSIC_REFS.slice(0, 2).map((ref) =>
        block(`典籍依据（${ref.source}）：${ref.text}`, 'cite', { classic_id: ref.id }),
      ),
      true,
    ),
  ]
  const explainDomains = input.explain?.sections.find((s) => s.section_id === 'domains')
  if (explainDomains?.blocks.length) {
    return [
      section('domains-explain', '生活域推断', 'inference', explainDomains.blocks.map((b) => ({
        text: truncateText(b.text),
        layer: b.layer,
        classic_id: b.classic_id,
      })), true),
      ...citeTail,
    ]
  }
  const cards = buildBaziModuleCards(input.bazi).filter((c) => c.title !== '开运' && c.title !== '月运')
  if (!cards.length) {
    return [
      section('vol5-empty', '事理', 'inference', [block('域分析待载入。', 'inference')], true),
      ...citeTail,
    ]
  }
  return [
    ...cards.map((card, idx) => section(
      `domain-${idx}`,
      card.title,
      'inference',
      [block(`${card.lead}。${truncateText(card.body, 80)}`, 'inference', { score: undefined })],
      true,
    )),
    ...citeTail,
  ]
}

function buildVol6Sections(_input: BuildLifeVolumesInput): VolumeSection[] {
  const modules = LLM_MODULES.map((m) => m.label).join('、')
  return [
    section('vol6-on-demand', '问书助手', 'inference', [
      block(
        '卷六为问书助手：需主动展开后选择模块提问。打磨期不自动调用问书，避免首屏静默消耗额度或打断阅读节奏；展开后即可把排盘事实、卷二神煞读法与卷三运限对照追问，把「怎么问」当作阅读延伸，而非另开玄学聊天。提问前请先确认已读卷一与卷三要点。',
        'fact',
      ),
    ], true),
    section('vol6-how-to-ask', '怎么问', 'inference', [
      block(
        '示例一（事业）：结合卷一格局与当前大运，今年事业宜进取还是守成？若要换赛道或谈晋升，有哪些方向更贴用神、哪些宜暂缓？请用可执行建议回答，并标明依据来自格局还是运限。',
        'inference',
      ),
      block(
        '示例二（婚恋）：对照卷二神煞与配偶宫线索，近两年感情节奏如何把握？沟通、承诺与边界上各要注意什么？请避免把刑冲直接当成情绪标签，改成可观察的相处节奏。',
        'inference',
      ),
      block(
        '示例三（流年）：根据卷三流年节选，明年关键节点在哪几个月？宜推动什么、宜暂缓什么，如何与当前大运叙事对齐？若只能抓两三个月份，请按优先级说明。',
        'inference',
      ),
    ], true),
    section('vol6-bridge', '与前卷衔接', 'inference', [
      block(
        '建议先读完卷一格局与用神、卷二关系/神煞读法、卷三当前大运与流年节选，再打开问书；带着具体年份、生活域或一件待决之事提问，回答更贴盘，也更少空泛套话。若前卷尚未读完，可先记下问题，读完再展开本卷。',
        'inference',
      ),
    ], true),
    section('vol6-access', '使用说明', 'fact', [
      block(
        `未登录时可先完成排盘与前五卷阅读，建立事实底稿；登录后展开本卷，可选择：${modules}。各模块需主动发起，不会在首屏自动请求；未登录时也可先浏览示例问法，登录后再正式提问。`,
        'fact',
      ),
    ], true),
  ]
}

function buildColophonVolumeSections(input: BuildLifeVolumesInput): VolumeSection[] {
  const col = buildColophonSummary({
    missingFields: input.missingFields,
    iztroAdvisory: input.iztroAdvisory,
    wenmoAdvisory: input.wenmoAdvisory ?? input.explain?.wenmo_advisory,
    engineLabel: input.engineLabel,
    generatedAt: input.generatedAt,
  })
  return [
    section('colophon-summary', '校勘摘要', 'fact', col.summary_lines.map((line) => block(line, 'fact'))),
  ]
}
