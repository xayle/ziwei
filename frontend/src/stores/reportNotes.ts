import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'fusheng_report_notes_v1'

type NotesMap = Record<string, string>

export const useReportNotesStore = defineStore('reportNotes', () => {
  const notesByProfile = ref<NotesMap>({})

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw) as NotesMap
      if (parsed && typeof parsed === 'object') {
        notesByProfile.value = parsed
      }
    } catch {
      // ignore parse errors
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(notesByProfile.value))
  }

  function getNotes(profileId: string): string {
    return notesByProfile.value[profileId] || ''
  }

  function setNotes(profileId: string, text: string) {
    notesByProfile.value = { ...notesByProfile.value, [profileId]: text }
    persist()
  }

  load()

  return {
    notesByProfile,
    getNotes,
    setNotes,
  }
})
