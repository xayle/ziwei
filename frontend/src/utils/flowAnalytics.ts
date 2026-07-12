const STORAGE_KEY = 'fusheng_flow_v1'
const MAX_EVENTS = 50

export type FlowEvent = {
  step: string
  detail?: string
  at: string
}

export function trackFlowEvent(step: string, detail?: string): void {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const events: FlowEvent[] = raw ? JSON.parse(raw) as FlowEvent[] : []
    events.push({ step, detail, at: new Date().toISOString() })
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(-MAX_EVENTS)))
  } catch {
    // ignore storage errors
  }
}

export function readFlowEvents(): FlowEvent[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) as FlowEvent[] : []
  } catch {
    return []
  }
}
