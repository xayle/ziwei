import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziLiuyueHeatmap from '@/components/workbench/WorkbenchBaziLiuyueHeatmap.vue'

const heatmapItems = [
  {
    month: 3,
    month_ganzhi: '己卯',
    month_dizhi: '卯',
    luck_level: '平',
    heatBar: '#f59e0b',
    heatBg: 'rgba(245, 158, 11, 0.12)',
    isSelected: false,
    isCurrent: false,
    isLinked: false,
    tip: '宜稳中推进',
  },
  {
    month: 4,
    month_ganzhi: '庚辰',
    month_dizhi: '辰',
    luck_level: '吉',
    heatBar: '#16a34a',
    heatBg: 'rgba(22, 163, 74, 0.12)',
    isSelected: true,
    isCurrent: true,
    isLinked: true,
    tip: '本月利合作',
  },
]

const trendData = {
  w: 220,
  h: 28,
  pts: [
    { x: 10, y: 18, color: '#f59e0b', label: '3月 平' },
    { x: 210, y: 8, color: '#16a34a', label: '4月 吉' },
  ],
}

describe('WorkbenchBaziLiuyueHeatmap', () => {
  it('渲染流月热力图、趋势线和当前流月详情', () => {
    const wrapper = mount(WorkbenchBaziLiuyueHeatmap, {
      props: {
        currentYear: 2026,
        heatmapItems,
        trendData,
        activeDetail: {
          month: 4,
          month_ganzhi: '庚辰',
          month_dizhi: '辰',
          luck_level: '吉',
          color_hint: '青绿',
          dayun_stem: '庚',
          relation_to_rizhu: '比助',
          clash_with: '戌',
          tip: '利于推进重点计划。',
          disclaimer: '月度提示仅供参考。',
        },
        linkedMonths: [4, 8],
        showCurrentYearLinkHint: true,
      },
    })

    expect(wrapper.text()).toContain('流月热力')
    expect(wrapper.text()).toContain('2026年')
    expect(wrapper.findAll('.wb-lm-hm-cell')).toHaveLength(2)
    expect(wrapper.find('.wb-lm-hm-cell.lm-hm-active').text()).toContain('4月')
    expect(wrapper.find('.wb-lm-trend-svg').exists()).toBe(true)
    expect(wrapper.text()).toContain('4月 · 庚辰')
    expect(wrapper.text()).toContain('流年关键月')
    expect(wrapper.text()).toContain('宜色：青绿')
    expect(wrapper.text()).toContain('大运天干：庚')
    expect(wrapper.text()).toContain('比助')
    expect(wrapper.text()).toContain('冲：戌')
    expect(wrapper.text()).toContain('利于推进重点计划。')
    expect(wrapper.text()).toContain('当前流月为 2026 年数据')
    expect(wrapper.text()).toContain('月度提示仅供参考。')
  })

  it('点击月份时发出 selectMonth', async () => {
    const wrapper = mount(WorkbenchBaziLiuyueHeatmap, {
      props: {
        currentYear: 2026,
        heatmapItems,
        trendData: null,
        activeDetail: null,
        linkedMonths: [],
        showCurrentYearLinkHint: false,
      },
    })

    await wrapper.findAll('.wb-lm-hm-cell')[0].trigger('click')

    expect(wrapper.emitted('selectMonth')).toEqual([[3]])
  })
})
