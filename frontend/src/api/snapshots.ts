/**
 * snapshots.ts — 案例快照 CRUD + Diff API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface SnapshotCreate {
  kind?: string                  // "ziwei" | "bazi" etc.
  compute_flags?: Record<string, unknown>
  input_json?: Record<string, unknown>
  output_json?: Record<string, unknown>
  backend_json?: Record<string, unknown>
  api_version?: string
  rule_version?: string
  schema_version?: string        // default "snapshot@5.0"
  summary_level?: string
  summary_warning_count?: number
  summary_diff_count?: number
  summary_engine_primary?: string
  note?: string
}

export interface SnapshotOut {
  id: string
  case_id: string
  kind: string
  compute_flags: Record<string, unknown> | null
  input_json: Record<string, unknown> | null
  output_json: Record<string, unknown> | null
  backend_json: Record<string, unknown> | null
  api_version: string | null
  rule_version: string | null
  schema_version: string | null
  summary_level: string | null
  summary_warning_count: number | null
  summary_diff_count: number | null
  summary_engine_primary: string | null
  note: string | null
  created_at: string
}

export interface SnapshotDiffField {
  field: string
  value_a: unknown
  value_b: unknown
}

export interface SnapshotDiffResponse {
  snapshot_a: string
  snapshot_b: string
  changed_fields: SnapshotDiffField[]
  added_fields: string[]
  removed_fields: string[]
  total_changes: number
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/cases/:caseId/snapshots — 创建快照 */
export async function createSnapshot(caseId: string, req: SnapshotCreate): Promise<SnapshotOut> {
  const { data } = await apiClient.post<SnapshotOut>(`/api/v1/cases/${caseId}/snapshots`, req)
  return data
}

/** GET /api/v1/cases/:caseId/snapshots — 快照列表 */
export async function listSnapshots(caseId: string, params?: { limit?: number; offset?: number }): Promise<SnapshotOut[]> {
  const { data } = await apiClient.get<SnapshotOut[]>(`/api/v1/cases/${caseId}/snapshots`, { params })
  return data
}

/** GET /api/v1/snapshots/:id — 单个快照详情 */
export async function getSnapshot(snapshotId: string): Promise<SnapshotOut> {
  const { data } = await apiClient.get<SnapshotOut>(`/api/v1/snapshots/${snapshotId}`)
  return data
}

/** DELETE /api/v1/snapshots/:id — 删除快照 */
export async function deleteSnapshot(snapshotId: string): Promise<void> {
  await apiClient.delete(`/api/v1/snapshots/${snapshotId}`)
}

/** GET /api/v1/snapshots/diff — 快照对比 */
export async function diffSnapshots(a: string, b: string): Promise<SnapshotDiffResponse> {
  const { data } = await apiClient.get<SnapshotDiffResponse>('/api/v1/snapshots/diff', { params: { a, b } })
  return data
}
