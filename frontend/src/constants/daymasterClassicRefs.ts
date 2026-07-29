/** 日主 verified 摘句（对齐 BE engine_ref.daymaster_*，供 Adapter 同源）。 */
export type DaymasterClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const DAYMASTER_CLASSIC_REFS: readonly DaymasterClassicRef[] = [
  {
    id: 'engine_ref.daymaster_001',
    source: '《子平真诠·论日主》',
    text: '日主为命之主宰，强弱须以月令旺相休囚死论，得令则旺，失令则弱，余柱参论。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.daymaster_002',
    source: '《滴天髓》',
    text: '日主旺则能承财官，弱则宜印比相助。命局之美丑，皆以日主能否承受为首要判断。',
    hint_type: 'verified',
  },
] as const
