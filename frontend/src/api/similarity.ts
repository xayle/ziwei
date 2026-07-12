import apiClient from './client'

export interface SimilarityIndexRequest {
  chart_hash: string
  birth_year: number
  birth_month: number
  birth_day: number
  birth_hour: number
  gender: string
  wuxing_ju_name?: string
  life_palace_gz?: string
  pattern_summary?: string
  source_label?: string
}

export interface SimilarityCaseResponse {
  id: string
  chart_hash: string
}

export interface SimilarResult {
  case_id: string
  chart_hash: string
  score: number
  wuxing_ju_name?: string
  life_palace_gz?: string
  pattern_summary?: string
}

export interface SimilaritySearchResponse {
  items: SimilarResult[]
  total: number
}

export async function indexChart(payload: SimilarityIndexRequest): Promise<SimilarityCaseResponse> {
  const { data } = await apiClient.post<SimilarityCaseResponse>('/api/v1/similarity/index', payload)
  return data
}

export async function searchSimilar(chartHash: string, topK = 5): Promise<SimilarResult[]> {
  const { data } = await apiClient.get<SimilaritySearchResponse>('/api/v1/similarity/search', {
    params: { chart_hash: chartHash, top_k: topK },
  })
  return data.items ?? []
}
