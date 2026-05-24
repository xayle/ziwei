/**
 * AdminView.spec.ts — 管理后台视图单元测试
 * 测试：Tab 切换、仪表盘渲染、案例列表、审计日志过滤和加载更多
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import AdminView from '@/views/AdminView.vue'

// ── API mock ─────────────────────────────────────────────
vi.mock('@/api/admin', () => ({
  getDashboard: vi.fn(),
  getAuditLogs: vi.fn(),
  getCases: vi.fn(),
  deleteCase: vi.fn(),
  listReviews: vi.fn(),
  getReviewStats: vi.fn(),
  updateReview: vi.fn(),
  deleteReview: vi.fn(),
  listExperiments: vi.fn(),
  deleteExperiment: vi.fn(),
  getExperimentResults: vi.fn(),
  listApiKeys: vi.fn(),
  createApiKey: vi.fn(),
  revokeApiKey: vi.fn(),
  getRules: vi.fn(),
  updateRules: vi.fn(),
  getRemediesRules: vi.fn(),
  updateRemediesRules: vi.fn(),
}))

vi.mock('@/api/events', () => ({
  getEventStats: vi.fn(),
  listEvents: vi.fn(),
}))

vi.mock('@/api/bazi', () => ({
  getGoldenCases: vi.fn(),
}))

vi.mock('@/api/static-data', () => ({
  getGlossary: vi.fn(),
  updateGlossaryTerm: vi.fn(),
}))

import { getDashboard, getAuditLogs, getCases, deleteCase } from '@/api/admin'
import { getEventStats, listEvents } from '@/api/events'
import { getGoldenCases } from '@/api/bazi'
import { getGlossary, updateGlossaryTerm } from '@/api/static-data'
import type { Mock } from 'vitest'

// ── 测试数据 ─────────────────────────────────────────────
const MOCK_DASHBOARD = {
  cases_total: 42, cases_this_month: 7,
  snapshots_total: 128, snapshots_this_month: 15,
  reviews_pending: 3, reviews_approved: 20,
  reviews_rejected: 2, reviews_revised: 1,
  daily_activity: [
    { date: '2026-03-20', count: 5 }, { date: '2026-03-21', count: 3 },
    { date: '2026-03-22', count: 8 }, { date: '2026-03-23', count: 2 },
    { date: '2026-03-24', count: 6 }, { date: '2026-03-25', count: 4 },
    { date: '2026-03-26', count: 9 },
  ],
  recent_cases: [
    { case_id: 'c1', name: '张三', created_at: '2026-03-25T10:00:00Z' },
  ],
  generated_at: '2026-03-26T00:00:00Z',
  owner_id: 1,
}

const MOCK_CASES = {
  items: [
    { id: 'c1', name: '张三命盘', tags: ['八字'], created_at: '2026-03-25T10:00:00Z',
      updated_at: '2026-03-25T10:00:00Z', last_snapshot_at: null },
    { id: 'c2', name: '李四紫微', tags: null, created_at: '2026-03-24T08:00:00Z',
      updated_at: '2026-03-24T08:00:00Z', last_snapshot_at: null },
  ],
  total: 2,
  next_cursor: null,
}

const MOCK_AUDIT = {
  items: [
    { id: 101, user_id: 1, action: 'create_case', resource_type: 'case',
      resource_id: 'c1', details: null, ip_address: '127.0.0.1',
      status: 'success', created_at: '2026-03-26T10:00:00Z' },
  ],
  total: 1,
  next_cursor: null,
}

const MOCK_EVENT_STATS = {
  total: 3,
  by_type: [
    { event_type: 'marriage', count: 2 },
    { event_type: 'career', count: 1 },
  ],
}

const MOCK_EVENTS = {
  items: [
    { id: 1, owner_id: 1, member_id: 11, name: '结婚择日', event_type: 'marriage', bazi_json: '{}', pillars_primary: null, ten_gods: null, five_elements: null, L_level: 3, confidence_score: 0.9, recommendation: null, recommendation_engine: null, created_at: '2026-03-26T10:00:00Z', updated_at: '2026-03-26T10:00:00Z' },
  ],
  total: 1,
  next_cursor: null,
}

const MOCK_GOLDEN = {
  total: 1,
  cases: [
    { id: 'gold-1', birth_dt_local: '1990-01-15T08:30:00', gender: 'male', lon: 116.41, note: '经典官格案例', created_at: '2026-03-20T08:00:00Z' },
  ],
}

const MOCK_GLOSSARY = [
  { term: '七杀', pinyin: 'qi sha', definition: '克我之偏官，主压力与执行力。', category: '十神', classic_source: '《滴天髓》' },
]

async function mountView() {
  const freshRouter = createRouter({
    history: createWebHistory(),
    routes: [{ path: '/admin', component: AdminView }],
  })
  await freshRouter.push('/admin')
  await freshRouter.isReady()
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(AdminView, {
    global: { plugins: [pinia, freshRouter], stubs: { teleport: true } },
  })
}

describe('AdminView — 初始加载（仪表盘 Tab）', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('onMounted 时自动调用 getDashboard()', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    await mountView()
    await flushPromises()
    expect(getDashboard).toHaveBeenCalledOnce()
  })

  it('渲染统计卡数字', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('42')   // cases_total
    expect(wrapper.text()).toContain('128')  // snapshots_total
    expect(wrapper.text()).toContain('3')    // reviews_pending
  })

  it('加载失败时显示错误提示', async () => {
    ;(getDashboard as Mock).mockRejectedValueOnce(new Error('network'))
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('加载失败')
  })

  it('渲染最近案例表格', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('张三')
  })
})

describe('AdminView — Tab 切换 → 案例管理', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换到案例 Tab 自动加载案例列表', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getCases as Mock).mockResolvedValueOnce(MOCK_CASES)

    const wrapper = await mountView()
    await flushPromises()

    const tabBtns = wrapper.findAll('.tab-btn')
    const caseTab = tabBtns.find(b => b.text().includes('案例'))
    expect(caseTab).toBeDefined()
    await caseTab!.trigger('click')
    await flushPromises()

    expect(getCases).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('张三命盘')
    expect(wrapper.text()).toContain('李四紫微')
  })

  it('重复切换不重复加载', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getCases as Mock).mockResolvedValue(MOCK_CASES)

    const wrapper = await mountView()
    await flushPromises()

    const tabBtns = wrapper.findAll('.tab-btn')
    const caseTab = tabBtns.find(b => b.text().includes('案例'))!
    await caseTab.trigger('click')
    await flushPromises()
    await caseTab.trigger('click')  // 再点一次
    await flushPromises()

    // 第二次点击时 casesLoaded=true，不应再次触发 loadCases（仅刷新按钮才会）
    expect(getCases).toHaveBeenCalledTimes(1)
  })
})

describe('AdminView — Tab 切换 → 审计日志', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换到审计 Tab 自动加载日志', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getAuditLogs as Mock).mockResolvedValueOnce(MOCK_AUDIT)

    const wrapper = await mountView()
    await flushPromises()

    const tabBtns = wrapper.findAll('.tab-btn')
    const auditTab = tabBtns.find(b => b.text().includes('审计'))
    expect(auditTab).toBeDefined()
    await auditTab!.trigger('click')
    await flushPromises()

    expect(getAuditLogs).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('create_case')
    expect(wrapper.text()).toContain('success')
  })
})

describe('AdminView — 案例删除', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('点删除后从列表移除该案例', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getCases as Mock).mockResolvedValueOnce(MOCK_CASES)
    ;(deleteCase as Mock).mockResolvedValueOnce(undefined)

    // 模拟 confirm 返回 true
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true)

    const wrapper = await mountView()
    await flushPromises()

    // 先切换到案例 Tab
    const caseTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('案例'))!
    await caseTab.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('张三命盘')

    // 点击第一行删除按钮
    const delBtns = wrapper.findAll('.btn-danger')
    await delBtns[0].trigger('click')
    await flushPromises()

    expect(deleteCase).toHaveBeenCalledWith('c1')
    expect(wrapper.text()).not.toContain('张三命盘')
  })

  it('confirm 取消时不调用 deleteCase', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getCases as Mock).mockResolvedValueOnce(MOCK_CASES)
    vi.spyOn(window, 'confirm').mockReturnValueOnce(false)

    const wrapper = await mountView()
    await flushPromises()

    const caseTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('案例'))!
    await caseTab.trigger('click')
    await flushPromises()

    const delBtns = wrapper.findAll('.btn-danger')
    await delBtns[0].trigger('click')
    await flushPromises()

    expect(deleteCase).not.toHaveBeenCalled()
  })
})

describe('AdminView — Tab 切换 → 事件统计', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换到事件统计 Tab 自动加载统计与事件列表', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getEventStats as Mock).mockResolvedValueOnce(MOCK_EVENT_STATS)
    ;(listEvents as Mock).mockResolvedValueOnce(MOCK_EVENTS)

    const wrapper = await mountView()
    await flushPromises()

    const eventTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('事件统计'))
    expect(eventTab).toBeDefined()
    await eventTab!.trigger('click')
    await flushPromises()

    expect(getEventStats).toHaveBeenCalledOnce()
    expect(listEvents).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('marriage')
    expect(wrapper.text()).toContain('结婚择日')
  })
})

describe('AdminView — Tab 切换 → 黄金案例', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换到黄金案例 Tab 自动加载案例库', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getGoldenCases as Mock).mockResolvedValueOnce(MOCK_GOLDEN)

    const wrapper = await mountView()
    await flushPromises()

    const goldenTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('黄金案例'))
    expect(goldenTab).toBeDefined()
    await goldenTab!.trigger('click')
    await flushPromises()

    expect(getGoldenCases).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('经典官格案例')
    expect(wrapper.text()).toContain('1990-01-15T08:30:00')
  })
})

describe('AdminView — Tab 切换 → 词汇管理', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('切换到词汇管理 Tab 自动加载术语列表', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getGlossary as Mock).mockResolvedValueOnce(MOCK_GLOSSARY)

    const wrapper = await mountView()
    await flushPromises()

    const glossaryTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('词汇管理'))
    expect(glossaryTab).toBeDefined()
    await glossaryTab!.trigger('click')
    await flushPromises()

    expect(getGlossary).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('七杀')
    expect(wrapper.text()).toContain('《滴天髓》')
  })

  it('编辑词汇后调用 updateGlossaryTerm 保存', async () => {
    ;(getDashboard as Mock).mockResolvedValueOnce(MOCK_DASHBOARD)
    ;(getGlossary as Mock).mockResolvedValueOnce(MOCK_GLOSSARY)
    ;(updateGlossaryTerm as Mock).mockResolvedValueOnce({
      ...MOCK_GLOSSARY[0],
      definition: '更新后的定义',
    })

    const wrapper = await mountView()
    await flushPromises()

    const glossaryTab = wrapper.findAll('.tab-btn').find(b => b.text().includes('词汇管理'))!
    await glossaryTab.trigger('click')
    await flushPromises()

    const editBtn = wrapper.findAll('.btn-sec').find(b => b.text().includes('编辑'))
    expect(editBtn).toBeDefined()
    await editBtn!.trigger('click')
    await flushPromises()

    const textareas = wrapper.findAll('.admin-form-textarea')
    await textareas[0].setValue('更新后的定义')
    const modalButtons = wrapper.findAll('.admin-modal-actions .btn-sec')
    await modalButtons[1].trigger('click')
    await flushPromises()

    expect(updateGlossaryTerm).toHaveBeenCalledOnce()
    expect(updateGlossaryTerm).toHaveBeenCalledWith('七杀', expect.objectContaining({
      definition: '更新后的定义',
      pinyin: 'qi sha',
      classic_source: '《滴天髓》',
    }))
    expect(wrapper.text()).toContain('更新后的定义')
  })
})
