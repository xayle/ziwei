import { ref } from 'vue'
import {
  getAuditLogs, listReviews, getReviewStats, updateReview, deleteReview,
} from '@/api/admin'
import type { AuditLogItem, ChartReviewResponse, ReviewStats } from '@/api/admin'

/** 审计日志 + 审查管理面板 */
export function useAdminAudit() {
  // ── 审计日志 ──────────────────────────────────────────────
  const auditLogs = ref<AuditLogItem[]>([])
  const auditTotal = ref(0)
  const auditNext = ref<number | null>(null)
  const auditLoading = ref(false)
  const auditError = ref('')
  const auditLoaded = ref(false)
  const auditFilter = ref('')

  async function loadAudit(reset = false) {
    if (auditLoading.value) return
    auditLoading.value = true
    auditError.value = ''
    try {
      const params: Record<string, unknown> = { limit: 50 }
      if (!reset && auditNext.value) params.before_id = auditNext.value
      if (auditFilter.value) params.action = auditFilter.value
      const res = await getAuditLogs(params)
      if (reset) {
        auditLogs.value = res.items
      } else {
        auditLogs.value.push(...res.items)
      }
      auditTotal.value = res.total
      auditNext.value = res.next_cursor
      auditLoaded.value = true
    } catch {
      auditError.value = '审计日志加载失败'
    } finally {
      auditLoading.value = false
    }
  }

  function applyAuditFilter() {
    auditNext.value = null
    auditLogs.value = []
    auditLoaded.value = false
    loadAudit(true)
  }

  // ── 审查管理 ──────────────────────────────────────────────
  const reviews = ref<ChartReviewResponse[]>([])
  const reviewsTotal = ref(0)
  const reviewsLoading = ref(false)
  const reviewsLoaded = ref(false)
  const reviewStats = ref<ReviewStats | null>(null)

  async function loadReviews() {
    if (reviewsLoading.value) return
    reviewsLoading.value = true
    try {
      const [list, stats] = await Promise.all([listReviews({ page_size: 30 }), getReviewStats()])
      reviews.value = list.items
      reviewsTotal.value = list.total
      reviewStats.value = stats
      reviewsLoaded.value = true
    } catch { /* ignore */ }
    finally { reviewsLoading.value = false }
  }

  async function handleApproveReview(id: number) {
    try {
      await updateReview(id, { status: 'approved', reviewer: 'admin' })
      await loadReviews()
    } catch { alert('操作失败') }
  }

  async function handleRejectReview(id: number) {
    const reason = prompt('驳回原因：')
    if (!reason) return
    try {
      await updateReview(id, { status: 'rejected', reviewer: 'admin', reject_reason: reason })
      await loadReviews()
    } catch { alert('操作失败') }
  }

  async function handleDeleteReview(id: number) {
    if (!confirm('确认删除？')) return
    try { await deleteReview(id); await loadReviews() } catch { alert('删除失败') }
  }

  return {
    auditLogs, auditTotal, auditNext, auditLoading, auditError, auditLoaded, auditFilter,
    loadAudit, applyAuditFilter,
    reviews, reviewsTotal, reviewsLoading, reviewsLoaded, reviewStats,
    loadReviews, handleApproveReview, handleRejectReview, handleDeleteReview,
  }
}
