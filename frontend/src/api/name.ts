import apiClient from './client'
import type {
  CharStrokeInfo,
  GridInfoResponse,
  NameAnalysisResponse,
  NameRequest,
  NameSuggestRequest,
  NameSuggestResponse,
  NameSuggestionItem,
  SancaiInfoResponse,
  StrokesResponse,
} from './openapiTypes'

export type GridInfo = GridInfoResponse
export type SancaiInfo = SancaiInfoResponse
export type { CharStrokeInfo, NameAnalysisResponse, NameRequest, NameSuggestRequest, NameSuggestResponse, NameSuggestionItem, StrokesResponse }

export async function analyzeName(payload: NameRequest): Promise<NameAnalysisResponse> {
  const { data } = await apiClient.post<NameAnalysisResponse>('/api/v1/name/analyze', payload)
  return data
}

export async function suggestNames(payload: NameSuggestRequest): Promise<NameSuggestResponse> {
  const { data } = await apiClient.post<NameSuggestResponse>('/api/v1/name/suggest', payload)
  return data
}

export async function analyzeStrokes(name: string): Promise<StrokesResponse> {
  const { data } = await apiClient.post<StrokesResponse>('/api/v1/name/strokes', { name })
  return data
}
