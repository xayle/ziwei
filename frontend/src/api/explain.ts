import apiClient from '@/api/client'
import type {
  ExplainBatchResponse as SchemaExplainBatchResponse,
  ExplainBlockModel,
  ExplainSectionResultModel,
} from '@/api/openapiTypes'
import {
  REPORT_BAZI_EXPLAIN_SECTIONS,
  REPORT_ZIWEI_EXPLAIN_SECTIONS,
} from '@/constants/feBeContract'

// ── 嵌套模型（OpenAPI 真源 · P3-3）──────────────────────────
export type ExplainBlock = ExplainBlockModel
export type ExplainSectionResult = ExplainSectionResultModel

/** 成功响应对齐 schema；错误 stub 可仅含 sections */
export type ExplainBatchResponse = Partial<
  Pick<SchemaExplainBatchResponse, 'chart_hash' | 'disclaimer_block' | 'content_versions' | 'wenmo_advisory'>
> & {
  sections?: ExplainSectionResultModel[]
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
    const { data } = await apiClient.post<SchemaExplainBatchResponse>('/api/v1/bazi/explain/batch', {
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

export async function fetchZiweiExplainBatchWithMeta(
  sections: string[],
  profilePayload: Record<string, unknown>,
): Promise<ExplainBatchResult> {
  try {
    const { data } = await apiClient.post<SchemaExplainBatchResponse>('/api/v1/ziwei/explain/batch', {
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

export async function fetchZiweiExplainBatch(
  sections: string[],
  profilePayload: Record<string, unknown>,
): Promise<ExplainBatchResponse> {
  const result = await fetchZiweiExplainBatchWithMeta(sections, profilePayload)
  return result.data
}

/** 报告页标准 explain 批次（FE-BE Q9 · ≤2 POST） */
export async function fetchReportExplainBatches(
  baziPayload: Record<string, unknown>,
  ziweiPayload: Record<string, unknown>,
): Promise<ExplainBatchResponse> {
  const result = await fetchReportExplainBatchesWithMeta(baziPayload, ziweiPayload)
  return result.data
}

/** REP-02：带失败元信息，避免空 sections 静默当成功 */
export async function fetchReportExplainBatchesWithMeta(
  baziPayload: Record<string, unknown>,
  ziweiPayload: Record<string, unknown>,
): Promise<{ ok: boolean; data: ExplainBatchResponse; error?: string }> {
  const [baziEx, ziweiEx] = await Promise.all([
    fetchBaziExplainBatchWithMeta([...REPORT_BAZI_EXPLAIN_SECTIONS], baziPayload),
    fetchZiweiExplainBatchWithMeta([...REPORT_ZIWEI_EXPLAIN_SECTIONS], ziweiPayload),
  ])
  const ok = baziEx.ok || ziweiEx.ok
  const errors = [baziEx.error, ziweiEx.error].filter(Boolean)
  return {
    ok,
    data: mergeExplainResponses(baziEx.data, ziweiEx.data),
    error: errors.length ? errors.join('；') : undefined,
  }
}
