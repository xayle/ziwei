export type FlowStepId = 'home' | 'profile' | 'bazi' | 'ziwei' | 'report' | 'extensions'

export type FlowStep = {
  id: FlowStepId
  label: string
  path: string
  requiresBirth?: boolean
}

export const FUSHENG_FLOW_STEPS: FlowStep[] = [
  { id: 'home', label: '首页', path: '/' },
  { id: 'profile', label: '档案', path: '/profile' },
  { id: 'bazi', label: '八字', path: '/new/bazi', requiresBirth: true },
  { id: 'ziwei', label: '紫微', path: '/new/ziwei', requiresBirth: true },
  { id: 'report', label: '报告', path: '/report', requiresBirth: true },
  { id: 'extensions', label: '工具', path: '/extensions', requiresBirth: true },
]

export function resolveFlowStepId(path: string): FlowStepId {
  if (path === '/' || path === '/home' || path === '/new') return 'home'
  if (path.startsWith('/extensions')) return 'extensions'
  if (path.startsWith('/new/ziwei')) return 'ziwei'
  const matched = FUSHENG_FLOW_STEPS.find((step) => step.path === path)
  return matched?.id ?? 'home'
}

export function isFlowStepReady(step: FlowStep, hasBirthDt: boolean): boolean {
  if (!step.requiresBirth) return true
  return hasBirthDt
}
