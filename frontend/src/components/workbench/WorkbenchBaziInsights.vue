<script setup lang="ts">
interface DomainItem {
  key: string
  val: string
}

interface FortuneSummary {
  this_year_domains?: Record<string, string>
  top3_actions?: string[]
}

interface YongshenInfo {
  rationale?: string | null
}

interface GejuInfo {
  interpretation_text?: string | null
}

interface LiunianDetailItem {
  year: number
  ganzhi: string
  tenGod?: string | null
  flowWuxing?: string | null
  clash?: string | null
  annualScore: number
  isCurrent: boolean
  domains: DomainItem[]
  interpretationText?: string | null
  taiSuiRelations: string[]
  clashPillars: string[]
  notableMonths: number[]
  optimalAction?: string | null
  tags: string[]
}

interface BaziAnalysisData {
  wealth_analysis?: {
    wealth_score: number
    wealth_tier?: string | null
    annual_range?: string | null
    industries?: string[]
  } | null
  career?: {
    career_score: number
    career_directions?: string[]
    optimal_move_timing?: string | null
    suitable_industries?: string[]
  } | null
  marriage_analysis?: {
    marriage_score: number
    peach_blossom?: string | null
    partner_direction?: string | null
    marriage_windows?: string[]
  } | null
  health?: {
    health_score: number
    risk_level?: string | null
    risk_organs?: string[]
  } | null
  personality?: {
    core_trait?: string | null
    inference_tags?: string[]
    growth_advice?: string | null
  } | null
  life_arc?: {
    early_fortune?: string | null
    mid_fortune?: string | null
    late_fortune?: string | null
    overall_tier?: string | null
    peak_periods?: string[]
    caution_periods?: string[]
    life_motto?: string | null
  } | null
  lucky?: {
    lucky_colors?: string[]
    lucky_numbers?: Array<string | number>
    lucky_direction?: string | null
    lucky_item?: string | null
    avoid_colors?: string[]
    avoid_direction?: string | null
  } | null
  milestones?: Array<{
    age: number
    year: number
    ganzhi_context?: string | null
    milestone_type?: string | null
    description?: string | null
    advice?: string | null
    risk_level?: string | null
  }>
  relationship?: {
    noble_people?: string[]
    petty_people?: string[]
    liu_qin?: Record<string, string>
    social_strategy?: string | null
  } | null
  fengshui?: {
    auspicious_directions?: string[]
    decor?: string[]
    plants?: string[]
    taboo?: string[]
  } | null
  lifestyle?: {
    exercise?: string[]
    diet?: string[]
    best_times?: string | null
    travel_direction?: string | null
    sleep_advice?: string | null
  } | null
}

const props = defineProps<{
  currentYear: number
  simpleView: boolean
  summary?: string | null
  baziData?: BaziAnalysisData | null
  thisYearDetail?: { interpretation_text?: string | null } | null
  fortSummary?: FortuneSummary | null
  liunianDetailRows: LiunianDetailItem[]
  expandedLiunianDetailYear?: number | null
  activeLiuyueMonth?: number | null
  geju?: GejuInfo | null
  yongshen?: YongshenInfo | null
}>()

const emit = defineEmits<{
  (e: 'toggleLiunianDetail', year: number): void
  (e: 'selectLiunianMonth', payload: { year: number; month: number }): void
}>()

function scoreColor(score: number): string {
  return score >= 70 ? '#16a34a' : score >= 40 ? '#d97706' : '#dc2626'
}
</script>

