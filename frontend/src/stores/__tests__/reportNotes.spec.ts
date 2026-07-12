import { describe, expect, it, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useReportNotesStore } from '@/stores/reportNotes'

describe('reportNotes store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('persists notes per profile id', () => {
    const store = useReportNotesStore()
    store.setNotes('profile-a', '换运节点 2028')
    store.setNotes('profile-b', '客户反馈良好')

    expect(store.getNotes('profile-a')).toBe('换运节点 2028')
    expect(store.getNotes('profile-b')).toBe('客户反馈良好')
    expect(store.getNotes('missing')).toBe('')
  })
})
