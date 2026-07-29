/** 用神 verified 摘句（对齐 BE engine_ref.yongshen_*，供 Adapter 同源）。 */
export type YongshenClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const YONGSHEN_CLASSIC_REFS: readonly YongshenClassicRef[] = [
  {
    id: 'engine_ref.yongshen_001',
    source: '《子平真诠·论用神》',
    text: '用神者，命中最需之物也。命局缺之必用，有之必护，逢生则旺，逢克则衰。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.yongshen_008',
    source: '《三命通会》',
    text: '月令为命局之根基，用神从月令取，方为正道。月令旺相，则用神得令有力，命局安稳。',
    hint_type: 'verified',
  },
] as const
