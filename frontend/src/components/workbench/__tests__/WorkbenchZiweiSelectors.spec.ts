import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchZiweiSelectors from '@/components/workbench/WorkbenchZiweiSelectors.vue'

const dayunItems = [
  { index: 0, ganzhi: '甲子', start_age: 3, end_age: 12, start_year: 1993 },
  { index: 1, ganzhi: '乙丑', start_age: 13, end_age: 22, start_year: 2003 },
]

const liuyueItems = [
  { month: 3, month_name: '三月', month_gz: '丙辰' },
  { month: 4, month_name: '四月', month_gz: '丁巳' },
]

describe('WorkbenchZiweiSelectors', () => {
  it('渲染大限列表、流月 chips 与摘要', () => {
    const wrapper = mount(WorkbenchZiweiSelectors, {
      props: {
        dayunItems,
        liuyueItems,
        activeDayunIndex: 1,
        activeLiuyueMonth: 3,
        activeDayunSummary: '乙丑大限（13-22岁）',
        activeLiuyueSummary: '当前流月：三月 丙辰',
      },
    })

    expect(wrapper.findAll('.zw-select-item')).toHaveLength(2)
    expect(wrapper.findAll('.zw-chip')).toHaveLength(2)
    expect(wrapper.text()).toContain('乙丑大限（13-22岁）')
    expect(wrapper.text()).toContain('当前流月：三月 丙辰')
    expect(wrapper.find('.zw-select-item.active').text()).toContain('乙丑')
    expect(wrapper.find('.zw-chip.active').text()).toContain('三月')
  })

  it('点击大限与流月时发出对应事件', async () => {
    const wrapper = mount(WorkbenchZiweiSelectors, {
      props: {
        dayunItems,
        liuyueItems,
        activeDayunIndex: null,
        activeLiuyueMonth: null,
      },
    })

    await wrapper.findAll('.zw-select-item')[0].trigger('click')
    await wrapper.findAll('.zw-chip')[1].trigger('click')

    expect(wrapper.emitted('selectDayun')).toEqual([[0]])
    expect(wrapper.emitted('selectLiuyue')).toEqual([[4]])
  })

  it('无流月数据时不渲染 chip 区', () => {
    const wrapper = mount(WorkbenchZiweiSelectors, {
      props: {
        dayunItems,
        liuyueItems: [],
        activeDayunIndex: 0,
        activeLiuyueMonth: null,
      },
    })

    expect(wrapper.find('.zw-chip-list').exists()).toBe(false)
  })
})
