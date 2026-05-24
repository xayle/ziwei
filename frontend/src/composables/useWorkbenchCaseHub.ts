import { computed, type ComputedRef, type Ref } from 'vue'
import type { Router, RouteLocationNormalizedLoaded } from 'vue-router'
import type { CaseOut } from '@/api/report'
import { useNavStore } from '@/stores/nav'

export type WorkbenchActionTone = 'accent' | 'ghost'

export type WorkbenchOnboardAction = {
  key: string
  label: string
  tone: WorkbenchActionTone
}

export type WorkbenchCaseHubStatusItem = {
  label: string
  value: string
}

export type WorkbenchCaseHubAction = {
  key: string
  title: string
  desc: string
  button: string
  route: string
  tone: WorkbenchActionTone
  disabled: boolean
}

type UseWorkbenchCaseHubOptions = {
  route: RouteLocationNormalizedLoaded
  router: Router
  nav: ReturnType<typeof useNavStore>
  caseDetail: Ref<CaseOut | null>
  birthLocalText: ComputedRef<string>
  baziCaseSummaryLine: ComputedRef<string>
  ziweiCaseSummaryText: ComputedRef<string>
  genderLabel: (gender: string | null | undefined) => string
  isBaziSection: (sectionId: string | null | undefined) => boolean
  isZiweiSectionId: (sectionId: string | null | undefined) => boolean
  openCreateDialog: () => void
  syncProfileToWorkbenchCase: () => void | Promise<void>
  openEditDialog: () => void
}

type UseWorkbenchCaseHubReturn = {
  isCaseHubView: ComputedRef<boolean>
  caseHubSummary: ComputedRef<string>
  caseHubStatusItems: ComputedRef<WorkbenchCaseHubStatusItem[]>
  caseHubActions: ComputedRef<WorkbenchCaseHubAction[]>
  delegatedSectionTitle: ComputedRef<string>
  delegatedSectionSummary: ComputedRef<string>
  caseHubOnboardActions: WorkbenchOnboardAction[]
  delegatedSectionActions: ComputedRef<WorkbenchOnboardAction[]>
  openCaseHubAction: (targetRoute: string) => void
  handleCaseHubOnboardAction: (actionKey: string) => void | Promise<void>
  handleDelegatedSectionAction: (actionKey: string) => void
}

