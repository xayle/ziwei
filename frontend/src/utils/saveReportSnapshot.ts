import type { BaziResponse } from '@/api/bazi'
import type { ZiweiResponse } from '@/api/ziwei'
import { createSnapshot } from '@/api/snapshots'

export async function saveReportSnapshot(params: {
  caseId: string
  bazi: BaziResponse
  ziwei: ZiweiResponse
  profileSignature: string
  generatedAt?: string
}): Promise<{ ok: boolean; snapshotId?: string; error?: string; skipped?: boolean }> {
  try {
    const snap = await createSnapshot(params.caseId, {
      kind: 'fusheng_report',
      input_json: {
        profile_signature: params.profileSignature,
        generated_at: params.generatedAt ?? null,
      },
      output_json: {
        bazi: params.bazi,
        ziwei: params.ziwei,
      },
      api_version: params.bazi.api_version ?? null,
      rule_version: params.bazi.rule_version ?? null,
      schema_version: params.bazi.schema_version ?? 'snapshot@5.0',
      note: 'Fusheng report auto snapshot',
    })
    return { ok: true, snapshotId: snap.id }
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    return {
      ok: false,
      error: typeof detail === 'string' ? detail : '快照保存失败。',
    }
  }
}
