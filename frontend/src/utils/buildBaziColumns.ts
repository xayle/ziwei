import type { BaziResponse } from '@/api/bazi'

export type PillarKey = 'liunian' | 'dayun' | 'year' | 'month' | 'day' | 'hour'

export type HiddenStemLine = { stem: string; tenGod: string }

export type BaziColumn = {
  key: PillarKey
  label: string
  mainStar?: string
  stem?: string
  branch?: string
  hiddenStems?: HiddenStemLine[]
  xingyun?: string
  selfSeat?: string
  void?: string
  nayin?: string
  shensha?: string[]
}

type DayunItem = NonNullable<NonNullable<BaziResponse['dayun']>['items']>[number]

function textOrMissing(value?: string | null): string {
  const trimmed = value?.trim()
  return trimmed ? trimmed : '缺失'
}

function findCurrentDayun(result: BaziResponse, currentYear: number): DayunItem | undefined {
  const items = result.dayun?.items ?? result.dayun?.cycles ?? []
  return items.find((item) => {
    const startYear = item.start_year ?? 0
    return startYear <= currentYear && currentYear <= startYear + 9
  }) ?? items[0]
}

export function buildFallbackBaziColumns(): BaziColumn[] {
  return [
    { key: 'liunian', label: '流年', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
    { key: 'dayun', label: '大运', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
    { key: 'year', label: '年柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
    { key: 'month', label: '月柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
    { key: 'day', label: '日柱', mainStar: '日主', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
    { key: 'hour', label: '时柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: ['接口不可用'] },
  ]
}

export function buildBaziColumns(result: BaziResponse | null, currentYear = new Date().getFullYear()): BaziColumn[] {
  if (!result) return buildFallbackBaziColumns()

  const currentDayun = findCurrentDayun(result, currentYear)
  const liunianItem = (result.liunian?.items ?? []).find((item) => item.year === currentYear)
  const pillarDetails = result.pillar_details ?? {}
  const yearItem = result.pillars_primary?.year
  const monthItem = result.pillars_primary?.month
  const dayItem = result.pillars_primary?.day
  const hourItem = result.pillars_primary?.hour
  const kongwang = result.kongwang?.length ? result.kongwang.join('、') : '缺失'
  const liunianDetail = liunianItem as unknown as { hidden_stems?: HiddenStemLine[]; xingyun?: string; self_seat?: string; nayin?: string; shensha?: Array<{ name?: string }> } | undefined
  const dayunDetail = currentDayun as unknown as { hidden_stems?: HiddenStemLine[]; xingyun?: string; self_seat?: string; nayin?: string; shensha?: Array<{ name?: string }> } | undefined

  return [
    {
      key: 'liunian',
      label: '流年',
      mainStar: liunianItem?.ten_god || result.current_fortune_summary?.current_liunian,
      stem: liunianItem?.stem || '',
      branch: liunianItem?.branch || '',
      hiddenStems: liunianDetail?.hidden_stems,
      xingyun: liunianDetail?.xingyun,
      selfSeat: liunianDetail?.self_seat ?? '缺失',
      void: kongwang,
      nayin: liunianDetail?.nayin ?? '缺失',
      shensha: liunianDetail?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
    {
      key: 'dayun',
      label: '大运',
      mainStar: currentDayun?.ten_god,
      stem: currentDayun?.stem || '',
      branch: currentDayun?.branch || '',
      hiddenStems: dayunDetail?.hidden_stems,
      xingyun: dayunDetail?.xingyun,
      selfSeat: dayunDetail?.self_seat ?? '缺失',
      void: kongwang,
      nayin: dayunDetail?.nayin ?? '缺失',
      shensha: dayunDetail?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
    {
      key: 'year',
      label: '年柱',
      mainStar: result.ten_gods?.year,
      stem: yearItem?.stem || '',
      branch: yearItem?.branch || '',
      hiddenStems: pillarDetails.year?.hidden_stems,
      xingyun: pillarDetails.year?.xingyun,
      selfSeat: pillarDetails.year?.self_seat ?? '缺失',
      void: kongwang,
      nayin: pillarDetails.year?.nayin ?? '缺失',
      shensha: pillarDetails.year?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
    {
      key: 'month',
      label: '月柱',
      mainStar: result.ten_gods?.month,
      stem: monthItem?.stem || '',
      branch: monthItem?.branch || '',
      hiddenStems: pillarDetails.month?.hidden_stems,
      xingyun: pillarDetails.month?.xingyun,
      selfSeat: pillarDetails.month?.self_seat ?? '缺失',
      void: kongwang,
      nayin: pillarDetails.month?.nayin ?? '缺失',
      shensha: pillarDetails.month?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
    {
      key: 'day',
      label: '日柱',
      mainStar: '日主',
      stem: dayItem?.stem || '',
      branch: dayItem?.branch || '',
      hiddenStems: pillarDetails.day?.hidden_stems,
      xingyun: pillarDetails.day?.xingyun,
      selfSeat: pillarDetails.day?.self_seat ?? textOrMissing(dayItem?.branch),
      void: kongwang,
      nayin: pillarDetails.day?.nayin ?? '缺失',
      shensha: pillarDetails.day?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
    {
      key: 'hour',
      label: '时柱',
      mainStar: result.ten_gods?.hour,
      stem: hourItem?.stem || '',
      branch: hourItem?.branch || '',
      hiddenStems: pillarDetails.hour?.hidden_stems,
      xingyun: pillarDetails.hour?.xingyun,
      selfSeat: pillarDetails.hour?.self_seat ?? '缺失',
      void: kongwang,
      nayin: pillarDetails.hour?.nayin ?? '缺失',
      shensha: pillarDetails.hour?.shensha?.map((item) => item.name || '').filter(Boolean) || ['缺失'],
    },
  ]
}
