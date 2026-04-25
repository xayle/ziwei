// frontend/src/api/compat.ts — 四柱合婚 (§5.1)
import apiClient from './client'

export interface CompatDetail {
  dimension:   string
  score:       number
  max:         number
  description: string
  level:       string
}

export interface PillarInfo {
  stem:   string
  branch: string
}

export interface PersonSummary {
  pillars:  Record<string, PillarInfo>
  weights:  Record<string, number>
  day_stem: string
  day_elem: string
}

export interface CompatResponse {
  score:    number
  grade:    string      // 上上 / 上 / 中 / 下 / 下下
  summary:  string
  details:  CompatDetail[]
  person_a: PersonSummary
  person_b: PersonSummary
}

export interface CompatParams {
  a_dt:  string
  a_tz:  string
  a_lon: number
  b_dt:  string
  b_tz:  string
  b_lon: number
}

export async function getBaziCompat(params: CompatParams): Promise<CompatResponse> {
  const { data } = await apiClient.get<CompatResponse>('/api/v1/compat/bazi', {
    params: {
      a_dt:  params.a_dt,
      a_tz:  params.a_tz,
      a_lon: params.a_lon,
      b_dt:  params.b_dt,
      b_tz:  params.b_tz,
      b_lon: params.b_lon,
    }
  })
  return data
}
