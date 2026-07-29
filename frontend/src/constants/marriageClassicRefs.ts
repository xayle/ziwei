/** 婚姻 verified 摘句（对齐 BE engine_ref.marriage_*，供 Adapter 同源）。 */
export type MarriageClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const MARRIAGE_CLASSIC_REFS: readonly MarriageClassicRef[] = [
  {
    id: 'engine_ref.marriage_003',
    source: '《渊海子平》',
    text: '婚姻宫（日支）安稳，则夫妻关系和谐；日支受冲，婚姻稳定性弱，需双方加强沟通经营。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.marriage_ext03',
    source: '《渊海子平》',
    text: '日支为配偶宫，日支三刑六冲，配偶宫不稳；日支三合六合，配偶宫和谐有助力。',
    hint_type: 'verified',
  },
] as const
