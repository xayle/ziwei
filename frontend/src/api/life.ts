import apiClient from './client'
import type { LifeVolumeResponse } from '@/types/life-volume'
import { isLifeVolumeResponse } from '@/utils/feBeAdapter'
import { LIFE_VOLUMES_API_STORAGE_KEY } from '@/constants/feBeContract'
import type { LifeSnippetsResponseModel } from '@/api/openapiTypes'

/**
 * T079：volumes 权威开关。
 * - env `VITE_USE_LIFE_VOLUMES_API=true` → 强制开
 * - localStorage `fusheng-use-life-volumes-api=1` → E2E/联调开
 */
export function useLifeVolumesApiEnabled(): boolean {
  if (import.meta.env.VITE_USE_LIFE_VOLUMES_API === 'true') return true
  try {
    return localStorage.getItem(LIFE_VOLUMES_API_STORAGE_KEY) === '1'
  } catch {
    return false
  }
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
