import { describe, expect, it } from 'vitest'
import { buildRelationCompat, cardToneClass, dimensionPct } from './buildRelationCompat'
import type { RelationFullResponse } from '@/api/relation'

const mockRaw: RelationFullResponse = {
  schema_version: 'relation-compat@1.0',
  relation_type: 'couple',
  relation_type_label: '情侣合盘',
  person_a: { label: '甲', gender: 'male', birth_solar: '1990-01-01', pillars_primary: {} },
  person_b: { label: '乙', gender: 'female', birth_solar: '1990-02-01', pillars_primary: {} },
  combined_score: 59.5,
  grade: '中',
  summary: '测试摘要',
  summary_cards: [{ id: 'c1', tone: 'conflict', text: '日支六冲' }],
  layers: {},
  dimensions: [{ id: 'day_branch', label: '日支', score: 0, max_score: 30, weight: 0.2, description: '丑未冲', layer: 'fact' }],
  palace_cross: [],
  timeline: [{ year: 2026, label: '2026', summary: '值太岁' }],
  action_items: [{ id: 'a1', text: '多沟通' }],
  tensions: [],
  missing_fields: [],
  disclaimer_block: { text: '免责声明', version: '1', jurisdiction: 'CN' },
}

describe('buildRelationCompat', () => {
  it('maps API response to display model', () => {
    const d = buildRelationCompat(mockRaw)
    expect(d.title).toBe('情侣合盘')
    expect(d.subtitle).toBe('甲 × 乙')
    expect(d.combinedScore).toBe(59.5)
    expect(d.summaryCards).toHaveLength(1)
  })

  it('dimensionPct calculates ratio', () => {
    expect(dimensionPct({ id: 'x', label: 'x', score: 15, max_score: 30, weight: 1, description: '', layer: 'fact' })).toBe(50)
  })

  it('cardToneClass returns css class', () => {
    expect(cardToneClass('conflict')).toBe('tone-conflict')
  })
})
