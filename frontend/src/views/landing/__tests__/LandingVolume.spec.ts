import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import LandingVolume from '@/views/landing/LandingVolume.vue'
import { LANDING_BRAND, LANDING_CTA, LANDING_DISCLAIMER } from '@/constants/landingVolume'
import { UTM_STORAGE_KEY } from '@/utils/utmCapture'

const fetchPreviewMock = vi.fn(async () => null as unknown)

vi.mock('@/utils/analytics', () => ({
  track: vi.fn(),
  trackVolumeView: vi.fn(),
  trackLandingCta: vi.fn(),
  flushAnalytics: vi.fn(async () => null),
}))

vi.mock('@/api/life', () => ({
  fetchLifeVol1Preview: (...args: unknown[]) => fetchPreviewMock(...args),
}))

describe('LandingVolume (T091)', () => {
  beforeEach(() => {
    sessionStorage.clear()
    fetchPreviewMock.mockReset()
    fetchPreviewMock.mockResolvedValue(null)
  })

  async function mountLanding(query: Record<string, string> = {}) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/landing', name: 'landing', component: LandingVolume },
        { path: '/profile', name: 'profile', component: { template: '<div />' } },
      ],
    })
    await router.push({ path: '/landing', query })
    await router.isReady()
    return mount(LandingVolume, {
      global: { plugins: [router] },
    })
  }

  it('renders brand, preface CTA and disclaimer', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.get('[data-testid="landing-volume"]').exists()).toBe(true)
    expect(wrapper.text()).toContain(LANDING_BRAND)
    expect(wrapper.get('[data-testid="landing-cta"]').text()).toContain(LANDING_CTA)
    expect(wrapper.get('[data-testid="landing-disclaimer"]').text()).toBe(LANDING_DISCLAIMER)
  })

  it('captures utm and navigates to profile on CTA', async () => {
    const wrapper = await mountLanding({
      utm_source: 'douyin',
      utm_campaign: 'geju_hook',
      content_id: 'video_1',
    })
    await flushPromises()
    const stored = JSON.parse(sessionStorage.getItem(UTM_STORAGE_KEY) || '{}') as {
      utm_source?: string
      content_id?: string
    }
    expect(stored.utm_source).toBe('douyin')
    expect(stored.content_id).toBe('video_1')

    await wrapper.get('[data-testid="landing-cta"]').trigger('click')
    await flushPromises()
    const router = wrapper.vm.$router
    expect(router.currentRoute.value.path).toBe('/profile')
    expect(router.currentRoute.value.query.utm_source).toBe('douyin')
    expect(router.currentRoute.value.query.from).toBe('landing')
  })

  it('root landing node is present for mobile layout', async () => {
    const wrapper = await mountLanding()
    expect(wrapper.get('[data-testid="landing-volume"]').classes()).toContain('landing-volume')
  })

  it('loads H5 vol1 preview when case_id+token present (SHARE-02)', async () => {
    fetchPreviewMock.mockResolvedValue({
      schema_version: 'life-volume@1.0',
      case_id: 'c1',
      chart_hash: 'h',
      generated_at: '2026-01-01T00:00:00Z',
      volumes: [{
        id: 'vol1',
        title: '命之根',
        sections: [{
          id: 's1',
          title: 't',
          layer: 'fact',
          blocks: [{ text: '试读句·日主甲木', layer: 'fact' }],
        }],
      }],
      disclaimer_block: { text: '仅供文化研究' },
    })
    const wrapper = await mountLanding({ case_id: 'c1', token: 'h5-tok' })
    await flushPromises()
    expect(fetchPreviewMock).toHaveBeenCalledWith('c1', 'h5-tok')
    expect(wrapper.get('[data-testid="landing-h5-preview"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="landing-h5-preview-line"]').text()).toContain('试读句·日主甲木')
  })
})
