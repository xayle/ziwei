<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type { ZiweiChartTheme, ZiweiFontSizeLevel } from '@/composables/useZiweiViewPreferences'

type ChartMode = 'feixing' | 'sanhe' | 'sihua'

type StarDisplayOptions = {
  showMainStars: boolean
  showAuxStars: boolean
  showTransforms: boolean
  showBrightness: boolean
  showChangsheng: boolean
  showBoshi: boolean
  showJiangSui: boolean
}

type OverlayDisplayOptions = {
  showDaxian: boolean
  showLiunian: boolean
  showLiuyue: boolean
  showXiaoxian: boolean
}

type LiuyueOption = {
  month: number
  month_name: string
  month_gz: string
}

const props = defineProps({
  chartMode: {
    type: String as PropType<ChartMode>,
    required: true,
  },
  showSihuaLines: {
    type: Boolean,
    required: true,
  },
  showLiunianOverlay: {
    type: Boolean,
    required: true,
  },
  selectedLiuyueMonth: {
    type: Number,
    required: true,
  },
  liuyueOptions: {
    type: Array as PropType<LiuyueOption[]>,
    required: true,
  },
  starDisplayOpts: {
    type: Object as PropType<StarDisplayOptions>,
    required: true,
  },
  overlayOpts: {
    type: Object as PropType<OverlayDisplayOptions>,
    required: true,
  },
  showThemePanel: {
    type: Boolean,
    required: true,
  },
  chartTheme: {
    type: String as PropType<ZiweiChartTheme>,
    required: true,
  },
  fontSizeLevel: {
    type: String as PropType<ZiweiFontSizeLevel>,
    required: true,
  },
  chartThemes: {
    type: Array as PropType<Array<{ id: ZiweiChartTheme; name: string; desc: string; colors: { primary: string; bg: string } }>>,
    required: true,
  },
  fontSizeOptions: {
    type: Array as PropType<Array<{ id: ZiweiFontSizeLevel; label: string; scale: number }>>,
    required: true,
  },
})

const emit = defineEmits<{
  'update:chartMode': [value: ChartMode]
  'update:showSihuaLines': [value: boolean]
  'update:showLiunianOverlay': [value: boolean]
  'update:selectedLiuyueMonth': [value: number]
  'update:starDisplayOpts': [value: StarDisplayOptions]
  'update:overlayOpts': [value: OverlayDisplayOptions]
  toggleThemePanel: []
  closeThemePanel: []
  setChartTheme: [value: ZiweiChartTheme]
  setFontSize: [value: ZiweiFontSizeLevel]
}>()

const currentChartMode = computed({
  get: () => props.chartMode,
  set: (value: ChartMode) => emit('update:chartMode', value),
})

const sihuaLinesVisible = computed({
  get: () => props.showSihuaLines,
  set: (value: boolean) => emit('update:showSihuaLines', value),
})

const liunianOverlayEnabled = computed({
  get: () => props.showLiunianOverlay,
  set: (value: boolean) => emit('update:showLiunianOverlay', value),
})

const currentLiuyueMonth = computed({
  get: () => props.selectedLiuyueMonth,
  set: (value: number) => emit('update:selectedLiuyueMonth', value),
})

function setStarOption<K extends keyof StarDisplayOptions>(key: K, value: StarDisplayOptions[K]) {
  emit('update:starDisplayOpts', {
    ...props.starDisplayOpts,
    [key]: value,
  })
}

function setOverlayOption<K extends keyof OverlayDisplayOptions>(key: K, value: OverlayDisplayOptions[K]) {
  emit('update:overlayOpts', {
    ...props.overlayOpts,
    [key]: value,
  })
}
</script>

