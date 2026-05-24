import { computed, ref, type Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'
import { readStorage, writeStorage } from '@/utils/browserStorage'

export type ZiweiNoteTarget = 'palace' | 'star' | 'general'

export interface ZiweiChartNote {
  id: string
  target: ZiweiNoteTarget
  targetName: string
  content: string
  createdAt: number
  updatedAt: number
}

const NOTES_KEY = 'ziwei_chart_notes'
const BOOKMARKS_KEY = 'ziwei_palace_bookmarks'
const STARRED_STARS_KEY = 'ziwei_starred_stars'

type UseZiweiInteractionStateOptions = {
  result: Ref<ZiweiResponse | null>
  selectedPalace: Ref<PalaceResponse | null>
}

function readJsonArray<T>(key: string, fallback: T[] = []): T[] {
  try {
    const raw = readStorage(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

export function useZiweiInteractionState(options: UseZiweiInteractionStateOptions) {
  const showNotesPanel = ref(false)
  const showBookmarksPanel = ref(false)
  const chartNotes = ref<ZiweiChartNote[]>(readJsonArray<ZiweiChartNote>(NOTES_KEY))
  const editingNote = ref<ZiweiChartNote | null>(null)
  const noteInput = ref('')
  const noteTarget = ref<ZiweiNoteTarget>('general')
  const noteTargetName = ref('')
  const palaceBookmarks = ref<Set<number>>(new Set(readJsonArray<number>(BOOKMARKS_KEY)))
  const starredStars = ref<Set<string>>(new Set(readJsonArray<string>(STARRED_STARS_KEY)))

  function persistNotes() {
    writeStorage(NOTES_KEY, JSON.stringify(chartNotes.value))
  }

  function persistBookmarks() {
    writeStorage(BOOKMARKS_KEY, JSON.stringify([...palaceBookmarks.value]))
  }

  function persistStarredStars() {
    writeStorage(STARRED_STARS_KEY, JSON.stringify([...starredStars.value]))
  }

  function resetNoteForm() {
    editingNote.value = null
    noteInput.value = ''
    noteTarget.value = 'general'
    noteTargetName.value = ''
  }

  function toggleNotesPanel() {
    showNotesPanel.value = !showNotesPanel.value
  }

  function toggleBookmarksPanel() {
    showBookmarksPanel.value = !showBookmarksPanel.value
  }

  function addNote() {
    if (!noteInput.value.trim()) return
    const note: ZiweiChartNote = {
      id: `note_${Date.now()}`,
      target: noteTarget.value,
      targetName: noteTargetName.value || '全盘',
      content: noteInput.value.trim(),
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    chartNotes.value.unshift(note)
    persistNotes()
    resetNoteForm()
  }

  function updateNote() {
    if (!editingNote.value || !noteInput.value.trim()) return
    const idx = chartNotes.value.findIndex((note) => note.id === editingNote.value?.id)
    if (idx < 0) return
    chartNotes.value[idx] = {
      ...chartNotes.value[idx],
      target: noteTarget.value,
      targetName: noteTargetName.value || chartNotes.value[idx].targetName || '全盘',
      content: noteInput.value.trim(),
      updatedAt: Date.now(),
    }
    persistNotes()
    resetNoteForm()
  }

  function startEditNote(note: ZiweiChartNote) {
    editingNote.value = note
    noteInput.value = note.content
    noteTarget.value = note.target
    noteTargetName.value = note.target === 'general' ? '' : note.targetName
    showNotesPanel.value = true
  }

  function cancelEditNote() {
    resetNoteForm()
  }

  function deleteNote(id: string) {
    chartNotes.value = chartNotes.value.filter((note) => note.id !== id)
    persistNotes()
    if (editingNote.value?.id === id) {
      resetNoteForm()
    }
  }

  function togglePalaceBookmark(idx: number) {
    if (palaceBookmarks.value.has(idx)) {
      palaceBookmarks.value.delete(idx)
    } else {
      palaceBookmarks.value.add(idx)
    }
    persistBookmarks()
  }

  function isPalaceBookmarked(idx: number) {
    return palaceBookmarks.value.has(idx)
  }

  const bookmarkedPalaces = computed(() => {
    if (!options.result.value?.palaces) return []
    return options.result.value.palaces.filter((palace) => palaceBookmarks.value.has(palace.index))
  })

  function toggleStarStar(starName: string) {
    if (!starName) return
    if (starredStars.value.has(starName)) {
      starredStars.value.delete(starName)
    } else {
      starredStars.value.add(starName)
    }
    persistStarredStars()
  }

  function isStarStarred(starName: string) {
    return starredStars.value.has(starName)
  }

  const starredStarsDistribution = computed(() => {
    const palaces = options.result.value?.palaces ?? []
    if (!palaces.length || !starredStars.value.size) return [] as Array<{ star: string; palaces: string[] }>

    return [...starredStars.value]
      .map((star) => ({
        star,
        palaces: palaces
          .filter((palace) => palace.main_stars?.some((item) => item.name === star))
          .map((palace) => palace.name.replace('宫', '')),
      }))
      .filter((item) => item.palaces.length > 0)
  })

  const selectedPalaceStarredStars = computed(() => {
    const palace = options.selectedPalace.value
    if (!palace?.main_stars?.length) return [] as string[]
    return palace.main_stars.map((item) => item.name).filter((star) => starredStars.value.has(star))
  })

  return {
    showNotesPanel,
    showBookmarksPanel,
    chartNotes,
    editingNote,
    noteInput,
    noteTarget,
    noteTargetName,
    palaceBookmarks,
    starredStars,
    toggleNotesPanel,
    toggleBookmarksPanel,
    addNote,
    updateNote,
    startEditNote,
    cancelEditNote,
    deleteNote,
    togglePalaceBookmark,
    isPalaceBookmarked,
    bookmarkedPalaces,
    toggleStarStar,
    isStarStarred,
    starredStarsDistribution,
    selectedPalaceStarredStars,
  }
}