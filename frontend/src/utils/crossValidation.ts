import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'

export type CrossValidationItem = {
  label: string
  status: 'pass' | 'warn' | 'fail'
  detail: string
}

export type CrossValidationResult = {
  overall: 'pass' | 'warn' | 'fail'
  items: CrossValidationItem[]
}

function pillarText(stem?: string, branch?: string): string {
  return `${stem || ''}${branch || ''}`.trim()
}

export function validateBaziZiweiConsistency(
  bazi: BaziResponse | null,
  ziwei: ZiweiResponse | null,
): CrossValidationResult {
  if (!bazi || !ziwei) {
    return {
      overall: 'fail',
      items: [{ label: '数据完整性', status: 'fail', detail: '八字或紫微结果缺失，无法互证。' }],
    }
  }

  const items: CrossValidationItem[] = []
  const baziDay = pillarText(bazi.pillars_primary?.day?.stem, bazi.pillars_primary?.day?.branch)
  const ziweiDay = ziwei.lunar?.day_gz || ''
  const baziHour = pillarText(bazi.pillars_primary?.hour?.stem, bazi.pillars_primary?.hour?.branch)
  const ziweiHour = ziwei.lunar?.hour_gz || ziwei.lunar?.hour_branch || ''

  if (baziDay && ziweiDay) {
    items.push({
      label: '日柱',
      status: baziDay === ziweiDay ? 'pass' : 'warn',
      detail: baziDay === ziweiDay
        ? `日柱一致：${baziDay}`
        : `八字日柱 ${baziDay}，紫微日柱 ${ziweiDay}，请核对出生时刻与历法口径。`,
    })
  }

  if (baziHour && ziweiHour) {
    const ziweiHourGz = ziweiHour.length === 1 ? `${ziwei.lunar?.hour_gz || ''}` : ziweiHour
    items.push({
      label: '时柱',
      status: baziHour === ziweiHourGz ? 'pass' : 'warn',
      detail: baziHour === ziweiHourGz
        ? `时柱一致：${baziHour}`
        : `八字时柱 ${baziHour}，紫微时柱 ${ziweiHourGz}，若精度为「未知时辰」属可接受偏差。`,
    })
  }

  if (ziwei.life_palace_gz) {
    items.push({
      label: '命宫',
      status: 'pass',
      detail: `紫微命宫 ${ziwei.life_palace_gz}，五行局 ${ziwei.wuxing_ju_name || '—'}`,
    })
  }

  if (bazi.geju?.geju_name) {
    items.push({
      label: '八字格局',
      status: 'pass',
      detail: `${bazi.geju.geju_name}，用神 ${bazi.yongshen?.favor?.join('、') || '缺失'}`,
    })
  }

  const hasFail = items.some((item) => item.status === 'fail')
  const hasWarn = items.some((item) => item.status === 'warn')
  return {
    overall: hasFail ? 'fail' : hasWarn ? 'warn' : 'pass',
    items,
  }
}
