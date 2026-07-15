import type { Colophon } from '@/types/life-volume'
import { formatMissingFieldLabel } from '@/utils/buildEngineTrustDisplay'

export interface ColophonInput {
  missingFields?: string[]
  iztroAdvisory?: string
  wenmoAdvisory?: string
  dualTrackNote?: string
  engineLabel?: string
  generatedAt?: string
}

const DEFAULT_DISCLAIMER = '本辑录仅供文化研究与自我认知参考，不构成医疗、法律或投资建议。'

/** 与 `life_volume_service._build_colophon` 对齐：人读注记，不用 raw key。 */
export function buildColophonSummary(input: ColophonInput): Colophon {
  const missing = (input.missingFields ?? []).map((f) => f.trim()).filter(Boolean)
  const engineBit = input.engineLabel
    ? `引擎 ${input.engineLabel}${input.generatedAt ? ` · ${input.generatedAt.slice(0, 10)}` : ''}`
    : '引擎 —'
  const lines: string[] = [
    `校勘：${engineBit}；排盘字段${missing.length ? '有注记见下行' : '齐备'}，可核对卷内 fact/cite/inference 分层。`,
  ]
  if (missing.length) {
    const labels = missing.slice(0, 4).map(formatMissingFieldLabel)
    lines.push(`字段注记：${labels.join('、')}（不影响已写出块；对照项非故障，展开脚注可核）。`)
  }
  if (input.iztroAdvisory?.trim()) {
    lines.push(truncateColophonLine(input.iztroAdvisory))
  }
  if (lines.length === 1 && !missing.length) {
    lines.push('双轨核验：可对照开源排盘 / 文墨对照（若有）。')
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
