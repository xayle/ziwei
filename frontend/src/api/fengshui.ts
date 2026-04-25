/**
 * fengshui.ts — 风水 API（选项、八宅、室内布局）
 */
import apiClient from './client'

// ── 类型定义 ──────────────────────────────────────────────────

export interface FengshuiOptions {
  house_facing_options: Record<string, string>
  directions_zh: Record<string, string>
  room_type_options: Record<string, string>
}

export interface RoomLayoutRequest {
  birth_year: number
  gender: string                // "男" | "女"
  rooms: Record<string, string> // direction → room_type
  house_facing?: string         // N/NE/E/SE/S/SW/W/NW
}

export interface ZoneAssessmentResponse {
  direction: string
  direction_zh: string
  label: string
  level_css: string
  room_type: string
  room_zh: string
  assess_level: string
  assess_score: number
  assess_note: string
}

export interface RoomLayoutResponse {
  life_gua: number
  gua_name: string
  score: number
  grade: string
  grade_css: string
  cells: ZoneAssessmentResponse[]
  suggestions: string[]
  disclaimer: string
}

// ── API 函数 ──────────────────────────────────────────────────

/** GET /api/v1/fengshui/options — 风水选项（方位、房型等） */
export async function getFengshuiOptions(): Promise<FengshuiOptions> {
  const { data } = await apiClient.get<FengshuiOptions>('/api/v1/fengshui/options')
  return data
}

/** POST /api/v1/fengshui/room-layout — 室内布局分析 */
export async function analyzeRoomLayout(req: RoomLayoutRequest): Promise<RoomLayoutResponse> {
  const { data } = await apiClient.post<RoomLayoutResponse>('/api/v1/fengshui/room-layout', req)
  return data
}
