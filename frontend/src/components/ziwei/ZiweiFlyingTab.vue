<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FlyingChartResponse } from '@/api/ziwei'
import {
  FLYING_COLUMN_TIPS,
  FLYING_HOW_TO_READ,
  SIHUA_ORDER,
  buildPalacePlainReading,
} from './flyingStarGuide'

const props = defineProps<{
  flying: FlyingChartResponse | null | undefined
}>()

const guideOpen = ref(true)
const expandedPalace = ref<string | null>(null)

const palaceRows = computed(() => props.flying?.palaces ?? [])

const receivedEntries = computed(() => {
  const raw = props.flying?.received ?? {}
  return Object.entries(raw).filter(([, items]) => (items?.length ?? 0) > 0)
})

const chongedEntries = computed(() => {
  const raw = props.flying?.chonged ?? {}
  return Object.entries(raw).filter(([, items]) => (items?.length ?? 0) > 0)
})

const selfTransforms = computed(() => props.flying?.self_transforms ?? [])

function tip(key: string): string {
  return FLYING_COLUMN_TIPS[key] || ''
}

function togglePalace(name: string) {
  expandedPalace.value = expandedPalace.value === name ? null : name
}

function plainFor(row: { palace_name: string; stem_name: string; flying_out: Record<string, string>; opposition_palace: string; self_transforms: string[] }) {
  return buildPalacePlainReading(row)
}
</script>

<template>
  <div class="ziwei-flying-tab" data-testid="ziwei-flying-tab">
    <p class="ziwei-flying-tab__lead">
      飞星以各宫宫干带出<strong>化禄 / 化权 / 化科 / 化忌</strong>，观落宫与自化、冲宫。
      点表头「?」看释义；点某一宫行可展开白话。
    </p>

    <details
      class="ziwei-flying-tab__guide"
      data-testid="ziwei-flying-guide"
      :open="guideOpen"
      @toggle="guideOpen = ($event.target as HTMLDetailsElement).open"
    >
      <summary>怎么读飞星盘</summary>
      <ol>
        <li v-for="(line, idx) in FLYING_HOW_TO_READ" :key="idx">{{ line }}</li>
      </ol>
    </details>

    <p v-if="!flying" class="ziwei-flying-tab__empty">当前模板未返回飞星盘（请使用标准模板）。</p>

    <template v-else>
      <div class="ziwei-flying-tab__table-wrap">
        <table class="ziwei-flying-tab__table">
          <thead>
            <tr>
              <th>
                宫位
                <abbr class="field-tip" :title="tip('宫位')">?</abbr>
              </th>
              <th>
                宫干
                <abbr class="field-tip" :title="tip('宫干')">?</abbr>
              </th>
              <th v-for="key in SIHUA_ORDER" :key="key">
                {{ key }}
                <abbr class="field-tip" :title="tip(key)">?</abbr>
              </th>
              <th>
                对冲
                <abbr class="field-tip" :title="tip('对冲')">?</abbr>
              </th>
              <th>
                自化
                <abbr class="field-tip" :title="tip('自化')">?</abbr>
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="row in palaceRows" :key="row.palace_name">
              <tr
                class="ziwei-flying-tab__row"
                :class="{ 'is-expanded': expandedPalace === row.palace_name }"
                :data-testid="`flying-row-${row.palace_name}`"
                tabindex="0"
                role="button"
                :aria-expanded="expandedPalace === row.palace_name"
                @click="togglePalace(row.palace_name)"
                @keydown.enter.prevent="togglePalace(row.palace_name)"
                @keydown.space.prevent="togglePalace(row.palace_name)"
              >
                <td>{{ row.palace_name }}</td>
                <td>{{ row.stem_name }}</td>
                <td v-for="key in SIHUA_ORDER" :key="`${row.palace_name}-${key}`">
                  {{ row.flying_out?.[key] || '—' }}
                </td>
                <td>{{ row.opposition_palace || '—' }}</td>
                <td>{{ row.self_transforms?.join('；') || '—' }}</td>
              </tr>
              <tr
                v-if="expandedPalace === row.palace_name"
                class="ziwei-flying-tab__plain-row"
                :data-testid="`flying-plain-${row.palace_name}`"
              >
                <td :colspan="2 + SIHUA_ORDER.length + 2">
                  <p class="ziwei-flying-tab__plain">{{ plainFor(row) }}</p>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-if="receivedEntries.length" class="ziwei-flying-tab__block">
        <h3>入宫汇总</h3>
        <ul>
          <li v-for="[palace, items] in receivedEntries" :key="palace">
            <strong>{{ palace }}</strong>：{{ items.join('；') }}
          </li>
        </ul>
      </div>

      <div v-if="chongedEntries.length" class="ziwei-flying-tab__block">
        <h3>飞化冲宫</h3>
        <ul>
          <li v-for="[palace, items] in chongedEntries" :key="palace">
            <strong>{{ palace }}</strong>：{{ items.join('；') }}
          </li>
        </ul>
      </div>

      <div v-if="selfTransforms.length" class="ziwei-flying-tab__block">
        <h3>全局自化</h3>
        <ul>
          <li v-for="(item, idx) in selfTransforms" :key="idx">{{ item }}</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ziwei-flying-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ziwei-flying-tab__lead {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #57534e;
}

.ziwei-flying-tab__guide {
  margin: 0;
  padding: 8px 12px;
  border: 1px solid #e7e5e4;
  border-radius: 8px;
  background: #fafaf9;
  font-size: 13px;
  color: #44403c;
}

.ziwei-flying-tab__guide summary {
  cursor: pointer;
  font-weight: 600;
  color: #78350f;
}

.ziwei-flying-tab__guide ol {
  margin: 8px 0 0;
  padding-left: 18px;
  line-height: 1.55;
  color: #57534e;
}

.ziwei-flying-tab__empty {
  margin: 0;
  padding: 12px;
  border-radius: 10px;
  background: #fafaf9;
  border: 1px dashed #d6d3d1;
  color: #78716c;
  font-size: 13px;
}

.ziwei-flying-tab__table-wrap {
  overflow-x: auto;
}

.ziwei-flying-tab__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.ziwei-flying-tab__table th,
.ziwei-flying-tab__table td {
  border: 1px solid #e7e5e4;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}

.ziwei-flying-tab__table th {
  background: #fffbeb;
  color: #78350f;
  font-weight: 700;
  white-space: nowrap;
}

.field-tip {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 600;
  color: #a8a29e;
  text-decoration: none;
  cursor: help;
}

.ziwei-flying-tab__row {
  cursor: pointer;
}

.ziwei-flying-tab__row:hover,
.ziwei-flying-tab__row.is-expanded {
  background: #fffbeb;
}

.ziwei-flying-tab__plain-row td {
  background: #fafaf9;
}

.ziwei-flying-tab__plain {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #44403c;
}

.ziwei-flying-tab__block h3 {
  margin: 0 0 6px;
  font-size: 13px;
  color: #44403c;
}

.ziwei-flying-tab__block ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.55;
  color: #57534e;
}
</style>
