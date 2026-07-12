import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LIFE_VOLUME_LABELS, type LifeVolumeId } from '@/types/life-volume'

export interface VolumeRouteMeta {
  volumeId: LifeVolumeId | null
  volumeLabel: string | null
  pageTitle: string
}

const ROUTE_VOLUME: Record<string, LifeVolumeId> = {
  '/new/bazi': 'vol1',
  '/new/ziwei/timeline': 'vol3',
  '/new/ziwei': 'vol4',
  '/report': 'preface',
}

export function resolveVolumeRouteMeta(path: string): VolumeRouteMeta {
  const normalized = path.replace(/\/+$/, '') || '/'
  let volumeId: LifeVolumeId | null = null
  if (ROUTE_VOLUME[normalized]) {
    volumeId = ROUTE_VOLUME[normalized]
  } else if (normalized.startsWith('/new/ziwei/timeline')) {
    volumeId = 'vol3'
  } else if (normalized.startsWith('/new/ziwei')) {
    volumeId = 'vol4'
  } else if (normalized.startsWith('/report')) {
    volumeId = 'preface'
  } else if (normalized.startsWith('/new/bazi')) {
    volumeId = 'vol1'
  }

  const volumeLabel = volumeId ? LIFE_VOLUME_LABELS[volumeId] : null
  const pageTitle = volumeLabel ?? (
    normalized === '/' || normalized === '/home' || normalized === '/new'
      ? '首页'
      : normalized.startsWith('/profile')
        ? '档案'
        : '浮生'
  )

  return { volumeId, volumeLabel, pageTitle }
}

export function useVolumeRouteMeta() {
  const route = useRoute()
  return computed(() => resolveVolumeRouteMeta(route.path))
}

export function reportVolumeHref(volumeId: LifeVolumeId): string {
  return `/report#report-volume-${volumeId}`
}