<template>
  <div class="wb-bazi-insights">
    <div v-if="props.summary && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">综合解读</h2>
      <div class="wb-interpret-body">{{ props.summary }}</div>
    </div>

    <div v-if="(props.baziData?.wealth_analysis || props.baziData?.career || props.baziData?.marriage_analysis || props.baziData?.health) && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">四维分析</h2>
      <div class="wb-quadrant-grid">
        <div v-if="props.baziData?.wealth_analysis" class="wb-quad-card">
          <div class="wb-quad-head">
            <span class="wb-quad-icon">💰</span>
            <span class="wb-quad-label">财运</span>
            <span class="wb-quad-score" :style="{ color: scoreColor(props.baziData.wealth_analysis.wealth_score) }">
              {{ props.baziData.wealth_analysis.wealth_score }}
            </span>
          </div>
          <div class="wb-quad-tier">{{ props.baziData.wealth_analysis.wealth_tier }}</div>
          <div class="wb-quad-range">年入参考：{{ props.baziData.wealth_analysis.annual_range }}</div>
          <div v-if="props.baziData.wealth_analysis.industries?.length" class="wb-quad-tags">
            <span v-for="ind in props.baziData.wealth_analysis.industries.slice(0, 3)" :key="ind" class="wb-tag">{{ ind }}</span>
          </div>
        </div>
        <div v-if="props.baziData?.career" class="wb-quad-card">
          <div class="wb-quad-head">
            <span class="wb-quad-icon">💼</span>
            <span class="wb-quad-label">事业</span>
            <span class="wb-quad-score" :style="{ color: scoreColor(props.baziData.career.career_score) }">
              {{ props.baziData.career.career_score }}
            </span>
          </div>
          <div v-if="props.baziData.career.career_directions?.length" class="wb-quad-tier">{{ props.baziData.career.career_directions.slice(0, 2).join('／') }}</div>
          <div class="wb-quad-range">展期：{{ props.baziData.career.optimal_move_timing }}</div>
          <div v-if="props.baziData.career.suitable_industries?.length" class="wb-quad-tags">
            <span v-for="ind in props.baziData.career.suitable_industries.slice(0, 3)" :key="ind" class="wb-tag">{{ ind }}</span>
          </div>
        </div>
        <div v-if="props.baziData?.marriage_analysis" class="wb-quad-card">
          <div class="wb-quad-head">
            <span class="wb-quad-icon">❤️</span>
            <span class="wb-quad-label">婚恋</span>
            <span class="wb-quad-score" :style="{ color: scoreColor(props.baziData.marriage_analysis.marriage_score) }">
              {{ props.baziData.marriage_analysis.marriage_score }}
            </span>
          </div>
          <div class="wb-quad-tier">桃花：{{ props.baziData.marriage_analysis.peach_blossom }} &nbsp;配对方位：{{ props.baziData.marriage_analysis.partner_direction }}</div>
          <div v-if="props.baziData.marriage_analysis.marriage_windows?.length" class="wb-quad-tags">
            <span v-for="w in props.baziData.marriage_analysis.marriage_windows.slice(0, 2)" :key="w" class="wb-tag">{{ w }}</span>
          </div>
        </div>
        <div v-if="props.baziData?.health" class="wb-quad-card">
          <div class="wb-quad-head">
            <span class="wb-quad-icon">🏥</span>
            <span class="wb-quad-label">健康</span>
            <span class="wb-quad-score" :style="{ color: scoreColor(props.baziData.health.health_score) }">
              {{ props.baziData.health.health_score }}
            </span>
          </div>
          <div class="wb-quad-tier">风险：{{ props.baziData.health.risk_level }}</div>
          <div v-if="props.baziData.health.risk_organs?.length" class="wb-quad-tags">
            <span v-for="org in props.baziData.health.risk_organs.slice(0, 4)" :key="org" class="wb-tag">{{ org }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="props.baziData?.personality && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">性格分析</h2>
      <div class="wb-personality-box">
        <p class="wb-personality-core">{{ props.baziData.personality.core_trait }}</p>
        <div v-if="props.baziData.personality.inference_tags?.length" class="wb-chip-list" style="margin-top:10px;">
          <span v-for="tag in props.baziData.personality.inference_tags" :key="tag" class="wb-chip good">{{ tag }}</span>
        </div>
        <p v-if="props.baziData.personality.growth_advice" class="wb-personality-advice">成长建议：{{ props.baziData.personality.growth_advice }}</p>
      </div>
    </div>

    <div v-if="props.thisYearDetail || props.fortSummary" class="wb-section">
      <h2 class="wb-sec-title">{{ props.currentYear }} 年运势</h2>
      <div class="wb-fortune-wrap">
        <div v-if="props.thisYearDetail?.interpretation_text" class="wb-fortune-text">
          {{ props.thisYearDetail.interpretation_text }}
        </div>
        <div v-if="props.fortSummary?.this_year_domains" class="wb-domains">
          <div v-for="(val, domain) in props.fortSummary.this_year_domains" :key="String(domain)" class="wb-domain-item">
            <span class="wb-domain-key">{{ domain }}</span>
            <span class="wb-domain-val">{{ val }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="props.liunianDetailRows.length && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">流年四维详情 <span class="wb-sec-note">近 5 年</span></h2>
      <div class="wb-lyd-list">
        <div
          v-for="detail in props.liunianDetailRows"
          :key="detail.year"
          class="wb-lyd-card"
          :class="{ current: detail.isCurrent, expanded: props.expandedLiunianDetailYear === detail.year }"
        >
          <button
            type="button"
            class="wb-lyd-head wb-lyd-toggle"
            @click="emit('toggleLiunianDetail', detail.year)"
          >
            <div>
              <div class="wb-lyd-year">{{ detail.year }} · {{ detail.ganzhi }}</div>
              <div class="wb-lyd-meta">
                <span v-if="detail.tenGod">十神：{{ detail.tenGod }}</span>
                <span v-if="detail.flowWuxing">五行：{{ detail.flowWuxing }}</span>
                <span v-if="detail.clash">冲克：{{ detail.clash }}</span>
              </div>
            </div>
            <div class="wb-lyd-head-right">
              <div class="wb-lyd-score" :class="detail.annualScore >= 70 ? 'good' : detail.annualScore >= 40 ? 'mid' : 'bad'">
                {{ detail.annualScore }}
              </div>
              <span class="wb-lyd-arrow" :class="{ expanded: props.expandedLiunianDetailYear === detail.year }">▾</span>
            </div>
          </button>

          <div v-if="props.expandedLiunianDetailYear === detail.year && detail.domains.length" class="wb-lyd-domains">
            <div v-for="item in detail.domains" :key="item.key" class="wb-lyd-domain">
              <span class="wb-lyd-domain-key">{{ item.key }}</span>
              <span class="wb-lyd-domain-val">{{ item.val }}</span>
            </div>
          </div>

          <div v-if="props.expandedLiunianDetailYear === detail.year && detail.interpretationText" class="wb-lyd-text">
            {{ detail.interpretationText }}
          </div>

          <div v-if="props.expandedLiunianDetailYear === detail.year && (detail.taiSuiRelations.length || detail.clashPillars.length || detail.notableMonths.length)" class="wb-lyd-extra">
            <div v-if="detail.taiSuiRelations.length" class="wb-lyd-block">
              <span class="wb-lyd-label">太岁关系</span>
              <div class="wb-chip-list">
                <span v-for="rel in detail.taiSuiRelations" :key="rel" class="wb-chip">{{ rel }}</span>
              </div>
            </div>
            <div v-if="detail.clashPillars.length" class="wb-lyd-block">
              <span class="wb-lyd-label">冲柱提示</span>
              <div class="wb-chip-list">
                <span v-for="pillar in detail.clashPillars" :key="pillar" class="wb-chip bad">{{ pillar }}</span>
              </div>
            </div>
            <div v-if="detail.notableMonths.length" class="wb-lyd-block">
              <span class="wb-lyd-label">关键月份</span>
              <div class="wb-chip-list">
                <button
                  v-for="month in detail.notableMonths"
                  :key="month"
                  type="button"
                  class="wb-chip good wb-month-chip"
                  :class="{ active: detail.year === props.currentYear && month === props.activeLiuyueMonth }"
                  @click="emit('selectLiunianMonth', { year: detail.year, month })"
                >{{ month }}月</button>
              </div>
            </div>
          </div>

          <div v-if="props.expandedLiunianDetailYear === detail.year && (detail.optimalAction || detail.tags.length)" class="wb-lyd-foot">
            <div v-if="detail.optimalAction" class="wb-lyd-action">建议动作：{{ detail.optimalAction }}</div>
            <div v-if="detail.tags.length" class="wb-chip-list">
              <span v-for="tag in detail.tags" :key="tag" class="wb-chip">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="props.fortSummary?.top3_actions?.length && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">建议与注意事项</h2>
      <ol class="wb-advice-list">
        <li v-for="(a, i) in props.fortSummary.top3_actions" :key="i" class="wb-advice-item">
          {{ a }}
        </li>
      </ol>
    </div>

    <div v-if="props.geju?.interpretation_text && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">详细格局解读</h2>
      <div class="wb-quote-block">
        <p class="wb-quote-text">{{ props.geju.interpretation_text }}</p>
        <p v-if="props.yongshen?.rationale" class="wb-quote-note">用神说明：{{ props.yongshen.rationale }}</p>
      </div>
    </div>

    <div v-if="props.baziData?.life_arc && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">生命弧线</h2>
      <div class="wb-lifearc-grid">
        <div class="wb-larc-card">
          <div class="wb-larc-label">早年</div>
          <div class="wb-larc-val">{{ props.baziData.life_arc.early_fortune }}</div>
        </div>
        <div class="wb-larc-card">
          <div class="wb-larc-label">中年</div>
          <div class="wb-larc-val">{{ props.baziData.life_arc.mid_fortune }}</div>
        </div>
        <div class="wb-larc-card">
          <div class="wb-larc-label">晚年</div>
          <div class="wb-larc-val">{{ props.baziData.life_arc.late_fortune }}</div>
        </div>
        <div class="wb-larc-card wb-larc-tier">
          <div class="wb-larc-label">整体层次</div>
          <div class="wb-larc-val">{{ props.baziData.life_arc.overall_tier }}</div>
        </div>
      </div>
      <div v-if="props.baziData.life_arc.peak_periods?.length || props.baziData.life_arc.caution_periods?.length" class="wb-larc-periods">
        <div v-if="props.baziData.life_arc.peak_periods?.length" class="wb-larc-period good">
          <span class="wb-lp-label">峰值期</span>
          <div class="wb-chip-list">
            <span v-for="p in props.baziData.life_arc.peak_periods" :key="p" class="wb-chip good">{{ p }}</span>
          </div>
        </div>
        <div v-if="props.baziData.life_arc.caution_periods?.length" class="wb-larc-period bad">
          <span class="wb-lp-label">谨慎期</span>
          <div class="wb-chip-list">
            <span v-for="p in props.baziData.life_arc.caution_periods" :key="p" class="wb-chip bad">{{ p }}</span>
          </div>
        </div>
      </div>
      <div v-if="props.baziData.life_arc.life_motto" class="wb-larc-motto">箴言：「{{ props.baziData.life_arc.life_motto }}」</div>
    </div>

    <div v-if="props.baziData?.lucky && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">开运建议</h2>
      <div class="wb-lucky-grid">
        <div class="wb-lucky-item">
          <span class="wb-lucky-label">幸运色</span>
          <div class="wb-lucky-colors">
            <span v-for="c in props.baziData.lucky.lucky_colors" :key="c" class="wb-color-chip">{{ c }}</span>
          </div>
        </div>
        <div class="wb-lucky-item">
          <span class="wb-lucky-label">幸运数字</span>
          <span class="wb-lucky-val">{{ props.baziData.lucky.lucky_numbers?.join('、') }}</span>
        </div>
        <div class="wb-lucky-item">
          <span class="wb-lucky-label">幸运方位</span>
          <span class="wb-lucky-val">{{ props.baziData.lucky.lucky_direction }}</span>
        </div>
        <div class="wb-lucky-item">
          <span class="wb-lucky-label">开运物品</span>
          <span class="wb-lucky-val">{{ props.baziData.lucky.lucky_item }}</span>
        </div>
        <div v-if="props.baziData.lucky.avoid_colors?.length" class="wb-lucky-item">
          <span class="wb-lucky-label">忌色</span>
          <div class="wb-lucky-colors">
            <span v-for="c in props.baziData.lucky.avoid_colors" :key="c" class="wb-color-chip avoid">{{ c }}</span>
          </div>
        </div>
        <div v-if="props.baziData.lucky.avoid_direction" class="wb-lucky-item">
          <span class="wb-lucky-label">忌方位</span>
          <span class="wb-lucky-val">{{ props.baziData.lucky.avoid_direction }}</span>
        </div>
      </div>
    </div>

    <div v-if="props.baziData?.milestones?.length && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">人生里程碑</h2>
      <div class="wb-milestone-list">
        <div v-for="(ms, idx) in props.baziData.milestones" :key="idx" class="wb-ms-item" :class="{ 'ms-risk': ms.risk_level === '高', 'ms-warn': ms.risk_level === '中' }">
          <div class="wb-ms-meta">
            <span class="wb-ms-age">{{ ms.age }}岁</span>
            <span class="wb-ms-year">({{ ms.year }}年)</span>
            <span class="wb-ms-gz">{{ ms.ganzhi_context }}</span>
            <span class="wb-ms-type wb-tag">{{ ms.milestone_type }}</span>
          </div>
          <div class="wb-ms-desc">{{ ms.description }}</div>
          <div v-if="ms.advice" class="wb-ms-advice">💡 {{ ms.advice }}</div>
        </div>
      </div>
    </div>

    <div v-if="props.baziData?.relationship && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">六亲与人际</h2>
      <div class="wb-rel-grid">
        <div v-if="props.baziData.relationship.noble_people?.length" class="wb-rel-card">
          <div class="wb-rel-label">贵人</div>
          <div class="wb-chip-list">
            <span v-for="p in props.baziData.relationship.noble_people" :key="p" class="wb-chip good">{{ p }}</span>
          </div>
        </div>
        <div v-if="props.baziData.relationship.petty_people?.length" class="wb-rel-card">
          <div class="wb-rel-label">小人</div>
          <div class="wb-chip-list">
            <span v-for="p in props.baziData.relationship.petty_people" :key="p" class="wb-chip bad">{{ p }}</span>
          </div>
        </div>
        <div v-if="props.baziData.relationship.liu_qin && Object.keys(props.baziData.relationship.liu_qin).length" class="wb-rel-card wb-rel-full">
          <div class="wb-rel-label">六亲对应</div>
          <div class="wb-liuqin-grid">
            <div v-for="(val, key) in props.baziData.relationship.liu_qin" :key="String(key)" class="wb-liuqin-item">
              <span class="wb-liuqin-key">{{ key }}</span>
              <span class="wb-liuqin-val">{{ val }}</span>
            </div>
          </div>
        </div>
        <div v-if="props.baziData.relationship.social_strategy" class="wb-rel-card wb-rel-full">
          <div class="wb-rel-label">社交策略</div>
          <p class="wb-rel-text">{{ props.baziData.relationship.social_strategy }}</p>
        </div>
      </div>
    </div>

    <div v-if="props.baziData?.fengshui && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">风水建议</h2>
      <div class="wb-fs-grid">
        <div v-if="props.baziData.fengshui.auspicious_directions?.length" class="wb-fs-item">
          <span class="wb-fs-label">吉方位</span>
          <div class="wb-chip-list"><span v-for="d in props.baziData.fengshui.auspicious_directions" :key="d" class="wb-chip good">{{ d }}</span></div>
        </div>
        <div v-if="props.baziData.fengshui.decor?.length" class="wb-fs-item">
          <span class="wb-fs-label">装饰建议</span>
          <div class="wb-chip-list"><span v-for="d in props.baziData.fengshui.decor" :key="d" class="wb-chip">{{ d }}</span></div>
        </div>
        <div v-if="props.baziData.fengshui.plants?.length" class="wb-fs-item">
          <span class="wb-fs-label">植物推荐</span>
          <div class="wb-chip-list"><span v-for="p in props.baziData.fengshui.plants" :key="p" class="wb-chip good">{{ p }}</span></div>
        </div>
        <div v-if="props.baziData.fengshui.taboo?.length" class="wb-fs-item">
          <span class="wb-fs-label">忌讳</span>
          <div class="wb-chip-list"><span v-for="t in props.baziData.fengshui.taboo" :key="t" class="wb-chip bad">{{ t }}</span></div>
        </div>
      </div>
    </div>

    <div v-if="props.baziData?.lifestyle && !props.simpleView" class="wb-section">
      <h2 class="wb-sec-title">生活建议</h2>
      <div class="wb-ls-grid">
        <div v-if="props.baziData.lifestyle.exercise?.length" class="wb-ls-item">
          <span class="wb-ls-label">运动方式</span>
          <div class="wb-chip-list"><span v-for="e in props.baziData.lifestyle.exercise" :key="e" class="wb-chip">{{ e }}</span></div>
        </div>
        <div v-if="props.baziData.lifestyle.diet?.length" class="wb-ls-item">
          <span class="wb-ls-label">饮食建议</span>
          <div class="wb-chip-list"><span v-for="d in props.baziData.lifestyle.diet" :key="d" class="wb-chip">{{ d }}</span></div>
        </div>
        <div v-if="props.baziData.lifestyle.best_times" class="wb-ls-item">
          <span class="wb-ls-label">最佳时段</span>
          <span class="wb-ls-val">{{ props.baziData.lifestyle.best_times }}</span>
        </div>
        <div v-if="props.baziData.lifestyle.travel_direction" class="wb-ls-item">
          <span class="wb-ls-label">出行吉方</span>
          <span class="wb-ls-val">{{ props.baziData.lifestyle.travel_direction }}</span>
        </div>
        <div v-if="props.baziData.lifestyle.sleep_advice" class="wb-ls-item wb-ls-full">
          <span class="wb-ls-label">休息建议</span>
          <span class="wb-ls-val">{{ props.baziData.lifestyle.sleep_advice }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wb-bazi-insights {
  display: contents;
}

.wb-section {
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.88));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: var(--shadow-xs);
}

.wb-sec-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 800;
  margin: 0 0 14px;
  color: var(--text-1);
}

