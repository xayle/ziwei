/**
 * life-volume@1.0 — 与 docs/contracts/life-volume.schema.json 对齐
 * FE Adapter：buildLifeVolumes (W3–W15) · BE 权威：GET /life/volumes (W16+)
 */

export type LifeVolumeId =
  | 'preface'
  | 'vol1'
  | 'vol2'
  | 'vol3'
  | 'vol4'
  | 'vol5'
  | 'vol6'
  | 'colophon'

/** 用户语义层（UI 文案：排盘推算 / 典籍依据 / 经验推断） */
export type ContentLayer = 'fact' | 'cite' | 'inference'

export type TrustLevel = 'full' | 'degraded'

export interface DisclaimerBlock {
  text: string
  version: string
  jurisdiction?: string
}

export interface ContentVersions {
  classics?: string
  glossary?: string
  concepts?: string
  star_profiles?: string
  wenmo_reference_cases?: string
}

/** UI 三层标签（FE-BE Q5 · VolumeSection 用） */
export const CONTENT_LAYER_LABELS: Record<ContentLayer, string> = {
  fact: '排盘推算',
  cite: '典籍依据',
  inference: '经验推断',
}

export interface AnalysisBlock {
  text: string
  layer: ContentLayer
  evidence_ids?: string[]
  classic_id?: string
  glossary_refs?: string[]
  score?: number
  tier?: string
}

export interface VolumeSection {
  id: string
  heading: string
  layer: ContentLayer
  collapsed_default?: boolean
  blocks: AnalysisBlock[]
}

export interface LifeVolume {
  id: LifeVolumeId
  title: string
  subtitle?: string
  locked?: boolean
  sections: VolumeSection[]
}

export interface Colophon {
  summary_lines: string[]
  missing_fields?: string[]
  iztro_advisory?: string
  wenmo_advisory?: string
  dual_track_note?: string
  expandable?: boolean
}

export interface LifeVolumeResponse {
  schema_version: 'life-volume@1.0'
  case_id: string
  chart_hash: string
  rule_version?: string
  content_versions?: ContentVersions
  disclaimer_block: DisclaimerBlock
  trust_level?: TrustLevel
  volumes: LifeVolume[]
  colophon: Colophon
}

/** provenance API 层 → UI ContentLayer（FE-BE Q5） */
export const PROVENANCE_TO_CONTENT_LAYER = {
  engine: 'fact',
  classical: 'cite',
  heuristic: 'inference',
} as const satisfies Record<string, ContentLayer>

export const LIFE_VOLUME_LABELS: Record<LifeVolumeId, string> = {
  preface: '卷首',
  vol1: '卷一·命之根',
  vol2: '卷二·业之象',
  vol3: '卷三·运之波',
  vol4: '卷四·宫之图',
  vol5: '卷五·事之理',
  vol6: '卷六·问书',
  colophon: '跋·校勘',
}
