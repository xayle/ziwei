import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchZiweiSummary from '@/components/workbench/WorkbenchZiweiSummary.vue'

const summary = {
  lifePalace: '命宫在午',
  bodyPalace: '身宫在迁移',
  wuxingJu: '火六局',
  rulers: '命主：贪狼 / 身主：天相',
  dayun: '33-42岁 甲辰大限',
  liunian: '2026 丙午流年',
  yearlyScore: 86,
  yearlyTone: 'c-good',
  liuyue: '农历三月',
  liuyuePalace: '财帛',
  currentMonthScore: 78,
  liuyueTrend: { cls: 'up', text: '高于均值' },
  liuyueTone: 'c-warn',
}

describe('WorkbenchZiweiSummary', () => {
  it('渲染四张概览卡与关键文案', () => {
    const wrapper = mount(WorkbenchZiweiSummary, { props: { summary } })

    expect(wrapper.findAll('.wb-csum-card')).toHaveLength(4)
    expect(wrapper.text()).toContain('命宫 / 身宫')
    expect(wrapper.text()).toContain('火六局')
    expect(wrapper.text()).toContain('33-42岁 甲辰大限')
    expect(wrapper.text()).toContain('农历三月')
  })

  it('渲染流年与流月分数和趋势 class', () => {
    const wrapper = mount(WorkbenchZiweiSummary, { props: { summary } })

    const cards = wrapper.findAll('.wb-csum-card')
    expect(cards[2].classes()).toContain('c-good')
    expect(cards[3].classes()).toContain('c-warn')
    expect(wrapper.findAll('.wb-csum-score')).toHaveLength(2)
    expect(wrapper.find('.wb-csum-trend').classes()).toContain('is-up')
    expect(wrapper.find('.wb-csum-trend').text()).toContain('高于均值')
  })

  it('无分数时不渲染分数徽标', () => {
    const wrapper = mount(WorkbenchZiweiSummary, {
      props: {
        summary: {
          ...summary,
          yearlyScore: null,
          currentMonthScore: null,
          liuyueTrend: { cls: 'flat', text: '接近均值' },
        },
      },
    })

    expect(wrapper.findAll('.wb-csum-score')).toHaveLength(0)
    expect(wrapper.find('.wb-csum-trend').classes()).toContain('is-flat')
  })
})
