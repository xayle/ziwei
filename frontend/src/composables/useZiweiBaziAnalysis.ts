import { computed, type Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'

export type BaziStemInfo = { element: string; yin_yang: string; meaning: string }
export type BaziBranchInfo = { zodiac: string; element: string; meaning: string }
export type BaziPillarDetails = {
  stem: string
  branch: string
  stemInfo?: BaziStemInfo
  branchInfo?: BaziBranchInfo
  isJieqi?: boolean
}
export type BaziDetails = {
  birth_solar: string
  gender: string
  true_solar_time: string
  lunar: ZiweiResponse['lunar']
  year: BaziPillarDetails
  month: BaziPillarDetails
  day: BaziPillarDetails
  hour: BaziPillarDetails
}
export type ShiShenAnalyze = {
  dayMaster: string
  relations: Record<string, string>
}
export type CangganInfo = { main: string; aux1?: string; aux2?: string }
export type CangganNayin = Record<'year' | 'month' | 'day' | 'hour', { branch: string; canggan?: CangganInfo; nayin?: string }>
export type BaziShenshaItem = { name: string; level: '吉' | '中' | '警'; hit: string[]; reason: string }
export type BaziRelationItem = { type: string; a: string; b: string; pillars: string }
export type BaziRelationAnalyze = { branchRelations: BaziRelationItem[]; stemRelations: BaziRelationItem[] }
export type BaziGejuYongshen = {
  dominant: string
  gejuName: string
  favor: string[]
  avoid: string[]
  rationale: string
}
export type BaziLuckDayunItem = {
  rawIdx: number
  idx: number
  ganzhi: string
  startAge: number
  endAge: number
  startYear: number
  isCurrent: boolean
}
export type BaziLuckLiuyueItem = {
  month: number
  monthName: string
  monthGz: string
  palace: string
}
export type BaziLuckOverview = {
  currentDayun: string
  dayun: BaziLuckDayunItem[]
  liunianYear: number
  liunianGz: string
  liuyue: BaziLuckLiuyueItem[]
}
export type BaziDayunFocusDetail = {
  idx: number
  rawIdx: number
  ganzhi: string
  startAge: number
  endAge: number
  startYear: number
  tenGod: string
  narrative: string
}
export type BaziTenGodUsageItem = {
  pillar: string
  stem: string
  tenGod: string
  interpretation: string
}

type UseZiweiBaziAnalysisOptions = {
  result: Ref<ZiweiResponse | null>
  currentDayunGz: Ref<string>
  baziDayunFocusIdx: Ref<number>
}

export function useZiweiBaziAnalysis(options: UseZiweiBaziAnalysisOptions) {
  const baziDetails = computed(() => {
    if (!options.result.value?.lunar) return null
    const lunar = options.result.value.lunar

    const stemMeanings: Record<string, { element: string; yin_yang: string; meaning: string }> = {
      '甲': { element: '木', yin_yang: '阳', meaning: '生长出生，生机勃勃' },
      '乙': { element: '木', yin_yang: '阴', meaning: '柔软灵活，缠绕缗柔' },
      '丙': { element: '火', yin_yang: '阳', meaning: '炎热光彩，热情似火' },
      '丁': { element: '火', yin_yang: '阴', meaning: '温暖内秀，火焰柔和' },
      '戊': { element: '土', yin_yang: '阳', meaning: '厚实高大，坚实稳定' },
      '己': { element: '土', yin_yang: '阴', meaning: '温厚细腻，柔和谦虚' },
      '庚': { element: '金', yin_yang: '阳', meaning: '坚硬锐利，变革开放' },
      '辛': { element: '金', yin_yang: '阴', meaning: '精致细腻，锋芒内敛' },
      '壬': { element: '水', yin_yang: '阳', meaning: '流动奔放，聪敏多变' },
      '癸': { element: '水', yin_yang: '阴', meaning: '柔弱神秘，敏感智慧' },
    }

    const branchMeanings: Record<string, { zodiac: string; element: string; meaning: string }> = {
      '子': { zodiac: '鼠', element: '水', meaning: '聪慧敏锐，夜间之灵' },
      '丑': { zodiac: '牛', element: '土', meaning: '勤勉踏实，坚韧刻苦' },
      '寅': { zodiac: '虎', element: '木', meaning: '勇猛阳刚，震撼雄峙' },
      '卯': { zodiac: '兔', element: '木', meaning: '温柔秀雅，活泼灵巧' },
      '辰': { zodiac: '龙', element: '土', meaning: '龙威显赫，气势磅礴' },
      '巳': { zodiac: '蛇', element: '火', meaning: '聪敏狡黠，智慧深思' },
      '午': { zodiac: '马', element: '火', meaning: '热烈奔放，光彩夺目' },
      '未': { zodiac: '羊', element: '土', meaning: '温和善良，艺术灵秀' },
      '申': { zodiac: '猴', element: '金', meaning: '灵机敏锐，多才多艺' },
      '酉': { zodiac: '鸡', element: '金', meaning: '警惕认真，文采斐然' },
      '戌': { zodiac: '狗', element: '土', meaning: '忠诚守信，坦诚直率' },
      '亥': { zodiac: '猪', element: '水', meaning: '温和坦率，智慧感悟' },
    }

    const yearStem = lunar.year_gz?.charAt(0) || ''
    const yearBranch = lunar.year_gz?.charAt(1) || ''
    const monthStem = lunar.jieqi_month_gz?.charAt(0) || lunar.month_gz?.charAt(0) || ''
    const monthBranch = lunar.jieqi_month_gz?.charAt(1) || lunar.month_gz?.charAt(1) || ''
    const dayStem = lunar.day_gz?.charAt(0) || ''
    const dayBranch = lunar.day_gz?.charAt(1) || ''
    const hourStem = lunar.hour_gz?.charAt(0) || ''
    const hourBranch = lunar.hour_branch || lunar.hour_gz?.charAt(1) || ''

    return {
      birth_solar: options.result.value?.birth_solar || '',
      gender: options.result.value?.gender || '',
      true_solar_time: options.result.value?.true_solar_time || '',
      lunar,
      year: { stem: yearStem, branch: yearBranch, stemInfo: stemMeanings[yearStem], branchInfo: branchMeanings[yearBranch] },
      month: { stem: monthStem, branch: monthBranch, stemInfo: stemMeanings[monthStem], branchInfo: branchMeanings[monthBranch], isJieqi: Boolean(lunar.jieqi_month_gz && lunar.jieqi_month_gz !== lunar.month_gz) },
      day: { stem: dayStem, branch: dayBranch, stemInfo: stemMeanings[dayStem], branchInfo: branchMeanings[dayBranch] },
      hour: { stem: hourStem, branch: hourBranch, stemInfo: stemMeanings[hourStem], branchInfo: branchMeanings[hourBranch] },
    } as BaziDetails
  })

  const shiShenAnalyze = computed<ShiShenAnalyze | null>(() => {
    if (!baziDetails.value) return null
    const dayMaster = baziDetails.value.day.stem
    const shishenRelations: Record<string, Record<string, string>> = {
      '甲': { '甲': '比肩', '乙': '劫财', '丙': '食神', '丁': '伤官', '戊': '偏财', '己': '正财', '庚': '七杀', '辛': '正官', '壬': '偏印', '癸': '正印' },
      '乙': { '甲': '劫财', '乙': '比肩', '丙': '伤官', '丁': '食神', '戊': '正财', '己': '偏财', '庚': '正官', '辛': '七杀', '壬': '正印', '癸': '偏印' },
      '丙': { '甲': '食神', '乙': '伤官', '丙': '比肩', '丁': '劫财', '戊': '偏印', '己': '正印', '庚': '偏财', '辛': '正财', '壬': '七杀', '癸': '正官' },
      '丁': { '甲': '伤官', '乙': '食神', '丙': '劫财', '丁': '比肩', '戊': '正印', '己': '偏印', '庚': '正财', '辛': '偏财', '壬': '正官', '癸': '七杀' },
      '戊': { '甲': '偏财', '乙': '正财', '丙': '偏印', '丁': '正印', '戊': '比肩', '己': '劫财', '庚': '伤官', '辛': '食神', '壬': '正官', '癸': '七杀' },
      '己': { '甲': '正财', '乙': '偏财', '丙': '正印', '丁': '偏印', '戊': '劫财', '己': '比肩', '庚': '食神', '辛': '伤官', '壬': '七杀', '癸': '正官' },
      '庚': { '甲': '七杀', '乙': '正官', '丙': '偏财', '丁': '正财', '戊': '伤官', '己': '食神', '庚': '比肩', '辛': '劫财', '壬': '偏印', '癸': '正印' },
      '辛': { '甲': '正官', '乙': '七杀', '丙': '正财', '丁': '偏财', '戊': '食神', '己': '伤官', '庚': '劫财', '辛': '比肩', '壬': '正印', '癸': '偏印' },
      '壬': { '甲': '偏印', '乙': '正印', '丙': '七杀', '丁': '正官', '戊': '偏财', '己': '正财', '庚': '正官', '辛': '七杀', '壬': '比肩', '癸': '劫财' },
      '癸': { '甲': '正印', '乙': '偏印', '丙': '正官', '丁': '七杀', '戊': '正财', '己': '偏财', '庚': '七杀', '辛': '正官', '壬': '劫财', '癸': '比肩' },
    }
    return { dayMaster, relations: shishenRelations[dayMaster] || {} }
  })

  function baziWuxingCount(element: string): number {
    if (!options.result.value?.lunar || !baziDetails.value) return 0
    const details = baziDetails.value
    const stemElementMap: Record<string, string> = {
      '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
    }
    const branchElementMap: Record<string, string> = {
      '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水',
    }
    let count = 0
    if (stemElementMap[details.year.stem] === element) count++
    if (branchElementMap[details.year.branch] === element) count++
    if (stemElementMap[details.month.stem] === element) count++
    if (branchElementMap[details.month.branch] === element) count++
    if (stemElementMap[details.day.stem] === element) count++
    if (branchElementMap[details.day.branch] === element) count++
    if (stemElementMap[details.hour.stem] === element) count++
    if (branchElementMap[details.hour.branch] === element) count++
    return count
  }

  const cangganNayin = computed<CangganNayin | null>(() => {
    const branchCanggan: Record<string, { main: string; aux1?: string; aux2?: string }> = {
      '子': { main: '癸' }, '丑': { main: '己', aux1: '辛', aux2: '癸' }, '寅': { main: '甲', aux1: '丙', aux2: '戊' }, '卯': { main: '乙' },
      '辰': { main: '戊', aux1: '乙', aux2: '癸' }, '巳': { main: '丙', aux1: '戊', aux2: '庚' }, '午': { main: '丁', aux1: '己' }, '未': { main: '己', aux1: '丁', aux2: '乙' },
      '申': { main: '庚', aux1: '壬', aux2: '戊' }, '酉': { main: '辛' }, '戌': { main: '戊', aux1: '辛', aux2: '丁' }, '亥': { main: '壬', aux1: '甲' },
    }
    const nayinMap: Record<string, string> = {
      '甲子': '海中金', '乙丑': '海中金', '丙寅': '炉中火', '丁卯': '炉中火', '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
      '壬申': '剑锋金', '癸酉': '剑锋金', '甲戌': '山头火', '乙亥': '山头火', '丙子': '涧下水', '丁丑': '涧下水', '戊寅': '城头土', '己卯': '城头土',
      '庚辰': '白蜡金', '辛巳': '白蜡金', '壬午': '杨柳木', '癸未': '杨柳木', '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
      '戊子': '霹雳火', '己丑': '霹雳火', '庚寅': '松柏木', '辛卯': '松柏木', '壬辰': '长流水', '癸巳': '长流水', '甲午': '沙中金', '乙未': '沙中金',
      '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
    }
    if (!baziDetails.value) return null
    const details = baziDetails.value
    return {
      year: { branch: details.year.branch, canggan: branchCanggan[details.year.branch], nayin: nayinMap[details.year.stem + details.year.branch] },
      month: { branch: details.month.branch, canggan: branchCanggan[details.month.branch], nayin: nayinMap[details.month.stem + details.month.branch] },
      day: { branch: details.day.branch, canggan: branchCanggan[details.day.branch], nayin: nayinMap[details.day.stem + details.day.branch] },
      hour: { branch: details.hour.branch, canggan: branchCanggan[details.hour.branch], nayin: nayinMap[details.hour.stem + details.hour.branch] },
    }
  })

  const baziShenshaList = computed<BaziShenshaItem[]>(() => {
    if (!baziDetails.value) return []
    const details = baziDetails.value
    const branches = [details.year.branch, details.month.branch, details.day.branch, details.hour.branch]
    const branchLabels = ['年柱', '月柱', '日柱', '时柱']
    const findHit = (targets: string[]) => branches.map((b, idx) => (targets.includes(b) ? branchLabels[idx] : '')).filter(Boolean)
    const dayStem = details.day.stem
    const dayBranch = details.day.branch
    const yearBranch = details.year.branch
    const tianyiMap: Record<string, string[]> = {
      '甲': ['丑', '未'], '乙': ['子', '申'], '丙': ['亥', '酉'], '丁': ['亥', '酉'], '戊': ['丑', '未'], '己': ['子', '申'], '庚': ['寅', '午'], '辛': ['寅', '午'], '壬': ['卯', '巳'], '癸': ['卯', '巳'],
    }
    const taohuaMap: Record<string, string> = { '申': '酉', '子': '酉', '辰': '酉', '寅': '卯', '午': '卯', '戌': '卯', '亥': '子', '卯': '子', '未': '子', '巳': '午', '酉': '午', '丑': '午' }
    const yimaMap: Record<string, string> = { '申': '寅', '子': '寅', '辰': '寅', '寅': '申', '午': '申', '戌': '申', '亥': '巳', '卯': '巳', '未': '巳', '巳': '亥', '酉': '亥', '丑': '亥' }
    const huagaiMap: Record<string, string> = { '申': '辰', '子': '辰', '辰': '辰', '寅': '戌', '午': '戌', '戌': '戌', '亥': '未', '卯': '未', '未': '未', '巳': '丑', '酉': '丑', '丑': '丑' }
    const resultList: BaziShenshaItem[] = []
    const tianyiHit = findHit(tianyiMap[dayStem] || [])
    if (tianyiHit.length) resultList.push({ name: '天乙贵人', level: '吉', hit: tianyiHit, reason: `以日干${dayStem}查贵人位，命局见${(tianyiMap[dayStem] || []).join('、')}，主逢凶化吉。` })
    const taohuaTarget = taohuaMap[yearBranch] || taohuaMap[dayBranch]
    const taohuaHit = taohuaTarget ? findHit([taohuaTarget]) : []
    if (taohuaHit.length) resultList.push({ name: '桃花', level: '中', hit: taohuaHit, reason: `以年支/日支查桃花位，见${taohuaTarget}，人缘与情感互动较活跃。` })
    const yimaTarget = yimaMap[yearBranch] || yimaMap[dayBranch]
    const yimaHit = yimaTarget ? findHit([yimaTarget]) : []
    if (yimaHit.length) resultList.push({ name: '驿马', level: '中', hit: yimaHit, reason: `命局见驿马位${yimaTarget}，多主变动、奔波或跨地域机会。` })
    const huagaiTarget = huagaiMap[yearBranch] || huagaiMap[dayBranch]
    const huagaiHit = huagaiTarget ? findHit([huagaiTarget]) : []
    if (huagaiHit.length) resultList.push({ name: '华盖', level: '中', hit: huagaiHit, reason: `命局临华盖位${huagaiTarget}，偏向思辨、艺术与独处沉淀。` })
    const wuxingWeak = ['木', '火', '土', '金', '水'].filter((e) => baziWuxingCount(e) === Math.min(...['木', '火', '土', '金', '水'].map((x) => baziWuxingCount(x))))
    if (wuxingWeak.length > 0) resultList.push({ name: '五行偏枯提示', level: '警', hit: ['全盘'], reason: `当前偏弱五行为${wuxingWeak.join('、')}，建议在起名、行业与作息中做补益。` })
    return resultList
  })

  const baziRelationAnalyze = computed<BaziRelationAnalyze>(() => {
    if (!baziDetails.value) return { branchRelations: [], stemRelations: [] }
    const details = baziDetails.value
    const pillarData = [
      { key: '年柱', stem: details.year.stem, branch: details.year.branch },
      { key: '月柱', stem: details.month.stem, branch: details.month.branch },
      { key: '日柱', stem: details.day.stem, branch: details.day.branch },
      { key: '时柱', stem: details.hour.stem, branch: details.hour.branch },
    ]
    const liuhe = new Map<string, string>([['子', '丑'], ['寅', '亥'], ['卯', '戌'], ['辰', '酉'], ['巳', '申'], ['午', '未']])
    const liuchong = new Map<string, string>([['子', '午'], ['丑', '未'], ['寅', '申'], ['卯', '酉'], ['辰', '戌'], ['巳', '亥']])
    const xiangxingGroups = [['寅', '巳', '申'], ['丑', '未', '戌']]
    const ziMaoXing = ['子', '卯']
    const stemHe = new Map<string, string>([['甲', '己'], ['乙', '庚'], ['丙', '辛'], ['丁', '壬'], ['戊', '癸']])
    const stemKe: Record<string, string[]> = { '甲': ['戊', '己'], '乙': ['戊', '己'], '丙': ['庚', '辛'], '丁': ['庚', '辛'], '戊': ['壬', '癸'], '己': ['壬', '癸'], '庚': ['甲', '乙'], '辛': ['甲', '乙'], '壬': ['丙', '丁'], '癸': ['丙', '丁'] }
    const branchRelations: BaziRelationItem[] = []
    const stemRelations: BaziRelationItem[] = []
    for (let i = 0; i < pillarData.length; i++) {
      for (let j = i + 1; j < pillarData.length; j++) {
        const A = pillarData[i]
        const B = pillarData[j]
        if (liuhe.get(A.branch) === B.branch || liuhe.get(B.branch) === A.branch) branchRelations.push({ type: '六合', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
        if (liuchong.get(A.branch) === B.branch || liuchong.get(B.branch) === A.branch) branchRelations.push({ type: '六冲', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
        if (xiangxingGroups.some((g) => g.includes(A.branch) && g.includes(B.branch)) || (ziMaoXing.includes(A.branch) && ziMaoXing.includes(B.branch))) branchRelations.push({ type: '相刑', a: A.branch, b: B.branch, pillars: `${A.key} - ${B.key}` })
        if (stemHe.get(A.stem) === B.stem || stemHe.get(B.stem) === A.stem) stemRelations.push({ type: '天干合', a: A.stem, b: B.stem, pillars: `${A.key} - ${B.key}` })
        if ((stemKe[A.stem] || []).includes(B.stem) || (stemKe[B.stem] || []).includes(A.stem)) stemRelations.push({ type: '天干克', a: A.stem, b: B.stem, pillars: `${A.key} - ${B.key}` })
      }
    }
    return { branchRelations, stemRelations }
  })

  const baziGejuYongshen = computed<BaziGejuYongshen | null>(() => {
    if (!baziDetails.value || !shiShenAnalyze.value) return null
    const details = baziDetails.value
    const rel = shiShenAnalyze.value.relations
    const otherStems = [details.year.stem, details.month.stem, details.hour.stem]
    const countMap: Record<string, number> = {}
    otherStems.forEach((stem) => {
      const r = rel[stem]
      if (!r) return
      countMap[r] = (countMap[r] || 0) + 1
    })
    const dominant = Object.entries(countMap).sort((a, b) => b[1] - a[1])[0]?.[0] || '比肩'
    const gejuMap: Record<string, string> = {
      '正官': '正官格倾向', '七杀': '七杀格倾向', '正财': '财格倾向', '偏财': '偏财格倾向', '食神': '食神格倾向', '伤官': '伤官格倾向', '正印': '印绶格倾向', '偏印': '偏印格倾向', '比肩': '比劫格倾向', '劫财': '比劫格倾向',
    }
    const wuxingAll = ['木', '火', '土', '金', '水']
    const counts = wuxingAll.map((element) => ({ element, count: baziWuxingCount(element) }))
    const minCount = Math.min(...counts.map((x) => x.count))
    const maxCount = Math.max(...counts.map((x) => x.count))
    const favor = counts.filter((x) => x.count === minCount).map((x) => x.element)
    const avoid = counts.filter((x) => x.count === maxCount).map((x) => x.element)
    return {
      dominant,
      gejuName: gejuMap[dominant] || '综合平衡格局',
      favor,
      avoid,
      rationale: `以月令与透干关系估算，当前十神主导为${dominant}；结合五行分布，宜补${favor.join('、')}，慎过旺之${avoid.join('、')}。`,
    }
  })

  const baziLuckOverview = computed<BaziLuckOverview>(() => {
    const dayunItems = (options.result.value?.dayun?.items || []) as unknown as Array<Record<string, unknown>>
    const liuyueItems = (options.result.value?.liuyue || []) as unknown as Array<Record<string, unknown>>
    const liunian = (options.result.value?.liunian || null) as Record<string, unknown> | null
    const dayun = dayunItems.slice(0, 8).map((item, idx) => {
      const stem = String(item.stem || '')
      const branch = String(item.branch || '')
      const ganzhi = String(item.ganzhi || `${stem}${branch}`)
      return {
        rawIdx: idx,
        idx: idx + 1,
        ganzhi,
        startAge: Number(item.start_age || 0),
        endAge: Number(item.end_age || 0),
        startYear: Number(item.start_year || 0),
        isCurrent: options.currentDayunGz.value ? options.currentDayunGz.value === ganzhi : false,
      }
    })
    const liuyue = liuyueItems.slice(0, 12).map((m) => ({
      month: Number(m.month || 0),
      monthName: String(m.month_name || `${m.month || ''}月`),
      monthGz: String(m.month_gz || ''),
      palace: String(m.palace_name || ''),
    }))
    return {
      currentDayun: options.currentDayunGz.value || '',
      dayun,
      liunianYear: Number(liunian?.year || 0),
      liunianGz: String(liunian?.ganzhi || ''),
      liuyue,
    }
  })

  const baziDayunFocusDetail = computed<BaziDayunFocusDetail | null>(() => {
    const dayunItems = (options.result.value?.dayun?.items || []) as unknown as Array<Record<string, unknown>>
    if (!dayunItems.length) return null
    let idx = options.baziDayunFocusIdx.value
    if (idx < 0 || idx >= dayunItems.length) {
      idx = dayunItems.findIndex((item) => {
        const gz = String(item.ganzhi || `${String(item.stem || '')}${String(item.branch || '')}`)
        return options.currentDayunGz.value ? gz === options.currentDayunGz.value : false
      })
      if (idx < 0) idx = 0
    }
    const item = dayunItems[idx]
    const ganzhi = String(item.ganzhi || `${String(item.stem || '')}${String(item.branch || '')}`)
    return {
      idx: idx + 1,
      rawIdx: idx,
      ganzhi,
      startAge: Number(item.start_age || 0),
      endAge: Number(item.end_age || 0),
      startYear: Number(item.start_year || 0),
      tenGod: String(item.ten_god || ''),
      narrative: String(item.narrative || ''),
    }
  })

  const baziFocusedDayunSihuaStars = computed(() => {
    const dayunItems = (options.result.value?.dayun?.items || []) as unknown as Array<Record<string, unknown>>
    if (!dayunItems.length || !baziDayunFocusDetail.value) return [] as string[]
    const item = dayunItems[baziDayunFocusDetail.value.rawIdx]
    if (!item || typeof item !== 'object') return [] as string[]
    const sihua = (item.sihua || {}) as Record<string, unknown>
    return Object.keys(sihua)
  })

  const baziRelatedLiuyueMap = computed(() => {
    const liuyueItems = (options.result.value?.liuyue || []) as unknown as Array<Record<string, unknown>>
    const dayunStars = baziFocusedDayunSihuaStars.value
    const related: Record<number, number> = {}
    if (!liuyueItems.length || !dayunStars.length) return related
    const dayunSet = new Set(dayunStars)
    liuyueItems.forEach((m) => {
      const month = Number(m.month || 0)
      if (!month) return
      const monthSihua = (m.sihua || {}) as Record<string, unknown>
      const monthStars = Object.keys(monthSihua)
      const matched = monthStars.filter((s) => dayunSet.has(s)).length
      if (matched > 0) related[month] = matched
    })
    return related
  })

  const baziTenGodUsage = computed<BaziTenGodUsageItem[]>(() => {
    if (!baziDetails.value || !shiShenAnalyze.value) return []
    const details = baziDetails.value
    const dayMasterRel = shiShenAnalyze.value.relations
    const usageMap: Record<string, string> = {
      '比肩': '适合自主与并行发展，宜强化执行与自我边界。', '劫财': '强调资源调配与竞争意识，需注意财务分配。', '食神': '利输出与口碑沉淀，适合长期主义路径。', '伤官': '表达力强，利创新突破，注意节奏与规则平衡。', '偏财': '利市场与机会型收益，宜重风控。', '正财': '利稳健经营与现金流管理，适合可持续积累。', '七杀': '目标导向强，利攻坚，需配套情绪与压力管理。', '正官': '利组织与制度体系，适合走规范路径。', '偏印': '利学习与研究，适合策略型岗位。', '正印': '利贵人与资质提升，适合长期进修与背书。',
    }
    const items = [
      { pillar: '年柱（外部环境）', stem: details.year.stem },
      { pillar: '月柱（事业核心）', stem: details.month.stem },
      { pillar: '日柱（自我关系）', stem: details.day.stem },
      { pillar: '时柱（晚景与产出）', stem: details.hour.stem },
    ]
    return items.map((item) => {
      const tenGod = dayMasterRel[item.stem] || '比肩'
      return { pillar: item.pillar, stem: item.stem, tenGod, interpretation: usageMap[tenGod] || '可结合大运流年进一步细化。' }
    })
  })

  return {
    baziDetails,
    shiShenAnalyze,
    cangganNayin,
    baziShenshaList,
    baziRelationAnalyze,
    baziGejuYongshen,
    baziLuckOverview,
    baziDayunFocusDetail,
    baziFocusedDayunSihuaStars,
    baziRelatedLiuyueMap,
    baziTenGodUsage,
    baziWuxingCount,
  }
}
