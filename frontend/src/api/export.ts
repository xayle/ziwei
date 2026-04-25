/**
 * export.ts — 案例导出 API（JSON / PDF）
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface ExportMetaResponse {
  input_snapshot: Record<string, unknown>
}

export interface ExportJsonResponse {
  export_format_version: string
  exported_at: string
  input_snapshot: Record<string, unknown>
  snapshot_meta: Record<string, unknown>
  compute_result: Record<string, unknown>
}

// ── API 函数 ──────────────────────────────────────────────────

/** GET /api/v1/cases/:id/export — 导出完整JSON（下载） */
export async function exportCaseJson(caseId: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/api/v1/cases/${caseId}/export`, { responseType: 'blob' })
  return data
}

/** GET /api/v1/cases/:id/export/meta — 导出元数据 */
export async function exportCaseMeta(caseId: string): Promise<ExportMetaResponse> {
  const { data } = await apiClient.get<ExportMetaResponse>(`/api/v1/cases/${caseId}/export/meta`)
  return data
}

/** GET /api/v1/cases/:id/export/pdf — 导出PDF（下载） */
export async function exportCasePdf(caseId: string): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/api/v1/cases/${caseId}/export/pdf`, { responseType: 'blob' })
  return data
}

/** 辅助：触发浏览器下载 Blob */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
