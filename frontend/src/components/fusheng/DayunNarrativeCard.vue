<script setup lang="ts">
import { computed } from 'vue'
import PatternTierBadge from '@/components/fusheng/PatternTierBadge.vue'
import {
  resolveDayunNarrativeSections,
  type DayunNarrativeSections,
} from '@/utils/parseDayunNarrativeSections'

const props = withDefaults(defineProps<{
  ganzhi: string
  range: string
  tenGod?: string | null
  gejuImpact?: string | null
  yongshenShiftLabel?: string | null
  narrative?: string | null
  sections?: DayunNarrativeSections | null
  showReferenceShell?: boolean
}>(), {
  showReferenceShell: true,
})

const resolved = computed(() => resolveDayunNarrativeSections(props.sections, props.narrative))
const hasDomains = computed(() => {
  const s = resolved.value
  return !!(s?.career || s?.wealth || s?.love || s?.health)
})

const domains = [
  { key: 'career' as const, title: '事业' },
  { key: 'wealth' as const, title: '财运' },
  { key: 'love' as const, title: '情感' },
  { key: 'health' as const, title: '健康' },
]
</script>

<template>
  <article class="dayun-narrative-card" data-testid="dayun-narrative-card">
    <header class="dayun-narrative-card__data" data-testid="dayun-narrative-data">
      <h3 class="dayun-narrative-card__title">
        {{ ganzhi }} · 大运
        <PatternTierBadge layer="heuristic" />
      </h3>
      <p class="dayun-narrative-card__facts">
        <span>{{ range || '大运周期' }}</span>
        <span v-if="tenGod">十神 {{ tenGod }}</span>
        <span v-if="yongshenShiftLabel">{{ yongshenShiftLabel }}</span>
      </p>
      <p v-if="gejuImpact" class="dayun-narrative-card__engine">{{ gejuImpact }}</p>
    </header>

    <template v-if="resolved">
      <p v-if="resolved.core" class="dayun-narrative-card__core">{{ resolved.core }}</p>
      <p v-if="resolved.trend_note" class="dayun-narrative-card__trend">{{ resolved.trend_note }}</p>

      <div
        v-if="hasDomains"
        class="dayun-narrative-card__grid"
        data-testid="dayun-narrative-domains"
      >
        <section
          v-for="domain in domains"
          :key="domain.key"
          class="dayun-narrative-card__domain"
          :data-domain="domain.key"
        >
          <h4>{{ domain.title }}</h4>
          <p>{{ resolved[domain.key] || '—' }}</p>
        </section>
      </div>
      <p
        v-else-if="resolved.core"
        class="dayun-narrative-card__fallback"
        data-testid="dayun-narrative-fallback"
      >
        {{ resolved.core }}
      </p>

      <details v-if="resolved.classics?.length" class="dayun-narrative-card__classics">
        <summary>古籍佐证</summary>
        <ul>
          <li v-for="(c, idx) in resolved.classics" :key="idx">
            <strong>{{ c.source }}</strong>：「{{ c.text }}」
          </li>
        </ul>
      </details>
      <p v-if="resolved.disclaimer" class="dayun-narrative-card__disclaimer">{{ resolved.disclaimer }}</p>
    </template>

    <details
      v-if="showReferenceShell"
      class="dayun-narrative-card__ref"
      data-testid="dayun-reference-tracks"
    >
      <summary>互证参考 · 河洛｜奇门</summary>
      <p class="dayun-narrative-card__ref-body">
        河洛易数、奇门遁甲参考轨尚未接入计算，不展示推演结果。当前仅以八字大运启发式讲解为准。
      </p>
      <p class="dayun-narrative-card__ref-status" data-status="not_implemented">状态：未接入</p>
    </details>
  </article>
</template>

<style scoped>
.dayun-narrative-card {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
}

.dayun-narrative-card__title {
  margin: 0;
  font-size: 1.05rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.dayun-narrative-card__facts {
  margin: 6px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  font-size: 0.92rem;
  color: var(--muted, #5c5346);
}

.dayun-narrative-card__engine,
.dayun-narrative-card__core,
.dayun-narrative-card__trend {
  margin: 0;
  line-height: 1.55;
  font-size: 0.95rem;
}

.dayun-narrative-card__grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 640px) {
  .dayun-narrative-card__grid {
    grid-template-columns: 1fr;
  }
}

.dayun-narrative-card__domain {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface) 92%, var(--ink, #2a241c) 4%);
}

.dayun-narrative-card__domain h4 {
  margin: 0 0 6px;
  font-size: 0.9rem;
}

.dayun-narrative-card__domain p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.55;
}

.dayun-narrative-card__classics,
.dayun-narrative-card__ref {
  border-top: 1px solid var(--border);
  padding-top: 8px;
  font-size: 0.88rem;
}

.dayun-narrative-card__classics ul {
  margin: 8px 0 0;
  padding-left: 1.1rem;
}

.dayun-narrative-card__disclaimer,
.dayun-narrative-card__ref-body,
.dayun-narrative-card__ref-status {
  margin: 6px 0 0;
  color: var(--muted, #5c5346);
  font-size: 0.85rem;
}

.dayun-narrative-card__fallback {
  margin: 0;
  line-height: 1.55;
}
</style>
