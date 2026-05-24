/**
 * BaziView.spec.ts — 八字排盘视图单元测试
 * 测试：表单提交 / loading状态 / 四柱渲染 / Tab切换 / 用神改名联动
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import BaziView from '@/views/BaziView.vue'

// ── API mock ─────────────────────────────────────────────
vi.mock('@/api/bazi', () => ({
  computeBazi: vi.fn(),
}))

vi.mock('@/api/report', () => ({
  createCase: vi.fn(),
}))

vi.mock('@/api/llm', () => ({
  interpretBazi: vi.fn(),
}))

import { computeBazi } from '@/api/bazi'
import { createCase } from '@/api/report'
import { interpretBazi } from '@/api/llm'
import type { Mock } from 'vitest'

// ── Router ────────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/bazi', component: BaziView },
    { path: '/name', component: { template: '<div>name</div>' } },
  ],
})

// ── 测试数据 ─────────────────────────────────────────────
const MOCK_BAZI = {
  pillars_primary: {
    year:  { stem: '庚', branch: '午' },
    month: { stem: '丁', branch: '丑' },
    day:   { stem: '甲', branch: '子' },
    hour:  { stem: '丙', branch: '辰' },
  },
  ten_gods: { '年': '七杀', '月': '伤官', '时': '食神' },
  yongshen: {
    favor: ['木', '火'],
    neutral: ['土'],
    avoid: ['金', '水'],
    summary: '身弱用木火',
  },
  day_master_strength: { label: '身弱', score: 32 },
  geju: { name: '正官格', description: '官星得位' },
  start_dayun_age: 5,
  dayun: {
    items: [
      { stem: '戊', branch: '寅', start_age: 5, end_age: 14, start_year: 1995, end_year: 2005 },
      { stem: '己', branch: '卯', start_age: 15, end_age: 24, start_year: 2005, end_year: 2015 },
    ],
  },
  wuxing_score: { wood: 3.0, fire: 2.5, earth: 1.0, metal: 0.5, water: 1.5 },
  methods: { solar_date: '1990-01-15', lunar_date: '己巳年腊月十九' },
}

async function mountView() {
  await router.push('/bazi')
  await router.isReady()
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(BaziView, {
    global: {
      plugins: [pinia, router],
      stubs: { teleport: true },
    },
  })
}

// ─────────────────────────────────────────────────────────
describe('BaziView — 页面结构', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('渲染页面标题「八字排盘」', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.page-title').text()).toBe('八字排盘')
  })

  it('初始状态不渲染结果区（四柱表）', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.pillars-card').exists()).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────
describe('BaziView — 排盘交互', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('点击「开始排盘」调用 computeBazi', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()
    expect(computeBazi).toHaveBeenCalledOnce()
  })

  it('loading 时按钮 disabled 且显示「排盘中…」', async () => {
    let resolveFn!: (v: unknown) => void
    ;(computeBazi as Mock).mockReturnValueOnce(
      new Promise<unknown>(r => { resolveFn = r })
    )
    const wrapper = await mountView()
    const btn = wrapper.find('.btn-primary')
    await btn.trigger('click')
    // trigger() 已等待 nextTick，此时 loading=true 并已重渲染
    expect(btn.text()).toContain('排盘中')
    expect((btn.element as HTMLButtonElement).disabled).toBe(true)
    // 释放 promise，确保测试后状态正常
    resolveFn(MOCK_BAZI)
    await flushPromises()
  })

  it('API 失败时显示错误消息', async () => {
    ;(computeBazi as Mock).mockRejectedValueOnce({
      response: { data: { detail: '参数不合法' } },
    })
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.error-msg').text()).toContain('参数不合法')
  })

  it('重置按钮清除结果区', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.pillars-card').exists()).toBe(true)

    await wrapper.find('.btn-sec').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.pillars-card').exists()).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────
describe('BaziView — 结果渲染', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('排盘成功后渲染四柱天干（庚丁甲丙）', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('庚')  // 年干
    expect(text).toContain('丁')  // 月干
    expect(text).toContain('甲')  // 日干
    expect(text).toContain('丙')  // 时干
  })
})

// ─────────────────────────────────────────────────────────
describe('BaziView — 用神改名联动', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('用神非空时显示「根据用神推荐改名」按钮', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.btn-suggest-name').exists()).toBe(true)
  })

  it('点击改名按钮后路由跳转到 /name', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    await wrapper.find('.btn-suggest-name').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/name')
  })
})

// ─────────────────────────────────────────────────────────
describe('BaziView — 保存案例', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('排盘成功后显示「保存到案例库」按钮', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    expect(wrapper.find('.btn-case-save').exists()).toBe(true)
    expect(wrapper.text()).toContain('保存到案例库')
  })

  it('保存案例时调用 createCase 并显示保存成功状态', async () => {
    ;(computeBazi as Mock).mockResolvedValueOnce(MOCK_BAZI)
    ;(createCase as Mock).mockResolvedValueOnce({
      id: 'case-001',
      name: '测试案例',
    })

    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    await wrapper.find('.btn-case-save').trigger('click')
    await wrapper.find('.bazi-form-input').setValue('测试案例')
    await wrapper.find('.bazi-form-textarea').setValue('用于保存案例测试')
    const actionButtons = wrapper.findAll('.bazi-modal-actions button')
    await actionButtons[1].trigger('click')
    await flushPromises()

    expect(createCase).toHaveBeenCalledOnce()
    expect(createCase).toHaveBeenCalledWith(expect.objectContaining({
      name: '测试案例',
      birth_dt_local: '1990-01-15T08:30:00',
      tz: 'Asia/Shanghai',
      lon: 116.41,
      gender: 'male',
      city: '北京',
      solar_time_enabled: false,
      notes: '用于保存案例测试',
    }))
    expect(wrapper.text()).toContain('已保存 · case-001')
  })
})

// ─────────────────────────────────────────────────────────
