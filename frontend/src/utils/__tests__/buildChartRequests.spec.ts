import { describe, expect, it } from 'vitest'
import type { ProfileData } from '@/stores/profile'
import {
  buildBaziRequest,
  buildFushengReportPdfRequest,
  buildProfileSignature,
  buildZiweiCacheKey,
  buildZiweiRequest,
} from '@/utils/buildChartRequests'

const profile: ProfileData = {
  birthDt: '1990-01-15T08:30',
  lon: 116.41,
  cityName: '北京',
  province: '北京市',
  tz: 'Asia/Shanghai',
  gender: 'male',
  mode: 'dual',
  solarTime: false,
  surname: '',
  calendarMode: 'gregorian',
  isLeapMonth: false,
  yearDivide: 'lichun',
  dayDivide: 'solar_next',
  lateZishi: true,
  ziweiYoubiMethod: 'month',
  sihuaMethod: 'quanshu',
  liunianSihuaMethod: 'year_stem',
  kuiyueMethod: 'standard',
  tianmaMethod: 'year',
  templateVersion: 'standard',
  birthTimePrecision: 'exact',
  unknownTimeFallback: 'midday',
  givenName: '',
  currentCityName: '',
  currentProvince: '',
  currentLon: undefined,
  currentTz: 'Asia/Shanghai',
  focusTopic: '',
  cityTier: '一线' as const,
  industry: '金融IT' as const,
  ziDayRule: 'sxtwl',
  ziweiBrightnessMethod: 'standard',
}

describe('buildChartRequests', () => {
  it('builds bazi request with normalized dt', () => {
    const req = buildBaziRequest(profile)
    expect(req.dt).toContain('1990-01-15')
    expect(req.lon).toBe(116.41)
    expect(req.gender).toBe('male')
    expect(req.include_liuri).toBe(true)
  })

  it('builds ziwei request from profile', () => {
    const req = buildZiweiRequest(profile, 2026)
    expect(req.year).toBe(1990)
    expect(req.month).toBe(1)
    expect(req.day).toBe(15)
    expect(req.gender).toBe('男')
    expect(req.liunian_year).toBe(2026)
    expect(req.longitude).toBeUndefined()
    expect(req.youbi_method).toBe('month')
    expect(req.liunian_sihua_method).toBe('year_stem')
    expect(req.kuiyue_method).toBe('standard')
    expect(req.tianma_method).toBe('year')
    expect(req.template_version).toBe('standard')
    expect(req.include_flow_liuri).toBe(true)
  })

  it('passes longitude when solarTime enabled', () => {
    const req = buildZiweiRequest({ ...profile, solarTime: true }, 2026)
    expect(req.longitude).toBe(116.41)
  })

  it('passes year_divide from profile', () => {
    const req = buildZiweiRequest({ ...profile, yearDivide: 'normal' }, 2026)
    expect(req.year_divide).toBe('normal')
  })

  it('passes day_divide and late_zishi from profile', () => {
    const req = buildZiweiRequest({ ...profile, dayDivide: 'forward', lateZishi: false }, 2026)
    expect(req.day_divide).toBe('forward')
    expect(req.late_zishi).toBe(false)
  })

  it('passes city_tier and industry when set', () => {
    const req = buildBaziRequest({ ...profile, cityTier: '一线', industry: '金融IT' })
    expect(req.city_tier).toBe('一线')
    expect(req.industry).toBe('金融IT')
  })

  it('passes birth_time_precision from profile', () => {
    expect(buildBaziRequest(profile).birth_time_precision).toBe('exact')
    const req = buildBaziRequest({ ...profile, birthTimePrecision: 'unknown' })
    expect(req.birth_time_precision).toBe('unknown')
  })

  it('builds pdf request aligned with chart requests', () => {
    const req = buildFushengReportPdfRequest(profile, { label: '测试', notes: '批注' })
    expect(req.birth_dt).toContain('1990-01-15')
    expect(req.year_divide).toBe('lichun')
    expect(req.day_divide).toBe('solar_next')
    expect(req.late_zishi).toBe(true)
    expect(req.birth_time_precision).toBe('exact')
    expect(req.unknown_time_fallback).toBe('midday')
    expect(req.include_liuri).toBe(true)
    expect(req.notes).toBe('批注')
  })

  it('passes target_date when provided for bazi', () => {
    const req = buildBaziRequest(profile, '2026-07-21')
    expect(req.target_date).toBe('2026-07-21T00:00:00')
  })

  it('passes target_date and liunian year for ziwei timeline', () => {
    const req = buildZiweiRequest(profile, 2026, '2026-07-21')
    expect(req.target_date).toBe('2026-07-21T00:00:00')
    expect(req.liunian_year).toBe(2026)
  })

  it('includes timeline target date in ziwei cache signature', () => {
    const base = buildProfileSignature(profile)
    const withDate = buildZiweiCacheKey(profile, '2026-07-21')
    expect(withDate).not.toBe(base)
    expect(withDate).toContain('2026-07-21')
  })

  it('signature changes when precision changes', () => {
    const a = buildProfileSignature(profile)
    const b = buildProfileSignature({ ...profile, birthTimePrecision: 'unknown' })
    expect(a).not.toBe(b)
  })
})
