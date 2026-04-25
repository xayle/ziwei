import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziIndicators from '@/components/workbench/WorkbenchBaziIndicators.vue'

const keyIndicators = {
  geju: '食神生财',
  gejuLevel: '上格',
  yongshen: '水',
  yongshenStar: '正财',
  topGoodShensha: [{ name: '天乙贵人' }],
  topBadShensha: [{ name: '白虎' }],
  weakList: '火、土',
}

const activeIndicator = {
  key: 'good-天乙贵人',
  name: '天乙贵人',
  pillar: '日柱',
  isBeneficial: true,
  meaning: '逢凶化吉，遇事多得助力。',
  advice: '宜主动争取合作与资源支持。',
}

describe('WorkbenchBaziIndicators', () => {
  it('渲染指标条、神煞详情与格局卡组', () => {
    const wrapper = mount(WorkbenchBaziIndicators, {
      props: {
        keyIndicators,
        activeIndicator,
        geju: { geju_name: '食神生财', geju_level: '上格' },
        yongshen: { favor: ['水', '金'], avoid: ['火'] },
        strength: { tier: '偏强' },
        dayStem: '甲',
        dayStemColor: '#16a34a',
      },
    })

    expect(wrapper.text()).toContain('格局')
    expect(wrapper.text()).toContain('食神生财')
    expect(wrapper.text()).toContain('用神')
    expect(wrapper.text()).toContain('正财')
    expect(wrapper.text()).toContain('凶煞')
    expect(wrapper.text()).toContain('白虎')
    expect(wrapper.find('.wb-shensha-detail-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('所在柱：日柱')
    expect(wrapper.text()).toContain('偏吉')
    expect(wrapper.text()).toContain('忌神')
    expect(wrapper.text()).toContain('偏强')
    expect(wrapper.findAll('.wb-card')).toHaveLength(4)
  })

  it('点击神煞指标时发出切换事件', async () => {
    const wrapper = mount(WorkbenchBaziIndicators, {
      props: {
        keyIndicators,
        activeIndicator: null,
        geju: null,
        yongshen: null,
        strength: null,
        dayStem: '甲',
      },
    })

    const buttons = wrapper.findAll('button.wb-indi-item.is-clickable')
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('toggleIndicatorShensha')).toEqual([
      ['good-天乙贵人'],
      ['bad-白虎'],
    ])
  })

  it('缺少扩展数据时保持降级展示', () => {
    const wrapper = mount(WorkbenchBaziIndicators, {
      props: {
        keyIndicators: null,
        activeIndicator: null,
        geju: null,
        yongshen: { favor: [], avoid: [] },
        strength: null,
        dayStem: null,
      },
    })

    expect(wrapper.find('.wb-indicator-bar').exists()).toBe(false)
    expect(wrapper.find('.wb-shensha-detail-card').exists()).toBe(false)
    expect(wrapper.findAll('.wb-card')).toHaveLength(2)
    expect(wrapper.text()).toContain('用神')
    expect(wrapper.text()).toContain('忌神')
  })
})
