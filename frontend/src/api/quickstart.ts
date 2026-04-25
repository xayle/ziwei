/**
 * quickstart.ts — 快速开始 API（一键建案例+计算）
 */
import apiClient from './client'
import type { CaseOut } from './report'

// ── 类型定义 ──────────────────────────────────────────────────

export interface QuickstartRequest {
  name: string
  birth_dt_local: string
  tz: string
  lon: number
  gender?: string
  city?: string
  solar_time_enabled?: boolean
  notes?: string
  tags?: string[]
  mode?: string                 // "dual" | "single"
  liunian_years?: number[]
}

export interface ComputeTaskStatus {
  status: string
  error?: string
  [key: string]: unknown
}

export interface ComputeResponse {
  compute_batch_id: string
  case_id: string
  input_effective: Record<string, unknown>
  tasks: Record<string, ComputeTaskStatus>
  snapshots_created: Array<Record<string, unknown>>
}

export interface QuickstartResponse {
  case: CaseOut
  compute: ComputeResponse
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/quickstart — 一键建案例并计算 */
export async function quickstart(req: QuickstartRequest): Promise<QuickstartResponse> {
  const { data } = await apiClient.post<QuickstartResponse>('/api/v1/quickstart', req)
  return data
}
