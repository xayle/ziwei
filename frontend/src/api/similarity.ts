import apiClient from './client'
import type {
  SimilarityCaseResponse,
  SimilarityIndexRequest,
  SimilaritySearchResponse,
  SimilarResult,
} from './openapiTypes'

export type { SimilarityCaseResponse, SimilarityIndexRequest, SimilarResult, SimilaritySearchResponse }

export async function indexChart(payload: SimilarityIndexRequest): Promise<SimilarityCaseResponse> {
  const { data } = await apiClient.post<SimilarityCaseResponse>('/api/v1/similarity/index', payload)
  return data
}

export async function searchSimilar(chartHash: string, topK = 5): Promise<SimilarResult[]> {
  const { data } = await apiClient.get<SimilaritySearchResponse>('/api/v1/similarity/search', {
    params: { chart_hash: chartHash, top_k: topK },
  })
  return data.results ?? []
}
