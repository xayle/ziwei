import { ref } from 'vue'
import { readStorage, writeStorage } from '@/utils/browserStorage'

export function useOneTimeFlag(key: string) {
  const isVisible = ref(!readStorage(key))

  function dismiss(): void {
    isVisible.value = false
    writeStorage(key, 'true')
  }

  return {
    isVisible,
    dismiss,
  }
}