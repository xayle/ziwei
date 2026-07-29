/** 五行 verified 摘句（对齐 BE engine_ref.wuxing_*）。 */
export type WuxingClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const WUXING_CLASSIC_REFS: readonly WuxingClassicRef[] = [
  {
    id: 'engine_ref.wuxing_004',
    source: '《三命通会》',
    text: '五行过旺，须其所克之行制之；五行过衰，须其所生之行扶之。调候之法，在于平衡中和。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.wuxing_008',
    source: '《滴天髓》',
    text: '五行流通则命局活跃，五行淤滞则命局凝固。循环有情，一气流通，为命局有力之象。',
    hint_type: 'verified',
  },
] as const
