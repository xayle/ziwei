import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchInfoBar from '@/components/workbench/WorkbenchInfoBar.vue'

const caseDetail = {
  id: 'case-1',
  name: '张三',
  gender: 'male',
  city: '上海',
  tz: 'Asia/Shanghai',
  lon: 121.47,
  solar_time_enabled: true,
  birth_dt_local: '1990-05-15T08:30:00',
} as any

describe('WorkbenchInfoBar', () => {
  it('渲染案例基础信息与分享链接', () => {
    const wrapper = mount(WorkbenchInfoBar, {
      props: {
        caseDetail,
        simpleView: true,
        shareUrl: 'https://example.com/share/abc',
      },
    })

    expect(wrapper.find('.wb-info-avatar').text()).toBe('张')
    expect(wrapper.find('.wb-info-name').text()).toBe('张三')
    expect(wrapper.text()).toContain('男 命')
    expect(wrapper.text()).toContain('1990年05月15日  08:30')
    expect(wrapper.text()).toContain('121.47° E')
    expect(wrapper.find('.wb-bool').text()).toContain('已启用')
    expect(wrapper.find('.wb-share-url a').attributes('href')).toBe('https://example.com/share/abc')
  })

  it('按钮点击时发出对应事件', async () => {
    const wrapper = mount(WorkbenchInfoBar, {
      props: {
        caseDetail,
        simpleView: false,
        shareUrl: null,
      },
    })

    const buttons = wrapper.findAll('button')
    const btn = (text: string) => buttons.find((b) => b.text().includes(text))!

    await btn('查看完整报告').trigger('click')
    expect(wrapper.emitted('openReport')).toHaveLength(1)

    await btn('切换完整视图').trigger('click')
    expect(wrapper.emitted('toggleView')).toHaveLength(1)

    await btn('同步个人信息').trigger('click')
    expect(wrapper.emitted('syncProfile')).toHaveLength(1)

    await btn('删除案例').trigger('click')
    expect(wrapper.emitted('deleteCase')).toHaveLength(1)
  })

  it('simpleView=false 与 solar_time_enabled=false 时显示对应降级文本', () => {
    const wrapper = mount(WorkbenchInfoBar, {
      props: {
        caseDetail: {
          ...caseDetail,
          gender: 'female',
          city: null,
          solar_time_enabled: false,
          birth_dt_local: null,
        },
        simpleView: false,
        shareUrl: null,
      },
    })

    expect(wrapper.find('.wb-btn-ghost.is-active').exists()).toBe(false)
    expect(wrapper.findAll('.wb-btn-ghost').some((b) => b.text().includes('完整视图'))).toBe(true)
    expect(wrapper.text()).toContain('女 命')
    expect(wrapper.text()).toContain('—')
    expect(wrapper.find('.wb-bool.off').text()).toContain('未启用')
    expect(wrapper.find('.wb-share-url').exists()).toBe(false)
  })
})
