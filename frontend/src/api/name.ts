import apiClient from './client'

export interface GridInfo {
  number: number
  element: string
  lucky: string
  score: number
  desc: string
}

export interface SancaiInfo {
  pattern: string
  lucky: string
  score: number
  desc: string
}

export interface NameAnalysisResponse {
  surname: string
  given_name: string
  tianke: GridInfo
  renke: GridInfo
  dike: GridInfo
  waike: GridInfo
  zonge: GridInfo
  sancai: SancaiInfo
  overall_score: number
  summary: string
  algorithm_version: string
}

export interface NameRequest {
  surname: string
  given_name: string
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

export interface NameSuggestRequest {
  surname: string
  name_length?: number
  preferred_elements?: string[]
  top_n?: number
  min_score?: number
}

export interface NameSuggestResponse {
  surname: string
  name_length: number
  preferred_elements: string[] | null
  total_candidates_evaluated: number
  suggestions: NameSuggestionItem[]
  algorithm_version: string
}

export async function analyzeName(payload: NameRequest): Promise<NameAnalysisResponse> {
  const { data } = await apiClient.post<NameAnalysisResponse>('/api/v1/name/analyze', payload)
  return data
}

export async function suggestNames(payload: NameSuggestRequest): Promise<NameSuggestResponse> {
  const { data } = await apiClient.post<NameSuggestResponse>('/api/v1/name/suggest', payload)
  return data
}

export interface CharStrokeInfo {
  char: string
  strokes: number
  numerology_digit: number
}

export interface StrokesResponse {
  name: string
  chars: CharStrokeInfo[]
  total_strokes: number
  expression_number: number
}

export async function analyzeStrokes(name: string): Promise<StrokesResponse> {
  const { data } = await apiClient.post<StrokesResponse>('/api/v1/name/strokes', { name })
  return data
}
