import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import VolumePaywall from '@/components/fusheng/VolumePaywall.vue'
import VolumeSection from '@/components/fusheng/VolumeSection.vue'
import type { VolumeSection as VolumeSectionType } from '@/types/life-volume'

vi.mock('@/utils/analytics', () => ({
  track: vi.fn(),
}))

describe('VolumePaywall (T092)', () => {
  it('shows lock need and mock unlock CTA', async () => {
    const wrapper = mount(VolumePaywall, {
      props: { volumeId: 'vol3' },
    })
    expect(wrapper.get('[data-testid="volume-paywall"]').attributes('data-volume-id')).toBe('vol3')
    expect(wrapper.text()).toContain('读卷 Pass')
    expect(wrapper.get('[data-testid="volume-paywall-mock-unlock"]').text()).toContain('模拟')
    await wrapper.get('[data-testid="volume-paywall-mock-unlock"]').trigger('click')
    expect(wrapper.emitted('mockUnlock')).toHaveLength(1)
  })

  it('prefers detail blurb from BE locked section', () => {
    const wrapper = mount(VolumePaywall, {
      props: { volumeId: 'vol5', detail: '本卷需全书权益后方可展开全文（当前档位不足）。' },
    })
    expect(wrapper.text()).toContain('全书权益后方可展开')
  })
})

describe('VolumeSection locked teaser', () => {
  it('marks locked section with seal', () => {
    const section: VolumeSectionType = {
      id: 'locked',
      heading: '本卷未解锁',
      layer: 'fact',
      collapsed_default: false,
      blocks: [{ text: '需读卷 Pass', layer: 'fact' }],
    }
    const wrapper = mount(VolumeSection, {
      props: { section, volumeId: 'vol3', volumeLocked: true },
    })
    expect(wrapper.get('.volume-section').attributes('data-locked')).toBe('1')
    expect(wrapper.text()).toContain('锁')
    expect(wrapper.text()).toContain('本卷未解锁')
  })
})
