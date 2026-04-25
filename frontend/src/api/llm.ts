/**
 * llm.ts — LLM 辅助解读 API 封装
 *
 * ⚠️  /api/v1/llm/stream 需要 Authorization: Bearer <token>
 *     EventSource 不支持自定义 header，因此使用 fetch() + ReadableStream 手动解析 SSE。
 */

const BASE = '/api/v1/llm'

function emitBackendUnavailable(status?: number, path?: string): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('app:backend-unavailable', {
    detail: {
      status: typeof status === 'number' ? status : null,
      path: path ?? '',
    },
  }))
}

function getToken(): string | null {
  return localStorage.getItem('token')
}

// ── SSE 流式生成 ──────────────────────────────────────────────────────────────

export interface StreamParams {
  chart_hash: string
  life_palace_gz?: string
  wuxing_ju_name?: string
  pattern_summary?: string
  birth_info_summary?: string
}

/**
 * 调用 GET /api/v1/llm/stream（SSE），逐字 chunk 回调
 *
 * @param params      SSE query 参数
 * @param onChunk     每次收到文字块的回调
 * @param onDone      流结束回调（带完整文本）
 * @param onSaved     草稿自动保存后回调（带 saved_id）
 */
export async function streamInterpretation(
  params: StreamParams,
  onChunk: (chunk: string) => void,
  onDone: (fullText: string) => void,
  onSaved: (savedId: number) => void
): Promise<void> {
  const qs = new URLSearchParams({
    chart_hash: params.chart_hash,
    life_palace_gz: params.life_palace_gz ?? '',
    wuxing_ju_name: params.wuxing_ju_name ?? '',
    pattern_summary: params.pattern_summary ?? '',
    birth_info_summary: params.birth_info_summary ?? '',
  })

  const token = getToken()
  const headers: Record<string, string> = { Accept: 'text/event-stream' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${BASE}/stream?${qs}`, { headers })
  } catch {
    emitBackendUnavailable(undefined, '/stream')
    throw new Error('后端连接失败，请确认服务已启动并重试')
  }

  if (!res.ok) {
    if (res.status >= 500) {
      emitBackendUnavailable(res.status, '/stream')
    }
    throw new Error(`SSE 请求失败: ${res.status} ${res.statusText}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  let currentEvent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        const rawData = line.slice(5).trim()
        if (!rawData) continue

        if (currentEvent === 'done') {
          try {
            const payload = JSON.parse(rawData)
            onDone(payload.full_text ?? '')
          } catch { /* ignore parse error */ }
          currentEvent = ''
        } else if (currentEvent === 'saved') {
          try {
            const payload = JSON.parse(rawData)
            onSaved(payload.saved_id)
          } catch { /* ignore */ }
          currentEvent = ''
        } else {
          // 普通 data chunk
          onChunk(rawData)
        }
      } else if (line === '') {
        currentEvent = ''
      }
    }
  }
}

// ── 同步解读（非流式）─────────────────────────────────────────────────────────

export interface InterpretRequest {
  chart_hash: string
  life_palace_gz?: string
  wuxing_ju_name?: string
  pattern_summary?: string
  birth_info_summary?: string
  geju_name?: string
  yongshen_favor?: string[]
}

export interface LlmDraft {
  id: number
  chart_hash: string
  provider: string
  model: string
  prompt_version: string
  draft_text: string
  status: 'pending_review' | 'approved' | 'rejected'
  reviewer: string
  reviewer_notes: string
  input_tokens: number
  output_tokens: number
  cost_usd_estimate: number
  created_at: string
  reviewed_at: string | null
  deleted_at: string | null
}

async function authPost<T>(path: string, body: unknown): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })
  } catch {
    emitBackendUnavailable(undefined, path)
    throw new Error('后端连接失败，请确认服务已启动并重试')
  }

  if (!res.ok) {
    if (res.status >= 500) {
      emitBackendUnavailable(res.status, path)
    }
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<T>
}

async function authGet<T>(path: string, qs?: Record<string, string>): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const url = qs ? `${BASE}${path}?${new URLSearchParams(qs)}` : `${BASE}${path}`
  let res: Response
  try {
    res = await fetch(url, { headers })
  } catch {
    emitBackendUnavailable(undefined, path)
    throw new Error('后端连接失败，请确认服务已启动并重试')
  }

  if (!res.ok) {
    if (res.status >= 500) {
      emitBackendUnavailable(res.status, path)
    }
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<T>
}

/** POST /api/v1/llm/interpret-bazi — 完整八字一键解读（D3） */
export function interpretBazi(caseId: string, module?: string): Promise<LlmDraft> {
  return authPost<LlmDraft>('/interpret-bazi', { case_id: caseId, module })
}

/** POST /api/v1/llm/interpret-module — 分模块解读（D1） */
export function interpretModule(
  caseId: string,
  module: string,
  context?: Record<string, unknown>
): Promise<{ case_id: string; module: string; interpretation: string; generated_at: string }> {
  return authPost('/interpret-module', { case_id: caseId, module, context })
}

/** GET /api/v1/llm/drafts — 最近草稿列表 */
export function fetchDrafts(params?: { limit?: number; status?: string }): Promise<{
  total: number
  items: LlmDraft[]
}> {
  const qs: Record<string, string> = {}
  if (params?.limit) qs.limit = String(params.limit)
  if (params?.status) qs.status = params.status
  return authGet('/drafts', Object.keys(qs).length ? qs : undefined)
}

/** GET /api/v1/llm/config — LLM 配置 */
export function getLlmConfig(): Promise<Record<string, unknown>> {
  return authGet('/config')
}

/** GET /api/v1/llm/drafts/:id — 获取单个草稿 */
export function getDraft(draftId: number): Promise<LlmDraft> {
  return authGet(`/drafts/${draftId}`)
}

/** PATCH /api/v1/llm/drafts/:id — 更新草稿（审核等） */
export async function updateDraft(draftId: number, body: { status?: string; reviewer?: string; reviewer_notes?: string }): Promise<LlmDraft> {
  const token = getToken()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${BASE}/drafts/${draftId}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body),
    })
  } catch {
    emitBackendUnavailable(undefined, `/drafts/${draftId}`)
    throw new Error('后端连接失败，请确认服务已启动并重试')
  }
  if (!res.ok) {
    if (res.status >= 500) {
      emitBackendUnavailable(res.status, `/drafts/${draftId}`)
    }
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<LlmDraft>
}

/** DELETE /api/v1/llm/drafts/:id — 删除草稿 */
export async function deleteDraft(draftId: number): Promise<void> {
  const token = getToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${BASE}/drafts/${draftId}`, { method: 'DELETE', headers })
  } catch {
    emitBackendUnavailable(undefined, `/drafts/${draftId}`)
    throw new Error('后端连接失败，请确认服务已启动并重试')
  }
  if (!res.ok) {
    if (res.status >= 500) {
      emitBackendUnavailable(res.status, `/drafts/${draftId}`)
    }
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
}

/** POST /api/v1/llm/interpret — 通用解读（非流式） */
export function interpretGeneric(body: InterpretRequest): Promise<LlmDraft> {
  return authPost<LlmDraft>('/interpret', body)
}
