import { describe, expect, it, beforeEach } from 'vitest'
import { readFlowEvents, trackFlowEvent } from '@/utils/flowAnalytics'

describe('flowAnalytics', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('records flow events', () => {
    trackFlowEvent('profile_save', 'default')
    trackFlowEvent('report_generate', 'default')

    const events = readFlowEvents()
    expect(events).toHaveLength(2)
    expect(events[0].step).toBe('profile_save')
    expect(events[1].step).toBe('report_generate')
  })
})
