/**
 * ZiweiView.spec.ts — 紫微斗数视图单元测试
 * 测试：演示盘 / 12宫格渲染 / 信息栏 / Tab切换 / 宫格详情 / 错误处理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ZiweiView from '@/views/ZiweiView.vue'

// ── API mock ─────────────────────────────────────────────
vi.mock('@/api/ziwei', () => ({
  computeZiwei: vi.fn(),
  demoZiwei:    vi.fn(),
  ziweiBatch:   vi.fn(),
  ziweiMultiCompat: vi.fn(),
}))

vi.mock('@/api/report', () => ({
  createCase: vi.fn(),
  fetchCaseList: vi.fn(),
  deleteCase: vi.fn(),
  fetchFengshuiBagua: vi.fn(),
}))

vi.mock('@/api/snapshots', () => ({
  createSnapshot: vi.fn(),
  listSnapshots: vi.fn(),
  diffSnapshots: vi.fn(),
}))

vi.mock('@/api/similarity', () => ({
  indexChart: vi.fn(),
  searchSimilar: vi.fn(),
}))

vi.mock('@/api/admin', () => ({
  createReview: vi.fn(),
  listReviews: vi.fn(),
  getReviewStats: vi.fn(),
  getReviewQueue: vi.fn(),
  getMyReviewQueue: vi.fn(),
  getReviewAssignees: vi.fn(),
  updateReview: vi.fn(),
  getReviewHistory: vi.fn(),
  bulkReviewAction: vi.fn(),
  assignReview: vi.fn(),
  getAdminStats: vi.fn(),
  createExperiment: vi.fn(),
  listExperiments: vi.fn(),
  updateExperiment: vi.fn(),
  deleteExperiment: vi.fn(),
  getExperimentResults: vi.fn(),
}))

vi.mock('@/api/llm', () => ({
  getLlmConfig: vi.fn(),
  interpretGeneric: vi.fn(),
  streamInterpretation: vi.fn(),
  fetchDrafts: vi.fn(),
  getDraft: vi.fn(),
  updateDraft: vi.fn(),
}))

vi.mock('@/api/static-data', () => ({
  getGlossary: vi.fn(),
}))

vi.mock('@/api/fengshui', () => ({
  getFengshuiOptions: vi.fn(),
  analyzeRoomLayout: vi.fn(),
}))

vi.mock('html2canvas', () => ({
  default: vi.fn(),
}))


import { computeZiwei, demoZiwei, ziweiBatch, ziweiMultiCompat } from '@/api/ziwei'
import { createCase, fetchCaseList, fetchFengshuiBagua } from '@/api/report'
import { createSnapshot, listSnapshots, diffSnapshots } from '@/api/snapshots'
import { indexChart, searchSimilar } from '@/api/similarity'
import { createReview, listReviews, getReviewStats, getReviewQueue, getMyReviewQueue, getReviewAssignees, getReviewHistory, bulkReviewAction, assignReview, getAdminStats, createExperiment, listExperiments, getExperimentResults } from '@/api/admin'
import { getLlmConfig, interpretGeneric, fetchDrafts, getDraft, updateDraft } from '@/api/llm'
import { getGlossary } from '@/api/static-data'
import { getFengshuiOptions, analyzeRoomLayout } from '@/api/fengshui'
import html2canvas from 'html2canvas'
import type { Mock } from 'vitest'

// ── Router ────────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/ziwei', component: ZiweiView }],
})

// ── 测试数据 ─────────────────────────────────────────────
const PALACE_NAMES = [
  '命宫', '兄弟宫', '夫妻宫', '子女宫', '财帛宫', '疾厄宫',
  '迁移宫', '仆役宫', '官禄宫', '田宅宫', '福德宫', '父母宫',
]

const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

function makePalace(index: number) {
  return {
    index,
    name: PALACE_NAMES[index],
    branch: BRANCHES[index],
    stem: '甲',
    main_stars: [{ name: '紫微', brightness: '庙', brightness_val: 6, transforms: [] }],
    aux_stars: ['左辅', '右弼'],
    analysis: '测试分析',
    analysis_tags: [],
    conclusion: '测试结论',
    explanation: '详细说明文字',
    suggestion: '调整建议',
    tooltip: '',
    xiaoxian_ages: [],
    opposition_name: '',
  }
}

const MOCK_ZIWEI = {
  birth_solar: '2002-03-13',
  gender: '女',
  lunar: {
    lunar_year: 2002, lunar_month: 2, lunar_day: 1,
    is_leap_month: false, year_gz: '壬午', month_gz: '甲寅',
    hour_branch: '未', jieqi_month_gz: '甲寅',
  },
  life_palace_gz: '寅',
  body_palace_gz: '申',
  wuxing_ju: 3,
  wuxing_ju_name: '木三局',
  palaces: Array.from({ length: 12 }, (_, i) => makePalace(i)),
  dayun: {
    forward: true,
    start_age: 4,
    start_age_text: '4岁起运',
    items: [
      { index: 0, ganzhi: '癸卯', start_age: 4,  end_age: 13, start_year: 2006, sihua: {} },
      { index: 1, ganzhi: '甲辰', start_age: 14, end_age: 23, start_year: 2016, sihua: {} },
    ],
  },
  life_ruler_star: '紫微',
  body_ruler_star: '天府',
  laiyin_palace: '命宫',
  true_solar_time: '14:58',
  summary: '命盘概述文字',
  analysis: {},
  patterns: [
    { name: '紫府同宫', level: '上格', description: '贵格之命' },
  ],
  remedies: [
    { id: 'remedy_1', name: '方位调整', cost_level: '方位', actions: ['宜向东发展'], evidence: '木旺' },
  ],
  life_suggestions: [
    { category: '事业', name: '方向发展', short_desc: '宜向东南发展', actions: [] },
  ],
  template_version: 'standard',
  algorithm_version: '2.0',
  engine_version: '2.0',
}

async function mountView(options?: { attachTo?: HTMLElement }) {
  await router.push('/ziwei')
  await router.isReady()
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(ZiweiView, {
    attachTo: options?.attachTo,
    global: { plugins: [pinia, router] },
  })
}

/** 挂载并加载演示盘 */
async function mountWithResult(options?: { attachTo?: HTMLElement }) {
  ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
  const wrapper = await mountView(options)
  const demoBtn = wrapper.findAll('.btn-sec').find(b => b.text().includes('演示'))!
  await demoBtn.trigger('click')
  await flushPromises()
  return wrapper
}

