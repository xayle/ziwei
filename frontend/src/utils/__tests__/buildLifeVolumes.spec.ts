import { describe, expect, it } from 'vitest'
import { buildLifeVolumes } from '@/utils/buildLifeVolumes'
import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'

const minimalBazi = {
  pillars_primary: {
    day: { stem: '甲', branch: '子' },
    year: { stem: '庚', branch: '午' },
    month: { stem: '丙', branch: '寅' },
    hour: { stem: '壬', branch: '申' },
  },
  geju: { geju_name: '正官格', interpretation_text: '测试格局' },
  personality: { day_stem_trait: '仁慈', interpretation_text: '性格测试文案' },
  career: { career_score: 80, interpretation_text: '事业测试' },
  wealth_analysis: { wealth_tier: '中', interpretation_text: '财运测试' },
  marriage_analysis: { marriage_score: 70, interpretation_text: '婚恋测试' },
  health: { risk_level: '低', interpretation_text: '健康测试' },
  relationship: { relationship_score: 75, interpretation_text: '人际测试' },
  shensha: [{ name: '天乙' }],
} as BaziResponse

describe('buildLifeVolumes', () => {
  it('returns life-volume@1.0 with eight volumes', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
      profileLabel: '测试档案',
    })
    expect(doc.schema_version).toBe('life-volume@1.0')
    expect(doc.volumes).toHaveLength(8)
    expect(doc.volumes.map((v) => v.id)).toEqual([
      'preface', 'vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6', 'colophon',
    ])
    expect(doc.colophon.summary_lines.length).toBeLessThanOrEqual(3)
  })

  it('colophon summary_lines capped at three', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
      iztroAdvisory: 'iztro 提示',
      wenmoAdvisory: '文墨对照',
      engineLabel: 'e2e',
      generatedAt: '2026-07-12T00:00:00Z',
      missingFields: ['a', 'b', 'c', 'd'],
    })
    expect(doc.colophon.summary_lines.length).toBeLessThanOrEqual(3)
    expect(doc.colophon.wenmo_advisory).toContain('文墨')
  })

  it('matches life-volume@1.0 required top-level keys', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
    })
    expect(doc).toMatchObject({
      schema_version: 'life-volume@1.0',
      case_id: 'case-1',
      chart_hash: 'hash-1',
    })
    expect(doc.disclaimer_block?.text).toBeTruthy()
    expect(doc.volumes).toHaveLength(8)
    expect(doc.colophon.expandable).toBe(true)
  })

  it('marks vol5 sections as inference and collapsed', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
    })
    const vol5 = doc.volumes.find((v) => v.id === 'vol5')
    expect(vol5?.sections.length).toBeGreaterThan(0)
    expect(vol5?.sections.every((s) => s.layer === 'inference')).toBe(true)
    expect(vol5?.sections.every((s) => s.collapsed_default)).toBe(true)
  })

  it('builds all six narrative volumes with at least one section', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
    })
    for (const id of ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] as const) {
      const volume = doc.volumes.find((v) => v.id === id)
      expect(volume?.sections.length).toBeGreaterThan(0)
    }
  })

  it('merges explain batches into vol1 vol2 vol5 with layered blocks', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
      explain: {
        chart_hash: 'hash-1',
        disclaimer_block: { text: '仅供文化研究', version: '1.0' },
        sections: [
          {
            section_id: 'geju',
            blocks: [{ text: '正官格典籍句', layer: 'cite', classic_id: 'CL001' }],
          },
          {
            section_id: 'relations',
            blocks: [{ text: '天干合化说明', layer: 'fact' }],
          },
          {
            section_id: 'domains',
            blocks: [{ text: '事业域推断', layer: 'inference' }],
          },
        ],
      },
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const vol2 = doc.volumes.find((v) => v.id === 'vol2')
    const vol5 = doc.volumes.find((v) => v.id === 'vol5')
    expect(vol1?.sections.some((s) => s.id === 'geju-explain')).toBe(true)
    expect(vol1?.sections.find((s) => s.id === 'geju-explain')?.blocks[0].classic_id).toBe('CL001')
    expect(vol2?.sections.some((s) => s.id === 'relations-explain')).toBe(true)
    expect(vol5?.sections.some((s) => s.id === 'domains-explain')).toBe(true)
    expect(vol5?.sections.every((s) => s.collapsed_default)).toBe(true)
    expect(doc.disclaimer_block.text).toBe('仅供文化研究')
  })

  it('formats vol3 dayun ages without decimal noise and thickens palace vol4 blocks', () => {
    const bazi = {
      ...minimalBazi,
      dayun: {
        items: [{
          stem: '丙',
          branch: '子',
          start_age: 10.0,
          start_year: 2000,
          ten_god: '正官',
          narrative: '官星当令，宜在稳定结构中积累资历，避免冒进扩张。',
        }],
      },
    } as BaziResponse
    const ziwei = {
      wuxing_ju_name: '水二局',
      life_palace_gz: '甲子',
      body_palace_gz: '丙寅',
      patterns: [{ name: '紫府同宫', level: '上格', description: '主贵气与统御力并存，宜在组织内承担协调职责。' }],
      palaces: [{
        index: 0,
        name: '命宫',
        stem: '甲',
        branch: '子',
        main_stars: [{ name: '廉贞' }],
        aux_stars: [{ name: '文昌' }],
        analysis_tags: ['杀破狼'],
        analysis: '古称杀星与囚星同宫，主开创与变革。',
        conclusion: '',
        explanation: '',
        suggestion: '',
        tooltip: '',
        flying_out: {},
        xiaoxian_ages: [],
        opposition_name: '',
        dayun_boshi: [],
        changsheng: '',
        jiangqian_star: '',
        suiqian_star: '',
      }],
    } as unknown as ZiweiResponse

    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi,
      ziwei,
      explain: {
        chart_hash: 'hash-1',
        sections: [{
          section_id: 'palaces',
          blocks: [{ text: '命宫 子：廉贞、破军', layer: 'fact' }],
        }],
      },
    })

    const vol3 = doc.volumes.find((v) => v.id === 'vol3')
    const dayunText = vol3?.sections.find((s) => s.id === 'dayun')?.blocks[0]?.text ?? ''
    expect(dayunText).toContain('10–19岁')
    expect(dayunText).not.toMatch(/\d\.\d岁/)

    const vol4 = doc.volumes.find((v) => v.id === 'vol4')
    const palaceText = vol4?.sections.find((s) => s.id === 'palaces-explain')?.blocks[0]?.text ?? ''
    expect(palaceText.length).toBeGreaterThan(40)
    expect(vol4?.sections.some((s) => s.id === 'patterns')).toBe(true)
  })
})
