import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkbenchView from '@/views/WorkbenchView.vue'

const CURRENT_YEAR = new Date().getFullYear()
const CURRENT_MONTH = new Date().getMonth() + 1
const TARGET_MONTH = CURRENT_MONTH === 12 ? 11 : CURRENT_MONTH + 1

const mockCtx = vi.hoisted(() => {
  const routerPush = vi.fn()
  const aiSetCurrentCase = vi.fn()
  const loadCaseList = vi.fn(async () => {})
  const createCase = vi.fn()
  const computeFullBazi = vi.fn()
  const computeZiwei = vi.fn()
  const getJieqi = vi.fn()
  const getWesternChart = vi.fn()

  const reportStore = {
    caseList: [] as any[],
    loadCaseList,
  }

  const navStore = {
    currentSectionId: 'ziwei-overview' as string | null,
    currentSection: { label: '紫微总览' } as { label: string } | null,
    selectSection: vi.fn((id: string) => {
      navStore.currentSectionId = id
    }),
  }

  const uiStore = {
    rightPanelExpanded: false,
  }

  const aiStore = {
    setCurrentCase: aiSetCurrentCase,
  }

  const profileStore = {
    saved: false,
    surname: '',
    birthDt: '',
    lon: undefined as number | undefined,
    tz: '',
    gender: null as string | null,
    cityName: '',
    solarTime: false,
  }

  return {
    routerPush,
    aiSetCurrentCase,
    loadCaseList,
    createCase,
    computeFullBazi,
    computeZiwei,
    getJieqi,
    getWesternChart,
    reportStore,
    navStore,
    uiStore,
    aiStore,
    profileStore,
  }
})

const {
  routerPush,
  aiSetCurrentCase,
  loadCaseList,
  createCase,
  computeFullBazi,
  computeZiwei,
  getJieqi,
  getWesternChart,
  reportStore,
  navStore,
  uiStore,
  aiStore,
  profileStore,
} = mockCtx

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockCtx.routerPush }),
  useRoute: () => ({ path: '/workbench', query: {}, params: {} }),
}))

vi.mock('@/stores/report', () => ({
  useReportStore: () => mockCtx.reportStore,
}))

vi.mock('@/stores/ai', () => ({
  useAiStore: () => mockCtx.aiStore,
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => mockCtx.uiStore,
}))

vi.mock('@/stores/nav', () => ({
  useNavStore: () => mockCtx.navStore,
}))

vi.mock('@/stores/profile', () => ({
  useProfileStore: () => mockCtx.profileStore,
}))

vi.mock('@/api/report', () => ({
  computeFullBazi: mockCtx.computeFullBazi,
  computeZiwei: mockCtx.computeZiwei,
  createCase: mockCtx.createCase,
  updateCase: vi.fn(),
  deleteCase: vi.fn(),
  createShareToken: vi.fn(),
}))

vi.mock('@/api/export', () => ({
  exportCaseJson: vi.fn(),
  exportCasePdf: vi.fn(),
  downloadBlob: vi.fn(),
}))

vi.mock('@/api/snapshots', () => ({
  listSnapshots: vi.fn(async () => []),
}))

vi.mock('@/api/bazi', () => ({
  getJieqi: mockCtx.getJieqi,
}))

vi.mock('@/api/western', () => ({
  getWesternChart: mockCtx.getWesternChart,
}))

vi.mock('@/api/static-data', () => ({
  getCities: vi.fn(async () => []),
}))

const baseCases = [
  {
    id: 'case-1',
    name: '张三',
    gender: 'male',
    city: '上海',
    tz: 'Asia/Shanghai',
    lon: 121.47,
    solar_time_enabled: false,
    birth_dt_local: '1990-05-15T08:30:00',
    tags: ['重点'],
    notes: '首个案例',
  },
  {
    id: 'case-2',
    name: '李四',
    gender: 'female',
    city: '北京',
    tz: 'Asia/Shanghai',
    lon: 116.41,
    solar_time_enabled: true,
    birth_dt_local: '1992-08-20T19:20:00',
    tags: ['回访'],
    notes: '第二个案例',
  },
]

