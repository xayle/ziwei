<script setup lang="ts">
import type { PropType } from 'vue'
import ZiweiHistoryPanel from './ZiweiHistoryPanel.vue'
import type { ZiweiChartHistoryItem } from '@/composables/useZiweiViewPreferences'

type HotkeyItem = {
  key: string
  desc: string
}

type BrightnessLegendItem = {
  level: string
  desc: string
  color: string
}

const props = defineProps({
  showHotkeyPanel: {
    type: Boolean,
    required: true,
  },
  hotkeyList: {
    type: Array as PropType<HotkeyItem[]>,
    required: true,
  },
  showBrightnessLegend: {
    type: Boolean,
    required: true,
  },
  brightnessLegend: {
    type: Array as PropType<BrightnessLegendItem[]>,
    required: true,
  },
  showHistoryPanel: {
    type: Boolean,
    required: true,
  },
  historyItems: {
    type: Array as PropType<ZiweiChartHistoryItem[]>,
    required: true,
  },
  formatHistoryTime: {
    type: Function as PropType<(timestamp: number) => string>,
    required: true,
  },
})

const emit = defineEmits<{
  closeHotkeyPanel: []
  closeBrightnessLegend: []
  clearHistory: []
  closeHistoryPanel: []
  restoreHistory: [item: ZiweiChartHistoryItem]
}>()
</script>

<template>
  <transition name="fade">
    <div v-if="props.showHotkeyPanel" class="hotkey-panel card no-print">
      <div class="hp-header">
        <span class="hp-title">⌨ 键盘快捷键</span>
        <button class="hp-close" @click="emit('closeHotkeyPanel')">✕</button>
      </div>
      <div class="hp-list">
        <div v-for="hk in props.hotkeyList" :key="hk.key" class="hp-item">
          <kbd class="hp-key">{{ hk.key }}</kbd>
          <span class="hp-desc">{{ hk.desc }}</span>
        </div>
        <div class="hp-item">
          <kbd class="hp-key">S</kbd>
          <span class="hp-desc">打开星曜搜索</span>
        </div>
      </div>
    </div>
  </transition>

  <transition name="fade">
    <div v-if="props.showBrightnessLegend" class="brightness-legend card no-print">
      <div class="bl-header">
        <span class="bl-title">💡 星曜亮度图例</span>
        <button class="bl-close" @click="emit('closeBrightnessLegend')">✕</button>
      </div>
      <div class="bl-list">
        <div v-for="item in props.brightnessLegend" :key="item.level" class="bl-item">
          <span class="bl-level" :style="{ background: item.color }">{{ item.level }}</span>
          <span class="bl-desc">{{ item.desc }}</span>
        </div>
      </div>
      <div class="bl-note">
        <small>亮度越高，星曜吉性越易发挥；陷落时则力量受损</small>
      </div>
    </div>
  </transition>

  <ZiweiHistoryPanel
    :visible="props.showHistoryPanel"
    :items="props.historyItems"
    :format-time="props.formatHistoryTime"
    @clear="emit('clearHistory')"
    @close="emit('closeHistoryPanel')"
    @restore="emit('restoreHistory', $event)"
  />
</template>

<style scoped>
.hotkey-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 280px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.hp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}

.hp-title {
  font-size: var(--fs-md);
  font-weight: 700;
}

.hp-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}

.hp-close:hover { color: var(--text); }

.hp-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.hp-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.hp-key {
  display: inline-block;
  min-width: 50px;
  padding: 4px 8px;
  background: var(--surface-2);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: var(--fs-sm);
  text-align: center;
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.hp-desc {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.brightness-legend {
  position: fixed;
  top: 80px;
  right: 320px;
  width: 220px;
  z-index: 1000;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.bl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}

.bl-title {
  font-size: var(--fs-md);
  font-weight: 700;
}

.bl-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}

.bl-close:hover { color: var(--text); }

.bl-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.bl-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.bl-level {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 24px;
  border-radius: 6px;
  color: #fff;
  font-weight: 700;
  font-size: var(--fs-xs);
}

.bl-desc {
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.bl-note {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px dashed var(--border);
  color: var(--text-3);
  line-height: 1.5;
}
</style>
