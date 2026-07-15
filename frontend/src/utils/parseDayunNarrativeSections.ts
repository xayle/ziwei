export type DayunNarrativeClassic = {
  source: string
  text: string
}

export type DayunNarrativeSections = {
  core: string
  career: string
  wealth: string
  love: string
  health: string
  trend_note?: string | null
  classics: DayunNarrativeClassic[]
  disclaimer: string
}

const DOMAIN_KEYS = ['事业', '财运', '情感', '健康', '古籍佐证'] as const

/** 从兼容长文还原分域（无 narrative_sections 时的 FE 降级）。 */
export function parseDayunNarrativeSections(
  narrative?: string | null,
): DayunNarrativeSections | null {
  const text = (narrative || '').trim()
  if (!text) return null

  const coreMatch = text.match(/^([\s\S]*?)(?=\n\n【事业】|【事业】)/)
  const core = (coreMatch?.[1] || text.split('【事业】')[0] || '').trim()

  function sliceDomain(label: string, nextLabels: string[]): string {
    const re = new RegExp(
      `【${label}】([\\s\\S]*?)(?=${nextLabels.map((n) => `【${n}】`).join('|')}|（仅供|$)`,
    )
    const m = text.match(re)
    return (m?.[1] || '').trim()
  }

  const career = sliceDomain('事业', ['财运', '情感', '健康', '古籍佐证'])
  const wealth = sliceDomain('财运', ['情感', '健康', '古籍佐证'])
  const love = sliceDomain('情感', ['健康', '古籍佐证'])
  const health = sliceDomain('健康', ['古籍佐证'])

  if (!career && !wealth && !love && !health) {
    // 无标签：整段当作 core，避免假分块
    return {
      core: text,
      career: '',
      wealth: '',
      love: '',
      health: '',
      classics: [],
      disclaimer: '',
    }
  }

  const classicsBlock = text.match(/【古籍佐证】\s*([\s\S]*?)(?=\n\n（仅供|$)/)?.[1] || ''
  const classics: DayunNarrativeClassic[] = []
  for (const line of classicsBlock.split('\n')) {
    const m = line.match(/——([^：:「]+)[：:]?「([^」]+)」/)
      || line.match(/——([^\s「]+)「([^」]+)」/)
    if (m) classics.push({ source: m[1].trim(), text: m[2].trim() })
  }

  const disclaimerMatch = text.match(/（仅供学术研究参考[^）]*）/)
  const trendMatch = text.match(/\n\n((?:此运用神|此运忌神)[\s\S]*?)\n\n【古籍佐证】/)
  const unused = DOMAIN_KEYS
  void unused

  return {
    core,
    career,
    wealth,
    love,
    health,
    trend_note: trendMatch?.[1]?.trim() || null,
    classics,
    disclaimer: disclaimerMatch?.[0] || '（仅供学术研究参考，不构成任何形式的预测或建议）',
  }
}

export function resolveDayunNarrativeSections(
  sections?: DayunNarrativeSections | null,
  narrative?: string | null,
): DayunNarrativeSections | null {
  if (sections?.career || sections?.core) {
    return {
      core: sections.core || '',
      career: sections.career || '',
      wealth: sections.wealth || '',
      love: sections.love || '',
      health: sections.health || '',
      trend_note: sections.trend_note,
      classics: sections.classics || [],
      disclaimer: sections.disclaimer || '',
    }
  }
  return parseDayunNarrativeSections(narrative)
}
