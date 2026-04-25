/**
 * glossaryData.ts — 术语词条静态数据模块
 * 直接 import glossary.json，导出为 Map<term, entry>（同步，无异步延迟）
 * 供 store、CardGlossary、ReportSectionList 等共同复用
 */
import glossaryJson from '@/assets/glossary.json'

export interface GlossaryEntry {
  term: string
  pinyin?: string
  definition: string
  category?: string
  classic_source?: string
}

export const GLOSSARY_LIST: GlossaryEntry[] = glossaryJson as unknown as GlossaryEntry[]

/** 术语词条查询 Map，key = term（O(1) 查询） */
export const GLOSSARY_MAP = new Map<string, GlossaryEntry>(
  GLOSSARY_LIST.map(e => [e.term, e])
)

/**
 * 按 term 查询词条，未找到返回含默认提示的兜底对象
 */
export function lookupGlossary(term: string): GlossaryEntry {
  return (
    GLOSSARY_MAP.get(term) ?? { term, definition: '（词条暂未收录）' }
  )
}
