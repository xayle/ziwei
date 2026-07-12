import apiClient from './client'

export interface CityRecord {
  name: string
  province: string
  lng: number
  lat: number
  city_type: string
}

export async function getCities(params?: { q?: string; city_type?: string }): Promise<CityRecord[]> {
  const { data } = await apiClient.get<CityRecord[]>('/api/v1/cities', { params })
  return data
}
