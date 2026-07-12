import { describe, expect, it } from 'vitest'
import type { ProfileData } from '@/stores/profile'
import {
  getMissingProfileFields,
  getProfileCompleteness,
  getProfileFieldLabel,
  getTimeConfidence,
} from '@/utils/profileMetrics'

const emptyProfile: ProfileData = {
  surname: '',
  givenName: '',
  gender: undefined,
  birthDt: '',
  cityName: '',
  lon: undefined,
  tz: 'Asia/Shanghai',
  solarTime: false,
  calendarMode: undefined,
  isLeapMonth: false,
  yearDivide: 'lichun',
  birthTimePrecision: undefined,
  unknownTimeFallback: 'midday',
  focusTopic: '',
  currentCityName: '',
  currentProvince: '',
  currentLon: undefined,
  currentTz: 'Asia/Shanghai',
  mode: 'dual',
}

const fullProfile: ProfileData = {
  ...emptyProfile,
  surname: '刘',
  givenName: '博',
  gender: 'male',
  birthDt: '1990-01-15T08:30',
  cityName: '北京',
  lon: 116.41,
  calendarMode: 'gregorian',
  birthTimePrecision: 'exact',
  focusTopic: '事业',
}

describe('profileMetrics', () => {
  it('returns 0 completeness for empty profile', () => {
    expect(getProfileCompleteness(emptyProfile)).toBe(0)
  })

  it('returns 100 completeness when blockers and enhancers filled', () => {
    expect(getProfileCompleteness(fullProfile)).toBe(100)
  })

  it('lists missing fields for partial profile', () => {
    const partial: ProfileData = {
      ...emptyProfile,
      birthDt: '1990-01-15T08:30',
      gender: 'male',
    }
    const missing = getMissingProfileFields(partial)
    expect(missing).toContain('cityName')
    expect(missing).toContain('surname')
    expect(missing).not.toContain('birthDt')
    expect(missing).not.toContain('gender')
  })

  it('exposes Chinese labels for fields', () => {
    expect(getProfileFieldLabel('birthDt')).toBe('出生时间')
    expect(getProfileFieldLabel('focusTopic')).toBe('关注重点')
  })

  it('rates exact birth time as highest confidence', () => {
    const exact = getTimeConfidence({ ...fullProfile, birthTimePrecision: 'exact' })
    const unknown = getTimeConfidence({ ...fullProfile, birthTimePrecision: 'unknown' })
    expect(exact.stars).toBe(3)
    expect(unknown.stars).toBe(0)
    expect(exact.label).toBeTruthy()
  })
})
