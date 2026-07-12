import type { BaziResponse } from '@/api/bazi'
import { formatRelationLines } from '@/utils/buildEngineTrustDisplay'

export function formatRelationsSummaryText(bazi: BaziResponse | null | undefined): string {
  const rs = bazi?.relations_summary
  if (rs) {
    const parts = [
      rs.interaction_summary,
      rs.clash_summary,
      rs.combine_summary,
      rs.harm_summary,
    ].filter((s) => s?.trim())
    if (parts.length) return parts.join('；')
    if (rs.items?.length) {
      return rs.items.slice(0, 6).map((i) => i.detail || i.type || '').filter(Boolean).join('；')
    }
  }
  const fallback = formatRelationLines(bazi)
  return fallback.slice(0, 4).join('；') || '暂无干支关系摘要'
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
