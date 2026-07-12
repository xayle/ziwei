import type { Colophon } from '@/types/life-volume'

export interface ColophonInput {
  missingFields?: string[]
  iztroAdvisory?: string
  wenmoAdvisory?: string
  dualTrackNote?: string
  engineLabel?: string
  generatedAt?: string
}

const DEFAULT_DISCLAIMER = '本辑录仅供文化研究与自我认知参考，不构成医疗、法律或投资建议。'

export function buildColophonSummary(input: ColophonInput): Colophon {
  const lines: string[] = []
  if (input.engineLabel) {
    lines.push(`引擎 ${input.engineLabel}${input.generatedAt ? ` · ${input.generatedAt.slice(0, 10)}` : ''}`)
  }
  if (input.missingFields?.length) {
    lines.push(`缺失字段：${input.missingFields.slice(0, 4).join('、')}`)
  } else {
    lines.push('排盘字段齐备，可核对卷内 fact/cite/inference 分层。')
  }
  if (input.iztroAdvisory?.trim()) {
    lines.push(truncateColophonLine(input.iztroAdvisory))
  }
  return {
    summary_lines: lines.slice(0, 3),
    missing_fields: input.missingFields,
    iztro_advisory: input.iztroAdvisory,
    wenmo_advisory: input.wenmoAdvisory,
    dual_track_note: input.dualTrackNote,
    expandable: true,
  }
}

export function defaultDisclaimerBlock() {
  return {
    text: DEFAULT_DISCLAIMER,
    version: '2026-07-12',
    jurisdiction: 'CN',
  }
}

function truncateColophonLine(text: string, max = 72): string {
  const t = text.trim()
  if (t.length <= max) return t
  return `${t.slice(0, max - 1)}…`
}
