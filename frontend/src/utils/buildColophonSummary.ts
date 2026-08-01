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
    `校勘：${engineBit}；排盘字段${missing.length ? '有注记见下行' : '齐备'}，可核对卷内事实 / 典籍 / 推断分层。`,
    '典籍语料：已挂 verified 引擎条处可标「典籍依据」；其余为软提示见卷二；冲合会专条已挂宿主真子集。',
  ]
  if (missing.length) {
    const labels = missing.slice(0, 4).map(formatMissingFieldLabel)
    lines.push(`字段注记：${labels.join('、')}（不影响已写出块；对照项非故障，展开脚注可核）。`)
  } else if (input.iztroAdvisory?.trim()) {
    lines.push(truncateColophonLine(input.iztroAdvisory, 100))
  } else {
    lines.push('双轨核验：可对照开源排盘与文墨对照盘（若有）；对照差异见脚注，不改写主卷事实。')
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
