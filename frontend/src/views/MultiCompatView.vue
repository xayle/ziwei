<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ziweiMultiCompat } from '@/api/ziwei'
import type { MultiCompatResponse, ZiweiRequest } from '@/api/ziwei'

type PersonLabel = '甲方' | '乙方' | '丙方' | '丁方'

const PERSON_LABELS: PersonLabel[] = ['甲方', '乙方', '丙方', '丁方']
const route = useRoute()
const router = useRouter()

function readNumber(value: unknown, fallback: number) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function createPerson(seed?: Partial<ZiweiRequest>): ZiweiRequest {
  return {
    year: seed?.year ?? 1995,
    month: seed?.month ?? 1,
    day: seed?.day ?? 1,
    hour: seed?.hour ?? 12,
    minute: seed?.minute ?? 0,
    gender: seed?.gender ?? '男',
    longitude: seed?.longitude,
  }
}

function readBasePersonFromQuery(): ZiweiRequest | null {
  if (!route.query.base_year) return null
  return createPerson({
    year: readNumber(route.query.base_year, 1995),
    month: readNumber(route.query.base_month, 1),
    day: readNumber(route.query.base_day, 1),
    hour: readNumber(route.query.base_hour, 12),
    minute: readNumber(route.query.base_minute, 0),
    gender: route.query.base_gender === '女' ? '女' : '男',
    longitude: route.query.base_longitude ? readNumber(route.query.base_longitude, 116.41) : undefined,
  })
}

const sourcePerson = readBasePersonFromQuery()
const persons = ref<ZiweiRequest[]>([
  sourcePerson ?? createPerson({ year: 1990, month: 6, day: 15, hour: 8, minute: 0, gender: '女', longitude: 116.41 }),
  createPerson({ year: 1992, month: 3, day: 22, hour: 10, minute: 30, gender: '男', longitude: 116.41 }),
])

const loading = ref(false)
const error = ref('')
const result = ref<MultiCompatResponse | null>(null)

const sourceHint = computed(() => route.query.from === 'ziwei' ? '已从紫微当前命盘带入甲方资料。' : '可直接录入 2-4 位成员的资料后生成关系矩阵。')

const bestPair = computed(() => {
  if (!result.value?.pairs?.length) return null
  return [...result.value.pairs].sort((a, b) => b.total_score - a.total_score)[0] ?? null
})

const scoreLegend = [
  { label: '85+ 高契合', className: 'is-excellent', hint: '适合长期深度协作或亲密搭档' },
  { label: '70-84 良好', className: 'is-good', hint: '整体磨合顺畅，偶有分歧可协调' },
  { label: '55-69 中等', className: 'is-fair', hint: '可合作，但需要明确分工和边界' },
  { label: '55 以下 观察', className: 'is-low', hint: '建议先小范围配合，再决定长期协作' },
] as const

const actionAdvice = computed(() => {
  if (!bestPair.value) return [] as string[]
  const pairLabel = `${getLabel(bestPair.value.person_a_idx)} × ${getLabel(bestPair.value.person_b_idx)}`
  if (bestPair.value.total_score >= 85) {
    return [
      `${pairLabel} 适合承担核心协作或亲密关系中的关键沟通角色。`,
      '建议优先安排需要高信任度、持续配合的事项。',
    ]
  }
  if (bestPair.value.total_score >= 70) {
    return [
      `${pairLabel} 适合稳定配合，建议保持固定节奏协作。`,
      '通过明确分工和反馈机制可进一步提升默契。',
    ]
  }
  if (bestPair.value.total_score >= 55) {
    return [
      `${pairLabel} 可先从低风险、小范围合作开始。`,
      '建议在边界、节奏和责任上提前约定。',
    ]
  }
  return [
    `${pairLabel} 当前更适合低耦合配合，不建议强绑定。`,
    '若必须合作，建议增加复核和中间同步节点。',
  ]
})

function getLabel(index: number) {
  return PERSON_LABELS[index] ?? `成员${index + 1}`
}

function addPerson() {
  if (persons.value.length >= 4) return
  persons.value.push(createPerson())
}

function removePerson(index: number) {
  if (persons.value.length <= 2) return
  persons.value.splice(index, 1)
}

function getPairClass(level?: string) {
  if (level?.includes('高') || level?.includes('极')) return 'is-excellent'
  if (level?.includes('良')) return 'is-good'
  if (level?.includes('中')) return 'is-fair'
  return 'is-low'
}

function getMatrixCellClass(score: number, rowIndex: number, colIndex: number) {
  const classes = ['matrix-cell']
  if (rowIndex === colIndex) return [...classes, 'is-self']
  classes.push('is-score')
  if (score >= 85) classes.push('is-excellent')
  else if (score >= 70) classes.push('is-good')
  else if (score >= 55) classes.push('is-fair')
  else classes.push('is-low')

  if (bestPair.value) {
    const { person_a_idx, person_b_idx } = bestPair.value
    const isBest = (rowIndex === person_a_idx && colIndex === person_b_idx) || (rowIndex === person_b_idx && colIndex === person_a_idx)
    if (isBest) classes.push('is-best-pair')
  }
  return classes
}

function getCellHint(score: number, rowIndex: number, colIndex: number) {
  if (rowIndex === colIndex) return `${getLabel(rowIndex)} 与自己不参与配对评分`
  return `${getLabel(rowIndex)} × ${getLabel(colIndex)}：${score} 分`
}

async function runAnalysis() {
  if (persons.value.length < 2 || loading.value) return
  loading.value = true
  error.value = ''
  result.value = null
  const payload = persons.value.map((item) => ({
    ...item,
    longitude: item.longitude || undefined,
  }))
   try {
    result.value = await ziweiMultiCompat({ person_list: payload })
   } catch (e: unknown) {
     error.value = (e as Error).message ?? '多人合盘失败，请稍后重试'
   } finally {
     loading.value = false
   }
 }