.wb-sec-note { font-size: 11px; color: var(--text-3); font-weight: 400; }

.wb-chip-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.wb-chip {
  display: inline-flex;
  align-items: center;
  height: 24px;
  border-radius: 999px;
  padding: 0 10px;
  font-size: 12px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  font-family: var(--font-cn);
}

.wb-chip.good { color: #166534; background: #ecfdf5; border-color: #bbf7d0; }
.wb-chip.bad { color: #991b1b; background: #fef2f2; border-color: #fecaca; }

.wb-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 99px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-3);
}

.wb-interpret-body {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 20px;
  font-size: 13px;
  line-height: 1.85;
  color: var(--text-2);
  font-family: var(--font-cn);
  white-space: pre-line;
}

.wb-quadrant-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.wb-quad-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.wb-quad-head { display: flex; align-items: center; gap: 8px; }
.wb-quad-icon { font-size: 18px; }
.wb-quad-label { font-size: 14px; font-weight: 600; color: var(--text); flex: 1; }
.wb-quad-score { font-size: 22px; font-weight: 700; font-family: var(--font-mono); }
.wb-quad-tier { font-size: 12px; color: var(--text-2); }
.wb-quad-range { font-size: 11px; color: var(--text-3); }
.wb-quad-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }

.wb-personality-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
}

