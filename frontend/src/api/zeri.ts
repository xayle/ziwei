import apiClient from './client'

// ── 类型定义 ────────────────────────────────────────────────────

export interface ZeriDayItem {
  date: string         // "2026-04-01"
  weekday: string      // "一"~"日"
  day_gz: string       // "乙巳"
  day_stem: string
  day_branch: string
  lunar_info: string   // "三月初五"
  score: number        // 0-100
  level: string        // "大吉"/"吉"/"中"/"凶"
  level_css: string    // "daji"/"ji"/"zhong"/"xiong"
  evidence: string[]
  is_break: boolean
  is_virtue: boolean
}

export interface ZeriMonthResult {
  year: number
  month: number
  purpose: string
  purpose_label: string
  year_gz: string
  month_gz: string
  days: ZeriDayItem[]
  top_days: string[]   // 推荐日期字符串列表
}

export interface ZeriRecommendParams {
  year: number
  month: number
  life_palace_branch: string
  wuxing_ju_name: string
  natal_year_branch?: string
  purpose?: string
}

// ── API 函数 ────────────────────────────────────────────────────

export async function recommendZeri(params: ZeriRecommendParams): Promise<ZeriMonthResult> {
  const res = await apiClient.get<ZeriMonthResult>('/api/v1/zeri/recommend', { params })
  return res.data
}

export async function getZeriPurposes(): Promise<Record<string, string>> {
  const res = await apiClient.get<{ purposes: Record<string, string> }>('/api/v1/zeri/purposes')
  return res.data.purposes
}
