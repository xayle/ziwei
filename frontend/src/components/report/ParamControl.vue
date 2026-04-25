<script setup lang="ts">
/**
 * ParamControl.vue — 章节内参数控制栏
 * 显示可调参数，有修改时显示黄色提示条+重新计算按钮
 */
import { computed } from 'vue'
import { useReportStore } from '@/stores/report'

const props = defineProps<{
  chapterKey: 'bazi' | 'ziwei' | 'name' | 'zeri' | 'fengshui'
}>()

const store = useReportStore()
const isDirty = computed(() => store.dirtyParams[props.chapterKey])
const isLoading = computed(() => store.loadingMap[props.chapterKey])

// 各章节参数代理
const baziParams    = computed(() => store.pendingParams.bazi)
const ziweiParams   = computed(() => store.pendingParams.ziwei)
const nameParams    = computed(() => store.pendingParams.name)
const zeriParams    = computed(() => store.pendingParams.zeri)
const fengshuiParams = computed(() => store.pendingParams.fengshui)

function updateBazi(patch: Partial<typeof baziParams.value>) {
  store.updatePendingParam('bazi', patch)
}
function updateZiwei(patch: Partial<typeof ziweiParams.value>) {
  store.updatePendingParam('ziwei', patch)
}
function updateName(patch: Partial<typeof nameParams.value>) {
  store.updatePendingParam('name', patch)
}
function updateZeri(patch: Partial<typeof zeriParams.value>) {
  store.updatePendingParam('zeri', patch)
}
function updateFengshui(patch: Partial<typeof fengshuiParams.value>) {
  store.updatePendingParam('fengshui', patch)
}

// 生成当月起的12个月选项 (YYYY-MM)
const monthOptions = computed(() => {
  const opts: { label: string; value: string }[] = []
  const now = new Date()
  for (let i = -1; i <= 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    opts.push({ value: `${y}-${m}`, label: `${y}年${m}月` })
  }
  return opts
})

const ZERI_PURPOSES = [
  { value: 'general',   label: '通用' },
  { value: 'wedding',   label: '结婚' },
  { value: 'moving',    label: '搬居' },
  { value: 'business',  label: '开业' },
  { value: 'travel',    label: '出行' },
  { value: 'signing',   label: '签约' },
]

async function onRecompute() {
  await store.applyParamsAndRecompute(props.chapterKey)
}
function onDiscard() {
  store.discardParams(props.chapterKey)
}
</script>

