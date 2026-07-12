import { describe, expect, it } from 'vitest'
import { buildDayunDisplayRow, formatYongshenShift } from '@/utils/dayunDisplay'

describe('dayunDisplay', () => {
  it('formats yongshen shift labels', () => {
    expect(formatYongshenShift('forward')).toBe('用神得运（进）')
    expect(formatYongshenShift('backward')).toBe('忌神当令（退）')
    expect(formatYongshenShift('neutral')).toBe('用神进退中性')
    expect(formatYongshenShift()).toBe('')
  })

  it('builds dayun display row with engine hints', () => {
    const row = buildDayunDisplayRow({
      stem: '甲',
      branch: '子',
      ten_god: '比肩',
      geju_impact: '大运比肩助身',
      yongshen_shift: 'forward',
      wealth_hint: '财运平稳',
    }, { range: '2020-2029', narrative: '叙事文本' })

    expect(row.ganzhi).toBe('甲子')
    expect(row.gejuImpact).toBe('大运比肩助身')
    expect(row.yongshenShiftLabel).toBe('用神得运（进）')
    expect(row.hasEngineHints).toBe(true)
    expect(row.hasHeuristicHints).toBe(true)
  })
})
