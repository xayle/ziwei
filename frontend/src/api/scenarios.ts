/**
 * scenarios.ts — 情景模拟 CRUD + 模拟 API
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface ScenarioCreateRequest {
  base_member_id: number
  name: string
  description?: string
  scenario_type: string
  variations?: string           // JSON string
  results?: string              // JSON string
}

export interface ScenarioUpdateRequest {
  name?: string
  description?: string
  scenario_type?: string
  variations?: string
  results?: string
}

export interface ScenarioResponse {
  id: number
  owner_id: number
  base_member_id: number
  name: string
  description: string | null
  scenario_type: string
  variations: string | null
  results: string | null
  created_at: string
  updated_at: string
}

export interface ScenarioListResponse {
  items: ScenarioResponse[]
  total: number
  next_cursor: number | null
}

export interface SimulateRequest {
  birth_dt_override?: string
  longitude_override?: number
  gender_override?: string
  note?: string
}

export interface SimulateResponse {
  scenario_id: number
  geju_name: string
  yongshen_favor: string[]
  yongshen_avoid: string[]
  wuxing_scores: Record<string, number>
  note: string
  simulated_at: string
}

// ── API 函数 ──────────────────────────────────────────────────

/** POST /api/v1/scenarios — 创建情景 */
export async function createScenario(req: ScenarioCreateRequest): Promise<ScenarioResponse> {
  const { data } = await apiClient.post<ScenarioResponse>('/api/v1/scenarios', req)
  return data
}

/** GET /api/v1/scenarios — 情景列表 */
export async function listScenarios(params?: {
  member_id?: number; scenario_type?: string; limit?: number; last_id?: number
}): Promise<ScenarioListResponse> {
  const { data } = await apiClient.get<ScenarioListResponse>('/api/v1/scenarios', { params })
  return data
}

/** GET /api/v1/scenarios/:id — 情景详情 */
export async function getScenario(scenarioId: number): Promise<ScenarioResponse> {
  const { data } = await apiClient.get<ScenarioResponse>(`/api/v1/scenarios/${scenarioId}`)
  return data
}

/** PUT /api/v1/scenarios/:id — 更新情景 */
export async function updateScenario(scenarioId: number, req: ScenarioUpdateRequest): Promise<ScenarioResponse> {
  const { data } = await apiClient.put<ScenarioResponse>(`/api/v1/scenarios/${scenarioId}`, req)
  return data
}

/** DELETE /api/v1/scenarios/:id — 删除情景 */
export async function deleteScenario(scenarioId: number): Promise<void> {
  await apiClient.delete(`/api/v1/scenarios/${scenarioId}`)
}

/** GET /api/v1/members/:memberId/scenarios — 成员情景列表 */
export async function getMemberScenarios(memberId: number, params?: { limit?: number; last_id?: number }): Promise<ScenarioListResponse> {
  const { data } = await apiClient.get<ScenarioListResponse>(`/api/v1/members/${memberId}/scenarios`, { params })
  return data
}

/** POST /api/v1/scenarios/:id/simulate — 情景模拟 */
export async function simulateScenario(scenarioId: number, req: SimulateRequest): Promise<SimulateResponse> {
  const { data } = await apiClient.post<SimulateResponse>(`/api/v1/scenarios/${scenarioId}/simulate`, req)
  return data
}
