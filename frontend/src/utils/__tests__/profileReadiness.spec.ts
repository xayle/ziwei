import { describe, expect, it } from 'vitest'
import type { ProfileData } from '@/stores/profile'
import {
  getArchiveBlockers,
  getArchiveCompleteness,
  canAnalyzeName,
  isArchiveReady,
  isDemoSeedProfile,
} from '@/utils/profileReadiness'

const empty: ProfileData = {
  birthDt: '',
  lon: undefined,
  cityName: '',
  province: '',
  tz: 'Asia/Shanghai',
  gender: '',
  mode: 'dual',
  solarTime: false,
  surname: '',
  givenName: '',
  calendarMode: 'gregorian',
  isLeapMonth: false,
  yearDivide: 'lichun',
  birthTimePrecision: 'exact',
  unknownTimeFallback: 'midday',
  currentCityName: '',
  currentProvince: '',
  currentLon: undefined,
  currentTz: 'Asia/Shanghai',
  focusTopic: '',
}

const ready: ProfileData = {
  ...empty,
  birthDt: '1990-01-15T08:30',
  gender: 'male',
  cityName: '北京',
  lon: 116.41,
  birthTimePrecision: 'exact',
  calendarMode: 'gregorian',
  surname: '刘',
  givenName: '博',
  focusTopic: '事业',
}

describe('profileReadiness', () => {
  it('blocks empty archive', () => {
    expect(isArchiveReady(empty)).toBe(false)
    expect(getArchiveCompleteness(empty)).toBe(0)
    expect(getArchiveBlockers(empty).length).toBeGreaterThan(0)
  })

  it('allows ready archive', () => {
    expect(isArchiveReady(ready)).toBe(true)
    expect(getArchiveCompleteness(ready)).toBe(100)
  })

  it('detects demo seed profile', () => {
    expect(isDemoSeedProfile({
      ...empty,
      birthDt: '1990-01-15T08:30',
      cityName: '北京',
      lon: 116.41,
      gender: 'male',
    })).toBe(true)
  })

  it('requires surname and given name for name analysis', () => {
    expect(canAnalyzeName(ready)).toBe(true)
    expect(canAnalyzeName({ ...ready, givenName: '' })).toBe(false)
  })
})
