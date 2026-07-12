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
import { buildColophonSummary, defaultDisclaimerBlock } from '@/utils/buildColophonSummary'
import { truncateText } from '@/utils/truncateText'
import { formatRelationsSummaryText, formatShenshaSummaryText } from '@/utils/formatVol2Summary'
import {
  buildDayunVolumeText,
  formatDayunAgeRange,
} from '@/utils/dayunDisplay'

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
    locked: false,
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
  const sections: VolumeSection[] = [
    section('reading-guide', '读法导览', 'fact', [
      block('卷一至卷五按 fact（排盘推算）· cite（典籍依据）· inference（经验推断）分层阅读；卷六为问书助手，需主动展开。', 'fact'),
    ]),
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

function buildVol1Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const b = input.bazi
  if (!b) {
    return [section('vol1-empty', '命盘根气', 'fact', [block('八字数据待载入。', 'fact')])]
  }
  const day = b.pillars_primary?.day
  const geju = b.geju
  const sections: VolumeSection[] = [
    section('pillars', '四柱根气', 'fact', [
      block(`日主 ${day?.stem ?? '—'}${day?.branch ?? '—'}；格局 ${geju?.geju_name ?? '待分析'}。`, 'fact'),
    ]),
  ]
  if (geju?.geju_detail || geju?.interpretation_text) {
    sections.push(section('geju', '格局', 'fact', [
      block(geju.geju_detail || geju.interpretation_text || '', 'fact'),
    ]))
  }
  const classic = geju?.classic_ref?.trim()
  if (classic) {
    sections.push(section('geju-cite', '典籍句式', 'cite', [block(classic, 'cite')]))
  }
  const y = b.yongshen
  if (y?.favor?.length || y?.avoid?.length) {
    sections.push(section('yongshen', '用神', 'fact', [
      block(`喜用 ${(y.favor ?? []).join('、') || '—'}；忌 ${(y.avoid ?? []).join('、') || '—'}`, 'fact'),
    ]))
  }
  if (b.bazi_summary?.trim()) {
    sections.push(section('summary-inference', '综合总评', 'inference', [
      block(b.bazi_summary, 'inference'),
    ], true))
  }
  const explainGeju = input.explain?.sections.find((s) => s.section_id === 'geju')
  if (explainGeju?.blocks.length) {
    sections.push(section('geju-explain', '格局讲解', 'cite', explainGeju.blocks.map((b) => ({
      text: truncateText(b.text),
      layer: b.layer,
      classic_id: b.classic_id,
    }))))
  }
  return sections
}

function buildVol2Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const b = input.bazi
  const relationText = formatRelationsSummaryText(b)
  const shenshaText = formatShenshaSummaryText(b)
  const sections: VolumeSection[] = [
    section('relations', '干支关系', 'fact', [block(relationText, 'fact')]),
    section('shensha', '神煞摘要', 'fact', [block(shenshaText, 'fact')]),
  ]
  const explainRelations = input.explain?.sections.find((s) => s.section_id === 'relations')
  if (explainRelations?.blocks.length) {
    sections.push(section('relations-explain', '关系讲解', 'fact', explainRelations.blocks.map((b) => ({
      text: truncateText(b.text),
      layer: b.layer,
      classic_id: b.classic_id,
    }))))
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
        palace ? `应 ${palace}` : '',
        sihua ? `四化 ${sihua}` : '',
      ].filter(Boolean).join(' · ')
      return block(line, 'fact')
    })))
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
      block(`五行局 ${z.wuxing_ju_name ?? '—'}；命宫 ${z.life_palace_gz ?? '—'}；身宫 ${z.body_palace_gz ?? '—'}`, 'fact'),
    ]),
  ]
  const patterns = buildPatternAnalysisBlocks(z.patterns, 4)
  if (patterns.length) {
    sections.push(section('patterns', '格局', 'fact', patterns.map((p) => block(`${p.title}：${p.body}`, 'fact'))))
  }
  const explainPalaces = input.explain?.sections.find((s) => s.section_id === 'palaces')
  const palaces = z.palaces ?? []
  if (explainPalaces?.blocks.length) {
    sections.push(section('palaces-explain', '宫图与星曜要点', 'fact', explainPalaces.blocks.map((b, idx) => {
      const matched = findPalaceByExplainText(b.text, palaces) ?? palaces[idx]
      return {
        text: truncateText(enrichPalaceExplainText(b.text, matched), 500),
        layer: (b.layer === 'cite' ? 'inference' : b.layer) as ContentLayer,
      }
    })))
  } else if (palaces.length) {
    sections.push(section('palaces', '十二宫（节选）', 'fact', palaces.slice(0, 6).map((p) => block(buildPalaceVolumeText(p), 'fact'))))
  }
  return sections
}

function buildVol5Sections(input: BuildLifeVolumesInput): VolumeSection[] {
  const explainDomains = input.explain?.sections.find((s) => s.section_id === 'domains')
  if (explainDomains?.blocks.length) {
    return [
      section('domains-explain', '生活域推断', 'inference', explainDomains.blocks.map((b) => ({
        text: truncateText(b.text),
        layer: b.layer,
        classic_id: b.classic_id,
      })), true),
    ]
  }
  const cards = buildBaziModuleCards(input.bazi).filter((c) => c.title !== '开运' && c.title !== '月运')
  if (!cards.length) {
    return [section('vol5-empty', '事理', 'inference', [block('域分析待载入。', 'inference')], true)]
  }
  return cards.map((card, idx) => section(
    `domain-${idx}`,
    card.title,
    'inference',
    [block(`${card.lead}。${truncateText(card.body, 80)}`, 'inference', { score: undefined })],
    true,
  ))
}

function buildVol6Sections(_input: BuildLifeVolumesInput): VolumeSection[] {
  return [
    section('vol6-qa', '问书助手', 'inference', [
      block('卷六需主动展开后提问；打磨期不自动调用 LLM。', 'inference'),
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
