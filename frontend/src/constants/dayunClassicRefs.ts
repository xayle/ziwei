/** 大运 verified 摘句（对齐 BE engine_ref.dayun_*，供 Adapter 同源）。 */
export type DayunClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const DAYUN_CLASSIC_REFS: readonly DayunClassicRef[] = [
  {
    id: 'engine_ref.dayun_001',
    source: '《子平真诠·论大运》',
    text: '大运者，主一时之运，论其得失进退，须看大运天干地支与日主之生克制化。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.dayun_006',
    source: '《子平真诠·论大运》',
    text: '用神在大运中得旺相，虽命局有瑕，亦能转危为安；用神入墓绝，则运行不济。',
    hint_type: 'verified',
  },
] as const
