import apiClient from './client'
import type { LifeVolumeResponse } from '@/types/life-volume'
import { isLifeVolumeResponse } from '@/utils/feBeAdapter'
import { LIFE_VOLUMES_API_STORAGE_KEY } from '@/constants/feBeContract'

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

/** W16+ authority path; returns null on miss so buildLifeVolumes Adapter keeps working. */
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
