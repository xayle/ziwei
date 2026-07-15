import type { BaziResponse, DayunReportItem, DayunReportResponse } from '@/api/bazi'

function dayunEndAge(
  items: Array<{ start_age?: number | null }>,
  index: number,
): number | undefined {
  const current = items[index]
  if (!current?.start_age && current?.start_age !== 0) return undefined
  const next = items[index + 1]
  if (next?.start_age != null) return Number(next.start_age) - 1
  return Number(current.start_age) + 9
}

export function buildDayunReportFromBazi(bazi: BaziResponse | null): DayunReportResponse | null {
  const items = bazi?.dayun?.items ?? bazi?.dayun?.cycles ?? []
  if (!items.length) return null

  const hasNarrative = items.some((item) => !!item.narrative?.trim())
  if (!hasNarrative) return null

  const reportItems: DayunReportItem[] = items.map((item, index) => {
    const ganzhi = `${item.stem || ''}${item.branch || ''}`.trim()
    const sections = (item as { narrative_sections?: DayunReportItem['narrative_sections'] }).narrative_sections
    return {
      ganzhi,
      start_age: item.start_age ?? undefined,
      end_age: dayunEndAge(items, index),
      ten_god: item.ten_god ?? undefined,
      narrative: item.narrative || '',
      narrative_sections: sections ?? undefined,
    }
  })

  return {
    items: reportItems,
    narrative_total_chars: reportItems.reduce((sum, item) => sum + item.narrative.length, 0),
  }
}
