import { computed, ref, shallowRef } from 'vue'
import {
  fetchBaziExplainBatchWithMeta,
  fetchZiweiExplainBatchWithMeta,
  type ExplainBatchResponse,
} from '@/api/explain'
import { BAZI_PAGE_EXPLAIN_SECTIONS, ZIWEI_PAGE_EXPLAIN_SECTIONS } from '@/constants/feBeContract'
import type { ProfileData } from '@/stores/profile'
import { buildBaziRequest, buildZiweiRequest } from '@/utils/buildChartRequests'
import {
  extractAllReadingGuideParagraphs,
  resolveReadingGuideParagraphs,
} from '@/utils/extractReadingGuideParagraphs'

export function useReadingGuideExplain() {
  const loadingReading = ref(false)
  const readingFailed = ref(false)
  const explainBatch = shallowRef<ExplainBatchResponse | null>(null)
  let inflight: Promise<void> | null = null

  async function loadReadingGuide(profileData: ProfileData) {
    if (!profileData.birthDt) return
    if (inflight) {
      await inflight
      return
    }
    inflight = (async () => {
      loadingReading.value = true
      readingFailed.value = false
      const [baziResult, ziweiResult] = await Promise.all([
        fetchBaziExplainBatchWithMeta(
          [...BAZI_PAGE_EXPLAIN_SECTIONS],
          buildBaziRequest(profileData) as unknown as Record<string, unknown>,
        ),
        fetchZiweiExplainBatchWithMeta(
          [...ZIWEI_PAGE_EXPLAIN_SECTIONS],
          buildZiweiRequest(profileData) as unknown as Record<string, unknown>,
        ),
      ])
      loadingReading.value = false

      const mergedSections = [
        ...(baziResult.ok ? baziResult.data.sections : []),
        ...(ziweiResult.ok ? ziweiResult.data.sections : []),
      ]
      explainBatch.value = { sections: mergedSections }
      const dynamic = extractAllReadingGuideParagraphs(explainBatch.value)
      readingFailed.value = !baziResult.ok && !ziweiResult.ok
      if (!dynamic.length) {
        readingFailed.value = true
        explainBatch.value = null
      }
    })()
    try {
      await inflight
    } finally {
      inflight = null
    }
  }

  function resetReadingGuide() {
    inflight = null
    loadingReading.value = false
    readingFailed.value = false
    explainBatch.value = null
  }

  const readingParagraphs = computed(() => resolveReadingGuideParagraphs(explainBatch.value))
  const usingDynamicReading = computed(() => (
    !readingFailed.value && extractAllReadingGuideParagraphs(explainBatch.value).length > 0
  ))

  return {
    loadingReading,
    readingFailed,
    readingParagraphs,
    usingDynamicReading,
    loadReadingGuide,
    resetReadingGuide,
  }
}
