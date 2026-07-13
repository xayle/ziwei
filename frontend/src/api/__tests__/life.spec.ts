import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { LifeVolumeResponse } from '@/types/life-volume'

const getMock = vi.fn()

vi.mock('@/api/client', () => ({
  default: { get: (...args: unknown[]) => getMock(...args) },
}))

const volumeIds = [
  'preface', 'vol1', 'vol2', 'vol3', 'vol4', 'vol5', 'vol6', 'colophon',
] as const

const sampleDoc: LifeVolumeResponse = {
  schema_version: 'life-volume@1.0',
  case_id: 'case-1',
  chart_hash: 'abc',
  disclaimer_block: { text: '免责声明', version: '1.0' },
  volumes: volumeIds.map((id) => ({ id, title: id, sections: [] })),
  colophon: { summary_lines: ['跋'] },
}

describe('fetchLifeVolumes', () => {
  beforeEach(() => {
    getMock.mockReset()
    localStorage.clear()
  })

  it('returns null for empty case id', async () => {
    const { fetchLifeVolumes } = await import('@/api/life')
    await expect(fetchLifeVolumes('  ')).resolves.toBeNull()
    expect(getMock).not.toHaveBeenCalled()
  })

  it('returns payload when schema matches', async () => {
    getMock.mockResolvedValue({ data: sampleDoc })
    const { fetchLifeVolumes } = await import('@/api/life')
    const doc = await fetchLifeVolumes('case-1')
    expect(doc).toEqual(sampleDoc)
    expect(getMock).toHaveBeenCalledWith('/api/v1/life/volumes/case-1')
  })

  it('returns null on invalid shape or network error', async () => {
    const { fetchLifeVolumes } = await import('@/api/life')
    getMock.mockResolvedValue({ data: { schema_version: 'other' } })
    await expect(fetchLifeVolumes('case-1')).resolves.toBeNull()
    getMock.mockRejectedValue(new Error('404'))
    await expect(fetchLifeVolumes('case-1')).resolves.toBeNull()
  })
})

describe('useLifeVolumesApiEnabled', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('reads localStorage override for E2E / 联调', async () => {
    localStorage.setItem('fusheng-use-life-volumes-api', '1')
    const { useLifeVolumesApiEnabled } = await import('@/api/life')
    expect(useLifeVolumesApiEnabled()).toBe(true)
  })

  it('defaults false when storage empty', async () => {
    const { useLifeVolumesApiEnabled } = await import('@/api/life')
    expect(useLifeVolumesApiEnabled()).toBe(false)
  })
})
