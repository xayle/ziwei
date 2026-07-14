import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DouyinShareCard from '@/components/fusheng/DouyinShareCard.vue'

const downloadMock = vi.fn(async () => new Blob(['png'], { type: 'image/png' }))
const saveMock = vi.fn()
const trackMock = vi.fn()
const mintMock = vi.fn(async () => ({
  access_token: 'h5-tok',
  token_type: 'bearer',
  expires_in: 1800,
  case_id: 'case-abc',
  scope: 'life_preview_vol1',
}))
const copyMock = vi.fn(async () => true)

vi.mock('@/api/exportCard', () => ({
  downloadCaseShareCard: (...args: unknown[]) => downloadMock(...args),
  saveShareCardPng: (...args: unknown[]) => saveMock(...args),
}))

vi.mock('@/api/auth', () => ({
  mintH5PreviewToken: (...args: unknown[]) => mintMock(...args),
}))

vi.mock('@/utils/copyText', () => ({
  copyTextToClipboard: (...args: unknown[]) => copyMock(...args),
}))

vi.mock('@/utils/analytics', () => ({
  track: (...args: unknown[]) => trackMock(...args),
}))

describe('DouyinShareCard (T098)', () => {
  beforeEach(() => {
    downloadMock.mockClear()
    saveMock.mockClear()
    trackMock.mockClear()
    mintMock.mockClear()
    copyMock.mockClear()
  })

  it('renders 9:16 preview with paper volume and fact lines', () => {
    const wrapper = mount(DouyinShareCard, {
      props: {
        volumeTitle: '卷一·命之根',
        factLines: ['日主戊土，正官格透干。'],
        gejuLine: '正官格',
        disclaimer: '非命运断言',
      },
    })
    const card = wrapper.get('[data-testid="douyin-share-preview"]')
    expect(card.text()).toContain('浮生')
    expect(card.text()).toContain('卷一·命之根')
    expect(card.text()).toContain('日主戊土')
    expect(wrapper.text()).toContain('登录建档后可导出 PNG / 试读链接')
    expect(wrapper.find('[data-testid="douyin-share-export"]').exists()).toBe(false)
  })

  it('exports PNG via layout=douyin when caseId set', async () => {
    const wrapper = mount(DouyinShareCard, {
      props: {
        volumeTitle: '卷一·命之根',
        factLines: ['事实句'],
        caseId: 'case-abc',
        source: 'report',
      },
    })
    await wrapper.get('[data-testid="douyin-share-export"]').trigger('click')
    await flushPromises()
    expect(downloadMock).toHaveBeenCalledWith('case-abc', 'douyin')
    expect(saveMock).toHaveBeenCalled()
    expect(trackMock).toHaveBeenCalledWith(
      expect.objectContaining({
        event_type: 'share_card_export',
        case_id: 'case-abc',
        properties: expect.objectContaining({ layout: 'douyin', source: 'report' }),
      }),
    )
  })

  it('mints H5 preview link when caseId set (SHARE-02)', async () => {
    const wrapper = mount(DouyinShareCard, {
      props: {
        volumeTitle: '卷一·命之根',
        factLines: ['事实句'],
        caseId: 'case-abc',
        source: 'report',
      },
    })
    await wrapper.get('[data-testid="douyin-h5-preview-mint"]').trigger('click')
    await flushPromises()
    expect(mintMock).toHaveBeenCalledWith('case-abc')
    expect(copyMock).toHaveBeenCalled()
    expect(wrapper.get('[data-testid="douyin-h5-preview-status"]').text()).toContain('试读链接已复制')
  })
})
