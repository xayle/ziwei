import { ref, type Ref } from 'vue'
import type { CaseOut, CasePatch } from '@/api/report'
import { createCase, updateCase, deleteCase as deleteCaseApi } from '@/api/report'
import { useReportStore } from '@/stores/report'

export type WorkbenchCaseFormState = {
  name: string
  birth_dt_local: string
  tz: string
  lon: number
  gender: 'male' | 'female'
  city: string
  solar_time_enabled: boolean
  notes: string
  tags: string
}

type UseWorkbenchCaseCrudOptions = {
  store: ReturnType<typeof useReportStore>
  caseDetail: Ref<CaseOut | null>
  selectedId: Ref<string | null>
}

type UseWorkbenchCaseCrudReturn = {
  showCreateDialog: Ref<boolean>
  showEditDialog: Ref<boolean>
  formData: Ref<WorkbenchCaseFormState>
  formSaving: Ref<boolean>
  openCreateDialog: () => void
  openEditDialog: () => void
  submitCreate: () => Promise<void>
  submitEdit: () => Promise<void>
  handleDeleteCase: () => Promise<void>
  closeCaseDialog: () => void
}

function createDefaultFormState(): WorkbenchCaseFormState {
  return {
    name: '',
    birth_dt_local: '1990-01-15T08:30',
    tz: 'Asia/Shanghai',
    lon: 116.41,
    gender: 'male',
    city: '',
    solar_time_enabled: false,
    notes: '',
    tags: '',
  }
}

export function useWorkbenchCaseCrud(options: UseWorkbenchCaseCrudOptions): UseWorkbenchCaseCrudReturn {
  const showCreateDialog = ref(false)
  const showEditDialog = ref(false)
  const formSaving = ref(false)
  const formData = ref<WorkbenchCaseFormState>(createDefaultFormState())

  function openCreateDialog() {
    formData.value = createDefaultFormState()
    showCreateDialog.value = true
  }

  function openEditDialog() {
    if (!options.caseDetail.value) return
    const currentCase = options.caseDetail.value
    formData.value = {
      name: currentCase.name,
      birth_dt_local: currentCase.birth_dt_local.slice(0, 16),
      tz: currentCase.tz,
      lon: currentCase.lon,
      gender: (currentCase.gender as 'male' | 'female') ?? 'male',
      city: currentCase.city ?? '',
      solar_time_enabled: currentCase.solar_time_enabled,
      notes: currentCase.notes ?? '',
      tags: (currentCase.tags ?? []).join(', '),
    }
    showEditDialog.value = true
  }

  async function submitCreate() {
    formSaving.value = true
    try {
      const tags = formData.value.tags.split(',').map(s => s.trim()).filter(Boolean)
      await createCase({
        name: formData.value.name,
        birth_dt_local: `${formData.value.birth_dt_local}:00`,
        tz: formData.value.tz,
        lon: formData.value.lon,
        gender: formData.value.gender,
        city: formData.value.city || undefined,
        solar_time_enabled: formData.value.solar_time_enabled,
        notes: formData.value.notes || undefined,
        tags: tags.length ? tags : undefined,
      })
      showCreateDialog.value = false
      await options.store.loadCaseList()
    } catch (error: unknown) {
      alert((error as Error).message)
    } finally {
      formSaving.value = false
    }
  }

  async function submitEdit() {
    if (!options.caseDetail.value) return
    formSaving.value = true
    try {
      const tags = formData.value.tags.split(',').map(s => s.trim()).filter(Boolean)
      const payload: CasePatch = {
        name: formData.value.name,
        gender: formData.value.gender,
        city: formData.value.city || undefined,
        solar_time_enabled: formData.value.solar_time_enabled,
        notes: formData.value.notes || undefined,
        tags: tags.length ? tags : undefined,
      }
      const updated = await updateCase(options.caseDetail.value.id, payload)
      options.caseDetail.value = updated
      showEditDialog.value = false
      await options.store.loadCaseList()
    } catch (error: unknown) {
      alert((error as Error).message)
    } finally {
      formSaving.value = false
    }
  }

  async function handleDeleteCase() {
    if (!options.caseDetail.value) return
    if (!confirm('确认删除案例？此操作不可恢复。')) return
    try {
      await deleteCaseApi(options.caseDetail.value.id)
      options.caseDetail.value = null
      options.selectedId.value = null
      await options.store.loadCaseList()
    } catch (_error) {
      alert('删除失败')
    }
  }

  function closeCaseDialog() {
    showCreateDialog.value = false
    showEditDialog.value = false
  }

  return {
    showCreateDialog,
    showEditDialog,
    formData,
    formSaving,
    openCreateDialog,
    openEditDialog,
    submitCreate,
    submitEdit,
    handleDeleteCase,
    closeCaseDialog,
  }
}
