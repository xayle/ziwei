import { ref } from 'vue'
import { getCases, deleteCase } from '@/api/admin'
import type { CaseItem } from '@/api/admin'

/** 案例列表管理（分页 + 删除） */
export function useAdminCases() {
  const cases = ref<CaseItem[]>([])
  const casesTotal = ref(0)
  const casesNext = ref<string | null>(null)
  const casesLoading = ref(false)
  const casesError = ref('')
  const casesLoaded = ref(false)

  async function loadCases(reset = false) {
    if (casesLoading.value) return
    casesLoading.value = true
    casesError.value = ''
    try {
      const params: Record<string, unknown> = { limit: 20 }
      if (!reset && casesNext.value) params.before_created_at = casesNext.value
      const res = await getCases(params)
      if (reset) {
        cases.value = res.items
      } else {
        cases.value.push(...res.items)
      }
      casesTotal.value = res.total
      casesNext.value = res.next_cursor
      casesLoaded.value = true
    } catch {
      casesError.value = '案例加载失败'
    } finally {
      casesLoading.value = false
    }
  }

  async function handleDeleteCase(id: string) {
    if (!confirm('确认删除该案例？此操作不可恢复。')) return
    try {
      await deleteCase(id)
      cases.value = cases.value.filter(c => c.id !== id)
      casesTotal.value--
    } catch {
      alert('删除失败，请稍后重试')
    }
  }

  return {
    cases, casesTotal, casesNext, casesLoading, casesError, casesLoaded,
    loadCases, handleDeleteCase,
  }
}
