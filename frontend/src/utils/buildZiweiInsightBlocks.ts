import type { PatternResponse, ZiweiResponse } from '@/api/ziwei'
import type { AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'

/** Top-20 canonical ZRULE patterns (services/ziwei_engine/patterns.py _PATTERN_RULE_IDS subset). */
export const CLASSICAL_ZRULE_IDS = new Set([
  'ZRULE_001', 'ZRULE_002', 'ZRULE_003', 'ZRULE_004', 'ZRULE_005',
  'ZRULE_006', 'ZRULE_007', 'ZRULE_008', 'ZRULE_009', 'ZRULE_010',
  'ZRULE_011', 'ZRULE_012', 'ZRULE_013', 'ZRULE_014', 'ZRULE_015',
  'ZRULE_039', 'ZRULE_040', 'ZRULE_041', 'ZRULE_042', 'ZRULE_043',
])

export function patternLayerForRule(ruleId?: string | null): 'classical' | 'heuristic' {
  if (ruleId && CLASSICAL_ZRULE_IDS.has(ruleId)) return 'classical'
  return 'heuristic'
}

export function buildPatternAnalysisBlocks(
  patterns: PatternResponse[] | null | undefined,
  limit = 6,
): AnalysisBlock[] {
  if (!patterns?.length) return []
  return patterns.slice(0, limit).map((pattern, idx) => {
    const ruleId = pattern.rule_id || undefined
    return {
      id: `ziwei-pattern-${idx}`,
      title: pattern.name,
      lead: ruleId ? `${ruleId} · ${pattern.level || '格局'}` : (pattern.level || '格局'),
      body: pattern.description || '暂无格局说明。',
      chips: [ruleId, pattern.name].filter((chip): chip is string => Boolean(chip)),
      layer: patternLayerForRule(ruleId),
    }
  })
}

export function buildZiweiInsightBlocks(ziwei: ZiweiResponse | null | undefined): AnalysisBlock[] {
  if (!ziwei) return []

  const blocks: AnalysisBlock[] = []
  const forecast = ziwei.forecast

  if (forecast) {
    const yearly = forecast.yearly
    blocks.push({
      id: 'ziwei-forecast-year',
      title: `${forecast.year} 年运势`,
      lead: yearly ? `综合 ${yearly.score} 分 · ${yearly.overall || '—'}` : '年度运势',
      body: yearly?.advice || yearly?.palace_name || '暂无年度建议。',
      bullets: (forecast.monthly ?? []).slice(0, 4).map(
        (m) => `${m.period || m.ganzhi} ${m.score}分 · ${m.overall || ''}`.trim(),
      ),
      layer: 'heuristic',
    })
    const current = forecast.current_month
    if (current) {
      blocks.push({
        id: 'ziwei-forecast-month',
        title: '当月运势',
        lead: `${current.period || current.ganzhi} · ${current.score} 分`,
        body: current.advice || current.overall || '暂无当月建议。',
        layer: 'heuristic',
      })
    }
  }

  if (ziwei.remedies?.length) {
    blocks.push({
      id: 'ziwei-remedies',
      title: '化劫建议',
      lead: `共 ${ziwei.remedies.length} 条`,
      body: ziwei.remedies.slice(0, 3).map((r) => {
        const actions = r.actions?.length ? r.actions.join('；') : r.evidence
        return `${r.name}（${r.cost_level}）：${actions}`
      }).join('\n'),
      bullets: ziwei.remedies.map((r) => r.name),
      layer: 'engine',
    })
  }

  if (ziwei.life_suggestions?.length) {
    blocks.push({
      id: 'ziwei-life-suggestions',
      title: '生活建议',
      lead: ziwei.life_suggestions[0]?.category_label || '分类建议',
      body: ziwei.life_suggestions.slice(0, 4).map((s) => {
        const actions = s.actions?.length ? s.actions.join('；') : s.short_desc
        return `${s.category_label || s.category} · ${s.name}：${actions}`
      }).join('\n'),
      bullets: ziwei.life_suggestions.map((s) => s.name),
      layer: 'heuristic',
    })
  }

  return blocks
}
