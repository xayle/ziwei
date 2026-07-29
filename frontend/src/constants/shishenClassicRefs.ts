/** 十神 verified 摘句（对齐 BE engine_ref.shishen_*）。 */
export type ShishenClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const SHISHEN_CLASSIC_REFS: readonly ShishenClassicRef[] = [
  {
    id: 'engine_ref.shishen_004',
    source: '《三命通会》',
    text: '伤官见官为祸百端；若官星入墓或力弱，伤官有时反主高尚清贵之命格。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.shishen_006',
    source: '《三命通会》',
    text: '正财为妻财之象，务实稳健；偏财为父亲与意外之财之象，财来财往，善缘广结。',
    hint_type: 'verified',
  },
] as const
