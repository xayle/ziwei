import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useFushengReportStore } from '@/stores/fushengReport'

const currentYear = new Date().getFullYear()
const mockBaziPayload = {
  personality: { day_stem_trait: '正直稳重' },
  liunian: {
    items: [{ year: currentYear, stem: '丙', branch: '午' }],
  },
}
const mockZiweiPayload = { wuxing_ju_name: '水二局' }

const fetchArchiveBundle = vi.fn()
const computeBazi = vi.fn()
const computeZiwei = vi.fn()

vi.mock('@/api/fushengReport', () => ({
  fetchArchiveBundle: (...args: unknown[]) => fetchArchiveBundle(...args),
}))

vi.mock('@/api/bazi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/bazi')>()
  return {
    ...actual,
    computeBazi: (...args: unknown[]) => computeBazi(...args),
    dayunReportInline: vi.fn(),
  }
})

vi.mock('@/api/ziwei', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/ziwei')>()
  return {
    ...actual,
    computeZiwei: (...args: unknown[]) => computeZiwei(...args),
  }
})

function seedProfile(remoteCaseId?: string) {
  const profileData = {
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
  }
  localStorage.setItem('profile_v1', JSON.stringify(profileData))
  localStorage.setItem('profile_active_id_v1', 'p1')
  localStorage.setItem('profile_records_v1', JSON.stringify([
    {
      id: 'p1',
      label: '测试',
      createdAt: '2026-01-01T00:00:00Z',
      updatedAt: '2026-01-01T00:00:00Z',
      remoteCaseId: remoteCaseId ?? null,
      data: profileData,
    },
  ]))
  if (remoteCaseId) {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('username', 'test-user')
  }
}

describe('fushengReport.loadReport', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    fetchArchiveBundle.mockReset()
    computeBazi.mockReset()
    computeZiwei.mockReset()
  })

  it('uses archive-bundle when remote case is linked', async () => {
    seedProfile('case-001')
    fetchArchiveBundle.mockResolvedValue({
      case_id: 'case-001',
      bazi: mockBaziPayload,
      ziwei: mockZiweiPayload,
      missing_fields: [],
    })

    const store = useFushengReportStore()
    await store.loadReport()

    expect(fetchArchiveBundle).toHaveBeenCalledWith({ case_id: 'case-001' })
    expect(computeBazi).not.toHaveBeenCalled()
    expect(computeZiwei).not.toHaveBeenCalled()
    expect(store.bazi?.personality?.day_stem_trait).toBe('正直稳重')
    expect(store.ziwei?.wuxing_ju_name).toBe('水二局')
  })

  it('falls back to compute endpoints when no remote case', async () => {
    seedProfile()
    computeBazi.mockResolvedValue(mockBaziPayload)
    computeZiwei.mockResolvedValue(mockZiweiPayload)

    const store = useFushengReportStore()
    await store.loadReport()

    expect(fetchArchiveBundle).not.toHaveBeenCalled()
    expect(computeBazi).toHaveBeenCalled()
    expect(computeZiwei).toHaveBeenCalled()
    expect(store.bazi?.personality?.day_stem_trait).toBe('正直稳重')
  })
})
