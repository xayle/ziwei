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

  it('切换至「大运」Tab 显示大运干支', async () => {
    const wrapper = await mountWithResult()
    const dayunTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('大运'))
    expect(dayunTab).toBeDefined()
    await dayunTab!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('癸卯')
    expect(wrapper.text()).toContain('甲辰')
    expect(wrapper.text()).toContain('4岁起运')
  })

  it('切换至「格局」Tab 显示格局名称和描述', async () => {
    const wrapper = await mountWithResult()
    const patternTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('格局'))
    expect(patternTab).toBeDefined()
    await patternTab!.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('紫府同宫')
    expect(wrapper.text()).toContain('贵格之命')
  })

  it('切换至「建议」Tab 显示化解与生活建议', async () => {
    const wrapper = await mountWithResult()
    const suggestTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('建议'))
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

  it('可记录历史并从历史恢复先前参数', async () => {
    ;(computeZiwei as Mock).mockResolvedValue(MOCK_ZIWEI)
    const wrapper = await mountView()

    const numberInputs = () => wrapper.findAll('input[type="number"]')
    await numberInputs()[0].setValue('1999')
    await numberInputs()[1].setValue('1')
    await numberInputs()[2].setValue('2')
    await numberInputs()[3].setValue('3')
    await numberInputs()[4].setValue('4')
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    await wrapper.find('.btn-toggle-form').trigger('click')
    await numberInputs()[0].setValue('2001')
    await numberInputs()[1].setValue('5')
    await numberInputs()[2].setValue('6')
    await numberInputs()[3].setValue('7')
    await numberInputs()[4].setValue('8')
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    const historyBtn = wrapper.findAll('.btn-tool').find((b) => b.attributes('title') === '历史记录')
    expect(historyBtn).toBeDefined()
    await historyBtn!.trigger('click')
    await flushPromises()

    const items = wrapper.findAll('.hist-item')
    expect(items.length).toBeGreaterThanOrEqual(2)
    await items[1].trigger('click')
    await flushPromises()

    expect((numberInputs()[0].element as HTMLInputElement).value).toBe('1999')
    expect((numberInputs()[1].element as HTMLInputElement).value).toBe('1')
    expect((numberInputs()[2].element as HTMLInputElement).value).toBe('2')
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

    const tabBtn = wrapper.findAll('.tab-btn').find((b) => b.text().includes('建议'))
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

describe('ZiweiView — 案例数据流', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('alert', vi.fn())
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  it('可保存当前命盘到案例库并创建快照', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    ;(createCase as Mock).mockResolvedValueOnce({ id: 'case-001', name: '测试案例' })
    ;(createSnapshot as Mock).mockResolvedValueOnce({ id: 'snap-001' })
    ;(indexChart as Mock).mockResolvedValueOnce({ id: 1 })

    const wrapper = await mountWithResult()
    const saveBtn = wrapper.findAll('button').find((b) => b.text().includes('保存命盘'))
    expect(saveBtn).toBeDefined()

    await saveBtn!.trigger('click')
    await flushPromises()

    expect(createCase).toHaveBeenCalledOnce()
    expect(createSnapshot).toHaveBeenCalledOnce()
    expect(indexChart).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('已保存')
  })

  it('可打开案例库并显示案例列表', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    ;(fetchCaseList as Mock).mockResolvedValueOnce({
      items: [
        {
          id: 'case-001',
          name: '测试案例 A',
          gender: 'female',
          birth_dt_local: '2002-03-13T14:00:00',
          tz: 'Asia/Shanghai',
          birth_dt: null,
          lon: 116.4,
          city: '北京',
          solar_time_enabled: false,
          notes: null,
          tags: [],
          created_at: '2026-04-24T10:00:00',
          updated_at: '2026-04-24T10:30:00',
          last_snapshot_at: '2026-04-24T10:30:00',
          api_version_last: null,
          rule_version_last: null,
          schema_version: null,
          latest_verify_summary: null,
        },
      ],
      total: 1,
      next_cursor: null,
    })

    const wrapper = await mountWithResult()
    const casesBtn = wrapper.findAll('button').find((b) => b.text().includes('案例库'))
    expect(casesBtn).toBeDefined()

    await casesBtn!.trigger('click')
    await flushPromises()

    expect(fetchCaseList).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('测试案例 A')
  })

  it('可从案例库载入最新快照', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    ;(fetchCaseList as Mock).mockResolvedValueOnce({
      items: [
        {
          id: 'case-001',
          name: '测试案例 B',
          gender: 'female',
          birth_dt_local: '2002-03-13T14:00:00',
          tz: 'Asia/Shanghai',
          birth_dt: null,
          lon: 116.4,
          city: '北京',
          solar_time_enabled: false,
          notes: null,
          tags: [],
          created_at: '2026-04-24T10:00:00',
          updated_at: '2026-04-24T10:30:00',
          last_snapshot_at: '2026-04-24T10:30:00',
          api_version_last: null,
          rule_version_last: null,
          schema_version: null,
          latest_verify_summary: null,
        },
      ],
      total: 1,
      next_cursor: null,
    })
    ;(listSnapshots as Mock).mockResolvedValueOnce([
      {
        id: 'snap-001',
        case_id: 'case-001',
        kind: 'ziwei',
        compute_flags: null,
        input_json: {
          year: 2002,
          month: 3,
          day: 13,
          hour: 14,
          minute: 0,
          gender: '女',
          longitude: 116.4,
        },
        output_json: MOCK_ZIWEI,
        backend_json: null,
        api_version: '2.0',
        rule_version: null,
        schema_version: null,
        summary_level: null,
        summary_warning_count: null,
        summary_diff_count: null,
        summary_engine_primary: null,
        note: null,
        created_at: '2026-04-24T10:30:00',
      },
    ])

    const wrapper = await mountWithResult()
    const casesBtn = wrapper.findAll('button').find((b) => b.text().includes('案例库'))
    await casesBtn!.trigger('click')
    await flushPromises()

    const loadBtn = wrapper.findAll('button').find((b) => b.text().includes('载入'))
    expect(loadBtn).toBeDefined()
    await loadBtn!.trigger('click')
    await flushPromises()

    expect(listSnapshots).toHaveBeenCalledWith('case-001', { limit: 1, offset: 0 })
    expect(wrapper.find('.btn-save-case').text()).toContain('已保存')
  })
})

