import { describe, expect, it } from 'vitest'
import {
  buildClassicCitationRows,
  lookupClassicSourcePage,
} from '@/utils/buildEngineTrustDisplay'

describe('classic citation X-01', () => {
  const sample = [
    {
      id: 'chapter_agg.三命通会',
      title: '《三命通会》',
      source_page: '三命通会',
      verification_status: 'verified',
    },
    {
      id: 'pending.1',
      title: '待核',
      source_page: '',
      verification_status: 'unverified',
    },
  ]

  it('includes source_page on citation rows', () => {
    const rows = buildClassicCitationRows(sample)
    expect(rows[0].sourcePage).toBe('三命通会')
    expect(rows[1].sourcePage).toBeUndefined()
  })

  it('looks up page by classic_id', () => {
    expect(lookupClassicSourcePage('chapter_agg.三命通会', sample)).toBe('三命通会')
    expect(lookupClassicSourcePage('missing', sample)).toBeUndefined()
  })
})
