/**
 * 年份事件预测 API
 * 对应后端 routers/event_prediction.py
 */
import apiClient from './client'

// ── 类型定义 ─────────────────────────────────────────────────────────────────

export type SignalLayer = 'natal_base' | 'dayun_trigger' | 'liunian_trigger' | 'month_trigger'
export type SignalSev   = 'primary' | 'secondary' | 'tertiary'
export type RiskLevel  = 'none' | 'low' | 'medium' | 'medium_high' | 'high'
export type EventType  = 'marriage' | 'wealth' | 'property' | 'career' | 'health'

export interface EventSignal {
  signal_key: string
  label:      string
  layer:      SignalLayer
  severity:   SignalSev
  rule_id?:   string
}

export interface ClassicalNote {
  basis:  string
  source: string
}

export interface EventResult {
  event_type:             EventType
  year:                   number
  risk_level:             RiskLevel
  opportunity_level:      RiskLevel
  confidence:             number         // 0.0 ~ 1.0
  main_judgment:          string
  trigger_summary:        string
  event_subtypes:         string[]
  signals:                EventSignal[]
  possible_manifestations: string[]
  key_months:             number[]
  omens:                  string[]
  advice:                 string[]
  classical_notes:        ClassicalNote[]
  avoid_overclaim?:       string
}

// ── 请求 / 响应 ───────────────────────────────────────────────────────────────

export interface YearEventRequest {
  case_id:     string
  year:        number
  event_types?: EventType[]
}

export interface YearEventResponse {
  case_id:           string
  year:              number
  year_ganzhi:       string
  events:            Record<EventType, EventResult>
  overall_year_score: number
}

export interface MultiYearTrendRequest {
  case_id: string
  years:   number[]
}

export interface YearSummary {
  year:        number
  year_ganzhi: string
  main_theme:  string
  top_events:  EventType[]
  risk:        RiskLevel
  opportunity: RiskLevel
  annual_score: number
}

export interface MultiYearTrendResponse {
  case_id:          string
  timeline_summary: string
  summaries:        YearSummary[]
}

export interface YearEventConsultRequest {
  case_id:       string
  year:          number
  event_type:    EventType
  user_question: string
}

export interface YearEventConsultResponse {
  case_id:             string
  year:                number
  event_type:          EventType
  interpretation:      string
  followup_questions:  string[]
}

// ── 辅助：风险等级中文映射 ──────────────────────────────────────────────────

export const RISK_LABEL: Record<RiskLevel, string> = {
  none:        '平稳',
  low:         '轻微',
  medium:      '中等',
  medium_high: '偏高',
  high:        '高风险',
}

export const EVENT_DISPLAY: Record<EventType, string> = {
  marriage: '婚姻感情',
  wealth:   '财运财务',
  property: '置业动产',
  career:   '事业发展',
  health:   '健康状态',
}

export const SIGNAL_LAYER_LABEL: Record<SignalLayer, string> = {
  natal_base:      '命局基础',
  dayun_trigger:   '大运触发',
  liunian_trigger: '流年触发',
  month_trigger:   '月令触发',
}

// ── API 函数 ──────────────────────────────────────────────────────────────────

/** POST /api/v1/bazi/year-events — 单年五大事件分析 */
export async function yearEvents(req: YearEventRequest): Promise<YearEventResponse> {
  const { data } = await apiClient.post<YearEventResponse>('/api/v1/bazi/year-events', req)
  return data
}

/** POST /api/v1/bazi/multi-year-trend — 多年趋势 */
export async function multiYearTrend(req: MultiYearTrendRequest): Promise<MultiYearTrendResponse> {
  const { data } = await apiClient.post<MultiYearTrendResponse>('/api/v1/bazi/multi-year-trend', req)
  return data
}

/** POST /api/v1/bazi/year-event-consult — AI 咨询式解读 */
export async function yearEventConsult(req: YearEventConsultRequest): Promise<YearEventConsultResponse> {
  const { data } = await apiClient.post<YearEventConsultResponse>('/api/v1/bazi/year-event-consult', req)
  return data
}
