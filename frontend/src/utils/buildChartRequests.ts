import type { BaziRequest } from '@/api/bazi'
import type { FushengReportPdfRequest } from '@/api/fushengReport'
import type { ZiweiRequest } from '@/api/ziwei'
import type { ProfileData } from '@/stores/profile'
import { normalizeBirthDateTime } from '@/utils/timeNormalization'

export type ChartRequestMeta = {
  normalizedBirthDt: string
  timeRiskLabel: string
  timeRiskHint: string
  dstLabel: string
  calendarNote: string
  yearDivideNote: string
  precisionLabel: string
}

function applyUnknownTimeFallback(
  birthDt: string,
  fallback: ProfileData['unknownTimeFallback'],
): string {
  const [datePart] = birthDt.split('T')
  const hour = fallback === 'noon' ? 12 : fallback === 'midday' ? 12 : 0
  const minute = fallback === 'start_of_hour' ? 0 : 30
  return `${datePart}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`
}

export function buildChartRequestMeta(data: ProfileData): ChartRequestMeta {
  const precision = data.birthTimePrecision || 'exact'
  let effectiveBirthDt = data.birthDt
  if (precision === 'unknown') {
    effectiveBirthDt = applyUnknownTimeFallback(data.birthDt, data.unknownTimeFallback || 'midday')
  }

  const normalized = normalizeBirthDateTime({
    birthDt: effectiveBirthDt,
    precision,
    unknownTimeFallback: data.unknownTimeFallback || 'midday',
  })

  const dayDivideNote = data.dayDivide === 'forward'
    ? '换日：子时换日（forward，对齐 iztro）。'
    : data.dayDivide === 'current'
      ? '换日：当日子时（current）。'
      : '换日：公历次日换日（solar_next，默认）。'

  const calendarNote = data.calendarMode === 'lunar'
    ? `农历模式：录入农历后保存自动转公历排盘；${data.isLeapMonth ? '已标记闰月。' : '未标记闰月。'}`
    : '公历模式：出生时间按公历录入。'
  const yearDivideNote = data.yearDivide === 'normal'
    ? '紫微年界：正月初一换年。'
    : '紫微年界：立春换年（默认）。'

  const precisionLabel = precision === 'exact' ? '精确到分'
    : precision === 'hour' ? '只知时辰'
      : precision === 'approximate' ? '大致时间'
        : `未知时辰（兜底：${data.unknownTimeFallback || 'midday'}）`

  return {
    normalizedBirthDt: normalized.normalizedBirthDt,
    timeRiskLabel: normalized.timeRiskLabel,
    timeRiskHint: normalized.timeRiskHint,
    dstLabel: normalized.dstLabel,
    calendarNote: `${calendarNote} ${yearDivideNote} ${dayDivideNote}`,
    yearDivideNote,
    precisionLabel,
  }
}

function normalizeTargetDate(targetDate?: string): string | undefined {
  if (!targetDate?.trim()) return undefined
  const trimmed = targetDate.trim()
  if (trimmed.includes('T')) return trimmed
  return `${trimmed}T00:00:00`
}

function liunianYearFromTargetDate(targetDate?: string, fallback?: number): number {
  if (!targetDate?.trim()) return fallback ?? new Date().getFullYear()
  const parsed = new Date(normalizeTargetDate(targetDate)!)
  if (Number.isNaN(parsed.getTime())) return fallback ?? new Date().getFullYear()
  return parsed.getFullYear()
}

/** 与后端 `_default_liunian_years` 对齐：±2 年偏移 + 当前日历年 */
export function buildDefaultLiunianYearOffsets(birthYear: number, calendarYear = new Date().getFullYear()): number[] {
  const deltas = new Set<number>([-2, -1, 0, 1, 2])
  deltas.add(calendarYear - birthYear)
  return [...deltas].sort((a, b) => a - b)
}

function birthYearFromIsoDt(dt: string): number {
  const year = Number.parseInt(dt.slice(0, 4), 10)
  return Number.isFinite(year) ? year : new Date().getFullYear()
}

