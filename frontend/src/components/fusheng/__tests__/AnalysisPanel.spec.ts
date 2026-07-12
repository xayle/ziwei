import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AnalysisPanel, { type AnalysisBlock } from '@/components/fusheng/AnalysisPanel.vue'

const blocks: AnalysisBlock[] = [
  {
    id: 'classical-1',
    title: '典籍断语',
    lead: 'lead',
    body: 'body',
    layer: 'classical',
  },
  {
    id: 'heuristic-1',
    title: '启发式提示',
    lead: 'lead',
    body: 'body',
    layer: 'heuristic',
  },
]

describe('AnalysisPanel', () => {
  it('renders classical badge and layer class', () => {
    const wrapper = mount(AnalysisPanel, {
      props: { blocks: [blocks[0]], defaultOpenId: 'classical-1' },
    })
    expect(wrapper.find('[data-layer="classical"]').exists()).toBe(true)
    expect(wrapper.find('.analysis-panel__block--classical').exists()).toBe(true)
  })

  it('collapses heuristic blocks by default', () => {
    const wrapper = mount(AnalysisPanel, {
      props: { blocks: [blocks[1]], collapseHeuristic: true },
    })
    expect(wrapper.find('.analysis-panel__head--heuristic').exists()).toBe(true)
    expect(wrapper.find('.analysis-panel__body').exists()).toBe(false)
    expect(wrapper.find('button').text()).toBe('展开')
  })

  it('expands heuristic on toggle', async () => {
    const wrapper = mount(AnalysisPanel, {
      props: { blocks: [blocks[1]] },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('.analysis-panel__body').exists()).toBe(true)
    expect(wrapper.text()).toContain('body')
  })
})
