import { describe, expect, it } from 'vitest'
import {
  getContentLayerLabel,
  isLifeVolumeResponse,
  mapProvenanceLayerToContent,
  mapProvenanceLayerToTrustLabel,
  resolveLifeVolumeDoc,
  shouldTryLifeVolumesRemote,
  shouldBuildLifeVolumesAdapter,
} from '@/utils/feBeAdapter'
import type { LifeVolumeResponse } from '@/types/life-volume'
import { buildLifeVolumes } from '@/utils/buildLifeVolumes'

function minimalLifeDoc(overrides: Partial<LifeVolumeResponse> = {}): LifeVolumeResponse {
  const base = buildLifeVolumes({
    caseId: 'case-test',
    chartHash: 'hash-test',
    bazi: null,
    ziwei: null,
  })
  return { ...base, ...overrides }
}

describe('feBeAdapter', () => {
  it('maps provenance layers to UI content layers (Q5)', () => {
    expect(mapProvenanceLayerToContent('engine')).toBe('fact')
    expect(mapProvenanceLayerToContent('classical')).toBe('cite')
    expect(mapProvenanceLayerToContent('heuristic')).toBe('inference')
  })

  it('maps provenance layers to trust panel labels', () => {
    expect(mapProvenanceLayerToTrustLabel('classical')).toBe('典籍')
    expect(mapProvenanceLayerToTrustLabel('unknown')).toBe('unknown')
  })

  it('getContentLayerLabel handles cite without classic_id', () => {
    expect(getContentLayerLabel('cite', 'CL001')).toBe('典籍依据')
    expect(getContentLayerLabel('cite')).toBe('待校勘')
  })

  it('validates life-volume@1.0 shape', () => {
    expect(isLifeVolumeResponse(minimalLifeDoc())).toBe(true)
    expect(isLifeVolumeResponse({ schema_version: 'other' })).toBe(false)
  })

  it('resolveLifeVolumeDoc prefers remote when valid', () => {
    const local = minimalLifeDoc({ case_id: 'local' })
    const remote = minimalLifeDoc({ case_id: 'remote' })
    expect(resolveLifeVolumeDoc({ local, remote: null }).source).toBe('local')
    expect(resolveLifeVolumeDoc({ local, remote }).doc.case_id).toBe('remote')
  })

  it('shouldTryLifeVolumesRemote respects env and auth', () => {
    // TEST-01 @debt：envFlag=true 时未登录也可试拉 volumes（联调/GTM 开关）；
    // 产品若改为「仅登录」，请改断言并同步 shouldTryLifeVolumesRemote。
    expect(shouldTryLifeVolumesRemote({ envFlag: true, isLoggedIn: false })).toBe(true)
    expect(shouldTryLifeVolumesRemote({ envFlag: false, isLoggedIn: true, remoteCaseId: 'x' })).toBe(true)
    expect(shouldTryLifeVolumesRemote({ envFlag: false, isLoggedIn: false })).toBe(false)
  })

  it('T081 shouldBuildLifeVolumesAdapter skips when remote is valid', () => {
    expect(shouldBuildLifeVolumesAdapter(null)).toBe(true)
    expect(shouldBuildLifeVolumesAdapter(minimalLifeDoc())).toBe(false)
    expect(shouldBuildLifeVolumesAdapter({ schema_version: 'other' } as LifeVolumeResponse)).toBe(true)
  })
})
