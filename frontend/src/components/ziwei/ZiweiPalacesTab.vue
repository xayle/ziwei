<script setup lang="ts">
import type { PalaceResponse } from '@/api/ziwei'

interface PalacesStats {
  total: number
  withMain: number
  withConclusion: number
}

interface PalaceGroupItem {
  key: string
  title: string
  items: PalaceResponse[]
}

const props = defineProps<{
  palaces: PalaceResponse[]
  palacesStats: PalacesStats
  palaceFilter: string
  groupedFilteredPalaces: PalaceGroupItem[]
  palaceGroupExpanded: Record<string, boolean>
  filteredPalacesCount: number
}>()

const emit = defineEmits<{
  (e: 'update:palaceFilter', value: string): void
  (e: 'toggle-group', groupKey: string): void
}>()

function updateFilter(value: string) {
  emit('update:palaceFilter', value)
}

function clearFilter() {
  emit('update:palaceFilter', '')
}

function toggleQuickFilter(name: string) {
  emit('update:palaceFilter', props.palaceFilter === name ? '' : name)
}
</script>

<template>
  <div class="palaces-toolbar">
    <div class="palaces-stats">
      <span class="ps-item">共 <b>{{ palacesStats.total }}</b> 宫</span>
      <span class="ps-item">有主星 <b>{{ palacesStats.withMain }}</b></span>
      <span class="ps-item">有解读 <b>{{ palacesStats.withConclusion }}</b></span>
    </div>
    <div class="palaces-filter">
      <input
        :value="palaceFilter"
        type="text"
        placeholder="搜索宫位/星曜..."
        class="palace-search-input"
        @input="updateFilter(($event.target as HTMLInputElement).value)"
      />
      <button v-if="palaceFilter" class="palace-clear-btn" @click="clearFilter">✕</button>
    </div>
  </div>

  <div class="palaces-quick-nav">
    <button
      v-for="palace in palaces"
      :key="palace.index"
      :class="['pqn-btn', { 'pqn-active': palaceFilter === palace.name }]"
      @click="toggleQuickFilter(palace.name)"
    >
      {{ palace.name.replace('宫', '') }}
    </button>
  </div>

  <div class="palaces-interpretations-grouped">
    <div v-for="group in groupedFilteredPalaces" :key="group.key" class="pig-group card">
      <button class="pig-head" @click="emit('toggle-group', group.key)">
        <span class="pig-title">{{ group.title }}</span>
        <span class="pig-count">{{ group.items.length }} 宫</span>
        <span class="pig-toggle">{{ palaceGroupExpanded[group.key] ? '收起' : '展开' }}</span>
      </button>

      <div v-if="palaceGroupExpanded[group.key]" class="palaces-interpretations">
        <div v-for="palace in group.items" :key="palace.index" class="palace-interp-card card">
          <div class="pi-header">
            <span class="pi-name">{{ palace.name }}</span>
            <span class="pi-gz">{{ palace.stem }}{{ palace.branch }}</span>
            <span v-if="palace.name.includes('命')" class="pi-tag life">命宫</span>
            <span v-if="palace.name.includes('身')" class="pi-tag body">身宫</span>
          </div>

          <div v-if="palace.main_stars.length" class="pi-stars">
            <span v-for="star in palace.main_stars" :key="star.name" class="pi-star">
              <b>{{ star.name }}</b>
              <span class="pi-br">{{ star.brightness }}</span>
              <span v-if="star.transforms.length" class="pi-tf">{{ star.transforms.join(' ') }}</span>
            </span>
          </div>

          <div v-if="palace.analysis_tags?.length" class="pi-tags">
            <span v-for="tag in palace.analysis_tags" :key="tag" class="pi-tag-item">{{ tag }}</span>
          </div>

          <p v-if="palace.conclusion" class="pi-conclusion">
            <strong>结论：</strong>{{ palace.conclusion }}
          </p>
          <p v-if="palace.explanation" class="pi-explanation">
            <strong>详解：</strong>{{ palace.explanation }}
          </p>
          <p v-if="palace.suggestion" class="pi-suggestion">
            <strong>建议：</strong>{{ palace.suggestion }}
          </p>
          <p v-else-if="palace.analysis" class="pi-analysis">{{ palace.analysis }}</p>
        </div>
      </div>
    </div>

    <p v-if="filteredPalacesCount === 0" class="muted">没有匹配的宫位</p>
  </div>
