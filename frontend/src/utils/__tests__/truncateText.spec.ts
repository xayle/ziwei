import { describe, expect, it } from 'vitest'
import { truncateText } from '@/utils/truncateText'

describe('truncateText', () => {
  it('returns short text unchanged', () => {
    expect(truncateText('短句。')).toBe('短句。')
  })

  it('prefers Chinese sentence boundary over hard cut', () => {
    const body = '甲句完整。乙句也很完整。丙句会被裁掉并尽量不拦腰。'
    const out = truncateText(body.repeat(6), 80)
    expect(out.endsWith('。') || out.endsWith('…')).toBe(true)
    expect(out).toContain('甲句完整。')
  })

  it('allows long vol1 geju explain budget', () => {
    const long = `${'格局讲解完整句。'.repeat(40)}尾部`
    const out = truncateText(long, 500)
    expect(out.length).toBeLessThanOrEqual(500)
    expect(out).toContain('格局讲解完整句。')
  })
})
