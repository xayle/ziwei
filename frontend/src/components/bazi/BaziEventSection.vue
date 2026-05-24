<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventPrediction } from '@/composables/useEventPrediction'
import {
  RISK_LABEL,
  EVENT_DISPLAY,
  SIGNAL_LAYER_LABEL,
  type EventType,
} from '@/api/eventPrediction'

const props = defineProps<{
  caseId: string | null
}>()

const emit = defineEmits<{
  (e: 'open-save-dialog'): void
}>()

const ALL_EVENT_TYPES: EventType[] = ['marriage', 'wealth', 'property', 'career', 'health']

// 将 caseId prop 转为 Ref<string|null> 供 useEventPrediction 使用
const caseIdRef = computed(() => props.caseId)

const {
  selectedYear:       evtYear,
  selectedEventType:  evtType,
  eventData:          evtData,
  trendData:          evtTrend,
  consultText:        evtConsultText,
  consultLoading:     evtConsultLoading,
  eventLoading:       evtLoading,
  trendLoading:       evtTrendLoading,
  currentEventResult: evtResult,
  followupQuestions:  evtFollowups,
  trendSummaries:     evtSummaries,
  timelineSummary:    evtTimelineSummary,
  consultError:       evtConsultError,
  fetchYearEvents,
  fetchTrend,
  consult:            evtConsult,
  selectYear,
  selectEventType,
} = useEventPrediction(caseIdRef)

const evtUserQuestion = ref('')

// 当 caseId 设置后自动加载趋势与年份事件
watch(caseIdRef, (id) => {
  if (id) {
    fetchTrend()
    fetchYearEvents()
  }
})

async function handleEvtConsult(question: string) {
  evtUserQuestion.value = question
  await evtConsult(question)
}
</script>

