import { describe, expect, it } from 'vitest'
import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import {
  buildBaziStructuralLines,
  buildDualTrackRows,
  buildIztroDisplay,
  buildLiuriSummary,
  buildPalaceStructuredRows,
  buildPillarDetailRows,
  buildProvenanceRows,
  buildValidationLines,
  collectMissingFields,
  formatMissingFieldLabel,
  formatMissingFieldLine,
  formatRelationLines,
  formatTrustValidationLine,
  buildTrustOverviewLines,
  trustLineTone,
} from '@/utils/buildEngineTrustDisplay'

describe('buildEngineTrustDisplay', () => {
  it('collects and deduplicates missing_fields', () => {
    const bazi = {
      missing_fields: ['geju_detail', 'geju_detail'],
      liuri_liushi: { missing_fields: ['flow_score'], day_ganzhi: '甲子' },
    } as BaziResponse
    const ziwei = { missing_fields: ['forecast'] } as ZiweiResponse
    const result = collectMissingFields(bazi, ziwei)
    expect(result.bazi).toEqual(['geju_detail', 'flow_score'])
    expect(result.ziwei).toEqual(['forecast'])
    expect(result.merged).toEqual(['geju_detail', 'flow_score', 'forecast'])
  })

  it('builds provenance rows from bazi and ziwei', () => {
    const rows = buildProvenanceRows(
      { geju: { layer: 'classical', confidence: 0.9, note: 'ZIP09' } },
      { stars: { layer: 'engine', confidence: 0.95 } },
    )
    expect(rows).toHaveLength(2)
    expect(rows[0].domain).toBe('八字·格局')
    expect(rows[0].layer).toBe('典籍')
    expect(rows[1].domain).toBe('紫微·安星')
  })

  it('builds dual-track rows when geju has recorded vs engine', () => {
    const rows = buildDualTrackRows({
      geju: {
        recorded_geju: '正官格',
        engine_geju: '七杀格',
        dual_track_id: 'ZIP09',
        dual_track_note: '典籍与引擎口径不同',
      },
    } as BaziResponse)
    expect(rows).toHaveLength(1)
    expect(rows[0]).toMatchObject({
      id: 'ZIP09',
      recorded: '正官格',
      engine: '七杀格',
      note: '典籍与引擎口径不同',
    })
  })

  it('summarizes liuri_liushi', () => {
    const summary = buildLiuriSummary({
      date: '2026-07-11',
      day_ganzhi: '甲子',
      day_ten_god: '比肩',
      hour_ganzhi: '丙寅',
      hour_label: '寅时',
      flow_summary: '平稳',
      current_dayun_ganzhi: '乙丑',
      flow_score: 72,
    })
    expect(summary?.day).toBe('甲子（比肩）')
    expect(summary?.hour).toContain('丙寅')
    expect(summary?.links).toContain('大运 乙丑')
    expect(summary?.score).toBe('72')
  })

  it('formats pillar details and relations', () => {
    const bazi = {
      pillar_details: {
        day: {
          kongwang: ['戌', '亥'],
          shensha: [{ name: '天乙' }],
          hidden_stems: [{ stem: '癸', ten_god: '偏印' }],
        },
      },
      dizhi_relations: [{ type: '六合', branches: '子丑' }],
      tiangan_clashes: [{ stems: '甲庚', note: '冲' }],
      shensha: [{ name: '华盖' }],
    } as BaziResponse
    const pillars = buildPillarDetailRows(bazi)
    expect(pillars).toHaveLength(1)
    expect(pillars[0].pillar).toBe('日')
    const relations = formatRelationLines(bazi)
    expect(relations[0]).toContain('六合')
    expect(relations.some((line) => line.includes('华盖'))).toBe(true)
  })

  it('returns empty relations when bazi has no structural data', () => {
    expect(formatRelationLines({} as BaziResponse)).toEqual([])
    expect(formatRelationLines(null)).toEqual([])
  })

  it('prefers analysis_structured for palace rows', () => {
    const rows = buildPalaceStructuredRows({
      analysis_structured: [{
        palace_index: 0,
        palace_name: '命宫',
        conclusion: '主贵',
        explanation: '紫微坐命',
        suggestion: '宜进取',
        tooltip: '',
        analysis_tags: ['贵'],
        is_empty_palace: false,
      }],
      palaces: [{ name: '命宫', conclusion: 'fallback' }],
    } as ZiweiResponse)
    expect(rows[0].conclusion).toBe('主贵')
    expect(rows[0].tags).toEqual(['贵'])
  })

  it('flattens bazi structural summary', () => {
    const lines = buildBaziStructuralLines({
      bazi_structural_summary: {
        core_snapshot: { day_master: '甲' },
        relation_summary: { clashes: 1 },
      },
    } as BaziResponse)
    expect(lines.some((line) => line.includes('日主'))).toBe(true)
    expect(lines.some((line) => line.includes('day_master'))).toBe(false)
  })

  it('builds validation and iztro display rows', () => {
    const validation = buildValidationLines({
      confidence_level: 'medium',
      confidence_score: 72,
      validation: {
        level: 'L2',
        mode: 'dual',
        interpretation_enabled: true,
        reasons: ['near_shichen_boundary'],
        diff_fields: ['hour'],
      },
    } as BaziResponse)
    expect(validation.some((line) => line.includes('置信度'))).toBe(true)
    expect(validation.some((line) => line.includes('中等'))).toBe(true)
    expect(validation.some((line) => line.includes('双轨'))).toBe(true)
    expect(validation.some((line) => line.includes('接近时辰交界'))).toBe(true)
    expect(validation.some((line) => line.includes('L2'))).toBe(true)

    const iztro = buildIztroDisplay({
      iztro_crosscheck: {
        status: 'life_palace_mismatch',
        main_match: 0,
        main_total: 14,
        life_palace_match: false,
        engine_life_palace_gz: '乙丑',
        iztro_life_palace_gz: '癸丑',
        advisory: 'ZW03 双轨边界',
        dual_track: {
          label: 'iztro 对照轨',
          year_divide: 'normal',
          day_divide: 'forward',
          life_palace_gz: '癸丑',
          main_match: 0,
          main_total: 14,
          note: '不覆盖引擎主盘',
        },
      },
    } as ZiweiResponse, { yearDivide: 'lichun', dayDivide: 'solar_next' })
    expect(iztro?.status).toBe('life_palace_mismatch')
    expect(iztro?.statusLabel).toBe('命宫不一致')
    expect(iztro?.showDualTrackTable).toBe(true)
    expect(iztro?.dualTrack?.lifePalaceGz).toBe('癸丑')
    expect(iztro?.engineLifePalaceGz).toBe('乙丑')
    expect(iztro?.dualTrack?.yearDivide).toBe('正月初一换年')
    expect(iztro?.dualTrack?.dayDivide).toBe('农历日+1安星')
    expect(iztro?.engineTrack?.dayDivide).toBe('公历次日换日')
  })

  it('formats missing field labels for register rows', () => {
    expect(formatMissingFieldLabel('clash_summary')).toBe('刑冲摘要')
    expect(formatMissingFieldLabel('hour_pillar')).toBe('时柱')
  })

  it('classifies trust line tone for register rows', () => {
    expect(trustLineTone('缺失字段未覆盖')).toBe('missing')
    expect(trustLineTone('近时辰边界 15分钟')).toBe('drift')
    expect(trustLineTone('置信度: medium')).toBe('ok')
  })

  it('humanizes trust validation and missing lines', () => {
    expect(formatMissingFieldLine('clash_summary').main).toBe('刑冲摘要（引擎未返回）')
    expect(formatMissingFieldLine('clash_summary').note).toBeUndefined()
    expect(formatMissingFieldLine('clash_summary').tone).toBe('missing')
    const advisory = formatMissingFieldLine('youbi_month_vs_iztro_hour')
    expect(advisory.main).toContain('右弼')
    expect(advisory.main).toContain('非故障')
    expect(advisory.tone).toBe('drift')
    expect(advisory.note).toBeTruthy()
    expect(formatMissingFieldLabel('palace_ten_gods')).toBe('宫位十神')
    expect(formatTrustValidationLine('近时辰边界（15 分钟）').main).toContain('时辰交界')
    expect(formatTrustValidationLine('置信度：medium').main).toBe('整体置信度：中等')
    expect(formatTrustValidationLine('置信度：中等').main).toBe('整体置信度：中等')
  })

  it('builds overview preview with max two lines', () => {
    const lines = buildTrustOverviewLines(
      ['clash_summary', 'hour_pillar'],
      ['置信度：medium', '近时辰边界（15 分钟）'],
      { max: 2 },
    )
    expect(lines).toHaveLength(2)
    expect(lines[0].main).toContain('刑冲摘要')
  })
})
