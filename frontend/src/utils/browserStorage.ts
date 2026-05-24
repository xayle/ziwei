function getStorage(kind: 'local' | 'session' = 'local'): Storage | null {
  if (typeof window === 'undefined') return null
  return kind === 'local' ? window.localStorage : window.sessionStorage
}

export function readStorage(key: string, kind: 'local' | 'session' = 'local'): string | null {
  try {
    return getStorage(kind)?.getItem(key) ?? null
  } catch {
    return null
  }
}

export function writeStorage(key: string, value: string, kind: 'local' | 'session' = 'local'): boolean {
  try {
    getStorage(kind)?.setItem(key, value)
    return true
  } catch {
    return false
  }
}

export function removeStorage(key: string, kind: 'local' | 'session' = 'local'): boolean {
  try {
    getStorage(kind)?.removeItem(key)
    return true
  } catch {
    return false
  }
}