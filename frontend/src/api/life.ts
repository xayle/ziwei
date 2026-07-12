import apiClient from './client'
import type { LifeVolumeResponse } from '@/types/life-volume'
import { isLifeVolumeResponse } from '@/utils/feBeAdapter'

/** Dev override: force BE authority path even without remote case id. */
export function useLifeVolumesApiEnabled(): boolean {
  return import.meta.env.VITE_USE_LIFE_VOLUMES_API === 'true'
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
