import apiClient from './client'

export interface ReviewCreateRequest {
  report_hash: string
  birth_info: string
  life_palace_gz?: string
  wuxing_ju_name?: string
  pattern_summary?: string
  template_version?: string
}

export interface ReviewResponse {
  id: number
  report_hash: string
  birth_info: string
  life_palace_gz: string
  wuxing_ju_name: string
  pattern_summary: string
  status: string
  reviewer: string
  notes: string
  reject_reason: string
  algorithm_version: string
  template_version: string
  revision: number
  created_at: string
  reviewed_at?: string | null
  deleted_at?: string | null
}

export async function createReview(payload: ReviewCreateRequest): Promise<ReviewResponse> {
  const { data } = await apiClient.post<ReviewResponse>('/api/v1/reviews', payload)
  return data
}