describe('ZiweiView — 相似盘检索', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('alert', vi.fn())
  })

  it('可打开相似盘面板并触发检索', async () => {
    ;(searchSimilar as Mock).mockResolvedValueOnce({
      query_hash: 'hash-001',
      total_indexed: 28,
      results: [
        {
          similarity: 0.86,
          case: {
            id: 7,
            chart_hash: 'similar-001',
            birth_solar: '1998-08-09',
            birth_year: 1998,
            birth_month: 8,
            birth_day: 9,
            birth_hour: 14,
            gender: '女',
            wuxing_ju_name: '木三局',
            life_palace_gz: '寅',
            patterns: [{ name: '紫府同宫', level: '上格' }],
            source_label: 'spa-ziwei',
            created_at: '2026-04-24T12:00:00',
          },
        },
      ],
    })

    const wrapper = await mountWithResult()
    const simBtn = wrapper.findAll('button').find((b) => b.text().includes('相似盘'))
    expect(simBtn).toBeDefined()

    await simBtn!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('相似盘检索')

    const searchBtn = wrapper.findAll('button').find((b) => b.text().includes('开始检索'))
    expect(searchBtn).toBeDefined()
    await searchBtn!.trigger('click')
    await flushPromises()

    expect(searchSimilar).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('86%')
    expect(wrapper.text()).toContain('高度相似')
  })

  it('可将当前命盘单独加入相似盘索引库', async () => {
    ;(indexChart as Mock).mockResolvedValueOnce({ id: 9 })

    const wrapper = await mountWithResult()
    const simBtn = wrapper.findAll('button').find((b) => b.text().includes('相似盘'))
    await simBtn!.trigger('click')
    await flushPromises()

    const indexBtn = wrapper.findAll('button').find((b) => b.text().includes('当前命盘入库'))
    expect(indexBtn).toBeDefined()
    await indexBtn!.trigger('click')
    await flushPromises()

    expect(indexChart).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('当前命盘已加入相似盘索引库')
  })
})

describe('ZiweiView — 快照历史', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('alert', vi.fn())
  })

  it('可打开快照面板并显示快照列表', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    ;(createCase as Mock).mockResolvedValueOnce({ id: 'case-001', name: '测试案例' })
    ;(createSnapshot as Mock).mockResolvedValueOnce({ id: 'snap-latest' })
    ;(indexChart as Mock).mockResolvedValueOnce({ id: 1 })
    ;(listSnapshots as Mock).mockResolvedValueOnce([
      {
        id: 'snap-latest',
        case_id: 'case-001',
        kind: 'ziwei',
        compute_flags: null,
        input_json: { year: 2002, month: 3, day: 13, hour: 14, minute: 0, gender: '女' },
        output_json: MOCK_ZIWEI,
        backend_json: null,
        api_version: '2.0',
        rule_version: null,
        schema_version: null,
        summary_level: null,
        summary_warning_count: null,
        summary_diff_count: null,
        summary_engine_primary: null,
        note: '最新快照',
        created_at: '2026-04-24T12:00:00',
      },
    ])

    const wrapper = await mountWithResult()
    await wrapper.find('.btn-save-case').trigger('click')
    await flushPromises()

    const snapshotBtn = wrapper.findAll('button').find((b) => b.text().includes('快照'))
    expect(snapshotBtn).toBeDefined()
    await snapshotBtn!.trigger('click')
    await flushPromises()

    expect(listSnapshots).toHaveBeenCalledWith('case-001', { limit: 10, offset: 0 })
    expect(wrapper.text()).toContain('快照历史')
    expect(wrapper.text()).toContain('最新快照')
  })

  it('可对比两个快照并显示差异摘要', async () => {
    ;(demoZiwei as Mock).mockResolvedValueOnce(MOCK_ZIWEI)
    ;(createCase as Mock).mockResolvedValueOnce({ id: 'case-001', name: '测试案例' })
    ;(createSnapshot as Mock).mockResolvedValueOnce({ id: 'snap-current' })
    ;(indexChart as Mock).mockResolvedValueOnce({ id: 1 })
    ;(listSnapshots as Mock).mockResolvedValueOnce([
      {
        id: 'snap-a',
        case_id: 'case-001',
        kind: 'ziwei',
        compute_flags: null,
        input_json: { year: 2001 },
        output_json: MOCK_ZIWEI,
        backend_json: null,
        api_version: '1.9',
        rule_version: null,
        schema_version: null,
        summary_level: null,
        summary_warning_count: null,
        summary_diff_count: null,
        summary_engine_primary: null,
        note: null,
        created_at: '2026-04-24T11:00:00',
      },
      {
        id: 'snap-b',
        case_id: 'case-001',
        kind: 'ziwei',
        compute_flags: null,
        input_json: { year: 2002 },
        output_json: MOCK_ZIWEI,
        backend_json: null,
        api_version: '2.0',
        rule_version: null,
        schema_version: null,
        summary_level: null,
        summary_warning_count: null,
        summary_diff_count: null,
        summary_engine_primary: null,
        note: null,
        created_at: '2026-04-24T12:00:00',
      },
    ])
    ;(diffSnapshots as Mock).mockResolvedValueOnce({
      snapshot_a: 'snap-a',
      snapshot_b: 'snap-b',
      changed_fields: [
        { field: 'input_json.year', value_a: 2001, value_b: 2002 },
      ],
      added_fields: ['output_json.summary'],
      removed_fields: [],
      total_changes: 1,
    })

    const wrapper = await mountWithResult()
    await wrapper.find('.btn-save-case').trigger('click')
    await flushPromises()

    const snapshotBtn = wrapper.findAll('button').find((b) => b.text().includes('快照'))
    await snapshotBtn!.trigger('click')
    await flushPromises()

    const selects = wrapper.findAll('.snp-select')
    await selects[0].setValue('snap-a')
    await selects[1].setValue('snap-b')
    await wrapper.find('.snp-compare-btn').trigger('click')
    await flushPromises()

    expect(diffSnapshots).toHaveBeenCalledWith('snap-a', 'snap-b')
    expect(wrapper.text()).toContain('共 1 处变更')
    expect(wrapper.text()).toContain('input_json.year')
  })
})

