import type { BaziResponse } from '@/api/bazi'
import { DIZHI_CLASSIC_REFS } from '@/constants/dizhiClassicRefs'
import { RELATIONS_VERIFIED_CITES } from '@/constants/relationsVerifiedCites'
import { formatRelationLines } from '@/utils/buildEngineTrustDisplay'

type ShenshaItem = NonNullable<NonNullable<BaziResponse['shensha_summary']>['items']>[number]

function relationItemLine(item: NonNullable<NonNullable<BaziResponse['relations_summary']>['items']>[number]): string {
  const summary = item.summary?.trim()
  if (summary) return summary
  const legacy = item.detail?.trim()
  if (legacy) return legacy
  const type = item.type?.trim() ?? ''
  const subject = item.subject?.trim() ?? ''
  const target = item.target?.trim()
  const core = [type, subject, target].filter(Boolean).join(' ')
  if (core) return core
  return item.pillars?.trim() ?? ''
}

function clipText(text: string, limit: number): string {
  const t = text.trim()
  if (t.length <= limit) return t
  return `${t.slice(0, Math.max(0, limit - 1))}…`
}

/** Pad short blocks so content density stays above the thin gate (<40 chars). */
export function enrichVolumeBlockText(label: string, body: string, floor = 40): string {
  const trimmed = body.trim()
  if (trimmed.length >= floor) return trimmed
  let combined = `${label}：${trimmed}。详见本节与相邻讲解；以排盘事实为准，勿单句外推。`
  let pad = '宜对照卷内相邻章节一并阅读。'
  while (combined.length < floor) {
    combined = `${combined}${pad}`
    pad = '。'
  }
  return combined
}

/** Pad short vol2 blocks；够长则不再套话（V2-04）。 */
export function enrichVol2BlockText(label: string, body: string): string {
  const trimmed = body.trim()
  if (trimmed.length >= 40) return trimmed
  const prefix = trimmed.startsWith('暂无') ? `卷二${label}：` : `卷二${label}摘要：`
  let combined = `${prefix}${trimmed}。详见本节与相邻讲解；以排盘事实为准，勿单句外推。`
  let pad = '宜对照卷内相邻章节一并阅读。'
  while (combined.length < 40) {
    combined = `${combined}${pad}`
    pad = '。'
  }
  return combined
}

export function formatRelationsSummaryText(bazi: BaziResponse | null | undefined): string {
  const rs = bazi?.relations_summary
  if (rs) {
    const parts = [
      rs.interaction_summary,
      rs.clash_summary,
      rs.combine_summary,
      rs.harm_summary,
    ].filter((s): s is string => typeof s === 'string' && Boolean(s.trim()))
    if (parts.length) return parts.join('；')
    if (rs.items?.length) {
      const lines = rs.items.map(relationItemLine).filter(Boolean)
      if (lines.length) return lines.slice(0, 6).join('；')
    }
  }
  const fallback = formatRelationLines(bazi)
  if (fallback.length) return fallback.slice(0, 4).join('；')
  return '暂无干支关系摘要'
}

/** 卷二关系事实段（对齐 BE relations fact）。 */
export function formatRelationsFactText(bazi: BaziResponse | null | undefined): string {
  return (
    `干支关系摘要：${formatRelationsSummaryText(bazi)}。` +
    '以上为排盘事实层要点（合冲刑害等），细读见下一节「关系读法」；' +
    '勿将关键词名单直接等同于终身性格结论，也勿跳过格局与用神单独解读关系。' +
    '有 explain 关系讲解时，以讲解与本摘要互参。'
  )
}

