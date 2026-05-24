<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FlyingChartResponse } from '@/api/ziwei'
import {
  getReceivedTransformLabels,
  getReceivedTransformTexts,
  tfColorStyle,
  type FlyingReceivedItem,
} from '@/utils/ziweiViewHelpers'

type FlyingFilter = 'all' | 'lu' | 'quan' | 'ke' | 'ji'
type FlyingInsight = {
  type: '禄' | '权' | '科' | '忌'
  palaces: string[]
  cls: string
}

const props = defineProps<{
  flying: FlyingChartResponse
}>()

const flyingFilter = ref<FlyingFilter>('all')

const filteredFlyingPalaces = computed(() => {
  if (!props.flying.palaces?.length) return []
  if (flyingFilter.value === 'all') return props.flying.palaces

  const tfMap: Record<Exclude<FlyingFilter, 'all'>, string> = {
    lu: '禄',
    quan: '权',
    ke: '科',
    ji: '忌',
  }
  const target = tfMap[flyingFilter.value]
  return props.flying.palaces.filter((palace) =>
    Object.values(palace.flying_out || {}).some((transform) => transform.includes(target)),
  )
})

const flyingKeyInsights = computed<FlyingInsight[]>(() => {
  const TF_TYPES = ['禄', '权', '科', '忌'] as const
  const TF_CLS: Record<FlyingInsight['type'], string> = {
    '禄': 'fi-lu',
    '权': 'fi-quan',
    '科': 'fi-ke',
    '忌': 'fi-ji',
  }
  const groups: Record<FlyingInsight['type'], string[]> = {
    '禄': [],
    '权': [],
    '科': [],
    '忌': [],
  }

  if (props.flying.received) {
    Object.entries(props.flying.received).forEach(([palace, transforms]) => {
      getReceivedTransformTexts(transforms as FlyingReceivedItem).forEach((transform) => {
        TF_TYPES.forEach((type) => {
          if (transform.includes(type) && !groups[type].includes(palace)) groups[type].push(palace)
        })
      })
    })
  } else {
    ;(props.flying.palaces ?? []).forEach((palace) => {
      Object.values(palace.flying_out ?? {}).forEach((transform) => {
        TF_TYPES.forEach((type) => {
          if (transform.includes(type)) {
            const target = palace.opposition_palace || palace.palace_name
            if (!groups[type].includes(target)) groups[type].push(target)
          }
        })
      })
    })
  }

  return TF_TYPES
    .map((type) => ({
      type,
      palaces: groups[type],
      cls: TF_CLS[type],
    }))
    .filter((item) => item.palaces.length > 0)
})
</script>

