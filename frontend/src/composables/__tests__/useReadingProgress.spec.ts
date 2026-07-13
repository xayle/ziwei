import { describe, it, expect, beforeEach } from 'vitest'
import { effectScope } from 'vue'
import { useReadingProgress } from '@/composables/useReadingProgress'

describe('useReadingProgress', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('loads saved volume for active profile id', () => {
    localStorage.setItem('fusheng-reading-progress', JSON.stringify({ default: 'vol5' }))
    const scope = effectScope()
    scope.run(() => {
      const { lastVolumeId } = useReadingProgress(() => 'default')
      expect(lastVolumeId.value).toBe('vol5')
    })
  })

  it('uses localStorage active id when case id is empty', () => {
    localStorage.setItem('profile_active_id_v1', 'default')
    localStorage.setItem('fusheng-reading-progress', JSON.stringify({ default: 'vol5' }))
    const scope = effectScope()
    scope.run(() => {
      const { lastVolumeId } = useReadingProgress(() => '')
      expect(lastVolumeId.value).toBe('vol5')
    })
  })
})
