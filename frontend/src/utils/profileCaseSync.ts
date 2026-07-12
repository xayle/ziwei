import type { CaseCreate, CasePatch, CaseOut } from '@/api/cases'
import type { ProfileData } from '@/stores/profile'
import { buildChartRequestMeta } from '@/utils/buildChartRequests'

function normalizeBirthDtLocal(value: string): string {
  const raw = value.trim().replace(' ', 'T')
  return raw.length === 16 ? `${raw}:00` : raw
}

function buildFushengTags(data: ProfileData): string {
  const parts = ['fusheng']
  if (data.surname?.trim()) parts.push(`sn:${data.surname.trim()}`)
  if (data.givenName?.trim()) parts.push(`gn:${data.givenName.trim()}`)
  if (data.lunarBirthDt?.trim()) parts.push(`lbd:${data.lunarBirthDt.trim()}`)
  if (data.cityTier) parts.push(`ct:${data.cityTier}`)
  if (data.industry) parts.push(`ind:${data.industry}`)
  parts.push(`lz:${data.lateZishi ? '1' : '0'}`)
  if (data.ziweiBrightnessMethod) parts.push(`zbm:${data.ziweiBrightnessMethod}`)
  if (data.ziweiYoubiMethod) parts.push(`zyb:${data.ziweiYoubiMethod}`)
  if (data.sihuaMethod) parts.push(`zsm:${data.sihuaMethod}`)
  if (data.liunianSihuaMethod) parts.push(`zlsm:${data.liunianSihuaMethod}`)
  if (data.kuiyueMethod) parts.push(`zkm:${data.kuiyueMethod}`)
  if (data.tianmaMethod) parts.push(`ztm:${data.tianmaMethod}`)
  if (data.templateVersion) parts.push(`ztv:${data.templateVersion}`)
  return parts.join(',')
}

function parseFushengTags(tags?: string | string[] | null): Partial<ProfileData> {
  const raw = Array.isArray(tags) ? tags.join(',') : (tags || '')
  const result: Partial<ProfileData> = {}
  for (const part of raw.split(',')) {
    const trimmed = part.trim()
    if (trimmed.startsWith('sn:')) result.surname = trimmed.slice(3)
    else if (trimmed.startsWith('gn:')) result.givenName = trimmed.slice(3)
    else if (trimmed.startsWith('lbd:')) result.lunarBirthDt = trimmed.slice(4)
    else if (trimmed.startsWith('ct:')) result.cityTier = trimmed.slice(3) as ProfileData['cityTier']
    else if (trimmed.startsWith('ind:')) result.industry = trimmed.slice(4) as ProfileData['industry']
    else if (trimmed.startsWith('lz:')) result.lateZishi = trimmed.slice(3) === '1'
    else if (trimmed.startsWith('zbm:')) {
      result.ziweiBrightnessMethod = trimmed.slice(4) as ProfileData['ziweiBrightnessMethod']
    } else if (trimmed.startsWith('zyb:')) {
      result.ziweiYoubiMethod = trimmed.slice(4) as ProfileData['ziweiYoubiMethod']
    } else if (trimmed.startsWith('zsm:')) {
      result.sihuaMethod = trimmed.slice(4) as ProfileData['sihuaMethod']
    } else if (trimmed.startsWith('zlsm:')) {
      result.liunianSihuaMethod = trimmed.slice(5) as ProfileData['liunianSihuaMethod']
    } else if (trimmed.startsWith('zkm:')) {
      result.kuiyueMethod = trimmed.slice(4) as ProfileData['kuiyueMethod']
    } else if (trimmed.startsWith('ztm:')) {
      result.tianmaMethod = trimmed.slice(4) as ProfileData['tianmaMethod']
    } else if (trimmed.startsWith('ztv:')) {
      result.templateVersion = trimmed.slice(4) as ProfileData['templateVersion']
    }
  }
  return result
}

