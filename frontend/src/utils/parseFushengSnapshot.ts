import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import type { SnapshotOut } from '@/api/snapshots'

export type FushengSnapshotOutput = {
  bazi?: BaziResponse
  ziwei?: ZiweiResponse
  /** CASE-01：快照写入时的档案签名，用于恢复缓存键 */
  profileSignature?: string
}

export function parseFushengSnapshotOutput(snap: SnapshotOut): FushengSnapshotOutput | null {
  const raw = snap.output_json
  if (!raw || typeof raw !== 'object') return null
  const output = raw as FushengSnapshotOutput
  if (!output.bazi && !output.ziwei) return null
  const input = snap.input_json
  const sig = input && typeof input === 'object'
    ? (input as { profile_signature?: unknown }).profile_signature
    : undefined
  return {
    bazi: output.bazi,
    ziwei: output.ziwei,
    profileSignature: typeof sig === 'string' && sig.trim() ? sig : undefined,
  }
}
