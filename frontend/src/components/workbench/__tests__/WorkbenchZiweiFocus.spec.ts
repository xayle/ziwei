import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchZiweiFocus from '@/components/workbench/WorkbenchZiweiFocus.vue'

const palaces = [
  {
    name: '命宫',
    stem: '甲',
    branch: '子',
    changsheng: '临官',
    aux_stars: ['左辅', '右弼'],
    main_stars: [
      { name: '紫微', brightness: '庙', transforms: ['化科'] },
      { name: '天府', brightness: '旺' },
    ],
    analysis: '主先天格局与人生主轴。',
    suggestion: '本月宜稳中求进。',
  },
  {
    name: '迁移',
    stem: '乙',
    branch: '丑',
    changsheng: '帝旺',
    aux_stars: ['文昌'],
    main_stars: [{ name: '破军', brightness: '平', transforms: ['化禄'] }],
    tooltip: '外出与变动相关。',
  },
]

const relations = {
  opposite: '迁移',
  flyingOutEntries: [{ transform: '化科', target: '迁移' }],
  receiving: [{ src: '官禄', transform: '化权' }],
}

const relationGraph = {
  width: 300,
  height: 220,
  centerX: 150,
  centerY: 110,
  innerRadius: 40,
  outerRadius: 80,
  links: [
    { from: '命宫', to: '迁移', label: '对宫', kind: 'opposite' as const, d: 'M1 1 L2 2', labelX: 80, labelY: 60 },
    { from: '命宫', to: '迁移', label: '化科', kind: 'out' as const, d: 'M2 2 L3 3', labelX: 100, labelY: 80 },
  ],
  nodes: [
    { id: 'active', displayLabel: { line1: '命宫', line2: '' }, fullLabel: '命宫', x: 150, y: 110, kind: 'active' as const, palaceName: '命宫' },
    { id: 'out-1', displayLabel: { line1: '迁移', line2: '' }, fullLabel: '迁移', x: 220, y: 110, kind: 'out' as const, palaceName: '迁移' },
  ],
}

function mountComponent() {
  return mount(WorkbenchZiweiFocus, {
    props: {
      palaces,
      activePalace: palaces[0],
      highlightedPalaceName: '命宫',
      relations,
      relationGraph,
    },
  })
}

describe('WorkbenchZiweiFocus', () => {
  it('渲染宫位网格与高亮标签', () => {
    const wrapper = mountComponent()
    expect(wrapper.findAll('.zw-cell')).toHaveLength(2)
    expect(wrapper.text()).toContain('十二宫与主星')
    expect(wrapper.text()).toContain('本月落宫')
    expect(wrapper.find('.zw-cell.highlighted').text()).toContain('命宫')
  })

  it('渲染当前宫位主星、建议与关系区', () => {
    const wrapper = mountComponent()
    expect(wrapper.find('.zw-focus-title').text()).toContain('命宫 · 甲子')
    expect(wrapper.text()).toContain('紫微')
    expect(wrapper.text()).toContain('建议：本月宜稳中求进。')
    expect(wrapper.text()).toContain('对宫')
    expect(wrapper.text()).toContain('化科 → 迁移')
    expect(wrapper.find('svg.zw-rel-graph').exists()).toBe(true)
  })

  it('点击宫位、关系按钮和关系节点时发出 selectPalace', async () => {
    const wrapper = mountComponent()

    await wrapper.findAll('.zw-cell')[1].trigger('click')
    await wrapper.find('.zw-link-chip.out').trigger('click')
    await wrapper.findAll('.zw-rel-node')[1].trigger('click')

    expect(wrapper.emitted('selectPalace')).toEqual([
      ['迁移'],
      ['迁移'],
      ['迁移'],
    ])
  })
})
