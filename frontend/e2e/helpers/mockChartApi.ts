import type { Page } from '@playwright/test'
import { LIFE_VOLUME_LABELS } from '../../src/types/life-volume'

/** ≥300 城 mock，满足 citiesCache MIN_CITIES 与 E2E 建档选城 */
export const mockCitiesPayload = (() => {
  const municipalities = [
    { name: '北京', province: '北京市', lng: 116.4074, lat: 39.9042, city_type: '直辖市' },
    { name: '上海', province: '上海市', lng: 121.4737, lat: 31.2304, city_type: '直辖市' },
    { name: '天津', province: '天津市', lng: 117.2, lat: 39.12, city_type: '直辖市' },
    { name: '重庆', province: '重庆市', lng: 106.55, lat: 29.56, city_type: '直辖市' },
  ]
  const provinces = [
    '广东省', '四川省', '浙江省', '江苏省', '山东省', '河南省', '湖北省', '湖南省',
    '福建省', '安徽省', '江西省', '辽宁省', '吉林省', '黑龙江省', '陕西省', '甘肃省',
    '云南省', '贵州省', '海南省', '山西省', '河北省', '广西壮族自治区', '内蒙古自治区',
    '宁夏回族自治区', '新疆维吾尔自治区', '西藏自治区', '青海省',
  ]
  const rows = [...municipalities]
  let i = 0
  while (rows.length < 337) {
    const province = provinces[i % provinces.length]
    rows.push({
      name: `示例市${i + 1}`,
      province,
      lng: 100 + (i % 35),
      lat: 22 + (i % 18),
      city_type: '地级市',
    })
    i += 1
  }
  return rows
})()

export async function setupCitiesApiMock(page: Page) {
  await page.route('**/api/v1/cities**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockCitiesPayload),
    })
  })
}

export const mockBaziPayload = {
  pillars_primary: {
    year: { stem: '己', branch: '巳' },
    month: { stem: '丁', branch: '丑' },
    day: { stem: '甲', branch: '子' },
    hour: { stem: '戊', branch: '辰' },
  },
  ten_gods: { year: '正财', month: '伤官', hour: '偏财' },
  kongwang: ['戌', '亥'],
  pillar_details: {
    year: { hidden_stems: [{ stem: '丙', ten_god: '食神' }], xingyun: '帝旺', self_seat: '衰', nayin: '大林木', kongwang: ['戌', '亥'], shensha: [{ name: '天乙', polarity: '+' }, { name: '亡神', polarity: '-' }] },
    month: { hidden_stems: [{ stem: '癸', ten_god: '正印' }], xingyun: '墓', self_seat: '养', nayin: '涧下水', kongwang: ['申', '酉'], shensha: [{ name: '华盖', polarity: '+' }] },
    day: { hidden_stems: [{ stem: '癸', ten_god: '正印' }], xingyun: '沐浴', self_seat: '长生', nayin: '海中金', kongwang: ['戌', '亥'], shensha: [{ name: '将星', polarity: '+' }] },
    hour: { hidden_stems: [{ stem: '乙', ten_god: '劫财' }], xingyun: '衰', self_seat: '冠带', nayin: '大林木', kongwang: ['子', '丑'], shensha: [{ name: '驿马', polarity: '-' }] },
  },
  liunian: {
    items: [{
      year: 2026,
      stem: '丙',
      branch: '午',
      ten_god: '食神',
      nayin: '天河水',
      self_seat: '胎',
      xingyun: '临官',
      kongwang: ['辰', '巳'],
      hidden_stems: [{ stem: '丁', ten_god: '伤官' }, { stem: '己', ten_god: '正财' }],
      shensha: [{ name: '红鸾', polarity: '+' }],
    }],
  },
  current_fortune_summary: { current_liunian: '食神' },
  geju: {
    geju_name: '正官格',
    interpretation_text: 'E2E 测试格局说明。',
    engine_geju: '正官格',
    recorded_geju: '建禄格',
    dual_track_id: 'ZIP09',
    dual_track_note: '典籍口径与引擎格局不同，双轨并存。',
  },
  yongshen: { favor: ['wood', 'earth'], avoid: ['fire'] },
  wuxing_weak: ['wood'],
  wuxing_strong: ['earth'],
  day_master_strength: { tier: '中和' },
  personality: {
    day_stem_trait: '正直稳重',
    growth_advice: '宜深耕专业。',
    advantages: ['责任心'],
  },
  career: {
    career_score: 82,
    development_advice: '稳步晋升。',
    career_directions: ['技术', '管理'],
  },
  wealth_analysis: {
    wealth_tier: '中上',
    strategy: '长期积累。',
    industries: ['金融'],
  },
  marriage_analysis: {
    marriage_score: 76,
    interpretation_text: '宜晚婚。',
    marriage_windows: ['28-32岁'],
  },
  health: {
    risk_level: '低',
    health_advice: '注意作息。',
    risk_organs: ['肝'],
  },
  relationship: {
    relationship_score: 71,
    social_strategy: '以诚待人。',
    noble_people: ['长辈'],
  },
  lucky: {
    lucky_item: '水晶',
    interpretation_text: '宜静养。',
    lucky_colors: ['蓝', '黑'],
  },
  monthly_fortune: [
    { month: 1, luck_level: '平' },
    { month: 2, luck_level: '吉' },
  ],
  dayun: {
    items: [{
      start_year: 2020,
      stem: '辛',
      branch: '未',
      ten_god: '正官',
      nayin: '路旁土',
      self_seat: '养',
      xingyun: '冠带',
      kongwang: ['寅', '卯'],
      shensha: [{ name: '天德', polarity: '+' }],
      hidden_stems: [{ stem: '己', ten_god: '正财' }, { stem: '丁', ten_god: '食神' }],
    }],
  },
  shishen_summary: {
    dominant: ['正官', '正印'],
    score_share: { 正官: 0.32, 正印: 0.28, 偏财: 0.15 },
    hidden_contrib_by_ten_god: { 食神: 0.18, 正印: 0.26, 偏财: 0.12 },
  },
  bazi_summary: 'E2E 八字摘要。',
  validation: {
    level: 'L2',
    mode: 'dual',
    interpretation_enabled: true,
    reasons: ['near_shichen_boundary'],
  },
  confidence_level: 'medium',
  confidence_score: 72,
  provenance: {
    geju: { layer: 'classical', confidence: 0.9, note: '典籍口径' },
    dayun: { layer: 'engine', confidence: 0.85 },
  },
}

