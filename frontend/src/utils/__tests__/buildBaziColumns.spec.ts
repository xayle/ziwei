import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import { buildBaziColumns, buildFallbackBaziColumns } from '@/utils/buildBaziColumns'

describe('buildBaziColumns', () => {
  it('returns fallback columns when result is null', () => {
    const columns = buildBaziColumns(null)
    expect(columns).toHaveLength(6)
    expect(columns[4].key).toBe('day')
    expect(columns[4].mainStar).toBe('日主')
    expect(columns[0].stem).toBe('待计算')
  })

  it('exports stable fallback helper', () => {
    expect(buildFallbackBaziColumns()).toEqual(buildBaziColumns(null))
  })

  it('maps pillar data from API response', () => {
    const result = {
      pillars_primary: {
        year: { stem: '庚', branch: '午' },
        month: { stem: '己', branch: '丑' },
        day: { stem: '甲', branch: '子' },
        hour: { stem: '丙', branch: '寅' },
      },
      ten_gods: { year: '七杀', month: '正财', hour: '食神' },
      kongwang: ['戌', '亥'],
      pillar_details: {
        day: { nayin: '海中金', self_seat: '沐浴' },
      },
      dayun: {
        items: [{ stem: '辛', branch: '未', ten_god: '正官', start_year: 2020 }],
      },
      liunian: {
        items: [{ year: 2026, stem: '丙', branch: '午', ten_god: '食神' }],
      },
    } as unknown as BaziResponse

    const columns = buildBaziColumns(result, 2026)
    const dayCol = columns.find((c) => c.key === 'day')
    const yearCol = columns.find((c) => c.key === 'year')
    const liunianCol = columns.find((c) => c.key === 'liunian')

    expect(dayCol?.stem).toBe('甲')
    expect(dayCol?.branch).toBe('子')
    expect(dayCol?.nayin).toBe('海中金')
    expect(yearCol?.mainStar).toBe('七杀')
    expect(liunianCol?.stem).toBe('丙')
    expect(liunianCol?.void).toBe('戌、亥')
  })
})