<template>
  <div v-if="flyingKeyInsights.length" class="flying-insights-bar">
    <span class="fib-label">落宫</span>
    <div v-for="item in flyingKeyInsights" :key="item.type" :class="['fib-item', item.cls]">
      <span class="fib-type">{{ item.type }}</span>
      <span class="fib-arrow">→</span>
      <span class="fib-palaces">{{ item.palaces.join('、') }}</span>
    </div>
  </div>

  <div class="flying-toolbar">
    <div class="flying-stats">
      <span class="flying-stat">自化 <b>{{ flying.self_transforms?.length || 0 }}</b></span>
      <span class="flying-stat">宫位 <b>{{ flying.palaces?.length || 0 }}</b></span>
      <span class="flying-stat">接收 <b>{{ Object.keys(flying.received || {}).length }}</b></span>
      <span class="flying-stat">冲宫 <b>{{ Object.keys(flying.chonged || {}).length }}</b></span>
    </div>
    <div class="flying-filter">
      <span class="ff-label">筛选：</span>
      <button :class="['ff-btn', { active: flyingFilter === 'all' }]" @click="flyingFilter = 'all'">全部</button>
      <button :class="['ff-btn ff-lu', { active: flyingFilter === 'lu' }]" @click="flyingFilter = 'lu'">禄</button>
      <button :class="['ff-btn ff-quan', { active: flyingFilter === 'quan' }]" @click="flyingFilter = 'quan'">权</button>
      <button :class="['ff-btn ff-ke', { active: flyingFilter === 'ke' }]" @click="flyingFilter = 'ke'">科</button>
      <button :class="['ff-btn ff-ji', { active: flyingFilter === 'ji' }]" @click="flyingFilter = 'ji'">忌</button>
    </div>
  </div>

  <div v-if="flying.self_transforms?.length && flyingFilter === 'all'" class="section-block">
    <h3 class="section-title">
      自化星
      <span class="section-count">{{ flying.self_transforms.length }}</span>
    </h3>
    <div class="flying-tags-row">
      <span v-for="star in flying.self_transforms" :key="star" class="flying-self-tag">{{ star }}</span>
    </div>
  </div>

  <div class="flying-palaces-grid">
    <div v-for="palace in filteredFlyingPalaces" :key="palace.palace_name" class="flying-palace-card">
      <div class="fp-head">
        <span class="fp-name">{{ palace.palace_name }}</span>
        <span v-if="palace.stem_name" class="fp-stem">{{ palace.stem_name }}</span>
      </div>
      <div v-if="Object.keys(palace.flying_out || {}).length" class="fp-row">
        <span class="fp-label">飞出：</span>
        <span v-for="(transform, star) in palace.flying_out" :key="star" class="pc-tf" :style="tfColorStyle(transform)">
          {{ star }}{{ transform.slice(1) }}
        </span>
      </div>
      <div v-if="palace.opposition_palace" class="fp-row fp-opp">
        对宫：<b>{{ palace.opposition_palace }}</b>
      </div>
      <div v-if="palace.self_transforms?.length" class="fp-row">
        <span class="fp-label">自化：</span>
        <span v-for="star in palace.self_transforms" :key="star" class="fp-self-tag">{{ star }}</span>
      </div>
    </div>
  </div>
  <p v-if="filteredFlyingPalaces.length === 0 && flyingFilter !== 'all'" class="muted">没有符合筛选条件的飞化</p>

  <div v-if="flying.received && Object.keys(flying.received).length && flyingFilter === 'all'" class="section-block section-gap">
    <h3 class="section-title">各宫接收四化</h3>
    <div class="flying-received-grid">
      <div v-for="(transforms, palace) in flying.received" :key="palace" class="fr-item">
        <span class="fr-palace">{{ palace }}</span>
        <div class="fr-tfs">
          <span v-for="label in getReceivedTransformLabels(transforms as FlyingReceivedItem)" :key="label" class="pc-tf fr-tf">
            {{ label }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <div v-if="flying.chonged && Object.keys(flying.chonged).length && flyingFilter === 'all'" class="section-block section-gap">
    <h3 class="section-title">冲宫关系</h3>
    <div class="flying-received-grid">
      <div v-for="(value, palace) in flying.chonged" :key="palace" class="fr-item">
        <span class="fr-palace">{{ palace }}</span>
        <span class="fr-opp">↔ {{ value }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-block { margin-bottom: var(--sp-6); }
.section-gap { margin-top: var(--sp-5); }
.section-title {
  font-size: var(--fs-lg);
  font-weight: 600;
  margin-bottom: var(--sp-4);
  color: var(--text);
}
.section-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  margin-left: var(--sp-2);
  padding: 1px 8px;
  font-size: var(--fs-xs);
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--text-2);
}
.flying-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-4);
}
.flying-stats { display: flex; flex-wrap: wrap; gap: 8px; }
.flying-stat {
  font-size: var(--fs-sm);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-2);
}
.flying-filter { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.ff-label { font-size: var(--fs-sm); color: var(--text-2); margin-right: 4px; }
.ff-btn {
  padding: 4px 10px;
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.ff-btn:hover { border-color: var(--accent); }
.ff-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.ff-btn.ff-lu.active { background: #16a34a; border-color: #16a34a; }
.ff-btn.ff-quan.active { background: #dc2626; border-color: #dc2626; }
.ff-btn.ff-ke.active { background: #2563eb; border-color: #2563eb; }
.ff-btn.ff-ji.active { background: #1e293b; border-color: #1e293b; }
.flying-tags-row { display: flex; flex-wrap: wrap; gap: 8px; }
.flying-self-tag {
  font-size: var(--fs-xs);
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(124,58,237,.08);
  color: #7c3aed;
  border: 1px solid rgba(124,58,237,.15);
}
.flying-palaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-5);
}
.flying-insights-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  margin-bottom: var(--sp-4);
}
.fib-label { font-size: var(--fs-xs); color: var(--text-2); flex-shrink: 0; }
.fib-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-md);
  background: var(--surface);
  font-size: var(--fs-xs);
}
.fib-type { font-weight: 700; font-size: var(--fs-sm); }
.fib-arrow { color: var(--text-2); }
.fib-palaces { color: var(--text); }
.fi-lu { border-color: #86efac; background: #f0fdf4; }
.fi-lu .fib-type { color: #166534; }
.fi-quan { border-color: #fca5a5; background: #fff1f2; }
.fi-quan .fib-type { color: #991b1b; }
.fi-ke { border-color: #93c5fd; background: #eff6ff; }
.fi-ke .fib-type { color: #1e40af; }
.fi-ji { border-color: #c4b5fd; background: #f5f3ff; }
.fi-ji .fib-type { color: #5b21b6; }
.flying-palace-card {
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.fp-head { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.fp-name { font-size: var(--fs-sm); font-weight: 700; font-family: var(--font-cn); }
.fp-stem { font-size: var(--fs-xs); color: var(--text-2); }
.fp-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 3px; font-size: var(--fs-xs); }
.fp-label { color: var(--text-2); flex-shrink: 0; }
.fp-opp { color: var(--text-2); }
.fp-self-tag {
  font-size: var(--fs-xs);
  padding: 1px 5px;
  background: rgba(124,58,237,.08);
  color: #7c3aed;
  border-radius: 4px;
  border: 1px solid rgba(124,58,237,.15);
}
.pc-tf {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: var(--fs-xs);
  font-weight: 700;
}
.flying-received-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--sp-2);
}
.fr-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.fr-palace { font-size: var(--fs-sm); font-weight: 600; font-family: var(--font-cn); min-width: 36px; }
.fr-tfs { display: flex; flex-wrap: wrap; gap: 3px; }
.fr-tf { font-size: 10px !important; padding: 1px 4px !important; }
.fr-opp { font-size: var(--fs-sm); color: var(--text-2); }
.muted { color: var(--text-3); font-size: var(--fs-sm); }
</style>
