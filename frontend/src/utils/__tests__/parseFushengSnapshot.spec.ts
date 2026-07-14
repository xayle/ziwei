import { describe, expect, it } from 'vitest'
import { parseFushengSnapshotOutput } from '@/utils/parseFushengSnapshot'
import type { SnapshotOut } from '@/api/snapshots'

describe('parseFushengSnapshotOutput CASE-01', () => {
  it('reads profile_signature from input_json', () => {
    const snap = {
      id: 's1',
      case_id: 'c1',
      kind: 'fusheng_report',
      input_json: { profile_signature: '{"birthDt":"1990-01-01"}' },
      output_json: {
        bazi: { pillars_primary: {} },
        ziwei: { palaces: [] },
      },
    } as unknown as SnapshotOut
    const out = parseFushengSnapshotOutput(snap)
    expect(out?.profileSignature).toBe('{"birthDt":"1990-01-01"}')
  })

  it('returns null without charts', () => {
    const snap = {
      id: 's1',
      case_id: 'c1',
      kind: 'fusheng_report',
      output_json: {},
    } as unknown as SnapshotOut
    expect(parseFushengSnapshotOutput(snap)).toBeNull()
  })
})
