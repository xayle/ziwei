import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'
import { useProfileStore } from '@/stores/profile'
import { buildIztroDisplay } from '@/utils/buildEngineTrustDisplay'

export function useYoubiHourAlign(ziwei: Ref<ZiweiResponse | null | undefined>) {
  const profile = useProfileStore()

  const iztro = computed(() => buildIztroDisplay(ziwei.value, {
    yearDivide: profile.yearDivide,
    dayDivide: profile.dayDivide,
  }))

  const showYoubiDriftHint = computed(() => {
    if ((profile.ziweiYoubiMethod ?? 'month') === 'hour') return false
    const warnings = ziwei.value?.engine_warnings ?? []
    return warnings.some((w) => w.includes('右弼') || w.includes('youbi'))
      || (iztro.value?.status === 'main_match' && Boolean(iztro.value))
  })

  async function applyYoubiHour(reload: () => Promise<unknown>) {
    profile.setProfile({ ziweiYoubiMethod: 'hour' })
    await reload()
  }

  return {
    showYoubiDriftHint,
    applyYoubiHour,
  }
}
