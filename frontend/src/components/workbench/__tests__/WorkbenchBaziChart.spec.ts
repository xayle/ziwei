import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziChart from '@/components/workbench/WorkbenchBaziChart.vue'

const pillars = [
  { key: 'year', label: '年柱', stem: '甲', branch: '子', shishen: '偏印', stemColor: '#16a34a', branchColor: '#2563eb' },
  { key: 'month', label: '月柱', stem: '丙', branch: '寅', shishen: '比肩', stemColor: '#dc2626', branchColor: '#16a34a' },
  { key: 'day', label: '日柱', stem: '戊', branch: '辰', shishen: '日主', isDay: true, stemColor: '#d97706', branchColor: '#d97706' },
  { key: 'hour', label: '时柱', stem: '庚', branch: '申', shishen: '食神', stemColor: '#ca8a04', branchColor: '#ca8a04' },
] as const

const activePillarDetail = {
  ...pillars[2],
  nayin: '大林木',
  canggan: '戊乙癸',
  stemWx: '土',
  branchWx: '土',
  goodShensha: [{ name: '天乙贵人' }],
  badShensha: [{ name: '白虎' }],
}

const wuxing = [
  { key: '木', val: 3.2 },
  { key: '火', val: 2.6 },
  { key: '土', val: 4.1 },
  { key: '金', val: 1.4 },
  { key: '水', val: 0.9 },
]

const wuxingRadarAxes = [
  { label: '木', x: 70, y: 14, color: '#16a34a' },
  { label: '火', x: 123, y: 52, color: '#dc2626' },
  { label: '土', x: 103, y: 118, color: '#d97706' },
  { label: '金', x: 37, y: 118, color: '#ca8a04' },
  { label: '水', x: 17, y: 52, color: '#2563eb' },
]

describe('WorkbenchBaziChart', () => {
  it('渲染四柱主表、日主强度、柱详情与五行图表', () => {
    const wrapper = mount(WorkbenchBaziChart, {
      props: {
        pillars: [...pillars],
        activePillarKey: 'day',
        activePillarDetail,
        strength: { score: 68, tier: '偏强' },
        strengthBarColor: '#f59e0b',
        wuxing,
        wuxingMax: 5,
        wuxingRadarPoints: '70,20 116,54 98,110 42,110 24,54',
        wuxingRadarAxes,
      },
    })

    expect(wrapper.text()).toContain('命盘可视化')
    expect(wrapper.findAll('.wb-pillar-table thead th')).toHaveLength(4)
    expect(wrapper.find('.wb-pillar-table th.active').text()).toContain('日柱')
    expect(wrapper.find('.wb-pt-cell.stem.active').text()).toContain('戊')
    expect(wrapper.text()).toContain('日主强度')
    expect(wrapper.find('.wb-str-tier').text()).toContain('偏强')
    expect(wrapper.find('.wb-str-score').text()).toContain('68')
    expect(wrapper.text()).toContain('日柱 · 戊辰')
    expect(wrapper.text()).toContain('纳音：大林木')
    expect(wrapper.text()).toContain('天干五行：土')
    expect(wrapper.text()).toContain('地支五行：土')
    expect(wrapper.text()).toContain('藏干：戊乙癸')
    expect(wrapper.text()).toContain('吉 · 天乙贵人')
    expect(wrapper.text()).toContain('凶 · 白虎')
    expect(wrapper.findAll('.wb-wx-row')).toHaveLength(5)
    expect(wrapper.text()).toContain('五行分布')
    expect(wrapper.find('.wb-wx-radar-poly').exists()).toBe(true)
    expect(wrapper.findAll('.wb-wx-radar-label')).toHaveLength(5)
  })

  it('点击柱位时发出 selectPillar', async () => {
    const wrapper = mount(WorkbenchBaziChart, {
      props: {
        pillars: [...pillars],
        activePillarKey: 'day',
        activePillarDetail,
        strength: { score: 68, tier: '偏强' },
        strengthBarColor: '#f59e0b',
        wuxing,
        wuxingMax: 5,
        wuxingRadarPoints: '70,20 116,54 98,110 42,110 24,54',
        wuxingRadarAxes,
      },
    })

    await wrapper.findAll('.wb-pillar-table thead th')[1].trigger('click')

    expect(wrapper.emitted('selectPillar')).toEqual([['month']])
  })

  it('缺少详情和雷达图时保持降级展示', () => {
    const wrapper = mount(WorkbenchBaziChart, {
      props: {
        pillars: [...pillars],
        activePillarKey: 'year',
        activePillarDetail: null,
        strength: null,
        strengthBarColor: '#f59e0b',
        wuxing,
        wuxingMax: 5,
        wuxingRadarPoints: undefined,
        wuxingRadarAxes,
      },
    })

    expect(wrapper.find('.wb-pillar-detail-card').exists()).toBe(false)
    expect(wrapper.find('.wb-strength-row').exists()).toBe(false)
    expect(wrapper.find('.wb-wx-radar-wrap').exists()).toBe(false)
    expect(wrapper.findAll('.wb-wx-row')).toHaveLength(5)
  })
})
