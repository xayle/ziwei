import { nextTick, type Ref } from 'vue'
import type { Router, RouteLocationNormalizedLoaded, LocationQueryRaw } from 'vue-router'
import { computeZiwei, demoZiwei, type ZiweiResponse } from '@/api/ziwei'
import { loadZiweiCaseWorkflowContext } from '@/utils/ziweiCaseWorkflowContext'

type ProfileLike = {
  parseBirthDt: () => { year: number; month: number; day: number; hour: number; minute: number }
  gender?: string
  lon?: number | null
  cityName?: string | null
  saved?: boolean
}

type WorkflowLike = {
  clearSavedCaseState: () => void
  applySavedCaseState: (incoming: unknown) => void
}

type UseZiweiCalculationFlowOptions = {
  route: RouteLocationNormalizedLoaded
  router: Router
  profile: ProfileLike
  workflowActions: WorkflowLike
  result: Ref<ZiweiResponse | null>
  loading: Ref<boolean>
  error: Ref<string>
  activeTab: Ref<string>
  selectedPalace: Ref<unknown | null>
  showForm: Ref<boolean>
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  minute: Ref<number>
  gender: Ref<'男' | '女'>
  liunianYear: Ref<number | undefined>
  longitude: Ref<number | undefined>
  initCity: Ref<string>
  algoLateZishi: Ref<boolean>
  algoLeapMethod: Ref<'mid' | 'next' | 'same'>
  algoKuiyue: Ref<'standard' | 'gengxin_mahu' | 'gengxin_huima' | 'liuxin_mahu'>
  algoTianma: Ref<'year' | 'month'>
  algoTiankong: Ref<'standard' | 'shun'>
  algoBrightness: Ref<'standard' | 'zhongzhou' | 'mod1' | 'mod2'>
  algoJiukong: Ref<'dual' | 'single' | 'zhanyan'>
  algoTianshang: Ref<'standard' | 'zhongzhou'>
  algoMingzhu: Ref<'quanshu' | 'zhongzhou'>
  algoLiunianSihua: Ref<'year_stem' | 'life_palace_stem'>
  algoChangsheng: Ref<'standard' | 'water_earth' | 'fire_earth'>
  buildSihuaIndices: () => Record<string, number> | undefined
  saveToHistory: () => void
}

