import { ref } from 'vue'
import { batchCompare, type BatchCompareResponse } from '@/api/bazi'

/** 五行色彩映射（用于批量对比面板） */
export const WX_COLORS_MAP: Record<string, string> = {
  '木': 'var(--wx-wood,#22c55e)',
  '火': 'var(--wx-fire,#ef4444)',
  '土': 'var(--wx-earth,#f59e0b)',
  '金': 'var(--wx-metal,#94a3b8)',
  '水': 'var(--wx-water,#3b82f6)',
}

/** 多案例批量对比逻辑 (T2.4) */
export function useBaziBatchCompare() {
  const batchCaseIds   = ref('')
  const batchLoading   = ref(false)
  const batchError     = ref('')
  const batchResult    = ref<BatchCompareResponse | null>(null)
  const batchPanelOpen = ref(false)

  async function doBatchCompare() {
    const ids = batchCaseIds.value
      .split(/[,，\s]+/)
      .map(s => s.trim())
      .filter(Boolean)
    if (ids.length < 2) {
      batchError.value = '请至少输入 2 个案例 ID（逗号或空格分隔）'
      return
    }
    batchLoading.value = true
    batchError.value   = ''
    batchResult.value  = null
    try {
      batchResult.value = await batchCompare({ case_ids: ids })
    } catch (e: unknown) {
      batchError.value = (e as Error).message ?? '批量对比失败'
    } finally {
      batchLoading.value = false
    }
  }

  return {
    batchCaseIds,
    batchLoading,
    batchError,
    batchResult,
    batchPanelOpen,
    WX_COLORS_MAP,
    doBatchCompare,
  }
}
