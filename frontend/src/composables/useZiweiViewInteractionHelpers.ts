import { computed, type Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import type { Router } from 'vue-router'

type UseZiweiViewInteractionHelpersOptions = {
  router: Router
  result: Ref<ZiweiResponse | null>
  selectedPalace: Ref<PalaceResponse | null>
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  doCalculate: () => void
}

export function useZiweiViewInteractionHelpers(options: UseZiweiViewInteractionHelpersOptions) {
  const sanfangIndices = computed(() => {
    if (!options.selectedPalace.value) return new Set<number>()
    const idx = options.selectedPalace.value.index
    return new Set([
      (idx + 4) % 12,
      (idx + 8) % 12,
      (idx + 6) % 12,
    ])
  })

  function shiftDay(delta: number) {
    const date = new Date(options.year.value, options.month.value - 1, options.day.value)
    date.setDate(date.getDate() + delta)
    options.year.value = date.getFullYear()
    options.month.value = date.getMonth() + 1
    options.day.value = date.getDate()
    options.doCalculate()
  }

  function shiftHour(delta: number) {
    const hours = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    const currentIdx = hours.findIndex((value) => value === options.hour.value)
    const nextIdx = ((currentIdx < 0 ? 0 : currentIdx) + delta + 12) % 12
    options.hour.value = hours[nextIdx]!
    options.doCalculate()
  }

  function gotoZeri() {
    if (!options.result.value) return
    const branch = options.result.value.life_palace_gz.slice(-1)
    const juName = options.result.value.wuxing_ju_name
    // 本命年支：从出生年计算
    const BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    const birthYear = options.year.value
    const natalBranch = BRANCHES[((birthYear - 4) % 12 + 12) % 12]
    options.router.push({
      path: '/zeri',
      query: {
        life_palace_branch: branch,
        wuxing_ju_name: juName,
        natal_year_branch: natalBranch,
        birth_year: birthYear,
      },
    })
  }

  return {
    sanfangIndices,
    shiftDay,
    shiftHour,
    gotoZeri,
  }
}
