import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useFushengReportStore } from '@/stores/fushengReport'
import { mockBaziPayload, mockZiweiPayload } from '../../../e2e/helpers/mockChartApi'

describe('fushengReport.restoreFromSnapshot', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    localStorage.setItem('profile_v1', JSON.stringify({
      birthDt: '1990-01-15T08:30',
      lon: 116.4,
      cityName: '北京',
      province: '北京市',
      tz: 'Asia/Shanghai',
      gender: 'male',
      mode: 'dual',
      solarTime: false,
      surname: '',
      givenName: '',
      calendarMode: 'gregorian',
      isLeapMonth: false,
      yearDivide: 'lichun',
      dayDivide: 'solar_next',
      lateZishi: true,
      ziDayRule: 'sxtwl',
      birthTimePrecision: 'exact',
      unknownTimeFallback: 'midday',
      currentCityName: '',
      currentProvince: '',
      currentTz: 'Asia/Shanghai',
      focusTopic: '',
      cityTier: '',
      industry: '',
    }))
    localStorage.setItem('profile_active_id_v1', 'p1')
    localStorage.setItem('profile_records_v1', JSON.stringify([
      {
        id: 'p1',
        label: '测试',
        createdAt: '2026-01-01T00:00:00Z',
        updatedAt: '2026-01-01T00:00:00Z',
        data: JSON.parse(localStorage.getItem('profile_v1') || '{}'),
      },
    ]))
  })

  it('restores bazi/ziwei and sets snapshot note', () => {
    const store = useFushengReportStore()
    store.restoreFromSnapshot({
      bazi: mockBaziPayload as never,
      ziwei: mockZiweiPayload as never,
    })

    expect(store.bazi?.personality?.day_stem_trait).toBe('正直稳重')
    expect(store.ziwei?.wuxing_ju_name).toBe('水二局')
    expect(store.snapshotNote).toContain('已从云端快照恢复')
  })
})
