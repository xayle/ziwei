import { onUnmounted, ref } from 'vue'

type OverlayFeedbackType = 'success' | 'info' | 'error'
type OverlayFeedbackState = {
  panel: string
  type: OverlayFeedbackType
  message: string
}

export function useZiweiOverlayFeedback() {
  const overlayFeedback = ref<OverlayFeedbackState | null>(null)
  let overlayFeedbackTimer: number | undefined

  function showOverlayFeedback(panel: string, message: string, type: OverlayFeedbackType = 'success') {
    overlayFeedback.value = { panel, message, type }
    if (overlayFeedbackTimer) {
      window.clearTimeout(overlayFeedbackTimer)
    }
    overlayFeedbackTimer = window.setTimeout(() => {
      if (overlayFeedback.value?.panel === panel && overlayFeedback.value?.message === message) {
        overlayFeedback.value = null
      }
    }, 2400)
  }

  function clearOverlayFeedback(panel?: string) {
    if (!panel || overlayFeedback.value?.panel === panel) {
      overlayFeedback.value = null
    }
  }

  function isOverlayFeedbackVisible(panel: string): boolean {
    return overlayFeedback.value?.panel === panel
  }

  onUnmounted(() => {
    if (overlayFeedbackTimer) {
      window.clearTimeout(overlayFeedbackTimer)
    }
  })

  return {
    overlayFeedback,
    showOverlayFeedback,
    clearOverlayFeedback,
    isOverlayFeedbackVisible,
  }
}
