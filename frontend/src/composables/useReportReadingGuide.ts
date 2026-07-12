import { computed, toRef, type MaybeRefOrGetter } from 'vue'
import type { ExplainBatchResponse } from '@/api/explain'
import {
  extractAllReadingGuideParagraphs,
  resolveReadingGuideParagraphs,
} from '@/utils/extractReadingGuideParagraphs'

/** 报告页：从已加载的 explain batch 派生 ReadingGuide 文案 */
export function useReportReadingGuide(explainBatch: MaybeRefOrGetter<ExplainBatchResponse | null>) {
  const batch = toRef(explainBatch)
  const readingParagraphs = computed(() => resolveReadingGuideParagraphs(batch.value))
  const usingDynamicReading = computed(() => extractAllReadingGuideParagraphs(batch.value).length > 0)
  const readingFailed = computed(() => (
    Boolean(batch.value) && !usingDynamicReading.value
  ))
  return { readingParagraphs, usingDynamicReading, readingFailed }
}
