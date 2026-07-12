import { describe, expect, it } from 'vitest'
import { reportVolumeHref, resolveVolumeRouteMeta } from '@/composables/useVolumeRouteMeta'

describe('useVolumeRouteMeta', () => {
  it('maps bazi route to vol1', () => {
    const meta = resolveVolumeRouteMeta('/new/bazi')
    expect(meta.volumeId).toBe('vol1')
    expect(meta.volumeLabel).toBe('卷一·命之根')
  })

  it('maps ziwei timeline to vol3', () => {
    const meta = resolveVolumeRouteMeta('/new/ziwei/timeline')
    expect(meta.volumeId).toBe('vol3')
    expect(meta.volumeLabel).toBe('卷三·运之波')
  })

  it('maps report to preface volume context', () => {
    const meta = resolveVolumeRouteMeta('/report')
    expect(meta.volumeId).toBe('preface')
    expect(meta.volumeLabel).toBe('卷首')
  })

  it('builds report hash href', () => {
    expect(reportVolumeHref('vol5')).toBe('/report#report-volume-vol5')
  })
})
