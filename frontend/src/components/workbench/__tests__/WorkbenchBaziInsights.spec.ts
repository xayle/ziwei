import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WorkbenchBaziInsights from '@/components/workbench/WorkbenchBaziInsights.vue'

const baziData = {
  wealth_analysis: {
    wealth_score: 78,
    wealth_tier: '稳中有升',
    annual_range: '30-50万',
    industries: ['咨询', '教育', '文化'],
  },
  career: {
    career_score: 66,
    career_directions: ['管理', '策划'],
    optimal_move_timing: '秋季更佳',
    suitable_industries: ['科技', '培训'],
  },
  marriage_analysis: {
    marriage_score: 72,
    peach_blossom: '中上',
    partner_direction: '东南',
    marriage_windows: ['2026', '2028'],
  },
  health: {
    health_score: 58,
    risk_level: '中',
    risk_organs: ['脾胃', '睡眠'],
  },
  personality: {
    core_trait: '主见强，执行力高，但节奏容易偏快。',
    inference_tags: ['主动', '果断'],
    growth_advice: '学会留白与节奏管理。',
  },
  life_arc: {
    early_fortune: '积累期',
    mid_fortune: '发力期',
    late_fortune: '守成期',
    overall_tier: '中上',
    peak_periods: ['33-42'],
    caution_periods: ['27-29'],
    life_motto: '稳中求进',
  },
  lucky: {
    lucky_colors: ['青', '绿'],
    lucky_numbers: [3, 8],
    lucky_direction: '东方',
    lucky_item: '木质饰品',
    avoid_colors: ['灰'],
    avoid_direction: '西北',
  },
  milestones: [
    {
      age: 33,
      year: 2026,
      ganzhi_context: '丙午',
      milestone_type: '事业',
      description: '进入角色跃迁窗口。',
      advice: '先稳团队，再推项目。',
      risk_level: '中',
    },
  ],
  relationship: {
    noble_people: ['长辈', '女性上司'],
    petty_people: ['口舌型同事'],
    liu_qin: { 父母: '助力', 伴侣: '需沟通', 子女: '平稳' },
    social_strategy: '宜少而精，重质量合作。',
  },
  fengshui: {
    auspicious_directions: ['东', '东南'],
    decor: ['原木', '绿植'],
    plants: ['富贵竹'],
    taboo: ['杂乱堆积'],
  },
  lifestyle: {
    exercise: ['快走'],
    diet: ['清淡'],
    best_times: '早晨',
    travel_direction: '东南',
    sleep_advice: '23点前入睡。',
  },
}

const liunianDetailRows = [
  {
    year: 2026,
    ganzhi: '丙午',
    tenGod: '偏财',
    flowWuxing: '火',
    clash: '冲月柱',
    annualScore: 82,
    isCurrent: true,
    domains: [
      { key: '事业', val: '稳中有升' },
      { key: '财运', val: '偏强' },
    ],
    interpretationText: '宜主动推进重点项目。',
    taiSuiRelations: ['拱合'],
    clashPillars: ['月柱'],
    notableMonths: [4, 8],
    optimalAction: '把握窗口期。',
    tags: ['扩张', '合作'],
  },
]

describe('WorkbenchBaziInsights', () => {
  it('渲染八字解读区主要卡组与流年详情', () => {
    const wrapper = mount(WorkbenchBaziInsights, {
      props: {
        currentYear: 2026,
        simpleView: false,
        summary: '整体结构偏燥，宜补水润局。',
        baziData,
        thisYearDetail: { interpretation_text: '今年以稳住主线为先。' },
        fortSummary: {
          this_year_domains: { 事业: '推进', 财运: '回升' },
          top3_actions: ['控制节奏', '优化协作'],
        },
        liunianDetailRows,
        expandedLiunianDetailYear: 2026,
        activeLiuyueMonth: 4,
        geju: { interpretation_text: '此局成于木火流通。' },
        yongshen: { rationale: '以水调候，以金佐之。' },
      },
    })

    expect(wrapper.text()).toContain('综合解读')
    expect(wrapper.text()).toContain('四维分析')
    expect(wrapper.text()).toContain('性格分析')
    expect(wrapper.text()).toContain('2026 年运势')
    expect(wrapper.text()).toContain('流年四维详情')
    expect(wrapper.text()).toContain('建议与注意事项')
    expect(wrapper.text()).toContain('详细格局解读')
    expect(wrapper.text()).toContain('生命弧线')
    expect(wrapper.text()).toContain('开运建议')
    expect(wrapper.text()).toContain('人生里程碑')
    expect(wrapper.text()).toContain('六亲与人际')
    expect(wrapper.text()).toContain('风水建议')
    expect(wrapper.text()).toContain('生活建议')
    expect(wrapper.findAll('.wb-quad-card')).toHaveLength(4)
    expect(wrapper.find('.wb-lyd-card.current').text()).toContain('2026 · 丙午')
    expect(wrapper.find('.wb-month-chip.active').text()).toContain('4月')
    expect(wrapper.text()).toContain('用神说明：以水调候，以金佐之。')
  })

  it('触发流年展开与关键月份联动事件', async () => {
    const wrapper = mount(WorkbenchBaziInsights, {
      props: {
        currentYear: 2026,
        simpleView: false,
        summary: null,
        baziData: null,
        thisYearDetail: null,
        fortSummary: null,
        liunianDetailRows,
        expandedLiunianDetailYear: 2026,
        activeLiuyueMonth: 4,
        geju: null,
        yongshen: null,
      },
    })

    await wrapper.find('.wb-lyd-toggle').trigger('click')
    await wrapper.find('.wb-month-chip').trigger('click')

    expect(wrapper.emitted('toggleLiunianDetail')).toEqual([[2026]])
    expect(wrapper.emitted('selectLiunianMonth')).toEqual([[{ year: 2026, month: 4 }]])
  })

  it('简洁视图下收起扩展解读但保留年运势', () => {
    const wrapper = mount(WorkbenchBaziInsights, {
      props: {
        currentYear: 2026,
        simpleView: true,
        summary: '整体结构偏燥，宜补水润局。',
        baziData,
        thisYearDetail: { interpretation_text: '今年以稳住主线为先。' },
        fortSummary: { this_year_domains: { 事业: '推进' }, top3_actions: ['控制节奏'] },
        liunianDetailRows,
        expandedLiunianDetailYear: 2026,
        activeLiuyueMonth: 4,
        geju: { interpretation_text: '此局成于木火流通。' },
        yongshen: { rationale: '以水调候，以金佐之。' },
      },
    })

    expect(wrapper.text()).toContain('2026 年运势')
    expect(wrapper.text()).not.toContain('综合解读')
    expect(wrapper.text()).not.toContain('四维分析')
    expect(wrapper.text()).not.toContain('建议与注意事项')
  })
})
