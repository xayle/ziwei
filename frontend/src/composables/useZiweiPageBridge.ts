import type { Ref } from 'vue'
import type { PalaceResponse, ZiweiResponse } from '@/api/ziwei'

type UseZiweiPageBridgeOptions = {
  result: Ref<ZiweiResponse | null>
  showHotkeyPanel: Ref<boolean>
  selectPalace: (palace: PalaceResponse) => void
}

export function useZiweiPageBridge(options: UseZiweiPageBridgeOptions) {
  function getChartExportElement(): HTMLElement | null {
    return document.querySelector('.palace-grid-wrap') as HTMLElement | null
      ?? document.querySelector('.chart-tab-panel') as HTMLElement | null
  }

  function toggleHotkeyPanel() {
    options.showHotkeyPanel.value = !options.showHotkeyPanel.value
  }

  function selectPalaceByOrder(order: number) {
    const palace = options.result.value?.palaces?.[order - 1]
    if (palace) options.selectPalace(palace)
  }

  return {
    getChartExportElement,
    toggleHotkeyPanel,
    selectPalaceByOrder,
  }
}
