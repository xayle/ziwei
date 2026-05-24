import { ref, type Ref } from 'vue'
import type { CaseOut } from '@/api/report'
import { createShareToken } from '@/api/report'
import { exportCaseJson, exportCasePdf, downloadBlob } from '@/api/export'
import { listSnapshots } from '@/api/snapshots'
import type { SnapshotOut } from '@/api/snapshots'

type UseWorkbenchOutputsOptions = {
  caseDetail: Ref<CaseOut | null>
}

export function useWorkbenchOutputs(options: UseWorkbenchOutputsOptions) {
  const shareUrl = ref<string | null>(null)
  const snapshots = ref<SnapshotOut[]>([])
  const snapshotsLoading = ref(false)

  function triggerPrint() {
    window.print()
  }

  async function handleShare() {
    if (!options.caseDetail.value) return
    try {
      const result = await createShareToken(options.caseDetail.value.id)
      shareUrl.value = result.share_url
      setTimeout(() => {
        shareUrl.value = null
      }, 8000)
    } catch (_error) {
      alert('生成分享链接失败')
    }
  }

  async function handleExportJson() {
    if (!options.caseDetail.value) return
    try {
      const blob = await exportCaseJson(options.caseDetail.value.id)
      downloadBlob(blob, `${options.caseDetail.value.name}.json`)
    } catch (_error) {
      alert('导出失败')
    }
  }

  async function handleExportPdf() {
    if (!options.caseDetail.value) return
    try {
      const blob = await exportCasePdf(options.caseDetail.value.id)
      downloadBlob(blob, `${options.caseDetail.value.name}.pdf`)
    } catch (_error) {
      alert('PDF导出失败')
    }
  }

  async function loadSnapshots() {
    if (!options.caseDetail.value) return
    snapshotsLoading.value = true
    const result = await listSnapshots(options.caseDetail.value.id, { limit: 10 }).catch(() => null as SnapshotOut[] | null)
    if (result) snapshots.value = result
    snapshotsLoading.value = false
  }

  return {
    shareUrl,
    snapshots,
    snapshotsLoading,
    triggerPrint,
    handleShare,
    handleExportJson,
    handleExportPdf,
    loadSnapshots,
  }
}
