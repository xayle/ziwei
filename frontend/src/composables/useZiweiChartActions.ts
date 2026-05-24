import { onMounted, onUnmounted, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

export type ZiweiQuickAction = 'adjust' | 'copy' | 'export' | 'share' | 'notes' | 'calendar' | 'compare' | 'bookmarks'

type UseZiweiChartActionsOptions = {
  result: Ref<ZiweiResponse | null>
  activeTab: Ref<string>
  getChartExportElement: () => HTMLElement | null
  toggleSharePanel: () => void
  toggleNotesPanel: () => void
  toggleCalendarView: () => void
  toggleComparePanel: () => void
  toggleBookmarksPanel: () => void
  showOverlayFeedback: (panel: string, message: string, type?: 'success' | 'info' | 'error') => void
}

export function useZiweiChartActions(options: UseZiweiChartActionsOptions) {
  const isExportingImage = { value: false } as Ref<boolean>

  function showAdjustModal() {
    const hourInput = document.querySelector<HTMLSelectElement>('.ziwei-form select[name="hour"]')
    if (!hourInput) return
    hourInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
    hourInput.focus()
    hourInput.classList.add('highlight-input')
    setTimeout(() => hourInput.classList.remove('highlight-input'), 2000)
  }

  function exportPDF() {
    window.print()
  }

  async function exportChartAsImage() {
    if (!options.result.value) {
      options.showOverlayFeedback('chart', '请先完成排盘再导出 PNG', 'error')
      return
    }

    if (options.activeTab.value !== 'chart') {
      options.activeTab.value = 'chart'
      await Promise.resolve()
    }

    const chartEl = options.getChartExportElement()
    if (!chartEl) {
      options.showOverlayFeedback('chart', '未找到命盘区域，请稍后重试', 'error')
      return
    }

    isExportingImage.value = true
    try {
      const html2canvas = (await import('html2canvas')).default
      const canvas = await html2canvas(chartEl, {
        backgroundColor: '#fff',
        scale: 2,
        useCORS: true,
        logging: false,
      })

      const link = document.createElement('a')
      const birthInfo = options.result.value.birth_solar || '命盘'
      link.download = `紫微命盘_${birthInfo.replace(/[^\d\u4e00-\u9fa5]/g, '_')}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
      options.showOverlayFeedback('chart', 'PNG 已开始下载')
    } catch (error) {
      console.error('导出图片失败:', error)
      options.showOverlayFeedback('chart', '导出 PNG 失败，请稍后重试', 'error')
    } finally {
      isExportingImage.value = false
    }
  }

  async function copyChartInfo() {
    if (!options.result.value) return
    const r = options.result.value
    const lines = [
      '【紫微斗数命盘】',
      `出生：${r.birth_solar} ${r.gender}`,
      `农历：${r.lunar.lunar_year}年${r.lunar.is_leap_month ? '闰' : ''}${r.lunar.lunar_month}月${r.lunar.lunar_day}日 ${r.lunar.hour_branch}时`,
      `四柱：${r.lunar.year_gz} ${r.lunar.jieqi_month_gz || r.lunar.month_gz} ${r.lunar.hour_branch}`,
      `命宫：${r.life_palace_gz}  身宫：${r.body_palace_gz}`,
      `五行局：${r.wuxing_ju_name}`,
      `命主：${r.life_ruler_star}  身主：${r.body_ruler_star}`,
      r.dayun ? `起运：${r.dayun.start_age_text || r.dayun.start_age + '岁'} ${r.dayun.forward ? '顺行' : '逆行'}` : '',
      '',
      '【十二宫】',
      ...r.palaces.map((p) => `${p.name}（${p.stem}${p.branch}）：${p.main_stars.map((s) => s.name + (s.brightness ? `[${s.brightness}]` : '')).join('、') || '无主星'}`),
      '',
      r.patterns?.length ? `【格局】${r.patterns.map((p) => p.name).join('、')}` : '',
    ].filter(Boolean)

    await navigator.clipboard.writeText(lines.join('\n'))
    const btn = document.querySelector('.pc-copy-btn') as HTMLButtonElement | null
    if (!btn) return
    const original = btn.textContent
    btn.textContent = '✓ 已复制'
    setTimeout(() => {
      btn.textContent = original
    }, 1500)
  }

  function runQuickAction(action: ZiweiQuickAction) {
    switch (action) {
      case 'adjust':
        showAdjustModal()
        break
      case 'copy':
        void copyChartInfo()
        break
      case 'export':
        void exportChartAsImage()
        break
      case 'share':
        options.toggleSharePanel()
        break
      case 'notes':
        options.toggleNotesPanel()
        break
      case 'calendar':
        options.toggleCalendarView()
        break
      case 'compare':
        options.toggleComparePanel()
        break
      case 'bookmarks':
        options.toggleBookmarksPanel()
        break
    }
  }

  function handleRightPanelQuickAction(evt: Event) {
    const action = (evt as CustomEvent<ZiweiQuickAction>).detail
    if (!action) return
    runQuickAction(action)
  }

  onMounted(() => {
    window.addEventListener('ziwei:quick-action', handleRightPanelQuickAction as EventListener)
  })

  onUnmounted(() => {
    window.removeEventListener('ziwei:quick-action', handleRightPanelQuickAction as EventListener)
  })

  return {
    isExportingImage,
    showAdjustModal,
    exportPDF,
    exportChartAsImage,
    copyChartInfo,
    runQuickAction,
  }
}