<script setup lang="ts">
import { computed } from 'vue'
import type { FlyingChartResponse } from '@/api/ziwei'

const props = defineProps<{
  flying: FlyingChartResponse | null | undefined
}>()

const SIHUA_ORDER = ['化禄', '化权', '化科', '化忌'] as const

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
</script>

<template>
  <div class="ziwei-flying-tab" data-testid="ziwei-flying-tab">
    <p class="ziwei-flying-tab__lead">
      飞星以各宫宫干带出<strong>化禄 / 化权 / 化科 / 化忌</strong>，观落宫与自化、冲宫。
    </p>

    <p v-if="!flying" class="ziwei-flying-tab__empty">当前模板未返回飞星盘（请使用标准模板）。</p>

    <template v-else>
      <div class="ziwei-flying-tab__table-wrap">
        <table class="ziwei-flying-tab__table">
          <thead>
            <tr>
              <th>宫位</th>
              <th>宫干</th>
              <th v-for="key in SIHUA_ORDER" :key="key">{{ key }}</th>
              <th>对冲</th>
              <th>自化</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in palaceRows" :key="row.palace_name">
              <td>{{ row.palace_name }}</td>
              <td>{{ row.stem_name }}</td>
              <td v-for="key in SIHUA_ORDER" :key="`${row.palace_name}-${key}`">
                {{ row.flying_out?.[key] || '—' }}
              </td>
              <td>{{ row.opposition_palace || '—' }}</td>
              <td>{{ row.self_transforms?.join('；') || '—' }}</td>
            </tr>
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