describe('ZiweiView — 审核面板', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    ;(getReviewAssignees as Mock).mockResolvedValue({
      current_username: 'reviewer',
      items: [{ id: 1, username: 'reviewer', email: 'reviewer@example.com', role: 'editor', is_admin: false, is_current_user: true }],
    })
  })

  it('可打开审核面板并加载列表与统计', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 11,
          case_id: 'case-001',
          chart_hash: 'hash-001',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待审核',
          reject_reason: null,
          created_at: '2026-04-24T10:00:00',
          updated_at: '2026-04-24T10:05:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({
      total: 1,
      pending: 1,
      approved: 0,
      rejected: 0,
      revised: 0,
    })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({
      review_id: 11,
      total: 1,
      items: [{ action: 'created', actor: 'system', timestamp: '2026-04-24T10:00:00', notes: '初始提交' }],
    })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    expect(listReviews).toHaveBeenCalledOnce()
    expect(getReviewStats).toHaveBeenCalledOnce()
    expect(getReviewHistory).toHaveBeenCalledWith(11)
    expect(wrapper.text()).toContain('审核面板')
    expect(wrapper.text()).toContain('待审核')
    expect(wrapper.text()).toContain('全部审核记录')
    expect(wrapper.text()).toContain('当前视图 1')
    expect(wrapper.text()).toContain('最后刷新')
    expect(wrapper.find('.rvp-item-status').classes()).toContain('is-pending')
    expect(wrapper.find('.rvp-owner-tag').text()).toContain('待领取')
    expect(wrapper.find('.rvp-history-tag').text()).toContain('创建')
    expect(wrapper.find('.rvp-history-tag').classes()).toContain('is-created')
  })

  it('可提交当前命盘到审核队列', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 0, pending: 0, approved: 0, rejected: 0, revised: 0 })
    ;(createReview as Mock).mockResolvedValueOnce({
      id: 21,
      case_id: null,
      chart_hash: 'hash-001',
      chart_type: 'ziwei',
      status: 'pending',
      reviewer: null,
      notes: '提交审核备注',
      reject_reason: null,
      created_at: '2026-04-24T11:00:00',
      updated_at: '2026-04-24T11:00:00',
    })
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 21,
          case_id: null,
          chart_hash: 'hash-001',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '提交审核备注',
          reject_reason: null,
          created_at: '2026-04-24T11:00:00',
          updated_at: '2026-04-24T11:00:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 21, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    await wrapper.find('.rvp-submit-notes').setValue('提交审核备注')
    const submitBtn = wrapper.findAll('.rvp-btn').find((b) => b.text().includes('提交当前命盘'))
    await submitBtn!.trigger('click')
    await flushPromises()

    expect(createReview).toHaveBeenCalledWith(expect.objectContaining({
      chart_type: 'ziwei',
      notes: '提交审核备注',
    }))
    expect(wrapper.text()).toContain('#21')
  })

  it('可手动刷新当前审核视图', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 22,
          case_id: null,
          chart_hash: 'hash-022',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '首次加载',
          reject_reason: null,
          created_at: '2026-04-24T11:05:00',
          updated_at: '2026-04-24T11:05:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 22, total: 0, items: [] })
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 22,
          case_id: null,
          chart_hash: 'hash-022',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '刷新后记录',
          reject_reason: null,
          created_at: '2026-04-24T11:05:00',
          updated_at: '2026-04-24T11:06:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const refreshBtn = wrapper.findAll('button').find((b) => b.text() === '刷新')
    await refreshBtn!.trigger('click')
    await flushPromises()

    expect(listReviews).toHaveBeenCalledTimes(2)
    expect((wrapper.find('.rvp-detail-notes').element as HTMLTextAreaElement).value).toBe('刷新后记录')
  })

  it('可批量通过审核记录', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 2,
      items: [
        {
          id: 31,
          case_id: null,
          chart_hash: 'hash-031',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待审 1',
          reject_reason: null,
          created_at: '2026-04-24T11:10:00',
          updated_at: '2026-04-24T11:10:00',
        },
        {
          id: 32,
          case_id: null,
          chart_hash: 'hash-032',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待审 2',
          reject_reason: null,
          created_at: '2026-04-24T11:11:00',
          updated_at: '2026-04-24T11:11:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 2, pending: 2, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 31, total: 0, items: [] })
    ;(bulkReviewAction as Mock).mockResolvedValueOnce({ succeeded: [31, 32], failed: [], total: 2, action: 'approved' })
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 2,
      items: [
        {
          id: 31,
          case_id: null,
          chart_hash: 'hash-031',
          chart_type: 'ziwei',
          status: 'approved',
          reviewer: 'reviewer',
          notes: '批量通过',
          reject_reason: null,
          created_at: '2026-04-24T11:10:00',
          updated_at: '2026-04-24T11:12:00',
        },
        {
          id: 32,
          case_id: null,
          chart_hash: 'hash-032',
          chart_type: 'ziwei',
          status: 'approved',
          reviewer: 'reviewer',
          notes: '批量通过',
          reject_reason: null,
          created_at: '2026-04-24T11:11:00',
          updated_at: '2026-04-24T11:12:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 2, pending: 0, approved: 2, rejected: 0, revised: 0 })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const checks = wrapper.findAll('.rvp-item-check')
    await checks[0].trigger('click')
    await checks[1].trigger('click')
    await wrapper.find('.rvp-bulk-notes').setValue('批量通过')
    expect(wrapper.findAll('.rvp-item')[0].classes()).toContain('selected-bulk')

    const bulkApproveBtn = wrapper.findAll('button').find((b) => b.text().includes('批量通过'))
    await bulkApproveBtn!.trigger('click')
    await flushPromises()

    expect(bulkReviewAction).toHaveBeenCalledWith(expect.objectContaining({
      ids: [31, 32],
      action: 'approved',
      notes: '批量通过',
    }))
    expect(wrapper.text()).toContain('批量已通过完成：成功 2 条')
  })

  it('可切到待审队列并领取当前审核单', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewQueue as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 41,
          case_id: null,
          chart_hash: 'hash-041',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待领取',
          reject_reason: null,
          created_at: '2026-04-24T11:20:00',
          updated_at: '2026-04-24T11:20:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 41, total: 0, items: [] })
    ;(assignReview as Mock).mockResolvedValueOnce({
      id: 41,
      case_id: null,
      chart_hash: 'hash-041',
      chart_type: 'ziwei',
      status: 'pending',
      reviewer: 'reviewer',
      notes: '待领取',
      reject_reason: null,
      created_at: '2026-04-24T11:20:00',
      updated_at: '2026-04-24T11:21:00',
    })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 41, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const queueBtn = wrapper.findAll('button').find((b) => b.text().includes('待审队列'))
    await queueBtn!.trigger('click')
    await flushPromises()

    expect(getReviewQueue).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('领取当前')

    const claimBtn = wrapper.findAll('button').find((b) => b.text().includes('领取当前'))
    await claimBtn!.trigger('click')
    await flushPromises()

    expect(assignReview).toHaveBeenCalledWith(41, { assignee: 'reviewer' })
    expect(wrapper.findAll('.rvp-item')[0].classes()).toContain('claimed-me')
    expect(wrapper.find('.rvp-owner-tag').text()).toContain('已归我')
    expect(wrapper.text()).toContain('已领取到我的队列')

    ;(getMyReviewQueue as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 41,
          case_id: null,
          chart_hash: 'hash-041',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: 'reviewer',
          notes: '待领取',
          reject_reason: null,
          created_at: '2026-04-24T11:20:00',
          updated_at: '2026-04-24T11:21:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })

    const mineBtn = wrapper.findAll('button').find((b) => b.text().includes('我的队列'))
    await mineBtn!.trigger('click')
    await flushPromises()

    expect(getMyReviewQueue).toHaveBeenCalledOnce()
  })

  it('可快速指派给指定 reviewer', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 51,
          case_id: null,
          chart_hash: 'hash-051',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待指派',
          reject_reason: null,
          created_at: '2026-04-24T11:30:00',
          updated_at: '2026-04-24T11:30:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 51, total: 0, items: [] })
    ;(assignReview as Mock).mockResolvedValueOnce({
      id: 51,
      case_id: null,
      chart_hash: 'hash-051',
      chart_type: 'ziwei',
      status: 'pending',
      reviewer: 'qa-reviewer',
      notes: '待指派',
      reject_reason: null,
      created_at: '2026-04-24T11:30:00',
      updated_at: '2026-04-24T11:31:00',
    })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 51, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    await wrapper.find('.rvp-assign-input').setValue('qa-reviewer')
    const assignBtn = wrapper.findAll('button').find((b) => b.text() === '指派')
    await assignBtn!.trigger('click')
    await flushPromises()

    expect(assignReview).toHaveBeenCalledWith(51, { assignee: 'qa-reviewer' })
    expect(localStorage.getItem('ziwei_review_assignee_recents')).toContain('qa-reviewer')
    expect(wrapper.text()).toContain('已指派给 qa-reviewer')
  })

  it('会读取最近使用的 reviewer 作为快捷候选', async () => {
    localStorage.setItem('ziwei_review_assignee_recents', JSON.stringify(['recent-reviewer']))
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 61,
          case_id: null,
          chart_hash: 'hash-061',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待指派',
          reject_reason: null,
          created_at: '2026-04-24T11:40:00',
          updated_at: '2026-04-24T11:40:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 61, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('recent-reviewer')
  })

  it('会读取服务端审核员候选，并用于当前领取人默认值', async () => {
    ;(getReviewAssignees as Mock).mockResolvedValueOnce({
      current_username: 'ops-user',
      items: [
        { id: 2, username: 'ops-user', email: 'ops@example.com', role: 'owner', is_admin: true, is_current_user: true },
        { id: 3, username: 'qa-reviewer', email: 'qa@example.com', role: 'editor', is_admin: false, is_current_user: false },
        { id: 4, username: 'viewer-user', email: 'viewer@example.com', role: 'viewer', is_admin: false, is_current_user: false },
      ],
    })
    ;(listReviews as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 62,
          case_id: null,
          chart_hash: 'hash-062',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待领取',
          reject_reason: null,
          created_at: '2026-04-24T11:41:00',
          updated_at: '2026-04-24T11:41:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 62, total: 0, items: [] })
    ;(assignReview as Mock).mockResolvedValueOnce({
      id: 62,
      case_id: null,
      chart_hash: 'hash-062',
      chart_type: 'ziwei',
      status: 'pending',
      reviewer: 'ops-user',
      notes: '待领取',
      reject_reason: null,
      created_at: '2026-04-24T11:41:00',
      updated_at: '2026-04-24T11:42:00',
    })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 62, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('ops-user')
  expect(wrapper.text()).toContain('当前')
  expect(wrapper.text()).toContain('qa-reviewer')
  expect(wrapper.text()).toContain('编辑')
  expect(wrapper.text()).not.toContain('viewer-user')

    const claimBtn = wrapper.findAll('button').find((b) => b.text().includes('领取当前'))
    await claimBtn!.trigger('click')
    await flushPromises()

    expect(assignReview).toHaveBeenCalledWith(62, { assignee: 'ops-user' })
  })

  it('在我的队列为空时显示分流空态文案', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 0, pending: 0, approved: 0, rejected: 0, revised: 0 })
    ;(getMyReviewQueue as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 0, pending: 0, approved: 0, rejected: 0, revised: 0 })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const mineBtn = wrapper.findAll('button').find((b) => b.text().includes('我的队列'))
    await mineBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('我的队列')
    expect(wrapper.text()).toContain('我的队列暂无待处理审核单，可先从待审队列领取')
  })

  it('在待审队列模式下禁用批量处理并显示提示', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 2, pending: 2, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewQueue as Mock).mockResolvedValueOnce({
      total: 2,
      items: [
        {
          id: 71,
          case_id: null,
          chart_hash: 'hash-071',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待领取 1',
          reject_reason: null,
          created_at: '2026-04-24T11:50:00',
          updated_at: '2026-04-24T11:50:00',
        },
        {
          id: 72,
          case_id: null,
          chart_hash: 'hash-072',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: null,
          notes: '待领取 2',
          reject_reason: null,
          created_at: '2026-04-24T11:51:00',
          updated_at: '2026-04-24T11:51:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 2, pending: 2, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 71, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const queueBtn = wrapper.findAll('button').find((b) => b.text().includes('待审队列'))
    await queueBtn!.trigger('click')
    await flushPromises()

    const bulkApproveBtn = wrapper.findAll('button').find((b) => b.text().includes('批量通过'))
    expect((bulkApproveBtn!.element as HTMLButtonElement).disabled).toBe(true)
    expect((wrapper.find('.rvp-bulk-notes').element as HTMLTextAreaElement).disabled).toBe(true)
    expect(wrapper.text()).toContain('待审队列建议先领取到我的队列，再执行批量处理')
  })

  it('在我的队列模式下显示仅处理已归我记录的强化提示', async () => {
    ;(listReviews as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getMyReviewQueue as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 81,
          case_id: null,
          chart_hash: 'hash-081',
          chart_type: 'ziwei',
          status: 'pending',
          reviewer: 'reviewer',
          notes: '我的待处理',
          reject_reason: null,
          created_at: '2026-04-24T12:00:00',
          updated_at: '2026-04-24T12:00:00',
        },
      ],
    })
    ;(getReviewStats as Mock).mockResolvedValueOnce({ total: 1, pending: 1, approved: 0, rejected: 0, revised: 0 })
    ;(getReviewHistory as Mock).mockResolvedValueOnce({ review_id: 81, total: 0, items: [] })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('审核'))
    await btn!.trigger('click')
    await flushPromises()

    const mineBtn = wrapper.findAll('button').find((b) => b.text().includes('我的队列'))
    await mineBtn!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('我的队列仅处理已归我的审核单，可直接执行批量处理')
    expect(wrapper.text()).toContain('当前为我的队列：建议优先处理已归我记录，避免跨人协作遗漏')
  })
})

