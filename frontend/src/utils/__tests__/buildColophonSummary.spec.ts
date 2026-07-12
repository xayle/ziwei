import { describe, expect, it } from 'vitest'
import { buildColophonSummary } from '@/utils/buildColophonSummary'

describe('buildColophonSummary', () => {
  it('caps summary at three lines', () => {
    const col = buildColophonSummary({
      engineLabel: 'bazi+ziwei',
      generatedAt: '2026-07-12T00:00:00.000Z',
      missingFields: ['hour_pillar'],
      iztroAdvisory: 'iztro 对照提示',
    })
    expect(col.summary_lines.length).toBeLessThanOrEqual(3)
    expect(col.expandable).toBe(true)
  })

  it('passes wenmo_advisory through to colophon', () => {
    const col = buildColophonSummary({
      wenmoAdvisory: '文墨天机为 advisory 对照轨',
    })
    expect(col.wenmo_advisory).toContain('文墨')
  })
})
