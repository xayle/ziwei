import { onMounted, ref } from 'vue'
import { readStorage, writeStorage } from '@/utils/browserStorage'

export type AppTheme = 'default' | 'bazi'

const THEME_KEY = 'theme'

function normalizeTheme(value: string | null): AppTheme {
  return value === 'bazi' ? 'bazi' : 'default'
}

function applyTheme(theme: AppTheme): void {
  if (typeof document === 'undefined') return
  if (theme === 'bazi') {
    document.documentElement.dataset.theme = 'bazi'
    return
  }
  delete document.documentElement.dataset.theme
}

export function resolveStoredTheme(): AppTheme {
  return normalizeTheme(readStorage(THEME_KEY))
}

export function useThemePreference() {
  const theme = ref<AppTheme>('default')

  function setTheme(nextTheme: AppTheme): void {
    theme.value = nextTheme
    applyTheme(nextTheme)
    writeStorage(THEME_KEY, nextTheme)
  }

  function toggleTheme(): void {
    setTheme(theme.value === 'default' ? 'bazi' : 'default')
  }

  function syncTheme(): void {
    const nextTheme = resolveStoredTheme()
    theme.value = nextTheme
    applyTheme(nextTheme)
  }

  onMounted(syncTheme)

  return {
    theme,
    setTheme,
    toggleTheme,
    syncTheme,
  }
}