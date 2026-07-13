import { describe, expect, it, vi } from 'vitest'
import { copyTextToClipboard } from '@/utils/copyText'

describe('copyTextToClipboard', () => {
  it('returns false for empty text', async () => {
    expect(await copyTextToClipboard('  ')).toBe(false)
  })

  it('uses navigator.clipboard when available', async () => {
    const writeText = vi.fn(async () => undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })
    expect(await copyTextToClipboard('钩子句')).toBe(true)
    expect(writeText).toHaveBeenCalledWith('钩子句')
  })
})
