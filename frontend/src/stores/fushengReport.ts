import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { analyzeName, suggestNames, type NameAnalysisResponse, type NameSuggestResponse } from '@/api/name'
import { computeBazi, dayunReportInline, type BaziResponse, type DayunReportResponse } from '@/api/bazi'
import { computeZiwei, type ZiweiResponse } from '@/api/ziwei'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import {
  buildBaziRequest,
  buildChartRequestMeta,
  buildProfileSignature,
  buildZiweiCacheKey,
  buildZiweiRequest,
  type ChartRequestMeta,
} from '@/utils/buildChartRequests'
import { buildDayunReportFromBazi } from '@/utils/buildDayunReport'
import { saveReportSnapshot } from '@/utils/saveReportSnapshot'
import type { FushengSnapshotOutput } from '@/utils/parseFushengSnapshot'
import { canAnalyzeName, isArchiveReady } from '@/utils/profileReadiness'
import { toCnElements } from '@/utils/yongshenElements'

export const useFushengReportStore = defineStore('fushengReport', () => {
  const loading = ref(false)
  const loadingBazi = ref(false)
  const loadingZiwei = ref(false)
  const loadingName = ref(false)
  const loadingDayun = ref(false)
  const loadingNameSuggest = ref(false)
  const error = ref('')
  const bazi = ref<BaziResponse | null>(null)
  const ziwei = ref<ZiweiResponse | null>(null)
  const nameAnalysis = ref<NameAnalysisResponse | null>(null)
  const dayunReport = ref<DayunReportResponse | null>(null)
  const nameSuggestions = ref<NameSuggestResponse | null>(null)
  const cachedSignature = ref('')
  const ziweiCacheKey = ref('')
  const ziweiTargetDate = ref<string | undefined>()
  const requestMeta = ref<ChartRequestMeta | null>(null)
  const generatedAt = ref('')
  const engineLabel = ref('引擎版本待计算')
  const dayunError = ref('')
  const snapshotNote = ref('')
  const skipSnapshotPersistAfterRestore = ref(false)
  const snapshotError = ref('')

  function updateEngineLabel(baziRes: BaziResponse | null, ziweiRes: ZiweiResponse | null) {
    const parts: string[] = []
    if (baziRes?.rule_version) parts.push(`八字 ${baziRes.rule_version}`)
    if (ziweiRes?.engine_version || ziweiRes?.algorithm_version) {
      parts.push(`紫微 ${ziweiRes.engine_version || ziweiRes.algorithm_version}`)
    }
    engineLabel.value = parts.length ? parts.join(' · ') : '引擎版本待计算'
  }

  function readProfileData() {
    return useProfileStore().asProfileData()
  }

  const isCacheValid = computed(() => {
    const data = readProfileData()
    return isArchiveReady(data)
      && !!cachedSignature.value
      && cachedSignature.value === buildProfileSignature(data)
      && !!bazi.value
  })

  const isZiweiCacheValid = computed(() => {
    const data = readProfileData()
    return isArchiveReady(data)
      && !!ziwei.value
      && !!ziweiCacheKey.value
      && ziweiCacheKey.value === buildZiweiCacheKey(data, ziweiTargetDate.value)
  })

  const isNameCacheValid = computed(() => {
    const data = readProfileData()
    if (!canAnalyzeName(data)) return false
    return isCacheValid.value && !!nameAnalysis.value && cachedSignature.value === buildProfileSignature(data)
  })

  function invalidate() {
    cachedSignature.value = ''
    ziweiCacheKey.value = ''
    ziweiTargetDate.value = undefined
    bazi.value = null
    ziwei.value = null
    nameAnalysis.value = null
    dayunReport.value = null
    nameSuggestions.value = null
    error.value = ''
    dayunError.value = ''
    snapshotNote.value = ''
    snapshotError.value = ''
    requestMeta.value = null
    generatedAt.value = ''
  }

  function ensureArchiveReady(): boolean {
    const data = readProfileData()
    if (!isArchiveReady(data)) {
      error.value = '请先补全档案必填项：出生时间、性别、出生地、经度。'
      return false
    }
    return true
  }

  async function loadNameAnalysis(force = false) {
    const data = readProfileData()
    if (!canAnalyzeName(data)) {
      nameAnalysis.value = null
      return null
    }

    const signature = buildProfileSignature(data)
    if (!force && cachedSignature.value === signature && nameAnalysis.value) {
      return nameAnalysis.value
    }

    loadingName.value = true
    error.value = ''

    try {
      const res = await analyzeName({
        surname: data.surname.trim(),
        given_name: data.givenName.trim(),
      })
      nameAnalysis.value = res
      return res
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      error.value = typeof detail === 'string' ? detail : '姓名分析失败，请稍后重试。'
      nameAnalysis.value = null
      return null
    } finally {
      loadingName.value = false
    }
  }

  async function loadBazi(force = false) {
    if (!ensureArchiveReady()) {
      bazi.value = null
      return null
    }

    const data = readProfileData()
    const signature = buildProfileSignature(data)
    requestMeta.value = buildChartRequestMeta(data)

    if (!force && cachedSignature.value === signature && bazi.value) {
      return bazi.value
    }

    loadingBazi.value = true
    error.value = ''

    try {
      const baziRes = await computeBazi(buildBaziRequest(data))
      bazi.value = baziRes
      cachedSignature.value = signature
      generatedAt.value = new Date().toISOString()
      updateEngineLabel(baziRes, ziwei.value)
      return baziRes
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      error.value = typeof detail === 'string' ? detail : '八字计算失败，请稍后重试。'
      bazi.value = null
      return null
    } finally {
      loadingBazi.value = false
    }
  }

  async function loadZiwei(force = false, targetDate?: string) {
    if (!ensureArchiveReady()) {
      ziwei.value = null
      return null
    }

    const data = readProfileData()
    const cacheKey = buildZiweiCacheKey(data, targetDate)
    requestMeta.value = buildChartRequestMeta(data)

    if (!force && ziweiCacheKey.value === cacheKey && ziwei.value) {
      return ziwei.value
    }

    loadingZiwei.value = true
    error.value = ''

    try {
      const ziweiRes = await computeZiwei(buildZiweiRequest(data, undefined, targetDate))
      ziwei.value = ziweiRes
      ziweiCacheKey.value = cacheKey
      ziweiTargetDate.value = targetDate
      cachedSignature.value = buildProfileSignature(data)
      generatedAt.value = new Date().toISOString()
      updateEngineLabel(bazi.value, ziweiRes)
      return ziweiRes
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      error.value = typeof detail === 'string' ? detail : '紫微计算失败，请稍后重试。'
      ziwei.value = null
      return null
    } finally {
      loadingZiwei.value = false
    }
  }

  async function loadDayunNarratives(force = false) {
    if (!ensureArchiveReady()) {
      dayunReport.value = null
      return null
    }

    const data = readProfileData()
    const signature = buildProfileSignature(data)
    if (!force && cachedSignature.value === signature && dayunReport.value) {
      return dayunReport.value
    }

    loadingDayun.value = true
    dayunError.value = ''
    try {
      const fromBazi = !force ? buildDayunReportFromBazi(bazi.value) : null
      if (fromBazi) {
        dayunReport.value = fromBazi
        return fromBazi
      }
      const res = await dayunReportInline(buildBaziRequest(data))
      dayunReport.value = res
      return res
    } catch {
      dayunReport.value = null
      dayunError.value = '大运叙事加载失败，仅显示干支序列。'
      return null
    } finally {
      loadingDayun.value = false
    }
  }

  async function loadNameSuggestions(force = false) {
    const data = readProfileData()
    const surname = data.surname?.trim()
    if (!surname) {
      nameSuggestions.value = null
      return null
    }

    const signature = buildProfileSignature(data)
    if (!force && cachedSignature.value === signature && nameSuggestions.value) {
      return nameSuggestions.value
    }

    loadingNameSuggest.value = true
    try {
      const favor = toCnElements(bazi.value?.yongshen?.favor)
      const res = await suggestNames({
        surname,
        name_length: 2,
        preferred_elements: favor.length ? favor : undefined,
        top_n: 5,
        min_score: 60,
      })
      nameSuggestions.value = res
      return res
    } catch {
      nameSuggestions.value = null
      return null
    } finally {
      loadingNameSuggest.value = false
    }
  }

  async function persistReportSnapshot(signature: string) {
    if (skipSnapshotPersistAfterRestore.value) {
      skipSnapshotPersistAfterRestore.value = false
      return
    }
    const auth = useAuthStore()
    if (!auth.isLoggedIn || !bazi.value || !ziwei.value) return

    const profileStore = useProfileStore()
    let caseId = profileStore.activeProfile?.remoteCaseId ?? null
    if (!caseId) {
      const sync = await profileStore.syncRemoteCase()
      if (sync.ok && sync.caseId) {
        caseId = sync.caseId
      }
    }
    if (!caseId) return

    const snap = await saveReportSnapshot({
      caseId,
      bazi: bazi.value,
      ziwei: ziwei.value,
      profileSignature: signature,
      generatedAt: generatedAt.value,
    })
    if (snap.ok) {
      snapshotNote.value = snap.snapshotId
        ? `报告已自动存档（快照 ${snap.snapshotId.slice(0, 8)}…）`
        : '报告已自动存档。'
      snapshotError.value = ''
      void profileStore.pullRemoteSnapshots()
    } else if (!snap.skipped) {
      snapshotError.value = snap.error || '快照保存失败。'
    }
  }

  async function loadReport(force = false) {
    if (!ensureArchiveReady()) {
      bazi.value = null
      ziwei.value = null
      nameAnalysis.value = null
      dayunReport.value = null
      return
    }

    const data = readProfileData()
    const signature = buildProfileSignature(data)
    requestMeta.value = buildChartRequestMeta(data)

    const chartsCached = !force && cachedSignature.value === signature && bazi.value && ziwei.value
    const nameCached = !force && cachedSignature.value === signature && (
      !canAnalyzeName(data) || !!nameAnalysis.value
    )
    const dayunCached = !force && cachedSignature.value === signature && !!dayunReport.value

    if (chartsCached && nameCached && dayunCached) {
      return
    }

    loading.value = true
    error.value = ''

    try {
      type TaskKey = 'bazi' | 'ziwei' | 'name'
      const taskList: Array<{ key: TaskKey; promise: Promise<unknown> }> = [
        { key: 'bazi', promise: computeBazi(buildBaziRequest(data)) },
        { key: 'ziwei', promise: computeZiwei(buildZiweiRequest(data)) },
      ]
      if (canAnalyzeName(data)) {
        taskList.push({
          key: 'name',
          promise: analyzeName({
            surname: data.surname.trim(),
            given_name: data.givenName.trim(),
          }),
        })
      }

      const settled = await Promise.allSettled(taskList.map((task) => task.promise))
      const failures: string[] = []

      settled.forEach((result, idx) => {
        const key = taskList[idx].key
        if (result.status === 'fulfilled') {
          if (key === 'bazi') bazi.value = result.value as BaziResponse
          else if (key === 'ziwei') ziwei.value = result.value as ZiweiResponse
          else nameAnalysis.value = result.value as NameAnalysisResponse
          return
        }

        const detail = (result.reason as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        const message = typeof detail === 'string' ? detail : '加载失败'
        if (key === 'bazi') {
          bazi.value = null
          failures.push(`八字：${message}`)
        } else if (key === 'ziwei') {
          ziwei.value = null
          failures.push(`紫微：${message}`)
        } else {
          nameAnalysis.value = null
          failures.push(`姓名：${message}`)
        }
      })

      if (!bazi.value && !ziwei.value) {
        error.value = failures.join('；') || '报告生成失败，请稍后重试。'
        dayunReport.value = null
        return
      }

      if (!canAnalyzeName(data)) {
        nameAnalysis.value = null
      }

      cachedSignature.value = signature
      generatedAt.value = new Date().toISOString()
      updateEngineLabel(bazi.value, ziwei.value)
      error.value = failures.length ? `部分模块加载失败：${failures.join('；')}` : ''
      const cachedDayun = buildDayunReportFromBazi(bazi.value)
      dayunReport.value = cachedDayun
      await persistReportSnapshot(signature)
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      error.value = typeof detail === 'string' ? detail : '报告生成失败，请稍后重试。'
      bazi.value = null
      ziwei.value = null
      nameAnalysis.value = null
      dayunReport.value = null
    } finally {
      loading.value = false
    }
  }

  function restoreFromSnapshot(output: FushengSnapshotOutput) {
    if (output.bazi) bazi.value = output.bazi
    if (output.ziwei) ziwei.value = output.ziwei
    const data = readProfileData()
    cachedSignature.value = buildProfileSignature(data)
    generatedAt.value = new Date().toISOString()
    updateEngineLabel(bazi.value, ziwei.value)
    dayunReport.value = buildDayunReportFromBazi(bazi.value)
    error.value = ''
    snapshotNote.value = '已从云端快照恢复排盘数据。'
    snapshotError.value = ''
    skipSnapshotPersistAfterRestore.value = true
  }

  return {
    loading,
    loadingBazi,
    loadingZiwei,
    loadingName,
    loadingDayun,
    loadingNameSuggest,
    error,
    bazi,
    ziwei,
    nameAnalysis,
    dayunReport,
    nameSuggestions,
    cachedSignature,
    requestMeta,
    generatedAt,
    engineLabel,
    dayunError,
    snapshotNote,
    snapshotError,
    ziweiTargetDate,
    isCacheValid,
    isZiweiCacheValid,
    isNameCacheValid,
    invalidate,
    loadBazi,
    loadZiwei,
    loadNameAnalysis,
    loadDayunNarratives,
    loadNameSuggestions,
    loadReport,
    restoreFromSnapshot,
  }
})
