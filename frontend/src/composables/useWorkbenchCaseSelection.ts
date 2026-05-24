import type { Ref } from 'vue'
import type { Router } from 'vue-router'
import { createCase, type CaseOut } from '@/api/report'
import type { ZiweiResponse } from '@/api/ziwei'
import { useAiStore } from '@/stores/ai'
import { useNavStore } from '@/stores/nav'
import { useProfileStore } from '@/stores/profile'
import { useReportStore } from '@/stores/report'
import { useUiStore } from '@/stores/ui'
import type { NullableRef, WorkbenchBaziLike, WorkbenchCaseLoader, WorkbenchSectionPredicate } from '@/composables/workbenchTypes'

type UseWorkbenchCaseSelectionOptions = {
  store: ReturnType<typeof useReportStore>
  ai: ReturnType<typeof useAiStore>
  nav: ReturnType<typeof useNavStore>
  ui: ReturnType<typeof useUiStore>
  profile: ReturnType<typeof useProfileStore>
  router: Router
  selectedId: Ref<string | null>
  caseDetail: Ref<CaseOut | null>
  localBazi: NullableRef<WorkbenchBaziLike>
  localZiwei: NullableRef<ZiweiResponse>
  ziweiError: Ref<string | null>
  selectedZiweiPalaceName: Ref<string | null>
  selectedZiweiDayunIndex: Ref<number | null>
  selectedZiweiLiuyueMonth: Ref<number | null>
  selectedIndicatorShensha: Ref<string | null>
  loadBaziForCase: WorkbenchCaseLoader
  loadZiweiForCase: WorkbenchCaseLoader
  isZiweiSectionId: WorkbenchSectionPredicate
  profileSyncTag: string
  profileSyncMark: string
}

export function useWorkbenchCaseSelection(options: UseWorkbenchCaseSelectionOptions) {
  async function selectCase(currentCase: CaseOut) {
    if (options.selectedId.value === currentCase.id) {
      return
    }

    options.selectedId.value = currentCase.id
    options.caseDetail.value = currentCase
    options.ai.setCurrentCase(currentCase.id)
    options.localZiwei.value = null
    options.ziweiError.value = null
    options.selectedZiweiPalaceName.value = null
    options.selectedZiweiDayunIndex.value = null
    options.selectedZiweiLiuyueMonth.value = new Date().getMonth() + 1
    options.selectedIndicatorShensha.value = null

    if (options.isZiweiSectionId(options.nav.currentSectionId)) {
      await Promise.all([options.loadBaziForCase(currentCase), options.loadZiweiForCase(currentCase)])
    } else {
      await options.loadBaziForCase(currentCase)
    }

    if (options.localBazi.value) {
      options.ai.setCurrentCase(currentCase.id, options.localBazi.value.request_id)
    }
  }

  function normalizeBirthMinute(value: string | null | undefined): string {
    if (!value) return ''
    const raw = value.trim().replace(' ', 'T')
    if (!raw) return ''
    return raw.length >= 16 ? raw.slice(0, 16) : raw
  }

  function buildProfileCaseName(): string {
    const surname = (options.profile.surname || '').trim()
    if (surname) return `${surname}氏档案`
    return '个人信息档案'
  }

  function isProfileSyncedCase(currentCase: CaseOut): boolean {
    const tags = currentCase.tags ?? []
    return tags.includes(options.profileSyncTag) || (currentCase.notes ?? '').includes(options.profileSyncMark)
  }

  function isCaseMatchingProfile(currentCase: CaseOut): boolean {
    const profileBirth = normalizeBirthMinute(options.profile.birthDt)
    const caseBirth = normalizeBirthMinute(currentCase.birth_dt_local)
    const caseLon = Number(currentCase.lon)
    const profileLon = Number(options.profile.lon)
    const profileGender = options.profile.gender || null
    return (
      caseBirth === profileBirth
      && currentCase.tz === options.profile.tz
      && Number.isFinite(caseLon)
      && Number.isFinite(profileLon)
      && Math.abs(caseLon - profileLon) < 0.001
      && (currentCase.gender ?? null) === profileGender
      && (currentCase.city ?? '') === (options.profile.cityName ?? '')
      && currentCase.solar_time_enabled === options.profile.solarTime
    )
  }

  async function ensureProfileSyncedCase(): Promise<CaseOut | null> {
    if (!options.profile.saved) return null
    if (!options.profile.birthDt || options.profile.lon === undefined || !options.profile.tz) return null

    const existing = (options.store.caseList ?? []).find(currentCase => isProfileSyncedCase(currentCase) && isCaseMatchingProfile(currentCase))
    if (existing) return existing

    return createCase({
      name: buildProfileCaseName(),
      birth_dt_local: `${normalizeBirthMinute(options.profile.birthDt)}:00`,
      tz: options.profile.tz,
      lon: Number(options.profile.lon),
      gender: options.profile.gender || null,
      city: options.profile.cityName || null,
      solar_time_enabled: options.profile.solarTime,
      notes: `${options.profileSyncMark} 自动由“个人信息”同步`,
      tags: [options.profileSyncTag],
    })
  }

  async function syncProfileToWorkbenchCase(): Promise<void> {
    if (!options.profile.saved || !options.profile.birthDt || options.profile.lon === undefined) {
      alert('请先在“个人信息”页保存完整出生信息')
      options.router.push('/profile')
      return
    }
    try {
      const profileCase = await ensureProfileSyncedCase()
      if (!profileCase) {
        alert('个人信息同步失败，请稍后重试')
        return
      }
      await options.store.loadCaseList()
      const matched = (options.store.caseList ?? []).find(currentCase => currentCase.id === profileCase.id)
      if (matched) {
        await selectCase(matched)
        options.nav.selectSection('bazi-birth')
        options.ui.openRightPanelIfAllowed()
        return
      }
      alert('同步案例创建成功，但未在列表中找到，请刷新页面重试')
    } catch (_error) {
      alert('同步个人信息到客户档案失败')
    }
  }

  return {
    selectCase,
    ensureProfileSyncedCase,
    syncProfileToWorkbenchCase,
  }
}
