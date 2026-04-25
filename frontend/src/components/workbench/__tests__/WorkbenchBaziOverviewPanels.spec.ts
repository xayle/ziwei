import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziOverviewPanels from '@/components/workbench/WorkbenchBaziOverviewPanels.vue'

const pillars = [
  { key: 'year', label: '年柱', stem: '庚', branch: '午', shishen: '七杀', stemColor: '#ca8a04', branchColor: '#dc2626' },
  { key: 'month', label: '月柱', stem: '辛', branch: '巳', shishen: '正官', stemColor: '#ca8a04', branchColor: '#dc2626' },
  { key: 'day', label: '日柱', stem: '甲', branch: '子', shishen: '日主', stemColor: '#16a34a', branchColor: '#2563eb' },
  { key: 'hour', label: '时柱', stem: '丙', branch: '寅', shishen: '食神', stemColor: '#dc2626', branchColor: '#16a34a' },
] as const

const wuxing = [
  { key: '木', val: 3.2 },
  { key: '火', val: 2.6 },
  { key: '土', val: 1.8 },
  { key: '金', val: 1.4 },
  { key: '水', val: 2.2 },
]

const dayunItems = [
  { start_year: 2022, stem: '庚', branch: '寅' },
  { start_year: 2032, stem: '辛', branch: '卯' },
]

describe('WorkbenchBaziOverviewPanels', () => {
  it('在 overview 模式下渲染概览四块与藏干信息', () => {
    const wrapper = mount(WorkbenchBaziOverviewPanels, {
      props: {
        mode: 'overview',
        caseName: '张三',
        birthLocalText: '1990-05-15 08:30',
        genderText: '男',
        city: '上海',
        tz: 'Asia/Shanghai',
        lon: 121.47,
        summaryText: '当前大运适合稳步推进核心事项。',
        pillars: [...pillars],
        activePillarKey: 'day',
        strength: { score: 68, tier: '偏强' },
        tenGodsText: '七杀、正官、日主、食神',
        activePillarDetail: { label: '日柱', canggan: '癸', nayin: '海中金' },
        wuxing,
        wuxingMax: 5,
        cangganNayinRows: [{ label: '日柱', canggan: '癸', nayin: '海中金' }],
        zodiacText: '马',
        gejuName: '食神生财',
        favorText: '水、金',
        avoidText: '火',
        shenshaSummaryText: '天乙贵人、白虎',
        dayunItems,
      },
    })

    expect(wrapper.text()).toContain('1.1 生辰数据')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('1.3 五行与藏干')
    expect(wrapper.text()).toContain('藏干：癸 · 纳音：海中金')
    expect(wrapper.text()).toContain('生肖')
    expect(wrapper.text()).toContain('1.4 格局与大运')
    expect(wrapper.findAll('.wb-pillar-card')).toHaveLength(4)
    expect(wrapper.find('.wb-pillar-card.active').text()).toContain('日柱')
  })

  it('在 hotfix 模式下渲染基础信息与运势摘要，并支持柱位切换', async () => {
    const wrapper = mount(WorkbenchBaziOverviewPanels, {
      props: {
        mode: 'hotfix',
        birthLocalText: '1990-05-15 08:30',
        city: '上海',
        tz: 'Asia/Shanghai',
        lon: 121.47,
        summaryText: '当前大运适合稳步推进核心事项。',
        pillars: [...pillars],
        activePillarKey: 'year',
        strength: { score: 68, tier: '偏强' },
        tenGodsText: '七杀、正官、日主、食神',
        wuxing,
        wuxingMax: 5,
        gejuName: '食神生财',
        favorText: '水、金',
        shenshaSummaryText: '天乙贵人、白虎',
        dayunItems,
      },
    })

    expect(wrapper.text()).toContain('基础信息')
    expect(wrapper.text()).toContain('大运摘要')
    expect(wrapper.text()).toContain('运势摘要')

    await wrapper.findAll('.wb-pillar-card')[1].trigger('click')
    expect(wrapper.emitted('selectPillar')).toEqual([['month']])
  })

  it('缺少数据时保持降级展示', () => {
    const wrapper = mount(WorkbenchBaziOverviewPanels, {
      props: {
        mode: 'hotfix',
        birthLocalText: '1990-05-15 08:30',
        pillars: [],
        wuxing: [],
        wuxingMax: 5,
        dayunItems: [],
      },
    })

    expect(wrapper.findAll('.wb-empty-hint')).toHaveLength(3)
    expect(wrapper.text()).toContain('暂无四柱数据')
    expect(wrapper.text()).toContain('暂无五行数据')
    expect(wrapper.text()).toContain('暂无大运数据')
  })
})