export const mockBaziDegradedPayload = {
  ...mockBaziPayload,
  missing_fields: ['hour_pillar', 'geju_detail'],
  validation: {
    level: 'degraded',
    mode: 'single',
    interpretation_enabled: false,
    reasons: ['时辰边界风险'],
  },
  confidence_level: 'low',
}

export const mockBaziExplainBatch = {
  chart_hash: 'e2e-bazi-hash',
  disclaimer_block: { text: '仅供文化研究参考，不构成决策建议。', version: '1.0' },
  sections: [
    {
      section_id: 'geju',
      blocks: [{ text: '正官格：月令本气透出。', layer: 'cite', classic_id: 'CL001' }],
    },
    {
      section_id: 'relations',
      blocks: [{ text: '年柱与月柱半合。', layer: 'fact' }],
    },
    {
      section_id: 'reading',
      blocks: [{ text: '先读盘面，再展开典籍与推断。', layer: 'fact' }],
    },
    {
      section_id: 'domains',
      blocks: [{ text: '事业宜深耕专业。', layer: 'inference' }],
    },
    {
      section_id: 'summary',
      blocks: [{ text: '综合平稳推进。', layer: 'inference' }],
    },
  ],
}

export const mockZiweiExplainBatch = {
  chart_hash: 'e2e-ziwei-hash',
  sections: [
    {
      section_id: 'palaces',
      blocks: [
        { text: '命宫 子：紫微', layer: 'fact' },
        { text: '紫微主贵气与主导性。', layer: 'inference' },
      ],
    },
    {
      section_id: 'reading',
      blocks: [{ text: '先读方盘，再展开宫论与典籍。', layer: 'fact' }],
    },
    {
      section_id: 'fortune',
      blocks: [{ text: '大限 3–12岁 命宫', layer: 'fact' }],
    },
  ],
}

