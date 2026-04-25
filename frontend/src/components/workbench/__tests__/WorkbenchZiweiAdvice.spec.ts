import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchZiweiAdvice from '@/components/workbench/WorkbenchZiweiAdvice.vue'

const remedies = [
  { id: 1, name: '作息调整', valid_scope: '本月', evidence: '火气偏旺', actions: ['减少熬夜'] },
  { id: 2, name: '环境整理', valid_scope: '居家', evidence: '动线较乱', actions: ['整理书桌'] },
  { id: 3, name: '情绪疏导', valid_scope: '关系', evidence: '压力累积', actions: ['固定散步'] },
  { id: 4, name: '财务节律', valid_scope: '财务', evidence: '支出波动', actions: ['设置预算'] },
  { id: 5, name: '社交节制', valid_scope: '外务', evidence: '信息过载', actions: ['减少应酬'] },
]

const suggestions = [
  { id: 's1', category_label: '事业', name: '聚焦主线' },
  { id: 's2', category_label: '关系', name: '减少情绪对抗' },
  { id: 's3', category_label: '健康', name: '保证睡眠' },
  { id: 's4', category_label: '财务', name: '控制冲动消费' },
  { id: 's5', category_label: '学习', name: '阶段复盘' },
  { id: 's6', category_label: '节律', name: '固定晨间计划' },
  { id: 's7', category_label: '出行', name: '提前规划' },
]

describe('WorkbenchZiweiAdvice', () => {
  it('渲染调理建议列表与截断后的建议标签', () => {
    const wrapper = mount(WorkbenchZiweiAdvice, {
      props: {
        remedies,
        suggestions,
      },
    })

    expect(wrapper.text()).toContain('建议与调理')
    expect(wrapper.findAll('.zw-advice-item')).toHaveLength(4)
    expect(wrapper.findAll('.zw-advice-chip')).toHaveLength(6)
    expect(wrapper.text()).toContain('作息调整 · 本月 · 减少熬夜')
    expect(wrapper.text()).toContain('事业 · 聚焦主线')
    expect(wrapper.text()).not.toContain('社交节制 · 外务 · 减少应酬')
    expect(wrapper.text()).not.toContain('出行 · 提前规划')
  })

  it('空数据时显示空态文案', () => {
    const wrapper = mount(WorkbenchZiweiAdvice, {
      props: {
        remedies: [],
        suggestions: [],
      },
    })

    expect(wrapper.find('.zw-advice-empty').exists()).toBe(true)
    expect(wrapper.text()).toContain('暂无可展示的调理建议。')
  })
})
