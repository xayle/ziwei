import apiClient from './client'
import type { CityModel } from './openapiTypes'

export type CityRecord = CityModel

export async function getCities(params?: { q?: string; city_type?: string }): Promise<CityRecord[]> {
  const { data } = await apiClient.get<CityRecord[]>('/api/v1/cities', { params })
  return data
}
