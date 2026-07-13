import apiClient from './client'
import type {
  ActionItemModel,
  DimensionScoreModel,
  PalaceCrossModel,
  ProfileSummaryResponse,
  RelationFullRequest,
  RelationFullResponse,
  RelationPersonInput,
  SummaryCardModel,
  TimelineNodeModel,
} from './openapiTypes'

// ── 请求 / 响应（OpenAPI 真源 · P3-3）──────────────────────
export type RelationType = RelationFullRequest['relation_type']
export type { RelationFullRequest, RelationFullResponse, RelationPersonInput, ProfileSummaryResponse }

// ── 嵌套模型（FE 别名 · 向后兼容）──────────────────────────
export type SummaryCard = SummaryCardModel
export type DimensionScore = DimensionScoreModel
export type PalaceCross = PalaceCrossModel
export type TimelineNode = TimelineNodeModel
export type ActionItem = ActionItemModel

export const RELATION_TYPE_OPTIONS: { value: RelationType; label: string }[] = [
  { value: 'couple', label: '情侣合盘' },
  { value: 'friend', label: '友人合盘' },
  { value: 'parent_child', label: '亲子合盘' },
  { value: 'colleague', label: '同事合盘' },
  { value: 'business_partner', label: '合作伙伴合盘' },
  { value: 'supervisor_subordinate', label: '上下级合盘' },
]

export async function relationFull(body: RelationFullRequest): Promise<RelationFullResponse> {
  const { data } = await apiClient.post<RelationFullResponse>('/api/v1/relation/full', body)
  return data
}

export async function relationExportPdf(body: RelationFullRequest): Promise<Blob> {
  const { data } = await apiClient.post<Blob>('/api/v1/relation/export/pdf', body, {
    responseType: 'blob',
    timeout: 120_000,
  })
  return data
}

export async function relationExportPng(body: RelationFullRequest): Promise<Blob> {
  const { data } = await apiClient.post<Blob>('/api/v1/relation/export/png', body, {
    responseType: 'blob',
    timeout: 60_000,
  })
  return data
}

export { saveBlobAsFile } from './fushengReport'

export async function profileSummary(caseId: string): Promise<ProfileSummaryResponse> {
  const { data } = await apiClient.get<ProfileSummaryResponse>(`/api/v1/profile/${caseId}/summary`)
  return data
}
