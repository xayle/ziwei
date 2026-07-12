import apiClient from '@/api/client'
import {
  REPORT_BAZI_EXPLAIN_SECTIONS,
  REPORT_ZIWEI_EXPLAIN_SECTIONS,
} from '@/constants/feBeContract'
import type { ContentLayer } from '@/types/life-volume'

export interface ExplainBlock {
  text: string
  layer: ContentLayer
  classic_id?: string
  evidence_ids?: string[]
}

export interface ExplainSectionResult {
  section_id: string
  blocks: ExplainBlock[]
  verified?: boolean
}

export interface ExplainBatchResponse {
  chart_hash?: string
  disclaimer_block?: { text: string; version: string; jurisdiction?: string }
  content_versions?: Record<string, string>
  wenmo_advisory?: string
  sections: ExplainSectionResult[]
}

export function mergeExplainResponses(
  ...responses: ExplainBatchResponse[]
): ExplainBatchResponse {
  const sections = responses.flatMap((r) => r.sections ?? [])
  const chart_hash = responses.find((r) => r.chart_hash)?.chart_hash
  const disclaimer_block = responses.find((r) => r.disclaimer_block)?.disclaimer_block
  const content_versions = responses.find((r) => r.content_versions)?.content_versions
  const wenmo_advisory = responses.find((r) => r.wenmo_advisory)?.wenmo_advisory
  return { chart_hash, disclaimer_block, content_versions, wenmo_advisory, sections }
}

export interface ExplainBatchResult {
  ok: boolean
  data: ExplainBatchResponse
  error?: string
}

export async function fetchBaziExplainBatchWithMeta(
  sections: string[],
  profilePayload: Record<string, unknown>,
): Promise<ExplainBatchResult> {
  try {
    const { data } = await apiClient.post<ExplainBatchResponse>('/api/v1/bazi/explain/batch', {
      sections,
      ...profilePayload,
    })
    return { ok: true, data }
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    return {
      ok: false,
      data: { sections: [] },
      error: typeof detail === 'string' ? detail : 'explain batch failed',
    }
  }
}

export async function fetchBaziExplainBatch(
  sections: string[],
  profilePayload: Record<string, unknown>,
): Promise<ExplainBatchResponse> {
  const result = await fetchBaziExplainBatchWithMeta(sections, profilePayload)
  return result.data
}

export async function fetchZiweiExplainBatch(
  sections: string[],
  profilePayload: Record<string, unknown>,
): Promise<ExplainBatchResponse> {
  try {
    const { data } = await apiClient.post<ExplainBatchResponse>('/api/v1/ziwei/explain/batch', {
      sections,
      ...profilePayload,
    })
    return data
  } catch {
    return { sections: [] }
  }
}

/** 报告页标准 explain 批次（FE-BE Q9 · ≤2 POST） */
export async function fetchReportExplainBatches(
  baziPayload: Record<string, unknown>,
  ziweiPayload: Record<string, unknown>,
): Promise<ExplainBatchResponse> {
  const [baziEx, ziweiEx] = await Promise.all([
    fetchBaziExplainBatch([...REPORT_BAZI_EXPLAIN_SECTIONS], baziPayload),
    fetchZiweiExplainBatch([...REPORT_ZIWEI_EXPLAIN_SECTIONS], ziweiPayload),
  ])
  return mergeExplainResponses(baziEx, ziweiEx)
}
