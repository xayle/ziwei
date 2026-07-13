/**
 * FE-GTM-06 / T090 · 产品埋点 SDK
 *
 * 对接 `POST /api/v1/analytics/events`。
 * **禁止**将姓名、生日等 PII 写入 properties（发送前剥离）。
 */

import apiClient from '@/api/client'
import type { components } from '@/api/schema'

type AnalyticsEventItem = components['schemas']['AnalyticsEventItem']
type AnalyticsEventsBatchResponse = components['schemas']['AnalyticsEventsBatchResponse']

export type AnalyticsEventType = AnalyticsEventItem['event_type']

export type AnalyticsProperties = Record<string, string | number | boolean | null | undefined>

export type TrackPayload = {
  event_type: AnalyticsEventType
  case_id?: string | null
  volume_id?: string | null
  properties?: AnalyticsProperties
  ts?: string | null
}

const SESSION_KEY = 'fusheng-analytics-session'
const MAX_BATCH = 50
const FLUSH_MS = 800

/** 与 BE `scrub_properties` 对齐的 PII 键（小写） */
export const ANALYTICS_PII_KEYS = new Set([
  'name',
  'username',
  'real_name',
  'full_name',
  'email',
  'phone',
  'mobile',
  'password',
  'birthday',
  'birthdate',
  'birth_dt',
  'birth_dt_local',
  'birth_year',
  'birth_month',
  'birth_day',
  'lon',
  'lat',
  'latitude',
  'longitude',
  'address',
  'id_card',
])

export function isAnalyticsPiiKey(key: string): boolean {
  const low = key.trim().toLowerCase()
  return ANALYTICS_PII_KEYS.has(low) || low.startsWith('birth_')
}

/** 剥离 PII；返回清理后的 properties 与被丢弃的键名 */
export function scrubAnalyticsProperties(
  raw: AnalyticsProperties | undefined | null,
): { properties: Record<string, string | number | boolean | null>; dropped: string[] } {
  if (!raw) return { properties: {}, dropped: [] }
  const properties: Record<string, string | number | boolean | null> = {}
  const dropped: string[] = []
  for (const [key, value] of Object.entries(raw)) {
    if (isAnalyticsPiiKey(key)) {
      dropped.push(key)
      continue
    }
    if (value === undefined) continue
    if (typeof value === 'string') {
      properties[key] = value.length > 500 ? value.slice(0, 500) : value
    } else if (typeof value === 'number' || typeof value === 'boolean' || value === null) {
      properties[key] = value
    }
    // 嵌套对象 / 数组一律丢弃，避免误传 PII
  }
  return { properties, dropped }
}

export function getAnalyticsSessionId(): string {
  try {
    const existing = sessionStorage.getItem(SESSION_KEY)
    if (existing && existing.length >= 8) return existing
    const id =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    sessionStorage.setItem(SESSION_KEY, id)
    return id
  } catch {
    return `sess-ephemeral-${Date.now()}`
  }
}

let queue: AnalyticsEventItem[] = []
let flushTimer: ReturnType<typeof setTimeout> | null = null
let flushing = false

function enqueue(item: AnalyticsEventItem): void {
  queue.push(item)
  if (queue.length >= MAX_BATCH) {
    void flushAnalytics()
    return
  }
  if (flushTimer == null) {
    flushTimer = setTimeout(() => {
      flushTimer = null
      void flushAnalytics()
    }, FLUSH_MS)
  }
}

export function resetAnalyticsQueueForTests(): void {
  queue = []
  if (flushTimer != null) {
    clearTimeout(flushTimer)
    flushTimer = null
  }
  flushing = false
}

/** 立即冲刷队列；失败静默（埋点不得打断主流程） */
export async function flushAnalytics(): Promise<AnalyticsEventsBatchResponse | null> {
  if (flushTimer != null) {
    clearTimeout(flushTimer)
    flushTimer = null
  }
  if (flushing || queue.length === 0) return null
  flushing = true
  const batch = queue.splice(0, MAX_BATCH)
  try {
    const { data } = await apiClient.post<AnalyticsEventsBatchResponse>(
      '/api/v1/analytics/events',
      { events: batch },
    )
    return data
  } catch {
    // 丢失本批；不重试，避免打爆限流
    return null
  } finally {
    flushing = false
    if (queue.length > 0) {
      flushTimer = setTimeout(() => {
        flushTimer = null
        void flushAnalytics()
      }, FLUSH_MS)
    }
  }
}

/** 记录单条事件（自动剥离 PII · 批量发送） */
export function track(payload: TrackPayload): { dropped: string[] } {
  const { properties, dropped } = scrubAnalyticsProperties(payload.properties)
  const item: AnalyticsEventItem = {
    event_type: payload.event_type,
    session_id: getAnalyticsSessionId(),
    case_id: payload.case_id ?? null,
    volume_id: payload.volume_id ?? null,
    ts: payload.ts ?? new Date().toISOString(),
    properties,
  }
  enqueue(item)
  return { dropped }
}

export function trackVolumeView(volumeId: string, opts?: { caseId?: string; dwellMs?: number }): void {
  track({
    event_type: 'volume_view',
    volume_id: volumeId,
    case_id: opts?.caseId,
    properties: opts?.dwellMs != null ? { dwell_ms: opts.dwellMs } : undefined,
  })
}

export function trackVolumeDwell(volumeId: string, dwellMs: number, caseId?: string): void {
  track({
    event_type: 'volume_dwell',
    volume_id: volumeId,
    case_id: caseId,
    properties: { dwell_ms: dwellMs },
  })
}

export function trackGlossaryClick(termId: string, opts?: { volumeId?: string; caseId?: string }): void {
  track({
    event_type: 'glossary_click',
    volume_id: opts?.volumeId,
    case_id: opts?.caseId,
    properties: { term_id: termId },
  })
}

export function trackLandingCta(cta: string): void {
  track({
    event_type: 'landing_cta_click',
    properties: { cta },
  })
}
