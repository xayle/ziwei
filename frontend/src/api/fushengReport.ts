import apiClient from './client'
import type { BaziResponse } from './bazi'
import type { ZiweiResponse } from './ziwei'

export interface ArchiveBundleRequest {
  case_id: string
  include_ziwei?: boolean
}

export interface ArchiveBundleResponse {
  case_id: string
  bazi: BaziResponse
  ziwei?: ZiweiResponse | null
  missing_fields?: string[]
}

export async function fetchArchiveBundle(payload: ArchiveBundleRequest): Promise<ArchiveBundleResponse> {
  const { data } = await apiClient.post<ArchiveBundleResponse>('/api/v1/fusheng/archive-bundle', {
    include_ziwei: true,
    ...payload,
  })
  return data
}

export interface FushengReportPdfRequest {

  label: string

  birth_dt: string

  lon: number

  tz: string

  gender: 'male' | 'female'

  solar_time_enabled?: boolean

  mode?: 'dual' | 'single'

  city_name?: string

  calendar_mode?: 'gregorian' | 'lunar'

  is_leap_month?: boolean

  year_divide?: 'lichun' | 'normal'

  day_divide?: 'solar_next' | 'forward' | 'current'

  late_zishi?: boolean

  zi_day_rule?: 'sxtwl' | 'early_zi_prev_day' | 'early_zi_same_day'

  birth_time_precision?: 'exact' | 'hour' | 'approximate' | 'unknown'

  unknown_time_fallback?: 'midday' | 'noon' | 'start_of_hour'

  include_liuri?: boolean

  surname?: string

  given_name?: string

  focus_topic?: string

  notes?: string

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