<template>
  <section class="card section-inline">
    <h2 class="card-title">年份事件</h2>

    <!-- 未保存提示 -->
    <div v-if="!caseId" class="yev-save-hint">
      <p class="muted">保存案例后可查看年份事件预测（婚姻 / 财运 / 置业 / 事业 / 健康）。</p>
      <button class="btn-primary" style="margin-top:8px" @click="emit('open-save-dialog')">保存案例 →</button>
    </div>

    <!-- 时间轴摘要 -->
    <div v-if="evtTrend" class="yev-trend-block">
      <p v-if="evtTimelineSummary" class="yev-timeline-summary">{{ evtTimelineSummary }}</p>
      <div class="yev-year-track">
        <div
          v-for="s in evtSummaries" :key="s.year"
          :class="['yev-year-chip', { 'yev-year-active': s.year === evtYear }]"
          @click="selectYear(s.year)"
        >
          <div class="yev-year-num">{{ s.year }}</div>
          <div class="yev-year-gz">{{ s.year_ganzhi }}</div>
          <div
            class="yev-year-score-bar"
            :style="{ height: Math.round(s.annual_score * 40 / 10) + 'px', minHeight: '4px' }"
            :class="s.annual_score >= 6 ? 'bar-good' : s.annual_score <= 3 ? 'bar-bad' : 'bar-mid'"
          ></div>
          <div class="yev-year-risk" :class="'risk-' + s.risk">{{ RISK_LABEL[s.risk] }}</div>
        </div>
      </div>
      <p v-if="evtTrendLoading" class="muted small">加载趋势中…</p>
    </div>
    <div v-else-if="evtTrendLoading" class="yev-loading">加载多年趋势中…</div>
    <div v-else-if="!evtTrend" class="yev-no-trend">
      <button class="btn-sec" @click="fetchTrend()">加载多年趋势</button>
    </div>

    <!-- 年份选择器 + 事件类型切换 -->
    <div class="yev-controls">
      <div class="yev-year-pick">
        <label>预测年份</label>
        <input
          type="number"
          :value="evtYear"
          min="2020" max="2060"
          @change="selectYear(Number(($event.target as HTMLInputElement).value))"
        />
      </div>
      <div class="yev-event-pills">
        <button
          v-for="et in ALL_EVENT_TYPES" :key="et"
          :class="['evt-pill', { 'evt-pill-active': evtType === et }]"
          @click="selectEventType(et)"
        >{{ EVENT_DISPLAY[et] }}</button>
      </div>
    </div>
    <p v-if="evtLoading" class="muted">分析中…</p>

    <!-- 事件结果卡 -->
    <div v-if="evtResult" class="yev-result-card">
      <div class="yev-result-header">
        <span class="yev-event-name">{{ EVENT_DISPLAY[evtType] }}</span>
        <span class="yev-gz">{{ evtData?.year_ganzhi }} 年</span>
        <span :class="['yev-risk-badge', 'risk-' + evtResult.risk_level]">风险：{{ RISK_LABEL[evtResult.risk_level] }}</span>
        <span :class="['yev-opp-badge', 'opp-' + evtResult.opportunity_level]">机遇：{{ RISK_LABEL[evtResult.opportunity_level] }}</span>
        <span class="yev-conf">置信 {{ Math.round(evtResult.confidence * 100) }}%</span>
      </div>
      <p class="yev-main-judgment">{{ evtResult.main_judgment }}</p>
      <p v-if="evtResult.trigger_summary" class="yev-trigger-summary">{{ evtResult.trigger_summary }}</p>

      <!-- 信号列表 -->
      <div v-if="evtResult.signals?.length" class="yev-signals">
        <div v-for="sig in evtResult.signals" :key="sig.signal_key" :class="['yev-sig-chip', 'layer-' + sig.layer]">
          <span class="sig-layer-lbl">{{ SIGNAL_LAYER_LABEL[sig.layer] }}</span>
          <span class="sig-label">{{ sig.label }}</span>
        </div>
      </div>

      <!-- 关键月份 -->
      <div v-if="evtResult.key_months?.length" class="yev-months">
        <span class="yev-months-lbl">关键月份：</span>
        <span v-for="m in evtResult.key_months" :key="m" class="yev-month-tag">{{ m }}月</span>
      </div>

      <!-- 可能表现 -->
      <div v-if="evtResult.possible_manifestations?.length" class="yev-list-block">
        <div class="yev-list-title">可能的现实表现</div>
        <ul class="yev-list">
          <li v-for="m in evtResult.possible_manifestations" :key="m">{{ m }}</li>
        </ul>
      </div>

      <!-- 预兆 -->
      <div v-if="evtResult.omens?.length" class="yev-list-block">
        <div class="yev-list-title">现实预兆</div>
        <ul class="yev-list">
          <li v-for="o in evtResult.omens" :key="o">{{ o }}</li>
        </ul>
      </div>

      <!-- 建议 -->
      <div v-if="evtResult.advice?.length" class="yev-list-block yev-advice">
        <div class="yev-list-title">应对建议</div>
        <ul class="yev-list">
          <li v-for="a in evtResult.advice" :key="a">{{ a }}</li>
        </ul>
      </div>

      <!-- 古籍依据 -->
      <div v-if="evtResult.classical_notes?.length" class="yev-classical">
        <span v-for="cn in evtResult.classical_notes" :key="cn.basis" class="yev-classical-note">
          {{ cn.source }}「{{ cn.basis }}」
        </span>
      </div>

      <!-- avoid_overclaim -->
      <div v-if="evtResult.avoid_overclaim" class="yev-overclaim">
        ⚠ {{ evtResult.avoid_overclaim }}
      </div>
    </div>
    <div v-else-if="!evtLoading && evtData" class="muted">暂无该事件分析结果</div>
    <div v-else-if="!evtLoading && !evtData && caseId" class="yev-empty">
      <button class="btn-sec" @click="fetchYearEvents()">分析 {{ evtYear }} 年事件</button>
    </div>

    <!-- AI 咨询区 -->
    <div v-if="evtResult" class="yev-consult-block">
      <div class="yev-consult-title">AI 深度咨询</div>
      <div class="yev-consult-input-row">
        <input
          v-model="evtUserQuestion"
          class="yev-consult-input"
          placeholder="输入你的问题，例如：今年婚姻有没有问题？"
          @keyup.enter="handleEvtConsult(evtUserQuestion)"
        />
        <button
          class="btn-primary yev-ask-btn"
          :disabled="evtConsultLoading || !evtUserQuestion.trim()"
          @click="handleEvtConsult(evtUserQuestion)"
        >{{ evtConsultLoading ? '解读中…' : '咨询' }}</button>
      </div>
      <!-- 追问问题 -->
      <div class="yev-followup-row">
        <button
          v-for="q in evtFollowups" :key="q"
          class="yev-followup-btn"
          @click="handleEvtConsult(q)"
        >{{ q }}</button>
      </div>
      <!-- 解读结果 -->
      <div v-if="evtConsultText" class="yev-consult-result">
        <pre class="yev-consult-pre">{{ evtConsultText }}</pre>
      </div>
      <p v-if="evtConsultError" class="error-msg">{{ evtConsultError }}</p>
    </div>
  </section>