function backToSynastry() {
  router.push('/compat/synastry')
}

function backToZiwei() {
  router.push('/ziwei')
}
</script>

<template>
  <main class="team-view">
    <section class="hero card">
      <div>
        <p class="hero-kicker">关系分析模块</p>
        <h1 class="hero-title">紫微多人合盘</h1>
        <p class="hero-desc">将 2-4 位成员放在同一矩阵中，快速识别最佳组合、总体和谐度与协作建议。</p>
      </div>
      <div class="hero-actions">
        <button class="btn-primary" @click="backToSynastry">返回合盘入口</button>
        <button class="btn-secondary" @click="backToZiwei">返回紫微模块</button>
      </div>
    </section>

    <section class="card tip-card">
      <div class="tip-title">当前来源</div>
      <div class="tip-desc">{{ sourceHint }}</div>
    </section>

    <section class="editor-grid">
      <article class="card form-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">成员资料</h2>
            <p class="section-desc">至少录入 2 人，最多支持 4 人。</p>
          </div>
          <div class="section-actions">
            <button class="btn-secondary" :disabled="persons.length >= 4" @click="addPerson">添加成员</button>
            <button class="btn-primary" :disabled="loading" @click="runAnalysis">{{ loading ? '计算中…' : '计算缘分矩阵' }}</button>
          </div>
        </div>

        <div class="person-list">
          <article v-for="(person, index) in persons" :key="index" class="person-card">
            <div class="person-top">
              <div>
                <div class="person-title">{{ getLabel(index) }}</div>
                <div class="person-note">{{ index === 0 && route.query.from === 'ziwei' ? '来自当前紫微命盘' : '可直接调整成员信息' }}</div>
              </div>
              <button class="delete-btn" :disabled="persons.length <= 2" @click="removePerson(index)">删除</button>
            </div>

            <div class="form-grid">
              <label>
                <span>年</span>
                <input v-model.number="person.year" type="number" min="1900" max="2100">
              </label>
              <label>
                <span>月</span>
                <input v-model.number="person.month" type="number" min="1" max="12">
              </label>
              <label>
                <span>日</span>
                <input v-model.number="person.day" type="number" min="1" max="31">
              </label>
              <label>
                <span>时</span>
                <input v-model.number="person.hour" type="number" min="0" max="23">
              </label>
              <label>
                <span>分</span>
                <input v-model.number="person.minute" type="number" min="0" max="59">
              </label>
              <label>
                <span>性别</span>
                <select v-model="person.gender">
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </label>
              <label class="is-wide">
                <span>经度（可选）</span>
                <input v-model.number="person.longitude" type="number" step="0.1" placeholder="116.41">
              </label>
            </div>
          </article>
        </div>
      </article>

      <aside class="result-side">
        <section v-if="error" class="card state-card error">{{ error }}</section>
        <section v-else-if="!result" class="card state-card empty">尚未生成缘分矩阵，补齐成员资料后点击上方按钮开始计算。</section>

        <template v-if="result">
          <section class="card score-card">
            <div class="score-value">{{ result.team_harmony_score }}</div>
            <div class="score-label">团队和谐指数</div>
            <div class="legend-list">
              <span v-for="item in scoreLegend" :key="item.label" class="legend-chip" :class="item.className" :title="item.hint">{{ item.label }}</span>
            </div>
          </section>

          <section v-if="bestPair" class="card banner-card">
            当前最佳组合：{{ getLabel(bestPair.person_a_idx) }} × {{ getLabel(bestPair.person_b_idx) }} · {{ bestPair.total_score }} 分 · {{ bestPair.level }}
          </section>

          <section v-if="actionAdvice.length" class="card advice-card">
            <h2 class="section-title">行动建议</h2>
            <ul>
              <li v-for="item in actionAdvice" :key="item">{{ item }}</li>
            </ul>
          </section>
        </template>
      </aside>
    </section>

    <section v-if="result" class="content-grid">
      <article class="card matrix-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">缘分矩阵</h2>
            <p class="section-desc">高亮格表示当前最佳组合。</p>
          </div>
        </div>
        <div class="matrix-wrap">
          <table class="matrix-table">
            <thead>
              <tr>
                <th></th>
                <th v-for="idx in result.person_count" :key="`head-${idx}`">{{ getLabel(idx - 1) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in result.matrix" :key="`row-${rowIndex}`">
                <th>{{ getLabel(rowIndex) }}</th>
                <td
                  v-for="(cell, colIndex) in row"
                  :key="`cell-${rowIndex}-${colIndex}`"
                  :class="getMatrixCellClass(cell, rowIndex, colIndex)"
                  :title="getCellHint(cell, rowIndex, colIndex)"
                >
                  {{ rowIndex === colIndex ? '—' : cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card pairs-card">
        <div class="section-head">
          <div>
            <h2 class="section-title">配对明细</h2>
            <p class="section-desc">按接口返回展示所有组合。</p>
          </div>
        </div>
        <div class="pairs-list">
          <article v-for="pair in result.pairs" :key="`${pair.person_a_idx}-${pair.person_b_idx}`" class="pair-item" :class="getPairClass(pair.level)">
            <div class="pair-top">
              <strong>{{ getLabel(pair.person_a_idx) }} × {{ getLabel(pair.person_b_idx) }}</strong>
              <span>{{ pair.total_score }}/{{ pair.max_score }}</span>
            </div>
            <div class="pair-level">{{ pair.level }}</div>
          </article>
        </div>
      </article>
    </section>
  </main>
</template>

<style src="./MultiCompatView.css" scoped />
