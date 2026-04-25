/**
 * events.ts — 事件记录 CRUD API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface EventCreateRequest {
  member_id: number
  name: string
  event_type: string
  bazi_json: string
  pillars_primary?: string
  ten_gods?: string
  five_elements?: string
  L_level?: number
  confidence_score?: number
  recommendation?: string
  recommendation_engine?: string
}

export interface EventUpdateRequest {
  name?: string
  event_type?: string
  L_level?: number
  confidence_score?: number
  recommendation?: string
  recommendation_engine?: string
  pillars_primary?: string
  ten_gods?: string
  five_elements?: string
}

export interface EventResponse {
  id: number
  owner_id: number
  member_id: number
  name: string
  event_type: string
  bazi_json: string
  pillars_primary: string | null
  ten_gods: string | null
  five_elements: string | null
  L_level: number
  confidence_score: number
  recommendation: string | null
  recommendation_engine: string | null
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  items: EventResponse[]
  next_cursor: number | null
  total: number
}

export interface EventStatsResponse {
  total: number
  by_type: Array<{ event_type: string; count: number }>
}

export interface MemberEventsResponse {
  events: EventResponse[]
  next_cursor: number | null
  has_more: boolean
  total_returned: number
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/events — 创建事件 */
export async function createEvent(req: EventCreateRequest): Promise<EventResponse> {
  const { data } = await apiClient.post<EventResponse>('/api/v1/events', req)
  return data
}

/** GET /api/v1/events — 事件列表 */
export async function listEvents(params?: {
  member_id?: number; event_type?: string; limit?: number; last_id?: number
}): Promise<EventListResponse> {
  const { data } = await apiClient.get<EventListResponse>('/api/v1/events', { params })
  return data
}

/** GET /api/v1/events/stats — 事件统计 */
export async function getEventStats(params?: { date_from?: string; date_to?: string }): Promise<EventStatsResponse> {
  const { data } = await apiClient.get<EventStatsResponse>('/api/v1/events/stats', { params })
  return data
}

/** GET /api/v1/events/:id — 事件详情 */
export async function getEvent(eventId: number): Promise<EventResponse> {
  const { data } = await apiClient.get<EventResponse>(`/api/v1/events/${eventId}`)
  return data
}

/** PATCH /api/v1/events/:id — 更新事件 */
export async function updateEvent(eventId: number, req: EventUpdateRequest): Promise<EventResponse> {
  const { data } = await apiClient.patch<EventResponse>(`/api/v1/events/${eventId}`, req)
  return data
}

/** PUT /api/v1/events/:id — 全量更新事件 */
export async function replaceEvent(eventId: number, req: EventCreateRequest): Promise<EventResponse> {
  const { data } = await apiClient.put<EventResponse>(`/api/v1/events/${eventId}`, req)
  return data
}

/** DELETE /api/v1/events/:id — 删除事件 */
export async function deleteEvent(eventId: number): Promise<void> {
  await apiClient.delete(`/api/v1/events/${eventId}`)
}

/** GET /api/v1/members/:memberId/events — 成员事件列表 */
export async function getMemberEvents(memberId: number, params?: { last_id?: number; limit?: number }): Promise<MemberEventsResponse> {
  const { data } = await apiClient.get<MemberEventsResponse>(`/api/v1/members/${memberId}/events`, { params })
  return data
}