export function buildBaziRequest(data: ProfileData, targetDate?: string): BaziRequest {
  const meta = buildChartRequestMeta(data)
  const normalizedTargetDate = normalizeTargetDate(targetDate)
  const calendarYear = liunianYearFromTargetDate(targetDate)
  const birthYear = birthYearFromIsoDt(meta.normalizedBirthDt)
  return {
    dt: meta.normalizedBirthDt,
    lon: data.lon ?? 116.41,
    tz: data.tz || 'Asia/Shanghai',
    mode: data.mode || 'dual',
    solar_time_enabled: data.solarTime ?? false,
    ...(data.gender === 'male' || data.gender === 'female' ? { gender: data.gender } : {}),
    zi_day_rule: data.ziDayRule ?? 'sxtwl',
    birth_time_precision: data.birthTimePrecision || 'exact',
    ...(data.cityTier ? { city_tier: data.cityTier } : {}),
    ...(data.industry ? { industry: data.industry } : {}),
    include_liuri: true,
    liunian_years: buildDefaultLiunianYearOffsets(birthYear, calendarYear),
    ...(normalizedTargetDate ? { target_date: normalizedTargetDate } : {}),
  }
}

export function buildZiweiRequest(
  data: ProfileData,
  liunianYear?: number,
  targetDate?: string,
): ZiweiRequest {
  const meta = buildChartRequestMeta(data)
  const [datePart, timePart = '08:30:00'] = meta.normalizedBirthDt.split('T')
  const [y, m, d] = datePart.split('-').map(Number)
  const [hh, mm] = timePart.split(':').map(Number)
  const gender: '男' | '女' | undefined = data.gender === 'female' ? '女' : data.gender === 'male' ? '男' : undefined

  const lon = data.lon ?? 116.41
  const normalizedTargetDate = normalizeTargetDate(targetDate)
  const resolvedLiunianYear = liunianYearFromTargetDate(targetDate, liunianYear ?? new Date().getFullYear())
  const flowMonth = normalizedTargetDate ? Number(normalizedTargetDate.slice(5, 7)) : undefined
  const flowDay = normalizedTargetDate ? Number(normalizedTargetDate.slice(8, 10)) : undefined
  const sihuaStemIndices = data.sihuaMethod === 'zhongzhou'
    ? { 庚: 1, 辛: 1 }
    : undefined

  return {
    year: y,
    month: m,
    day: d,
    hour: hh,
    minute: mm || 0,
    ...(gender ? { gender } : {}),
    liunian_year: resolvedLiunianYear,
    ...(data.solarTime ? { longitude: lon } : {}),
    template_version: data.templateVersion ?? 'standard',
    leap_month_method: data.isLeapMonth ? 'same' : 'mid',
    year_divide: data.yearDivide ?? 'lichun',
    day_divide: data.dayDivide ?? 'solar_next',
    late_zishi: data.lateZishi ?? true,
    brightness_method: data.ziweiBrightnessMethod ?? 'standard',
    youbi_method: data.ziweiYoubiMethod ?? 'month',
    liunian_sihua_method: data.liunianSihuaMethod ?? 'year_stem',
    kuiyue_method: data.kuiyueMethod ?? 'standard',
    tianma_method: data.tianmaMethod ?? 'year',
    ...(sihuaStemIndices ? { sihua_stem_indices: sihuaStemIndices } : {}),
    ...(flowDay != null && !Number.isNaN(flowDay) ? { flow_lunar_day: flowDay } : {}),
    ...(flowMonth != null && !Number.isNaN(flowMonth) ? { flow_liuyue_month: flowMonth } : {}),
    include_flow_liuri: true,
    ...(normalizedTargetDate ? { target_date: normalizedTargetDate } : {}),
  }
}

