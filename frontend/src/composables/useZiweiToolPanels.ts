import { computed, ref, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

export interface ZiweiCompareTarget {
  year: number
  month: number
  day: number
  hour: number
  minute: number
  gender: '男' | '女'
}

export interface ZiweiDayFortune {
  day: number
  score: number
  brief: string
}

type UseZiweiToolPanelsOptions = {
  result: Ref<ZiweiResponse | null>
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  minute: Ref<number>
  gender: Ref<'男' | '女'>
  longitude: Ref<number | undefined>
  getMonthForecast: (month: number) => { score?: number } | null | undefined
}

export function useZiweiToolPanels(options: UseZiweiToolPanelsOptions) {
  const showSharePanel = ref(false)
  const showComparePanel = ref(false)
  const showCalendarView = ref(false)

  const compareTarget = ref<ZiweiCompareTarget | null>(null)
  const compareYear = ref(1990)
  const compareMonth = ref(1)
  const compareDay = ref(1)
  const compareHour = ref(12)
  const compareMinute = ref(0)
  const compareGender = ref<'男' | '女'>('女')

  const calendarViewYear = ref(new Date().getFullYear())
  const calendarViewMonth = ref(new Date().getMonth() + 1)

  const shareLink = computed(() => {
    if (!options.result.value) return ''
    const params = new URLSearchParams({
      y: String(options.year.value),
      m: String(options.month.value),
      d: String(options.day.value),
      h: String(options.hour.value),
      mi: String(options.minute.value),
      g: options.gender.value,
    })
    if (options.longitude.value) params.set('lng', String(options.longitude.value))
    return `${window.location.origin}${window.location.pathname}?${params.toString()}`
  })

  async function copyShareLink() {
    if (!shareLink.value) return
    try {
      await navigator.clipboard.writeText(shareLink.value)
      alert('链接已复制到剪贴板')
      showSharePanel.value = false
    } catch {
      alert('复制失败，请手动复制')
    }
  }

  function toggleSharePanel() {
    showSharePanel.value = !showSharePanel.value
  }

  function closeSharePanel() {
    showSharePanel.value = false
  }

  function toggleComparePanel() {
    showComparePanel.value = !showComparePanel.value
  }

  function closeComparePanel() {
    showComparePanel.value = false
  }

  function setCompareTarget() {
    compareTarget.value = {
      year: compareYear.value,
      month: compareMonth.value,
      day: compareDay.value,
      hour: compareHour.value,
      minute: compareMinute.value,
      gender: compareGender.value,
    }
    showComparePanel.value = false
  }

  function clearCompareTarget() {
    compareTarget.value = null
  }

  function toggleCalendarView() {
    showCalendarView.value = !showCalendarView.value
  }

  function closeCalendarView() {
    showCalendarView.value = false
  }

  const calendarDays = computed((): ZiweiDayFortune[] => {
    const days: ZiweiDayFortune[] = []
    const daysInMonth = new Date(calendarViewYear.value, calendarViewMonth.value, 0).getDate()

    for (let d = 1; d <= daysInMonth; d++) {
      const monthForecast = options.getMonthForecast(calendarViewMonth.value)
      const baseScore = monthForecast?.score ?? 70
      const dayMod = ((d * 7) % 20) - 10
      const score = Math.max(30, Math.min(100, baseScore + dayMod))

      let brief = '平'
      if (score >= 85) brief = '大吉'
      else if (score >= 75) brief = '吉'
      else if (score >= 60) brief = '平'
      else if (score >= 45) brief = '凶'
      else brief = '大凶'

      days.push({ day: d, score, brief })
    }

    return days
  })

  const calendarFirstDayOfWeek = computed(() => new Date(calendarViewYear.value, calendarViewMonth.value - 1, 1).getDay())

  const calendarGrid = computed(() => {
    const grid: Array<ZiweiDayFortune | null> = []
    for (let i = 0; i < calendarFirstDayOfWeek.value; i++) {
      grid.push(null)
    }
    grid.push(...calendarDays.value)
    return grid
  })

  function prevCalendarMonth() {
    if (calendarViewMonth.value === 1) {
      calendarViewMonth.value = 12
      calendarViewYear.value--
    } else {
      calendarViewMonth.value--
    }
  }

  function nextCalendarMonth() {
    if (calendarViewMonth.value === 12) {
      calendarViewMonth.value = 1
      calendarViewYear.value++
    } else {
      calendarViewMonth.value++
    }
  }

  function getDayFortuneClass(score: number) {
    if (score >= 85) return 'fortune-great'
    if (score >= 75) return 'fortune-good'
    if (score >= 60) return 'fortune-normal'
    if (score >= 45) return 'fortune-bad'
    return 'fortune-terrible'
  }

  return {
    showSharePanel,
    shareLink,
    copyShareLink,
    toggleSharePanel,
    closeSharePanel,
    showComparePanel,
    compareTarget,
    compareYear,
    compareMonth,
    compareDay,
    compareHour,
    compareMinute,
    compareGender,
    toggleComparePanel,
    closeComparePanel,
    setCompareTarget,
    clearCompareTarget,
    showCalendarView,
    calendarViewYear,
    calendarViewMonth,
    calendarGrid,
    toggleCalendarView,
    closeCalendarView,
    prevCalendarMonth,
    nextCalendarMonth,
    getDayFortuneClass,
  }
}