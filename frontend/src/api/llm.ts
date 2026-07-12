import apiClient from './client'

export interface LlmConfigResponse {
  provider: string
  model: string
  available: boolean
  note?: string
}

export interface LlmInterpretRequest {
  chart_hash: string
  life_palace_gz?: string
  wuxing_ju_name?: string
  pattern_summary?: string
  birth_info_summary?: string
  evidence_snippets?: string[]
  geju_name?: string
  yongshen_favor?: string[]
}

export interface LlmDraftResponse {
  id: number
  chart_hash: string
  provider: string
  model: string
  prompt_version: string
  draft_text: string
  status: string
  reviewer: string
  reviewer_notes: string
  input_tokens: number
  output_tokens: number
  cost_usd_estimate: number
  created_at: string
  reviewed_at?: string | null
  deleted_at?: string | null
}

export interface BaziInterpretRequest {
  case_id: string
  module?: string | null
  chart_hash?: string | null
}

export const LLM_MODULES = [
  { id: 'dayun_narrative', label: '大运叙述' },
  { id: 'liunian_advice', label: '流年建议' },
  { id: 'career_detail', label: '事业详解' },
  { id: 'marriage_detail', label: '婚恋详解' },
  { id: 'wealth_detail', label: '财富详解' },
  { id: 'fengshui_suggestion', label: '风水建议' },
] as const

export type LlmModuleId = typeof LLM_MODULES[number]['id']

export interface ModuleInterpretRequest {
  case_id: string
  module: LlmModuleId
  context?: Record<string, unknown> | null
}

export interface ModuleInterpretResponse {
  case_id: string
  module: string
  interpretation: string
  generated_at: string
}

export async function getLlmConfig(): Promise<LlmConfigResponse> {
  const { data } = await apiClient.get<LlmConfigResponse>('/api/v1/llm/config')
  return data
}

export async function interpretChart(payload: LlmInterpretRequest): Promise<LlmDraftResponse> {
  const { data } = await apiClient.post<LlmDraftResponse>('/api/v1/llm/interpret', payload)
  return data
}

export async function interpretBaziByCase(payload: BaziInterpretRequest): Promise<LlmDraftResponse> {
  const { data } = await apiClient.post<LlmDraftResponse>('/api/v1/llm/interpret-bazi', payload)
  return data
}

export async function interpretModule(payload: ModuleInterpretRequest): Promise<ModuleInterpretResponse> {
  const { data } = await apiClient.post<ModuleInterpretResponse>('/api/v1/llm/interpret-module', payload)
  return data
}
