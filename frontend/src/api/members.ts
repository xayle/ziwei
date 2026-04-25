/**
 * members.ts — 成员管理 CRUD API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface MemberCreateRequest {
  name: string
  birth_date: string             // "YYYY-MM-DD"
  gender: string
  birth_time_hour?: number
  birth_time_minute?: number
  birth_time?: string            // "HH:MM"
  birth_city?: string
  birth_longitude?: number
  solar_time_enabled?: boolean
  notes?: string
}

export interface MemberUpdateRequest {
  name?: string
  gender?: string
  birth_time_hour?: number
  birth_time_minute?: number
  birth_time?: string
  birth_city?: string
  birth_longitude?: number
  solar_time_enabled?: boolean
  notes?: string
}

export interface MemberResponse {
  id: number
  name: string
  birth_date: string
  gender: string
  birth_time_hour: number | null
  birth_time_minute: number | null
  birth_city: string | null
  birth_longitude: number | null
  solar_time_enabled: boolean
  notes: string | null
  birth_time: string | null      // computed "HH:MM"
}

export interface MemberListResponse {
  items: MemberResponse[]
  next_cursor: number | null
  total: number
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/members — 创建成员 */
export async function createMember(req: MemberCreateRequest): Promise<MemberResponse> {
  const { data } = await apiClient.post<MemberResponse>('/api/v1/members', req)
  return data
}

/** GET /api/v1/members — 成员列表 */
export async function listMembers(params?: { limit?: number; last_id?: number }): Promise<MemberListResponse> {
  const { data } = await apiClient.get<MemberListResponse>('/api/v1/members', { params })
  return data
}

/** GET /api/v1/members/:id — 成员详情 */
export async function getMember(memberId: number): Promise<MemberResponse> {
  const { data } = await apiClient.get<MemberResponse>(`/api/v1/members/${memberId}`)
  return data
}

/** PUT /api/v1/members/:id — 全量更新成员 */
export async function replaceMember(memberId: number, req: MemberCreateRequest): Promise<MemberResponse> {
  const { data } = await apiClient.put<MemberResponse>(`/api/v1/members/${memberId}`, req)
  return data
}

/** PATCH /api/v1/members/:id — 部分更新成员 */
export async function updateMember(memberId: number, req: MemberUpdateRequest): Promise<MemberResponse> {
  const { data } = await apiClient.patch<MemberResponse>(`/api/v1/members/${memberId}`, req)
  return data
}

/** DELETE /api/v1/members/:id — 删除成员 */
export async function deleteMember(memberId: number): Promise<void> {
  await apiClient.delete(`/api/v1/members/${memberId}`)
}
