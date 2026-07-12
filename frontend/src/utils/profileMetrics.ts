import type { ProfileData } from '@/stores/profile'
import {
  getArchiveBlockerLabel,
  getArchiveBlockers,
  getArchiveCompleteness,
  getArchiveEnhancerLabel,
  getArchiveEnhancers,
  isArchiveReady,
} from '@/utils/profileReadiness'
import { normalizeBirthDateTime, type BirthTimePrecision } from '@/utils/timeNormalization'

export type ProfileFieldKey =
  | 'surname'
  | 'givenName'
  | 'gender'
  | 'birthDt'
  | 'cityName'
  | 'lon'
  | 'calendarMode'
  | 'birthTimePrecision'
  | 'focusTopic'

const FIELD_LABELS: Record<ProfileFieldKey, string> = {
  surname: '姓氏',
  givenName: '名字',
  gender: '性别',
  birthDt: '出生时间',
  cityName: '出生地',
  lon: '经度',
  calendarMode: '历法',
  birthTimePrecision: '时辰精度',
  focusTopic: '关注重点',
}

export function getMissingProfileFields(data: ProfileData): ProfileFieldKey[] {
  const blockers = getArchiveBlockers(data)
  const enhancers = getArchiveEnhancers(data)
  const missing: ProfileFieldKey[] = []
  for (const key of blockers) missing.push(key)
  for (const key of enhancers) missing.push(key)
  return missing
}

export function getProfileCompleteness(data: ProfileData): number {
  return getArchiveCompleteness(data)
}

export function getProfileFieldLabel(key: ProfileFieldKey): string {
  if (key === 'birthDt' || key === 'gender' || key === 'cityName' || key === 'lon') {
    return getArchiveBlockerLabel(key)
  }
  if (key === 'birthTimePrecision' || key === 'calendarMode' || key === 'surname' || key === 'givenName' || key === 'focusTopic') {
    return getArchiveEnhancerLabel(key)
  }
  return FIELD_LABELS[key]
}

export function getTimeConfidence(data: ProfileData) {
  const meta = normalizeBirthDateTime({
    birthDt: data.birthDt || '',
    precision: (data.birthTimePrecision || 'exact') as BirthTimePrecision,
    unknownTimeFallback: data.unknownTimeFallback || 'midday',
    autoDst: true,
  })
  const stars = !isArchiveReady(data) ? 0
    : data.birthTimePrecision === 'exact' ? 3
      : data.birthTimePrecision === 'hour' ? 2
        : data.birthTimePrecision === 'approximate' ? 1
          : 0
  return {
    stars,
    label: meta.timeRiskLabel,
    hint: meta.timeRiskHint,
    dstLabel: meta.dstLabel,
  }
}

export { isArchiveReady, getArchiveBlockers, getArchiveEnhancers }
