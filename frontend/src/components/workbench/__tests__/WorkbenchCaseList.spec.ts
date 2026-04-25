import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchCaseList from '@/components/workbench/WorkbenchCaseList.vue'

const cases = [
  {
    id: '1',
    name: '张三',
    gender: 'male',
    birth_dt_local: '1990-05-15T08:30:00',
    city: '上海',
    tz: 'Asia/Shanghai',
    tags: ['重点', '同步档案'],
  },
  {
    id: '2',
    name: '李四',
    gender: 'female',
    birth_dt_local: '1992-08-20T19:20:00',
    city: '北京',
    tz: 'Asia/Shanghai',
    tags: ['复盘'],
  },
] as any[]

describe('WorkbenchCaseList', () => {
  it('渲染案例列表、选中态和扩展摘要', () => {
    const wrapper = mount(WorkbenchCaseList, {
      props: {
        modelValue: '',
        cases,
        selectedId: '1',
        profileSyncTag: '同步档案',
        currentDayunLabel: '庚寅大运',
        ziweiSummaryText: '命宫在午，流月落财帛。',
        baziSummaryLine: '流年偏财走强，注意节奏。',
      },
    })

    expect(wrapper.findAll('.wb-case-item')).toHaveLength(2)
    expect(wrapper.find('.wb-case-item.active').text()).toContain('张三')
    expect(wrapper.text()).toContain('个人信息')
    expect(wrapper.text()).toContain('当前大运：庚寅大运')
    expect(wrapper.text()).toContain('命宫在午，流月落财帛。')
    expect(wrapper.text()).toContain('流年偏财走强，注意节奏。')
  })

  it('输入搜索与点击案例时发出对应事件', async () => {
    const wrapper = mount(WorkbenchCaseList, {
      props: {
        modelValue: '',
        cases,
        selectedId: null,
        profileSyncTag: '同步档案',
      },
    })

    await wrapper.find('.wb-search').setValue('张')
    await wrapper.find('.btn-new').trigger('click')
    await wrapper.findAll('.wb-case-item')[1].trigger('click')

    expect(wrapper.emitted('update:modelValue')).toEqual([['张']])
    expect(wrapper.emitted('create')).toHaveLength(1)
    expect(wrapper.emitted('selectCase')?.[0]?.[0]).toMatchObject({ id: '2', name: '李四' })
  })

  it('无案例时根据搜索词显示空态文案', () => {
    const emptyWrapper = mount(WorkbenchCaseList, {
      props: {
        modelValue: '',
        cases: [],
        selectedId: null,
        profileSyncTag: '同步档案',
      },
    })
    expect(emptyWrapper.find('.wb-empty-hint').text()).toBe('暂无案例')

    const filteredWrapper = mount(WorkbenchCaseList, {
      props: {
        modelValue: '王',
        cases: [],
        selectedId: null,
        profileSyncTag: '同步档案',
      },
    })
    expect(filteredWrapper.find('.wb-empty-hint').text()).toBe('无匹配结果')
  })
})
