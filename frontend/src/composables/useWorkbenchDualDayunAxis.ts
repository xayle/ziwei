import { computed, type ComputedRef, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

type BaziDayunTimelineItem = {
  startYear: number | null
  endYear: number | null
  isActive: boolean
  isPast: boolean
  ganzhi: string
}

type ZiweiDayunItem = {
  index: number
  ganzhi: string
  start_year?: number | null
}

type WorkbenchDualDayunSegment = {
  label: string
  left: number
  width: number
  isActive: boolean
  isPast: boolean
  startYear: number | null
  onSelect: () => void
}

type WorkbenchDualDayunZiweiSegment = WorkbenchDualDayunSegment & {
  index: number
}

type WorkbenchDualDayunAxisData = {
  baziSegments: WorkbenchDualDayunSegment[]
  zwSegments: WorkbenchDualDayunZiweiSegment[]
  nowPct: number
  minYear: number
  maxYear: number
}

type UseWorkbenchDualDayunAxisReturn = {
  dualDayunAxis: ComputedRef<WorkbenchDualDayunAxisData | null>
}

type UseWorkbenchDualDayunAxisOptions = {
  currentYear: number
  dayunTimelineItems: ComputedRef<BaziDayunTimelineItem[]>
  localZiwei: Ref<ZiweiResponse | null>
  selectDayun: (startYear: number | null) => void
  selectZiweiDayun: (index: number) => void
}

export function useWorkbenchDualDayunAxis(options: UseWorkbenchDualDayunAxisOptions): UseWorkbenchDualDayunAxisReturn {
  const dualDayunAxis = computed<WorkbenchDualDayunAxisData | null>(() => {
    const baziItems = options.dayunTimelineItems.value
    const ziweiItems = ((options.localZiwei.value?.dayun?.items ?? []) as ZiweiDayunItem[]).map((item, index, arr) => ({
      constNextStartYear: arr[index + 1]?.start_year ?? null,
      item,
      index,
      arr,
    })).map(({ item, constNextStartYear }) => ({
      ...item,
      startYear: item.start_year ?? null,
      endYear: constNextStartYear ? constNextStartYear - 1 : null,
      isActive:
        item.start_year != null
        && item.start_year <= options.currentYear
        && (constNextStartYear == null || constNextStartYear > options.currentYear),
      isPast:
        constNextStartYear != null
        && constNextStartYear - 1 < options.currentYear
        && !(item.start_year != null
          && item.start_year <= options.currentYear
          && (constNextStartYear == null || constNextStartYear > options.currentYear)),
    }))

    if (!baziItems.length && !ziweiItems.length) return null

    const allStarts = [
      ...baziItems.map(item => item.startYear ?? 0),
      ...ziweiItems.map(item => item.startYear ?? 0),
    ].filter(Boolean)

    const minYear = Math.max(Math.min(...allStarts), options.currentYear - 20)
    const maxYear = options.currentYear + 30
    const span = maxYear - minYear || 1
    const pct = (year: number | null) => year == null ? 0 : Math.max(0, Math.min(100, ((year - minYear) / span) * 100))

    const baziSegments = baziItems
      .filter(item => item.startYear != null && (item.endYear == null || item.endYear >= minYear))
      .map(item => ({
        label: item.ganzhi,
        left: pct(item.startYear),
        width: pct(item.endYear != null ? item.endYear + 1 : maxYear) - pct(item.startYear),
        isActive: item.isActive,
        isPast: item.isPast,
        startYear: item.startYear,
        onSelect: () => options.selectDayun(item.startYear),
      }))

    const ziweiSegments = ziweiItems
      .filter(item => item.startYear != null && (item.endYear == null || item.endYear >= minYear))
      .map(item => ({
        label: item.ganzhi,
        left: pct(item.startYear),
        width: pct(item.endYear != null ? item.endYear + 1 : maxYear) - pct(item.startYear),
        isActive: item.isActive,
        isPast: item.isPast,
        startYear: item.startYear,
        index: item.index,
        onSelect: () => options.selectZiweiDayun(item.index),
      }))

    return {
      baziSegments,
      zwSegments: ziweiSegments,
      nowPct: pct(options.currentYear),
      minYear,
      maxYear,
    }
  })

  return {
    dualDayunAxis,
  }
}
