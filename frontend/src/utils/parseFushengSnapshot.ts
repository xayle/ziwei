import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import type { SnapshotOut } from '@/api/snapshots'

export type FushengSnapshotOutput = {
  bazi?: BaziResponse
  ziwei?: ZiweiResponse
}

export function parseFushengSnapshotOutput(snap: SnapshotOut): FushengSnapshotOutput | null {
  const raw = snap.output_json
  if (!raw || typeof raw !== 'object') return null
  const output = raw as FushengSnapshotOutput
  if (!output.bazi && !output.ziwei) return null
  return output
}
