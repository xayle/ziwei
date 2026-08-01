import { describe, expect, it } from 'vitest'
import { localizeElementWords, toCnElements } from '@/utils/yongshenElements'

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

describe('localizeElementWords', () => {
  it('replaces English elements glued to Chinese yin/yang', () => {
    expect(localizeElementWords('日主癸 (water阴) 的')).toBe('日主癸 (水阴) 的')
    expect(localizeElementWords('日主甲（wood阳）')).toBe('日主甲（木阳）')
  })
})
