import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const postMock = vi.fn()

vi.mock('@/api/client', () => ({
  default: { post: (...args: unknown[]) => postMock(...args) },
}))

describe('analytics (FE-GTM-06 / T090)', () => {
  beforeEach(() => {
    postMock.mockReset()
    postMock.mockResolvedValue({
      data: {
        accepted: 1,
        rejected: 0,
        scrubbed_pii_keys: [],
        schema_version: 'analytics-events@1.0',
      },
    })
    sessionStorage.clear()
    vi.useFakeTimers()
  })

  afterEach(async () => {
    const { resetAnalyticsQueueForTests } = await import('@/utils/analytics')
    resetAnalyticsQueueForTests()
    vi.useRealTimers()
  })

  it('scrubs name and birth keys from properties', async () => {
    const { scrubAnalyticsProperties, isAnalyticsPiiKey } = await import('@/utils/analytics')
    expect(isAnalyticsPiiKey('name')).toBe(true)
    expect(isAnalyticsPiiKey('birth_dt_local')).toBe(true)
    expect(isAnalyticsPiiKey('term_id')).toBe(false)

    const { properties, dropped } = scrubAnalyticsProperties({
      term_id: '七杀',
      name: '张三',
      birth_dt: '1990-01-01',
      dwell_ms: 1200,
    })
    expect(properties).toEqual({ term_id: '七杀', dwell_ms: 1200 })
    expect(dropped).toContain('name')
    expect(dropped).toContain('birth_dt')
  })

  it('never sends PII keys in POST body', async () => {
    const { track, flushAnalytics, resetAnalyticsQueueForTests } = await import('@/utils/analytics')
    resetAnalyticsQueueForTests()

    const { dropped } = track({
      event_type: 'glossary_click',
      properties: {
        term_id: '正官',
        name: '泄露',
        birthday: '1990-01-01',
      },
    })
    expect(dropped).toEqual(expect.arrayContaining(['name', 'birthday']))

    await flushAnalytics()
    expect(postMock).toHaveBeenCalledTimes(1)
    const body = postMock.mock.calls[0][1] as {
      events: Array<{ properties?: Record<string, unknown> }>
    }
    expect(postMock.mock.calls[0][0]).toBe('/api/v1/analytics/events')
    const props = body.events[0].properties ?? {}
    expect(props).toEqual({ term_id: '正官' })
    expect(Object.keys(props)).not.toContain('name')
    expect(Object.keys(props)).not.toContain('birthday')
  })

  it('batches volume_view via debounced flush', async () => {
    const {
      trackVolumeView,
      flushAnalytics,
      resetAnalyticsQueueForTests,
      getAnalyticsSessionId,
    } = await import('@/utils/analytics')
    resetAnalyticsQueueForTests()

    const session = getAnalyticsSessionId()
    trackVolumeView('vol1', { caseId: 'case-1' })
    trackVolumeView('vol2', { caseId: 'case-1' })
    expect(postMock).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(900)
    // debounce may have fired; ensure complete
    await flushAnalytics()

    expect(postMock).toHaveBeenCalled()
    const body = postMock.mock.calls[0][1] as {
      events: Array<{ event_type: string; session_id?: string | null; volume_id?: string | null }>
    }
    expect(body.events.length).toBeGreaterThanOrEqual(1)
    expect(body.events.every((e) => e.session_id === session)).toBe(true)
    expect(body.events.some((e) => e.volume_id === 'vol1')).toBe(true)
  })

  it('swallows network errors on flush', async () => {
    postMock.mockRejectedValueOnce(new Error('network'))
    const { track, flushAnalytics, resetAnalyticsQueueForTests } = await import('@/utils/analytics')
    resetAnalyticsQueueForTests()
    track({ event_type: 'landing_cta_click', properties: { cta: 'register' } })
    await expect(flushAnalytics()).resolves.toBeNull()
  })
})
