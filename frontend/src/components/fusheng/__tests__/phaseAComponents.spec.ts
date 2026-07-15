import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PatternTierBadge from '@/components/fusheng/PatternTierBadge.vue'
import DualTrackTable from '@/components/fusheng/DualTrackTable.vue'
import VolumeSection from '@/components/fusheng/VolumeSection.vue'
import ColophonFootnote from '@/components/fusheng/ColophonFootnote.vue'
import BaziStructuralRelations from '@/components/fusheng/BaziStructuralRelations.vue'
import type { VolumeSection as VolumeSectionType } from '@/types/life-volume'
import type { Colophon } from '@/types/life-volume'

describe('PatternTierBadge', () => {
  it('renders classical label', () => {
    const wrapper = mount(PatternTierBadge, { props: { layer: 'classical' } })
    expect(wrapper.text()).toContain('全书口径')
    expect(wrapper.attributes('data-layer')).toBe('classical')
  })

  it('derives layer from rule id', () => {
    const wrapper = mount(PatternTierBadge, { props: { ruleId: 'ZRULE_001' } })
    expect(wrapper.attributes('data-layer')).toBe('classical')
  })
})

describe('DualTrackTable', () => {
  it('renders reference rows', () => {
    const wrapper = mount(DualTrackTable, {
      props: {
        rows: [{ id: 'ZIP09', topic: '格局', recorded: '从官杀', engine: '七杀', note: '双轨' }],
      },
    })
    expect(wrapper.text()).toContain('ZIP09')
    expect(wrapper.text()).toContain('七杀')
  })
})

describe('VolumeSection', () => {
  const baseSection: VolumeSectionType = {
    id: 'geju',
    heading: '格局',
    layer: 'cite',
    collapsed_default: false,
    blocks: [],
  }

  it('shows 典籍依据 only when classic_id present', () => {
    const withClassic = mount(VolumeSection, {
      props: {
        section: {
          ...baseSection,
          blocks: [{ layer: 'cite', text: '正官格', classic_id: 'CL001' }],
        },
      },
    })
    expect(withClassic.text()).toContain('典籍依据')

    const pending = mount(VolumeSection, {
      props: {
        section: {
          ...baseSection,
          blocks: [{ layer: 'cite', text: '待校勘条目' }],
        },
      },
    })
    expect(pending.text()).toContain('待校勘')
    expect(pending.text()).not.toContain('典籍依据')
  })

  it('exposes aria-expanded on collapsible inference sections', async () => {
    const wrapper = mount(VolumeSection, {
      props: {
        section: {
          ...baseSection,
          layer: 'inference',
          collapsed_default: true,
          blocks: [{ layer: 'inference', text: '经验推断示例' }],
        },
      },
    })
    const toggle = wrapper.get('button.volume-section__toggle')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
  })
})

describe('ColophonFootnote', () => {
  const baseColophon: Colophon = {
    summary_lines: ['引擎 v1.0', '口径：立春换年'],
    expandable: true,
    iztro_advisory: '命宫与 iztro 差一宫，见双轨表。',
    dual_track_note: '典籍与引擎格局并存。',
    missing_fields: ['palace_stems_partial'],
  }

  it('toggles aria-expanded on expandable colophon', async () => {
    const wrapper = mount(ColophonFootnote, { props: { colophon: baseColophon } })
    const toggle = wrapper.get('button.colophon-footnote__toggle')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.text()).toContain('对照轨')
  })

  it('omits toggle when colophon is not expandable', () => {
    const wrapper = mount(ColophonFootnote, {
      props: { colophon: { ...baseColophon, expandable: false } },
    })
    expect(wrapper.find('button.colophon-footnote__toggle').exists()).toBe(false)
  })

  it('shows wenmo advisory in expanded detail', async () => {
    const wrapper = mount(ColophonFootnote, {
      props: {
        colophon: {
          ...baseColophon,
          wenmo_advisory: '文墨天机为 advisory 对照轨',
        },
      },
    })
    await wrapper.get('button.colophon-footnote__toggle').trigger('click')
    expect(wrapper.text()).toContain('文墨对照')
  })
})

describe('BaziStructuralRelations', () => {
  it('humanizes missing fields and avoids raw keys', () => {
    const wrapper = mount(BaziStructuralRelations, {
      props: {
        missingFields: ['combine_summary', 'palace_ten_gods'],
        relations: [],
      },
    })
    const alert = wrapper.get('[data-testid="bazi-structural-missing"]')
    expect(alert.text()).toContain('合化摘要')
    expect(alert.text()).toContain('宫位十神')
    expect(alert.text()).not.toContain('combine_summary')
    expect(alert.text()).not.toContain('引擎未覆盖')
    expect(alert.text()).toContain('字段注记')
  })

  it('labels advisory-only gaps as 对照注记', () => {
    const wrapper = mount(BaziStructuralRelations, {
      props: {
        missingFields: ['palace_ten_gods'],
        relations: [],
      },
    })
    expect(wrapper.get('[data-testid="bazi-structural-missing"]').text()).toContain('对照注记')
  })
})
