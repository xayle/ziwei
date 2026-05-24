import { computed, nextTick, onMounted, ref, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'
import { readStorage, removeStorage, writeStorage } from '@/utils/browserStorage'

export interface ZiweiChartHistoryItem {
  id: string
  timestamp: number
  birthSolar: string
  gender: string
  lifePalaceGz: string
  wuxingJuName: string
  params: {
    year: number
    month: number
    day: number
    hour: number
    minute: number
    gender: string
    longitude?: number
  }
}

export type ZiweiChartTheme = 'classic' | 'modern' | 'elegant' | 'dark'
export type ZiweiFontSizeLevel = 'sm' | 'md' | 'lg' | 'xl'

const HISTORY_KEY = 'ziwei_chart_history'
const THEME_KEY = 'ziwei_chart_theme'
const FONT_SIZE_KEY = 'ziwei_font_size'
const MAX_HISTORY = 10

export const ZIWEI_CHART_THEMES: Array<{ id: ZiweiChartTheme; name: string; desc: string; colors: { primary: string; bg: string } }> = [
  { id: 'classic', name: '经典', desc: '传统紫色调', colors: { primary: '#7c3aed', bg: '#faf5ff' } },
  { id: 'modern', name: '现代', desc: '清新蓝色调', colors: { primary: '#3b82f6', bg: '#eff6ff' } },
  { id: 'elegant', name: '雅致', desc: '沉稳棕色调', colors: { primary: '#92400e', bg: '#fef3c7' } },
  { id: 'dark', name: '暗黑', desc: '深色护眼', colors: { primary: '#a78bfa', bg: '#1e1b4b' } },
]

export const ZIWEI_FONT_SIZE_OPTIONS: Array<{ id: ZiweiFontSizeLevel; label: string; scale: number }> = [
  { id: 'sm', label: '小', scale: 0.9 },
  { id: 'md', label: '中', scale: 1.0 },
  { id: 'lg', label: '大', scale: 1.1 },
  { id: 'xl', label: '特大', scale: 1.2 },
]

type UseZiweiViewPreferencesOptions = {
  result: Ref<ZiweiResponse | null>
  year: Ref<number>
  month: Ref<number>
  day: Ref<number>
  hour: Ref<number>
  minute: Ref<number>
  gender: Ref<'男' | '女'>
  longitude: Ref<number | undefined>
  setFormValues: (params: ZiweiChartHistoryItem['params']) => void
  triggerRecalculate: () => Promise<void> | void
}

function loadHistoryFromStorage(): ZiweiChartHistoryItem[] {
  try {
    const raw = readStorage(HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function applyTheme(theme: ZiweiChartTheme) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  const themeVars: Record<ZiweiChartTheme, Record<string, string>> = {
    classic: {
      '--theme-primary': '#7c3aed',
      '--theme-primary-bg': 'rgba(124, 58, 237, 0.1)',
      '--theme-bg': '#faf5ff',
      '--theme-card': '#ffffff',
      '--theme-text': '#1f2937',
      '--theme-text-2': '#6b7280',
      '--theme-border': '#e5e7eb',
    },
    modern: {
      '--theme-primary': '#3b82f6',
      '--theme-primary-bg': 'rgba(59, 130, 246, 0.1)',
      '--theme-bg': '#eff6ff',
      '--theme-card': '#ffffff',
      '--theme-text': '#1e3a5f',
      '--theme-text-2': '#64748b',
      '--theme-border': '#dbeafe',
    },
    elegant: {
      '--theme-primary': '#92400e',
      '--theme-primary-bg': 'rgba(146, 64, 14, 0.1)',
      '--theme-bg': '#fefbf3',
      '--theme-card': '#fffdf7',
      '--theme-text': '#451a03',
      '--theme-text-2': '#78716c',
      '--theme-border': '#fde68a',
    },
    dark: {
      '--theme-primary': '#a78bfa',
      '--theme-primary-bg': 'rgba(167, 139, 250, 0.15)',
      '--theme-bg': '#0f0d1a',
      '--theme-card': '#1e1b2e',
      '--theme-text': '#e2e8f0',
      '--theme-text-2': '#94a3b8',
      '--theme-border': '#334155',
    },
  }

  Object.entries(themeVars[theme]).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
}

function applyFontSize(level: ZiweiFontSizeLevel) {
  if (typeof document === 'undefined') return
  const option = ZIWEI_FONT_SIZE_OPTIONS.find((item) => item.id === level)
  if (!option) return
  document.documentElement.style.setProperty('--font-scale', String(option.scale))
}

export function useZiweiViewPreferences(options: UseZiweiViewPreferencesOptions) {
  const showHistoryPanel = ref(false)
  const showThemePanel = ref(false)
  const chartHistory = ref<ZiweiChartHistoryItem[]>(loadHistoryFromStorage())
  const chartTheme = ref<ZiweiChartTheme>((readStorage(THEME_KEY) as ZiweiChartTheme) || 'classic')
  const fontSizeLevel = ref<ZiweiFontSizeLevel>((readStorage(FONT_SIZE_KEY) as ZiweiFontSizeLevel) || 'md')

  const historyCount = computed(() => chartHistory.value.length)

  function refreshHistory() {
    chartHistory.value = loadHistoryFromStorage()
  }

  function saveToHistory() {
    if (!options.result.value) return
    const history = loadHistoryFromStorage()
    const newItem: ZiweiChartHistoryItem = {
      id: Date.now().toString(),
      timestamp: Date.now(),
      birthSolar: options.result.value.birth_solar,
      gender: options.result.value.gender,
      lifePalaceGz: options.result.value.life_palace_gz,
      wuxingJuName: options.result.value.wuxing_ju_name,
      params: {
        year: options.year.value,
        month: options.month.value,
        day: options.day.value,
        hour: options.hour.value,
        minute: options.minute.value,
        gender: options.gender.value,
        longitude: options.longitude.value,
      },
    }

    const existIdx = history.findIndex((item) =>
      item.params.year === newItem.params.year &&
      item.params.month === newItem.params.month &&
      item.params.day === newItem.params.day &&
      item.params.hour === newItem.params.hour &&
      item.params.gender === newItem.params.gender,
    )

    if (existIdx >= 0) history.splice(existIdx, 1)
    history.unshift(newItem)
    if (history.length > MAX_HISTORY) history.pop()

    writeStorage(HISTORY_KEY, JSON.stringify(history))
    chartHistory.value = history
  }

  async function restoreFromHistory(item: ZiweiChartHistoryItem) {
    options.setFormValues(item.params)
    showHistoryPanel.value = false
    await nextTick()
    await options.triggerRecalculate()
  }

  function clearHistory() {
    removeStorage(HISTORY_KEY)
    chartHistory.value = []
    showHistoryPanel.value = false
  }

  function formatHistoryTime(ts: number): string {
    const d = new Date(ts)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  function toggleHistoryPanel() {
    showHistoryPanel.value = !showHistoryPanel.value
    if (showHistoryPanel.value) refreshHistory()
  }

  function setChartTheme(theme: ZiweiChartTheme) {
    chartTheme.value = theme
    writeStorage(THEME_KEY, theme)
    applyTheme(theme)
    showThemePanel.value = false
  }

  function toggleThemePanel() {
    showThemePanel.value = !showThemePanel.value
  }

  function closeThemePanel() {
    showThemePanel.value = false
  }

  function setFontSize(level: ZiweiFontSizeLevel) {
    fontSizeLevel.value = level
    writeStorage(FONT_SIZE_KEY, level)
    applyFontSize(level)
  }

  onMounted(() => {
    applyTheme(chartTheme.value)
    applyFontSize(fontSizeLevel.value)
  })

  return {
    showHistoryPanel,
    showThemePanel,
    chartHistory,
    historyCount,
    chartTheme,
    fontSizeLevel,
    saveToHistory,
    restoreFromHistory,
    clearHistory,
    formatHistoryTime,
    toggleHistoryPanel,
    setChartTheme,
    toggleThemePanel,
    closeThemePanel,
    setFontSize,
    CHART_THEMES: ZIWEI_CHART_THEMES,
    FONT_SIZE_OPTIONS: ZIWEI_FONT_SIZE_OPTIONS,
  }
}