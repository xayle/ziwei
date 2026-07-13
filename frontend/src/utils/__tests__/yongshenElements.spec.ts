import { describe, expect, it } from 'vitest'
import { toCnElements } from '@/utils/yongshenElements'

describe('toCnElements', () => {
  it('maps English wuxing to Chinese', () => {
    expect(toCnElements(['wood', 'fire'])).toEqual(['木', '火'])
  })

  it('keeps Chinese elements', () => {
    expect(toCnElements(['金', '水'])).toEqual(['金', '水'])
  })

  it('deduplicates mixed input', () => {
    expect(toCnElements(['wood', '木', 'metal'])).toEqual(['木', '金'])
  })
})

describe('formatCnElementsJoin', () => {
  it('joins localized elements with fallback', async () => {
    const { formatCnElementsJoin } = await import('@/utils/yongshenElements')
    expect(formatCnElementsJoin(['wood', 'earth'])).toBe('木、土')
    expect(formatCnElementsJoin([])).toBe('缺失')
    expect(formatCnElementsJoin(undefined, '—')).toBe('—')
  })
})