.wb-personality-core {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.7;
  font-family: var(--font-cn);
  margin: 0;
}

.wb-personality-advice {
  font-size: 12px;
  color: var(--text-3);
  margin: 8px 0 0;
  font-family: var(--font-cn);
  line-height: 1.6;
}

.wb-lyd-list { display: flex; flex-direction: column; gap: 12px; }
.wb-lyd-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.wb-lyd-card.current {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 25%, transparent);
}
.wb-lyd-card.expanded { box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }
.wb-lyd-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.wb-lyd-toggle {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0;
  text-align: left;
  cursor: pointer;
}
.wb-lyd-head-right { display: flex; align-items: center; gap: 10px; }
.wb-lyd-year { font-size: 15px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.wb-lyd-meta {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11px;
  color: var(--text-3);
  font-family: var(--font-cn);
}
.wb-lyd-score {
  min-width: 46px;
  height: 46px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 15px;
  font-weight: 700;
  border: 1px solid var(--border);
}
.wb-lyd-score.good { background: #dcfce7; color: #15803d; }
.wb-lyd-score.mid  { background: #fef3c7; color: #b45309; }
.wb-lyd-score.bad  { background: #fee2e2; color: #b91c1c; }
.wb-lyd-arrow { font-size: 18px; line-height: 1; color: var(--text-3); transition: transform .18s ease; }
.wb-lyd-arrow.expanded { transform: rotate(180deg); }
.wb-lyd-domains {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.wb-lyd-domain {
  background: var(--surface-2);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.wb-lyd-domain-key { font-size: 11px; color: var(--text-3); font-weight: 500; }
.wb-lyd-domain-val { font-size: 13px; color: var(--text); font-family: var(--font-cn); }
.wb-lyd-text { font-size: 13px; line-height: 1.7; color: var(--text-2); font-family: var(--font-cn); }
.wb-lyd-extra,
.wb-lyd-foot { display: flex; flex-direction: column; gap: 8px; }
.wb-lyd-block { display: flex; flex-direction: column; gap: 6px; }
.wb-lyd-label { font-size: 11px; color: var(--text-3); font-weight: 500; }
.wb-lyd-action {
  font-size: 12px;
  color: #d97706;
  font-family: var(--font-cn);
  background: color-mix(in srgb, #f59e0b 10%, white);
  border-radius: 8px;
  padding: 8px 10px;
}

.wb-fortune-wrap { display: flex; flex-direction: column; gap: 12px; }
.wb-fortune-text {
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-2);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  font-family: var(--font-cn);
}
.wb-domains { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; }
.wb-domain-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.wb-domain-key { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.wb-domain-val { font-size: 12px; color: var(--text); font-family: var(--font-cn); }

.wb-advice-list { padding-left: 18px; margin: 0; }
.wb-advice-item {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.8;
  padding: 4px 0;
  font-family: var(--font-cn);
  border-bottom: 1px solid var(--border);
}
.wb-advice-item:last-child { border-bottom: none; }

.wb-quote-block {
  background: var(--surface);
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
  padding: 14px 18px;
  border-top: 1px solid var(--border);
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.wb-quote-text { font-size: 13px; color: var(--text-2); line-height: 1.85; font-family: var(--font-cn); }
.wb-quote-note { font-size: 12px; color: var(--text-3); margin-top: 8px; font-style: italic; }

.wb-lifearc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.wb-larc-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 10px 14px;
  text-align: center;
}
.wb-larc-tier { background: var(--accent-lt); border-color: var(--accent); }
.wb-larc-label { font-size: 11px; color: var(--text-3); margin-bottom: 4px; }
.wb-larc-val { font-size: 14px; font-weight: 600; color: var(--text); font-family: var(--font-cn); }
.wb-larc-periods { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.wb-larc-period { display: flex; align-items: flex-start; gap: 10px; }
.wb-lp-label { font-size: 11px; font-weight: 600; min-width: 40px; padding-top: 3px; }
.wb-larc-period.good .wb-lp-label { color: #16a34a; }
.wb-larc-period.bad .wb-lp-label { color: #dc2626; }
.wb-larc-motto {
  font-size: 13px;
  color: var(--text-2);
  font-style: italic;
  font-family: var(--font-cn);
  text-align: center;
  padding: 8px 0 2px;
}

.wb-lucky-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.wb-lucky-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.wb-lucky-label { font-size: 11px; color: var(--text-3); }
.wb-lucky-val { font-size: 14px; font-weight: 600; color: var(--text); font-family: var(--font-cn); }
.wb-lucky-colors { display: flex; flex-wrap: wrap; gap: 4px; }
.wb-color-chip {
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 500;
  background: var(--accent-lt);
  color: var(--accent);
  border: 1px solid var(--accent-glow);
}
.wb-color-chip.avoid { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }

.wb-milestone-list { display: flex; flex-direction: column; gap: 10px; }
.wb-ms-item {
  border-left: 3px solid var(--border);
  padding: 10px 14px;
  border-radius: 0 8px 8px 0;
  background: var(--surface);
  transition: border-color .12s;
}
.wb-ms-item.ms-risk { border-color: #dc2626; background: #fff5f5; }
.wb-ms-item.ms-warn { border-color: #d97706; background: #fffbeb; }
.wb-ms-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 5px; }
.wb-ms-age { font-weight: 700; font-size: 15px; color: var(--text); }
.wb-ms-year { color: var(--text-3); font-family: var(--font-mono); }
.wb-ms-gz { color: var(--text-2); font-family: var(--font-cn); }
.wb-ms-type { margin-left: auto; }
.wb-ms-desc { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.6; }
.wb-ms-advice { font-size: 12px; color: #d97706; margin-top: 5px; font-family: var(--font-cn); }

.wb-rel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.wb-rel-full { grid-column: 1 / -1; }
.wb-rel-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.wb-rel-label { font-size: 11px; color: var(--text-3); font-weight: 500; }
.wb-rel-text { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.65; margin: 0; }
.wb-liuqin-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.wb-liuqin-item {
  background: var(--surface-2);
  border-radius: 6px;
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.wb-liuqin-key { font-size: 10px; color: var(--text-3); }
.wb-liuqin-val { font-size: 13px; color: var(--text); font-family: var(--font-cn); font-weight: 500; }

.wb-fs-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.wb-fs-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.wb-fs-label { font-size: 11px; color: var(--text-3); font-weight: 500; }

.wb-ls-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.wb-ls-full { grid-column: 1 / -1; }
.wb-ls-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.wb-ls-label { font-size: 11px; color: var(--text-3); font-weight: 500; }
.wb-ls-val { font-size: 13px; color: var(--text); font-family: var(--font-cn); }

.wb-month-chip {
  appearance: none;
  border: none;
  cursor: pointer;
  transition: transform .12s, box-shadow .12s;
}
.wb-month-chip:hover { transform: translateY(-1px); }
.wb-month-chip.active {
  box-shadow: 0 0 0 2px rgba(99,102,241,.22);
  background: #ede9fe;
  color: #5b21b6;
}

@media (max-width: 900px) {
  .wb-lucky-grid,
  .wb-rel-grid,
  .wb-fs-grid,
  .wb-ls-grid,
  .wb-quadrant-grid,
  .wb-lyd-domains {
    grid-template-columns: 1fr;
  }

  .wb-lifearc-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .wb-liuqin-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .wb-lyd-head,
  .wb-ms-meta,
  .wb-larc-period {
    flex-direction: column;
    align-items: flex-start;
  }

  .wb-ms-type {
    margin-left: 0;
  }
}

@media (max-width: 560px) {
  .wb-lifearc-grid,
  .wb-liuqin-grid {
    grid-template-columns: 1fr;
  }

  .wb-sec-title {
    flex-wrap: wrap;
    gap: 6px;
  }
}
</style>