<template>
  <div class="chart-mode-bar no-print">
    <div class="mode-btns">
      <button :class="['mode-btn', { active: currentChartMode === 'feixing' }]" @click="currentChartMode = 'feixing'">飞星</button>
      <button :class="['mode-btn', { active: currentChartMode === 'sanhe' }]" @click="currentChartMode = 'sanhe'">三合</button>
      <button :class="['mode-btn', { active: currentChartMode === 'sihua' }]" @click="currentChartMode = 'sihua'">四化</button>
    </div>

    <label v-if="currentChartMode === 'sihua'" class="sihua-line-toggle">
      <input v-model="sihuaLinesVisible" type="checkbox" />
      显示飞星连线
    </label>

    <label class="liunian-overlay-toggle">
      <input v-model="liunianOverlayEnabled" type="checkbox" />
      叠加流年
    </label>

    <div v-if="props.liuyueOptions.length" class="liuyue-selector">
      <label>流月：</label>
      <select v-model.number="currentLiuyueMonth" class="liuyue-select">
        <option :value="0">不显示</option>
        <option v-for="month in props.liuyueOptions" :key="month.month" :value="month.month">
          {{ month.month_name }} ({{ month.month_gz }})
        </option>
      </select>
    </div>

    <div class="star-display-opts">
      <label><input :checked="props.starDisplayOpts.showMainStars" type="checkbox" @change="setStarOption('showMainStars', ($event.target as HTMLInputElement).checked)" />主星</label>
      <label><input :checked="props.starDisplayOpts.showAuxStars" type="checkbox" @change="setStarOption('showAuxStars', ($event.target as HTMLInputElement).checked)" />辅星</label>
      <label><input :checked="props.starDisplayOpts.showTransforms" type="checkbox" @change="setStarOption('showTransforms', ($event.target as HTMLInputElement).checked)" />四化</label>
      <label><input :checked="props.starDisplayOpts.showBrightness" type="checkbox" @change="setStarOption('showBrightness', ($event.target as HTMLInputElement).checked)" />亮度</label>
      <label><input :checked="props.starDisplayOpts.showChangsheng" type="checkbox" @change="setStarOption('showChangsheng', ($event.target as HTMLInputElement).checked)" />长生</label>
      <label><input :checked="props.starDisplayOpts.showBoshi" type="checkbox" @change="setStarOption('showBoshi', ($event.target as HTMLInputElement).checked)" />博士</label>
      <label><input :checked="props.starDisplayOpts.showJiangSui" type="checkbox" @change="setStarOption('showJiangSui', ($event.target as HTMLInputElement).checked)" />将岁</label>
    </div>

    <div class="overlay-display-opts">
      <span class="overlay-label">叠加：</span>
      <label><input :checked="props.overlayOpts.showDaxian" type="checkbox" @change="setOverlayOption('showDaxian', ($event.target as HTMLInputElement).checked)" />大限</label>
      <label><input :checked="props.overlayOpts.showLiunian" type="checkbox" @change="setOverlayOption('showLiunian', ($event.target as HTMLInputElement).checked)" />流年</label>
      <label><input :checked="props.overlayOpts.showLiuyue" type="checkbox" @change="setOverlayOption('showLiuyue', ($event.target as HTMLInputElement).checked)" />流月</label>
      <label><input :checked="props.overlayOpts.showXiaoxian" type="checkbox" @change="setOverlayOption('showXiaoxian', ($event.target as HTMLInputElement).checked)" />小限</label>
    </div>

    <div class="visual-settings">
      <button class="vs-btn" title="切换配色主题" @click="emit('toggleThemePanel')">
        🎨
      </button>
      <div class="font-size-btns">
        <button
          v-for="opt in props.fontSizeOptions"
          :key="opt.id"
          :class="['fs-btn', { active: props.fontSizeLevel === opt.id }]"
          :title="`字体${opt.label}`"
          @click="emit('setFontSize', opt.id)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
  </div>

  <div v-if="props.showThemePanel" class="theme-panel no-print">
    <div class="tp-header">
      <span>选择配色主题</span>
      <button class="tp-close" @click="emit('closeThemePanel')">✕</button>
    </div>
    <div class="tp-grid">
      <button
        v-for="theme in props.chartThemes"
        :key="theme.id"
        :class="['tp-item', { active: props.chartTheme === theme.id }]"
        @click="emit('setChartTheme', theme.id)"
      >
        <div class="tp-preview">
          <span class="tp-dot" :style="{ background: theme.colors.primary }"></span>
          <span class="tp-bg" :style="{ background: theme.colors.bg }"></span>
        </div>
        <div class="tp-name">{{ theme.name }}</div>
        <div class="tp-desc">{{ theme.desc }}</div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chart-mode-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
  padding: 8px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.mode-btns {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.mode-btn {
  padding: 8px 20px;
  border: none;
  background: var(--surface);
  color: var(--text-2);
  font-size: var(--fs-md);
  font-weight: 600;
  font-family: var(--font-cn);
  cursor: pointer;
  transition: all var(--dur-fast);
  border-right: 1px solid var(--border-md);
}

.mode-btn:last-child {
  border-right: none;
}

.mode-btn:hover {
  background: var(--surface-2);
  color: var(--text);
}

.mode-btn.active {
  background: var(--accent);
  color: #fff;
}

.sihua-line-toggle,
.liunian-overlay-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
  color: var(--text-2);
  cursor: pointer;
}

