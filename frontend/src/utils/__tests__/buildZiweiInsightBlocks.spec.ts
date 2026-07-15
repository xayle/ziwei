import { describe, expect, it } from 'vitest'
import {
  buildPatternAnalysisBlocks,
  buildZiweiInsightBlocks,
  patternLayerForRule,
} from '@/utils/buildZiweiInsightBlocks'

const sampleZiwei = {
  patterns: [
    { name: '紫府同宫', rule_id: 'ZRULE_005', level: '吉', description: '典籍格局。' },
    { name: '启发式余格', rule_id: 'ZRULE_099', level: '平', description: '扩展格局。' },
  ],
  forecast: {
    year: 2026,
    yearly: { score: 75, overall: '平', advice: '稳扎稳打。', palace_name: '财帛' },
    monthly: [{ period: '1月', ganzhi: '丙寅', score: 70, overall: '吉' }],
    current_month: { period: '7月', ganzhi: '辛未', score: 80, advice: '宜规划。', overall: '吉' },
  },
  remedies: [{ name: '补水', cost_level: '低', actions: ['多饮水'] }],
  life_suggestions: [{
    category: 'career',
    category_label: '事业',
    name: '稳中求进',
    actions: ['专注主业'],
  }],
}

describe('buildZiweiInsightBlocks', () => {
  it('maps classical vs heuristic pattern tiers', () => {
    expect(patternLayerForRule('ZRULE_005')).toBe('classical')
    expect(patternLayerForRule('ZRULE_099')).toBe('heuristic')
    const blocks = buildPatternAnalysisBlocks(sampleZiwei.patterns as never)
    expect(blocks[0].layer).toBe('classical')
    expect(blocks[0].lead).toBe('吉')
    expect(blocks[0].chips).not.toContain('ZRULE_005')
    expect(blocks[0].chips).toContain('紫府同宫')
    expect(blocks[1].layer).toBe('heuristic')
  })

  it('maps forecast, remedies and life_suggestions', () => {
    const blocks = buildZiweiInsightBlocks(sampleZiwei as never)
    expect(blocks.some((b) => b.title.includes('2026 年运势'))).toBe(true)
    expect(blocks.some((b) => b.title === '化劫建议')).toBe(true)
    expect(blocks.some((b) => b.title === '生活建议')).toBe(true)
  })

  it('returns empty array without ziwei', () => {
    expect(buildZiweiInsightBlocks(null)).toEqual([])
  })
})
