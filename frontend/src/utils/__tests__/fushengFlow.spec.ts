import { describe, expect, it } from 'vitest'
import { FUSHENG_FLOW_STEPS, isFlowStepReady, resolveFlowStepId } from '@/utils/fushengFlow'

describe('fushengFlow', () => {
  it('resolves home aliases', () => {
    expect(resolveFlowStepId('/')).toBe('home')
    expect(resolveFlowStepId('/home')).toBe('home')
    expect(resolveFlowStepId('/new')).toBe('home')
  })

  it('resolves feature routes', () => {
    expect(resolveFlowStepId('/profile')).toBe('profile')
    expect(resolveFlowStepId('/new/bazi')).toBe('bazi')
    expect(resolveFlowStepId('/report')).toBe('report')
  })

  it('locks birth-dependent steps without birthDt', () => {
    const bazi = FUSHENG_FLOW_STEPS.find((s) => s.id === 'bazi')!
    expect(isFlowStepReady(bazi, false)).toBe(false)
    expect(isFlowStepReady(bazi, true)).toBe(true)
  })

  it('keeps profile step always ready', () => {
    const profile = FUSHENG_FLOW_STEPS.find((s) => s.id === 'profile')!
    expect(isFlowStepReady(profile, false)).toBe(true)
  })
})
