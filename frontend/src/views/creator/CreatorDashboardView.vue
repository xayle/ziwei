<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAuthMe } from '@/api/auth'
import {
  fetchCreatorStats,
  formatConversionRate,
  type CreatorStatsResponse,
} from '@/api/creatorStats'
import { useAuthStore } from '@/stores/auth'
import '@/assets/fusheng-page.css'

const router = useRouter()
const auth = useAuthStore()

const windowDays = ref(30)
const loading = ref(false)
const forbidden = ref(false)
const errorMsg = ref('')
const stats = ref<CreatorStatsResponse | null>(null)

const topics = computed(() => stats.value?.topics ?? [])
const funnel = computed(() => stats.value?.funnel ?? [])
const totals = computed(() => stats.value?.totals)

const funnelMax = computed(() => Math.max(1, ...funnel.value.map((s) => s.count || 0)))

async function load() {
  if (!auth.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: '/creator' } })
    return
  }
  loading.value = true
  errorMsg.value = ''
  forbidden.value = false
  try {
    const me = await fetchAuthMe()
    if (!me.is_admin) {
      forbidden.value = true
      stats.value = null
      return
    }
    stats.value = await fetchCreatorStats(windowDays.value)
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 403) {
      forbidden.value = true
      stats.value = null
    } else if (status === 401) {
      router.push({ path: '/login', query: { redirect: '/creator' } })
    } else {
      errorMsg.value = '统计加载失败，请稍后重试。'
    }
  } finally {
    loading.value = false
  }
}

watch(windowDays, () => {
  void load()
})

onMounted(() => {
  void load()
})

function funnelLabel(step: string): string {
  const map: Record<string, string> = {
    landing_cta: '落地页 CTA',
    volume_view: '卷阅读',
    share_card_export: '分享卡导出',
    registration: '注册',
    paid: '付费',
  }
  return map[step] || step
}
</script>

<template>
  <main class="fs-page creator-dash">
    <header class="fs-page-head">
      <div>
        <p class="fs-page-head__eyebrow">FE-GTM-05 · T100</p>
        <h1 class="fs-page-head__title">创作者看板</h1>
        <p class="fs-page-lead">
          主题归因 → 注册 → 付费转化（仅管理员）。数据来自
          <code>GET /api/v1/creator/stats</code>。
        </p>
      </div>
      <div class="fs-page-actions">
        <label class="window-picker">
          窗口
          <select v-model.number="windowDays" :disabled="loading || forbidden">
            <option :value="7">7 天</option>
            <option :value="14">14 天</option>
            <option :value="30">30 天</option>
            <option :value="90">90 天</option>
          </select>
        </label>
        <button type="button" class="fs-btn fs-btn--ghost" @click="router.push('/')">返回首页</button>
        <button type="button" class="fs-btn fs-btn--primary" :disabled="loading" @click="load">
          刷新
        </button>
      </div>
    </header>

    <p v-if="forbidden" class="state state--warn" role="status">
      需要管理员权限才能查看创作者统计。
    </p>
    <p v-else-if="errorMsg" class="state state--err" role="alert">{{ errorMsg }}</p>
    <p v-else-if="loading && !stats" class="state" role="status">加载中…</p>

    <template v-else-if="stats && totals">
      <section class="totals" aria-label="汇总">
        <div class="total-cell">
          <span class="total-cell__label">用户</span>
          <strong>{{ totals.users }}</strong>
        </div>
        <div class="total-cell">
          <span class="total-cell__label">有归因</span>
          <strong>{{ totals.attributed_users }}</strong>
        </div>
        <div class="total-cell">
          <span class="total-cell__label">付费</span>
          <strong>{{ totals.paid_users }}</strong>
        </div>
        <div class="total-cell">
          <span class="total-cell__label">落地 CTA</span>
          <strong>{{ totals.landing_cta_clicks }}</strong>
        </div>
        <div class="total-cell">
          <span class="total-cell__label">卷阅读</span>
          <strong>{{ totals.volume_views }}</strong>
        </div>
        <div class="total-cell">
          <span class="total-cell__label">分享导出</span>
          <strong>{{ totals.share_card_exports }}</strong>
        </div>
      </section>

      <section class="panel" aria-labelledby="funnel-h">
        <h2 id="funnel-h">漏斗</h2>
        <ul v-if="funnel.length" class="funnel">
          <li v-for="step in funnel" :key="step.step" class="funnel__row">
            <span class="funnel__name">{{ funnelLabel(step.step) }}</span>
            <span class="funnel__bar-wrap" aria-hidden="true">
              <span
                class="funnel__bar"
                :style="{ width: `${Math.round((step.count / funnelMax) * 100)}%` }"
              />
            </span>
            <span class="funnel__count">{{ step.count }}</span>
          </li>
        </ul>
        <p v-else class="state">暂无漏斗事件。</p>
      </section>

      <section class="panel" aria-labelledby="topics-h">
        <h2 id="topics-h">主题转化表</h2>
        <div class="table-wrap">
          <table v-if="topics.length" class="cohort-table">
            <thead>
              <tr>
                <th scope="col">主题键</th>
                <th scope="col">source</th>
                <th scope="col">campaign</th>
                <th scope="col">content</th>
                <th scope="col">注册</th>
                <th scope="col">付费</th>
                <th scope="col">转化率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in topics" :key="row.topic_key">
                <td class="mono">{{ row.topic_key }}</td>
                <td>{{ row.utm_source || '—' }}</td>
                <td>{{ row.utm_campaign || '—' }}</td>
                <td>{{ row.content_id || '—' }}</td>
                <td>{{ row.registrations }}</td>
                <td>{{ row.paid_conversions }}</td>
                <td>{{ formatConversionRate(row.conversion_rate) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="state">窗口内暂无 UTM 主题 cohort。</p>
        </div>
        <p class="meta">
          窗口 {{ stats.window_days }} 天 · 生成于 {{ stats.generated_at }}
        </p>
      </section>
    </template>
  </main>
</template>

<style scoped>
.creator-dash {
  gap: var(--sp-5, 18px);
  max-width: 960px;
  margin-inline: auto;
  padding: var(--sp-4, 16px);
}

.fs-page-head__title {
  margin: 0.2em 0 0;
  font-family: "LXGW Neo ZhiSong", "Songti SC", serif;
  font-size: clamp(1.4rem, 3vw, 1.85rem);
  color: var(--brand-ink);
}

.window-picker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-sm, 0.9rem);
  color: var(--brand-mist);
}

