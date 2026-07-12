import { describe, expect, it } from 'vitest'
import type { ProfileData } from '@/stores/profile'
import { profileToCasePayload } from '@/utils/profileCaseSync'

const profile: ProfileData = {
  birthDt: '1990-01-15T08:30',
  lon: 116.41,
  cityName: '北京',
  province: '北京市',
  tz: 'Asia/Shanghai',
  gender: 'male',
  mode: 'dual',
  solarTime: false,
  surname: '张',
  calendarMode: 'gregorian',
  isLeapMonth: false,
  yearDivide: 'lichun',
  dayDivide: 'solar_next',
  lateZishi: true,
  ziDayRule: 'sxtwl',
  ziweiBrightnessMethod: 'zhongzhou',
  ziweiYoubiMethod: 'hour',
  sihuaMethod: 'zhongzhou',
  liunianSihuaMethod: 'life_palace_stem',
  kuiyueMethod: 'gengxin_mahu',
  tianmaMethod: 'month',
  templateVersion: 'pro',
  birthTimePrecision: 'exact',
  unknownTimeFallback: 'midday',
  givenName: '三',
  currentCityName: '',
  currentProvince: '',
  currentLon: undefined,
  currentTz: 'Asia/Shanghai',
  focusTopic: '事业',
  cityTier: '',
  industry: '',
}

describe('profileCaseSync', () => {
  it('maps profile to CaseCreate payload', () => {
    const payload = profileToCasePayload(profile, '张三')
    expect(payload.name).toBe('张三')
    expect(payload.birth_dt_local).toContain('1990-01-15')
    expect(payload.lon).toBe(116.41)
    expect(payload.gender).toBe('male')
    expect(payload.tags).toContain('fusheng')
    expect(payload.tags).toContain('sn:张')
    expect(payload.tags).toContain('gn:三')
    expect(payload.year_divide).toBe('lichun')
    expect(payload.zi_day_rule).toBe('sxtwl')
    expect(payload.ziwei_brightness_method).toBe('zhongzhou')
    expect(payload.ziwei_youbi_method).toBe('hour')
    expect(payload.ziwei_sihua_method).toBe('zhongzhou')
    expect(payload.ziwei_liunian_sihua_method).toBe('life_palace_stem')
    expect(payload.ziwei_kuiyue_method).toBe('gengxin_mahu')
    expect(payload.ziwei_tianma_method).toBe('month')
    expect(payload.ziwei_template_version).toBe('pro')
    expect(payload.tags).toContain('zsm:zhongzhou')
    expect(payload.tags).toContain('zbm:zhongzhou')
    expect(payload.tags).toContain('zyb:hour')
    expect(payload.notes).toBe('事业')
  })
})
