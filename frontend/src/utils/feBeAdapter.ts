/**
 * 前后端适配层 — 类型校验、层映射、加载策略
 * @see docs/plan/FE-BE-DECISIONS.md
 */

import {
  LIFE_VOLUME_SCHEMA_VERSION,
  PROVENANCE_LAYER_TO_CONTENT,
  PROVENANCE_LAYER_TRUST_LABELS,
  type LifeVolumeLoadPhase,
} from '@/constants/feBeContract'
import type { ContentLayer, LifeVolumeResponse } from '@/types/life-volume'
import { CONTENT_LAYER_LABELS } from '@/types/life-volume'

export function isLifeVolumeResponse(data: unknown): data is LifeVolumeResponse {
  if (!data || typeof data !== 'object') return false
  const doc = data as LifeVolumeResponse
  return doc.schema_version === LIFE_VOLUME_SCHEMA_VERSION
    && typeof doc.case_id === 'string'
    && typeof doc.chart_hash === 'string'
    && Array.isArray(doc.volumes)
    && doc.volumes.length >= 8
    && doc.disclaimer_block != null
    && doc.colophon != null
}

/** API provenance.layer → UI ContentLayer（Q5） */
export function mapProvenanceLayerToContent(layer?: string | null): ContentLayer {
  if (!layer) return 'fact'
  const mapped = PROVENANCE_LAYER_TO_CONTENT[layer as keyof typeof PROVENANCE_LAYER_TO_CONTENT]
  return mapped ?? 'fact'
}

/** 信任面板：provenance 层短标签 */
export function mapProvenanceLayerToTrustLabel(layer?: string | null): string {
  if (!layer) return '—'
  return PROVENANCE_LAYER_TRUST_LABELS[layer] ?? '未分层'
}

/** 六卷块：ContentLayer → 用户可见文案 */
export function getContentLayerLabel(layer: ContentLayer, classicId?: string | null): string {
  if (layer === 'cite' && !classicId) return '待校勘'
  return CONTENT_LAYER_LABELS[layer]
}

export type LifeVolumeSource = 'local' | 'remote'

export interface ResolveLifeVolumeInput {
  remote: LifeVolumeResponse | null
  local: LifeVolumeResponse
}

/** remote 优先；失败回退 local Adapter（Q1 / Q9） */
export function resolveLifeVolumeDoc(input: ResolveLifeVolumeInput): {
  doc: LifeVolumeResponse
  source: LifeVolumeSource
} {
  if (input.remote && isLifeVolumeResponse(input.remote)) {
    return { doc: input.remote, source: 'remote' }
  }
  return { doc: input.local, source: 'local' }
}

/**
 * T081：remote 已是合法 life-volume 时，生产路径不再跑 `buildLifeVolumes`。
 * （resolve 会选 remote；local 入参可复用同一份 doc，避免空壳类型。）
 */
export function shouldBuildLifeVolumesAdapter(remote: LifeVolumeResponse | null): boolean {
  return !(remote != null && isLifeVolumeResponse(remote))
}

export function shouldTryLifeVolumesRemote(options: {
  envFlag: boolean
  isLoggedIn: boolean
  remoteCaseId?: string | null
}): boolean {
  return options.envFlag || (options.isLoggedIn && Boolean(options.remoteCaseId?.trim()))
}

export function lifeVolumeLoadPhaseLabel(phase: LifeVolumeLoadPhase): string {
  return phase === 'w16_authority'
    ? 'GET /api/v1/life/volumes/{case_id}'
    : 'buildLifeVolumes + explain/batch'
}
