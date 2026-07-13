import { describe, expect, it, beforeEach } from 'vitest'
import {
  captureUtmFromQuery,
  parseUtmFromQuery,
  readStoredUtm,
  UTM_STORAGE_KEY,
} from '@/utils/utmCapture'

describe('utmCapture', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('parses snake and camel query keys', () => {
    expect(parseUtmFromQuery({ utm_source: 'douyin', contentId: 'v1' })).toEqual({
      utm_source: 'douyin',
      utm_campaign: undefined,
      content_id: 'v1',
    })
  })

  it('persists first-touch utm in sessionStorage', () => {
    captureUtmFromQuery({ utm_source: 'douyin', utm_campaign: 'geju' })
    expect(readStoredUtm()).toEqual({
      utm_source: 'douyin',
      utm_campaign: 'geju',
      content_id: undefined,
    })
    expect(sessionStorage.getItem(UTM_STORAGE_KEY)).toContain('douyin')
  })
})