const baziMock = {
  request_id: 'req-001',
  pillars_primary: {
    year: { stem: '庚', branch: '午' },
    month: { stem: '辛', branch: '巳' },
    day: { stem: '甲', branch: '子' },
    hour: { stem: '丙', branch: '寅' },
  },
  ten_gods: {
    year: '七杀',
    month: '正官',
    day: '日主',
    hour: '食神',
  },
  dayun: {
    items: [
      {
        stem: '庚',
        branch: '寅',
        ganzhi: '庚寅',
        start_year: CURRENT_YEAR - 4,
        end_year: CURRENT_YEAR + 5,
        start_age: 31,
        ten_god: '正官',
        flow_wuxing: '木火',
        wealth_hint: '稳中有升',
        love_hint: '宜沟通',
        health_hint: '注意作息',
        narrative: '当前大运适合稳步推进核心事项。',
      },
      {
        stem: '辛',
        branch: '卯',
        ganzhi: '辛卯',
        start_year: CURRENT_YEAR + 6,
        end_year: CURRENT_YEAR + 15,
        start_age: 41,
        ten_god: '偏印',
        flow_wuxing: '金木',
        wealth_hint: '宜蓄势',
        love_hint: '节奏放缓',
        health_hint: '关注肩颈',
        narrative: '未来大运更适合蓄力与结构调整。',
      },
    ],
  },
  liunian: {
    items: [
      { year: CURRENT_YEAR - 1, stem: '乙', branch: '巳', ten_god: '正官' },
      { year: CURRENT_YEAR, stem: '丙', branch: '午', ten_god: '偏财' },
      { year: CURRENT_YEAR + 1, stem: '丁', branch: '未', ten_god: '食神' },
    ],
  },
  liunian_detail: [
    {
      year: CURRENT_YEAR - 1,
      annual_score: 70,
      ten_god: '正官',
      flow_wuxing: '木',
      clash: '轻冲',
      domain_forecasts: { 事业: '守成', 财运: '平稳' },
      tai_sui_relations: ['平'],
      clash_pillars: ['年柱'],
      notable_months: [Math.max(1, CURRENT_MONTH - 1)],
      optimal_action: '稳住基本盘',
      interpretation_text: '上一年以稳定收尾为主。',
      inference_tags: ['整理', '收尾'],
    },
    {
      year: CURRENT_YEAR,
      annual_score: 82,
      ten_god: '偏财',
      flow_wuxing: '火',
      clash: '冲月柱',
      domain_forecasts: { 事业: '推进', 财运: '回升' },
      tai_sui_relations: ['拱合'],
      clash_pillars: ['月柱'],
      notable_months: [TARGET_MONTH],
      optimal_action: '把握窗口期',
      interpretation_text: '今年适合主动推进重点事项。',
      inference_tags: ['扩张', '合作'],
    },
    {
      year: CURRENT_YEAR + 1,
      annual_score: 76,
      ten_god: '食神',
      flow_wuxing: '土',
      clash: '无明显冲克',
      domain_forecasts: { 事业: '转型', 财运: '观察' },
      tai_sui_relations: ['平'],
      clash_pillars: [],
      notable_months: [],
      optimal_action: '先做储备',
      interpretation_text: '明年适合先做调整与储备。',
      inference_tags: ['蓄势'],
    },
  ],
  monthly_fortune: [
    {
      month: Math.max(1, CURRENT_MONTH - 1),
      month_ganzhi: '己卯',
      month_dizhi: '卯',
      luck_level: '平',
      color_hint: '米白',
      relation_to_rizhu: '比和',
      tip: '适合复盘与整理。',
    },
    {
      month: CURRENT_MONTH,
      month_ganzhi: '庚辰',
      month_dizhi: '辰',
      luck_level: '吉',
      color_hint: '青绿',
      dayun_stem: '庚',
      relation_to_rizhu: '生扶',
      tip: '本月适合推进手头重点。',
      disclaimer: '月份提示需结合个人节奏使用。',
    },
    {
      month: TARGET_MONTH,
      month_ganzhi: '辛巳',
      month_dizhi: '巳',
      luck_level: '凶',
      color_hint: '深蓝',
      dayun_stem: '庚',
      relation_to_rizhu: '受制',
      clash_with: '月柱',
      tip: '宜放慢节奏，避免高风险决策。',
      disclaimer: '关键月仅作提示，仍需结合全盘判断。',
    },
  ],
  wuxing_score: { wood: 3.2, fire: 2.6, earth: 1.5, metal: 1.1, water: 0.9 },
  wuxing_balance_score: 68,
  balance_advice: '结构略偏燥，宜补水润局。',
  wuxing_weak: ['金', '水'],
  wuxing_strong: ['木', '火'],
  summary: '整体结构偏燥，宜补水润局。',
  this_year_detail: { interpretation_text: '今年以稳中求进、抓主线为先。' },
  fortune_summary: {
    this_year_domains: { 事业: '推进', 财运: '回升' },
    top3_actions: ['控制节奏', '优化协作'],
  },
  geju: {
    name: '正官格',
    level: '中上',
    geju_name: '正官格',
    geju_level: '中上',
    interpretation_text: '此局成于木火流通，宜稳中发力。',
  },
  yongshen: {
    favor: ['水', '金'],
    avoid: ['火'],
    rationale: '以水调候，以金佐之。',
    god_element: '水',
    star: '偏印',
  },
}

