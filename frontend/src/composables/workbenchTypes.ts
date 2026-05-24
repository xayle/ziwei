import type { Ref } from 'vue'
import type { CaseOut } from '@/api/report'

export type WorkbenchSectionId = string | null | undefined
export type WorkbenchSectionIdRef = Ref<WorkbenchSectionId>
export type NullableRef<T> = Ref<T | null>
export type WorkbenchCaseLoader = (currentCase: CaseOut) => Promise<void>
export type WorkbenchSectionPredicate = (sectionId: WorkbenchSectionId) => boolean

export type WorkbenchPillarKey = 'year' | 'month' | 'day' | 'hour'

export type WorkbenchBaziPillar = {
	stem: string
	branch: string
}

export type WorkbenchBaziPillarSet = Record<WorkbenchPillarKey, WorkbenchBaziPillar>
export type WorkbenchBaziTenGods = Record<WorkbenchPillarKey, string>

export type WorkbenchBaziDayunItem = {
	stem?: string
	branch?: string
	start_year?: number
	end_year?: number
	start_age?: number
	end_age?: number
	ten_god?: string
	flow_wuxing?: string
	wealth_hint?: string
	love_hint?: string
	health_hint?: string
	narrative?: string
}

export type WorkbenchBaziLiunianItem = {
	year: number
	stem: string
	branch: string
	ten_god?: string
	clash?: string | null
}

export type WorkbenchMonthlyFortuneItem = {
	month: number
	month_ganzhi?: string
	month_dizhi?: string
	luck_level: string
	color_hint?: string
}

export type WorkbenchBaziLiunianDetailItem = {
	year: number
	ganzhi?: string
	annual_score?: number
	ten_god?: string
	flow_wuxing?: string
	clash?: string
	domain_forecasts?: Record<string, string>
	tai_sui_relations?: string[]
	clash_pillars?: string[]
	notable_months?: number[]
	optimal_action?: string
	interpretation_text?: string
	inference_tags?: string[]
}

export type WorkbenchBaziShenshaItem = {
	name?: string
	pillar?: string
	is_beneficial: boolean
}

export type WorkbenchGejuLike = {
	geju_name?: string
	geju_level?: string
	name?: string
	level?: string
}

export type WorkbenchYongshenLike = {
	god_element?: string
	element?: string
	star?: string
	name?: string
	favor?: string[]
	avoid?: string[]
	rationale?: string | null
}

export type WorkbenchDayMasterStrengthLike = {
	score?: number
	tier?: string
}

export type WorkbenchCurrentFortuneSummaryLike = {
	current_dayun?: string
	dayun_years_remaining?: number
	current_liunian?: string
	this_year_domains?: Record<string, string>
	top3_actions?: string[]
}

export type WorkbenchBaziLike = {
	request_id?: string
	dayun?: { items?: WorkbenchBaziDayunItem[] | null } | null
	liunian?: { items?: WorkbenchBaziLiunianItem[] | null } | null
	wuxing_score?: {
		wood: number
		fire: number
		earth: number
		metal: number
		water: number
	} | null
	pillars_primary?: WorkbenchBaziPillarSet | null
	ten_gods?: WorkbenchBaziTenGods | null
	geju?: WorkbenchGejuLike | null
	yongshen?: WorkbenchYongshenLike | null
	bazi_summary?: string | null
	day_master_strength?: WorkbenchDayMasterStrengthLike | null
	liunian_detail?: WorkbenchBaziLiunianDetailItem[] | null
	monthly_fortune?: WorkbenchMonthlyFortuneItem[] | null
	wuxing_balance_score?: number | null
	balance_advice?: string | null
	wuxing_weak?: string[] | null
	wuxing_strong?: string[] | null
	shensha?: WorkbenchBaziShenshaItem[] | null
	current_fortune_summary?: WorkbenchCurrentFortuneSummaryLike | null
	[key: string]: unknown
}