export const mockZiweiPayload = {
  birth_solar: '1990-01-15 08:30',
  gender: '男',
  wuxing_ju: 2,
  wuxing_ju_name: '水二局',
  life_palace_gz: '甲子',
  body_palace_gz: '乙丑',
  life_palace_branch_idx: 0,
  body_palace_branch_idx: 1,
  life_ruler_star: '贪狼',
  body_ruler_star: '天相',
  true_solar_time: '1990-01-15 08:30',
  laiyin_palace: '寅',
  lunar: {
    year_gz: '己巳',
    month_gz: '丁丑',
    day_gz: '乙丑',
    hour_gz: '戊辰',
    hour_branch: '辰',
    jieqi_month_gz: '丁丑',
  },
  palaces: [
    { name: '命宫', stem: '甲', branch: '子', main_stars: [{ name: '紫微', brightness: '庙', brightness_val: 5, transforms: [] }] },
    { name: '兄弟宫', stem: '乙', branch: '丑', main_stars: [{ name: '天机', brightness: '旺', brightness_val: 4, transforms: [] }] },
    { name: '夫妻宫', stem: '丙', branch: '寅', main_stars: [] },
    { name: '子女宫', stem: '丁', branch: '卯', main_stars: [{ name: '太阳', brightness: '得', brightness_val: 3, transforms: [] }] },
    { name: '财帛宫', stem: '戊', branch: '辰', main_stars: [] },
    { name: '疾厄宫', stem: '己', branch: '巳', main_stars: [] },
    { name: '迁移宫', stem: '庚', branch: '午', main_stars: [] },
    { name: '交友宫', stem: '辛', branch: '未', main_stars: [] },
    { name: '官禄宫', stem: '壬', branch: '申', main_stars: [] },
    { name: '田宅宫', stem: '癸', branch: '酉', main_stars: [] },
    { name: '福德宫', stem: '甲', branch: '戌', main_stars: [] },
    { name: '父母宫', stem: '乙', branch: '亥', main_stars: [] },
  ],
  flying: null,
  template_version: 'standard',
  algorithm_version: 'e2e',
  engine_version: 'e2e',
  analysis: {},
  patterns: [{ name: '紫府朝垣', description: 'E2E 格局说明。', rule_id: 'ZRULE_007' }],
  summary: 'E2E 紫微摘要。',
  analysis_structured: [{
    palace_index: 0,
    palace_name: '命宫',
    conclusion: '主贵',
    explanation: '紫微坐命',
    suggestion: '宜进取',
    tooltip: '',
    analysis_tags: ['贵'],
    is_empty_palace: false,
  }],
  liuri_liushi: {
    liuri: {
      lunar_day: 12,
      life_palace_branch: 2,
      branch: '寅',
      palace_name: '财帛宫',
    },
    liushi: {
      hour_branch_idx: 4,
      life_palace_branch: 6,
      branch: '辰',
      palace_name: '官禄宫',
      hour_label: '辰时',
    },
  },
  liunian: {
    year: 2026,
    year_gz: '丙午',
    life_palace_branch: 6,
    sihua: {},
  },
  liuyue: [{ month: 7, month_name: '7月', month_gz: '辛未', life_palace_branch: 8, palace_name: '迁移宫', sihua: {} }],
  forecast: {
    year: 2026,
    yearly: {
      score: 75,
      overall: '平',
      advice: '稳扎稳打。',
      palace_name: '财帛',
    },
    monthly: [{ period: '1月', ganzhi: '丙寅', score: 70, overall: '吉' }],
    current_month: {
      period: '7月',
      ganzhi: '辛未',
      score: 80,
      advice: '宜规划。',
      overall: '吉',
    },
  },
  remedies: [{ name: '补水', cost_level: '低', actions: ['多饮水'] }],
  life_suggestions: [{
    category: 'career',
    category_label: '事业',
    name: '稳中求进',
    actions: ['专注主业'],
  }],
  engine_warnings: ['右弼安星默认 month 口径，与 iztro hour 辅煞可能对齐差一宫'],
  missing_fields: ['palace_stems_partial'],
  provenance: {
    palaces: { layer: 'engine', confidence: 0.88 },
  },
  iztro_crosscheck: {
    status: 'life_palace_mismatch',
    main_match: 12,
    main_total: 14,
    life_palace_match: false,
    engine_life_palace_gz: '乙丑',
    iztro_life_palace_gz: '癸丑',
    advisory: 'ZW03 双轨边界：命宫不一致，请对照双轨表。',
    dual_track: {
      label: 'iztro 对照轨',
      year_divide: 'normal',
      day_divide: 'forward',
      life_palace_gz: '癸丑',
      main_match: 12,
      main_total: 14,
      note: 'ZW03 典型边界：立春前一日 + 晚子时。',
    },
  },
  dayun: {
    items: [
      { ganzhi: '乙丑', start_age: 3, end_age: 12, start_year: 1993, branch_idx: 1, palace_name: '兄弟宫', sihua: { 紫微: '化禄' } },
      { ganzhi: '丙寅', start_age: 13, end_age: 22, start_year: 2003, branch_idx: 2, palace_name: '夫妻宫', sihua: {} },
      { ganzhi: '丁卯', start_age: 23, end_age: 32, start_year: 2013, branch_idx: 3, palace_name: '子女宫', sihua: {} },
    ],
  },
}

