import { describe, expect, it } from 'vitest'
import {
  formatBaziRuleFlags,
  formatBaziRuleMatchLine,
} from '../baziRuleFlags'

describe('baziRuleFlags', () => {
  it('maps known flags to Chinese and drops unknown English keys', () => {
    expect(formatBaziRuleFlags(['broken_geju', 'need_remedy', 'unknown_en_key'])).toEqual([
      '格局破格',
      '需调候补救',
    ])
  })

  it('formats match line without leaking snake_case', () => {
    expect(
      formatBaziRuleMatchLine({
        name: '格局破格需调候',
        flags: ['broken_geju', 'need_remedy', 'variable_fortune'],
      }),
    ).toBe('格局破格需调候：格局破格、需调候补救、运程起伏')
  })

  it('falls back to name only when flags empty', () => {
    expect(formatBaziRuleMatchLine({ name: '木为用神', flags: [] })).toBe('木为用神')
  })
})
