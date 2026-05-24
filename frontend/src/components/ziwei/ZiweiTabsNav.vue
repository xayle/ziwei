<script setup lang="ts">
import { computed } from 'vue'

type ZiweiTabKey = 'chart' | 'summary' | 'palaces' | 'dayun' | 'liunian' | 'liuyue' | 'patterns' | 'flying' | 'forecast' | 'suggest'

const props = defineProps<{
  activeTab: string
  hasLiunian: boolean
  hasLiuyue: boolean
  patternsCount: number
  hasFlying: boolean
  hasForecast: boolean
}>()

const emit = defineEmits<{
  'update:activeTab': [tab: ZiweiTabKey]
}>()

const baseTabs: Array<{ key: ZiweiTabKey; label: string }> = [
  { key: 'chart', label: '命盘宫位' },
  { key: 'summary', label: '摘要' },
  { key: 'palaces', label: '逐宫解读' },
  { key: 'dayun', label: '大运' },
  { key: 'patterns', label: '格局' },
  { key: 'suggest', label: '建议' },
]

const optionalTabs = computed(() => [
  { key: 'liunian' as const, label: '流年', visible: props.hasLiunian },
  { key: 'liuyue' as const, label: '流月', visible: props.hasLiuyue },
  { key: 'flying' as const, label: '飞星', visible: props.hasFlying },
  { key: 'forecast' as const, label: '运势', visible: props.hasForecast },
])

const timeTabs = computed(() => optionalTabs.value.slice(0, 2).filter((item) => item.visible))
const analysisTabs = computed(() => optionalTabs.value.slice(2).filter((item) => item.visible))

function setActiveTab(tab: ZiweiTabKey) {
  emit('update:activeTab', tab)
}
</script>

<template>
  <div class="tabs">
    <button
      v-for="tab in baseTabs.slice(0, 4)"
      :key="tab.key"
      :class="['tab-btn', { active: props.activeTab === tab.key }]"
      @click="setActiveTab(tab.key)"
    >
      {{ tab.label }}
    </button>
    <button
      v-for="tab in timeTabs"
      :key="tab.key"
      :class="['tab-btn', { active: props.activeTab === tab.key }]"
      @click="setActiveTab(tab.key)"
    >
      {{ tab.label }}
    </button>
    <button :class="['tab-btn', { active: props.activeTab === 'patterns' }]" @click="setActiveTab('patterns')">
      格局
      <span v-if="props.patternsCount" class="badge">{{ props.patternsCount }}</span>
    </button>
    <button
      v-for="tab in analysisTabs"
      :key="tab.key"
      :class="['tab-btn', { active: props.activeTab === tab.key }]"
      @click="setActiveTab(tab.key)"
    >
      {{ tab.label }}
    </button>
    <button :class="['tab-btn', { active: props.activeTab === 'suggest' }]" @click="setActiveTab('suggest')">
      建议
    </button>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
  border-bottom: 2px solid var(--border);
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: var(--fs-md);
  color: var(--text-2);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color var(--dur-fast), border-color var(--dur-fast);
  display: flex;
  align-items: center;
  gap: 4px;
}

.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

.tab-btn:hover {
  color: var(--text);
}

.badge {
  background: var(--accent);
  color: #fff;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
}
</style>