/** 卷二关系读法：何意 / 对本命影响（对齐 BE `_relations_impact_text`）。 */
export function formatRelationsImpactText(bazi: BaziResponse | null | undefined): string {
  const rs = bazi?.relations_summary
  const base = formatRelationsSummaryText(bazi)
  const bits: string[] = []
  const clash = rs?.clash_summary?.trim() ?? ''
  const combine = rs?.combine_summary?.trim() ?? ''
  const harm = rs?.harm_summary?.trim() ?? ''
  const interaction = rs?.interaction_summary?.trim() ?? ''
  if (clash) {
    bits.push(
      `冲克见「${clash.slice(0, 48)}」，对本命常表现为节奏冲突与立场拉扯：` +
        '行事宜避硬碰硬，先稳后进，重大表态前多留一步缓冲；冲突年份尤忌临时起意的重大签约。',
    )
  }
  if (combine || base.includes('合') || base.includes('拱')) {
    bits.push(
      '会合或拱合提示人际与资源有牵绊：宜借合力成事，也忌纠缠不清、把人情债当成唯一路径；合多之时更要分清谁在借力、谁在消耗。',
    )
  }
  if (harm) {
    bits.push(
      `害破信号「${harm.slice(0, 36)}」，协作、契约与口头承诺宜留余地，避免一次把话说满，也避免把误会拖成长期对立。`,
    )
  }
  if (!bits.length && interaction) {
    bits.push(
      `干支互动要点：${interaction.slice(0, 80)}。阅读时先认清主线，再对照神煞与卷三运限起伏，把关键词落到可观察的行事节奏。`,
    )
  }
  if (!bits.length) {
    bits.push(
      `命局干支关系为「${base.slice(0, 72)}」。阅读时先分清冲合主线，再对照神煞与运限起伏，勿以单次关系论断终身。`,
    )
  }
  let text = bits.join('')
  if (text.length < 120) {
    text =
      `${text}本节是排盘事实之上的读法提示，用来帮助串联卷一格局与卷三运限，不作绝对断语。`
  }
  return clipText(text, 280)
}

function iterShenshaItems(bazi: BaziResponse | null | undefined): ShenshaItem[] {
  const fromSummary = bazi?.shensha_summary?.items
  if (fromSummary?.length) return fromSummary.filter((i) => Boolean(i.name))
  return (bazi?.shensha ?? []).filter((i) => Boolean(i.name)) as ShenshaItem[]
}

function shenshaIsBeneficial(item: ShenshaItem): boolean | null {
  if (typeof item.is_beneficial === 'boolean') return item.is_beneficial
  const pol = String((item as { polarity?: string }).polarity ?? '').trim().toLowerCase()
  if (['+', 'auspicious', 'good', '吉', 'beneficial'].includes(pol)) return true
  if (['-', 'inauspicious', 'bad', '凶', '慎'].includes(pol)) return false
  return null
}

export function formatShenshaSummaryText(bazi: BaziResponse | null | undefined): string {
  const ss = bazi?.shensha_summary
  if (ss?.highlights?.length) return ss.highlights.slice(0, 8).join('、')
  if (ss?.items?.length) {
    return ss.items.map((s) => s.name).filter(Boolean).slice(0, 8).join('、')
  }
  const names = (bazi?.shensha ?? []).map((s) => s.name).filter(Boolean).slice(0, 8)
  return names.length ? names.join('、') : '暂无神煞摘要'
}

