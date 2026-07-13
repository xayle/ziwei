/**
 * T078 · FE 侧 life-volume / snippets / archive 指针契约冒烟
 * 与 BE `tests/test_life_volume_schema_contract.py` 双端配对。
 */
import { describe, expect, it } from 'vitest'
import type { paths, components } from '@/api/schema'
import type {
  ArchiveExtensionPointer,
  LifeSnippetsResponseModel,
  LifeVolumeResponseModel,
} from '@/api/openapiTypes'
import { LIFE_VOLUME_SCHEMA_VERSION } from '@/constants/feBeContract'

describe('T078 OpenAPI ↔ FE life contracts', () => {
  it('exposes GET /life/volumes and /life/snippets paths', () => {
    const volumesPath: keyof paths = '/api/v1/life/volumes/{case_id}'
    const snippetsPath: keyof paths = '/api/v1/life/snippets/{case_id}'
    expect(volumesPath).toContain('life/volumes')
    expect(snippetsPath).toContain('life/snippets')
  })

  it('LifeVolumeResponseModel aligns with life-volume@1.0 constant', () => {
    type V = LifeVolumeResponseModel['schema_version']
    const version: V = 'life-volume@1.0'
    expect(version).toBe(LIFE_VOLUME_SCHEMA_VERSION)
  })

  it('LifeSnippetsResponseModel supports 3–5 hooks shape', () => {
    const sample: LifeSnippetsResponseModel = {
      schema_version: 'life-snippets@0.1',
      case_id: 'c1',
      hooks: [
        { tag: '事实', text: '日主甲子。', layer: 'engine' },
        { tag: '典籍', text: '官格贵印。', layer: 'classical' },
        { tag: '推算', text: '2026 丙午。', layer: 'engine' },
      ],
      vertical_title: '卷三·运之波',
      disclaimer: '非命运断言。',
    }
    expect(sample.hooks.length).toBeGreaterThanOrEqual(3)
    expect(sample.hooks.length).toBeLessThanOrEqual(5)
  })

  it('ArchiveExtensionPointer covers name/zeri kinds', () => {
    const namePtr: ArchiveExtensionPointer = {
      kind: 'name',
      path: '/api/v1/name/analyze',
      method: 'POST',
      ready: true,
      label: '姓名学',
      params: { surname: '张', given_name: '三' },
    }
    const zeriPtr: components['schemas']['ArchiveExtensionPointer'] = {
      kind: 'zeri',
      path: '/api/v1/zeri/recommend',
      method: 'GET',
      ready: false,
      label: '择日',
      params: {},
    }
    expect(namePtr.kind).toBe('name')
    expect(zeriPtr.kind).toBe('zeri')
  })
})
