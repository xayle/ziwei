import apiClient from './client'
import type {
  CaseCreate,
  CaseListResponse,
  CaseOut,
  CasePatch,
} from './openapiTypes'

export type { CaseCreate, CaseOut, CasePatch, CaseListResponse }

export async function createCase(payload: CaseCreate): Promise<CaseOut> {
  const { data } = await apiClient.post<CaseOut>('/api/v1/cases', payload)
  return data
}

export async function patchCase(caseId: string, payload: CasePatch): Promise<CaseOut> {
  const { data } = await apiClient.patch<CaseOut>(`/api/v1/cases/${caseId}`, payload)
  return data
}

export async function getCase(caseId: string): Promise<CaseOut> {
  const { data } = await apiClient.get<CaseOut>(`/api/v1/cases/${caseId}`)
  return data
}

export async function listCases(limit = 20): Promise<CaseListResponse> {
  const { data } = await apiClient.get<CaseListResponse>('/api/v1/cases', { params: { limit } })
  return data
}
