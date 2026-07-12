/**
 * FE-BE 契约常量 — 与 docs/contracts/*.json 对齐
 * @see docs/plan/FE-BE-DECISIONS.md
 * @see docs/contracts/explain-section-map.json
 * @see docs/contracts/life-volume.schema.json
 */

/** life-volume@1.0 schema version (Q1 / R096) */
export const LIFE_VOLUME_SCHEMA_VERSION = 'life-volume@1.0' as const

/** W8–W15：本地 Adapter；W16+：GET /life/volumes 权威 */
export type LifeVolumeLoadPhase = 'w8_adapter' | 'w16_authority'

export const LIFE_VOLUME_LOAD_PHASE: LifeVolumeLoadPhase = 'w8_adapter'

/**
 * 报告页 explain/batch 节 ID（≤4 请求 · FE-BE Q9 · explain-section-map report_page）
 * 八字 4 + 紫微 2 合并为 2 次 batch POST（各 ≤4 sections）
 */
export const REPORT_BAZI_EXPLAIN_SECTIONS = [
  'geju',
  'relations',
  'domains',
  'summary',
] as const

export const REPORT_ZIWEI_EXPLAIN_SECTIONS = [
  'palaces',
  'fortune',
] as const

/** 八字工作台 explain（可选预载） */
export const BAZI_PAGE_EXPLAIN_SECTIONS = ['geju', 'relations', 'reading'] as const

/** 紫微工作台 explain（可选预载） */
export const ZIWEI_PAGE_EXPLAIN_SECTIONS = ['palaces', 'reading'] as const

export type BaziExplainSectionId = (typeof REPORT_BAZI_EXPLAIN_SECTIONS)[number]
  | (typeof BAZI_PAGE_EXPLAIN_SECTIONS)[number]
export type ZiweiExplainSectionId = (typeof REPORT_ZIWEI_EXPLAIN_SECTIONS)[number]
  | (typeof ZIWEI_PAGE_EXPLAIN_SECTIONS)[number]

/** explain section → 六卷 volume_id（节选 · 完整见 explain-section-map.json） */
export const EXPLAIN_VOLUME_MAP: Record<string, string> = {
  geju: 'vol1',
  yongshen: 'vol1',
  summary: 'vol1',
  relations: 'vol2',
  dayun: 'vol3',
  fortune: 'vol3',
  palaces: 'vol4',
  patterns: 'vol4',
  domains: 'vol5',
  reading: 'preface',
}

/** API provenance.layer → UI ContentLayer（FE-BE Q5） */
export const PROVENANCE_LAYER_TO_CONTENT = {
  engine: 'fact',
  classical: 'cite',
  heuristic: 'inference',
  modern_convention: 'fact',
} as const

/** API provenance.layer → 信任面板短标签 */
export const PROVENANCE_LAYER_TRUST_LABELS: Record<string, string> = {
  classical: '典籍',
  engine: '引擎',
  heuristic: '启发式',
  modern_convention: '现代约定',
}

/** 打磨期：卷 locked 恒 false（FE-BE Q2） */
export const LIFE_VOLUME_LOCKED_DEFAULT = false

/** localStorage 续读键前缀（FE-BE Q13） */
export const READING_PROGRESS_STORAGE_KEY = 'fusheng-reading-progress'

/** 环境变量：强制走 GET life/volumes（开发联调） */
export const ENV_USE_LIFE_VOLUMES_API = 'VITE_USE_LIFE_VOLUMES_API'
