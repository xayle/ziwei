import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchStateBlock from '@/components/workbench/WorkbenchStateBlock.vue'

describe('WorkbenchStateBlock', () => {
  it('loading 状态按 skeletonCount 渲染骨架条', () => {
    const wrapper = mount(WorkbenchStateBlock, {
      props: { state: 'loading', skeletonCount: 3 },
    })

    expect(wrapper.find('.wb-loading-bar').exists()).toBe(true)
    expect(wrapper.findAll('.skel')).toHaveLength(3)
  })

  it('error 状态显示消息并支持重试事件', async () => {
    const wrapper = mount(WorkbenchStateBlock, {
      props: { state: 'error', message: '加载失败', retryLabel: '再次加载' },
    })

    expect(wrapper.find('.wb-error-card').text()).toContain('加载失败')
    expect(wrapper.find('.wb-error-card').text()).toContain('再次加载')

    await wrapper.find('.wb-error-card button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('empty 状态显示标题、说明与按钮', async () => {
    const wrapper = mount(WorkbenchStateBlock, {
      props: {
        state: 'empty',
        title: '暂无结果',
        description: '请先选择案例后再查看。',
        retryLabel: '去选择案例',
      },
    })

    expect(wrapper.find('.wb-empty-title').text()).toBe('暂无结果')
    expect(wrapper.find('.wb-empty-desc').text()).toContain('请先选择案例后再查看。')

    await wrapper.find('.wb-empty-btn').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
