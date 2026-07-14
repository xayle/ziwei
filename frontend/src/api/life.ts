import axios from 'axios'
import apiClient from './client'
import type { LifeVolumeResponse } from '@/types/life-volume'
import { isLifeVolumeResponse } from '@/utils/feBeAdapter'
import { LIFE_VOLUMES_API_STORAGE_KEY } from '@/constants/feBeContract'
import type { LifeSnippetsResponseModel } from '@/api/openapiTypes'

function resolveApiBaseUrl(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL || '').trim()
  if (!configured) return '/'
  return configured.endsWith('/') ? configured : `${configured}/`
}

/**
 * T079 / REP-04：volumes 权威开关。
 * - env `VITE_USE_LIFE_VOLUMES_API=true` → 强制开
 * - env `VITE_USE_LIFE_VOLUMES_API=false` → 强制关
 * - localStorage `fusheng-use-life-volumes-api=1|0` → 联调覆盖
 * - 默认：**开启**（GTM；登录+云端 case 时优先远端六卷）
 */
export function useLifeVolumesApiEnabled(): boolean {
  const env = import.meta.env.VITE_USE_LIFE_VOLUMES_API
  if (env === 'false') return false
  if (env === 'true') return true
  try {
    const ls = localStorage.getItem(LIFE_VOLUMES_API_STORAGE_KEY)
    if (ls === '0') return false
    if (ls === '1') return true
  } catch {
    /* ignore */
  }
  return true
}

/** W16+ 权威路径；失败返回 null，由 Report 回退 deprecated `buildLifeVolumes`。 */
export async function fetchLifeVolumes(caseId: string): Promise<LifeVolumeResponse | null> {
  const id = caseId.trim()
  if (!id) return null
  try {
    const { data } = await apiClient.get<LifeVolumeResponse>(
      `/api/v1/life/volumes/${encodeURIComponent(id)}`,
    )
    return isLifeVolumeResponse(data) ? data : null
  } catch {
    return null
  }
}

function isLifeSnippetsResponse(data: unknown): data is LifeSnippetsResponseModel {
  if (!data || typeof data !== 'object') return false
  const d = data as Record<string, unknown>
  return (
    d.schema_version === 'life-snippets@0.1' &&
    typeof d.case_id === 'string' &&
    Array.isArray(d.hooks) &&
    d.hooks.length >= 1
  )
}

/** T076/T096：抖音钩子句；失败返回 null（Report 可隐藏面板）。 */
export async function fetchLifeSnippets(
  caseId: string,
  limit = 5,
): Promise<LifeSnippetsResponseModel | null> {
  const id = caseId.trim()
  if (!id) return null
  try {
    const { data } = await apiClient.get<LifeSnippetsResponseModel>(
      `/api/v1/life/snippets/${encodeURIComponent(id)}`,
      { params: { limit } },
    )
    return isLifeSnippetsResponse(data) ? data : null
  } catch {
    return null
  }
}

/**
 * SHARE-02 / T095：免登录卷一试读。
 * 使用裸 axios + `?token=`，避免带登录 JWT 或 401 清会话。
 */
export async function fetchLifeVol1Preview(
  caseId: string,
  previewToken: string,
): Promise<LifeVolumeResponse | null> {
  const id = caseId.trim()
  const token = previewToken.trim()
  if (!id || !token) return null
  try {
    const { data } = await axios.get<LifeVolumeResponse>(
      `${resolveApiBaseUrl()}api/v1/life/preview/${encodeURIComponent(id)}`,
      { params: { token }, timeout: 30000 },
    )
    return isLifeVolumeResponse(data) ? data : null
  } catch {
    return null
  }
}
