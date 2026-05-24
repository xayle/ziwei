<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LifeSuggestionResponse, RemedyResponse } from '@/api/ziwei'

const props = defineProps<{
  remedies: RemedyResponse[]
  lifeSuggestions: LifeSuggestionResponse[]
}>()

const suggestCategoryFilter = ref<string>('all')

const suggestCategories = computed(() => {
  const categories = new Set<string>()
  props.lifeSuggestions.forEach((suggestion) => {
    const category = suggestion.category_label || suggestion.category
    if (category) categories.add(category)
  })
  return Array.from(categories)
})

const filteredLifeSuggestions = computed(() => {
  if (suggestCategoryFilter.value === 'all') return props.lifeSuggestions
  return props.lifeSuggestions.filter(
    (suggestion) => (suggestion.category_label || suggestion.category) === suggestCategoryFilter.value,
  )
})

const sortedRemedies = computed(() =>
  [...props.remedies].sort((a, b) => (a.priority ?? 9) - (b.priority ?? 9)),
)

const highPriorityCount = computed(() => props.remedies.filter((item) => item.priority === 1).length)
</script>

<template>
  <div class="suggest-overview card">
    <div class="sov-grid">
      <div class="sov-item sov-remedy">
        <span class="sov-num">{{ remedies.length }}</span>
        <span class="sov-label">化解建议</span>
      </div>
      <div class="sov-item sov-life">
        <span class="sov-num">{{ lifeSuggestions.length }}</span>
        <span class="sov-label">生活建议</span>
      </div>
      <div v-if="suggestCategories.length" class="sov-item sov-cats">
        <span class="sov-num">{{ suggestCategories.length }}</span>
        <span class="sov-label">领域分类</span>
      </div>
      <div class="sov-item sov-p1">
        <span class="sov-num">{{ highPriorityCount }}</span>
        <span class="sov-label">高优先项</span>
      </div>
    </div>

    <div v-if="suggestCategories.length" class="sov-filter">
      <button :class="['sov-cat-btn', { active: suggestCategoryFilter === 'all' }]" @click="suggestCategoryFilter = 'all'">全部</button>
      <button v-for="category in suggestCategories" :key="category" :class="['sov-cat-btn', { active: suggestCategoryFilter === category }]" @click="suggestCategoryFilter = category">
        {{ category }}
      </button>
    </div>
  </div>

  <div v-if="sortedRemedies.length" class="section-block">
    <h3 class="section-title">
      化解与调整
      <span class="section-count">{{ sortedRemedies.length }}</span>
    </h3>
    <div class="remedies-list">
      <div v-for="(remedy, index) in sortedRemedies" :key="index" class="remedy-item">
        <div class="remedy-head">
          <span v-if="remedy.priority" :class="['remedy-priority', `priority-${remedy.priority}`]">P{{ remedy.priority }}</span>
          <span class="remedy-cat">{{ remedy.cost_level || '建议' }}</span>
          <span class="remedy-name">{{ remedy.name }}</span>
          <span v-if="remedy.valid_scope" class="remedy-scope">{{ remedy.valid_scope }}</span>
        </div>
        <div v-if="remedy.actions?.length" class="remedy-actions">
          <div v-for="(action, actionIndex) in remedy.actions" :key="actionIndex" class="remedy-step">{{ actionIndex + 1 }}. {{ action }}</div>
        </div>
        <div v-if="remedy.evidence" class="remedy-reason">— {{ remedy.evidence }}</div>
        <p v-if="remedy.disclaimer" class="remedy-disclaimer">⚠ {{ remedy.disclaimer }}</p>
      </div>
    </div>
  </div>

  <div v-if="filteredLifeSuggestions.length" class="section-block">
    <h3 class="section-title">
      生活领域建议
      <span class="section-count">{{ filteredLifeSuggestions.length }}</span>
    </h3>
    <div class="suggest-list">
      <div v-for="(suggestion, index) in filteredLifeSuggestions" :key="index" class="suggest-item">
        <div class="suggest-head">
          <span v-if="suggestion.priority" :class="['suggest-priority', `priority-${suggestion.priority}`]">P{{ suggestion.priority }}</span>
          <span class="suggest-domain">{{ suggestion.category_label || suggestion.category }}</span>
          <span v-if="suggestion.cost_level" class="suggest-cost">{{ suggestion.cost_level }}</span>
        </div>
        <div class="suggest-name">{{ suggestion.name }}</div>
        <p v-if="suggestion.short_desc" class="suggest-text">{{ suggestion.short_desc }}</p>
        <div v-if="suggestion.actions?.length" class="suggest-actions">
          <div v-for="(action, actionIndex) in suggestion.actions" :key="actionIndex" class="suggest-step">{{ actionIndex + 1 }}. {{ action }}</div>
        </div>
        <div v-if="suggestion.evidence" class="suggest-evidence">依据：{{ suggestion.evidence }}</div>
        <div v-if="suggestion.notes" class="suggest-notes">备注：{{ suggestion.notes }}</div>
        <div v-if="suggestion.valid_scope" class="suggest-scope">适用：{{ suggestion.valid_scope }}</div>
        <p v-if="suggestion.disclaimer" class="suggest-disclaimer">⚠ {{ suggestion.disclaimer }}</p>
      </div>
    </div>
  </div>

  <p v-if="!remedies.length && !lifeSuggestions.length" class="muted">暂无建议数据</p>
