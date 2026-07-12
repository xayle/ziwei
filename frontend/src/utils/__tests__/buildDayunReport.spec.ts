import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import { buildDayunReportFromBazi } from '@/utils/buildDayunReport'

describe('buildDayunReportFromBazi', () => {
  it('returns null when narratives are missing', () => {
    const bazi = {
      dayun: { items: [{ stem: '甲', branch: '子', start_age: 8 }] },
    } as BaziResponse
    expect(buildDayunReportFromBazi(bazi)).toBeNull()
  })

  it('builds report from bazi dayun narratives', () => {
    const bazi = {
      dayun: {
        items: [
          { stem: '甲', branch: '子', start_age: 8, ten_god: '比肩', narrative: '第一段大运叙事。' },
          { stem: '乙', branch: '丑', start_age: 18, ten_god: '劫财', narrative: '第二段大运叙事。' },
        ],
      },
    } as BaziResponse
    const report = buildDayunReportFromBazi(bazi)
    expect(report?.items).toHaveLength(2)
    expect(report?.items[0].ganzhi).toBe('甲子')
    expect(report?.items[0].end_age).toBe(17)
    expect(report?.narrative_total_chars).toBeGreaterThan(0)
  })
})
