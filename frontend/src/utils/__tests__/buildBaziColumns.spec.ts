import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import { buildBaziColumns, buildFallbackBaziColumns, baziResponseHasCurrentLiunian, findLiunianItemForYear } from '@/utils/buildBaziColumns'

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
        day: { nayin: '海中金', self_seat: '沐浴', kongwang: ['戌', '亥'] },
        year: { kongwang: ['子', '丑'] },
      },
      dayun: {
        items: [{ stem: '辛', branch: '未', ten_god: '正官', start_year: 2020, kongwang: ['寅', '卯'] }],
      },
      liunian: {
        items: [{ year: 2026, stem: '丙', branch: '午', ten_god: '食神', kongwang: ['辰', '巳'] }],
      },
    } as unknown as BaziResponse

    const columns = buildBaziColumns(result, 2026)
    const dayCol = columns.find((c) => c.key === 'day')
    const yearCol = columns.find((c) => c.key === 'year')
    const liunianCol = columns.find((c) => c.key === 'liunian')
    const dayunCol = columns.find((c) => c.key === 'dayun')

    expect(dayCol?.stem).toBe('甲')
    expect(dayCol?.branch).toBe('子')
    expect(dayCol?.nayin).toBe('海中金')
    expect(dayCol?.void).toBe('戌、亥')
    expect(yearCol?.mainStar).toBe('七杀')
    expect(yearCol?.void).toBe('子、丑')
    expect(liunianCol?.stem).toBe('丙')
    expect(liunianCol?.mainStar).toBe('食神')
    expect(liunianCol?.void).toBe('辰、巳')
    expect(dayunCol?.void).toBe('寅、卯')
  })

  it('does not fall back liunian mainStar to current_liunian ganzhi', () => {
    const result = {
      pillars_primary: {
        year: { stem: '庚', branch: '午' },
        month: { stem: '己', branch: '丑' },
        day: { stem: '甲', branch: '子' },
        hour: { stem: '丙', branch: '寅' },
      },
      current_fortune_summary: { current_liunian: '丙午' },
      liunian: { items: [] },
    } as unknown as BaziResponse

    const liunianCol = buildBaziColumns(result, 2026).find((c) => c.key === 'liunian')
    expect(liunianCol?.mainStar).toBe('缺失')
  })

  it('matches liunian item when year is string from JSON', () => {
    const result = {
      pillars_primary: {
        year: { stem: '庚', branch: '午' },
        month: { stem: '己', branch: '丑' },
        day: { stem: '甲', branch: '子' },
        hour: { stem: '丙', branch: '寅' },
      },
      liunian: {
        items: [{ year: '2026' as unknown as number, stem: '丙', branch: '午', ten_god: '食神' }],
      },
    } as unknown as BaziResponse

    expect(findLiunianItemForYear(result, 2026)?.stem).toBe('丙')
    expect(baziResponseHasCurrentLiunian(result, 2026)).toBe(true)
    const liunianCol = buildBaziColumns(result, 2026).find((c) => c.key === 'liunian')
    expect(liunianCol?.mainStar).toBe('食神')
  })

  it('maps API ten_god into hidden stem rows', () => {
    const result = {
      pillars_primary: {
        year: { stem: '庚', branch: '午' },
        month: { stem: '己', branch: '丑' },
        day: { stem: '甲', branch: '子' },
        hour: { stem: '丙', branch: '寅' },
      },
      kongwang: ['戌', '亥'],
      pillar_details: {
        day: {
          hidden_stems: [{ stem: '癸', ten_god: '偏印' }],
          shensha: [{ name: '天乙', polarity: '+' }, { name: '亡神', polarity: '-' }],
        },
      },
    } as unknown as BaziResponse

    const dayCol = buildBaziColumns(result).find((c) => c.key === 'day')
    expect(dayCol?.hiddenStems?.[0]).toEqual({ stem: '癸', tenGod: '偏印' })
    expect(dayCol?.shensha?.[0]).toMatchObject({ name: '天乙', polarity: '+' })
    expect(dayCol?.shensha?.[1]).toMatchObject({ name: '亡神', polarity: '-' })
  })
})
