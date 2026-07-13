import apiClient from './client'
import type { ChartReviewCreate, ChartReviewResponse } from './openapiTypes'

export type ReviewCreateRequest = ChartReviewCreate
export type ReviewResponse = ChartReviewResponse

export async function createReview(payload: ReviewCreateRequest): Promise<ReviewResponse> {
  const { data } = await apiClient.post<ReviewResponse>('/api/v1/reviews', payload)
  return data
}
