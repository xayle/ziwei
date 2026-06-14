import { ref, computed } from 'vue'
import { getEventStats, listEvents } from '@/api/events'
import { getGoldenCases } from '@/api/bazi'
import type { EventResponse, EventStatsResponse } from '@/api/events'
import type { GoldenCasesResponse } from '@/api/bazi'

/** 事件统计 + 黄金案例面板 */
export function useAdminEvents() {
  // ── 事件统计 ──────────────────────────────────────────────
  const eventStats = ref<EventStatsResponse | null>(null)
  const eventRows = ref<EventResponse[]>([])
  const eventsLoading = ref(false)
  const eventsLoaded = ref(false)
  const eventsError = ref('')
  const eventFilter = ref('')

  const maxEventCount = computed(() => {
    const entries = eventStats.value?.by_type ?? []
    return Math.max(1, ...entries.map(item => item.count))
  })

  async function loadEventsPanel() {
    if (eventsLoading.value) return
    eventsLoading.value = true
    eventsError.value = ''
    try {
      const [stats, list] = await Promise.all([
        getEventStats(),
        listEvents({ limit: 20, event_type: eventFilter.value || undefined }),
      ])
      eventStats.value = stats
      eventRows.value = list.items
      eventsLoaded.value = true
    } catch {
      eventsError.value = '事件统计加载失败'
    } finally {
      eventsLoading.value = false
    }
  }

  function applyEventFilter() {
    eventsLoaded.value = false
    loadEventsPanel()
  }

  // ── 黄金案例 ──────────────────────────────────────────────
  const goldenCases = ref<Array<Record<string, unknown>>>([])
  const goldenTotal = ref(0)
  const goldenLoading = ref(false)
  const goldenLoaded = ref(false)
  const goldenError = ref('')

  async function loadGoldenCasesPanel() {
    if (goldenLoading.value) return
    goldenLoading.value = true
    goldenError.value = ''
    try {
      const res: GoldenCasesResponse = await getGoldenCases({ limit: 20 })
      goldenCases.value = res.cases ?? []
      goldenTotal.value = res.total ?? goldenCases.value.length
      goldenLoaded.value = true
    } catch {
      goldenError.value = '黄金案例加载失败'
    } finally {
      goldenLoading.value = false
    }
  }

  return {
    eventStats, eventRows, eventsLoading, eventsLoaded, eventsError, eventFilter, maxEventCount,
    loadEventsPanel, applyEventFilter,
    goldenCases, goldenTotal, goldenLoading, goldenLoaded, goldenError, loadGoldenCasesPanel,
  }
}
