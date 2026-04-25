import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziSummary from '@/components/workbench/WorkbenchBaziSummary.vue'

const summary = {
  dayunGz: '庚寅大运',
  dayunYearsLeft: 4,
  lyAnnualScore: 82,
  lyGz: '丙午',
  lyShishen: '偏财',
  lyTrend: { cls: 'up', text: '明显走强' },
  lyueLuck: '吉',
  lyueGz: '庚辰',
  lyueTrend: { cls: 'down', text: '略有回落' },
  balanceTone: 'c-warn',
  balanceScore: 68,
  strongList: '木、火',
  weakList: '金、水',
  balanceText: '结构略偏燥，宜补水润局。',
}

describe('WorkbenchBaziSummary', () => {
  it('渲染四张概览卡与核心文案', () => {
    const wrapper = mount(WorkbenchBaziSummary, {
      props: { summary, currentYear: 2026 },
    })

    expect(wrapper.findAll('.wb-csum-card')).toHaveLength(4)
    expect(wrapper.text()).toContain('当前大运')
    expect(wrapper.text()).toContain('庚寅大运')
    expect(wrapper.text()).toContain('2026 流年')
    expect(wrapper.text()).toContain('本月流月')
    expect(wrapper.text()).toContain('五行平衡')
  })

  it('根据分数和吉凶渲染 tone 与趋势', () => {
    const wrapper = mount(WorkbenchBaziSummary, {
      props: { summary, currentYear: 2026 },
    })

    const cards = wrapper.findAll('.wb-csum-card')
    expect(cards[1].classes()).toContain('c-good')
    expect(cards[2].classes()).toContain('c-good')
    expect(cards[3].classes()).toContain('c-warn')
    expect(wrapper.findAll('.wb-csum-score')).toHaveLength(1)
    expect(wrapper.findAll('.wb-csum-trend')[0].classes()).toContain('is-up')
    expect(wrapper.findAll('.wb-csum-trend')[1].classes()).toContain('is-down')
  })

  it('缺少分数和剩余年数时走降级展示', () => {
    const wrapper = mount(WorkbenchBaziSummary, {
      props: {
        summary: {
          ...summary,
          dayunYearsLeft: null,
          lyAnnualScore: null,
          lyShishen: '',
          lyueLuck: '平',
          balanceScore: null,
        },
        currentYear: 2026,
      },
    })

    expect(wrapper.findAll('.wb-csum-score')).toHaveLength(0)
    expect(wrapper.text()).not.toContain('剩 4 年')
    expect(wrapper.findAll('.wb-csum-card')[1].classes()).not.toContain('c-good')
    expect(wrapper.findAll('.wb-csum-card')[2].classes()).not.toContain('c-good')
    expect(wrapper.text()).not.toContain('偏财')
  })
})
