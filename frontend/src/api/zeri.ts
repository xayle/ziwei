import apiClient from './client'
import type { ZeriDayResponse, ZeriMonthResponse } from './openapiTypes'

export type { ZeriDayResponse, ZeriMonthResponse }

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
