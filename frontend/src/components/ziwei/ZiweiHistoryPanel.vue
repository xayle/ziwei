<script setup lang="ts">
import type { PropType } from 'vue'
import type { ZiweiChartHistoryItem } from '@/composables/useZiweiViewPreferences'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  items: {
    type: Array as PropType<ZiweiChartHistoryItem[]>,
    required: true,
  },
  formatTime: {
    type: Function as PropType<(timestamp: number) => string>,
    required: true,
  },
})

const emit = defineEmits<{
  close: []
  clear: []
  restore: [item: ZiweiChartHistoryItem]
}>()
</script>

<template>
  <transition name="fade">
    <div v-if="props.visible" class="history-panel card no-print">
      <div class="hist-header">
        <span class="hist-title">📋 排盘历史</span>
        <div class="hist-actions">
          <button v-if="props.items.length" class="hist-clear" title="清空历史" @click="emit('clear')">🗑</button>
          <button class="hist-close" @click="emit('close')">✕</button>
        </div>
      </div>
      <div v-if="props.items.length === 0" class="hist-empty">
        暂无历史记录
      </div>
      <div v-else class="hist-list">
        <div v-for="item in props.items" :key="item.id" class="hist-item" @click="emit('restore', item)">
          <div class="hist-main">
            <span class="hist-birth">{{ item.birthSolar }}</span>
            <span class="hist-gender">{{ item.gender }}</span>
          </div>
          <div class="hist-sub">
            <span class="hist-palace">命宫 {{ item.lifePalaceGz }}</span>
            <span class="hist-ju">{{ item.wuxingJuName }}</span>
          </div>
          <div class="hist-time">{{ props.formatTime(item.timestamp) }}</div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.history-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 300px;
  max-height: 400px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.hist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-2);
}

.hist-title {
  font-size: var(--fs-md);
  font-weight: 700;
}

.hist-actions {
  display: flex;
  gap: var(--sp-2);
}

.hist-clear,
.hist-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}

.hist-clear:hover {
  color: #dc2626;
}

.hist-close:hover {
  color: var(--text);
}

.hist-empty {
  text-align: center;
  padding: var(--sp-5);
  color: var(--text-3);
}

.hist-list {
  flex: 1;
  overflow-y: auto;
}

.hist-item {
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.hist-item:hover {
  background: var(--surface-2);
  border-left-color: var(--accent);
}

.hist-main {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.hist-birth {
  font-weight: 600;
  font-size: var(--fs-sm);
}

.hist-gender {
  font-size: var(--fs-xs);
  padding: 1px 5px;
  background: var(--surface-2);
  border-radius: 4px;
  color: var(--text-3);
}

.hist-sub {
  display: flex;
  gap: var(--sp-2);
  margin-top: 2px;
}

.hist-palace,
.hist-ju {
  font-size: var(--fs-xs);
  color: var(--text-2);
}

.hist-time {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin-top: 2px;
}
</style>