const SENTENCE_SEPS = ['。', '！', '？', '；', '\n'] as const

/**
 * 截断文本；超长时优先落在中文句末，避免格局/用神类长句拦腰切断。
 * @param max 默认 80（卡片短摘）；卷内长块请显式传 360/500。
 */
export function truncateText(text: string, max = 80): string {
  const trimmed = text.trim()
  if (!trimmed) return ''
  if (trimmed.length <= max) return trimmed
  const window = trimmed.slice(0, max)
  const minKeep = Math.max(40, Math.floor(max * 0.55))
  let best = -1
  for (const sep of SENTENCE_SEPS) {
    const idx = window.lastIndexOf(sep)
    if (idx >= minKeep && idx > best) best = idx
  }
  if (best >= 0) return window.slice(0, best + 1)
  const soft = window.replace(/[，、；：,.;\s]+$/u, '')
  const body = soft.length >= Math.max(20, Math.floor(max * 0.4)) ? soft : window.slice(0, max - 1)
  return `${body}…`
}
