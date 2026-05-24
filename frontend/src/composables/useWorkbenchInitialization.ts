import type { Ref } from 'vue'
import { createCase } from '@/api/report'
import type { CaseOut } from '@/api/report'
import { useNavStore } from '@/stores/nav'
import { useReportStore } from '@/stores/report'
import { useUiStore } from '@/stores/ui'

type UseWorkbenchInitializationOptions = {
  store: ReturnType<typeof useReportStore>
  nav: ReturnType<typeof useNavStore>
  ui: ReturnType<typeof useUiStore>
  simpleView: Ref<boolean>
  showNewbieGuide: Ref<boolean>
  selectedId: Ref<string | null>
  ensureProfileSyncedCase: () => Promise<CaseOut | null>
  selectCase: (currentCase: CaseOut) => Promise<void>
}

export function useWorkbenchInitialization(options: UseWorkbenchInitializationOptions) {
  async function initializeWorkbench() {
    try {
      options.simpleView.value = localStorage.getItem('workbench:simple-view') !== '0'
    } catch (_error) {
      options.simpleView.value = true
    }

    try {
      options.showNewbieGuide.value = localStorage.getItem('workbench:newbie-guide') !== '0'
    } catch (_error) {
      options.showNewbieGuide.value = true
    }

    await options.store.loadCaseList()

    try {
      const profileCase = await options.ensureProfileSyncedCase()
      if (profileCase) {
        await options.store.loadCaseList()
        const matched = (options.store.caseList ?? []).find(currentCase => currentCase.id === profileCase.id)
        if (matched) {
          await options.selectCase(matched)
        }
      }
    } catch (_error) {
      // ignore sync failure and fall back to default flow
    }

    if (options.store.caseList.length > 0 && !options.selectedId.value) {
      await options.selectCase(options.store.caseList[0])
    } else if (options.store.caseList.length === 0) {
      try {
        await createCase({
          name: '演示案例',
          birth_dt_local: '2000-01-15T14:30:00',
          tz: 'Asia/Shanghai',
          lon: 116.41,
          gender: 'male',
          city: '北京',
          solar_time_enabled: false,
          notes: '用于演示四柱八字、紫微斗数等功能的默认案例',
        })
        await options.store.loadCaseList()
        if (options.store.caseList.length > 0) {
          await options.selectCase(options.store.caseList[0])
        }
      } catch (error) {
        console.error('创建演示案例失败:', error)
      }
    }

    if (!options.nav.currentSectionId) {
      options.nav.selectSection('bazi-birth')
      options.ui.openRightPanelIfAllowed()
    }
  }

  return {
    initializeWorkbench,
  }
}
