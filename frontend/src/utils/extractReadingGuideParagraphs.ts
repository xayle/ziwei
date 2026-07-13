import type { ExplainBatchResponse } from '@/api/explain'
import type { LifeVolumeResponse } from '@/types/life-volume'

/** 静态兜底（explain / volumes 均未提供读法时） */
export const DEFAULT_READING_GUIDE_PARAGRAPHS = [
  '六卷辑录按分层阅读；卷五推断默认折叠，卷六问书需主动展开。',
] as const

/** 从 explain batch 提取全部 reading section 段落（支持八字/紫微分轨各一节） */
export function extractAllReadingGuideParagraphs(
  explain: ExplainBatchResponse | null | undefined,
): string[] {
  if (!explain?.sections.length) return []
  const texts: string[] = []
  const seen = new Set<string>()
  for (const section of explain.sections) {
    if (section.section_id !== 'reading') continue
    for (const block of section.blocks) {
      const text = block.text.trim()
      if (text && !seen.has(text)) {
        seen.add(text)
        texts.push(text)
      }
    }
  }
  return texts
}

/** T082：从 life/volumes 的 preface.reading-guide 提取读法（volumes 已含 explain 时不再依赖 batch） */
export function extractReadingGuideFromLifeVolumes(
  doc: LifeVolumeResponse | null | undefined,
): string[] {
  if (!doc?.volumes?.length) return []
  const preface = doc.volumes.find((v) => v.id === 'preface')
  if (!preface?.sections?.length) return []
  const texts: string[] = []
  const seen = new Set<string>()
  for (const section of preface.sections) {
    if (section.id !== 'reading-guide' && section.id !== 'bazi-reading') continue
    for (const block of section.blocks ?? []) {
      const text = (block.text ?? '').trim()
      if (text && !seen.has(text)) {
        seen.add(text)
        texts.push(text)
      }
    }
  }
  return texts
}

export function resolveReadingGuideParagraphs(
  explain: ExplainBatchResponse | null | undefined,
  lifeVolume?: LifeVolumeResponse | null,
): string[] {
  const fromExplain = extractAllReadingGuideParagraphs(explain)
  if (fromExplain.length) return fromExplain
  const fromVolumes = extractReadingGuideFromLifeVolumes(lifeVolume)
  if (fromVolumes.length) return fromVolumes
  return [...DEFAULT_READING_GUIDE_PARAGRAPHS]
}
