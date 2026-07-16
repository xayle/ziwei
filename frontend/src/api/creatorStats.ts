/**
 * T100 / FE-GTM-05 — 创作者统计（接 T099 API）
 */
import apiClient from './client'
import type { components } from './schema'

export type CreatorStatsResponse = components['schemas']['CreatorStatsResponse']
export type CreatorTopicCohort = components['schemas']['CreatorTopicCohort']
export type CreatorFunnelStep = components['schemas']['CreatorFunnelStep']
export type CreatorStatsTotals = components['schemas']['CreatorStatsTotals']

export async function fetchCreatorStats(windowDays = 30): Promise<CreatorStatsResponse> {
  const { data } = await apiClient.get<CreatorStatsResponse>('/api/v1/creator/stats', {
    params: { window_days: windowDays },
  })
  return data
}

export function formatConversionRate(rate: number | null | undefined): string {
  if (typeof rate !== 'number' || !Number.isFinite(rate)) return '—'
  return `${(rate * 100).toFixed(1)}%`
}
