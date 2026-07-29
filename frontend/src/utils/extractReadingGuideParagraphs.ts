import type { ExplainBatchResponse } from '@/api/explain'
import type { LifeVolumeResponse } from '@/types/life-volume'

/** 静态兜底（explain / volumes 均未提供读法时）；与 BE preface reading-guide 同源语义 */
export const DEFAULT_READING_GUIDE_PARAGRAPHS = [
  '全书按三层阅读：排盘推算（干支、宫星、运限等引擎事实）、典籍依据（有出处的句式与校勘）、经验推断（可读建议，默认不代替事实）。界面只用上述中文标签，不夹写英文层名。',
  '建议顺序：卷一格局与用神 → 卷二关系与神煞 → 卷三大运流年 → 卷四命身轴与十二宫 → 卷五事理（默认折叠）→ 卷六问书（需主动展开）。先立事实与读法，再追问具体事项；卷六不自动发起问书。',
] as const

/** Adapter / 单测复用的卷首读法块（与 BE `reading-guide` 对齐） */
export const PREFACE_READING_GUIDE_BLOCKS = [...DEFAULT_READING_GUIDE_PARAGRAPHS] as const

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