</template>

<style scoped>
/* ─── 年份事件预测 ─────────────────────────────────────────── */
.yev-timeline-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-year-track { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-4); overflow-x: auto; padding-bottom: 4px; }
.yev-year-chip { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 10px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); background: var(--surface-2); min-width: 52px; transition: border-color 0.2s, background 0.2s; }
.yev-year-chip:hover { border-color: var(--accent); }
.yev-year-active { border-color: var(--accent) !important; background: color-mix(in srgb, var(--accent) 10%, var(--surface-2)) !important; }
.yev-year-num { font-size: var(--fs-xs); color: var(--text-2); }
.yev-year-gz { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.yev-year-score-bar { width: 24px; border-radius: 3px; margin: 2px 0; }
.bar-good { background: #4ade80; } .bar-bad { background: #f87171; } .bar-mid { background: #fbbf24; }
.yev-year-risk { font-size: 10px; }
.yev-controls { display: flex; align-items: center; gap: var(--sp-4); flex-wrap: wrap; margin-bottom: var(--sp-4); }
.yev-year-pick { display: flex; align-items: center; gap: var(--sp-2); }
.yev-year-pick label { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; }
.yev-year-pick input { width: 80px; padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface-2); color: var(--text); }
.yev-event-pills { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
.evt-pill { padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-2); font-size: var(--fs-sm); color: var(--text-2); cursor: pointer; transition: all 0.15s; }
.evt-pill:hover { border-color: var(--accent); color: var(--text); }
.evt-pill-active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); font-weight: 600; }
.yev-result-card { border: 1px solid var(--border); border-radius: 12px; padding: var(--sp-4); margin-bottom: var(--sp-4); }
.yev-result-header { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-event-name { font-size: var(--fs-lg); font-weight: 700; color: var(--text); }
.yev-gz { font-size: var(--fs-sm); color: var(--text-2); }
.yev-risk-badge, .yev-opp-badge { font-size: var(--fs-xs); padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.risk-high { background: #fee2e2; color: #dc2626; }
.risk-medium_high { background: #fef3c7; color: #d97706; }
.risk-medium { background: #fef3c7; color: #ca8a04; }
.risk-low { background: #f0fdf4; color: #16a34a; }
.risk-none { background: var(--surface-2); color: var(--text-2); }
.opp-high { background: #d1fae5; color: #059669; }
.opp-medium_high { background: #d1fae5; color: #16a34a; }
.opp-medium { background: #ecfdf5; color: #22c55e; }
.opp-low { background: var(--surface-2); color: var(--text-2); }
.opp-none { background: var(--surface-2); color: var(--text-2); }
.yev-conf { font-size: var(--fs-xs); color: var(--text-2); margin-left: auto; }
.yev-main-judgment { font-size: var(--fs-md); color: var(--text); line-height: 1.6; margin-bottom: var(--sp-2); font-weight: 500; }
.yev-trigger-summary { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-3); }
.yev-signals { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-sig-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 12px; font-size: var(--fs-xs); border: 1px solid var(--border); background: var(--surface-2); }
.layer-natal_base { border-color: #c4b5fd; background: #f5f3ff; }
.layer-dayun_trigger { border-color: #93c5fd; background: #eff6ff; }
.layer-liunian_trigger { border-color: #6ee7b7; background: #ecfdf5; }
.layer-month_trigger { border-color: #fde68a; background: #fffbeb; }
.sig-layer-lbl { font-size: 10px; color: var(--text-2); }
.sig-label { font-size: var(--fs-xs); color: var(--text); }
.yev-months { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: var(--sp-3); }
.yev-months-lbl { font-size: var(--fs-sm); color: var(--text-2); white-space: nowrap; }
.yev-month-tag { padding: 2px 8px; background: color-mix(in srgb, var(--accent) 15%, var(--surface-2)); color: var(--accent); border-radius: 4px; font-size: var(--fs-xs); font-weight: 600; }
.yev-list-block { margin-bottom: var(--sp-3); }
.yev-list-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); margin-bottom: var(--sp-1); }
.yev-list { margin: 0; padding-left: 1.2em; font-size: var(--fs-sm); color: var(--text); line-height: 1.7; }
.yev-advice .yev-list-title { color: var(--accent); }
.yev-classical { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: var(--sp-2); }
.yev-classical-note { margin-right: var(--sp-3); }
.yev-overclaim { font-size: var(--fs-xs); color: #d97706; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 6px 10px; margin-top: var(--sp-2); }
.yev-consult-block { margin-top: var(--sp-4); border-top: 1px solid var(--border); padding-top: var(--sp-4); }
.yev-consult-title { font-size: var(--fs-md); font-weight: 700; color: var(--text); margin-bottom: var(--sp-3); }
.yev-consult-input-row { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); }
.yev-consult-input { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); color: var(--text); font-size: var(--fs-sm); }
.yev-consult-input:focus { outline: none; border-color: var(--accent); }
.yev-ask-btn { white-space: nowrap; }
.yev-followup-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.yev-followup-btn { padding: 4px 12px; font-size: var(--fs-xs); border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); color: var(--text-2); cursor: pointer; transition: border-color 0.15s; }
.yev-followup-btn:hover { border-color: var(--accent); color: var(--text); }
.yev-consult-result { background: var(--surface-2); border-radius: 8px; padding: var(--sp-4); border: 1px solid var(--border); }
.yev-consult-pre { white-space: pre-wrap; word-break: break-word; font-family: var(--font-cn); font-size: var(--fs-sm); color: var(--text); line-height: 1.8; margin: 0; }
.yev-no-trend, .yev-empty { padding: var(--sp-4) 0; }
.yev-loading { color: var(--text-2); font-size: var(--fs-sm); padding: var(--sp-3) 0; }
.yev-save-hint {
  display: flex; flex-direction: column; align-items: flex-start;
  padding: var(--sp-3) var(--sp-4);
  background: color-mix(in srgb, var(--accent) 6%, var(--surface-2));
  border: 1px dashed var(--border);
  border-radius: 8px;
  margin-bottom: var(--sp-3);
}
.yev-save-hint p { margin: 0; font-size: var(--fs-sm); }
.yev-trend-block { margin-bottom: var(--sp-4); }
.section-inline { margin-bottom: var(--sp-5); }
.section-inline .card-title { font-size: var(--fs-xl); font-weight: 700; padding-bottom: var(--sp-3); border-bottom: 1px solid var(--border); margin-bottom: var(--sp-4); }
</style>
