import { onBeforeUnmount, onMounted, watch, type Ref } from 'vue'
import type { CaseOut } from '@/api/report'
import type { ZiweiResponse } from '@/api/ziwei'
import type { NullableRef, WorkbenchBaziLike, WorkbenchCaseLoader, WorkbenchSectionIdRef, WorkbenchSectionPredicate } from '@/composables/workbenchTypes'

type UseWorkbenchLifecycleOptions = {
  currentSectionId: WorkbenchSectionIdRef
  caseDetail: Ref<CaseOut | null>
  localBazi: NullableRef<WorkbenchBaziLike>
  localZiwei: NullableRef<ZiweiResponse>
  isZiweiSectionId: WorkbenchSectionPredicate
  isBaziSection: WorkbenchSectionPredicate
  loadBaziForCase: WorkbenchCaseLoader
  loadZiweiForCase: WorkbenchCaseLoader
  initializeWorkbench: () => Promise<void>
  clearGuideDemoTimers: () => void
}

export function useWorkbenchLifecycle(options: UseWorkbenchLifecycleOptions) {
  watch(options.currentSectionId, async (sectionId, prevSectionId) => {
    if (!options.caseDetail.value || sectionId === prevSectionId) return
    if (options.isZiweiSectionId(sectionId) && !options.localZiwei.value) {
      await options.loadZiweiForCase(options.caseDetail.value)
      return
    }
    if (options.isBaziSection(sectionId) && !options.localBazi.value) {
      await options.loadBaziForCase(options.caseDetail.value)
    }
  })

  onMounted(async () => {
    await options.initializeWorkbench()
  })

  onBeforeUnmount(() => {
    options.clearGuideDemoTimers()
  })
}
