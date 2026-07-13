<script setup lang="ts">
import { computed } from 'vue'
import type { LiuriLiushiModel } from '@/api/bazi'

const props = defineProps<{
  liuri?: LiuriLiushiModel | null
}>()

function scoreLabel(value?: number | null): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return String(value)
}

const transitionHint = computed(() => {
  const hint = props.liuri?.transition_hint?.trim()
  if (!hint) return ''
  const summary = props.liuri?.flow_summary?.trim() ?? ''
  if (summary && summary.includes(hint)) return ''
  return hint
})
</script>

<template>
  <section v-if="liuri?.day_ganzhi" class="liuri-today" data-testid="bazi-liuri-today">
    <header class="liuri-today__head">
      <h2>今日流日</h2>
      <p class="liuri-today__date">{{ liuri.date || '今天' }}</p>
    </header>
    <div class="liuri-today__pillars">
      <span><strong>日柱</strong> {{ liuri.day_ganzhi }}{{ liuri.day_ten_god ? `（${liuri.day_ten_god}）` : '' }}</span>
      <span><strong>时柱</strong> {{ liuri.hour_ganzhi }}{{ liuri.hour_ten_god ? `（${liuri.hour_ten_god}）` : '' }}</span>
    </div>
    <p v-if="liuri.flow_summary || liuri.flow_tone" class="liuri-today__flow">
      {{ liuri.flow_summary || liuri.flow_tone }}
    </p>
    <div class="liuri-today__scores">
      <div class="liuri-today__score-cell">
        <span class="label">大运维</span>
        <span class="value">{{ scoreLabel(liuri.flow_score_dayun ?? liuri.flow_score) }}</span>
      </div>
      <div class="liuri-today__score-cell">
        <span class="label">流年维</span>
        <span class="value">{{ scoreLabel(liuri.flow_score_liunian) }}</span>
      </div>
      <div class="liuri-today__score-cell">
        <span class="label">格局维</span>
        <span class="value">{{ scoreLabel(liuri.flow_score_geju) }}</span>
      </div>
    </div>
    <p v-if="transitionHint" class="liuri-today__hint">{{ transitionHint }}</p>
    <ul v-if="liuri.warnings?.length" class="liuri-today__warnings">
      <li v-for="(w, idx) in liuri.warnings" :key="idx">{{ w }}</li>
    </ul>
  </section>
</template>

<style scoped>
.liuri-today {
  display: grid;
  gap: 10px;
}

.liuri-today__head h2 {
  margin: 0;
  padding-left: 10px;
  border-left: 3px solid var(--brand-gold);
  font-family: var(--font-display);
  font-size: 13px;
  letter-spacing: 0.1em;
  font-weight: 600;
  color: var(--brand-ink);
}

.liuri-today__date {
  margin: 4px 0 0;
  color: var(--text-2);
  font-size: 13px;
}

.liuri-today__pillars {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  font-size: 14px;
  color: var(--text-2);
}

.liuri-today__flow {
  margin: 0;
  line-height: 1.7;
  color: var(--brand-ink);
  font-size: 14px;
}

.liuri-today__scores {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.liuri-today__score-cell {
  padding: 10px;
  border-radius: 10px;
  background: var(--inset-tint);
  border: 1px solid var(--border);
  text-align: center;
}

.liuri-today__score-cell .label {
  display: block;
  font-size: 11px;
  color: var(--text-3);
}

.liuri-today__score-cell .value {
  display: block;
  margin-top: 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--brand-gold-dark);
}

.liuri-today__hint {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-gold);
  color: var(--brand-mist);
  font-size: 13px;
}

.liuri-today__warnings {
  margin: 0;
  padding-left: 18px;
  color: var(--brand-cinnabar);
  font-size: 13px;
}
</style>
