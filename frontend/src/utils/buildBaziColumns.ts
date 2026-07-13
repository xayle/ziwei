import type { BaziResponse } from '@/api/bazi'

export type PillarKey = 'liunian' | 'dayun' | 'year' | 'month' | 'day' | 'hour'

export type HiddenStemLine = { stem: string; tenGod: string }

export type ShenshaChip = {
  name: string
  polarity?: string | null
}

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
  shensha?: ShenshaChip[]
}

type DayunItem = NonNullable<NonNullable<BaziResponse['dayun']>['items']>[number]

type ApiHiddenStem = { stem?: string; ten_god?: string | null; tenGod?: string | null }
type ApiShensha = { name?: string; polarity?: string | null }

function textOrMissing(value?: string | null): string {
  const trimmed = value?.trim()
  return trimmed ? trimmed : '缺失'
}

export function formatKongwangDisplay(kongwang?: string[] | null): string {
  if (!kongwang?.length) return '缺失'
  const items = [...new Set(kongwang.map((k) => k.trim()).filter(Boolean))]
  if (!items.length) return '缺失'
  if (items.every((k) => k === '未知')) return '未知'
  return items.join('、')
}

function mapHiddenStems(stems?: ApiHiddenStem[] | null): HiddenStemLine[] | undefined {
  if (!stems?.length) return undefined
  return stems.map((item) => ({
    stem: item.stem?.trim() || '',
    tenGod: item.ten_god?.trim() || item.tenGod?.trim() || '',
  }))
}

function mapShensha(items?: ApiShensha[] | null): ShenshaChip[] {
  if (!items?.length) return []
  return items
    .map((item) => ({
      name: item.name?.trim() || '',
      polarity: item.polarity ?? null,
    }))
    .filter((item) => item.name)
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
    { key: 'liunian', label: '流年', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
    { key: 'dayun', label: '大运', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
    { key: 'year', label: '年柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
    { key: 'month', label: '月柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
    { key: 'day', label: '日柱', mainStar: '日主', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
    { key: 'hour', label: '时柱', mainStar: '待计算', stem: '待计算', branch: '待计算', selfSeat: '待计算', void: '待计算', nayin: '待计算', shensha: [{ name: '接口不可用' }] },
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
  const dayKongwang = formatKongwangDisplay(result.kongwang)
  const pillarVoid = (kongwang?: string[] | null) => formatKongwangDisplay(kongwang) || dayKongwang
  const liunianDetail = liunianItem as unknown as {
    hidden_stems?: ApiHiddenStem[]
    xingyun?: string
    self_seat?: string
    kongwang?: string[]
    nayin?: string
    shensha?: ApiShensha[]
  } | undefined
  const dayunDetail = currentDayun as unknown as {
    hidden_stems?: ApiHiddenStem[]
    xingyun?: string
    self_seat?: string
    kongwang?: string[]
    nayin?: string
    shensha?: ApiShensha[]
  } | undefined

  const shenshaOrMissing = (items?: ApiShensha[] | null) => {
    const mapped = mapShensha(items)
    return mapped.length ? mapped : [{ name: '缺失' }]
  }

  return [
    {
      key: 'liunian',
      label: '流年',
      mainStar: textOrMissing(liunianItem?.ten_god),
      stem: liunianItem?.stem || '',
      branch: liunianItem?.branch || '',
      hiddenStems: mapHiddenStems(liunianDetail?.hidden_stems),
      xingyun: liunianDetail?.xingyun,
      selfSeat: liunianDetail?.self_seat ?? '缺失',
      void: pillarVoid(liunianDetail?.kongwang),
      nayin: liunianDetail?.nayin ?? '缺失',
      shensha: shenshaOrMissing(liunianDetail?.shensha),
    },
    {
      key: 'dayun',
      label: '大运',
      mainStar: currentDayun?.ten_god,
      stem: currentDayun?.stem || '',
      branch: currentDayun?.branch || '',
      hiddenStems: mapHiddenStems(dayunDetail?.hidden_stems),
      xingyun: dayunDetail?.xingyun,
      selfSeat: dayunDetail?.self_seat ?? '缺失',
      void: pillarVoid(dayunDetail?.kongwang),
      nayin: dayunDetail?.nayin ?? '缺失',
      shensha: shenshaOrMissing(dayunDetail?.shensha),
    },
    {
      key: 'year',
      label: '年柱',
      mainStar: result.ten_gods?.year,
      stem: yearItem?.stem || '',
      branch: yearItem?.branch || '',
      hiddenStems: mapHiddenStems(pillarDetails.year?.hidden_stems),
      xingyun: pillarDetails.year?.xingyun,
      selfSeat: pillarDetails.year?.self_seat ?? '缺失',
      void: pillarVoid(pillarDetails.year?.kongwang),
      nayin: pillarDetails.year?.nayin ?? '缺失',
      shensha: shenshaOrMissing(pillarDetails.year?.shensha),
    },
    {
      key: 'month',
      label: '月柱',
      mainStar: result.ten_gods?.month,
      stem: monthItem?.stem || '',
      branch: monthItem?.branch || '',
      hiddenStems: mapHiddenStems(pillarDetails.month?.hidden_stems),
      xingyun: pillarDetails.month?.xingyun,
      selfSeat: pillarDetails.month?.self_seat ?? '缺失',
      void: pillarVoid(pillarDetails.month?.kongwang),
      nayin: pillarDetails.month?.nayin ?? '缺失',
      shensha: shenshaOrMissing(pillarDetails.month?.shensha),
    },
    {
      key: 'day',
      label: '日柱',
      mainStar: '日主',
      stem: dayItem?.stem || '',
      branch: dayItem?.branch || '',
      hiddenStems: mapHiddenStems(pillarDetails.day?.hidden_stems),
      xingyun: pillarDetails.day?.xingyun,
      selfSeat: pillarDetails.day?.self_seat ?? textOrMissing(dayItem?.branch),
      void: pillarVoid(pillarDetails.day?.kongwang),
      nayin: pillarDetails.day?.nayin ?? '缺失',
      shensha: shenshaOrMissing(pillarDetails.day?.shensha),
    },
    {
      key: 'hour',
      label: '时柱',
      mainStar: result.ten_gods?.hour,
      stem: hourItem?.stem || '',
      branch: hourItem?.branch || '',
      hiddenStems: mapHiddenStems(pillarDetails.hour?.hidden_stems),
      xingyun: pillarDetails.hour?.xingyun,
      selfSeat: pillarDetails.hour?.self_seat ?? '缺失',
      void: pillarVoid(pillarDetails.hour?.kongwang),
      nayin: pillarDetails.hour?.nayin ?? '缺失',
      shensha: shenshaOrMissing(pillarDetails.hour?.shensha),
    },
  ]
}
