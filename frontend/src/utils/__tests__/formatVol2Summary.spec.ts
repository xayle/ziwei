import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import { enrichVol2BlockText, formatRelationsSummaryText, formatShenshaSummaryText } from '@/utils/formatVol2Summary'

describe('formatVol2Summary', () => {
  it('formatRelationsSummaryText uses relations_summary summary fields', () => {
    const bazi = {
      relations_summary: {
        interaction_summary: '合：子丑',
        clash_summary: '冲：子午',
        combine_summary: '',
        harm_summary: '',
        items: [],
      },
    } as BaziResponse
    expect(formatRelationsSummaryText(bazi)).toBe('合：子丑；冲：子午')
    expect(formatRelationsSummaryText(bazi)).not.toContain('暂无干支关系摘要')
  })

  it('formatRelationsSummaryText maps item.summary not legacy detail-only', () => {
    const bazi = {
      relations_summary: {
        items: [
          { type: '干支互动', subject: '寅/卯', summary: '拱合' },
        ],
      },
    } as BaziResponse
    expect(formatRelationsSummaryText(bazi)).toBe('拱合')
  })

  it('formatRelationsSummaryText falls back to dizhi_relations', () => {
    const bazi = {
      dizhi_relations: [{ type: '六合', branches: '子丑', note: '合化' }],
    } as BaziResponse
    expect(formatRelationsSummaryText(bazi)).toContain('六合')
    expect(formatRelationsSummaryText(bazi)).not.toContain('暂无干支关系摘要')
  })

  it('formatShenshaSummaryText uses highlights', () => {
    const bazi = {
      shensha_summary: { highlights: ['天乙', '文昌'] },
    } as BaziResponse
    expect(formatShenshaSummaryText(bazi)).toBe('天乙、文昌')
  })

  it('enrichVol2BlockText pads short summaries to at least 40 chars', () => {
    const enriched = enrichVol2BlockText('干支关系', '辰戌冲')
    expect(enriched.length).toBeGreaterThanOrEqual(40)
    expect(enriched).toContain('卷二')
  })
})