export function useWorkbenchCaseHub(options: UseWorkbenchCaseHubOptions): UseWorkbenchCaseHubReturn {
  const isCaseHubView = computed<boolean>(() => options.route.path === '/cases' && !options.nav.currentSectionId)

  const caseHubSummary = computed<string>(() => {
    if (!options.caseDetail.value) {
      return '这里优先承担客户选择、资料校对和咨询流程分发，不再默认平铺整套分析结果。'
    }

    const pieces = [
      `${options.caseDetail.value.name} · ${options.genderLabel(options.caseDetail.value.gender)}`,
      options.birthLocalText.value,
      options.caseDetail.value.city || options.caseDetail.value.tz || '地点待补充',
    ].filter(Boolean)

    return `${pieces.join(' ｜ ')}。先确认资料是否完整，再进入对应工作区继续分析、生成报告或整理草稿。`
  })

  const caseHubStatusItems = computed<WorkbenchCaseHubStatusItem[]>(() => {
    const locationText = options.caseDetail.value
      ? [options.caseDetail.value.city, options.caseDetail.value.tz].filter(Boolean).join(' ｜ ') || '待补充'
      : '待补充'

    return [
      {
        label: '当前客户',
        value: options.caseDetail.value
          ? `${options.caseDetail.value.name} · ${options.genderLabel(options.caseDetail.value.gender)}`
          : '尚未选择案例',
      },
      {
        label: '基础资料',
        value: options.caseDetail.value ? `${options.birthLocalText.value} ｜ ${locationText}` : '请先创建或选择案例',
      },
      {
        label: '八字进度',
        value: options.baziCaseSummaryLine.value || '进入八字分析页查看四柱、五行与流年主线',
      },
      {
        label: '紫微进度',
        value: options.ziweiCaseSummaryText.value || '进入紫微分析页查看十二宫、主星与流年结构',
      },
    ]
  })

  const caseHubActions = computed<WorkbenchCaseHubAction[]>(() => {
    const caseId = options.caseDetail.value?.id
    return [
      {
        key: 'bazi',
        title: '进入八字分析',
        desc: '查看四柱、十神、五行、格局与大运流年，把重点整理成咨询结论。',
        button: '开始八字分析',
        route: '/bazi',
        tone: 'accent',
        disabled: false,
      },
      {
        key: 'ziwei',
        title: '进入紫微分析',
        desc: '查看命宫、主星、三方四正与流月走势，继续提炼本次解读主线。',
        button: '开始紫微分析',
        route: '/ziwei',
        tone: 'ghost',
        disabled: false,
      },
      {
        key: 'report',
        title: '进入报告整理',
        desc: caseId ? '基于当前客户整理摘要、段落结构与导出结果。' : '先选择客户，再生成报告或查看章节输出。',
        button: '整理报告',
        route: caseId ? `/report/${caseId}` : '/report',
        tone: 'ghost',
        disabled: !caseId,
      },
      {
        key: 'drafts',
        title: '进入辅助草稿',
        desc: '把当前客户上下文交给 AI，生成草稿、解释稿和备选表达。',
        button: '查看参考草稿',
        route: '/llm/drafts',
        tone: 'ghost',
        disabled: false,
      },
    ]
  })

  const delegatedSectionRoute = computed(() => {
    const routeFromSection = options.nav.currentSection?.route
    if (routeFromSection && routeFromSection !== '/cases') return routeFromSection
    if (options.isBaziSection(options.nav.currentSectionId)) return '/bazi'
    if (options.isZiweiSectionId(options.nav.currentSectionId)) return '/ziwei'
    return '/cases'
  })

  const delegatedSectionTitle = computed<string>(() => {
    if (options.isBaziSection(options.nav.currentSectionId)) return '四柱八字分析页'
    if (options.isZiweiSectionId(options.nav.currentSectionId)) return '紫微斗数分析页'
    return options.nav.currentSection?.label || '当前工作区'
  })

  const delegatedSectionSummary = computed<string>(() => {
    if (options.isBaziSection(options.nav.currentSectionId)) {
      return '八字相关内容已经收拢到独立分析页，建议直接进入对应页面继续完成本次咨询。'
    }
    if (options.isZiweiSectionId(options.nav.currentSectionId)) {
      return '紫微相关内容已回到主盘分析页，这里只保留客户选择、资料校对和下一步分发。'
    }
    return '当前课题建议进入对应独立页面继续处理，这里不再承载整页分析。'
  })

  const caseHubOnboardActions: WorkbenchOnboardAction[] = [
    { key: 'create', label: '＋ 新建咨询', tone: 'accent' },
    { key: 'sync', label: '👤 同步客户资料', tone: 'ghost' },
    { key: 'bazi', label: '进入八字分析', tone: 'ghost' },
  ]

  const delegatedSectionActions = computed<WorkbenchOnboardAction[]>(() => [
    { key: 'create', label: '＋ 新建咨询', tone: 'accent' },
    { key: 'open', label: '继续当前分析', tone: 'ghost' },
    ...(options.caseDetail.value ? [{ key: 'edit', label: '补充客户资料', tone: 'ghost' as const }] : []),
  ])

  function openCaseHubAction(targetRoute: string): void {
    if (options.route.path === targetRoute) return
    options.router.push(targetRoute)
  }

  function handleCaseHubOnboardAction(actionKey: string): void | Promise<void> {
    if (actionKey === 'create') return options.openCreateDialog()
    if (actionKey === 'sync') return options.syncProfileToWorkbenchCase()
    if (actionKey === 'bazi') return openCaseHubAction('/bazi')
  }

  function handleDelegatedSectionAction(actionKey: string): void {
    if (actionKey === 'create') return options.openCreateDialog()
    if (actionKey === 'open') return openCaseHubAction(delegatedSectionRoute.value)
    if (actionKey === 'edit') return options.openEditDialog()
  }

  return {
    isCaseHubView,
    caseHubSummary,
    caseHubStatusItems,
    caseHubActions,
    delegatedSectionTitle,
    delegatedSectionSummary,
    caseHubOnboardActions,
    delegatedSectionActions,
    openCaseHubAction,
    handleCaseHubOnboardAction,
    handleDelegatedSectionAction,
  }
}