.sihua-line-toggle input,
.liunian-overlay-toggle input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.liuyue-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
  color: var(--text-2);
}

.liuyue-select {
  font-size: var(--fs-sm);
  padding: 2px 6px;
  border: 1px solid #d6c9b3;
  border-radius: 4px;
  background: #fff;
  color: var(--text-1);
}

.liuyue-select option {
  color: #1f2937;
  background: #fff;
}

.liuyue-select option:checked,
.liuyue-select option:hover {
  color: #111827;
  background: #e5e7eb;
}

.star-display-opts {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 12px;
  border-left: 1px solid var(--border);
  margin-left: auto;
}

.star-display-opts label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-sm);
  color: var(--text-2);
  cursor: pointer;
  user-select: none;
}

.star-display-opts input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
  cursor: pointer;
}

.star-display-opts label:hover {
  color: var(--text);
}

.overlay-display-opts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-sm);
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(13,148,136,.05);
  border-radius: 6px;
  border: 1px solid rgba(13,148,136,.15);
}

.overlay-display-opts .overlay-label {
  font-weight: 600;
  color: #0d9488;
}

.overlay-display-opts label {
  display: flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.15s;
  color: var(--text-2);
}

.overlay-display-opts label:hover {
  background: rgba(13,148,136,.1);
  color: var(--text);
}

.overlay-display-opts input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #0d9488;
  cursor: pointer;
}

.visual-settings {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.vs-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.vs-btn:hover {
  background: var(--primary-bg);
  border-color: var(--primary);
}

.font-size-btns {
  display: flex;
  gap: 2px;
}

.fs-btn {
  padding: 4px 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text-2);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.fs-btn:first-child {
  border-radius: 4px 0 0 4px;
}

.fs-btn:last-child {
  border-radius: 0 4px 4px 0;
}

.fs-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.fs-btn:hover:not(.active) {
  background: var(--primary-bg);
}

.theme-panel {
  position: absolute;
  top: 60px;
  right: 12px;
  z-index: 100;
  width: 280px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  overflow: hidden;
}

.tp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 500;
}

.tp-close {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
}

.tp-close:hover {
  color: var(--danger);
}

.tp-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 12px;
}

.tp-item {
  padding: 10px;
  border: 2px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.tp-item:hover {
  border-color: var(--primary);
}

.tp-item.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.tp-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
}

.tp-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.tp-bg {
  width: 24px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.1);
}

.tp-name {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text);
}

.tp-desc {
  font-size: 10px;
  color: var(--text-2);
}
</style>