import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NameAnalysisResponse, NameSuggestResponse } from '@/api/name'

export const useNameStore = defineStore('name', () => {
  // 姓名分析
  const analyzeResult = ref<NameAnalysisResponse | null>(null)
  const analyzeLoading = ref(false)
  const analyzeError = ref<string | null>(null)

  // 改名建议
  const suggestResult = ref<NameSuggestResponse | null>(null)
  const suggestLoading = ref(false)
  const suggestError = ref<string | null>(null)

  // 从八字页传入的参数（用神五行预填）
  const prefillSurname = ref('')
  const prefillElements = ref<string[]>([])

  function setPrefill(surname: string, elements: string[]) {
    prefillSurname.value = surname
    prefillElements.value = elements
  }

  function clearAnalyze() {
    analyzeResult.value = null
    analyzeError.value = null
  }

  function clearSuggest() {
    suggestResult.value = null
    suggestError.value = null
  }

  return {
    analyzeResult, analyzeLoading, analyzeError,
    suggestResult, suggestLoading, suggestError,
    prefillSurname, prefillElements,
    setPrefill, clearAnalyze, clearSuggest,
  }
})
