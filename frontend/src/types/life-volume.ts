/**
 * life-volume@1.0 — OpenAPI `LifeVolumeResponseModel` + UI 常量
 * BE 权威：GET /life/volumes（W16+ / T079+）
 * FE Adapter：`buildLifeVolumes` **@deprecated（T081）** — 仅无 remote 回退与测试
 */
import type {
  AnalysisBlockModel,
  ColophonModel,
  DisclaimerBlockModel,
  LifeVolumeModel,
  LifeVolumeResponseModel,
  VolumeSectionModel,
} from '@/api/openapiTypes'

export type LifeVolumeId = LifeVolumeModel['id']

/** 用户语义层（UI 文案：排盘推算 / 典籍依据 / 经验推断） */
export type ContentLayer = AnalysisBlockModel['layer']

export type TrustLevel = NonNullable<LifeVolumeResponseModel['trust_level']>

export type DisclaimerBlock = DisclaimerBlockModel

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

/** Adapter 块可含 glossary / score 等扩展字段 */
export type AnalysisBlock = AnalysisBlockModel & {
  glossary_refs?: string[]
  score?: number
  tier?: string
}

export type VolumeSection = VolumeSectionModel

/** 卷 subtitle 为 FE Adapter 扩展，OpenAPI LifeVolumeModel 未建模 */
export type LifeVolume = LifeVolumeModel & {
  subtitle?: string
}

export type Colophon = ColophonModel

export type LifeVolumeResponse = LifeVolumeResponseModel

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
