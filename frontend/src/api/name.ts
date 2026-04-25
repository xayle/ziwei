import apiClient from './client'

// ── 请求类型 ───────────────────────────────────────────────────
export interface NameAnalyzeRequest {
  surname: string
  given_name: string
  birth_year?: number
}

export interface NameSuggestRequest {
  surname: string
  name_length?: 1 | 2
  preferred_elements?: string[]
  top_n?: number
  min_score?: number
}

// ── 响应类型 ───────────────────────────────────────────────────
export interface GridInfoResponse {
  number: number
  element: string
  lucky: string
  score: number
  desc: string
}

export interface SancaiInfoResponse {
  pattern: string
  lucky: string
  score: number
  desc: string
}

export interface NameAnalysisResponse {
  surname: string
  given_name: string
  tianke: GridInfoResponse
  renke: GridInfoResponse
  dike: GridInfoResponse
  waike: GridInfoResponse
  zonge: GridInfoResponse
  sancai: SancaiInfoResponse
  overall_score: number
  summary: string
  algorithm_version: string
}

export interface NameSuggestionItem {
  given_name: string
  overall_score: number
  renke_score: number
  sancai_score: number
  sancai_pattern: string
  element_composition: string[]
  summary: string
}

export interface NameSuggestResponse {
  surname: string
  name_length: number
  preferred_elements: string[] | null
  total_candidates_evaluated: number
  suggestions: NameSuggestionItem[]
  algorithm_version: string
}

// ── API 函数 ───────────────────────────────────────────────────
export async function analyzeName(data: NameAnalyzeRequest): Promise<NameAnalysisResponse> {
  const res = await apiClient.post<NameAnalysisResponse>('/api/v1/name/analyze', data)
  return res.data
}

export async function suggestNames(data: NameSuggestRequest): Promise<NameSuggestResponse> {
  const res = await apiClient.post<NameSuggestResponse>('/api/v1/name/suggest', data)
  return res.data
}
