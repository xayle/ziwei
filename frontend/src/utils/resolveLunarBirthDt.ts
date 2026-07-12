import { lunarToSolar } from '@/api/bazi'
import type { ProfileData } from '@/stores/profile'

export type LunarResolveResult = {
  birthDt: string
  lunarLabel?: string
  warning?: string
}

export async function resolveLunarBirthDt(data: ProfileData): Promise<LunarResolveResult> {
  if (data.calendarMode !== 'lunar') {
    return { birthDt: data.birthDt }
  }

  const lunarInput = (data.lunarBirthDt?.trim() || data.birthDt?.trim())
  if (!lunarInput) {
    return { birthDt: data.birthDt }
  }

  const [datePart, timePart = '12:00'] = lunarInput.split('T')
  const [y, m, d] = datePart.split('-').map(Number)
  const [hh, mm] = timePart.split(':').map(Number)
  if (![y, m, d].every(Number.isFinite)) {
    return { birthDt: data.birthDt, warning: '农历日期格式无效，未做公历转换。' }
  }

  try {
    const res = await lunarToSolar({
      lunar_year: y,
      lunar_month: m,
      lunar_day: d,
      hour: Number.isFinite(hh) ? hh : 12,
      minute: Number.isFinite(mm) ? mm : 0,
      is_leap_month: data.isLeapMonth,
    })
    return {
      birthDt: res.solar_dt,
      lunarLabel: res.lunar_label,
      warning: res.warnings?.length ? res.warnings.join('；') : undefined,
    }
  } catch {
    return {
      birthDt: data.birthDt,
      warning: '农历转公历失败，请检查农历年月日是否正确。',
    }
  }
}
