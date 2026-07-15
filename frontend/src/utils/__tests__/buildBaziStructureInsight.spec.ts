import { describe, expect, it } from 'vitest'
import { buildBaziStructureInsight } from '@/utils/buildBaziStructureInsight'

describe('buildBaziStructureInsight', () => {
  it('builds hero + short insight from engine fields', () => {
    const insight = buildBaziStructureInsight({
      pillars_primary: {
        day: { stem: '庚', branch: '辰' },
      },
      geju: {
        geju_name: '正印格',
        evidence_chain: [{ text: '月令印星透干，喜火土调候补气' }],
      },
      yongshen: { favor: ['fire', 'earth'] },
      day_master_strength: { tier: 'balanced' },
    } as never)

    expect(insight?.hero).toContain('庚辰')
    expect(insight?.hero).toContain('正印格')
    expect(insight?.hero).toContain('火')
    expect(insight?.insight.length).toBeLessThanOrEqual(40)
    expect(insight?.insight).toContain('月令印星')
  })

  it('surfaces missing field as trust tip', () => {
    const insight = buildBaziStructureInsight(
      {
        pillars_primary: { day: { stem: '甲', branch: '子' } },
        geju: { geju_name: '建禄格' },
        yongshen: { favor: ['water'] },
        day_master_strength: { tier: 'strong' },
      } as never,
      { missingFields: ['forecast'] },
    )
    expect(insight?.trustTip).toMatch(/缺/)
  })

  it('returns null without bazi', () => {
    expect(buildBaziStructureInsight(null)).toBeNull()
  })
})
