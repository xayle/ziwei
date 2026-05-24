import type { Ref } from 'vue'
import type { ZiweiResponse } from '@/api/ziwei'
import { buildPatternSummaryText } from '@/utils/ziweiNarrative'

export type BaziMenuKey = 'shengchen' | 'sizhu' | 'ribuzhu' | 'wuxing' | 'canggan' | 'shenshai' | 'chonghehexpo' | 'geju' | 'dayun' | 'shishen'

type BaziDetailsLike = {
  year: { stem: string; branch: string }
  month: { stem: string; branch: string }
  day: { stem: string; branch: string }
  hour: { stem: string; branch: string }
}

type ShiShenAnalyzeLike = {
  dayMaster: string
  relations?: Record<string, string>
}

type CangganNayinPillar = {
  canggan?: { main?: string; aux1?: string; aux2?: string }
  nayin?: string
}

type CangganNayinLike = {
  year?: CangganNayinPillar
  month?: CangganNayinPillar
  day?: CangganNayinPillar
  hour?: CangganNayinPillar
}

type ShenshaItem = {
  name: string
  level: '吉' | '中' | '警'
  hit: string[]
}

type RelationItem = {
  type: string
  a: string
  b: string
}

type BaziRelationLike = {
  branchRelations: RelationItem[]
  stemRelations: RelationItem[]
}

type BaziGejuYongshenLike = {
  gejuName: string
  favor: string[]
  avoid: string[]
  rationale: string
}

type BaziLuckOverviewLike = {
  currentDayun?: string
  liunianYear?: string | number
  liunianGz?: string
}

type BaziDayunFocusDetailLike = {
  ganzhi: string
  startAge: number
  endAge: number
}

type BaziTenGodUsageItem = {
  pillar: string
  stem: string
  tenGod: string
}

type UiLike = {
  openRightPanelIfAllowed: () => void
}

type AiLike = {
  sendMessage: (message: string, metadata?: Record<string, unknown>) => void
}

type UseZiweiNarrativeActionsOptions = {
  result: Ref<ZiweiResponse | null>
  ui: UiLike
  ai: AiLike
  baziMenuActive: Ref<BaziMenuKey>
  baziMenuItems: Record<BaziMenuKey, string>
  baziDetails: Ref<BaziDetailsLike | null>
  shiShenAnalyze: Ref<ShiShenAnalyzeLike | null>
  cangganNayin: Ref<CangganNayinLike | null>
  baziShenshaList: Ref<ShenshaItem[]>
  baziRelationAnalyze: Ref<BaziRelationLike>
  baziGejuYongshen: Ref<BaziGejuYongshenLike | null>
  baziLuckOverview: Ref<BaziLuckOverviewLike>
  baziDayunFocusDetail: Ref<BaziDayunFocusDetailLike | null>
  baziTenGodUsage: Ref<BaziTenGodUsageItem[]>
  baziCopyDone: Ref<boolean>
  baziWuxingCount: (element: string) => number
}

