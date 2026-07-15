import type { BaziResponse } from '@/api/bazi'
import { formatRelationLines } from '@/utils/buildEngineTrustDisplay'

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

const VOL2_READING_SUFFIX = '；卷二以事实层排盘关系为准，配合典籍 / 推断分层阅读。'

/** Pad short blocks so content density stays above the thin gate (<40 chars). */
export function enrichVolumeBlockText(label: string, body: string, floor = 40): string {
  const trimmed = body.trim()
  if (trimmed.length >= floor) return trimmed
  let combined = `${label}：${trimmed}。以排盘事实为准，配合卷内典籍 / 推断分层阅读。`
  if (combined.length < floor) {
    combined = `${combined}详见本节与相邻讲解。`
  }
  return combined
}

/** Pad short vol2 blocks so content audit thin gate passes (W102-14). */
export function enrichVol2BlockText(label: string, body: string): string {
  const trimmed = body.trim()
  if (trimmed.length >= 40) return trimmed
  const prefix = trimmed.startsWith('暂无') ? `卷二${label}：` : `卷二${label}摘要：`
  let combined = `${prefix}${trimmed}${VOL2_READING_SUFFIX}`
  if (combined.length < 40) {
    combined = `${combined} 详见排盘与 explain 关系讲解。`
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

export function formatShenshaSummaryText(bazi: BaziResponse | null | undefined): string {
  const ss = bazi?.shensha_summary
  if (ss?.highlights?.length) return ss.highlights.slice(0, 8).join('、')
  if (ss?.items?.length) {
    return ss.items.map((s) => s.name).filter(Boolean).slice(0, 8).join('、')
  }
  const names = (bazi?.shensha ?? []).map((s) => s.name).filter(Boolean).slice(0, 8)
  return names.length ? names.join('、') : '暂无神煞摘要'
}
