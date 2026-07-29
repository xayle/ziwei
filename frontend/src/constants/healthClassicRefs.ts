/** 健康 verified 摘句（对齐 BE engine_ref.health_*，供 Adapter 同源）。 */
export type HealthClassicRef = {
  id: string
  source: string
  text: string
  hint_type: 'verified'
}

export const HEALTH_CLASSIC_REFS: readonly HealthClassicRef[] = [
  {
    id: 'engine_ref.health_002',
    source: '《三命通会》',
    text: '火旺者，心血管与血压需要关注；水旺者，肾与泌尿系统需保养；金旺者，肺部呼吸道注意防护。',
    hint_type: 'verified',
  },
  {
    id: 'engine_ref.health_005',
    source: '《三命通会》',
    text: '印星旺则智慧高而体质偏弱，宜注重精神压力管理，防止过度用脑导致神经衰弱。',
    hint_type: 'verified',
  },
] as const
