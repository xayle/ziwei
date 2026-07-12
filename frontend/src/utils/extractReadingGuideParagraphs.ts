import type { ExplainBatchResponse } from '@/api/explain'

/** 静态兜底（explain 未加载或失败时） */
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

export function resolveReadingGuideParagraphs(
  explain: ExplainBatchResponse | null | undefined,
): string[] {
  const dynamic = extractAllReadingGuideParagraphs(explain)
  return dynamic.length ? dynamic : [...DEFAULT_READING_GUIDE_PARAGRAPHS]
}
