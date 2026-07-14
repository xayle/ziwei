/** Normalize FastAPI / axios error `detail` for UI banners. */
export function formatApiDetail(detail: unknown, fallback = '请求失败，请稍后重试。'): string {
  if (detail == null) return fallback
  if (typeof detail === 'string') {
    const trimmed = detail.trim()
    return trimmed || fallback
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const rec = item as Record<string, unknown>
          if (typeof rec.msg === 'string') return rec.msg
          if (typeof rec.message === 'string') return rec.message
        }
        return ''
      })
      .map((s) => s.trim())
      .filter(Boolean)
    return parts.length ? parts.join('；') : fallback
  }
  if (typeof detail === 'object') {
    const rec = detail as Record<string, unknown>
    if (typeof rec.msg === 'string' && rec.msg.trim()) return rec.msg.trim()
    if (typeof rec.message === 'string' && rec.message.trim()) return rec.message.trim()
    if (typeof rec.detail === 'string' && rec.detail.trim()) return rec.detail.trim()
  }
  return fallback
}

export function formatAxiosError(error: unknown, fallback = '请求失败，请稍后重试。'): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (detail !== undefined) return formatApiDetail(detail, fallback)
  if (error instanceof Error && error.message.trim()) return error.message
  return fallback
}
