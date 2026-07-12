import type { DayunItem } from '@/api/bazi'

export function formatYongshenShift(shift?: string | null): string {
  switch (shift) {
    case 'forward':
      return '用神得运（进）'
    case 'backward':
      return '忌神当令（退）'
    case 'neutral':
      return '用神进退中性'
    default:
      return ''
  }
}

export function computeDayunEndAge(
  items: Array<{ start_age?: number | null }>,
  index: number,
): number | undefined {
  const current = items[index]
  if (current?.start_age == null || !Number.isFinite(Number(current.start_age))) return undefined
  const next = items[index + 1]
  if (next?.start_age != null && Number.isFinite(Number(next.start_age))) {
    return Math.round(Number(next.start_age)) - 1
  }
  return Math.round(Number(current.start_age)) + 9
}

/** Integer age label for life-volume / report copy (avoids `0.0岁起`). */
export function formatDayunStartAge(age?: number | null): string {
  if (age == null || !Number.isFinite(Number(age))) return ''
  return `${Math.round(Number(age))}岁起`
}

export function formatDayunAgeRange(start?: number | null, end?: number | null): string {
  if (start == null || !Number.isFinite(Number(start))) return ''
  const startRounded = Math.round(Number(start))
  if (end != null && Number.isFinite(Number(end))) {
    return `${startRounded}–${Math.round(Number(end))}岁`
  }
  return `${startRounded}岁起`
}

export function buildDayunVolumeText(
  item: DayunItem,
  index: number,
  items: DayunItem[],
): string {
  const ganzhi = `${item.stem ?? ''}${item.branch ?? ''}`.trim() || '—'
  const endAge = computeDayunEndAge(items, index)
  const ageRange = item.start_age != null && endAge != null
    ? formatDayunAgeRange(item.start_age, endAge)
    : formatDayunStartAge(item.start_age)
  const yearRange = item.start_year != null
    ? `${item.start_year}–${item.start_year + 9}年`
    : ''
  const tenGod = item.ten_god?.trim()
  const shift = formatYongshenShift(item.yongshen_shift)
  const narrative = item.narrative?.trim()
  const hints = [
    item.geju_impact?.trim(),
    item.wealth_hint?.trim(),
    item.health_hint?.trim(),
    item.love_hint?.trim(),
  ].filter(Boolean) as string[]

  const head = [
    `${index + 1}. ${ganzhi}`,
    ageRange,
    yearRange,
    tenGod ? `十神 ${tenGod}` : '',
    shift,
    item.nayin?.trim() ? `纳音 ${item.nayin}` : '',
  ].filter(Boolean).join(' · ')

  if (narrative && narrative.length >= 20) {
    return `${head}。${narrative}`
  }
  if (hints.length) {
    return `${head}。${hints.join('；')}`
  }
  if (narrative) {
    return `${head}。${narrative}`
  }
  return head
}

export function buildDayunDisplayRow(item: DayunItem, extras?: {
  range?: string
  narrative?: string
  tenGod?: string
}) {
  const ganzhi = `${item.stem || ''}${item.branch || ''}`.trim() || '—'
  return {
    ganzhi,
    range: extras?.range || '—',
    tenGod: extras?.tenGod || item.ten_god || '—',
    gejuImpact: item.geju_impact || '',
    yongshenShift: item.yongshen_shift || '',
    yongshenShiftLabel: formatYongshenShift(item.yongshen_shift),
    wealthHint: item.wealth_hint || '',
    healthHint: item.health_hint || '',
    loveHint: item.love_hint || '',
    narrative: extras?.narrative || item.narrative || '',
    hasEngineHints: !!(item.geju_impact || item.yongshen_shift),
    hasHeuristicHints: !!(item.wealth_hint || item.health_hint || item.love_hint),
  }
}

export type DayunDisplayRow = ReturnType<typeof buildDayunDisplayRow>
