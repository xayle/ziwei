import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SnippetHooksPanel from '@/components/fusheng/SnippetHooksPanel.vue'

const copyMock = vi.fn(async () => true)
const trackMock = vi.fn()

vi.mock('@/utils/copyText', () => ({
  copyTextToClipboard: (...args: unknown[]) => copyMock(...args),
}))

vi.mock('@/utils/analytics', () => ({
  track: (...args: unknown[]) => trackMock(...args),
}))

const hooks = [
  { tag: '事实', text: '日主戊土，正官格透干。', layer: 'engine' as const },
  { tag: '典籍', text: '官格喜印护身。', layer: 'classical' as const },
]

describe('SnippetHooksPanel (T096)', () => {
  beforeEach(() => {
    copyMock.mockClear()
    trackMock.mockClear()
  })

  it('renders hooks and copies one line', async () => {
    const wrapper = mount(SnippetHooksPanel, {
      props: {
        hooks,
        caseId: 'case-1',
        verticalTitle: '卷三·运之波',
        source: 'report',
      },
    })
    expect(wrapper.get('[data-testid="snippet-hooks"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('日主戊土')
    await wrapper.get('[data-testid="snippet-copy-0"]').trigger('click')
    expect(copyMock).toHaveBeenCalledWith('日主戊土，正官格透干。')
    expect(trackMock).toHaveBeenCalledWith(
      expect.objectContaining({
        event_type: 'funnel_step',
        case_id: 'case-1',
        properties: expect.objectContaining({
          step: 'snippet_copy',
          action: 'one',
          source: 'report',
        }),
      }),
    )
  })

  it('copies all hooks joined by newline', async () => {
    const wrapper = mount(SnippetHooksPanel, {
      props: { hooks, source: 'landing' },
    })
    await wrapper.get('[data-testid="snippet-copy-all"]').trigger('click')
    expect(copyMock).toHaveBeenCalledWith('日主戊土，正官格透干。\n官格喜印护身。')
    expect(trackMock).toHaveBeenCalledWith(
      expect.objectContaining({
        properties: expect.objectContaining({ action: 'all', source: 'landing' }),
      }),
    )
  })
})
