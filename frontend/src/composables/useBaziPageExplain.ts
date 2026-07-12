import { computed, ref, shallowRef } from 'vue'
import { fetchBaziExplainBatchWithMeta, type ExplainBatchResponse } from '@/api/explain'
import { BAZI_PAGE_EXPLAIN_SECTIONS } from '@/constants/feBeContract'
import type { ProfileData } from '@/stores/profile'
import { buildBaziRequest } from '@/utils/buildChartRequests'
import { explainSectionsToAnalysisBlocks } from '@/utils/explainSectionsToAnalysisBlocks'

export function useBaziPageExplain() {
  const loadingExplain = ref(false)
  const explainFailed = ref(false)
  const explainBatch = shallowRef<ExplainBatchResponse | null>(null)
  let loadToken = 0

  async function loadPageExplain(profileData: ProfileData) {
    if (!profileData.birthDt) return
    const token = ++loadToken
    loadingExplain.value = true
    explainFailed.value = false
    const result = await fetchBaziExplainBatchWithMeta(
      [...BAZI_PAGE_EXPLAIN_SECTIONS],
      buildBaziRequest(profileData) as unknown as Record<string, unknown>,
    )
    if (token !== loadToken) return
    loadingExplain.value = false
    if (!result.ok) {
      explainFailed.value = true
      explainBatch.value = null
      return
    }
    explainBatch.value = result.data
    explainFailed.value = !result.data.sections.some((section) => section.blocks.length > 0)
  }

  function resetPageExplain() {
    loadToken += 1
    loadingExplain.value = false
    explainFailed.value = false
    explainBatch.value = null
  }

  const explainAnalysisBlocks = computed(() => (
    explainBatch.value
      ? explainSectionsToAnalysisBlocks(explainBatch.value.sections)
      : []
  ))

  const hasExplainContent = computed(() => explainAnalysisBlocks.value.length > 0)

  return {
    loadingExplain,
    explainFailed,
    explainBatch,
    explainAnalysisBlocks,
    hasExplainContent,
    loadPageExplain,
    resetPageExplain,
  }
}