export function buildFushengReportPdfRequest(
  data: ProfileData,
  extras: { label: string; notes?: string },
): FushengReportPdfRequest {
  const meta = buildChartRequestMeta(data)
  return {
    label: extras.label,
    birth_dt: meta.normalizedBirthDt,
    lon: data.lon ?? 116.41,
    tz: data.tz || 'Asia/Shanghai',
    gender: data.gender === 'female' ? 'female' : data.gender === 'male' ? 'male' : undefined,
    solar_time_enabled: data.solarTime ?? false,
    mode: data.mode || 'dual',
    city_name: data.cityName,
    calendar_mode: data.calendarMode,
    is_leap_month: data.isLeapMonth,
    year_divide: data.yearDivide ?? 'lichun',
    day_divide: data.dayDivide ?? 'solar_next',
    late_zishi: data.lateZishi ?? true,
    zi_day_rule: data.ziDayRule ?? 'sxtwl',
    birth_time_precision: data.birthTimePrecision,
    unknown_time_fallback: data.unknownTimeFallback,
    include_liuri: true,
    surname: data.surname,
    given_name: data.givenName,
    focus_topic: data.focusTopic,
    notes: extras.notes,
  }
}

export type ProfileSignatureOptions = {
  /** Timeline / session target date for ziwei flow cache invalidation */
  timelineTargetDate?: string
}

export function buildProfileSignature(data: ProfileData, options?: ProfileSignatureOptions): string {
  return JSON.stringify({
    birthDt: data.birthDt,
    lon: data.lon,
    tz: data.tz,
    gender: data.gender,
    mode: data.mode,
    solarTime: data.solarTime,
    calendarMode: data.calendarMode,
    isLeapMonth: data.isLeapMonth,
    lunarBirthDt: data.lunarBirthDt,
    yearDivide: data.yearDivide ?? 'lichun',
    dayDivide: data.dayDivide ?? 'solar_next',
    lateZishi: data.lateZishi ?? true,
    ziDayRule: data.ziDayRule ?? 'sxtwl',
    ziweiBrightnessMethod: data.ziweiBrightnessMethod ?? 'standard',
    ziweiYoubiMethod: data.ziweiYoubiMethod ?? 'month',
    sihuaMethod: data.sihuaMethod ?? 'quanshu',
    liunianSihuaMethod: data.liunianSihuaMethod ?? 'year_stem',
    kuiyueMethod: data.kuiyueMethod ?? 'standard',
    tianmaMethod: data.tianmaMethod ?? 'year',
    templateVersion: data.templateVersion ?? 'standard',
    birthTimePrecision: data.birthTimePrecision,
    unknownTimeFallback: data.unknownTimeFallback,
    surname: data.surname,
    givenName: data.givenName,
    cityTier: data.cityTier,
    industry: data.industry,
    ...(options?.timelineTargetDate ? { timelineTargetDate: options.timelineTargetDate } : {}),
  })
}

export function buildZiweiCacheKey(data: ProfileData, targetDate?: string): string {
  return buildProfileSignature(data, {
    timelineTargetDate: normalizeTargetDate(targetDate) ?? '',
  })
}

/** 合盘/多人矩阵：由 datetime-local + 经度构造 ZiweiRequest（继承档案紫微口径） */
export function birthDatetimeToZiweiRequest(
  birthDtLocal: string,
  gender: string,
  lon: number,
  defaults: ProfileData,
): ZiweiRequest {
  const normalized = birthDtLocal.trim().includes('T')
    ? (birthDtLocal.trim().length === 16 ? `${birthDtLocal.trim()}:00` : birthDtLocal.trim())
    : birthDtLocal.trim()
  const [datePart, timePart = '08:30:00'] = normalized.split('T')
  const [year, month, day] = datePart.split('-').map(Number)
  const [hour, minute = 0] = timePart.split(':').map(Number)
  const genderZiwei = gender === 'female' ? '女' : gender === 'male' ? '男' : gender

  return {
    year,
    month,
    day,
    hour,
    minute: minute || 0,
    gender: genderZiwei,
    longitude: lon,
    liunian_year: new Date().getFullYear(),
    template_version: defaults.templateVersion ?? 'standard',
    late_zishi: defaults.lateZishi ?? true,
    year_divide: defaults.yearDivide ?? 'lichun',
    day_divide: defaults.dayDivide ?? 'solar_next',
    brightness_method: defaults.ziweiBrightnessMethod ?? 'standard',
    youbi_method: defaults.ziweiYoubiMethod ?? 'month',
    liunian_sihua_method: defaults.liunianSihuaMethod ?? 'year_stem',
    kuiyue_method: defaults.kuiyueMethod ?? 'standard',
    tianma_method: defaults.tianmaMethod ?? 'year',
  }
}
