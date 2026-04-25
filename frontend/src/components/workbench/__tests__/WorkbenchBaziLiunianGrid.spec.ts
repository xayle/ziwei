import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziLiunianGrid from '@/components/workbench/WorkbenchBaziLiunianGrid.vue'

const items = [
  {
    year: 2025,
    stem: '乙',
    branch: '巳',
    ten_god: '正官',
    annualScore: 70,
    isCurrent: false,
    clash: '冲月柱',
    optimalAction: '稳住节奏',
    tags: ['守成'],
    stemColor: '#16a34a',
    branchColor: '#dc2626',
  },
  {
    year: 2026,
    stem: '丙',
    branch: '午',
    ten_god: '偏财',
    annualScore: 82,
    isCurrent: true,
    clash: '',
    optimalAction: '主动出击',
    tags: ['扩张', '合作'],
    stemColor: '#dc2626',
    branchColor: '#dc2626',
  },
]

const sparkline = {
  w: 220,
  h: 36,
  line: 'M 1 2 L 3 4',
  area: 'M 1 2 L 3 4 Z',
  pts: [
    { x: 4, y: 12, s: 70 },
    { x: 216, y: 6, s: 82 },
  ],
}

describe('WorkbenchBaziLiunianGrid', () => {
  it('渲染当前流年焦点、联动信息与流年网格', () => {
    const wrapper = mount(WorkbenchBaziLiunianGrid, {
      props: {
        currentYear: 2026,
        items,
        activeItem: items[1],
        activeDayunInfo: {
          ganzhi: '庚寅',
          startAge: 31,
          endAge: 40,
          isActive: true,
          isPast: false,
        },
        activeDomains: [
          { key: '事业', val: '稳中有升' },
          { key: '财运', val: '偏强' },
        ],
        sparkline,
      },
    })

    expect(wrapper.text()).toContain('流年')
    expect(wrapper.text()).toContain('2026 · 丙午')
    expect(wrapper.text()).toContain('年度分：82')
    expect(wrapper.text()).toContain('所处大运')
    expect(wrapper.text()).toContain('庚寅')
    expect(wrapper.findAll('.wb-ly-cell')).toHaveLength(2)
    expect(wrapper.find('.wb-ly-cell.current').text()).toContain('2026')
    expect(wrapper.find('.wb-fortune-badge').classes()).toContain('is-active')
  })

  it('点击流年单元时发出 selectYear', async () => {
    const wrapper = mount(WorkbenchBaziLiunianGrid, {
      props: {
        currentYear: 2026,
        items,
        activeItem: items[1],
        activeDomains: [],
      },
    })

    await wrapper.findAll('.wb-ly-cell')[0].trigger('click')

    expect(wrapper.emitted('selectYear')).toEqual([[2025]])
  })
})