</template>

<style scoped>
.palaces-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--sp-3);
}

.palaces-stats {
  display: flex;
  gap: var(--sp-4);
}

.palaces-stats .ps-item {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.palaces-stats .ps-item b {
  font-weight: 700;
  color: var(--accent);
}

.palaces-filter {
  display: flex;
  align-items: center;
  gap: 4px;
  position: relative;
}

.palace-search-input {
  padding: 6px 28px 6px 10px;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  width: 160px;
  background: #fff;
}

.palace-search-input:focus {
  outline: none;
  border-color: var(--accent);
}

.palace-clear-btn {
  position: absolute;
  right: 6px;
  width: 18px;
  height: 18px;
  border: none;
  background: var(--surface-2);
  border-radius: 50%;
  font-size: 10px;
  color: var(--text-3);
  cursor: pointer;
}

.palace-clear-btn:hover {
  background: var(--border);
  color: var(--text);
}

.palaces-quick-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-4);
}

.pqn-btn {
  padding: 4px 8px;
  font-size: var(--fs-xs);
  font-family: var(--font-cn);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}

.pqn-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.pqn-btn.pqn-active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.palaces-interpretations {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--sp-4);
}

.palaces-interpretations-grouped {
  display: grid;
  gap: var(--sp-4);
}

.pig-group {
  padding: 0;
  overflow: hidden;
}

.pig-head {
  width: 100%;
  border: 0;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
}

.pig-title {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
  flex: 1;
}

.pig-count {
  font-size: var(--fs-xs);
  color: var(--text-3);
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
}

.pig-toggle {
  font-size: var(--fs-xs);
  color: var(--accent);
}

.pig-group .palaces-interpretations {
  padding: var(--sp-3);
}

.palace-interp-card {
  padding: var(--sp-4);
  border-left: 3px solid var(--border-md);
}

.palace-interp-card:has(.pi-tag.life) {
  border-left-color: #dc2626;
}

.palace-interp-card:has(.pi-tag.body) {
  border-left-color: #2563eb;
}

.pi-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sp-3);
  flex-wrap: wrap;
}

.pi-name {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
  color: var(--text);
}

.pi-gz {
  font-size: var(--fs-sm);
  color: var(--text-3);
}

.pi-tag {
  font-size: var(--fs-xs);
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.pi-tag.life {
  background: rgba(220, 38, 38, .12);
  color: #dc2626;
}

.pi-tag.body {
  background: rgba(37, 99, 235, .12);
  color: #2563eb;
}

.pi-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--sp-3);
}

.pi-star {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}

.pi-star b {
  color: var(--text);
}

.pi-br {
  color: var(--text-2);
  font-size: var(--fs-xs);
}

.pi-tf {
  color: var(--accent);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.pi-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--sp-3);
}

.pi-tag-item {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: rgba(37, 99, 235, .08);
  color: #1d4ed8;
  border: 1px solid rgba(37, 99, 235, .2);
  border-radius: 10px;
}

.pi-conclusion {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}

.pi-conclusion strong {
  color: var(--accent);
}

.pi-explanation {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
  margin-bottom: var(--sp-2);
}

.pi-explanation strong {
  color: var(--text-2);
}

.pi-suggestion {
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  background: rgba(217, 119, 6, .08);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  line-height: 1.6;
}

.pi-suggestion strong {
  color: var(--accent);
}

.pi-analysis {
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.6;
}
</style>