describe('ZiweiView — AI 草稿', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.defineProperty(window.navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    })
  })

  it('可打开 AI 草稿面板并生成草稿', async () => {
    ;(getLlmConfig as Mock).mockResolvedValueOnce({ provider: 'openai', model: 'gpt-test' })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(interpretGeneric as Mock).mockResolvedValueOnce({
      id: 31,
      chart_hash: 'hash-001',
      provider: 'openai',
      model: 'gpt-test',
      prompt_version: 'v1',
      draft_text: '这是一段 AI 草稿。',
      status: 'pending_review',
      reviewer: '',
      reviewer_notes: '',
      input_tokens: 10,
      output_tokens: 20,
      cost_usd_estimate: 0.01,
      created_at: '2026-04-24T12:00:00',
      reviewed_at: null,
      deleted_at: null,
    })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 31,
          chart_hash: 'hash-001',
          provider: 'openai',
          model: 'gpt-test',
          prompt_version: 'v1',
          draft_text: '这是一段 AI 草稿。',
          status: 'pending_review',
          reviewer: '',
          reviewer_notes: '',
          input_tokens: 10,
          output_tokens: 20,
          cost_usd_estimate: 0.01,
          created_at: '2026-04-24T12:00:00',
          reviewed_at: null,
          deleted_at: null,
        },
      ],
    })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('AI 草稿'))
    await btn!.trigger('click')
    await flushPromises()

    await wrapper.findAll('.lzp-btn').find((b) => b.text().includes('生成草稿'))!.trigger('click')
    await flushPromises()

    expect(getLlmConfig).toHaveBeenCalledOnce()
    expect(interpretGeneric).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('这是一段 AI 草稿。')
    expect(wrapper.text()).toContain('gpt-test')
  })

  it('可审核当前 AI 草稿', async () => {
    ;(getLlmConfig as Mock).mockResolvedValueOnce({ provider: 'openai', model: 'gpt-test' })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 32,
          chart_hash: 'hash-001',
          provider: 'openai',
          model: 'gpt-test',
          prompt_version: 'v1',
          draft_text: '待审核草稿',
          status: 'pending_review',
          reviewer: '',
          reviewer_notes: '',
          input_tokens: 10,
          output_tokens: 20,
          cost_usd_estimate: 0.01,
          created_at: '2026-04-24T12:10:00',
          reviewed_at: null,
          deleted_at: null,
        },
      ],
    })
    ;(getDraft as Mock).mockResolvedValueOnce({
      id: 32,
      chart_hash: 'hash-001',
      provider: 'openai',
      model: 'gpt-test',
      prompt_version: 'v1',
      draft_text: '待审核草稿',
      status: 'pending_review',
      reviewer: '',
      reviewer_notes: '',
      input_tokens: 10,
      output_tokens: 20,
      cost_usd_estimate: 0.01,
      created_at: '2026-04-24T12:10:00',
      reviewed_at: null,
      deleted_at: null,
    })
    ;(updateDraft as Mock).mockResolvedValueOnce({
      id: 32,
      chart_hash: 'hash-001',
      provider: 'openai',
      model: 'gpt-test',
      prompt_version: 'v1',
      draft_text: '待审核草稿',
      status: 'approved',
      reviewer: 'reviewer',
      reviewer_notes: '',
      input_tokens: 10,
      output_tokens: 20,
      cost_usd_estimate: 0.01,
      created_at: '2026-04-24T12:10:00',
      reviewed_at: '2026-04-24T12:12:00',
      deleted_at: null,
    })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 32,
          chart_hash: 'hash-001',
          provider: 'openai',
          model: 'gpt-test',
          prompt_version: 'v1',
          draft_text: '待审核草稿',
          status: 'approved',
          reviewer: 'reviewer',
          reviewer_notes: '',
          input_tokens: 10,
          output_tokens: 20,
          cost_usd_estimate: 0.01,
          created_at: '2026-04-24T12:10:00',
          reviewed_at: '2026-04-24T12:12:00',
          deleted_at: null,
        },
      ],
    })

    const wrapper = await mountWithResult()
    const btn = wrapper.findAll('button').find((b) => b.text().includes('AI 草稿'))
    await btn!.trigger('click')
    await flushPromises()

    await wrapper.find('.lzp-item').trigger('click')
    await flushPromises()
    await wrapper.find('.lzp-btn-ok').trigger('click')
    await flushPromises()

    expect(getDraft).toHaveBeenCalledWith(32)
    expect(updateDraft).toHaveBeenCalledWith(32, expect.objectContaining({ status: 'approved' }))
    expect(wrapper.text()).toContain('草稿已通过')
  })

  it('可复制当前草稿并保存 reviewer notes', async () => {
    ;(getLlmConfig as Mock).mockResolvedValueOnce({ provider: 'openai', model: 'gpt-test' })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 33,
          chart_hash: 'hash-001',
          provider: 'openai',
          model: 'gpt-test',
          prompt_version: 'v1',
          draft_text: '需要补充细节的草稿',
          status: 'pending_review',
          reviewer: '',
          reviewer_notes: '',
          input_tokens: 10,
          output_tokens: 20,
          cost_usd_estimate: 0.01,
          created_at: '2026-04-24T12:20:00',
          reviewed_at: null,
          deleted_at: null,
        },
      ],
    })
    ;(getDraft as Mock).mockResolvedValueOnce({
      id: 33,
      chart_hash: 'hash-001',
      provider: 'openai',
      model: 'gpt-test',
      prompt_version: 'v1',
      draft_text: '需要补充细节的草稿',
      status: 'pending_review',
      reviewer: '',
      reviewer_notes: '',
      input_tokens: 10,
      output_tokens: 20,
      cost_usd_estimate: 0.01,
      created_at: '2026-04-24T12:20:00',
      reviewed_at: null,
      deleted_at: null,
    })
    ;(updateDraft as Mock).mockResolvedValueOnce({
      id: 33,
      chart_hash: 'hash-001',
      provider: 'openai',
      model: 'gpt-test',
      prompt_version: 'v1',
      draft_text: '需要补充细节的草稿',
      status: 'pending_review',
      reviewer: 'reviewer',
      reviewer_notes: '请补充事业与关系层的证据链。',
      input_tokens: 10,
      output_tokens: 20,
      cost_usd_estimate: 0.01,
      created_at: '2026-04-24T12:20:00',
      reviewed_at: null,
      deleted_at: null,
    })
    ;(fetchDrafts as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 33,
          chart_hash: 'hash-001',
          provider: 'openai',
          model: 'gpt-test',
          prompt_version: 'v1',
          draft_text: '需要补充细节的草稿',
          status: 'pending_review',
          reviewer: 'reviewer',
          reviewer_notes: '请补充事业与关系层的证据链。',
          input_tokens: 10,
          output_tokens: 20,
          cost_usd_estimate: 0.01,
          created_at: '2026-04-24T12:20:00',
          reviewed_at: null,
          deleted_at: null,
        },
      ],
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('AI 草稿'))!.trigger('click')
    await flushPromises()

    await wrapper.find('.lzp-item').trigger('click')
    await flushPromises()

    await wrapper.findAll('.lzp-btn').find((b) => b.text().includes('复制草稿'))!.trigger('click')
    expect(window.navigator.clipboard.writeText).toHaveBeenCalledWith('需要补充细节的草稿')

    await wrapper.find('.lzp-reviewer-notes').setValue('请补充事业与关系层的证据链。')
    await wrapper.findAll('.lzp-btn').find((b) => b.text().includes('保存备注'))!.trigger('click')
    await flushPromises()

    expect(updateDraft).toHaveBeenCalledWith(33, expect.objectContaining({ reviewer_notes: '请补充事业与关系层的证据链。' }))
    expect(wrapper.text()).toContain('reviewer notes 已保存')
  })
})

