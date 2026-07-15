import type { ExplainSectionResult } from '@/api/explain'
import type { AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'
import type { ContentLayer } from '@/types/life-volume'

const SECTION_TITLES: Record<string, string> = {
  geju: '格局解读',
  relations: '干支关系解读',
  reading: '读法导引',
  domains: '生活域推断',
  summary: '综合摘要',
  palaces: '宫图与星曜要点',
  fortune: '运限要点',
}

function toAnalysisLayer(layer: ContentLayer): AnalysisBlock['layer'] {
  if (layer === 'cite') return 'classical'
  if (layer === 'inference') return 'heuristic'
  return 'engine'
}

export function explainSectionToAnalysisBlock(section: ExplainSectionResult): AnalysisBlock | null {
  const texts = section.blocks.map((b) => b.text.trim()).filter(Boolean)
  if (!texts.length) return null
  const primaryLayer = section.blocks[0]?.layer ?? 'cite'
  return {
    id: `explain-${section.section_id}`,
    title: SECTION_TITLES[section.section_id] ?? section.section_id,
    lead: section.verified ? '典籍校勘' : '解读',
    body: texts.join('\n\n'),
    bullets: section.blocks
      .filter((b) => b.classic_id)
      .map(() => '出处：典籍依据'),
    layer: toAnalysisLayer(primaryLayer),
  }
}

export function explainSectionsToAnalysisBlocks(sections: ExplainSectionResult[]): AnalysisBlock[] {
  return sections
    .map(explainSectionToAnalysisBlock)
    .filter((block): block is AnalysisBlock => block != null)
}
