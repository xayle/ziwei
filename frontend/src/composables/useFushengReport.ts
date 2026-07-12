import { storeToRefs } from 'pinia'
import { useProfileStore } from '@/stores/profile'
import { useFushengReportStore } from '@/stores/fushengReport'

export function useFushengReport() {
  const profile = useProfileStore()
  const reportStore = useFushengReportStore()
  const {
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
    isCacheValid,
    isNameCacheValid,
    requestMeta,
    generatedAt,
    engineLabel,
    dayunError,
    snapshotNote,
    snapshotError,
  } = storeToRefs(reportStore)

  return {
    profile,
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
    isCacheValid,
    isNameCacheValid,
    requestMeta,
    generatedAt,
    engineLabel,
    dayunError,
    snapshotNote,
    snapshotError,
    loadReport: (force = false) => reportStore.loadReport(force),
    loadBazi: (force = false) => reportStore.loadBazi(force),
    loadZiwei: (force = false, targetDate?: string) => reportStore.loadZiwei(force, targetDate),
    loadNameAnalysis: (force = false) => reportStore.loadNameAnalysis(force),
    loadDayunNarratives: (force = false) => reportStore.loadDayunNarratives(force),
    loadNameSuggestions: (force = false) => reportStore.loadNameSuggestions(force),
    restoreFromSnapshot: (output: Parameters<typeof reportStore.restoreFromSnapshot>[0]) =>
      reportStore.restoreFromSnapshot(output),
    invalidate: () => reportStore.invalidate(),
  }
}