describe('ZiweiView — 运营面板与批量排盘', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('alert', vi.fn())
    vi.stubGlobal('confirm', vi.fn(() => true))
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:mock-url'),
      revokeObjectURL: vi.fn(),
    })
  })

  it('可打开运营面板并加载统计与实验列表', async () => {
    ;(getAdminStats as Mock).mockResolvedValueOnce({
      users: { total: 10, active: 7, inactive: 3 },
      audit_logs: { total: 12 },
      cases: { total: 8 },
      snapshots: { total: 16 },
      chart_cases: { total: 4 },
      reviews: { total: 5, pending: 2, approved: 2, rejected: 1, revised: 0 },
      api_keys: { total: 3 },
      experiments: { total: 2, running: 1, total_events: 15 },
      top_patterns: [{ name: '紫府同宫', count: 3 }],
      top_wuxing: [{ name: '木三局', count: 4 }],
      generated_at: '2026-04-24T13:00:00',
    })
    ;(listExperiments as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 41,
          name: '首页标题试验',
          description: '对照不同命盘摘要标题',
          status: 'running',
          variants: [
            { name: 'control', description: '对照组', weight: 50 },
            { name: 'variant_a', description: '实验组', weight: 50 },
          ],
          target_metric: 'conversion',
          hypothesis: '标题更聚焦会提升点击率',
          min_sample_size: 100,
          created_at: '2026-04-24T13:00:00',
          updated_at: '2026-04-24T13:00:00',
        },
      ],
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('运营'))!.trigger('click')
    await flushPromises()

    expect(getAdminStats).toHaveBeenCalledOnce()
    expect(listExperiments).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('运营面板')
    expect(wrapper.text()).toContain('总用户')
    expect(wrapper.text()).toContain('首页标题试验')
  })

  it('可在运营面板创建实验并查看结果', async () => {
    ;(getAdminStats as Mock).mockResolvedValueOnce({
      users: { total: 1, active: 1, inactive: 0 }, audit_logs: { total: 0 }, cases: { total: 1 }, snapshots: { total: 1 }, chart_cases: { total: 1 },
      reviews: { total: 0, pending: 0, approved: 0, rejected: 0, revised: 0 }, api_keys: { total: 0 }, experiments: { total: 0, running: 0, total_events: 0 },
      top_patterns: [], top_wuxing: [], generated_at: '2026-04-24T13:10:00',
    })
    ;(listExperiments as Mock).mockResolvedValueOnce({ total: 0, items: [] })
    ;(createExperiment as Mock).mockResolvedValueOnce({ id: 42 })
    ;(getAdminStats as Mock).mockResolvedValueOnce({
      users: { total: 1, active: 1, inactive: 0 }, audit_logs: { total: 0 }, cases: { total: 1 }, snapshots: { total: 1 }, chart_cases: { total: 1 },
      reviews: { total: 0, pending: 0, approved: 0, rejected: 0, revised: 0 }, api_keys: { total: 0 }, experiments: { total: 1, running: 0, total_events: 0 },
      top_patterns: [], top_wuxing: [], generated_at: '2026-04-24T13:11:00',
    })
    ;(listExperiments as Mock).mockResolvedValueOnce({
      total: 1,
      items: [
        {
          id: 42,
          name: '新实验',
          description: '描述',
          status: 'draft',
          variants: [
            { name: 'control', description: '对照组', weight: 50 },
            { name: 'variant_a', description: '实验组', weight: 50 },
          ],
          target_metric: 'conversion',
          hypothesis: '假设',
          min_sample_size: 100,
          created_at: '2026-04-24T13:11:00',
          updated_at: '2026-04-24T13:11:00',
        },
      ],
    })
    ;(getExperimentResults as Mock).mockResolvedValueOnce({
      experiment_id: 42,
      experiment_name: '新实验',
      status: 'draft',
      target_metric: 'conversion',
      min_sample_size: 100,
      total_assigned: 30,
      variants: [
        { variant: 'control', assigned: 15, conversions: 4, conversion_rate: 0.2667, other_events: {} },
        { variant: 'variant_a', assigned: 15, conversions: 6, conversion_rate: 0.4, other_events: {} },
      ],
      winner: 'variant_a',
      note: '实验组表现更好',
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('运营'))!.trigger('click')
    await flushPromises()

    await wrapper.findAll('.ozp-btn-soft').find((b) => b.text().includes('新建实验'))!.trigger('click')
    await wrapper.find('.ozp-input').setValue('新实验')
    await wrapper.findAll('.ozp-input')[1].setValue('conversion')
    await wrapper.findAll('.ozp-textarea')[0].setValue('描述')
    await wrapper.findAll('.ozp-textarea')[1].setValue('假设')
    await wrapper.findAll('.ozp-btn').find((b) => b.text().includes('创建实验'))!.trigger('click')
    await flushPromises()

    expect(createExperiment).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('新实验')

    await wrapper.findAll('.ozp-btn-soft').find((b) => b.text().includes('结果'))!.trigger('click')
    await flushPromises()

    expect(getExperimentResults).toHaveBeenCalledWith(42)
    expect(wrapper.text()).toContain('实验组表现更好')
  })

  it('可上传 CSV 并触发批量排盘', async () => {
    ;(ziweiBatch as Mock).mockResolvedValueOnce(new Blob(['zip-data'], { type: 'application/zip' }))

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('批量'))!.trigger('click')
    await flushPromises()

    const file = new File(['name,year\n张三,1990'], 'batch.csv', { type: 'text/csv' })
    const fileInput = wrapper.find('.bzp-file-input')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await fileInput.trigger('change')
    await flushPromises()

    await wrapper.findAll('.bzp-btn').find((b) => b.text().includes('开始批量排盘'))!.trigger('click')
    await flushPromises()

    expect(ziweiBatch).toHaveBeenCalledWith(file, undefined)
    expect(wrapper.text()).toContain('ZIP 已开始下载')
  })
})

