/**
 * ParamControl.spec.ts — 参数控制栏组件测试
 * 覆盖：dirty 提示条、重新计算按钮、取消按钮、各章节参数控件渲染
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { reactive } from 'vue'
import ParamControl from '@/components/report/ParamControl.vue'

// ─── store mock ───────────────────────────────────────────────────
const applyParamsAndRecompute = vi.fn(() => Promise.resolve())
const discardParams = vi.fn()
const updatePendingParam = vi.fn()

const storeMock = reactive({
  dirtyParams:  {} as Record<string, boolean>,
  loadingMap:   {} as Record<string, boolean>,
  caseData: { name: '张三', birth_dt_local: '1990-05-15T08:30:00' } as unknown,
  pendingParams: {
    bazi:     { mode: 'dual', solar_time_enabled: false, liunian_range: [2020, 2036] as [number,number] },
    ziwei:    { gender: 'M', template_version: 'standard', liunian_year: 2026, dayun_index: null },
    name:     { name_override: null, birth_year_override: null },
    zeri:     { purpose: 'general', month: '2026-04', house_direction: null },
    fengshui: { birth_year_override: null, gender_override: null },
  },
  applyParamsAndRecompute,
  discardParams,
  updatePendingParam,
})

vi.mock('@/stores/report', () => ({
  useReportStore: () => storeMock,
}))

function mountCtrl(chapterKey: string) {
  return mount(ParamControl, {
    props: { chapterKey },
  })
}

function resetStore() {
  storeMock.dirtyParams = {}
  storeMock.loadingMap  = {}
  vi.clearAllMocks()
}

// ─── dirty 提示条 ────────────────────────────────────────────────

describe('ParamControl — dirty 提示条', () => {
  beforeEach(resetStore)

  it('dirty=false 时不渲染 .dirty-bar', () => {
    storeMock.dirtyParams = { bazi: false }
    const wrapper = mountCtrl('bazi')
    expect(wrapper.find('.dirty-bar').exists()).toBe(false)
  })

  it('dirty=true 时渲染 .dirty-bar 并包含提示文字', async () => {
    storeMock.dirtyParams = { bazi: true }
    const wrapper = mountCtrl('bazi')
    await flushPromises()
    // dirty-bar 通过 v-if 控制，需要验证显示
    const bar = wrapper.find('.dirty-bar')
    expect(bar.exists()).toBe(true)
    expect(bar.text()).toContain('参数已修改')
  })

  it('dirty 提示条包含 "取消" 按钮', async () => {
    storeMock.dirtyParams = { bazi: true }
    const wrapper = mountCtrl('bazi')
    await flushPromises()
    const discardBtn = wrapper.find('.btn-discard')
    expect(discardBtn.exists()).toBe(true)
    expect(discardBtn.text()).toContain('取消')
  })

  it('ziwei 参数 dirty 时也渲染提示条', async () => {
    storeMock.dirtyParams = { ziwei: true }
    const wrapper = mountCtrl('ziwei')
    await flushPromises()
    expect(wrapper.find('.dirty-bar').exists()).toBe(true)
  })
})

// ─── 按钮行为 ────────────────────────────────────────────────────

describe('ParamControl — 重新计算 / 取消', () => {
  beforeEach(resetStore)

  it('点击"重新计算"调用 applyParamsAndRecompute("bazi")', async () => {
    const wrapper = mountCtrl('bazi')
    const btn = wrapper.find('.btn-recompute')
    await btn.trigger('click')
    expect(applyParamsAndRecompute).toHaveBeenCalledWith('bazi')
  })

  it('点击"重新计算"调用 applyParamsAndRecompute("ziwei")', async () => {
    const wrapper = mountCtrl('ziwei')
    const btn = wrapper.find('.btn-recompute')
    await btn.trigger('click')
    expect(applyParamsAndRecompute).toHaveBeenCalledWith('ziwei')
  })

  it('点击"取消"调用 discardParams("bazi")', async () => {
    storeMock.dirtyParams = { bazi: true }
    const wrapper = mountCtrl('bazi')
    await flushPromises()
    const discardBtn = wrapper.find('.btn-discard')
    await discardBtn.trigger('click')
    expect(discardParams).toHaveBeenCalledWith('bazi')
  })

  it('loading=true 时重新计算按钮被 disabled', () => {
    storeMock.loadingMap = { bazi: true }
    const wrapper = mountCtrl('bazi')
    const btn = wrapper.find('.btn-recompute')
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('loading=false 时重新计算按钮不 disabled', () => {
    storeMock.loadingMap = { bazi: false }
    const wrapper = mountCtrl('bazi')
    const btn = wrapper.find('.btn-recompute')
    expect(btn.attributes('disabled')).toBeUndefined()
  })
})

// ─── 八字参数控件 ────────────────────────────────────────────────

describe('ParamControl — 八字（bazi）参数区', () => {
  beforeEach(resetStore)

  it('渲染 "模式" label', () => {
    const wrapper = mountCtrl('bazi')
    expect(wrapper.text()).toContain('模式')
  })

  it('渲染 "真太阳时" label', () => {
    const wrapper = mountCtrl('bazi')
    expect(wrapper.text()).toContain('真太阳时')
  })

  it('渲染 "流年范围" label', () => {
    const wrapper = mountCtrl('bazi')
    expect(wrapper.text()).toContain('流年范围')
  })

  it('双历单选框被勾选（mode=dual）', () => {
    storeMock.pendingParams.bazi.mode = 'dual'
    const wrapper = mountCtrl('bazi')
    const radios = wrapper.findAll('input[type="radio"]')
    const dualRadio = radios.find(r => r.attributes('value') === 'dual')
    expect((dualRadio!.element as unknown as HTMLInputElement).checked).toBe(true)
  })

  it('单历单选框未勾选（mode=dual 时）', () => {
    storeMock.pendingParams.bazi.mode = 'dual'
    const wrapper = mountCtrl('bazi')
    const radios = wrapper.findAll('input[type="radio"]')
    const singleRadio = radios.find(r => r.attributes('value') === 'single')
    expect((singleRadio!.element as unknown as HTMLInputElement).checked).toBe(false)
  })

  it('真太阳时 checkbox 与 store 状态同步（false）', () => {
    storeMock.pendingParams.bazi.solar_time_enabled = false
    const wrapper = mountCtrl('bazi')
    const checkbox = wrapper.find('input.param-checkbox')
    expect((checkbox.element as HTMLInputElement).checked).toBe(false)
  })

  it('更改双历→单历时调用 updatePendingParam', async () => {
    const wrapper = mountCtrl('bazi')
    const radios = wrapper.findAll('input[type="radio"]')
    const singleRadio = radios.find(r => r.attributes('value') === 'single')
    await singleRadio!.trigger('change')
    expect(updatePendingParam).toHaveBeenCalledWith('bazi', { mode: 'single' })
  })
})

// ─── 紫微参数控件 ────────────────────────────────────────────────

describe('ParamControl — 紫微（ziwei）参数区', () => {
  beforeEach(resetStore)

  it('渲染 "版本" label', () => {
    const wrapper = mountCtrl('ziwei')
    expect(wrapper.text()).toContain('版本')
  })

  it('渲染 "查看年份" label', () => {
    const wrapper = mountCtrl('ziwei')
    expect(wrapper.text()).toContain('查看年份')
  })

  it('版本 select 有3个选项（标准/专业/简洁）', () => {
    const wrapper = mountCtrl('ziwei')
    const select = wrapper.find('select.param-select')
    const opts = select.findAll('option')
    expect(opts).toHaveLength(3)
    expect(opts.map(o => o.text())).toContain('标准版')
    expect(opts.map(o => o.text())).toContain('专业版（含博士星）')
    expect(opts.map(o => o.text())).toContain('简洁版（隐藏辅星）')
  })

  it('更改版本时调用 updatePendingParam("ziwei", ...)', async () => {
    const wrapper = mountCtrl('ziwei')
    const select = wrapper.find('select.param-select')
    await select.setValue('pro')
    expect(updatePendingParam).toHaveBeenCalledWith('ziwei', { template_version: 'pro' })
  })
})

// ─── 姓名参数控件 ────────────────────────────────────────────────

describe('ParamControl — 姓名（name）参数区', () => {
  beforeEach(resetStore)

  it('渲染 "姓名" label', () => {
    const wrapper = mountCtrl('name')
    expect(wrapper.text()).toContain('姓名')
  })

  it('渲染 "出生年" label', () => {
    const wrapper = mountCtrl('name')
    expect(wrapper.text()).toContain('出生年')
  })

  it('姓名输入框 placeholder 来自 caseData.name', () => {
    storeMock.caseData = { name: '李四', birth_dt_local: '1995-01-01T00:00:00' } as unknown
    const wrapper = mountCtrl('name')
    const input = wrapper.find('input.param-input-text')
    expect(input.attributes('placeholder')).toContain('李四')
  })
})

// ─── 择日参数控件 ────────────────────────────────────────────────

describe('ParamControl — 择日（zeri）参数区', () => {
  beforeEach(resetStore)

  it('渲染 "用途" label', () => {
    const wrapper = mountCtrl('zeri')
    expect(wrapper.text()).toContain('用途')
  })

  it('渲染 "月份" label', () => {
    const wrapper = mountCtrl('zeri')
    expect(wrapper.text()).toContain('月份')
  })

  it('用途 select 包含 "结婚" 选项', () => {
    const wrapper = mountCtrl('zeri')
    const selects = wrapper.findAll('select.param-select')
    const purposeSelect = selects[0]
    const opts = purposeSelect.findAll('option')
    expect(opts.map(o => o.text())).toContain('结婚')
  })

  it('更改用途时调用 updatePendingParam("zeri", {purpose: ...})', async () => {
    const wrapper = mountCtrl('zeri')
    const selects = wrapper.findAll('select.param-select')
    await selects[0].setValue('wedding')
    expect(updatePendingParam).toHaveBeenCalledWith('zeri', { purpose: 'wedding' })
  })
})

// ─── 风水参数控件 ────────────────────────────────────────────────

describe('ParamControl — 风水（fengshui）参数区', () => {
  beforeEach(resetStore)

  it('渲染 "出生年" label', () => {
    const wrapper = mountCtrl('fengshui')
    expect(wrapper.text()).toContain('出生年')
  })

  it('渲染 "性别" label', () => {
    const wrapper = mountCtrl('fengshui')
    expect(wrapper.text()).toContain('性别')
  })

  it('渲染 自动/男/女 单选框', () => {
    const wrapper = mountCtrl('fengshui')
    const text = wrapper.text()
    expect(text).toContain('自动')
    expect(text).toContain('男')
    expect(text).toContain('女')
  })
})
