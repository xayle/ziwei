import { describe, expect, it } from 'vitest'
import {
  buildDayunDisplayRow,
  buildDayunVolumeText,
  formatDayunAgeRange,
  formatDayunStartAge,
  formatYongshenShift,
} from '@/utils/dayunDisplay'

describe('dayunDisplay', () => {
  it('formats yongshen shift labels', () => {
    expect(formatYongshenShift('forward')).toBe('用神得运（进）')
    expect(formatYongshenShift('backward')).toBe('忌神当令（退）')
    expect(formatYongshenShift('neutral')).toBe('用神进退中性')
    expect(formatYongshenShift()).toBe('')
  })

  it('formats dayun ages as integers without decimal noise', () => {
    expect(formatDayunStartAge(10.0)).toBe('10岁起')
    expect(formatDayunStartAge(0.0)).toBe('0岁起')
    expect(formatDayunAgeRange(10.0, 19.0)).toBe('10–19岁')
  })

  it('builds thickened dayun volume text with narrative', () => {
    const text = buildDayunVolumeText({
      stem: '丙',
      branch: '子',
      start_age: 10,
      start_year: 2000,
      ten_god: '正官',
      yongshen_shift: 'forward',
      narrative: '此运官星当令，宜守正出奇，在稳定岗位中积累资历与口碑。',
    }, 0, [{ start_age: 10 }, { start_age: 20 }])
    expect(text).toContain('1. 丙子')
    expect(text).toContain('10–19岁')
    expect(text).toContain('十神 正官')
    expect(text).not.toContain('0.0')
    expect(text.length).toBeGreaterThan(40)
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
