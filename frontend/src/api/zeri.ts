import apiClient from './client'

export interface ZeriDayResponse {
  day: number
  ganzhi: string
  score: number
  level: string
  reason: string
}

export interface ZeriMonthResponse {
  year: number
  month: number
  purpose: string
  purpose_label: string
  life_palace_branch: string
  wuxing_ju_name: string
  days: ZeriDayResponse[]
  recommended: ZeriDayResponse[]
}

export async function getZeriPurposes(): Promise<Record<string, string>> {
  const { data } = await apiClient.get<{ purposes: Record<string, string> }>('/api/v1/zeri/purposes')
  return data.purposes ?? {}
}

export async function getZeriRecommend(params: {
  year: number
  month: number
  life_palace_branch: string
  wuxing_ju_name: string
  natal_year_branch?: string
  purpose?: string
}): Promise<ZeriMonthResponse> {
  const { data } = await apiClient.get<ZeriMonthResponse>('/api/v1/zeri/recommend', { params })
  return data
}
