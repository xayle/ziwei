<script setup lang="ts">
import { computed } from 'vue'
import type { ProfileData } from '@/stores/profile'
import type { ResponseProvenance } from '@/api/bazi'
import {
  formatDayDivideLabel,
  formatZiDayRuleLabel,
} from '@/utils/buildEngineTrustDisplay'

/** 紫微算法口径展示（ZiweiAlgo profile，与档案 / Case 同步） */
const props = defineProps<{
  profile: ProfileData
  provenance?: ResponseProvenance | null
}>()

const emit = defineEmits<{
  'update:brightnessMethod': [value: ProfileData['ziweiBrightnessMethod']]
  'update:youbiMethod': [value: ProfileData['ziweiYoubiMethod']]
}>()

const yearDivideLabel = computed(() =>
  props.profile.yearDivide === 'normal' ? '正月初一换年' : '立春换年',
)

const dayDivideLabel = computed(() => formatDayDivideLabel(props.profile.dayDivide))

const lateZishiLabel = computed(() =>
  props.profile.lateZishi ? '23:00–00:00 视为次日' : '仍算当日',
)

const ziDayRuleLabel = computed(() => formatZiDayRuleLabel(props.profile.ziDayRule))

/** 引擎默认 brightness_method / sihua 口径（与后端 ZiweiRequest 默认一致） */
const brightnessMethod = computed({
  get: () => props.profile.ziweiBrightnessMethod ?? 'standard',
  set: (v: ProfileData['ziweiBrightnessMethod']) => emit('update:brightnessMethod', v),
})
const youbiMethod = computed({
  get: () => props.profile.ziweiYoubiMethod ?? 'month',
  set: (v: ProfileData['ziweiYoubiMethod']) => emit('update:youbiMethod', v),
})

const METHOD_KEY_LABELS: Record<string, string> = {
  brightness_method: '亮度口径',
  youbi_method: '右弼口径',
  sihua_method: '生年四化',
  kuiyue_method: '天魁天钺',
  tianma_method: '天马',
  leap_month_method: '闰月',
  year_divide: '年界',
  day_divide: '换日',
}

const METHOD_VALUE_LABELS: Record<string, string> = {
  standard: '全书标准',
  zhongzhou: '中州',
  mod1: '变体 1',
  mod2: '变体 2',
  month: '按月',
  hour: '按时',
  mid: '月中分界',
  same: '视同本月',
  quanshu: '全书',
  year: '年支',
  lichun: '立春换年',
  normal: '正月初一换年',
  forward: '农历日+1安星',
  solar_next: '公历次日换日',
  current: '当日子时',
}

const ZiweiAlgoDefaults = {
  sihua_stem_indices: '按生年天干十干四化表',
  kuiyue_method: '全书标准',
  leap_month_method: '月中分界',
} as const

const provenanceMethods = computed(() => props.provenance?.methods ?? {})

function methodKeyLabel(key: string): string {
  return METHOD_KEY_LABELS[key] ?? key.replace(/_/g, ' ')
}

function methodValueLabel(val: unknown): string {
  const text = String(val)
  return METHOD_VALUE_LABELS[text] ?? text
}
</script>

<template>
  <div class="ziwei-algo-settings" data-testid="ziwei-algo-settings">
    <p class="ziwei-algo-settings__lead">
      紫微算法口径来自个人档案；亮度与右弼可在本页调整并写入档案。
    </p>

    <dl class="ziwei-algo-settings__grid">
      <div><dt>年界</dt><dd>{{ yearDivideLabel }}</dd></div>
      <div><dt>换日</dt><dd>{{ dayDivideLabel }}</dd></div>
      <div><dt>晚子时</dt><dd>{{ lateZishiLabel }}</dd></div>
      <div><dt>八字子时</dt><dd>{{ ziDayRuleLabel }}</dd></div>
      <div><dt>真太阳时</dt><dd>{{ profile.solarTime ? '开启（经度修正）' : '关闭' }}</dd></div>
      <div><dt>亮度口径</dt>
        <dd>
          <select v-model="brightnessMethod" data-testid="ziwei-brightness-method">
            <option value="standard">全书标准</option>
            <option value="zhongzhou">中州</option>
            <option value="mod1">变体 1</option>
            <option value="mod2">变体 2</option>
          </select>
        </dd>
      </div>
      <div><dt>右弼口径</dt>
        <dd>
          <select v-model="youbiMethod" data-testid="ziwei-youbi-method">
            <option value="month">按月（默认）</option>
            <option value="hour">按时（对照轨可选）</option>
          </select>
        </dd>
      </div>
      <div><dt>四化</dt><dd>{{ ZiweiAlgoDefaults.sihua_stem_indices }}</dd></div>
      <div><dt>闰月</dt><dd>{{ profile.isLeapMonth ? '闰月（视同本月）' : ZiweiAlgoDefaults.leap_month_method }}</dd></div>
    </dl>

    <div v-if="Object.keys(provenanceMethods).length" class="ziwei-algo-settings__prov">
      <h3>引擎回显口径</h3>
      <ul>
        <li v-for="(val, key) in provenanceMethods" :key="key">
          {{ methodKeyLabel(String(key)) }}：{{ methodValueLabel(val) }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.ziwei-algo-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ziwei-algo-settings__lead {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #57534e;
}

.ziwei-algo-settings__grid {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px 14px;
}

.ziwei-algo-settings__grid div {
  padding: 8px 10px;
  border-radius: 8px;
  background: #fffdf7;
  border: 1px solid #e7e5e4;
}

.ziwei-algo-settings__grid dt {
  margin: 0;
  font-size: 11px;
  color: #78716c;
}

.ziwei-algo-settings__grid dd {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: #292524;
}

.ziwei-algo-settings__prov h3 {
  margin: 0 0 6px;
  font-size: 12px;
  color: #44403c;
}

.ziwei-algo-settings__prov ul {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  line-height: 1.5;
  color: #57534e;
}
</style>
