import apiClient from './client'
import type {
  BaziInterpretRequest,
  InterpretModule,
  LlmConfigResponse,
  LlmDraftResponse,
  LlmInterpretRequest,
  ModuleInterpretRequest as SchemaModuleInterpretRequest,
  ModuleInterpretResponse,
} from './openapiTypes'

export type {
  BaziInterpretRequest,
  LlmConfigResponse,
  LlmDraftResponse,
  LlmInterpretRequest,
  ModuleInterpretResponse,
}

export const LLM_MODULES = [
  { id: 'dayun_narrative', label: '大运叙述' },
  { id: 'liunian_advice', label: '流年建议' },
  { id: 'career_detail', label: '事业详解' },
  { id: 'marriage_detail', label: '婚恋详解' },
  { id: 'wealth_detail', label: '财富详解' },
  { id: 'fengshui_suggestion', label: '风水建议' },
] as const satisfies ReadonlyArray<{ id: InterpretModule; label: string }>

export type LlmModuleId = typeof LLM_MODULES[number]['id']

export type ModuleInterpretRequest = SchemaModuleInterpretRequest & {
  module: LlmModuleId
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
