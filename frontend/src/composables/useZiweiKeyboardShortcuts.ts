import { onMounted, onUnmounted, type Ref } from 'vue'

type UseZiweiKeyboardShortcutsOptions = {
  activeTab: Ref<string>
  hasResult: () => boolean
  palaceCount: () => number
  selectPalaceByOrder: (order: number) => void
  closeSelectedPalace: () => void
  toggleHotkeyPanel?: () => void
}

const TAB_ORDER = ['chart', 'summary', 'palaces', 'dayun', 'liunian', 'liuyue', 'patterns', 'flying', 'forecast', 'suggest'] as const

export function useZiweiKeyboardShortcuts(options: UseZiweiKeyboardShortcutsOptions) {
  function handleKeydown(event: KeyboardEvent) {
    const target = event.target as HTMLElement | null
    const tag = target?.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
    if (!options.hasResult()) return true

    switch (event.key) {
      case 'ArrowLeft':
      case '[': {
        const idx = TAB_ORDER.indexOf(options.activeTab.value as (typeof TAB_ORDER)[number])
        if (idx > 0) options.activeTab.value = TAB_ORDER[idx - 1]
        event.preventDefault()
        break
      }
      case 'ArrowRight':
      case ']': {
        const idx = TAB_ORDER.indexOf(options.activeTab.value as (typeof TAB_ORDER)[number])
        if (idx >= 0 && idx < TAB_ORDER.length - 1) {
          options.activeTab.value = TAB_ORDER[idx + 1]
        }
        event.preventDefault()
        break
      }
      case 'Escape':
        options.closeSelectedPalace()
        event.preventDefault()
        break
      case '?':
        options.toggleHotkeyPanel?.()
        event.preventDefault()
        break
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
      case '0': {
        const order = event.key === '0' ? 10 : parseInt(event.key, 10)
        if (order <= options.palaceCount()) {
          options.selectPalaceByOrder(order)
        }
        event.preventDefault()
        break
      }
    }

    return true
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown)
  })

  return {
    handleKeydown,
    TAB_ORDER,
  }
}