describe('ZiweiView — 词汇工具与多人合盘', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('alert', vi.fn())
    Object.defineProperty(window.navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    })
  })

  it('可打开词汇工具并加载术语列表', async () => {
    ;(getGlossary as Mock).mockResolvedValueOnce([
      {
        term: '紫府同宫',
        pinyin: 'zi fu tong gong',
        definition: '紫微与天府同入一宫的格局。',
        category: '格局',
        classic_source: '紫微斗数全书',
      },
    ])

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('词汇'))!.trigger('click')
    await flushPromises()

    expect(getGlossary).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('词汇工具')
    expect(wrapper.text()).toContain('紫府同宫')
    expect(wrapper.text()).toContain('紫微斗数全书')
  })

  it('可复制词汇并通过相关词条再次检索', async () => {
    ;(getGlossary as Mock)
      .mockResolvedValueOnce([
        {
          term: '紫府同宫',
          pinyin: 'zi fu tong gong',
          definition: '紫微与天府同入一宫的格局。',
          category: '格局',
          classic_source: '紫微斗数全书',
        },
        {
          term: '天府',
          pinyin: 'tian fu',
          definition: '主库藏与稳定，也常见于紫府同宫。',
          category: '格局',
        },
      ])
      .mockResolvedValueOnce([
        {
          term: '天府',
          pinyin: 'tian fu',
          definition: '主库藏与稳定。',
          category: '格局',
        },
      ])

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('词汇'))!.trigger('click')
    await flushPromises()

    await wrapper.find('.gzp-copy-btn').trigger('click')
    expect(window.navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('紫府同宫'))
    expect(wrapper.text()).toContain('已复制术语：紫府同宫')

    const relatedButton = wrapper.findAll('.gzp-related-chip').find((b) => b.text().includes('天府'))
    expect(relatedButton).toBeTruthy()
    await relatedButton!.trigger('click')
    await flushPromises()

    expect(getGlossary).toHaveBeenLastCalledWith(expect.objectContaining({ q: '天府' }))
  })

  it('可提交多人合盘并显示缘分矩阵', async () => {
    ;(ziweiMultiCompat as Mock).mockResolvedValueOnce({
      person_count: 2,
      team_harmony_score: 82,
      matrix: [
        [0, 82],
        [82, 0],
      ],
      pairs: [
        {
          person_a_idx: 0,
          person_b_idx: 1,
          total_score: 82,
          max_score: 100,
          level: '良好',
        },
      ],
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('多人合盘'))!.trigger('click')
    await flushPromises()

    await wrapper.findAll('.mcz-btn').find((b) => b.text().includes('计算缘分矩阵'))!.trigger('click')
    await flushPromises()

    expect(ziweiMultiCompat).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('团队和谐指数')
    expect(wrapper.text()).toContain('82')
    expect(wrapper.text()).toContain('良好')
    expect(wrapper.text()).toContain('优先查看高亮最佳组合')
    expect(wrapper.text()).toContain('图例说明')
    expect(wrapper.text()).toContain('85+ 高契合')
    expect(wrapper.text()).toContain('行动建议')
    expect(wrapper.text()).toContain('适合稳定配合')
    expect(wrapper.find('.mcz-summary-banner').text()).toContain('当前最佳组合')
    expect(wrapper.findAll('.mcz-matrix td').some((cell) => cell.classes().includes('is-best-pair'))).toBe(true)
  })
})

