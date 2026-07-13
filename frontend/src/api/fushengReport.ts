import apiClient from './client'
import type { BaziResponse } from './bazi'
import type {
  ArchiveBundleRequest,
  FushengReportPdfRequest,
  SchemaArchiveBundleResponse,
} from './openapiTypes'
import type { ZiweiResponse } from './ziwei'

export type { ArchiveBundleRequest, FushengReportPdfRequest }

/** OpenAPI 中 bazi/ziwei 为 loose object；运行时按完整排盘响应收窄 */
export type ArchiveBundleResponse = Omit<SchemaArchiveBundleResponse, 'bazi' | 'ziwei'> & {
  bazi: BaziResponse
  ziwei?: ZiweiResponse | null
}

export async function fetchArchiveBundle(payload: ArchiveBundleRequest): Promise<ArchiveBundleResponse> {
  const { data } = await apiClient.post<ArchiveBundleResponse>('/api/v1/fusheng/archive-bundle', {
    include_ziwei: true,
    ...payload,
  })
  return data
}

export async function downloadFushengReportPdf(payload: FushengReportPdfRequest): Promise<Blob> {
  const { data } = await apiClient.post<Blob>('/api/v1/fusheng/report/pdf', payload, {
    responseType: 'blob',
    timeout: 120_000,
  })
  return data
}

export function saveBlobAsFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