// ─────────────────────────────────────────────────────────
describe('ZiweiView — 页面结构', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('渲染页面标题「紫微斗数」', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.page-title').text()).toBe('紫微斗数')
  })

  it('初始状态不渲染命盘宫格', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.palace-grid').exists()).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────
describe('ZiweiView — 演示盘', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('点击「演示盘」调用 demoZiwei', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    const wrapper = await mountView()
    const demoBtn = wrapper.findAll('.btn-sec').find(b => b.text().includes('演示'))
    expect(demoBtn).toBeDefined()
    await demoBtn!.trigger('click')
    await flushPromises()
    expect(demoZiwei).toHaveBeenCalledOnce()
  })

  it('演示盘成功后渲染 12 个宫格', async () => {
    const wrapper = await mountWithResult()
    expect(wrapper.findAll('.pc-cell').length).toBe(12)
  })

  it('渲染基本信息栏（birth_solar / 五行局名称）', async () => {
    const wrapper = await mountWithResult()
    expect(wrapper.text()).toContain('2002-03-13')
    expect(wrapper.text()).toContain('木三局')
  })

  it('API 失败时显示错误消息', async () => {
    ;(demoZiwei as Mock).mockRejectedValueOnce({
      response: { data: { detail: '演示盘加载失败' } },
    })
    const wrapper = await mountView()
    const demoBtn = wrapper.findAll('.btn-sec').find(b => b.text().includes('演示'))!
    await demoBtn.trigger('click')
    await flushPromises()
    expect(wrapper.find('.error-msg').text()).toContain('演示盘加载失败')
  })
})

// ─────────────────────────────────────────────────────────
describe('ZiweiView — Tab 切换', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换至「时间线」Tab 显示大运干支', async () => {
    const wrapper = await mountWithResult()
    const dayunTab = wrapper.findAll('.vt-btn').find(b => b.text().includes('时间线'))
    expect(dayunTab).toBeDefined()
    await dayunTab!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('癸卯')
    expect(wrapper.text()).toContain('甲辰')
    expect(wrapper.text()).toContain('4岁起运')
  })

  it('切换至「格局·宫位」Tab 显示格局名称和描述', async () => {
    const wrapper = await mountWithResult()
    const patternTab = wrapper.findAll('.vt-btn').find(b => b.text().includes('格局'))
    expect(patternTab).toBeDefined()
    await patternTab!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('紫府同宫')
    expect(wrapper.text()).toContain('贵格之命')
  })

  it('切换至「预测·建议」Tab 显示化解与生活建议', async () => {
    const wrapper = await mountWithResult()
    const suggestTab = wrapper.findAll('.vt-btn').find(b => b.text().includes('建议'))
    expect(suggestTab).toBeDefined()
    await suggestTab!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('宜向东发展')       // remedy action
    expect(wrapper.text()).toContain('宜向东南发展')    // life suggestion
  })
})

