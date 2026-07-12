import { describe, expect, it } from 'vitest'
import {
  DEFAULT_READING_GUIDE_PARAGRAPHS,
  extractAllReadingGuideParagraphs,
  resolveReadingGuideParagraphs,
} from '@/utils/extractReadingGuideParagraphs'

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
})
