/**
 * relations.ts — 关系合盘分析 API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface RelationComputeRequest {
  case_a_id: string
  case_b_id: string
  relation_type: string
}

export interface RelationProfile {
  case_id: string
  name: string
  [key: string]: unknown
}

export interface RelationPoint {
  tag: string
  detail: string
  weight: number
}

export interface RelationResult {
  relation_type: string
  compatibility_score: number
  summary: string
  support_points: RelationPoint[]
  conflict_points: RelationPoint[]
  advice: string
  meta: Record<string, unknown>
}

export interface RelationComputeResponse {
  case_a: RelationProfile
  case_b: RelationProfile
  result: RelationResult
  snapshots_created: string[]
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/relations/compat — 关系合盘 */
export async function computeRelationCompat(req: RelationComputeRequest): Promise<RelationComputeResponse> {
  const { data } = await apiClient.post<RelationComputeResponse>('/api/v1/relations/compat', req)
  return data
}
