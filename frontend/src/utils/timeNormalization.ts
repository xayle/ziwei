export type BirthTimePrecision = 'exact' | 'hour' | 'approximate' | 'unknown'

export type UnknownTimeFallback = 'midday' | 'noon' | 'start_of_hour'

export type TimeNormalizationResult = {
  normalizedBirthDt: string
  isPotentialChinaDst: boolean
  dstAdjustmentMinutes: number
  dstLabel: string
  timeRiskLabel: string
  timeRiskHint: string
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function formatLocalDateTime(dt: Date): string {
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}:00`
}

function formatLocalDateTimeParts(parts: {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  second?: number
}): string {
  return `${parts.year}-${pad(parts.month)}-${pad(parts.day)}T${pad(parts.hour)}:${pad(parts.minute)}:${pad(parts.second ?? 0)}`
}

function parseLocalDateTime(value: string): Date | null {
  if (!value) return null
  const raw = value.trim().replace(' ', 'T')
  const match = raw.match(
    /^(?<year>\d{4})-(?<month>\d{1,2})-(?<day>\d{1,2})T(?<hour>\d{1,2}):(?<minute>\d{1,2})(?::(?<second>\d{1,2}))?$/,
  )
  if (!match?.groups) return null
  const year = Number(match.groups.year)
  const month = Number(match.groups.month)
  const day = Number(match.groups.day)
  const hour = Number(match.groups.hour)
  const minute = Number(match.groups.minute)
  const second = Number(match.groups.second ?? '0')
  if ([year, month, day, hour, minute, second].some(part => !Number.isFinite(part))) return null
  const dt = new Date(year, month - 1, day, hour, minute, second)
  if (
    dt.getFullYear() !== year
    || dt.getMonth() !== month - 1
    || dt.getDate() !== day
    || dt.getHours() !== hour
    || dt.getMinutes() !== minute
    || dt.getSeconds() !== second
  ) {
    return null
  }
  return dt
}

function getFirstSundayOnOrAfter(year: number, monthIndex: number, dayOfMonth: number): Date {
  const start = new Date(year, monthIndex, dayOfMonth)
  const offset = (7 - start.getDay()) % 7
  return new Date(year, monthIndex, dayOfMonth + offset)
}

function getChinaDstWindow(year: number): { start: string; end: string } | null {
  if (year < 1986 || year > 1991) return null
  if (year === 1986) {
    return {
      start: '1986-05-04T02:00:00',
      end: '1986-09-14T02:00:00',
    }
  }
  if (year === 1991) {
    return {
      start: '1991-04-14T02:00:00',
      end: '1991-09-15T02:00:00',
    }
  }
  return {
    start: formatLocalDateTimeParts({
      year,
      month: 4,
      day: getFirstSundayOnOrAfter(year, 3, 10).getDate(),
      hour: 2,
      minute: 0,
    }),
    end: formatLocalDateTimeParts({
      year,
      month: 9,
      day: getFirstSundayOnOrAfter(year, 8, 10).getDate(),
      hour: 2,
      minute: 0,
    }),
  }
}

function isChinaDstDate(dt: Date): boolean {
  const window = getChinaDstWindow(dt.getFullYear())
  if (!window) return false
  const iso = formatLocalDateTime(dt)
  return iso >= window.start && iso < window.end
}

function describeTimeRisk(precision: BirthTimePrecision, fallback: UnknownTimeFallback, isDst: boolean): { label: string; hint: string } {
  if (precision === 'unknown') {
    return {
      label: '未知时辰',
      hint: `已启用兜底策略：${fallback === 'midday' ? '按日中 12:30' : fallback === 'noon' ? '按正午 12:00' : '按当日零点'}。`,
    }
  }
  if (precision === 'hour') {
    return {
      label: '仅知时辰',
      hint: '当前只知道时辰，遇到时辰交界时建议补分钟级时间。',
    }
  }
  if (precision === 'approximate') {
    return {
      label: '大致时间',
      hint: '当前时间为近似值，接近时辰边界时请优先核对原始记录。',
    }
  }
  return {
    label: isDst ? '精确时间，含夏令时风险' : '精确时间',
    hint: isDst ? '该时间落在中国历史夏令时窗口内，后端排盘时将按历史夏令时识别。' : '当前时间可直接用于排盘。',
  }
}

export function normalizeBirthDateTime(input: {
  birthDt: string
  precision?: BirthTimePrecision
  unknownTimeFallback?: UnknownTimeFallback
  /** @deprecated 前端不再回拨夏令时，避免与后端 auto_dst 双重修正 */
  autoDst?: boolean
}): TimeNormalizationResult {
  const precision = input.precision ?? 'exact'
  const fallback = input.unknownTimeFallback ?? 'midday'
  const parsed = parseLocalDateTime(input.birthDt)
  const normalizedBirthDt = parsed ? formatLocalDateTime(parsed) : input.birthDt
  const isDstWindow = !!(parsed && isChinaDstDate(parsed))
  const risk = describeTimeRisk(precision, fallback, isDstWindow)

  return {
    normalizedBirthDt,
    isPotentialChinaDst: isDstWindow,
    dstAdjustmentMinutes: 0,
    dstLabel: isDstWindow ? '落在中国历史夏令时窗口，由后端排盘识别' : '未触发历史夏令时窗口',
    timeRiskLabel: risk.label,
    timeRiskHint: risk.hint,
  }
}