// ─────────────────────────────────────────────────────────
describe('ZiweiView — 宫格交互', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('初始无宫格详情面板', async () => {
    const wrapper = await mountWithResult()
    expect(wrapper.find('.palace-detail').exists()).toBe(false)
  })

  it('点击宫格后显示详情面板', async () => {
    const wrapper = await mountWithResult()
    await wrapper.findAll('.pc-cell')[0].trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.palace-detail').exists()).toBe(true)
  })

  it('再次点击同一宫格关闭详情面板（切换逻辑）', async () => {
    const wrapper = await mountWithResult()
    const firstCell = wrapper.findAll('.pc-cell')[0]
    await firstCell.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.palace-detail').exists()).toBe(true)

    await firstCell.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.palace-detail').exists()).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────
describe('ZiweiView — 手动排盘', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('点击「排　盘」按钮调用 computeZiwei', async () => {
    ;(computeZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    const wrapper = await mountView()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()
    expect(computeZiwei).toHaveBeenCalledOnce()
  })

  it('修改参数、城市与预设后，会按新参数调用 computeZiwei', async () => {
    ;(computeZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    const wrapper = await mountView()

    const numberInputs = wrapper.findAll('input[type="number"]')
    await numberInputs[0].setValue('1998')
    await numberInputs[1].setValue('8')
    await numberInputs[2].setValue('9')
    await numberInputs[3].setValue('6')
    await numberInputs[4].setValue('15')

    const maleRadio = wrapper.findAll('input[type="radio"]').find((input) => (input.element as HTMLInputElement).value === '男')
    expect(maleRadio).toBeDefined()
    await maleRadio!.setValue(true)

    const selects = wrapper.findAll('select')
    await selects[0].setValue('上海市')
    await selects[1].setValue('上海')

    const presetBtn = wrapper.findAll('button').find((b) => b.text().includes('飞星派'))
    expect(presetBtn).toBeDefined()
    await presetBtn!.trigger('click')

    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    expect(computeZiwei).toHaveBeenCalledWith(expect.objectContaining({
      year: 1998,
      month: 8,
      day: 9,
      hour: 6,
      minute: 15,
      gender: '男',
      longitude: 121.47,
      leap_month_method: 'next',
      tianma_method: 'month',
      brightness_method: 'mod1',
    }))
  })
})

describe('ZiweiView — A组阅读增强', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    vi.stubGlobal('alert', vi.fn())
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('结果工具栏显示导出 PNG 按钮', async () => {
    const wrapper = await mountWithResult()
    expect(wrapper.text()).toContain('导出 PNG')
  })

  it('在非命盘页签点击导出时会自动切回命盘并导出', async () => {
    const wrapper = await mountWithResult({ attachTo: document.body })
    const html2canvasMock = html2canvas as unknown as Mock
    html2canvasMock.mockResolvedValue({
      toDataURL: vi.fn(() => 'data:image/png;base64,test'),
    })

    const createElementSpy = vi.spyOn(document, 'createElement')
    const anchorClick = vi.fn()
    createElementSpy.mockImplementation((tagName: string) => {
      const element = document.createElementNS('http://www.w3.org/1999/xhtml', tagName)
      if (tagName.toLowerCase() === 'a') {
        Object.defineProperty(element, 'click', {
          value: anchorClick,
          configurable: true,
        })
      }
      return element as HTMLElement
    })

    const originalCreateObjectURL = URL.createObjectURL
    const originalRevokeObjectURL = URL.revokeObjectURL
    URL.createObjectURL = vi.fn(() => 'blob:test')
    URL.revokeObjectURL = vi.fn()

    const tabBtn = wrapper.findAll('.vt-btn').find((b) => b.text().includes('建议'))
    expect(tabBtn).toBeDefined()
    await tabBtn!.trigger('click')
    await flushPromises()

    const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('导出 PNG'))
    expect(exportBtn).toBeDefined()
    await exportBtn!.trigger('click')
    await flushPromises()

    expect(html2canvasMock).toHaveBeenCalledOnce()
    expect(wrapper.find('.chart-tab-panel').exists()).toBe(true)
    expect(anchorClick).toHaveBeenCalledOnce()

    wrapper.unmount()
    createElementSpy.mockRestore()
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
  })

  it('可打开分享面板复制链接，并添加命盘笔记', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', {
      ...window.navigator,
      clipboard: { writeText },
    })

    const wrapper = await mountWithResult()

    window.dispatchEvent(new CustomEvent('ziwei:quick-action', { detail: 'share' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.share-panel').exists()).toBe(true)
    const shareInput = wrapper.find('.sp-link-input')
    expect((shareInput.element as HTMLInputElement).value).toContain('/ziwei?')
    expect((shareInput.element as HTMLInputElement).value).toContain('y=')
    expect((shareInput.element as HTMLInputElement).value).toContain('g=')

    await wrapper.find('.sp-copy-btn').trigger('click')
    await flushPromises()
    expect(writeText).toHaveBeenCalledWith((shareInput.element as HTMLInputElement).value)

    window.dispatchEvent(new CustomEvent('ziwei:quick-action', { detail: 'notes' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.notes-panel').exists()).toBe(true)
    await wrapper.find('.np-textarea').setValue('测试笔记内容')
    await wrapper.find('.np-add').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('测试笔记内容')
    expect(localStorage.getItem('ziwei_chart_notes')).toContain('测试笔记内容')
  })

  it('参数校验失败时显示提示并阻止排盘', async () => {
    const wrapper = await mountView()

    const numberInputs = wrapper.findAll('input[type="number"]')
    await numberInputs[0].setValue('1899')
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    expect(computeZiwei).not.toHaveBeenCalled()
    expect(wrapper.find('.error-msg').text()).toContain('年份需在 1900-2100 之间')
  })

})

