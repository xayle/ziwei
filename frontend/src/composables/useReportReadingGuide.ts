import { computed, toRef, type MaybeRefOrGetter } from 'vue'
import type { ExplainBatchResponse } from '@/api/explain'
import type { LifeVolumeResponse } from '@/types/life-volume'
import {
  extractAllReadingGuideParagraphs,
  extractReadingGuideFromLifeVolumes,
  resolveReadingGuideParagraphs,
} from '@/utils/extractReadingGuideParagraphs'

/**
 * 报告页 ReadingGuide：
 * - 优先 explain/batch 的 reading section（本地 Adapter 路径）
 * - 否则 life/volumes preface reading-guide（T082 volumes 权威，避免再拼 explain）
 */
export function useReportReadingGuide(
  explainBatch: MaybeRefOrGetter<ExplainBatchResponse | null>,
  lifeVolume?: MaybeRefOrGetter<LifeVolumeResponse | null | undefined>,
) {
  const batch = toRef(explainBatch)
  const volumeDoc = lifeVolume ? toRef(lifeVolume) : null
  const readingParagraphs = computed(() => resolveReadingGuideParagraphs(
    batch.value,
    volumeDoc?.value ?? null,
  ))
  const usingDynamicReading = computed(() => (
    extractAllReadingGuideParagraphs(batch.value).length > 0
    || extractReadingGuideFromLifeVolumes(volumeDoc?.value).length > 0
  ))
  const readingFailed = computed(() => (
    Boolean(batch.value) && extractAllReadingGuideParagraphs(batch.value).length === 0
    && extractReadingGuideFromLifeVolumes(volumeDoc?.value).length === 0
  ))
  return { readingParagraphs, usingDynamicReading, readingFailed }
}
