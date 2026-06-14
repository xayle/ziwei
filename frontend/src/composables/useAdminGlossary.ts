import { ref } from 'vue'
import { getGlossary, updateGlossaryTerm } from '@/api/static-data'
import type { GlossaryItem } from '@/api/static-data'

/** 词汇管理面板 */
export function useAdminGlossary() {
  const glossaryItems = ref<GlossaryItem[]>([])
  const glossaryLoading = ref(false)
  const glossaryLoaded = ref(false)
  const glossaryError = ref('')
  const glossarySearch = ref('')
  const glossaryDialogOpen = ref(false)
  const glossarySaving = ref(false)
  const glossarySaveError = ref('')
  const editingGlossary = ref<GlossaryItem | null>(null)
  const glossaryForm = ref({
    term: '',
    definition: '',
    pinyin: '',
    classic_source: '',
  })

  async function loadGlossaryPanel() {
    if (glossaryLoading.value) return
    glossaryLoading.value = true
    glossaryError.value = ''
    try {
      glossaryItems.value = await getGlossary({ q: glossarySearch.value || undefined, limit: 50 })
      glossaryLoaded.value = true
    } catch {
      glossaryError.value = '词汇管理加载失败'
    } finally {
      glossaryLoading.value = false
    }
  }

  function applyGlossaryFilter() {
    glossaryLoaded.value = false
    loadGlossaryPanel()
  }

  function openGlossaryDialog(item: GlossaryItem) {
    editingGlossary.value = item
    glossaryForm.value = {
      term: item.term,
      definition: item.definition,
      pinyin: item.pinyin || '',
      classic_source: item.classic_source || '',
    }
    glossarySaveError.value = ''
    glossaryDialogOpen.value = true
  }

  function closeGlossaryDialog() {
    glossaryDialogOpen.value = false
    glossarySaveError.value = ''
  }

  async function saveGlossary() {
    if (!editingGlossary.value) return
    if (!glossaryForm.value.definition.trim()) {
      glossarySaveError.value = '定义不能为空'
      return
    }
    glossarySaving.value = true
    glossarySaveError.value = ''
    try {
      const updated = await updateGlossaryTerm(editingGlossary.value.term, {
        definition: glossaryForm.value.definition.trim(),
        pinyin: glossaryForm.value.pinyin.trim() || undefined,
        classic_source: glossaryForm.value.classic_source.trim() || undefined,
      })
      glossaryItems.value = glossaryItems.value.map(item => item.term === updated.term ? updated : item)
      closeGlossaryDialog()
    } catch {
      glossarySaveError.value = '词汇保存失败'
    } finally {
      glossarySaving.value = false
    }
  }

  return {
    glossaryItems, glossaryLoading, glossaryLoaded, glossaryError, glossarySearch,
    glossaryDialogOpen, glossarySaving, glossarySaveError, editingGlossary, glossaryForm,
    loadGlossaryPanel, applyGlossaryFilter, openGlossaryDialog, closeGlossaryDialog, saveGlossary,
  }
}