.window-picker select {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--brand-ink);
  border-radius: 4px;
  padding: 4px 8px;
}

.state {
  margin: 0;
  color: var(--brand-mist);
  line-height: 1.6;
}

.state--warn {
  color: var(--brand-gold-dark);
  border-left: 3px solid var(--brand-gold);
  padding-left: 12px;
}

.state--err {
  color: var(--brand-cinnabar);
  border-left: 3px solid var(--brand-cinnabar);
  padding-left: 12px;
}

.totals {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.total-cell {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius-codex, 6px);
}

.total-cell__label {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--brand-mist);
}

.total-cell strong {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--brand-ink);
}

.panel {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius-codex, 6px);
}

.panel h2 {
  margin: 0;
  font-size: 1.05rem;
  font-family: "LXGW Neo ZhiSong", "Songti SC", serif;
  color: var(--brand-ink);
}

.funnel {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.funnel__row {
  display: grid;
  grid-template-columns: 7.5rem 1fr 3rem;
  gap: 10px;
  align-items: center;
}

.funnel__name {
  font-size: var(--fs-sm, 0.9rem);
  color: var(--brand-mist);
}

.funnel__bar-wrap {
  height: 8px;
  background: var(--surface-2);
  border-radius: 2px;
  overflow: hidden;
}

.funnel__bar {
  display: block;
  height: 100%;
  background: var(--brand-gold);
  min-width: 0;
}

.funnel__count {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.table-wrap {
  overflow-x: auto;
}

.cohort-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm, 0.9rem);
}

.cohort-table th,
.cohort-table td {
  border-bottom: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}

.cohort-table th {
  color: var(--brand-mist);
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.06em;
}

.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 0.85em;
}

.meta {
  margin: 0;
  font-size: 12px;
  color: var(--brand-mist);
}

@media (max-width: 560px) {
  .funnel__row {
    grid-template-columns: 1fr 2.5rem;
    grid-template-rows: auto auto;
  }

  .funnel__bar-wrap {
    grid-column: 1 / -1;
    order: 3;
  }
}
</style>
