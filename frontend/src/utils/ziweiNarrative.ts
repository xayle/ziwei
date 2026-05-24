import type { ZiweiResponse } from '@/api/ziwei'

export function buildPatternSummaryText(result: ZiweiResponse | null | undefined): string {
  return (result?.patterns || [])
    .map((item) => [item.name, item.level].filter(Boolean).join(' '))
    .filter(Boolean)
    .join('、')
}
