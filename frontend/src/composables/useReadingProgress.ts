import { computed, onMounted, ref, watch } from 'vue'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'
import { READING_PROGRESS_STORAGE_KEY } from '@/constants/feBeContract'

const ACTIVE_PROFILE_KEY = 'profile_active_id_v1'

export function useReadingProgress(caseId: () => string) {
  const revision = ref(0)

  function resolveCaseId(): string {
    const id = caseId()
    if (id) return id
    try {
      return localStorage.getItem(ACTIVE_PROFILE_KEY) || 'default'
    } catch {
      return 'default'
    }
  }

  function readSavedVolume(): LifeVolumeId | null {
    try {
      const raw = localStorage.getItem(READING_PROGRESS_STORAGE_KEY)
      if (!raw) return null
      const map = JSON.parse(raw) as Record<string, LifeVolumeId>
      const id = resolveCaseId()
      return id && map[id] ? map[id] : null
    } catch {
      return null
    }
  }

  const lastVolumeId = computed(() => {
    revision.value
    return readSavedVolume()
  })

  function save(volumeId: LifeVolumeId) {
    const id = resolveCaseId()
    if (!id) return
    try {
      const raw = localStorage.getItem(READING_PROGRESS_STORAGE_KEY)
      const map = raw ? JSON.parse(raw) as Record<string, LifeVolumeId> : {}
      map[id] = volumeId
      localStorage.setItem(READING_PROGRESS_STORAGE_KEY, JSON.stringify(map))
      revision.value += 1
    } catch {
      // ignore quota errors
    }
  }

  function load() {
    revision.value += 1
  }

  watch(() => caseId(), () => load(), { immediate: true })
  onMounted(() => load())

  const resumeLabel = computed(() => {
    const id = lastVolumeId.value
    if (!id) return null
    const title = LIFE_VOLUME_LABELS[id as LifeVolumeId] ?? id
    return `继续阅读「${title}」`
  })

  return { lastVolumeId, resumeLabel, save, load }
}
