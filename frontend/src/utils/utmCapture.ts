/**
 * 落地页 / 注册 UTM 首触捕获（对齐 BE T088）
 */

import { readStorage, writeStorage } from '@/utils/browserStorage'

export const UTM_STORAGE_KEY = 'fusheng-utm'

export type UtmParams = {
  utm_source?: string
  utm_campaign?: string
  content_id?: string
}

function clean(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const s = value.trim()
  return s || undefined
}

export function parseUtmFromQuery(query: Record<string, unknown>): UtmParams {
  return {
    utm_source: clean(query.utm_source) ?? clean(query.utmSource),
    utm_campaign: clean(query.utm_campaign) ?? clean(query.utmCampaign),
    content_id: clean(query.content_id) ?? clean(query.contentId),
  }
}

export function captureUtmFromQuery(query: Record<string, unknown>): UtmParams {
  const next = parseUtmFromQuery(query)
  const prev = readStoredUtm()
  const merged: UtmParams = {
    utm_source: next.utm_source ?? prev.utm_source,
    utm_campaign: next.utm_campaign ?? prev.utm_campaign,
    content_id: next.content_id ?? prev.content_id,
  }
  if (merged.utm_source || merged.utm_campaign || merged.content_id) {
    writeStorage(UTM_STORAGE_KEY, JSON.stringify(merged), 'session')
  }
  return merged
}

export function readStoredUtm(): UtmParams {
  const raw = readStorage(UTM_STORAGE_KEY, 'session')
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw) as UtmParams
    return {
      utm_source: clean(parsed.utm_source),
      utm_campaign: clean(parsed.utm_campaign),
      content_id: clean(parsed.content_id),
    }
  } catch {
    return {}
  }
}

/** 供 router.push query 透传 */
export function utmAsQuery(utm: UtmParams): Record<string, string> {
  const q: Record<string, string> = {}
  if (utm.utm_source) q.utm_source = utm.utm_source
  if (utm.utm_campaign) q.utm_campaign = utm.utm_campaign
  if (utm.content_id) q.content_id = utm.content_id
  return q
}
