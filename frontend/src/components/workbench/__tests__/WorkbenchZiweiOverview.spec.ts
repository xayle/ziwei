import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchZiweiOverview from '@/components/workbench/WorkbenchZiweiOverview.vue'

const patterns = [
  { name: '紫府同宫', level: '高' },
  { name: '禄马交驰', level: '中' },
  { name: '昌曲拱命', level: '高' },
  { name: '左右同临', level: '中' },
  { name: '财荫夹印', level: '中' },
  { name: '日月并明', level: '高' },
  { name: '火铃夹命', level: '低' },
]

describe('WorkbenchZiweiOverview', () => {
  it('渲染总论、基础数据与截断后的 pattern 标签', () => {
    const wrapper = mount(WorkbenchZiweiOverview, {
      props: {
        summary: '命盘整体偏开创，适合主动推进。',
        patterns,
        lunarText: '甲辰年三月十五',
        templateVersion: 'standard',
        trueSolarTime: '08:12',
        engineVersion: '8.0',
      },
    })

    expect(wrapper.text()).toContain('紫微盘概览')
    expect(wrapper.text()).toContain('命盘整体偏开创，适合主动推进。')
    expect(wrapper.text()).toContain('甲辰年三月十五')
    expect(wrapper.text()).toContain('standard')
    expect(wrapper.text()).toContain('08:12')
    expect(wrapper.text()).toContain('8.0')
    expect(wrapper.findAll('.zw-overview-chip')).toHaveLength(6)
    expect(wrapper.text()).toContain('紫府同宫 · 高')
    expect(wrapper.text()).not.toContain('火铃夹命 · 低')
  })

  it('缺省数据时走降级文案', () => {
    const wrapper = mount(WorkbenchZiweiOverview, {
      props: {
        summary: '',
        patterns: [],
        lunarText: '—',
        templateVersion: '',
        trueSolarTime: '',
        engineVersion: null,
      },
    })

    expect(wrapper.text()).toContain('暂无总论。')
    expect(wrapper.findAll('.zw-overview-chip')).toHaveLength(0)
    expect(wrapper.text()).toContain('四化版本standard')
    expect(wrapper.text()).toContain('真太阳时—')
    expect(wrapper.text()).toContain('引擎版本—')
  })
})