export const mockLifeVolumesPayload = {
  schema_version: 'life-volume@1.0',
  case_id: 'case-e2e-001',
  chart_hash: 'e2e-life-hash',
  disclaimer_block: { text: 'E2E 免责声明', version: '1.0' },
  volumes: [
    { id: 'preface', title: LIFE_VOLUME_LABELS.preface, sections: [] },
    { id: 'vol1', title: LIFE_VOLUME_LABELS.vol1, sections: [] },
    { id: 'vol2', title: LIFE_VOLUME_LABELS.vol2, sections: [] },
    { id: 'vol3', title: LIFE_VOLUME_LABELS.vol3, sections: [] },
    { id: 'vol4', title: LIFE_VOLUME_LABELS.vol4, sections: [] },
    { id: 'vol5', title: LIFE_VOLUME_LABELS.vol5, sections: [] },
    { id: 'vol6', title: LIFE_VOLUME_LABELS.vol6, sections: [] },
    { id: 'colophon', title: LIFE_VOLUME_LABELS.colophon, sections: [] },
  ],
  colophon: { summary_lines: ['E2E 跋'], expandable: true },
}

export async function setupLoggedInApiMocks(page: Page) {
  await setupCitiesApiMock(page)

  await page.route('**/api/v1/profile/*/summary', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        schema_version: '1.0',
        case_id: 'case-e2e-001',
        pillars_primary: { day: '甲子' },
        geju_one_liner: 'E2E 正官格',
        yongshen_favor: ['水'],
        strength_tier: '中和',
        ziwei_ming_one_liner: '紫微在命',
        current_dayun: '乙丑',
        liunian_2026_tag: '平',
        disclaimer_block: { text: 'E2E mock', version: '1.0' },
      }),
    })
  })

  await page.route(
    (url) => {
      const path = url.pathname
      return path === '/api/v1/cases' || path.endsWith('/api/v1/cases')
    },
    async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        })
        return
      }
      await route.fallback()
    },
  )

  await page.route('**/api/v1/life/volumes/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockLifeVolumesPayload),
    })
  })

  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'e2e-test-token',
        refresh_token: 'e2e-test-refresh',
      }),
    })
  })
}

/** 拦截排盘相关 API，使 E2E 不依赖真实后端 */
export async function setupChartApiMocks(page: Page) {
  await setupCitiesApiMock(page)

  await page.route('**/api/v1/bazi/full', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockBaziPayload),
    })
  })

  await page.route('**/api/v1/fusheng/archive-bundle', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        case_id: 'case-e2e-001',
        bazi: mockBaziPayload,
        ziwei: mockZiweiPayload,
        missing_fields: [],
      }),
    })
  })

  await page.route('**/api/v1/ziwei/full', async (route) => {
    let payload = mockZiweiPayload
    try {
      const body = route.request().postDataJSON() as { target_date?: string } | null
      const targetDate = body?.target_date?.slice(0, 10)
      if (targetDate === '2026-06-15') {
        payload = {
          ...mockZiweiPayload,
          liuri_liushi: {
            ...mockZiweiPayload.liuri_liushi,
            liuri: {
              ...mockZiweiPayload.liuri_liushi.liuri,
              lunar_day: 20,
              branch: '午',
              palace_name: '迁移宫',
              liuyue_month: 6,
            },
          },
        }
      }
    } catch {
      // keep default mock when post body is unavailable
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    })
  })

  await page.route('**/api/v1/bazi/dayun-report/inline', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [] }),
    })
  })

  await page.route('**/api/v1/bazi/explain/batch', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockBaziExplainBatch),
    })
  })

  await page.route('**/api/v1/ziwei/explain/batch', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockZiweiExplainBatch),
    })
  })

  await page.route('**/api/v1/llm/config', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        provider: 'mock',
        model: 'mock',
        available: true,
        note: 'E2E mock',
      }),
    })
  })
}

export async function setupSnapshotApiMocks(page: Page, caseId = 'case-e2e-001') {
  const snapshotId = 'snap-e2e-001'
  const createdAt = '2026-07-11T12:00:00Z'

  await page.route('**/api/v1/cases/*/snapshots', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: snapshotId,
            case_id: caseId,
            kind: 'fusheng_report',
            created_at: createdAt,
          },
        ]),
      })
      return
    }
    await route.continue()
  })

  await page.route(`**/api/v1/snapshots/${snapshotId}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: snapshotId,
        case_id: caseId,
        kind: 'fusheng_report',
        created_at: createdAt,
        output_json: {
          bazi: mockBaziPayload,
          ziwei: mockZiweiPayload,
        },
      }),
    })
  })
}