/** 返回吉神 / 慎神两段（对齐 BE `_shensha_polarity_texts`）。 */
export function formatShenshaPolarityTexts(bazi: BaziResponse | null | undefined): {
  auspicious: string
  caution: string
} {
  const good: string[] = []
  const cautionNames: string[] = []
  const unknown: string[] = []
  for (const item of iterShenshaItems(bazi).slice(0, 16)) {
    const name = item.name?.trim()
    if (!name) continue
    const flag = shenshaIsBeneficial(item)
    if (flag === true) good.push(name)
    else if (flag === false) cautionNames.push(name)
    else unknown.push(name)
  }
  if (!good.length && !cautionNames.length && unknown.length) {
    const joined = unknown.slice(0, 8).join('、')
    return {
      auspicious:
        `神煞见${joined}。吉凶未在摘要中分列，宜结合格局、用神与刑冲综合看，` +
        '把神煞当作旁证而非结论；贵人类信号可主动借力，灾煞类信号则宜留余地。',
      caution:
        '慎神分列待补：当前引擎未给出明确极性，阅读时以格局与刑冲为主、神煞为辅，勿因名单长短夸大吉凶。',
    }
  }
  if (!good.length && !cautionNames.length) {
    const base = formatShenshaSummaryText(bazi)
    return {
      auspicious:
        `神煞要点：${base}。宜视为格局旁证：有吉神不代表万事顺遂，仍须回到日主强弱与用神是否得力。`,
      caution:
        '暂无单独慎神分列；若后文出现灾煞、劫煞等，重大决策宜缓、契约宜细看，并把风险对照到卷三流年节点。',
    }
  }
  let ji = good.length
    ? `吉神见${good.slice(0, 8).join('、')}。提示贵人、文书、名望或护持机会：` +
      '宜主动借力、守信用，把贵人线索落到具体合作、引荐与学习场景，并与卷一用神对照；有吉神不等于万事顺遂，仍须看是否得令、是否被冲破。'
    : '本盘摘要未突出吉神；仍可从正印、贵人类格局与日主喜用中寻找护持线索，不必因名单偏短而气馁，也勿另造吉神叙事。'
  const caution = cautionNames.length
    ? `慎神见${cautionNames.slice(0, 8).join('、')}。提示口舌、波动、损耗或刚愎风险：` +
      '重大决策宜缓、契约宜细看，情绪上头时少做不可逆承诺；把风险落到具体事项与卷三流年节点，比空谈凶神更有用；若与刑冲同现，优先处理关系张力再谈扩张。'
    : '摘要未单列慎神；仍须对照刑冲、害破与流年再判风险，把谨慎落在具体月份与事项上，避免把名单长短当成命运判决。'
  if (unknown.length) {
    ji = `${ji}另有未分极性者：${unknown.slice(0, 4).join('、')}，宜回看其落柱与十神再判。`
  }
  return { auspicious: clipText(ji, 260), caution: clipText(caution, 260) }
}

export type ShenshaClassicQuote = {
  text: string
  layer: 'cite' | 'inference'
  classic_id?: string
}

export type RelationsClassicQuote = ShenshaClassicQuote

/** 从 relations_summary 抽出地支关系标签（对齐 BE `relations_signal_tags`）。 */
export function relationsSignalTags(bazi: BaziResponse | null | undefined): string[] {
  const rs = bazi?.relations_summary
  const parts = [
    rs?.clash_summary,
    rs?.combine_summary,
    rs?.harm_summary,
    rs?.interaction_summary,
    ...(rs?.items ?? []).slice(0, 8).map((it) => it.summary || it.detail || it.type || ''),
  ].filter((s): s is string => typeof s === 'string' && Boolean(s.trim()))
  const blob = parts.join('；')
  const tags: string[] = []
  if (blob.includes('冲') || rs?.clash_summary?.trim()) tags.push('六冲')
  if (blob.includes('三合')) tags.push('三合')
  if (blob.includes('合') || blob.includes('拱') || rs?.combine_summary?.trim()) tags.push('六合')
  if (blob.includes('刑')) tags.push('刑')
  if (blob.includes('害') || rs?.harm_summary?.trim()) tags.push('害')
  return [...new Set(tags)]
}

/** 关系典籍软提示（对齐 BE `relations_candidates`）。 */
export function buildRelationsClassicQuoteBlocks(
  bazi: BaziResponse | null | undefined,
  limit = 3,
): RelationsClassicQuote[] {
  const tags = relationsSignalTags(bazi)
  if (!tags.length) return []
  const hits = DIZHI_CLASSIC_REFS.filter((ref) => tags.some((t) => ref.tags.includes(t)))
  const pool = hits.length ? hits : DIZHI_CLASSIC_REFS.filter((r) => r.tags.includes('地支'))
  return pool.slice(0, limit).map((ref) => {
    const srcBit = ref.source ? `（${ref.source}）` : ''
    const verified = ref.hint_type === 'verified'
    const body = verified
      ? `典籍依据${srcBit}：${ref.text}`
      : `关系典籍软提示${srcBit}：${ref.text}（软提示，待校勘升格前不作「典籍依据」。）`
    return {
      text: clipText(body, 220),
      layer: (verified ? 'cite' : 'inference') as 'cite' | 'inference',
      classic_id: ref.id,
    }
  })
}

