import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziDayunTimeline from '@/components/workbench/WorkbenchBaziDayunTimeline.vue'

const items = [
  {
    stem: '庚',
    branch: '寅',
    ganzhi: '庚寅',
    startYear: 2021,
    endYear: 2030,
    startAge: 31,
    endAge: 40,
    isActive: true,
    isPast: false,
    progress: 58,
    ten_god: '偏财',
    flow_wuxing: '木',
    wealth_hint: '偏重进取',
    love_hint: '关系需稳',
    health_hint: '注意作息',
    narrative: '当前十年宜主动布局。',
    stemColor: '#111827',
    branchColor: '#2563eb',
  },
  {
    stem: '辛',
    branch: '卯',
    ganzhi: '辛卯',
    startYear: 2031,
    endYear: 2040,
    startAge: 41,
    endAge: 50,
    isActive: false,
    isPast: false,
    progress: 0,
    ten_god: '正财',
    stemColor: '#1f2937',
    branchColor: '#16a34a',
  },
]

describe('WorkbenchBaziDayunTimeline', () => {
  it('渲染当前大运详情与时间轴单元', () => {
    const wrapper = mount(WorkbenchBaziDayunTimeline, {
      props: {
        items,
        activeItem: items[0],
      },
    })

    expect(wrapper.text()).toContain('大运时间轴')
    expect(wrapper.text()).toContain('庚寅')
    expect(wrapper.text()).toContain('当前十年宜主动布局。')
    expect(wrapper.findAll('.wb-dayun-cell')).toHaveLength(2)
    expect(wrapper.find('.wb-fortune-badge').classes()).toContain('is-active')
    expect(wrapper.find('.wb-dayun-cell.selected').text()).toContain('2021-2030')
  })

  it('点击时间轴单元时发出 selectDayun', async () => {
    const wrapper = mount(WorkbenchBaziDayunTimeline, {
      props: {
        items,
        activeItem: items[0],
      },
    })

    await wrapper.findAll('.wb-dayun-cell')[1].trigger('click')

    expect(wrapper.emitted('selectDayun')).toEqual([[2031]])
  })
})
