import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchGuideCard from '@/components/workbench/WorkbenchGuideCard.vue'

const steps = [
  { title: '选择案例', desc: '先在左侧列表中选中一个客户案例。' },
  { title: '查看命盘', desc: '在中间区域查看八字或紫微命盘。' },
  { title: '切换重点', desc: '通过导航切换到关注模块。' },
]

function mountCard(currentStep = 2) {
  return mount(WorkbenchGuideCard, {
    props: {
      currentStep,
      progressPercent: '66%',
      steps,
    },
  })
}

describe('WorkbenchGuideCard', () => {
  it('渲染标题、进度和步骤内容', () => {
    const wrapper = mountCard()

    expect(wrapper.find('.wb-guide-title').text()).toBe('新手三步引导')
    expect(wrapper.find('.wb-guide-progress-label').text()).toContain('进度 2/3')
    expect(wrapper.find('.wb-guide-progress-fill').attributes('style')).toContain('66%')
    expect(wrapper.findAll('.wb-guide-step')).toHaveLength(3)
    expect(wrapper.text()).toContain('选择案例')
    expect(wrapper.text()).toContain('查看命盘')
    expect(wrapper.text()).toContain('切换重点')
  })

  it('根据 currentStep 切换 active 与上下步按钮禁用状态', () => {
    const firstWrapper = mountCard(1)
    expect(firstWrapper.findAll('.wb-guide-step')[0].classes()).toContain('is-active')
    expect(firstWrapper.findAll('.wb-guide-nav')[0].attributes('disabled')).toBeDefined()
    expect(firstWrapper.findAll('.wb-guide-nav')[1].attributes('disabled')).toBeUndefined()

    const lastWrapper = mountCard(3)
    expect(lastWrapper.findAll('.wb-guide-step')[2].classes()).toContain('is-active')
    expect(lastWrapper.findAll('.wb-guide-nav')[1].attributes('disabled')).toBeDefined()
  })

  it('点击控制按钮和定位按钮时发出对应事件', async () => {
    const wrapper = mountCard(2)

    const navButtons = wrapper.findAll('.wb-guide-nav')
    await navButtons[0].trigger('click')
    await navButtons[1].trigger('click')
    await wrapper.find('.wb-guide-play').trigger('click')
    await wrapper.find('.wb-guide-close').trigger('click')
    await wrapper.findAll('.wb-guide-step .wb-guide-jump')[1].trigger('click')

    expect(wrapper.emitted('prev')).toHaveLength(1)
    expect(wrapper.emitted('next')).toHaveLength(1)
    expect(wrapper.emitted('play')).toHaveLength(1)
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('focusStep')).toEqual([[2]])
  })
})
