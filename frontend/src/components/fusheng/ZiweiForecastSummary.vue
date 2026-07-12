<script setup lang="ts">
import { computed } from 'vue'
import type { EvidenceItem, ForecastResultResponse } from '@/api/ziwei'

const props = defineProps<{
  forecast?: ForecastResultResponse | null
  evidenceChain?: EvidenceItem[] | null
}>()

const TIER_LABEL: Record<string, string> = {
  favorable: '偏顺',
  neutral: '平稳',
  caution: '偏逆',
}

const tierClass = computed(() => {
  const tier = props.forecast?.yearly?.tier ?? props.forecast?.current_month?.tier ?? 'neutral'
  return `forecast-summary--${tier}`
})

const headline = computed(() => {
  const fc = props.forecast
  if (!fc?.yearly) return '暂无运势摘要'
  const tier = fc.yearly.tier ? TIER_LABEL[fc.yearly.tier] ?? fc.yearly.tier : ''
  return `${fc.year} 年 · ${fc.yearly.score} 分${tier ? ` · ${tier}` : ''} · ${fc.yearly.overall || '—'}`
})

const advice = computed(() =>
  props.forecast?.yearly?.advice || props.forecast?.current_month?.advice || '暂无建议。')

const evidenceRows = computed(() => (props.evidenceChain ?? []).slice(0, 3))

const eventHints = computed(() => {
  const events = props.forecast?.yearly?.events ?? []
  return events.slice(0, 3).map((e) => `${e.category}（${e.level}）：${e.description}`)
})
</script>

<template>
  <section
    v-if="forecast"
    class="forecast-summary fs-card"
    data-testid="ziwei-forecast-summary"
    :class="tierClass"
  >
    <h3>运限摘要</h3>
    <p class="forecast-summary__headline">{{ headline }}</p>
    <p class="forecast-summary__advice">{{ advice }}</p>

    <ul v-if="eventHints.length" class="forecast-summary__events">
      <li v-for="(line, idx) in eventHints" :key="idx">{{ line }}</li>
    </ul>

    <div v-if="evidenceRows.length" class="forecast-summary__evidence">
      <h4>依据链（前 3 条）</h4>
      <ul>
        <li v-for="(item, idx) in evidenceRows" :key="idx">
          <strong>{{ item.title }}</strong>：{{ item.value }}
          <span v-if="item.source" class="forecast-summary__source">（{{ item.source }}）</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.forecast-summary {
  padding: 14px 16px;
  border: 1px solid var(--border-soft, #e7e0d5);
  background: #fffdf7;
}

.forecast-summary h3 {
  margin: 0 0 8px;
  font-family: var(--font-cn);
  font-size: 15px;
  color: var(--brand-ink);
}

.forecast-summary h4 {
  margin: 12px 0 6px;
  font-size: 12px;
  color: #57534e;
}

.forecast-summary__headline {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #292524;
}

.forecast-summary__advice {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #44403c;
}

.forecast-summary__events {
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.55;
  color: #57534e;
}

.forecast-summary__evidence ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.55;
  color: #57534e;
}

.forecast-summary__source {
  color: #78716c;
}

.forecast-summary--favorable {
  border-color: var(--brand-gold);
  background: var(--brand-gold-lt);
}

.forecast-summary--caution {
  border-color: var(--brand-cinnabar);
  background: var(--surface);
  border-left: 3px solid var(--brand-cinnabar);
}
</style>
