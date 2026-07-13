const ELEMENT_EN_TO_CN: Record<string, string> = {
  metal: '金',
  wood: '木',
  water: '水',
  fire: '火',
  earth: '土',
}

export function toCnElements(values: string[] | undefined): string[] {
  if (!values?.length) return []
  const out = new Set<string>()
  for (const value of values) {
    const trimmed = value.trim()
    if (['金', '木', '水', '火', '土'].includes(trimmed)) {
      out.add(trimmed)
      continue
    }
    const mapped = ELEMENT_EN_TO_CN[trimmed.toLowerCase()]
    if (mapped) out.add(mapped)
  }
  return [...out]
}

export function formatCnElementsJoin(
  values: string[] | undefined | null,
  fallback = '缺失',
): string {
  const cn = toCnElements(values ?? undefined)
  return cn.length ? cn.join('、') : fallback
}
