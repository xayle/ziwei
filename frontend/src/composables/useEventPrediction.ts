/**
 * useEventPrediction.ts — 年份事件预测 composable
 *
 * 提供：
 *  - selectedYear      当前选择年份（默认当前年）
 *  - selectedEventType 当前事件类型（默认 marriage）
 *  - eventData         单年五大事件结果
 *  - trendData         多年趋势摘要
 *  - consultText       AI 咨询解读文本
 *  - consultLoading    AI 咨询 loading 状态
 *  - fetchYearEvents() 拉取单年数据
 *  - fetchTrend()      拉取多年趋势
 *  - consult()         发起 AI 咨询
 */
import { ref, computed, type Ref } from 'vue'
import {
  yearEvents,
  multiYearTrend,
  yearEventConsult,
  type YearEventResponse,
  type MultiYearTrendResponse,
  type YearEventConsultResponse,
  type EventType,
  EVENT_DISPLAY,
} from '@/api/eventPrediction'

// 固定追问问题映射（与 backend followup_service.py 保持同步）
const FOLLOWUP_MAP: Record<EventType, string[]> = {
  marriage: [
    '会不会有离婚的风险？',
    '哪几个月感情最不稳定？',
    '有什么具体的化解方式？',
    '感情上的主要矛盾在哪里？',
    '哪一年的婚姻运势最顺？',
  ],
  wealth: [
    '哪一年财运最旺？',
    '今年适合创业或投资吗？',
    '哪类投资需要避开？',
    '如何防范破财的风险？',
    '什么时候收入提升最明显？',
  ],
  property: [
    '上半年还是下半年置业更合适？',
    '贷款或资金压力大吗？',
    '会不会因家人意见拖延决策？',
    '哪一年买房时机最好？',
    '会不会多次看房但成交困难？',
  ],
  career: [
    '什么时候跳槽或升职最有利？',
    '今年适合自主创业吗？',
    '贵人运在哪个方向？',
    '有被裁员或调岗的风险吗？',
    '哪个行业方向对我最有利？',
  ],
  health: [
    '哪个季节需要重点保养？',
    '哪个脏腑系统最需要关注？',
    '什么时候精神压力最大？',
    '有什么具体的调养建议？',
    '有意外伤病的风险吗？',
  ],
}

export function useEventPrediction(caseIdRef: Ref<string | null>) {
  const currentYear = new Date().getFullYear()

  // ── 状态 ──────────────────────────────────────────────────────────────────
  const selectedYear      = ref<number>(currentYear)
  const selectedEventType = ref<EventType>('marriage')

  const eventData           = ref<YearEventResponse | null>(null)
  const trendData           = ref<MultiYearTrendResponse | null>(null)
  const consultResult       = ref<YearEventConsultResponse | null>(null)

  const eventLoading    = ref(false)
  const trendLoading    = ref(false)
  const consultLoading  = ref(false)

  const eventError   = ref<string | null>(null)
  const trendError   = ref<string | null>(null)
  const consultError = ref<string | null>(null)

  // ── 计算属性 ───────────────────────────────────────────────────────────────

  /** 当前选中年份 + 事件类型的 EventResult */
  const currentEventResult = computed(() =>
    eventData.value?.events?.[selectedEventType.value] ?? null
  )

  /** 当前事件类型对应的追问问题（始终有值，不依赖 LLM） */
  const followupQuestions = computed<string[]>(() =>
    FOLLOWUP_MAP[selectedEventType.value] ?? []
  )

  /** 当前事件类型中文名 */
  const eventDisplayName = computed(() =>
    EVENT_DISPLAY[selectedEventType.value]
  )

  /** AI 咨询解读文本 */
  const consultText = computed(() => consultResult.value?.interpretation ?? '')

  /** 多年趋势摘要列表 */
  const trendSummaries = computed(() => trendData.value?.summaries ?? [])

  /** 时间轴整体叙述 */
  const timelineSummary = computed(() => trendData.value?.timeline_summary ?? '')

  // ── 操作函数 ───────────────────────────────────────────────────────────────

  /** 拉取指定年份的五大事件（默认使用 selectedYear） */
  async function fetchYearEvents(year?: number) {
    const caseId = caseIdRef.value
    if (!caseId) return
    const targetYear = year ?? selectedYear.value
    eventLoading.value = true
    eventError.value   = null
    try {
      eventData.value = await yearEvents({
        case_id: caseId,
        year:    targetYear,
        event_types: ['marriage', 'wealth', 'property', 'career', 'health'],
      })
    } catch (e: unknown) {
      eventError.value = e instanceof Error ? e.message : '年份事件加载失败'
    } finally {
      eventLoading.value = false
    }
  }

  /** 拉取多年趋势；默认：[当前年-1 … 当前年+3] */
  async function fetchTrend(years?: number[]) {
    const caseId = caseIdRef.value
    if (!caseId) return
    const targetYears = years ?? [
      currentYear - 1,
      currentYear,
      currentYear + 1,
      currentYear + 2,
      currentYear + 3,
    ]
    trendLoading.value = true
    trendError.value   = null
    try {
      trendData.value = await multiYearTrend({
        case_id: caseId,
        years:   targetYears,
      })
    } catch (e: unknown) {
      trendError.value = e instanceof Error ? e.message : '多年趋势加载失败'
    } finally {
      trendLoading.value = false
    }
  }

  /** 发起 AI 咨询（针对 selectedYear + selectedEventType） */
  async function consult(userQuestion: string) {
    const caseId = caseIdRef.value
    if (!caseId) return
    consultLoading.value = true
    consultError.value   = null
    try {
      consultResult.value = await yearEventConsult({
        case_id:       caseId,
        year:          selectedYear.value,
        event_type:    selectedEventType.value,
        user_question: userQuestion,
      })
    } catch (e: unknown) {
      consultError.value = e instanceof Error ? e.message : 'AI 咨询失败'
    } finally {
      consultLoading.value = false
    }
  }

  /** 切换到某一年并自动重新拉取该年数据 */
  async function selectYear(year: number) {
    selectedYear.value = year
    consultResult.value = null
    await fetchYearEvents(year)
  }

  /** 切换事件类型 */
  function selectEventType(et: EventType) {
    selectedEventType.value = et
    consultResult.value = null
  }

  return {
    // 状态
    selectedYear,
    selectedEventType,
    eventData,
    trendData,
    consultText,
    consultLoading,
    eventLoading,
    trendLoading,
    eventError,
    trendError,
    consultError,

    // 计算属性
    currentEventResult,
    followupQuestions,
    eventDisplayName,
    trendSummaries,
    timelineSummary,

    // 操作
    fetchYearEvents,
    fetchTrend,
    consult,
    selectYear,
    selectEventType,
  }
}
