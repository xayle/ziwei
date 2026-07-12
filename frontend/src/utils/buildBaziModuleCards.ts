import type { BaziResponse } from '@/api/bazi'
import type { AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'
import type { ContentLayer } from '@/types/life-volume'
import { truncateText } from '@/utils/truncateText'

export type BaziModuleCard = {
  title: string
  lead: string
  body: string
  chips: string[]
  layer: ContentLayer
}

const DOMAIN_TITLES = ['性格', '事业', '财运', '婚恋', '健康', '人际'] as const

export function buildBaziModuleCards(bazi: BaziResponse | null | undefined): BaziModuleCard[] {
  if (!bazi) return []

  const personality = bazi.personality
  const career = bazi.career
  const wealth = bazi.wealth_analysis
  const marriage = bazi.marriage_analysis
  const health = bazi.health
  const relationship = bazi.relationship

  return [
    {
      title: '性格',
      lead: personality?.day_stem_trait || '待计算',
      body: truncateText(personality?.growth_advice || personality?.interpretation_text || '暂无性格说明。'),
      chips: personality?.advantages ?? [],
      layer: 'inference',
    },
    {
      title: '事业',
      lead: career?.career_score !== undefined ? `${career.career_score} 分` : '待计算',
      body: truncateText(career?.development_advice || career?.interpretation_text || '暂无事业建议。'),
      chips: career?.career_directions ?? [],
      layer: 'inference',
    },
    {
      title: '财运',
      lead: wealth?.wealth_tier || '待计算',
      body: truncateText(wealth?.strategy || wealth?.interpretation_text || '暂无财运建议。'),
      chips: wealth?.industries ?? [],
      layer: 'inference',
    },
    {
      title: '婚恋',
      lead: marriage?.marriage_score !== undefined ? `${marriage.marriage_score} 分` : '待计算',
      body: truncateText(marriage?.interpretation_text || marriage?.partner_profile || '暂无婚恋提示。'),
      chips: marriage?.marriage_windows ?? [],
      layer: 'inference',
    },
    {
      title: '健康',
      lead: health?.risk_level || '待计算',
      body: truncateText(health?.health_advice || health?.interpretation_text || '暂无健康建议。'),
      chips: health?.risk_organs ?? [],
      layer: 'inference',
    },
    {
      title: '人际',
      lead: relationship?.relationship_score !== undefined ? `${relationship.relationship_score} 分` : '待计算',
      body: truncateText(relationship?.social_strategy || relationship?.interpretation_text || '暂无人际建议。'),
      chips: relationship?.noble_people ?? [],
      layer: 'inference',
    },
  ].filter((card) => DOMAIN_TITLES.includes(card.title as typeof DOMAIN_TITLES[number]))
}

export function baziModuleCardsToAnalysisBlocks(cards: BaziModuleCard[]): AnalysisBlock[] {
  return cards.map((card, index) => ({
    id: `bazi-module-${index}`,
    title: card.title,
    lead: card.lead,
    body: card.body,
    chips: card.chips,
    layer: 'heuristic' as const,
  }))
}
