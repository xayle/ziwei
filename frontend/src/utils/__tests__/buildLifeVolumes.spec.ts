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

  it('E-01: soft classic_ref is inference, not cite', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: {
        ...minimalBazi,
        geju: { geju_name: '正官格', classic_ref: '官清印顺，贵气有序。' },
      } as BaziResponse,
      ziwei: null,
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const heuristic = vol1?.sections.find((s) => s.id === 'geju-heuristic')
    expect(heuristic?.layer).toBe('inference')
    expect(heuristic?.blocks[0]?.layer).toBe('inference')
    expect(vol1?.sections.some((s) => s.id === 'geju-cite')).toBe(false)
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

  it('marks vol5 domain sections as inference/collapsed; cite sections allowed', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi: minimalBazi,
      ziwei: null,
    })
    const vol5 = doc.volumes.find((v) => v.id === 'vol5')
    expect(vol5?.sections.length).toBeGreaterThan(0)
    const domains = vol5?.sections.filter((s) => !s.id.endsWith('-cite')) ?? []
    const cites = vol5?.sections.filter((s) => s.id.endsWith('-cite')) ?? []
    expect(domains.every((s) => s.layer === 'inference')).toBe(true)
    expect(cites.every((s) => s.layer === 'cite')).toBe(true)
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

  it('puts monthly_fortune into vol3 (BZ-Month)', () => {
    const bazi = {
      ...minimalBazi,
      monthly_fortune: [
        {
          month: 3,
          lunar_month: 2,
          month_dizhi: '卯',
          luck_level: '吉',
          color_hint: '绿',
          tip: '宜推进合作与学习',
          month_ganzhi: '乙卯',
          disclaimer: '仅供学术研究参考',
        },
      ],
    } as BaziResponse

    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi,
      ziwei: null,
    })

    const vol3 = doc.volumes.find((v) => v.id === 'vol3')
    const monthly = vol3?.sections.find((s) => s.id === 'monthly-fortune')
    expect(monthly?.blocks[0]?.text).toContain('3月')
    expect(monthly?.blocks[0]?.text).toContain('吉')
    expect(monthly?.blocks[0]?.text).toContain('乙卯')
  })

  it('thickens preface reading-guide with Chinese layer labels', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-preface',
      chartHash: 'hash-preface',
      bazi: minimalBazi,
      ziwei: null,
    })
    const preface = doc.volumes.find((v) => v.id === 'preface')
    const guide = preface?.sections.find((s) => s.id === 'reading-guide')
    const joined = (guide?.blocks ?? []).map((b) => b.text).join('')
    expect(guide?.blocks.length).toBeGreaterThanOrEqual(2)
    expect(joined).toContain('排盘推算')
    expect(joined).toContain('典籍依据')
    expect(joined).toContain('经验推断')
    expect(joined.toLowerCase()).not.toContain('cite')
    expect(joined.toLowerCase()).not.toContain('inference')
  })

  it('thickens vol4 with mingshen / sanfang reading guide', () => {
    const ziwei = {
      wuxing_ju_name: '水二局',
      life_palace_gz: '甲子',
      body_palace_gz: '丙寅',
      patterns: [],
      palaces: [],
    } as unknown as ZiweiResponse
    const doc = buildLifeVolumes({
      caseId: 'case-vol4',
      chartHash: 'hash-vol4',
      bazi: minimalBazi,
      ziwei,
    })
    const vol4 = doc.volumes.find((v) => v.id === 'vol4')
    const ids = vol4?.sections.map((s) => s.id) ?? []
    expect(ids).toContain('ziwei-meta')
    expect(ids).toContain('ziwei-reading')
    const reading = vol4?.sections.find((s) => s.id === 'ziwei-reading')?.blocks[0]?.text ?? ''
    expect(reading).toContain('命身轴')
    expect(reading).toContain('三方')
    expect(reading.length).toBeGreaterThanOrEqual(90)
  })

  it('falls back to verified relations cite when explain has no cite', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-rel-verified',
      chartHash: 'hash-rel-verified',
      bazi: {
        ...minimalBazi,
        relations_summary: {
          clash_summary: '冲：子午',
          combine_summary: '',
          items: [],
        },
      } as BaziResponse,
      ziwei: null,
      unlock: { unlocked_volumes: ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] },
    })
    const vol2 = doc.volumes.find((v) => v.id === 'vol2')
    const cite = vol2?.sections.find((s) => s.id === 'relations-cite')
    expect(cite?.blocks?.[0]?.layer).toBe('cite')
    expect(cite?.blocks?.[0]?.classic_id).toBeTruthy()
    expect(cite?.blocks?.[0]?.text).toContain('典籍依据')
    expect(vol2?.sections.some((s) => s.id === 'vol2-cite-pending')).toBe(false)
  })

  it('mounts daymaster cite and vol5 marriage/health cites', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-dm-domain',
      chartHash: 'hash-dm-domain',
      bazi: {
        ...minimalBazi,
        day_master_strength: { tier: '中和', score: 50 },
      } as BaziResponse,
      ziwei: null,
      unlock: { unlocked_volumes: ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] },
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const vol5 = doc.volumes.find((v) => v.id === 'vol5')
    expect(vol1?.sections.find((s) => s.id === 'daymaster-cite')?.blocks?.[0]?.classic_id)
      .toMatch(/^engine_ref\.daymaster_/)
    expect(vol5?.sections.find((s) => s.id === 'marriage-cite')?.blocks?.[0]?.classic_id)
      .toMatch(/^engine_ref\.marriage_/)
    expect(vol5?.sections.find((s) => s.id === 'health-cite')?.blocks?.[0]?.classic_id)
      .toMatch(/^engine_ref\.health_/)
  })

  it('mounts dayun/liunian verified cites into vol3', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-vol3-cite',
      chartHash: 'hash-vol3-cite',
      bazi: {
        ...minimalBazi,
        dayun: {
          items: [
            { ganzhi: '甲子', start_age: 8, end_age: 17 },
            { ganzhi: '乙丑', start_age: 18, end_age: 27 },
          ],
        },
        liunian: {
          items: [
            { year: 2025, stem: '乙', branch: '巳' },
            { year: 2026, stem: '丙', branch: '午' },
          ],
        },
      } as BaziResponse,
      ziwei: null,
      unlock: { unlocked_volumes: ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] },
    })
    const vol3 = doc.volumes.find((v) => v.id === 'vol3')
    const dayunCite = vol3?.sections.find((s) => s.id === 'dayun-cite')
    const liunianCite = vol3?.sections.find((s) => s.id === 'liunian-cite')
    expect(dayunCite?.blocks?.[0]?.classic_id).toMatch(/^engine_ref\.dayun_/)
    expect(liunianCite?.blocks?.[0]?.classic_id).toMatch(/^engine_ref\.liunian_/)
    expect(dayunCite?.blocks?.[0]?.text).toContain('典籍依据')
  })

  it('mounts yongshen verified cites into vol1', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-yong-cite',
      chartHash: 'hash-yong-cite',
      bazi: {
        ...minimalBazi,
        yongshen: { favor: ['fire'], avoid: ['wood'] },
      } as BaziResponse,
      ziwei: null,
      unlock: { unlocked_volumes: ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] },
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const cite = vol1?.sections.find((s) => s.id === 'yongshen-cite')
    expect(cite?.blocks?.[0]?.layer).toBe('cite')
    expect(cite?.blocks?.[0]?.classic_id).toMatch(/^engine_ref\.yongshen_/)
    expect(cite?.blocks?.[0]?.text).toContain('典籍依据')
  })

  it('mounts verified shensha classic_refs into shensha-cite (E-01)', () => {
    const bazi = {
      ...minimalBazi,
      shensha_summary: {
        items: [{
          name: '驿马',
          is_beneficial: true,
          dizhi: '寅',
          pillar: 'day',
          meaning: '',
          classic_source: '三命通会',
          classic_refs: [{
            id: 'engine_ref.shensha_003',
            source: '《三命通会》',
            text: '驿马：申子辰马在寅，巳酉丑马在亥，寅午戌马在申，亥卯未马在巳。驿马主奔波远行。',
            hint_type: 'verified',
          }],
        }],
      },
    } as BaziResponse
    const doc = buildLifeVolumes({
      caseId: 'case-shensha-verified',
      chartHash: 'hash-shensha-verified',
      bazi,
      ziwei: null,
      unlock: { unlocked_volumes: ['vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6'] },
    })
    const vol2 = doc.volumes.find((v) => v.id === 'vol2')
    const cite = vol2?.sections.find((s) => s.id === 'shensha-cite')
    expect(cite?.blocks?.[0]?.layer).toBe('cite')
    expect(cite?.blocks?.[0]?.classic_id).toBe('engine_ref.shensha_003')
    expect(cite?.blocks?.[0]?.text).toContain('驿马')
  })

  it('mounts shensha classic_refs soft quotes into vol2 (E-01)', () => {
    const bazi = {
      ...minimalBazi,
      shensha_summary: {
        items: [{
          name: '天乙贵人',
          is_beneficial: true,
          dizhi: '子',
          pillar: 'day',
          meaning: '',
          classic_source: '三命通会',
          classic_refs: [{
            id: 'shensha_001',
            source: '三命通会·论神煞',
            text: '天乙贵人，命中有之，遇事有贵人扶助。',
            hint_type: 'soft',
          }],
        }],
      },
    } as BaziResponse
    const doc = buildLifeVolumes({
      caseId: 'case-shensha-cite',
      chartHash: 'hash-shensha-cite',
      bazi,
      ziwei: null,
    })
    const vol2 = doc.volumes.find((v) => v.id === 'vol2')
    const soft = vol2?.sections.find((s) => s.id === 'shensha-classic-soft')
    expect(soft?.layer).toBe('inference')
    expect(soft?.blocks[0]?.layer).toBe('inference')
    expect(soft?.blocks[0]?.text).toContain('贵人扶助')
    expect(soft?.blocks[0]?.classic_id).toBe('shensha_001')
    expect(vol2?.sections.some((s) => s.id === 'vol2-cite-pending')).toBe(false)
  })

  it('thickens vol2 with reading / polarity / cite pending (D2)', () => {
    const bazi = {
      ...minimalBazi,
      relations_summary: {
        interaction_summary: '拱合；丁[火]克庚[金]',
        clash_summary: '冲：子午',
        items: [],
      },
      shensha_summary: {
        items: [
          { name: '天乙', is_beneficial: true, dizhi: '子', pillar: 'day', meaning: '', classic_source: '' },
          { name: '羊刃', is_beneficial: false, dizhi: '卯', pillar: 'year', meaning: '', classic_source: '' },
        ],
      },
    } as BaziResponse
    const doc = buildLifeVolumes({
      caseId: 'case-vol2',
      chartHash: 'hash-vol2',
      bazi,
      ziwei: null,
    })
    const vol2 = doc.volumes.find((v) => v.id === 'vol2')
    const ids = vol2?.sections.map((s) => s.id) ?? []
    expect(ids).toContain('relations-reading')
    expect(ids).toContain('shensha-auspicious')
    expect(ids).toContain('shensha-caution')
    expect(ids).toContain('relations-classic-soft')
    expect(ids).not.toContain('vol2-cite-pending')
    const blocks = vol2?.sections.flatMap((s) => s.blocks) ?? []
    expect(blocks.length).toBeGreaterThanOrEqual(5)
    const avg = blocks.reduce((n, b) => n + b.text.length, 0) / blocks.length
    expect(avg).toBeGreaterThanOrEqual(90)
    expect(vol2?.sections.find((s) => s.id === 'relations-classic-soft')?.blocks[0]?.text).toContain('软提示')
    expect(vol2?.sections.find((s) => s.id === 'shensha-auspicious')?.blocks[0]?.text).toContain('天乙')
    expect(vol2?.sections.find((s) => s.id === 'shensha-caution')?.blocks[0]?.text).toContain('羊刃')
  })

  it('thickens vol6 with howto / bridge / access and no LLM leak (D3)', () => {
    const doc = buildLifeVolumes({
      caseId: 'case-vol6',
      chartHash: 'hash-vol6',
      bazi: minimalBazi,
      ziwei: null,
    })
    const vol6 = doc.volumes.find((v) => v.id === 'vol6')
    const ids = vol6?.sections.map((s) => s.id) ?? []
    expect(ids).toContain('vol6-how-to-ask')
    expect(ids).toContain('vol6-bridge')
    expect(ids).toContain('vol6-access')
    const blocks = vol6?.sections.flatMap((s) => s.blocks) ?? []
    expect(blocks.length).toBeGreaterThanOrEqual(3)
    const joined = blocks.map((b) => b.text).join('')
    expect(joined).not.toContain('LLM')
    expect(joined).toContain('事业')
    const avg = blocks.reduce((n, b) => n + b.text.length, 0) / blocks.length
    expect(avg).toBeGreaterThanOrEqual(90)
  })

  it('caps vol1 current-fortune and keeps geju/yongshen intact', () => {
    const longTip = '宜拓展收入渠道并注意合作边界，'.repeat(12)
    const bazi = {
      ...minimalBazi,
      geju: {
        geju_name: '正印格',
        geju_detail: '印旺生身，宜学业与文书。此句应完整保留不被运势摘要挤掉。',
      },
      yongshen: { favor: ['fire'], avoid: ['wood'] },
      current_fortune_summary: {
        current_dayun: '癸酉',
        current_liunian: '丙午',
        this_year_domains: { 财运: longTip, 事业: longTip, 健康: longTip },
        top3_actions: [longTip, longTip],
      },
    } as BaziResponse
    const doc = buildLifeVolumes({
      caseId: 'case-vol1-trunc',
      chartHash: 'hash-vol1-trunc',
      bazi,
      ziwei: null,
      explain: {
        chart_hash: 'hash-vol1-trunc',
        sections: [{
          section_id: 'geju',
          blocks: [{ text: `${'格局讲解长句其一。'.repeat(40)}尾`, layer: 'cite', classic_id: 'CL1' }],
        }],
      },
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const geju = vol1?.sections.find((s) => s.id === 'geju')?.blocks[0]?.text ?? ''
    const yong = vol1?.sections.find((s) => s.id === 'yongshen')?.blocks[0]?.text ?? ''
    const fortune = vol1?.sections.find((s) => s.id === 'current-fortune')?.blocks[0]?.text ?? ''
    const explain = vol1?.sections.find((s) => s.id === 'geju-explain')?.blocks[0]?.text ?? ''
    expect(geju).toContain('此句应完整保留')
    expect(yong).toContain('用神须与格局')
    expect(fortune.length).toBeLessThanOrEqual(360)
    expect(explain.length).toBeLessThanOrEqual(500)
    expect(explain).toContain('格局讲解长句其一。')
  })

  it('thickens vol1 pillars / strength (CNT-01)', () => {
    const bazi = {
      ...minimalBazi,
      pillars_primary: {
        year: { stem: '庚', branch: '午', ganzhi: '庚午' },
        month: { stem: '戊', branch: '寅', ganzhi: '戊寅' },
        day: { stem: '甲', branch: '子', ganzhi: '甲子' },
        hour: { stem: '丙', branch: '寅', ganzhi: '丙寅' },
      },
      day_master_strength: {
        score: 62,
        tier: '中和偏弱',
        factors: [{ name: '月令得分', score: 70, weight: 0.4, weighted_score: 28, reason: '月支旺相状态' }],
      },
      current_fortune_summary: {
        current_dayun: '己亥',
        dayun_years_remaining: 4,
        current_liunian: '丙午',
        this_year_domains: { 事业: '稳中求进' },
        top3_actions: ['守成', '复盘'],
      },
    } as BaziResponse

    const doc = buildLifeVolumes({
      caseId: 'case-1',
      chartHash: 'hash-1',
      bazi,
      ziwei: null,
    })
    const vol1 = doc.volumes.find((v) => v.id === 'vol1')
    const pillars = vol1?.sections.find((s) => s.id === 'pillars')?.blocks[0]?.text ?? ''
    const strength = vol1?.sections.find((s) => s.id === 'strength')?.blocks[0]?.text ?? ''
    const fortune = vol1?.sections.find((s) => s.id === 'current-fortune')?.blocks[0]?.text ?? ''
    expect(pillars).toContain('年柱 庚午')
    expect(pillars).toContain('日柱 甲子')
    expect(pillars.length).toBeGreaterThanOrEqual(40)
    expect(strength).toContain('月令得分')
    expect(fortune).toContain('事业')
    expect(vol1?.sections.some((s) => s.id === 'strength')).toBe(true)
    expect(vol1?.sections.some((s) => s.id === 'current-fortune')).toBe(true)
  })
})
