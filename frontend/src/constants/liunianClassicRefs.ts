/** 流年 verified 摘句（对齐 BE engine_ref.liunian_*，供 Adapter 同源）。 */
export type LiunianClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const LIUNIAN_CLASSIC_REFS: readonly LiunianClassicRef[] = [
  {
    id: 'engine_ref.liunian_e02',
    source: '《渊海子平》',
    text: '值太岁者，岁君临命，宜守不宜动；冲太岁者，岁冲命，宜防意外变故与人际纠纷。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.liunian_e04',
    source: '《滴天髓》',
    text: '大运流年相互激荡，流年之凶须大运配合而发，大运之吉亦借流年之助而更旺。',
    hint_type: 'verified',
  },
] as const
