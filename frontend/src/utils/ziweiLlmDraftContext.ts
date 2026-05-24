import type { StreamParams } from '@/api/llm'

export interface ZiweiLlmDraftContext extends StreamParams {
  summary: string
  createdAt: string
}

const STORAGE_KEY = 'ziwei_llm_draft_context'

export function saveZiweiLlmDraftContext(context: ZiweiLlmDraftContext): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(context))
}

export function loadZiweiLlmDraftContext(): ZiweiLlmDraftContext | null {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as ZiweiLlmDraftContext
  } catch {
    return null
  }
}

export function clearZiweiLlmDraftContext(): void {
  sessionStorage.removeItem(STORAGE_KEY)
}
