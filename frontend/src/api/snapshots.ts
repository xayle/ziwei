import apiClient from './client'
import type { BaziResponse } from './bazi'
import type { SchemaSnapshotOut, SnapshotCreate } from './openapiTypes'
import type { ZiweiResponse } from './ziwei'

export type { SnapshotCreate }

/** OpenAPI output_json 为 loose object；运行时按排盘响应收窄 */
export type SnapshotOut = Omit<SchemaSnapshotOut, 'output_json'> & {
  output_json?: {
    bazi?: BaziResponse
    ziwei?: ZiweiResponse
  } | null
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
