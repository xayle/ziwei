import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import {
  buildRelationsClassicQuoteBlocks,
  buildShenshaClassicQuoteBlocks,
  enrichVol2BlockText,
  formatRelationsImpactText,
  formatRelationsSummaryText,
  formatShenshaPolarityTexts,
  formatShenshaSummaryText,
  pickRelationsVerifiedCites,
  relationsSignalTags,
} from '@/utils/formatVol2Summary'

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

  it('enrichVol2BlockText does not pad already-long bodies', () => {
    const body = '甲'.repeat(50)
    expect(enrichVol2BlockText('干支关系', body)).toBe(body)
  })

  it('formatRelationsImpactText expands clash/combine into reading guidance', () => {
    const bazi = {
      relations_summary: {
        clash_summary: '冲：子午',
        combine_summary: '合：子丑',
      },
    } as BaziResponse
    const text = formatRelationsImpactText(bazi)
    expect(text.length).toBeGreaterThanOrEqual(80)
    expect(text).toContain('冲克')
  })

  it('formatShenshaPolarityTexts splits beneficial vs caution', () => {
    const bazi = {
      shensha_summary: {
        items: [
          { name: '天乙', is_beneficial: true },
          { name: '羊刃', is_beneficial: false },
        ],
      },
    } as BaziResponse
    const { auspicious, caution } = formatShenshaPolarityTexts(bazi)
    expect(auspicious).toContain('天乙')
    expect(caution).toContain('羊刃')
  })

  it('pickRelationsVerifiedCites returns host cite for clash', () => {
    const bazi = {
      relations_summary: { clash_summary: '冲：子午', items: [] },
    } as BaziResponse
    const cites = pickRelationsVerifiedCites(bazi, 2)
    expect(cites.length).toBeGreaterThan(0)
    expect(cites[0].layer).toBe('cite')
    expect(cites[0].classic_id).toBe('daizhige.ziping.论刑冲会合解法')
    expect(cites[0].text).toContain('典籍依据')
  })

  it('relationsSignalTags and buildRelationsClassicQuoteBlocks follow clash/combine', () => {
    const bazi = {
      relations_summary: {
        clash_summary: '冲：子午',
        combine_summary: '合：子丑',
      },
    } as BaziResponse
    expect(relationsSignalTags(bazi)).toEqual(expect.arrayContaining(['六冲', '六合']))
    const quotes = buildRelationsClassicQuoteBlocks(bazi)
    expect(quotes.length).toBeGreaterThan(0)
    expect(quotes[0].layer).toBe('inference')
    expect(quotes.some((q) => q.classic_id === 'dizhi_ext01')).toBe(true)
  })

  it('buildShenshaClassicQuoteBlocks mounts soft refs as inference', () => {
    const bazi = {
      shensha_summary: {
        items: [{
          name: '天乙贵人',
          is_beneficial: true,
          classic_source: '三命通会',
          classic_refs: [{
            id: 'shensha_001',
            source: '三命通会·论神煞',
            text: '天乙贵人，命中有之，遇事有贵人扶助。',
            hint_type: 'soft',
          }],
        }],
      },
    } as unknown as BaziResponse
    const quotes = buildShenshaClassicQuoteBlocks(bazi)
    expect(quotes).toHaveLength(1)
    expect(quotes[0].layer).toBe('inference')
    expect(quotes[0].classic_id).toBe('shensha_001')
    expect(quotes[0].text).toContain('贵人扶助')
  })
})