</template>

<style scoped>
.section-block { margin-bottom: var(--sp-6); }
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
.remedies-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.remedy-item {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.remedy-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); }
.remedy-priority { font-size: var(--fs-xs); padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.remedy-priority.priority-1 { background: #dc2626; color: #fff; }
.remedy-priority.priority-2 { background: #f59e0b; color: #fff; }
.remedy-priority.priority-3 { background: #3b82f6; color: #fff; }
.remedy-priority.priority-4, .remedy-priority.priority-5 { background: #6b7280; color: #fff; }
.remedy-cat {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: var(--accent);
  color: #fff;
  border-radius: 10px;
  font-weight: 600;
  flex-shrink: 0;
}
.remedy-name { font-weight: 600; color: var(--text); }
.remedy-scope { font-size: var(--fs-xs); color: var(--text-3); margin-left: auto; }
.remedy-actions { display: flex; flex-direction: column; gap: 2px; padding-left: var(--sp-3); }
.remedy-step { font-size: var(--fs-sm); color: var(--text-2); }
.remedy-reason { font-size: var(--fs-sm); color: var(--text-3); font-style: italic; }
.remedy-disclaimer {
  font-size: var(--fs-xs);
  color: #b45309;
  background: #fef3c7;
  padding: var(--sp-2);
  border-radius: var(--radius-sm);
  margin: 0;
}
.suggest-overview {
  padding: var(--sp-4);
  margin-bottom: var(--sp-4);
}
.sov-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}
.sov-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}
.sov-num { font-size: var(--fs-xl); font-weight: 700; color: var(--text); }
.sov-label { font-size: var(--fs-xs); color: var(--text-2); }
.sov-remedy .sov-num { color: #92400e; }
.sov-p1 .sov-num { color: #991b1b; }
.sov-filter { display: flex; flex-wrap: wrap; gap: 6px; }
.sov-cat-btn {
  font-size: var(--fs-xs);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border-md);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.sov-cat-btn.active,
.sov-cat-btn:hover {
  border-color: var(--accent);
  background: rgba(217,119,6,.10);
  color: #78350f;
}
.suggest-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.suggest-item {
  padding: var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.suggest-head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--sp-2); margin-bottom: var(--sp-1); }
.suggest-priority { font-size: var(--fs-xs); padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.suggest-priority.priority-1 { background: #dc2626; color: #fff; }
.suggest-priority.priority-2 { background: #f59e0b; color: #fff; }
.suggest-priority.priority-3 { background: #3b82f6; color: #fff; }
.suggest-priority.priority-4, .suggest-priority.priority-5 { background: #6b7280; color: #fff; }
.suggest-domain {
  display: inline-block;
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: 10px;
  color: var(--text-2);
}
.suggest-cost { font-size: var(--fs-xs); padding: 2px 8px; background: #dbeafe; color: #1d4ed8; border-radius: 10px; }
.suggest-name { font-weight: 600; color: var(--text); font-size: var(--fs-md); }
.suggest-text { font-size: var(--fs-md); color: var(--text-2); line-height: 1.7; margin: 0; }
.suggest-actions { display: flex; flex-direction: column; gap: 2px; padding-left: var(--sp-3); }
.suggest-step { font-size: var(--fs-sm); color: var(--text-2); }
.suggest-evidence { font-size: var(--fs-sm); color: var(--text-3); font-style: italic; }
.suggest-notes { font-size: var(--fs-sm); color: var(--text-3); }
.suggest-scope { font-size: var(--fs-xs); color: var(--text-3); }
.suggest-disclaimer {
  font-size: var(--fs-xs);
  color: #b45309;
  background: #fef3c7;
  padding: var(--sp-2);
  border-radius: var(--radius-sm);
  margin: 0;
}
.muted { color: var(--text-3); font-size: var(--fs-sm); }
</style>
