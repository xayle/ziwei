import { describe, expect, it } from 'vitest'
import { formatConversionRate } from '@/api/creatorStats'

describe('formatConversionRate', () => {
  it('formats finite rates as percent', () => {
    expect(formatConversionRate(0)).toBe('0.0%')
    expect(formatConversionRate(0.125)).toBe('12.5%')
    expect(formatConversionRate(1)).toBe('100.0%')
  })

  it('returns dash for invalid', () => {
    expect(formatConversionRate(undefined)).toBe('—')
    expect(formatConversionRate(Number.NaN)).toBe('—')
  })
})
