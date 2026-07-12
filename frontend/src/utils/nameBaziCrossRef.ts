import type { BaziResponse } from '@/api/bazi'
import type { NameAnalysisResponse } from '@/api/name'

const ELEMENT_EN_TO_CN: Record<string, string> = {
  metal: '金',
  wood: '木',
  water: '水',
  fire: '火',
  earth: '土',
}

const ELEMENT_CN_SET = new Set(['金', '木', '水', '火', '土'])

export type NameElementAlignment = 'favor' | 'avoid' | 'neutral'

export type NameBaziCrossItem = {
  label: string
  element: string
  lucky: string
  alignment: NameElementAlignment
  note: string
}

export type NameBaziCrossRef = {
  favorCn: string[]
  avoidCn: string[]
  items: NameBaziCrossItem[]
  sancaiElements: string[]
  sancaiAlignment: NameElementAlignment
  verdict: string
  rationale?: string
}

function normalizeElementCn(raw: string): string | null {
  const trimmed = raw.trim()
  if (ELEMENT_CN_SET.has(trimmed)) return trimmed
  const mapped = ELEMENT_EN_TO_CN[trimmed.toLowerCase()]
  return mapped ?? null
}

function toCnElementSet(values: string[] | undefined): string[] {
  if (!values?.length) return []
  const out = new Set<string>()
  for (const value of values) {
    const cn = normalizeElementCn(value)
    if (cn) out.add(cn)
  }
  return [...out]
}

function alignElement(element: string, favor: Set<string>, avoid: Set<string>): NameElementAlignment {
  if (favor.has(element)) return 'favor'
  if (avoid.has(element)) return 'avoid'
  return 'neutral'
}

function alignmentNote(alignment: NameElementAlignment, element: string, favor: Set<string>): string {
  if (alignment === 'favor') return `「${element}」与八字喜用（${[...favor].join('、')}）相合`
  if (alignment === 'avoid') return `「${element}」落入八字忌避范围，宜留意`
  return '与喜忌无直接冲突'
}

export function buildNameBaziCrossRef(
  name: NameAnalysisResponse | null,
  bazi: BaziResponse | null,
): NameBaziCrossRef | null {
  if (!name || !bazi?.yongshen) return null

  const favorCn = toCnElementSet(bazi.yongshen.favor)
  const avoidCn = toCnElementSet(bazi.yongshen.avoid)
  const favor = new Set(favorCn)
  const avoid = new Set(avoidCn)

  const grids = [
    { label: '天格', info: name.tianke },
    { label: '人格', info: name.renke },
    { label: '地格', info: name.dike },
    { label: '外格', info: name.waike },
    { label: '总格', info: name.zonge },
  ]

  const items: NameBaziCrossItem[] = grids.map(({ label, info }) => {
    const alignment = alignElement(info.element, favor, avoid)
    return {
      label,
      element: info.element,
      lucky: info.lucky,
      alignment,
      note: alignmentNote(alignment, info.element, favor),
    }
  })

  const sancaiElements = [...name.sancai.pattern].filter((ch) => ELEMENT_CN_SET.has(ch))
  const sancaiHits = sancaiElements.filter((el) => favor.has(el)).length
  const sancaiAvoids = sancaiElements.filter((el) => avoid.has(el)).length
  const sancaiAlignment: NameElementAlignment = sancaiAvoids > 0
    ? 'avoid'
    : sancaiHits >= 2
      ? 'favor'
      : 'neutral'

  const core = items.find((item) => item.label === '人格')
  const verdict = !favorCn.length
    ? '八字用神未明确，姓名五行对照仅供参考。'
    : core?.alignment === 'favor' && sancaiAlignment !== 'avoid'
      ? `姓名主运（人格${core.element}）与八字喜用「${favorCn.join('、')}」相合，可视为补益。`
      : core?.alignment === 'avoid' || sancaiAlignment === 'avoid'
        ? `姓名五行与八字忌避存在张力，宜结合改名建议或后天调候。`
        : `姓名五行与八字喜用部分呼应，建议以人格、地格为主综合取舍。`

  return {
    favorCn,
    avoidCn,
    items,
    sancaiElements,
    sancaiAlignment,
    verdict,
    rationale: bazi.yongshen.rationale,
  }
}
