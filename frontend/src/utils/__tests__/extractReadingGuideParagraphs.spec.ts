import {
  DEFAULT_READING_GUIDE_PARAGRAPHS,
  extractAllReadingGuideParagraphs,
  extractReadingGuideFromLifeVolumes,
  resolveReadingGuideParagraphs,
} from '@/utils/extractReadingGuideParagraphs'
import type { LifeVolumeResponse } from '@/types/life-volume'

describe('extractReadingGuideParagraphs', () => {
  it('merges reading sections from bazi and ziwei tracks', () => {
    const paragraphs = extractAllReadingGuideParagraphs({
      sections: [
        { section_id: 'reading', blocks: [{ text: '先读盘面。', layer: 'fact' }] },
        { section_id: 'reading', blocks: [{ text: '先读方盘。', layer: 'fact' }] },
        { section_id: 'geju', blocks: [{ text: 'ignored', layer: 'cite' }] },
      ],
    })
    expect(paragraphs).toEqual(['先读盘面。', '先读方盘。'])
  })

  it('falls back to default copy when explain empty', () => {
    expect(resolveReadingGuideParagraphs(null)).toEqual([...DEFAULT_READING_GUIDE_PARAGRAPHS])
  })

  it('T082 prefers volumes reading-guide when explain missing', () => {
    const doc = {
      schema_version: 'life-volume@1.0',
      case_id: 'c1',
      chart_hash: 'h',
      disclaimer_block: { text: 'd', version: '1' },
      volumes: [
        {
          id: 'preface',
          title: '卷首',
          sections: [{
            id: 'reading-guide',
            title: '读法',
            layer: 'fact',
            blocks: [{ text: '来自 volumes 的读法。', layer: 'fact' }],
          }],
        },
      ],
      colophon: { summary_lines: [] },
    } as LifeVolumeResponse
    expect(extractReadingGuideFromLifeVolumes(doc)).toEqual(['来自 volumes 的读法。'])
    expect(resolveReadingGuideParagraphs(null, doc)).toEqual(['来自 volumes 的读法。'])
  })
})
