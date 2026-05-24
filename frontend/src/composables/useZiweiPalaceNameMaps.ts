/**
 * useZiweiPalaceNameMaps.ts — 大限/流年宫名映射及四化 map
 *
 * 提供：
 *  - palaceDaxianNames   宫格索引 → 大限宫名（如 "大命"）
 *  - daxianSihuaMap      大限四化 map（星名 → 四化类型）
 *  - liunianSihuaMap     流年四化 map
 */
import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

const DAXIAN_PREFIX  = ['大命','大兄','大夫','大子','大财','大疾','大迁','大友','大官','大田','大福','大父']
const LIUNIAN_PREFIX = ['年命','年兄','年夫','年子','年财','年疾','年迁','年友','年官','年田','年福','年父']

// Re-export so callers can use them if needed
export { DAXIAN_PREFIX, LIUNIAN_PREFIX }

interface Deps {
  result:            Ref<ZiweiResponse | null>
  selectedDaxianIdx: Ref<number>
  currentDayun:      Ref<{ ganzhi?: string; sihua?: Record<string, string> } | null | undefined>
}

export function useZiweiPalaceNameMaps({ result, selectedDaxianIdx, currentDayun }: Deps) {
  const palaceDaxianNames = computed((): Record<number, string> => {
    if (!result.value?.palaces || !result.value?.dayun?.items) return {}
    const map: Record<number, string> = {}
    const activeDayun = selectedDaxianIdx.value >= 0
      ? result.value.dayun.items[selectedDaxianIdx.value]
      : currentDayun.value
    if (!activeDayun) return map
    const dayunPalaceIdx = result.value.palaces.findIndex(
      p => (p.stem + p.branch) === activeDayun.ganzhi,
    )
    if (dayunPalaceIdx < 0) return map
    const forward = result.value.dayun.forward
    for (let i = 0; i < 12; i++) {
      const targetIdx = forward
        ? (dayunPalaceIdx + i) % 12
        : (dayunPalaceIdx - i + 12) % 12
      map[targetIdx] = DAXIAN_PREFIX[i]
    }
    return map
  })

  const daxianSihuaMap = computed((): Record<string, string> => {
    if (!result.value?.dayun?.items) return {}
    const activeDayun = selectedDaxianIdx.value >= 0
      ? result.value.dayun.items[selectedDaxianIdx.value]
      : currentDayun.value
    return (activeDayun as any)?.sihua ?? {}
  })

  const liunianSihuaMap = computed((): Record<string, string> => {
    if (!result.value?.liunian) return {}
    return result.value.liunian.sihua ?? {}
  })

  return {
    palaceDaxianNames,
    daxianSihuaMap,
    liunianSihuaMap,
  }
}
