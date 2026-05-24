import { computed, reactive, ref } from 'vue'

type ChartMode = 'feixing' | 'sanhe' | 'sihua'

type StarDisplayOptions = {
  showMainStars: boolean
  showAuxStars: boolean
  showTransforms: boolean
  showBrightness: boolean
  showChangsheng: boolean
  showBoshi: boolean
  showJiangSui: boolean
  auxLimit: number
}

type OverlayDisplayOptions = {
  showDaxian: boolean
  showLiunian: boolean
  showLiuyue: boolean
  showXiaoxian: boolean
}

const HOTKEY_LIST = [
  { key: '←/[', desc: '切换到上一个Tab' },
  { key: '→/]', desc: '切换到下一个Tab' },
  { key: 'Esc', desc: '关闭宫位详情面板' },
  { key: '1-9,0', desc: '选择第1-10个宫位' },
  { key: '?', desc: '打开/关闭快捷键帮助' },
] as const

const BRIGHTNESS_LEGEND = [
  { level: '庙', desc: '最旺，如鱼得水', color: '#92400e', val: 6 },
  { level: '旺', desc: '次吉，力量强盛', color: '#dc2626', val: 5 },
  { level: '得', desc: '平吉，发挥正常', color: '#b45309', val: 4 },
  { level: '利', desc: '小吉，略受限制', color: '#1d4ed8', val: 3 },
  { level: '平', desc: '普通，力量一般', color: '#374151', val: 2 },
  { level: '不', desc: '略弱，有所受损', color: '#78716c', val: 1 },
  { level: '陷', desc: '失势，力量受损', color: '#a8a29e', val: 0 },
] as const

export function useZiweiChartDisplayState() {
  const showHotkeyPanel = ref(false)
  const showBrightnessLegend = ref(false)
  const chartMode = ref<ChartMode>('feixing')
  const showSihuaLines = ref(true)

  const starDisplayOpts = reactive<StarDisplayOptions>({
    showMainStars: true,
    showAuxStars: true,
    showTransforms: true,
    showBrightness: true,
    showChangsheng: true,
    showBoshi: true,
    showJiangSui: true,
    auxLimit: 0,
  })

  const overlayOpts = reactive<OverlayDisplayOptions>({
    showDaxian: true,
    showLiunian: true,
    showLiuyue: true,
    showXiaoxian: true,
  })

  const showLiunianOverlay = computed({
    get: () => overlayOpts.showLiunian,
    set: (value: boolean) => {
      overlayOpts.showLiunian = value
    },
  })

  return {
    showHotkeyPanel,
    HOTKEY_LIST,
    showBrightnessLegend,
    BRIGHTNESS_LEGEND,
    chartMode,
    showSihuaLines,
    showLiunianOverlay,
    starDisplayOpts,
    overlayOpts,
  }
}
