import { onMounted, onUnmounted, type Ref } from 'vue'

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

/**
 * A11Y-01：简易焦点陷阱（弹层 / 锁卷墙）。
 * Esc → onEscape；Tab 循环于容器内可聚焦控件。
 */
export function useFocusTrap(
  containerRef: Ref<HTMLElement | null | undefined>,
  options: {
    active: Ref<boolean> | boolean
    onEscape?: () => void
  },
) {
  function isActive() {
    return typeof options.active === 'boolean' ? options.active : options.active.value
  }

  function onKeydown(event: KeyboardEvent) {
    if (!isActive()) return
    const root = containerRef.value
    if (!root) return

    if (event.key === 'Escape') {
      options.onEscape?.()
      return
    }
    if (event.key !== 'Tab') return

    const nodes = Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE))
      .filter((el) => !el.hasAttribute('disabled') && el.offsetParent !== null)
    if (!nodes.length) return

    const first = nodes[0]
    const last = nodes[nodes.length - 1]
    const active = document.activeElement as HTMLElement | null

    if (event.shiftKey && active === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && active === last) {
      event.preventDefault()
      first.focus()
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', onKeydown)
    if (isActive() && containerRef.value) {
      const first = containerRef.value.querySelector<HTMLElement>(FOCUSABLE)
      first?.focus()
    }
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', onKeydown)
  })
}
