/**
 * similarity.ts — 相似命盘检索 API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface SimilarityIndexRequest {
  chart_hash: string
  birth_solar?: string
  birth_year?: number
  birth_month?: number
  birth_day?: number
  birth_hour?: number
  gender?: string
  wuxing_ju_name?: string
  life_palace_gz?: string
  patterns?: Array<Record<string, unknown>>
  source_label?: string
}

export interface SimilarityCaseResponse {
  id: number
  chart_hash: string
  birth_solar: string
  birth_year: number
  birth_month: number
  birth_day: number
  birth_hour: number
  gender: string
  wuxing_ju_name: string
  life_palace_gz: string
  patterns: Array<Record<string, unknown>>
  source_label: string
  created_at: string
}

export interface SimilarResult {
  case: SimilarityCaseResponse
  similarity: number
}

export interface SearchResponse {
  query_hash: string
  total_indexed: number
  results: SimilarResult[]
}

export interface SimilarityCaseListResponse {
  total: number
  items: SimilarityCaseResponse[]
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/similarity/index — 索引命盘 */
export async function indexChart(req: SimilarityIndexRequest): Promise<SimilarityCaseResponse> {
  const { data } = await apiClient.post<SimilarityCaseResponse>('/api/v1/similarity/index', req)
  return data
}

/** GET /api/v1/similarity/search — 搜索相似命盘 */
export async function searchSimilar(params: {
  chart_hash: string
  life_palace_gz?: string
  wuxing_ju_name?: string
  gender?: string
  birth_year?: number
  patterns?: string            // JSON array, URL-encoded
  top_k?: number
}): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>('/api/v1/similarity/search', { params })
  return data
}

/** GET /api/v1/similarity/cases — 已索引命盘列表 */
export async function listSimilarityCases(params?: { skip?: number; limit?: number }): Promise<SimilarityCaseListResponse> {
  const { data } = await apiClient.get<SimilarityCaseListResponse>('/api/v1/similarity/cases', { params })
  return data
}

/** DELETE /api/v1/similarity/cases/:id — 删除已索引命盘 */
export async function deleteSimilarityCase(caseId: number): Promise<void> {
  await apiClient.delete(`/api/v1/similarity/cases/${caseId}`)
}
