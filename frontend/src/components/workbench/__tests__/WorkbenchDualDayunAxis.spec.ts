import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchDualDayunAxis from '@/components/workbench/WorkbenchDualDayunAxis.vue'

const selectBazi = vi.fn()
const selectZiwei = vi.fn()

const axis = {
  minYear: 1990,
  maxYear: 2039,
  nowPct: 52,
  baziSegments: [
    { label: '甲子', left: 0, width: 25, isActive: false, isPast: true, startYear: 1990, onSelect: selectBazi },
    { label: '乙丑', left: 25, width: 25, isActive: true, isPast: false, startYear: 2000, onSelect: selectBazi },
  ],
  zwSegments: [
    { label: '丙寅', left: 0, width: 30, isActive: false, isPast: true, startYear: 1991, index: 0, onSelect: selectZiwei },
    { label: '丁卯', left: 30, width: 30, isActive: true, isPast: false, startYear: 2001, index: 1, onSelect: selectZiwei },
  ],
}

describe('WorkbenchDualDayunAxis', () => {
  it('渲染双盘标题、当前刻度与分段按钮', () => {
    const wrapper = mount(WorkbenchDualDayunAxis, {
      props: {
        axis,
        selectedBaziStartYear: 2000,
        selectedZiweiIndex: 1,
      },
    })

    expect(wrapper.text()).toContain('双盘大运对照')
    expect(wrapper.text()).toContain('1990–2039')
    expect(wrapper.find('.wb-dual-now').attributes('style')).toContain('52%')
    expect(wrapper.findAll('.wb-dual-seg')).toHaveLength(4)
    expect(wrapper.findAll('.wb-dual-seg.selected')).toHaveLength(2)
  })

  it('点击八字与紫微分段时调用对应选择函数', async () => {
    selectBazi.mockClear()
    selectZiwei.mockClear()

    const wrapper = mount(WorkbenchDualDayunAxis, {
      props: {
        axis,
        selectedBaziStartYear: null,
        selectedZiweiIndex: null,
      },
    })

    const segments = wrapper.findAll('.wb-dual-seg')
    await segments[0].trigger('click')
    await segments[3].trigger('click')

    expect(selectBazi).toHaveBeenCalledTimes(1)
    expect(selectZiwei).toHaveBeenCalledWith(1)
  })

  it('按 active / past / is-zw 状态附加 class', () => {
    const wrapper = mount(WorkbenchDualDayunAxis, {
      props: {
        axis,
        selectedBaziStartYear: null,
        selectedZiweiIndex: null,
      },
    })

    const segments = wrapper.findAll('.wb-dual-seg')
    expect(segments[0].classes()).toContain('past')
    expect(segments[1].classes()).toContain('active')
    expect(segments[2].classes()).toContain('is-zw')
    expect(segments[3].classes()).toContain('active')
  })
})
