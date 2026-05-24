import { computed, type Ref } from 'vue'
import type { CaseOut } from '@/api/report'
import { useReportStore } from '@/stores/report'
import type { WorkbenchCaseLoader, WorkbenchSectionIdRef, WorkbenchSectionPredicate } from '@/composables/workbenchTypes'

type UseWorkbenchPageStateOptions = {
  store: ReturnType<typeof useReportStore>
  searchQ: Ref<string>
  caseDetail: Ref<CaseOut | null>
  currentSectionId: WorkbenchSectionIdRef
  isZiweiSectionId: WorkbenchSectionPredicate
  loadBaziForCase: WorkbenchCaseLoader
  loadZiweiForCase: WorkbenchCaseLoader
}

export function useWorkbenchPageState(options: UseWorkbenchPageStateOptions) {
  const filteredList = computed(() => {
    const source = options.store.caseList ?? []
    const query = options.searchQ.value.trim().toLowerCase()
    if (!query) return source
    return source.filter((item) => {
      const text = [
        item.name,
        item.city,
        item.tags,
        item.notes,
        item.birth_dt_local,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return text.includes(query)
    })
  })

  async function reloadCurrentCase() {
    if (!options.caseDetail.value) return
    if (options.isZiweiSectionId(options.currentSectionId.value)) {
      await Promise.all([
        options.loadBaziForCase(options.caseDetail.value),
        options.loadZiweiForCase(options.caseDetail.value),
      ])
      return
    }
    await options.loadBaziForCase(options.caseDetail.value)
  }

  function fmtDate(dt: string | null) {
    if (!dt) return '—'
    const [date, time] = dt.split('T')
    const [y, m, d] = date.split('-')
    const t = (time ?? '').slice(0, 5)
    return `${y}年${m}月${d}日  ${t}`
  }

  return {
    filteredList,
    reloadCurrentCase,
    fmtDate,
  }
}
