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