export function useZiweiCalculationFlow(options: UseZiweiCalculationFlowOptions) {
  function parseZiweiApiError(e: unknown, fallback: string): string {
    return parseZiweiApiErrorMessage(e, fallback)
  }

  function validateZiweiForm(): string | null {
    if (!Number.isInteger(options.year.value) || options.year.value < 1900 || options.year.value > 2100) return '年份需在 1900-2100 之间'
    if (!Number.isInteger(options.month.value) || options.month.value < 1 || options.month.value > 12) return '月份需在 1-12 之间'
    if (!Number.isInteger(options.day.value) || options.day.value < 1 || options.day.value > 31) return '日期不合法，请检查年月日'
    if (!Number.isInteger(options.hour.value) || options.hour.value < 0 || options.hour.value > 23) return '小时需在 0-23 之间'
    if (!Number.isInteger(options.minute.value) || options.minute.value < 0 || options.minute.value > 59) return '分钟需在 0-59 之间'
    if (!['男', '女'].includes(options.gender.value)) return '性别仅支持 男/女'

    const validDate = new Date(options.year.value, options.month.value - 1, options.day.value)
    if (
      validDate.getFullYear() !== options.year.value ||
      validDate.getMonth() !== options.month.value - 1 ||
      validDate.getDate() !== options.day.value
    ) {
      return '日期不合法，请检查年月日'
    }

    if (options.longitude.value !== undefined && options.longitude.value !== null) {
      if (!Number.isFinite(options.longitude.value) || options.longitude.value < -180 || options.longitude.value > 180) {
        return '经度需在 -180 到 180 之间'
      }
    }
    return null
  }

  function clearSavedCaseState() {
    options.workflowActions.clearSavedCaseState()
  }

  function restoreCaseWorkflowContextFromRoute(): boolean {
    if (options.route.query.context !== 'case-workflow') return false
    const incoming = loadZiweiCaseWorkflowContext()
    if (!incoming?.chartInput || !incoming.chartResult) return false

    options.year.value = incoming.chartInput.year
    options.month.value = incoming.chartInput.month
    options.day.value = incoming.chartInput.day
    options.hour.value = incoming.chartInput.hour
    options.minute.value = incoming.chartInput.minute
    options.gender.value = incoming.chartInput.gender
    options.longitude.value = incoming.chartInput.longitude ?? undefined
    options.liunianYear.value = incoming.chartInput.liunian_year ?? undefined
    if (incoming.chartInput.city_name) options.initCity.value = incoming.chartInput.city_name

    options.result.value = incoming.chartResult
    options.activeTab.value = 'chart'
    options.selectedPalace.value = null
    options.workflowActions.applySavedCaseState(incoming)

    const nextQuery = { ...options.route.query } as LocationQueryRaw
    delete nextQuery.context
    delete nextQuery.from
    options.router.replace({ query: nextQuery })
    return true
  }

  async function doCalculate() {
    const validationError = validateZiweiForm()
    if (validationError) {
      options.error.value = validationError
      return
    }

    options.loading.value = true
    options.error.value = ''
    options.result.value = null
    options.selectedPalace.value = null
    clearSavedCaseState()

    try {
      options.result.value = await computeZiwei({
        year: options.year.value,
        month: options.month.value,
        day: options.day.value,
        hour: options.hour.value,
        minute: options.minute.value,
        gender: options.gender.value,
        liunian_year: options.liunianYear.value || undefined,
        longitude: options.longitude.value || undefined,
        late_zishi: options.algoLateZishi.value,
        leap_month_method: options.algoLeapMethod.value,
        kuiyue_method: options.algoKuiyue.value,
        sihua_stem_indices: options.buildSihuaIndices(),
        tianma_method: options.algoTianma.value,
        tiankong_method: options.algoTiankong.value,
        brightness_method: options.algoBrightness.value,
        jiukong_method: options.algoJiukong.value,
        tianshang_method: options.algoTianshang.value,
        mingzhu_method: options.algoMingzhu.value,
        liunian_sihua_method: options.algoLiunianSihua.value,
        changsheng_method: options.algoChangsheng.value,
      })
      options.activeTab.value = 'chart'
      options.saveToHistory()
    } catch (e: unknown) {
      options.error.value = parseZiweiApiError(e, '排盘失败，请稍后重试')
    } finally {
      options.loading.value = false
    }
  }

  async function doDemo() {
    options.loading.value = true
    options.error.value = ''
    options.result.value = null
    options.selectedPalace.value = null
    clearSavedCaseState()
    try {
      options.result.value = await demoZiwei()
      options.activeTab.value = 'chart'
    } catch (e: unknown) {
      options.error.value = parseZiweiApiError(e, '演示命盘加载失败')
    } finally {
      options.loading.value = false
    }
  }

  function resetForm() {
    const bd = options.profile.parseBirthDt()
    options.year.value = bd.year
    options.month.value = bd.month
    options.day.value = bd.day
    options.hour.value = bd.hour
    options.minute.value = bd.minute
    options.gender.value = options.profile.gender === 'female' ? '女' : '男'
    options.liunianYear.value = undefined
    options.longitude.value = options.profile.lon ?? undefined
    options.initCity.value = options.profile.cityName || '北京'
    options.result.value = null
    options.error.value = ''
    clearSavedCaseState()
  }

  function loadFromUrlParams() {
    const params = new URLSearchParams(window.location.search)
    if (params.has('y') && params.has('m') && params.has('d')) {
      options.year.value = parseInt(params.get('y') || '1990')
      options.month.value = parseInt(params.get('m') || '1')
      options.day.value = parseInt(params.get('d') || '1')
      options.hour.value = parseInt(params.get('h') || '12')
      options.minute.value = parseInt(params.get('mi') || '0')
      options.gender.value = (params.get('g') as '男' | '女') || '男'
      if (params.has('lng')) options.longitude.value = parseFloat(params.get('lng') || '')
      window.history.replaceState({}, '', window.location.pathname)
      nextTick(() => doCalculate())
    }
  }

  function initializeFromProfileAndRoute() {
    const bd = options.profile.parseBirthDt()
    options.year.value = bd.year
    options.month.value = bd.month
    options.day.value = bd.day
    options.hour.value = bd.hour
    options.minute.value = bd.minute
    options.gender.value = options.profile.gender === 'female' ? '女' : '男'
    options.longitude.value = options.profile.lon ?? undefined
    options.initCity.value = options.profile.cityName || '北京'

    const restoredFromCaseWorkflow = restoreCaseWorkflowContextFromRoute()
    if (!restoredFromCaseWorkflow && options.profile.saved) {
      options.showForm.value = false
      nextTick(() => doCalculate())
    } else if (restoredFromCaseWorkflow) {
      options.showForm.value = false
    }
  }

  return {
    parseZiweiApiError,
    validateZiweiForm,
    clearSavedCaseState,
    restoreCaseWorkflowContextFromRoute,
    doCalculate,
    doDemo,
    resetForm,
    loadFromUrlParams,
    initializeFromProfileAndRoute,
  }
}

export function parseZiweiApiErrorMessage(e: unknown, fallback: string): string {
  if (e && typeof e === 'object') {
    const maybeResponse = (e as { response?: { data?: { detail?: unknown } } }).response
    const detail = maybeResponse?.data?.detail
    if (typeof detail === 'string' && detail.trim()) return detail

    if (Array.isArray(detail)) {
      const msgs = detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (item && typeof item === 'object') {
            const maybeMsg = (item as { msg?: unknown }).msg
            if (typeof maybeMsg === 'string') return maybeMsg
          }
          return ''
        })
        .filter(Boolean)
      if (msgs.length) return msgs.join('；')
    }

    if (detail && typeof detail === 'object') {
      const maybeMsg = (detail as { message?: unknown }).message
      if (typeof maybeMsg === 'string' && maybeMsg.trim()) return maybeMsg
    }
  }

  const directMsg = (e as { message?: string })?.message
  if (typeof directMsg === 'string' && directMsg.trim()) return directMsg
  return fallback
}