<template>
  <div class="param-control">
    <!-- 参数控件区 -->
    <div class="param-row">
      <!-- 八字参数 -->
      <template v-if="chapterKey === 'bazi'">
        <label class="param-label">模式</label>
        <div class="param-radio-group">
          <label class="radio-opt">
            <input
              type="radio" value="dual"
              :checked="baziParams.mode === 'dual'"
              @change="updateBazi({ mode: 'dual' })"
            /> 双历
          </label>
          <label class="radio-opt">
            <input
              type="radio" value="single"
              :checked="baziParams.mode === 'single'"
              @change="updateBazi({ mode: 'single' })"
            /> 单历
          </label>
        </div>

        <label class="param-label">真太阳时</label>
        <input
          type="checkbox"
          class="param-checkbox"
          :checked="baziParams.solar_time_enabled"
          @change="updateBazi({ solar_time_enabled: ($event.target as HTMLInputElement).checked })"
        />

        <label class="param-label">流年范围</label>
        <div class="param-range">
          <input
            type="number"
            class="param-input-num"
            :value="baziParams.liunian_range[0]"
            @change="updateBazi({ liunian_range: [Number(($event.target as HTMLInputElement).value), baziParams.liunian_range[1]] })"
          />
          <span class="range-sep">—</span>
          <input
            type="number"
            class="param-input-num"
            :value="baziParams.liunian_range[1]"
            @change="updateBazi({ liunian_range: [baziParams.liunian_range[0], Number(($event.target as HTMLInputElement).value)] })"
          />
        </div>
      </template>

      <!-- 紫微参数 -->
      <template v-else-if="chapterKey === 'ziwei'">
        <label class="param-label">版本</label>
        <select
          class="param-select"
          :value="ziweiParams.template_version"
          @change="updateZiwei({ template_version: ($event.target as HTMLSelectElement).value as 'standard' | 'pro' | 'simple' })"
        >
          <option value="standard">标准版</option>
          <option value="pro">专业版（含博士星）</option>
          <option value="simple">简洁版（隐藏辅星）</option>
        </select>

        <label class="param-label">查看年份</label>
        <input
          type="number"
          class="param-input-num"
          :value="ziweiParams.liunian_year"
          @change="updateZiwei({ liunian_year: Number(($event.target as HTMLInputElement).value) })"
        />
      </template>

      <!-- 姓名参数 -->
      <template v-else-if="chapterKey === 'name'">
        <label class="param-label">姓名</label>
        <input
          type="text"
          class="param-input-text"
          :placeholder="store.caseData?.name ?? '（使用案例姓名）'"
          :value="nameParams.name_override ?? ''"
          @input="updateName({ name_override: ($event.target as HTMLInputElement).value || null })"
        />
        <span class="param-hint">留空则使用案例原名</span>

        <label class="param-label">出生年</label>
        <input
          type="number"
          class="param-input-num"
          :value="nameParams.birth_year_override ?? ''"
          :placeholder="store.caseData?.birth_dt_local?.slice(0,4) ?? ''"
          @change="updateName({ birth_year_override: Number(($event.target as HTMLInputElement).value) || null })"
        />
      </template>

      <!-- 择日参数 -->
      <template v-else-if="chapterKey === 'zeri'">
        <label class="param-label">用途</label>
        <select
          class="param-select"
          :value="zeriParams.purpose"
          @change="updateZeri({ purpose: ($event.target as HTMLSelectElement).value })"
        >
          <option v-for="p in ZERI_PURPOSES" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>

        <label class="param-label">月份</label>
        <select
          class="param-select"
          :value="zeriParams.month"
          @change="updateZeri({ month: ($event.target as HTMLSelectElement).value })"
        >
          <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </template>

      <!-- 风水参数 -->
      <template v-else-if="chapterKey === 'fengshui'">
        <label class="param-label">出生年</label>
        <input
          type="number"
          class="param-input-num"
          :value="fengshuiParams.birth_year_override ?? ''"
          :placeholder="store.caseData?.birth_dt_local?.slice(0,4) ?? ''"
          @change="updateFengshui({ birth_year_override: Number(($event.target as HTMLInputElement).value) || null })"
        />

        <label class="param-label">性别</label>
        <div class="param-radio-group">
          <label class="radio-opt">
            <input
              type="radio" value=""
              :checked="!fengshuiParams.gender_override"
              @change="updateFengshui({ gender_override: null })"
            /> 自动
          </label>
          <label class="radio-opt">
            <input
              type="radio" value="男"
              :checked="fengshuiParams.gender_override === '男'"
              @change="updateFengshui({ gender_override: '男' })"
            /> 男
          </label>
          <label class="radio-opt">
            <input
              type="radio" value="女"
              :checked="fengshuiParams.gender_override === '女'"
              @change="updateFengshui({ gender_override: '女' })"
            /> 女
          </label>
        </div>
      </template>

      <!-- 右侧：重新计算按钮（始终显示） -->
      <div class="param-actions">
        <button
          class="btn-recompute"
          :disabled="isLoading"
          @click="onRecompute"
        >
          <span v-if="isLoading" class="spin">⟳</span>
          <span v-else>▶ 重新计算</span>
        </button>
      </div>
    </div>

    <!-- 脏参数提示条 -->
    <transition name="dirty-bar">
      <div v-if="isDirty" class="dirty-bar">
        <span>⚠️ 参数已修改，点击"重新计算"生效</span>
        <button class="btn-discard" @click="onDiscard">取消</button>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.param-control {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: var(--sp-5);
  overflow: hidden;
}

.param-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
}

.param-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
  white-space: nowrap;
}

.param-radio-group {
  display: flex;
  gap: var(--sp-3);
}

.radio-opt {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-sm);
  cursor: pointer;
}

.param-checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
}

.param-range {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.range-sep { color: var(--text-3); font-size: var(--fs-xs); }

.param-input-num {
  width: 68px;
  padding: 4px 8px;
  font-size: var(--fs-sm);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-family: var(--font-mono);
}

.param-input-text {
  width: 100px;
  padding: 4px 8px;
  font-size: var(--fs-sm);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
}

.param-hint {
  font-size: 11px;
  color: var(--text-3);
  white-space: nowrap;
}

.param-select {
  padding: 4px 8px;
  font-size: var(--fs-sm);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
}

.param-actions {
  margin-left: auto;
}

.btn-recompute {
  padding: 6px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-fast);
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-recompute:hover:not(:disabled) { background: var(--accent-dark); }
.btn-recompute:disabled { opacity: 0.5; cursor: not-allowed; }

.spin {
  display: inline-block;
  animation: rotate 1s linear infinite;
}
@keyframes rotate { to { transform: rotate(360deg); } }

/* 脏参数提示条 */
.dirty-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-4);
  background: #fef3c7;
  border-top: 1px solid #fcd34d;
  font-size: var(--fs-sm);
  color: #92400e;
}

.btn-discard {
  padding: 3px 10px;
  font-size: var(--fs-xs);
  background: #fff;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: #92400e;
}

/* 动画 */
.dirty-bar-enter-active, .dirty-bar-leave-active {
  transition: all var(--dur-mid);
  overflow: hidden;
}
.dirty-bar-enter-from, .dirty-bar-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.dirty-bar-enter-to, .dirty-bar-leave-from {
  opacity: 1;
  max-height: 80px;
}
</style>
