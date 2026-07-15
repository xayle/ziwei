import type { BaziResponse } from '@/api/bazi'
import { formatBaziRuleMatchLine } from '@/constants/baziRuleFlags'
import {
  formatMissingFieldLabel,
  formatWxList,
} from '@/utils/buildEngineTrustDisplay'
import { truncateText } from '@/utils/truncateText'

export type BaziStructureInsight = {
  hero: string
  insight: string
  trustTip: string | null
}

const STRENGTH_CN: Record<string, string> = {
  extremely_strong: '极旺',
  strong: '偏旺',
  balanced: '中和',
  neutral: '中和',
  weak: '偏弱',
  extremely_weak: '极弱',
}

function strengthLabel(tier?: string | null): string {
  const key = (tier || '').trim()
  return STRENGTH_CN[key] || key || '—'
}

function pickInsight(bazi: BaziResponse): string {
  const evidence = bazi.geju?.evidence_chain
  if (Array.isArray(evidence) && evidence.length) {
    const first = evidence[0] as { text?: string; note?: string; summary?: string }
    const raw = (first.text || first.note || first.summary || '').trim()
    if (raw) return truncateText(raw.replace(/\s+/g, ''), 40)
  }

  const note = (bazi.geju as { note?: string } | undefined)?.note?.trim()
  if (note) return truncateText(note.replace(/\s+/g, ''), 40)

  const rules = bazi.rule_matches
  if (Array.isArray(rules) && rules.length) {
    const line = formatBaziRuleMatchLine(rules[0] as { name?: string; flags?: string[] })
    if (line) return truncateText(line, 40)
  }

  const geju = bazi.geju?.geju_name?.trim()
  const favor = formatWxList(bazi.yongshen?.favor)
  if (geju && favor && favor !== '—') {
    return truncateText(`${geju}，喜用${favor}`, 40)
  }
  if (geju) return truncateText(`格局取「${geju}」，可与月令、透干互核`, 40)
  return '载入后可核对日主、格局与用神'
}

function pickTrustTip(
  bazi: BaziResponse,
  missingFields?: string[] | null,
  validationLines?: string[] | null,
): string | null {
  const missing = (missingFields?.length ? missingFields : bazi.missing_fields) ?? []
  if (missing.length) {
    return `缺：${formatMissingFieldLabel(missing[0])}`
  }
  const line = validationLines?.find((item) => item?.trim())
  if (line) return truncateText(line.trim(), 48)

  const dual = bazi.geju?.recorded_geju && bazi.geju?.engine_geju
    && bazi.geju.recorded_geju !== bazi.geju.engine_geju
  if (dual) {
    return `双轨：古籍「${bazi.geju.recorded_geju}」· 引擎「${bazi.geju.engine_geju}」`
  }
  return null
}

export function buildBaziStructureInsight(
  bazi?: BaziResponse | null,
  opts?: {
    missingFields?: string[] | null
    validationLines?: string[] | null
  },
): BaziStructureInsight | null {
  if (!bazi) return null
  const day = bazi.pillars_primary?.day
  const dayMaster = day?.stem && day?.branch ? `${day.stem}${day.branch}` : '—'
  const geju = bazi.geju?.geju_name?.trim() || '—'
  const favor = formatWxList(bazi.yongshen?.favor)
  const strength = strengthLabel(bazi.day_master_strength?.tier)
  const hero = truncateText(`${dayMaster} · ${geju} · 用神 ${favor} · ${strength}`, 96)
  return {
    hero,
    insight: pickInsight(bazi),
    trustTip: pickTrustTip(bazi, opts?.missingFields, opts?.validationLines),
  }
}
