import apiClient from './client'

export type RelationType =
  | 'couple'
  | 'friend'
  | 'parent_child'
  | 'colleague'
  | 'business_partner'
  | 'supervisor_subordinate'

export interface RelationPersonInput {
  case_id?: string
  birth_datetime: string
  tz?: string
  longitude?: number
  latitude?: number
  gender?: string
  label?: string
}

export interface RelationFullRequest {
  relation_type: RelationType
  supervisor_id?: 'a' | 'b'
  person_a: RelationPersonInput
  person_b: RelationPersonInput
  options?: {
    include_bazi?: boolean
    include_ziwei?: boolean
    timeline_years?: number[]
    liunian_year?: number
  }
}

export interface SummaryCard {
  id: string
  tone: 'support' | 'conflict' | 'neutral' | 'action'
  text: string
}

export interface DimensionScore {
  id: string
  label: string
  score: number
  max_score: number
  weight: number
  description: string
  layer: string
  engine?: string
}

export interface PalaceCross {
  pair_id: string
  a_palace: string
  b_palace: string
  relation_tag: string
  summary: string
}

export interface TimelineNode {
  year: number
  label: string
  summary: string
  risk_level?: '低' | '中' | '高'
}

export interface ActionItem {
  id: string
  text: string
  priority?: string
}

export interface RelationFullResponse {
  schema_version: string
  relation_type: RelationType
  relation_type_label?: string
  person_a: { label: string; birth_solar: string; pillars_primary: Record<string, { stem: string; branch: string }> }
  person_b: { label: string; birth_solar: string; pillars_primary: Record<string, { stem: string; branch: string }> }
  combined_score: number
  grade?: string
  summary: string
  summary_cards: SummaryCard[]
  dimensions: DimensionScore[]
  palace_cross: PalaceCross[]
  timeline: TimelineNode[]
  action_items: ActionItem[]
  tensions: { code: string; message: string }[]
  missing_fields: string[]
  disclaimer_block: { text: string; version: string }
}

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

export interface ProfileSummaryResponse {
  schema_version: string
  case_id?: string
  pillars_primary: Record<string, string>
  geju_one_liner?: string
  yongshen_favor: string[]
  strength_tier?: string
  ziwei_ming_one_liner?: string
  current_dayun?: string
  liunian_2026_tag?: string
  disclaimer_block: { text: string; version: string }
}

export async function profileSummary(caseId: string): Promise<ProfileSummaryResponse> {
  const { data } = await apiClient.get<ProfileSummaryResponse>(`/api/v1/profile/${caseId}/summary`)
  return data
}
