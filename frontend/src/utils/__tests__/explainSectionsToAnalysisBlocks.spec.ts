import { describe, expect, it } from 'vitest'
import { explainSectionsToAnalysisBlocks } from '@/utils/explainSectionsToAnalysisBlocks'

describe('explainSectionsToAnalysisBlocks', () => {
  it('maps geju/relations/reading to AnalysisPanel blocks', () => {
    const blocks = explainSectionsToAnalysisBlocks([
      {
        section_id: 'geju',
        verified: true,
        blocks: [{ text: '正官格说明。', layer: 'cite', classic_id: 'CL001' }],
      },
      {
        section_id: 'relations',
        blocks: [{ text: '年柱合月柱。', layer: 'fact' }],
      },
      {
        section_id: 'reading',
        blocks: [{ text: '先读盘面。', layer: 'fact' }],
      },
    ])
    expect(blocks).toHaveLength(3)
    expect(blocks[0]).toMatchObject({
      id: 'explain-geju',
      title: '格局解读',
      layer: 'classical',
    })
    expect(blocks[0].bullets).toEqual(['出处：CL001'])
    expect(blocks[1].title).toBe('干支关系解读')
    expect(blocks[2].title).toBe('读法导引')
  })

  it('skips empty sections', () => {
    expect(explainSectionsToAnalysisBlocks([
      { section_id: 'geju', blocks: [] },
    ])).toEqual([])
  })
})