export function useZiweiNarrativeActions(options: UseZiweiNarrativeActionsOptions) {
  function gotoAi() {
    if (!options.result.value) return
    options.ui.openRightPanelIfAllowed()
    const lp = options.result.value.life_palace_gz
    const ju = options.result.value.wuxing_ju_name
    const pattern = typeof options.result.value.geju_name === 'string'
      ? options.result.value.geju_name
      : buildPatternSummaryText(options.result.value)

    options.ai.sendMessage(`请帮我解读紫微斗数命盘：命宫${lp}，${ju}，格局${pattern || '待分析'}。`, {
      life_palace_gz: lp,
      wuxing_ju_name: ju,
      pattern_summary: pattern,
      birth_info_summary: `命宫${lp} ${ju}`,
    })
  }

  function copyBaziSectionSummary() {
    if (!options.result.value) return

    const title = options.baziMenuItems[options.baziMenuActive.value] || '四柱摘要'
    const lines: string[] = [`【${title}】`]

    if (options.baziMenuActive.value === 'shengchen') {
      lines.push(`出生：${options.result.value.birth_solar} ${options.result.value.gender}`)
      lines.push(`农历：${options.result.value.lunar.lunar_year}年${options.result.value.lunar.is_leap_month ? '闰' : ''}${options.result.value.lunar.lunar_month}月${options.result.value.lunar.lunar_day}日 ${options.result.value.lunar.hour_branch}时`)
      if (options.result.value.true_solar_time) lines.push(`真太阳时：${options.result.value.true_solar_time}`)
    }

    if (options.baziMenuActive.value === 'sizhu' && options.baziDetails.value) {
      lines.push(`年柱：${options.baziDetails.value.year.stem}${options.baziDetails.value.year.branch}`)
      lines.push(`月柱：${options.baziDetails.value.month.stem}${options.baziDetails.value.month.branch}`)
      lines.push(`日柱：${options.baziDetails.value.day.stem}${options.baziDetails.value.day.branch}`)
      lines.push(`时柱：${options.baziDetails.value.hour.stem}${options.baziDetails.value.hour.branch}`)
    }

    if (options.baziMenuActive.value === 'ribuzhu' && options.shiShenAnalyze.value) {
      lines.push(`日主：${options.shiShenAnalyze.value.dayMaster}`)
      const core = ['甲', '乙', '丙', '丁']
        .map((s) => `${s}:${options.shiShenAnalyze.value?.relations?.[s] || '-'}`)
        .join('，')
      lines.push(`十神参考：${core}`)
    }

    if (options.baziMenuActive.value === 'wuxing') {
      lines.push(`五行分布：木${options.baziWuxingCount('木')} 火${options.baziWuxingCount('火')} 土${options.baziWuxingCount('土')} 金${options.baziWuxingCount('金')} 水${options.baziWuxingCount('水')}`)
    }

    if (options.baziMenuActive.value === 'canggan' && options.cangganNayin.value) {
      ;(['year', 'month', 'day', 'hour'] as const).forEach((key, idx) => {
        const pillar = options.cangganNayin.value?.[key]
        if (!pillar) return
        const cg = [pillar.canggan?.main, pillar.canggan?.aux1, pillar.canggan?.aux2].filter(Boolean).join('/')
        lines.push(`${['年', '月', '日', '时'][idx]}柱：藏干${cg || '-'}，纳音${pillar.nayin || '-'}`)
      })
    }

    if (options.baziMenuActive.value === 'shenshai') {
      if (options.baziShenshaList.value.length) {
        lines.push(...options.baziShenshaList.value.map((x) => `${x.name}（${x.level}）- ${x.hit.join('、')}`))
      } else {
        lines.push('当前命盘未检出显著神煞组合。')
      }
    }

    if (options.baziMenuActive.value === 'chonghehexpo') {
      const branch = options.baziRelationAnalyze.value.branchRelations.slice(0, 5).map((x) => `${x.type}:${x.a}${x.b}`).join('，')
      const stem = options.baziRelationAnalyze.value.stemRelations.slice(0, 5).map((x) => `${x.type}:${x.a}${x.b}`).join('，')
      lines.push(`地支：${branch || '平和'}`)
      lines.push(`天干：${stem || '平和'}`)
    }

    if (options.baziMenuActive.value === 'geju' && options.baziGejuYongshen.value) {
      lines.push(`格局：${options.baziGejuYongshen.value.gejuName}`)
      lines.push(`宜：${options.baziGejuYongshen.value.favor.join('、') || '-'}`)
      lines.push(`慎：${options.baziGejuYongshen.value.avoid.join('、') || '-'}`)
      lines.push(`说明：${options.baziGejuYongshen.value.rationale}`)
    }

    if (options.baziMenuActive.value === 'dayun') {
      lines.push(`当前大运：${options.baziLuckOverview.value.currentDayun || '未定位'}`)
      lines.push(`流年：${options.baziLuckOverview.value.liunianYear || '-'} ${options.baziLuckOverview.value.liunianGz || ''}`)
      if (options.baziDayunFocusDetail.value) {
        lines.push(`选中大运：${options.baziDayunFocusDetail.value.ganzhi}（${options.baziDayunFocusDetail.value.startAge}-${options.baziDayunFocusDetail.value.endAge}岁）`)
      }
    }

    if (options.baziMenuActive.value === 'shishen') {
      lines.push(...options.baziTenGodUsage.value.map((x) => `${x.pillar}：${x.stem}→${x.tenGod}`))
    }

    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      options.baziCopyDone.value = true
      setTimeout(() => {
        options.baziCopyDone.value = false
      }, 1400)
    })
  }

  return {
    gotoAi,
    copyBaziSectionSummary,
  }
}
