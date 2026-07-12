import apiClient from './client'
import type { BaziResponse } from './bazi'
import type { ZiweiResponse } from './ziwei'

export interface SnapshotCreate {
  kind?: string
  compute_flags?: Record<string, unknown> | null
  input_json?: Record<string, unknown> | null
  output_json?: Record<string, unknown> | null
  backend_json?: Record<string, unknown> | null
  api_version?: string | null
  rule_version?: string | null
  schema_version?: string | null
  summary_level?: string | null
  summary_warning_count?: number | null
  summary_diff_count?: number | null
  summary_engine_primary?: string | null
  note?: string | null
}

export interface SnapshotOut {
  id: string
  case_id: string
  kind: string
  created_at: string
  note?: string | null
  compute_flags?: Record<string, unknown> | null
  input_json?: Record<string, unknown> | null
  output_json?: {
    bazi?: BaziResponse
    ziwei?: ZiweiResponse
  } | null
  backend_json?: Record<string, unknown> | null
  api_version?: string | null
  rule_version?: string | null
  schema_version?: string | null
  summary_level?: string | null
  summary_warning_count?: number | null
  summary_diff_count?: number | null
  summary_engine_primary?: string | null
}

export async function createSnapshot(caseId: string, payload: SnapshotCreate): Promise<SnapshotOut> {
  const { data } = await apiClient.post<SnapshotOut>(`/api/v1/cases/${caseId}/snapshots`, payload)
  return data
}

export async function listSnapshots(caseId: string): Promise<SnapshotOut[]> {
  const { data } = await apiClient.get<SnapshotOut[]>(`/api/v1/cases/${caseId}/snapshots`)
  return data
}

export async function getSnapshot(snapshotId: string): Promise<SnapshotOut> {
  const { data } = await apiClient.get<SnapshotOut>(`/api/v1/snapshots/${snapshotId}`)
  return data
}
