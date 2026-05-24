/**
 * useBaziComputation.ts — 八字排盘计算与案例保存逻辑
 *
 * 提供：
 *  - loading / error / result      排盘状态
 *  - savedCaseId                   已保存案例 ID
 *  - saveDialog*                   保存弹窗状态
 *  - doCalculate()                 执行排盘
 *  - openSaveDialog() / closeSaveDialog()
 *  - saveCurrentCase()             保存案例到后端
 *  - resetSaveState()              清空保存状态
 *  - resetResult()                 清空排盘结果
 */
import { ref } from 'vue'
import { computeBazi } from '@/api/bazi'
import { createCase } from '@/api/report'
import type { BaziResponse } from '@/api/bazi'

// 与 useBaziForm 返回值匹配的最小接口
interface BaziFormState {
  birthDt:   { value: string }
  lon:       { value: number | undefined }
  tz:        { value: string }
  gender:    { value: 'male' | 'female' | '' }
  mode:      { value: 'dual' | 'single' }
  solarTime: { value: boolean | undefined }
  cityName:  { value: string }
  initCity:  { value: string }
}

export function useBaziComputation(form: BaziFormState) {
  // ── 排盘状态 ──────────────────────────────────────────────────────────────
  const loading = ref(false)
  const error   = ref('')
  const result  = ref<BaziResponse | null>(null)

  // ── 案例保存状态 ──────────────────────────────────────────────────────────
  const savedCaseId    = ref<string | null>(null)
  const saveCaseName   = ref('')
  const saveCaseNotes  = ref('')
  const saveDialogOpen = ref(false)
  const saveCaseSaving = ref(false)
  const saveCaseError  = ref('')
  const saveCaseSuccess = ref('')

  // ── 辅助 ─────────────────────────────────────────────────────────────────
  function normalizeBirthDtLocal(value: string): string {
    if (!value) return ''
    const [datePart, timePart = '00:00'] = value.split('T')
    const normalizedTime = timePart.length === 5 ? `${timePart}:00` : timePart
    return `${datePart}T${normalizedTime}`
  }

  function buildDefaultCaseName(): string {
    const dateLabel = form.birthDt.value ? form.birthDt.value.replace('T', ' ') : '未命名时间'
    const cityLabel = form.cityName.value || form.initCity.value || '未命名城市'
    return `八字案例 · ${cityLabel} · ${dateLabel}`
  }

  function extractErrorMessage(e: unknown, fallback: string): string {
    return (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? fallback
  }

  // ── 操作 ─────────────────────────────────────────────────────────────────
  function resetSaveState(clearSuccess = true): void {
    saveDialogOpen.value  = false
    saveCaseError.value   = ''
    saveCaseSaving.value  = false
    savedCaseId.value     = null
    if (clearSuccess) saveCaseSuccess.value = ''
  }

  function resetResult(): void {
    result.value = null
    error.value  = ''
  }

  function openSaveDialog(): void {
    if (!result.value) return
    saveCaseError.value   = ''
    saveCaseSuccess.value = ''
    if (!saveCaseName.value.trim()) {
      saveCaseName.value = buildDefaultCaseName()
    }
    saveDialogOpen.value = true
  }

  function closeSaveDialog(): void {
    saveDialogOpen.value = false
    saveCaseError.value  = ''
  }

  async function doCalculate(): Promise<void> {
    if (!form.birthDt.value || form.lon.value === undefined) return
    loading.value = true
    error.value   = ''
    result.value  = null
    resetSaveState()
    try {
      const [datePart, timePart] = form.birthDt.value.split('T')
      const dt  = `${datePart}T${timePart || '00:00'}:00`
      const req: Parameters<typeof computeBazi>[0] = {
        dt,
        lon:               form.lon.value!,
        tz:                form.tz.value,
        mode:              form.mode.value,
        solar_time_enabled: form.solarTime.value,
      }
      if (form.gender.value) req.gender = form.gender.value
      result.value = await computeBazi(req)
    } catch (e: unknown) {
      error.value = extractErrorMessage(e, '排盘失败，请稍后重试')
    } finally {
      loading.value = false
    }
  }

  async function saveCurrentCase(): Promise<void> {
    if (!form.birthDt.value || form.lon.value === undefined) {
      saveCaseError.value = '出生信息不完整，无法保存案例'
      return
    }
    saveCaseSaving.value = true
    saveCaseError.value  = ''
    try {
      const created = await createCase({
        name:             saveCaseName.value.trim() || buildDefaultCaseName(),
        birth_dt_local:   normalizeBirthDtLocal(form.birthDt.value),
        tz:               form.tz.value,
        lon:              form.lon.value,
        gender:           form.gender.value || null,
        city:             form.cityName.value || form.initCity.value || null,
        solar_time_enabled: form.solarTime.value,
        notes:            saveCaseNotes.value.trim() || null,
      })
      savedCaseId.value    = created.id
      saveCaseSuccess.value = `已保存到案例库：${created.name}`
      saveDialogOpen.value  = false
    } catch (e: unknown) {
      saveCaseError.value = extractErrorMessage(e, '保存案例失败，请稍后重试')
    } finally {
      saveCaseSaving.value = false
    }
  }

  return {
    loading,
    error,
    result,
    savedCaseId,
    saveCaseName,
    saveCaseNotes,
    saveDialogOpen,
    saveCaseSaving,
    saveCaseError,
    saveCaseSuccess,
    doCalculate,
    openSaveDialog,
    closeSaveDialog,
    saveCurrentCase,
    resetSaveState,
    resetResult,
  }
}
