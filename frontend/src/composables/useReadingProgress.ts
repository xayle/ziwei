import { computed, ref, watch } from 'vue'
import type { LifeVolumeId } from '@/types/life-volume'

const STORAGE_KEY = 'fusheng-reading-progress'

export function useReadingProgress(caseId: () => string) {
  const lastVolumeId = ref<LifeVolumeId | null>(null)

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const map = JSON.parse(raw) as Record<string, LifeVolumeId>
      const id = caseId()
      if (id && map[id]) lastVolumeId.value = map[id]
    } catch {
      lastVolumeId.value = null
    }
  }

  function save(volumeId: LifeVolumeId) {
    const id = caseId()
    if (!id) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      const map = raw ? JSON.parse(raw) as Record<string, LifeVolumeId> : {}
      map[id] = volumeId
      localStorage.setItem(STORAGE_KEY, JSON.stringify(map))
      lastVolumeId.value = volumeId
    } catch {
      // ignore quota errors
    }
  }

  watch(caseId, () => load(), { immediate: true })

  const resumeLabel = computed(() => (lastVolumeId.value ? `继续阅读 ${lastVolumeId.value}` : null))

  return { lastVolumeId, resumeLabel, save, load }
}
