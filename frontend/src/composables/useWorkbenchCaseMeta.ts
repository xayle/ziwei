import { computed, type ComputedRef, type Ref } from 'vue'
import type { CaseOut } from '@/api/report'
import type { ZiweiResponse } from '@/api/ziwei'
import type { ChartSummaryCards } from './useWorkbenchBaziPanel'

type DayunLike = {
  start_year?: number
  stem?: string
  branch?: string
}

type ZiweiDayunLike = {
  ganzhi?: string
  start_age?: number
  end_age?: number
}

type ZiweiLiuyueLike = {
  month?: number
  month_name?: string
  month_gz?: string
}

type ChartSummaryCardLike = {
  dayunGz?: string
  lyGz?: string
  lyShishen?: string
  weakList?: string
}

type UseWorkbenchCaseMetaReturn = {
  genderLabel: (gender: string | null | undefined) => string
  currentCaseDayunLabel: ComputedRef<string | null>
  birthLocalText: ComputedRef<string>
  ziweiCaseSummaryText: ComputedRef<string>
  baziCaseSummaryLine: ComputedRef<string>
}

type UseWorkbenchCaseMetaOptions = {
  caseDetail: Ref<CaseOut | null>
  dayunItems: ComputedRef<DayunLike[]>
  chartSummaryCards: ComputedRef<ChartSummaryCards | ChartSummaryCardLike | null>
  isZiweiSection: ComputedRef<boolean>
  localZiwei: Ref<ZiweiResponse | null>
  activeZiweiDayun: ComputedRef<ZiweiDayunLike | null>
  currentZiweiDayun: ComputedRef<ZiweiDayunLike | null>
  activeZiweiLiuyue: ComputedRef<ZiweiLiuyueLike | null>
  currentZiweiLiuyue: ComputedRef<ZiweiLiuyueLike | null>
}

function genderLabel(gender: string | null | undefined): string {
  if (gender === 'male') return '男'
  if (gender === 'female') return '女'
  return '未填'
}

export function useWorkbenchCaseMeta(options: UseWorkbenchCaseMetaOptions): UseWorkbenchCaseMetaReturn {
  const currentYear = new Date().getFullYear()

  const currentCaseDayunLabel = computed<string | null>(() => {
    const current = options.dayunItems.value.find((item, index) => {
      if ((item.start_year ?? 0) > currentYear) return false
      const next = options.dayunItems.value[index + 1]
      return !next || (next.start_year ?? Number.MAX_SAFE_INTEGER) > currentYear
    })
    if (!current) return null
    return `${current.stem ?? '—'}${current.branch ?? ''}`
  })

  const birthLocalText = computed<string>(() => {
    const dt = options.caseDetail.value?.birth_dt_local
    if (!dt) return '—'
    return dt.replace('T', ' ').slice(0, 16)
  })

  const ziweiCaseSummaryText = computed<string>(() => {
    if (!options.isZiweiSection.value || !options.localZiwei.value) return ''
    const dayun = options.activeZiweiDayun.value ?? options.currentZiweiDayun.value
    const liuyue = options.activeZiweiLiuyue.value ?? options.currentZiweiLiuyue.value
    const dayunText = dayun ? `${dayun.ganzhi}(${dayun.start_age}-${dayun.end_age}岁)` : '—'
    const liuyueText = liuyue ? `${liuyue.month_name || `${liuyue.month}月`}${liuyue.month_gz}` : '—'
    return `紫微：${dayunText} ｜ ${liuyueText}`
  })

  const baziCaseSummaryLine = computed<string>(() => {
    const cards = options.chartSummaryCards.value
    if (!cards) return ''
    const parts: string[] = []
    if (cards.dayunGz && cards.dayunGz !== '—') parts.push(`大运 ${cards.dayunGz}`)
    if (cards.lyGz && cards.lyGz !== '—') parts.push(`流年 ${cards.lyGz}${cards.lyShishen ? `·${cards.lyShishen}` : ''}`)
    if (cards.weakList && cards.weakList !== '无') parts.push(`忌 ${cards.weakList}`)
    return parts.join(' ｜ ')
  })

  return {
    genderLabel,
    currentCaseDayunLabel,
    birthLocalText,
    ziweiCaseSummaryText,
    baziCaseSummaryLine,
  }
}