const ziweiMock = {
  summary: '命盘整体偏开创，适合主动推进。',
  patterns: [],
  lunar: { lunar_year: '甲辰', lunar_month: 3, lunar_day: 15 },
  template_version: 'standard',
  true_solar_time: '08:12',
  engine_version: '8.0',
  life_palace_gz: '命宫在午',
  body_palace_gz: '身宫在迁移',
  wuxing_ju_name: '火',
  wuxing_ju: 6,
  life_ruler_star: '贪狼',
  body_ruler_star: '天相',
  laiyin_palace: '财帛宫',
  dayun: {
    items: [
      { index: 0, ganzhi: '甲辰', start_age: 33, end_age: 42, start_year: CURRENT_YEAR - 1 },
      { index: 1, ganzhi: '乙巳', start_age: 43, end_age: 52, start_year: CURRENT_YEAR + 9 },
    ],
  },
  liunian: { year: CURRENT_YEAR, year_gz: '丙午' },
  liuyue: [
    { month: CURRENT_MONTH, month_name: `${CURRENT_MONTH}月`, month_gz: '丙辰', palace_name: '财帛', life_palace_branch: '卯' },
    { month: CURRENT_MONTH === 12 ? 1 : CURRENT_MONTH + 1, month_name: '下月', month_gz: '丁巳', palace_name: '迁移', life_palace_branch: '辰' },
  ],
  forecast: {
    yearly: { score: 86 },
    current_month: { score: 78 },
    monthly: [{ score: 72 }, { score: 78 }, { score: 76 }],
  },
  palaces: [
    {
      name: '命宫',
      stem: '甲',
      branch: '子',
      changsheng: '临官',
      aux_stars: [{ name: '左辅', brightness: '得', brightness_val: 4, transforms: [] }],
      main_stars: [{ name: '紫微', brightness: '庙', transforms: ['化科'] }],
      analysis: '先天主轴强。',
      suggestion: '宜稳中求进。',
      opposition_name: '迁移',
      flying_out: { 化科: '迁移' },
    },
    {
      name: '迁移',
      stem: '乙',
      branch: '丑',
      changsheng: '帝旺',
      aux_stars: [{ name: '文昌', brightness: '庙', brightness_val: 6, transforms: [] }],
      main_stars: [{ name: '破军', brightness: '平' }],
      analysis: '适合外拓与跑动。',
      opposition_name: '命宫',
      flying_out: { 化权: '命宫' },
    },
  ],
  remedies: [],
  life_suggestions: [],
}

function resetMocks() {
  reportStore.caseList = baseCases.map(item => ({ ...item }))
  navStore.currentSectionId = 'ziwei-overview'
  navStore.currentSection = { label: '紫微总览' }
  uiStore.rightPanelExpanded = false
  profileStore.saved = false
  profileStore.birthDt = ''
  profileStore.lon = undefined
  profileStore.tz = ''
  profileStore.gender = null
  profileStore.cityName = ''
  profileStore.solarTime = false
  localStorage.clear()
  vi.clearAllMocks()

  loadCaseList.mockResolvedValue(undefined)
  createCase.mockResolvedValue({ ...baseCases[0] })
  computeFullBazi.mockResolvedValue({ ...baziMock })
  computeZiwei.mockResolvedValue({ ...ziweiMock })
  getJieqi.mockResolvedValue({ items: [] })
  getWesternChart.mockResolvedValue({ planets: {}, houses: [], angles: {} })
}

