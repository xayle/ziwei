import type {
  ActionItem,
  DimensionScore,
  PalaceCross,
  RelationFullResponse,
  SummaryCard,
  TimelineNode,
} from '@/api/relation'

export interface RelationCompatDisplay {
  title: string
  subtitle: string
  combinedScore: number
  grade: string
  summary: string
  summaryCards: SummaryCard[]
  dimensions: DimensionScore[]
  palaceCross: PalaceCross[]
  timeline: TimelineNode[]
  actionItems: ActionItem[]
  tensions: { code: string; message: string }[]
  inferenceCollapsed: boolean
}

export function buildRelationCompat(raw: RelationFullResponse): RelationCompatDisplay {
  const a = raw.person_a?.label || '甲'
  const b = raw.person_b?.label || '乙'
  const typeLabel = raw.relation_type_label || raw.relation_type

  return {
    title: `${typeLabel}`,
    subtitle: `${a} × ${b}`,
    combinedScore: raw.combined_score,
    grade: raw.grade || '—',
    summary: raw.summary,
    summaryCards: raw.summary_cards || [],
    dimensions: raw.dimensions || [],
    palaceCross: raw.palace_cross || [],
    timeline: raw.timeline || [],
    actionItems: raw.action_items || [],
    tensions: raw.tensions || [],
    inferenceCollapsed: true,
  }
}

export function dimensionPct(d: DimensionScore): number {
  if (!d.max_score) return 0
  return Math.round((d.score / d.max_score) * 100)
}

export function cardToneClass(tone: SummaryCard['tone']): string {
  const map: Record<SummaryCard['tone'], string> = {
    support: 'tone-support',
    conflict: 'tone-conflict',
    neutral: 'tone-neutral',
    action: 'tone-action',
  }
  return map[tone] || 'tone-neutral'
}