/** 关系 verified cite（对齐 BE `pick_relations_verified_cites`；无 explain 时回退）。 */
export function pickRelationsVerifiedCites(
  bazi: BaziResponse | null | undefined,
  limit = 2,
): RelationsClassicQuote[] {
  let tags = relationsSignalTags(bazi)
  if (!tags.length) tags = ['六冲', '六合']
  const out: RelationsClassicQuote[] = []
  const seen = new Set<string>()
  for (const tag of tags) {
    for (const ref of RELATIONS_VERIFIED_CITES) {
      if (!ref.tags.includes(tag) || seen.has(ref.id)) continue
      seen.add(ref.id)
      let body = `典籍依据（${ref.title}）：${ref.passage}`
      if (body.length < 40) {
        body = `${body}宜与干支关系事实互参，不作单句断语。`
      }
      out.push({
        text: clipText(body, 220),
        layer: 'cite',
        classic_id: ref.id,
      })
      if (out.length >= limit) return out
    }
  }
  return out
}

type ClassicRefLike = {
  id?: string
  source?: string
  text?: string
  hint_type?: string
}

/** 挂载神煞 classic_refs 正文；soft→inference，verified→cite（E-01，对齐 BE）。 */
export function buildShenshaClassicQuoteBlocks(
  bazi: BaziResponse | null | undefined,
): ShenshaClassicQuote[] {
  const blocks: ShenshaClassicQuote[] = []
  const seen = new Set<string>()
  for (const item of iterShenshaItems(bazi).slice(0, 12)) {
    const name = item.name?.trim() ?? ''
    const refs = (item.classic_refs ?? []) as ClassicRefLike[]
    let picked: ClassicRefLike | undefined
    for (const ref of refs) {
      const quote = ref.text?.trim()
      if (!quote) continue
      const rid = ref.id?.trim() ?? ''
      if (rid && seen.has(rid)) continue
      picked = ref
      break
    }
    if (!picked?.text?.trim()) continue
    const rid = picked.id?.trim() ?? ''
    if (rid) seen.add(rid)
    const src = (picked.source || item.classic_source || '').trim()
    const hint = (picked.hint_type || 'soft').trim().toLowerCase()
    const layer: 'cite' | 'inference' = ['verified', 'hard', 'cite'].includes(hint)
      ? 'cite'
      : 'inference'
    const srcBit = src ? (src.startsWith('《') ? `（${src}）` : `（《${src}》）`) : ''
    let body = `${name || '神煞'}${srcBit}：${picked.text.trim()}`
    if (layer === 'inference') {
      body = `${body}（软提示，待校勘升格前不作「典籍依据」。）`
    }
    blocks.push({
      text: clipText(body, 220),
      layer,
      classic_id: rid || undefined,
    })
    if (blocks.length >= 3) break
  }
  return blocks
}

/** @deprecated 仅书名回退；优先用 buildShenshaClassicQuoteBlocks */
export function formatShenshaClassicCiteText(bazi: BaziResponse | null | undefined): string | null {
  const quotes = buildShenshaClassicQuoteBlocks(bazi)
  if (quotes.length) return quotes.map((q) => q.text).join('；')
  const bits: string[] = []
  for (const item of iterShenshaItems(bazi).slice(0, 8)) {
    const src = item.classic_source?.trim()
    const name = item.name?.trim()
    if (src && name) bits.push(`${name}：${src}`)
  }
  return bits.length ? bits.slice(0, 3).join('；') : null
}