async function mountView() {
  const wrapper = mount(WorkbenchView)
  await flushPromises()
  await flushPromises()
  return wrapper
}

describe('WorkbenchView', () => {
  beforeEach(resetMocks)

  it('进入紫微主盘页后自动选中首个案例并加载双盘数据', async () => {
    const wrapper = await mountView()

    expect(loadCaseList).toHaveBeenCalled()
    expect(computeFullBazi).toHaveBeenCalledTimes(1)
    expect(computeZiwei).toHaveBeenCalledTimes(1)
    expect(aiSetCurrentCase).toHaveBeenCalledWith('case-1')
    expect(aiSetCurrentCase).toHaveBeenCalledWith('case-1', 'req-001')

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('命宫在午')
    expect(wrapper.text()).toContain('双盘大运对照')
    expect(wrapper.text()).toContain('紫微：甲辰(33-42岁)')
    expect(wrapper.findAll('.wb-case-item')).toHaveLength(2)
  })

  it('点击案例列表后会切换当前案例并重新加载命盘', async () => {
    const wrapper = await mountView()
    computeFullBazi.mockClear()
    computeZiwei.mockClear()
    aiSetCurrentCase.mockClear()

    await wrapper.findAll('.wb-case-item')[1].trigger('click')
    await flushPromises()

    expect(computeFullBazi).toHaveBeenCalledTimes(1)
    expect(computeZiwei).toHaveBeenCalledTimes(1)
    expect(aiSetCurrentCase).toHaveBeenCalledWith('case-2')
    expect(aiSetCurrentCase).toHaveBeenCalledWith('case-2', 'req-001')
    expect(wrapper.find('.wb-info-name').text()).toBe('李四')
    expect(wrapper.find('.wb-case-item.active').text()).toContain('李四')
  })

  it('紫微计算失败时显示页面级错误态，并可点击重试', async () => {
    computeZiwei.mockRejectedValueOnce(new Error('紫微服务异常'))
    const wrapper = await mountView()

    expect(wrapper.find('.wb-error-card').exists()).toBe(true)
    expect(wrapper.find('.wb-error-card').text()).toContain('紫微服务异常')

    computeZiwei.mockResolvedValueOnce({ ...ziweiMock })
    computeFullBazi.mockResolvedValueOnce({ ...baziMock })
    await wrapper.find('.wb-error-card button').trigger('click')
    await flushPromises()

    expect(computeZiwei).toHaveBeenCalledTimes(2)
    expect(computeFullBazi).toHaveBeenCalledTimes(2)
  })

  it('非紫微章节会展示八字主线，并支持大运/流年/流月焦点切换', async () => {
    navStore.currentSectionId = 'overview'
    navStore.currentSection = { label: '综合总览' }

    const wrapper = await mountView()

    expect(wrapper.find('.wb-dayun-focus .wb-fortune-focus-title').text()).toContain('庚寅')
    expect(wrapper.find('.wb-liunian-focus .wb-fortune-focus-title').text()).toContain(String(CURRENT_YEAR))

    await wrapper.findAll('.wb-dayun-cell')[1].trigger('click')
    await flushPromises()
    expect(wrapper.find('.wb-dayun-focus .wb-fortune-focus-title').text()).toContain('辛卯')

    await wrapper.findAll('.wb-ly-cell')[2].trigger('click')
    await flushPromises()
    expect(wrapper.find('.wb-liunian-focus .wb-fortune-focus-title').text()).toContain(String(CURRENT_YEAR + 1))

    const targetMonthCell = wrapper.findAll('.wb-lm-hm-cell').find(cell => cell.text().includes(`${TARGET_MONTH}月`))
    expect(targetMonthCell).toBeTruthy()
    await targetMonthCell!.trigger('click')
    await flushPromises()

    expect(wrapper.find('.wb-liuyue-title').text()).toContain(`${TARGET_MONTH}月`)
  })

})
