import { computed, ref, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

type UseZiweiTimelineControlsOptions = {
  result: Ref<ZiweiResponse | null>
  liunianYear: Ref<number | undefined>
  currentYear: number
  triggerRecalculate: () => Promise<void> | void
}

export function useZiweiTimelineControls(options: UseZiweiTimelineControlsOptions) {
  const selectedDaxianIdx = ref<number>(-1)
  const selectedLiunianYear = ref<number>(options.currentYear)
  const selectedLiuyueMonth = ref<number>(0)
  const showYearPicker = ref(false)

  const liunianYears = computed(() => {
    const center = selectedLiunianYear.value || options.currentYear
    const years: number[] = []
    for (let y = center - 5; y <= center + 10; y++) years.push(y)
    return years
  })

  const allLiunianYears = computed(() => {
    const years: number[] = []
    for (let y = 1930; y <= 2080; y++) years.push(y)
    return years
  })

  const yearPickerRange = computed(() => {
    const items = options.result.value?.dayun?.items
    if (!items?.length) return { start: options.currentYear - 30, end: options.currentYear + 30 }
    return {
      start: items[0].start_year,
      end: items[items.length - 1].start_year + 10,
    }
  })

  const yearPickerList = computed(() => {
    const { start, end } = yearPickerRange.value
    const list: number[] = []
    for (let y = start; y <= end; y++) list.push(y)
    return list
  })

  function scrollToCurrentDayun() {
    const el = document.querySelector('.dayun-item.cur, .dt-node.dt-cur')
    if (!el) return
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-blink')
    setTimeout(() => el.classList.remove('highlight-blink'), 1500)
  }

  function scrollToCurrentLiuyue() {
    const el = document.querySelector('.liuyue-item.liuyue-cur, .lyq-btn.lyq-cur')
    if (!el) return
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-blink')
    setTimeout(() => el.classList.remove('highlight-blink'), 1500)
  }

  function toggleSelectedDaxian(idx: number) {
    selectedDaxianIdx.value = selectedDaxianIdx.value === idx ? -1 : idx
  }

  function setSelectedLiunianYearValue(year: number) {
    selectedLiunianYear.value = year
  }

  function stepSelectedLiunianYear(delta: number) {
    selectedLiunianYear.value += delta
  }

  function toggleYearPicker() {
    showYearPicker.value = !showYearPicker.value
  }

  function closeYearPicker() {
    showYearPicker.value = false
  }

  async function selectYearFromPicker(year: number) {
    selectedLiunianYear.value = year
    showYearPicker.value = false
    options.liunianYear.value = year
    if (options.result.value) {
      await options.triggerRecalculate()
    }
  }

  return {
    selectedDaxianIdx,
    selectedLiunianYear,
    selectedLiuyueMonth,
    showYearPicker,
    liunianYears,
    allLiunianYears,
    yearPickerList,
    scrollToCurrentDayun,
    scrollToCurrentLiuyue,
    toggleSelectedDaxian,
    setSelectedLiunianYearValue,
    stepSelectedLiunianYear,
    toggleYearPicker,
    closeYearPicker,
    selectYearFromPicker,
  }
}
