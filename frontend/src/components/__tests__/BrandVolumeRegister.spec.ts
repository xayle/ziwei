import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'

import BrandVolumeRegister from '@/components/fusheng/BrandVolumeRegister.vue'
import { BRAND_HOME_VOLUMES } from '@/constants/brandHome'

describe('BrandVolumeRegister', () => {
  it('renders six volume rows as line register, not cards', () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div />' } }],
    })

    const wrapper = mount(BrandVolumeRegister, {
      global: { plugins: [router] },
      props: { canOpenReport: true },
    })

    const rows = wrapper.findAll('.brand-register__row')
    expect(rows).toHaveLength(BRAND_HOME_VOLUMES.length)
    expect(wrapper.find('.brand-codex__panel').exists()).toBe(true)
    expect(wrapper.find('[data-testid="brand-codex"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="brand-lane-note"]').text()).toContain('排盘台')
    expect(wrapper.get('[data-volume-id="vol1"]').attributes('data-lane')).toBe('desk')
    expect(wrapper.get('[data-volume-id="vol2"]').attributes('data-lane')).toBe('book')
  })
})