export function profileToCasePayload(data: ProfileData, label: string): CaseCreate {
  const meta = buildChartRequestMeta(data)
  return {
    name: label,
    gender: data.gender === 'female' ? 'female' : data.gender === 'male' ? 'male' : null,
    birth_dt_local: meta.normalizedBirthDt,
    tz: data.tz || 'Asia/Shanghai',
    lon: data.lon ?? 116.41,
    city: data.cityName || null,
    current_city: data.currentCityName || null,
    current_province: data.currentProvince || null,
    current_lon: data.currentLon ?? null,
    current_tz: data.currentTz || null,
    calendar_mode: data.calendarMode,
    is_leap_month: data.isLeapMonth,
    birth_time_precision: data.birthTimePrecision,
    unknown_time_fallback: data.unknownTimeFallback,
    solar_time_enabled: data.solarTime,
    year_divide: data.yearDivide ?? 'lichun',
    day_divide: data.dayDivide ?? 'solar_next',
    zi_day_rule: data.ziDayRule ?? 'sxtwl',
    ziwei_brightness_method: data.ziweiBrightnessMethod ?? 'standard',
    ziwei_youbi_method: data.ziweiYoubiMethod ?? 'month',
    ziwei_sihua_method: data.sihuaMethod ?? 'quanshu',
    ziwei_liunian_sihua_method: data.liunianSihuaMethod ?? 'year_stem',
    ziwei_kuiyue_method: data.kuiyueMethod ?? 'standard',
    ziwei_tianma_method: data.tianmaMethod ?? 'year',
    ziwei_template_version: data.templateVersion ?? 'standard',
    notes: data.focusTopic || null,
    tags: buildFushengTags(data),
  }
}

export function profileToCasePatch(data: ProfileData, label: string): CasePatch {
  return profileToCasePayload(data, label)
}

export function caseOutToProfileData(caseOut: CaseOut): ProfileData {
  const tagMeta = parseFushengTags(caseOut.tags)
  const birthDt = normalizeBirthDtLocal(caseOut.birth_dt_local)
  const gender = caseOut.gender === 'female' ? 'female' : caseOut.gender === 'male' ? 'male' : ''
  const calendarMode = caseOut.calendar_mode === 'lunar' ? 'lunar' : 'gregorian'
  return {
    birthDt,
    lunarBirthDt: tagMeta.lunarBirthDt || (calendarMode === 'lunar' ? '' : ''),
    lon: caseOut.lon,
    cityName: caseOut.city || '',
    province: caseOut.current_province || '',
    tz: caseOut.tz || 'Asia/Shanghai',
    gender,
    mode: 'dual',
    solarTime: caseOut.solar_time_enabled ?? false,
    surname: tagMeta.surname || '',
    givenName: tagMeta.givenName || '',
    calendarMode,
    isLeapMonth: caseOut.is_leap_month ?? false,
    yearDivide: caseOut.year_divide === 'normal' ? 'normal' : 'lichun',
    dayDivide: (caseOut.day_divide as ProfileData['dayDivide']) || 'solar_next',
    ziDayRule: (caseOut.zi_day_rule as ProfileData['ziDayRule']) || 'sxtwl',
    ziweiBrightnessMethod: (caseOut.ziwei_brightness_method as ProfileData['ziweiBrightnessMethod'])
      ?? tagMeta.ziweiBrightnessMethod
      ?? 'standard',
    ziweiYoubiMethod: (caseOut.ziwei_youbi_method as ProfileData['ziweiYoubiMethod'])
      ?? tagMeta.ziweiYoubiMethod
      ?? 'month',
    sihuaMethod: (caseOut.ziwei_sihua_method as ProfileData['sihuaMethod'])
      ?? tagMeta.sihuaMethod
      ?? 'quanshu',
    liunianSihuaMethod: (caseOut.ziwei_liunian_sihua_method as ProfileData['liunianSihuaMethod'])
      ?? tagMeta.liunianSihuaMethod
      ?? 'year_stem',
    kuiyueMethod: (caseOut.ziwei_kuiyue_method as ProfileData['kuiyueMethod'])
      ?? tagMeta.kuiyueMethod
      ?? 'standard',
    tianmaMethod: (caseOut.ziwei_tianma_method as ProfileData['tianmaMethod'])
      ?? tagMeta.tianmaMethod
      ?? 'year',
    templateVersion: (caseOut.ziwei_template_version as ProfileData['templateVersion'])
      ?? tagMeta.templateVersion
      ?? 'standard',
    lateZishi: tagMeta.lateZishi ?? true,
    birthTimePrecision: (caseOut.birth_time_precision as ProfileData['birthTimePrecision']) || 'exact',
    unknownTimeFallback: (caseOut.unknown_time_fallback as ProfileData['unknownTimeFallback']) || 'midday',
    currentCityName: caseOut.current_city || '',
    currentProvince: caseOut.current_province || '',
    currentLon: caseOut.current_lon ?? undefined,
    currentTz: caseOut.current_tz || 'Asia/Shanghai',
    focusTopic: caseOut.notes || '',
    cityTier: tagMeta.cityTier || '',
    industry: tagMeta.industry || '',
  }
}

export function caseOutToProfileLabel(caseOut: CaseOut): string {
  return caseOut.name?.trim() || '云端档案'
}
