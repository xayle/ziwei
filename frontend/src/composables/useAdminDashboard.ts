import { ref, computed } from 'vue'
import { getDashboard } from '@/api/admin'
import type { DashboardResponse } from '@/api/admin'

/** 仪表盘数据管理 */
export function useAdminDashboard() {
  const dashboard = ref<DashboardResponse | null>(null)
  const dashLoading = ref(false)
  const dashError = ref('')

  async function loadDashboard() {
    if (dashboard.value) return   // 已加载则跳过
    dashLoading.value = true
    dashError.value = ''
    try {
      dashboard.value = await getDashboard()
    } catch {
      dashError.value = '加载失败，请稍后重试'
    } finally {
      dashLoading.value = false
    }
  }

  /** 7日活跃度最大值（用于柱高百分比） */
  const maxActivity = computed(() =>
    Math.max(1, ...(dashboard.value?.daily_activity.map(d => d.count) ?? [0]))
  )

  return { dashboard, dashLoading, dashError, loadDashboard, maxActivity }
}
