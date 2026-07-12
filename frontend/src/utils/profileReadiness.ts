import type { ProfileData } from '@/stores/profile'

export type ArchiveFieldKey =
  | 'birthDt'
  | 'gender'
  | 'cityName'
  | 'lon'

export type EnhancerFieldKey =
  | 'birthTimePrecision'
  | 'calendarMode'
  | 'surname'
  | 'givenName'
  | 'focusTopic'

const BLOCKER_LABELS: Record<ArchiveFieldKey, string> = {
  birthDt: '出生时间',
  gender: '性别',
  cityName: '出生地',
  lon: '经度',
}

const ENHANCER_LABELS: Record<EnhancerFieldKey, string> = {
  birthTimePrecision: '时辰精度',
  calendarMode: '历法',
  surname: '姓氏',
  givenName: '名字',
  focusTopic: '关注重点',
}

const ENHANCER_WEIGHTS: Record<EnhancerFieldKey, number> = {
  birthTimePrecision: 15,
  calendarMode: 10,
  surname: 5,
  givenName: 10,
  focusTopic: 10,
}

function isBlockerFilled(data: ProfileData, key: ArchiveFieldKey): boolean {
  switch (key) {
    case 'birthDt': return !!data.birthDt?.trim()
    case 'gender': return data.gender === 'male' || data.gender === 'female'
    case 'cityName': return !!data.cityName?.trim()
    case 'lon': return data.lon !== undefined && data.lon !== null && Number.isFinite(data.lon)
    default: return false
  }
}

function isEnhancerFilled(data: ProfileData, key: EnhancerFieldKey): boolean {
  switch (key) {
    case 'birthTimePrecision': return !!data.birthTimePrecision
    case 'calendarMode': return !!data.calendarMode
    case 'surname': return !!data.surname?.trim()
    case 'givenName': return !!data.givenName?.trim()
    case 'focusTopic': return !!data.focusTopic?.trim()
    default: return false
  }
}

/** 阻断排盘的必填项 */
export function getArchiveBlockers(data: ProfileData): ArchiveFieldKey[] {
  const keys: ArchiveFieldKey[] = ['birthDt', 'gender', 'cityName', 'lon']
  return keys.filter((key) => !isBlockerFilled(data, key))
}

export function isArchiveReady(data: ProfileData): boolean {
  return getArchiveBlockers(data).length === 0
}

export function getArchiveEnhancers(data: ProfileData): EnhancerFieldKey[] {
  const keys: EnhancerFieldKey[] = ['birthTimePrecision', 'calendarMode', 'surname', 'givenName', 'focusTopic']
  return keys.filter((key) => !isEnhancerFilled(data, key))
}

/** 完整度仅统计增强项；阻断项未齐时返回 0 */
export function getArchiveCompleteness(data: ProfileData): number {
  if (!isArchiveReady(data)) return 0
  const total = Object.values(ENHANCER_WEIGHTS).reduce((sum, w) => sum + w, 0)
  const score = (Object.keys(ENHANCER_WEIGHTS) as EnhancerFieldKey[]).reduce((sum, key) => {
    return sum + (isEnhancerFilled(data, key) ? ENHANCER_WEIGHTS[key] : 0)
  }, 0)
  return Math.round((score / total) * 100)
}

export function getArchiveBlockerLabel(key: ArchiveFieldKey): string {
  return BLOCKER_LABELS[key]
}

export function getArchiveEnhancerLabel(key: EnhancerFieldKey): string {
  return ENHANCER_LABELS[key]
}

export function canAnalyzeName(data: ProfileData): boolean {
  return !!data.surname?.trim() && !!data.givenName?.trim()
}

/** 是否仍为出厂演示数据（应禁止排盘） */
export function isDemoSeedProfile(data: ProfileData): boolean {
  return data.birthDt === '1990-01-15T08:30'
    && data.cityName === '北京'
    && data.lon === 116.41
    && data.gender === 'male'
    && !data.surname
    && !data.focusTopic
}