describe('ZiweiView — 风水助手', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('可打开风水面板并加载命卦分析', async () => {
    ;(getFengshuiOptions as Mock).mockResolvedValueOnce({
      house_facing_options: { N: '坐南朝北', S: '坐北朝南' },
      directions_zh: { N: '北', S: '南', E: '东', W: '西', NE: '东北', NW: '西北', SE: '东南', SW: '西南' },
      room_type_options: { study: '书房', master_bedroom: '主卧' },
    })
    ;(fetchFengshuiBagua as Mock).mockResolvedValueOnce({
      life_gua: 1,
      gua_name: '坎',
      gua_element: '水',
      group: '东四命',
      birth_year: 2002,
      gender: '女',
      auspicious: [{ direction: 'S', direction_zh: '南', label: '生气', level: '最吉', level_css: 'ji1', desc: '利事业' }],
      inauspicious: [{ direction: 'N', direction_zh: '北', label: '绝命', level: '最凶', level_css: 'xiong1', desc: '需回避' }],
      bed_tip: { item: '床头朝向', direction: 'S', direction_zh: '南', label: '生气', reason: '有助休息' },
      desk_tip: null,
      door_tip: null,
      house_facing: null,
      house_gua: null,
      house_gua_name: null,
      house_group: null,
      compatibility: '相合',
      compatibility_note: '命宅相配',
      disclaimer: '仅供参考',
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('风水'))!.trigger('click')
    await flushPromises()

    expect(getFengshuiOptions).toHaveBeenCalledOnce()
    expect(fetchFengshuiBagua).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('风水助手')
    expect(wrapper.text()).toContain('坎命')
    expect(wrapper.text()).toContain('生气')
    expect(wrapper.text()).toContain('方位图例')
    expect(wrapper.text()).toContain('南 · 生气')
  })

  it('可提交房间布局评估', async () => {
    ;(getFengshuiOptions as Mock).mockResolvedValueOnce({
      house_facing_options: { N: '坐南朝北', S: '坐北朝南' },
      directions_zh: { N: '北', S: '南', E: '东', W: '西', NE: '东北', NW: '西北', SE: '东南', SW: '西南' },
      room_type_options: { study: '书房', master_bedroom: '主卧' },
    })
    ;(fetchFengshuiBagua as Mock).mockResolvedValueOnce({
      life_gua: 1,
      gua_name: '坎',
      gua_element: '水',
      group: '东四命',
      birth_year: 2002,
      gender: '女',
      auspicious: [],
      inauspicious: [],
      bed_tip: null,
      desk_tip: null,
      door_tip: null,
      house_facing: null,
      house_gua: null,
      house_gua_name: null,
      house_group: null,
      compatibility: null,
      compatibility_note: null,
      disclaimer: '仅供参考',
    })
    ;(analyzeRoomLayout as Mock).mockResolvedValueOnce({
      life_gua: 1,
      gua_name: '坎',
      score: 88,
      grade: '优秀',
      grade_css: 'excellent',
      cells: [
        {
          direction: 'N',
          direction_zh: '北',
          label: '生气',
          level_css: 'ji1',
          room_type: 'study',
          room_zh: '书房',
          assess_level: 'excellent',
          assess_score: 90,
          assess_note: '布局较佳',
        },
        {
          direction: 'S',
          direction_zh: '南',
          label: '绝命',
          level_css: 'xiong1',
          room_type: 'master_bedroom',
          room_zh: '主卧',
          assess_level: 'fair',
          assess_score: 58,
          assess_note: '不宜久居',
        },
      ],
      suggestions: ['书房适合放在北方位。'],
      disclaimer: '仅供参考',
    })

    const wrapper = await mountWithResult()
    await wrapper.findAll('button').find((b) => b.text().includes('风水'))!.trigger('click')
    await flushPromises()

    const roomSelect = wrapper.findAll('.fsp-room-select')[0]
    await roomSelect.setValue('study')
    await wrapper.findAll('.fsp-btn-soft').find((b) => b.text().includes('评估布局'))!.trigger('click')
    await flushPromises()

    expect(analyzeRoomLayout).toHaveBeenCalledWith(expect.objectContaining({
      rooms: expect.objectContaining({ N: 'study' }),
    }))
    expect(wrapper.text()).toContain('优秀')
    expect(wrapper.text()).toContain('书房适合放在北方位')
    expect(wrapper.text()).toContain('推荐房型')
    expect(wrapper.text()).toContain('北适合书房（90分）')
    expect(wrapper.text()).toContain('避开房型')
    expect(wrapper.text()).toContain('南暂不宜放主卧（不宜久居）')
    expect(wrapper.find('.fsp-layout-board').exists()).toBe(true)
    expect(wrapper.findAll('.fsp-layout-cell').length).toBe(9)
  })
})
