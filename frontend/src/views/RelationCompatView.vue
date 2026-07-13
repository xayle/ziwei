<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VolumeHead from '@/components/fusheng/VolumeHead.vue'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useProfileStore } from '@/stores/profile'
import {
  RELATION_TYPE_OPTIONS,
  relationExplainBatch,
  relationExportPdf,
  relationExportPng,
  relationFull,
  saveBlobAsFile,
  type RelationFullRequest,
  type RelationFullResponse,
  type RelationType,
} from '@/api/relation'
import type { MultiCompatResponse } from '@/api/ziwei'
import { ziweiMultiCompat, ziweiMultiCompatExportPdf } from '@/api/ziwei'
import type { ExplainBatchResponse } from '@/api/explain'
import { buildRelationCompat, cardToneClass, dimensionPct } from '@/utils/buildRelationCompat'
import { birthDatetimeToZiweiRequest, buildZiweiRequest } from '@/utils/buildChartRequests'
import '@/assets/fusheng-page.css'

const router = useRouter()
const route = useRoute()
const profile = useProfileStore()

const relationType = ref<RelationType>(
  (route.query.type as RelationType) || 'couple',
)
const partnerBirthDt = ref('')
const partnerGender = ref('female')
const partnerLabel = ref('')
const partnerLon = ref<number | null>(null)
const partnerTz = ref('Asia/Shanghai')
const enableThirdPerson = ref(false)
const thirdBirthDt = ref('')
const thirdGender = ref('female')
const thirdLabel = ref('')
const thirdLon = ref<number | null>(null)
const supervisorId = ref<'a' | 'b'>('a')
const showInference = ref(false)
const showExplain = ref(false)
const loading = ref(false)
const exportingPdf = ref(false)
const exportingPng = ref(false)
const exportingMultiPdf = ref(false)
const error = ref('')
const rawResult = ref<RelationFullResponse | null>(null)
const lastRequest = ref<RelationFullRequest | null>(null)
const multiResult = ref<MultiCompatResponse | null>(null)
const explainBatch = ref<ExplainBatchResponse | null>(null)

const display = computed(() => (rawResult.value ? buildRelationCompat(rawResult.value) : null))

const multiLabels = computed(() => {
  if (!multiResult.value) return [] as string[]
  const n = multiResult.value.person_count || multiResult.value.matrix.length
  const defaults = [
    profile.activeProfile?.label || '我',
    partnerLabel.value.trim() || '对方',
    thirdLabel.value.trim() || '第三人',
  ]
  return defaults.slice(0, n)
})

const explainBlocks = computed(() =>
  explainBatch.value?.sections?.flatMap((s) => s.blocks ?? []) ?? [],
)

watch(
  () => route.query.type,
  (t) => {
    if (t && typeof t === 'string') relationType.value = t as RelationType
  },
)

function toIsoLocal(dtLocal: string): string {
  if (dtLocal.includes('T') && dtLocal.length >= 16) {
    return dtLocal.length === 16 ? `${dtLocal}:00` : dtLocal
  }
  return dtLocal
}

function partnerLongitude(): number {
  return Number.isFinite(partnerLon.value) ? partnerLon.value! : (profile.lon ?? 116.41)
}

function buildRelationRequest(): RelationFullRequest {
  const lonB = partnerLongitude()
  return {
    relation_type: relationType.value,
    supervisor_id: relationType.value === 'supervisor_subordinate' ? supervisorId.value : undefined,
    person_a: {
      birth_datetime: toIsoLocal(profile.birthDt),
      tz: profile.tz || 'Asia/Shanghai',
      longitude: profile.lon,
      gender: profile.gender || 'male',
      label: profile.activeProfile?.label || '我',
    },
    person_b: {
      birth_datetime: toIsoLocal(partnerBirthDt.value.trim()),
      tz: partnerTz.value || 'Asia/Shanghai',
      longitude: lonB,
      gender: partnerGender.value,
      label: partnerLabel.value.trim() || '对方',
    },
    options: { include_bazi: true, include_ziwei: true, liunian_year: new Date().getFullYear() },
  }
}

function buildMultiCompatRequest() {
  const profileData = profile.asProfileData()
  const lonB = partnerLongitude()
  const labels = [profile.activeProfile?.label || '我', partnerLabel.value.trim() || '对方']
  const personList = [
    buildZiweiRequest(profileData),
    birthDatetimeToZiweiRequest(partnerBirthDt.value.trim(), partnerGender.value, lonB, profileData),
  ]

  if (enableThirdPerson.value && thirdBirthDt.value.trim()) {
    const lonC = Number.isFinite(thirdLon.value) ? thirdLon.value! : lonB
    labels.push(thirdLabel.value.trim() || '第三人')
    personList.push(
      birthDatetimeToZiweiRequest(thirdBirthDt.value.trim(), thirdGender.value, lonC, profileData),
    )
  }

  if (personList.length < 2) return null

  return {
    person_list: personList,
    relation_type: relationType.value,
    labels,
    include_relation_dims: true,
    supervisor_id: relationType.value === 'supervisor_subordinate' ? supervisorId.value : undefined,
  }
}

function matrixCellLabel(i: number, j: number, score: number): string {
  if (i === j) return '—'
  const pair = multiResult.value?.pairs.find(
    (p) =>
      (p.person_a_idx === i && p.person_b_idx === j)
      || (p.person_a_idx === j && p.person_b_idx === i),
  )
  if (pair?.combined_score != null) {
    const parts = [`${score}%`]
    if (pair.bazi_score != null && pair.ziwei_score != null) {
      parts.push(`八字 ${pair.bazi_score} · 紫微 ${pair.ziwei_score}`)
    }
    if (pair.combined_score != null) parts.push(`综合 ${pair.combined_score.toFixed(1)}`)
    return parts.join(' · ')
  }
  return `${score}%`
}

function exportFilename(ext: 'pdf' | 'png'): string {
  const labelA = profile.activeProfile?.label || '我'
  const labelB = partnerLabel.value.trim() || '对方'
  return `合盘-${labelA}-${labelB}.${ext}`
}

async function runRelation() {
  if (!profile.birthDt?.trim()) {
    error.value = '请先补全当前档案出生时间。'
    return
  }
  if (!partnerBirthDt.value.trim()) {
    error.value = '请填写对方出生时间。'
    return
  }

  loading.value = true
  error.value = ''
  rawResult.value = null
  lastRequest.value = null
  multiResult.value = null
  explainBatch.value = null

  const body = buildRelationRequest()
  const multiBody = buildMultiCompatRequest()

  try {
    const [full, multi, explain] = await Promise.all([
      relationFull(body),
      multiBody && multiBody.person_list.length >= 3
        ? ziweiMultiCompat(multiBody)
        : Promise.resolve(null),
      relationExplainBatch({ ...body, sections: ['relation_reading'] }).catch(() => null),
    ])
    rawResult.value = full
    lastRequest.value = body
    multiResult.value = multi
    explainBatch.value = explain
  } catch {
    error.value = '关系合盘分析失败，请检查输入后重试。'
  } finally {
    loading.value = false
  }
}

async function downloadRelationPdf() {
  if (!lastRequest.value) return
  exportingPdf.value = true
  error.value = ''
  try {
    const blob = await relationExportPdf(lastRequest.value)
    saveBlobAsFile(blob, exportFilename('pdf'))
  } catch {
    error.value = 'PDF 导出失败，请稍后重试。'
  } finally {
    exportingPdf.value = false
  }
}

async function downloadRelationPng() {
  if (!lastRequest.value) return
  exportingPng.value = true
  error.value = ''
  try {
    const blob = await relationExportPng(lastRequest.value)
    saveBlobAsFile(blob, exportFilename('png'))
  } catch {
    error.value = '分享卡导出失败，请稍后重试。'
  } finally {
    exportingPng.value = false
  }
}

async function downloadMultiMatrixPdf() {
  const multiBody = buildMultiCompatRequest()
  if (!multiBody || multiBody.person_list.length < 2) return
  exportingMultiPdf.value = true
  error.value = ''
  try {
    const blob = await ziweiMultiCompatExportPdf(multiBody)
    saveBlobAsFile(blob, '合盘-多人矩阵.pdf')
  } catch {
    error.value = '多人矩阵 PDF 导出失败，请稍后重试。'
  } finally {
    exportingMultiPdf.value = false
  }
}
</script>

<template>
  <main class="fs-page relation-page">
    <VolumeHead
      :eyebrow="RELATION_TYPE_OPTIONS.find(o => o.value === relationType)?.label || '关系合盘'"
      title="双人合盘"
      :desc="display ? display.subtitle : '按关系类型切换评分维度与宫位对'"
    >
      <template #actions>
        <button class="fs-btn fs-btn--ghost" @click="router.push('/extensions')">返回工具箱</button>
        <button
          v-if="display && lastRequest"
          class="fs-btn fs-btn--ghost"
          :disabled="exportingPdf || exportingPng"
          data-testid="relation-export-pdf"
          @click="downloadRelationPdf"
        >
          {{ exportingPdf ? '导出中…' : '导出 PDF' }}
        </button>
        <button
          v-if="display && lastRequest"
          class="fs-btn fs-btn--ghost"
          :disabled="exportingPdf || exportingPng"
          data-testid="relation-export-png"
          @click="downloadRelationPng"
        >
          {{ exportingPng ? '导出中…' : '分享 PNG' }}
        </button>
        <button
          v-if="multiResult && multiResult.matrix.length >= 3"
          class="fs-btn fs-btn--ghost"
          :disabled="exportingMultiPdf"
          data-testid="relation-export-multi-pdf"
          @click="downloadMultiMatrixPdf"
        >
          {{ exportingMultiPdf ? '导出中…' : '矩阵 PDF' }}
        </button>
      </template>
    </VolumeHead>

    <section class="fs-card">
      <h2>关系类型</h2>
      <div class="type-grid" data-testid="relation-type-grid">
        <button
          v-for="opt in RELATION_TYPE_OPTIONS"
          :key="opt.value"
          class="type-chip"
          :class="{ active: relationType === opt.value }"
          :data-testid="`relation-type-${opt.value}`"
          @click="relationType = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>

      <div v-if="relationType === 'supervisor_subordinate'" class="field-row">
        <label class="field">
          <span>上级是</span>
          <select v-model="supervisorId" data-testid="relation-supervisor">
            <option value="a">当前档案（我）</option>
            <option value="b">对方</option>
          </select>
        </label>
      </div>

      <h2>对方信息</h2>
      <div class="field-grid">
        <label class="field">
          <span>称呼</span>
          <input v-model="partnerLabel" type="text" placeholder="可选" data-testid="relation-partner-label" />
        </label>
        <label class="field">
          <span>出生时间</span>
          <input v-model="partnerBirthDt" type="datetime-local" data-testid="relation-partner-birth" />
        </label>
        <label class="field">
          <span>性别</span>
          <select v-model="partnerGender">
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </label>
        <label class="field">
          <span>经度</span>
          <input
            v-model.number="partnerLon"
            type="number"
            step="0.001"
            min="-180"
            max="180"
            :placeholder="String(profile.lon ?? 116.41)"
            data-testid="relation-partner-lon"
          />
        </label>
        <label class="field">
          <span>时区</span>
          <input
            v-model="partnerTz"
            type="text"
            placeholder="Asia/Shanghai"
            data-testid="relation-partner-tz"
          />
        </label>
      </div>

      <div class="third-toggle">
        <label class="checkbox-row">
          <input v-model="enableThirdPerson" type="checkbox" data-testid="relation-enable-third" />
          <span>加入第三人（多人缘分矩阵 · 3×3）</span>
        </label>
      </div>

      <div v-if="enableThirdPerson" class="field-grid third-grid">
        <label class="field">
          <span>第三人称呼</span>
          <input v-model="thirdLabel" type="text" placeholder="可选" data-testid="relation-third-label" />
        </label>
        <label class="field">
          <span>出生时间</span>
          <input v-model="thirdBirthDt" type="datetime-local" data-testid="relation-third-birth" />
        </label>
        <label class="field">
          <span>性别</span>
          <select v-model="thirdGender">
            <option value="female">女</option>
            <option value="male">男</option>
          </select>
        </label>
        <label class="field">
          <span>经度</span>
          <input
            v-model.number="thirdLon"
            type="number"
            step="0.001"
            min="-180"
            max="180"
            :placeholder="String(partnerLongitude())"
            data-testid="relation-third-lon"
          />
        </label>
      </div>
      <button
        class="fs-btn fs-btn--primary"
        :disabled="loading"
        data-testid="relation-run"
        @click="runRelation"
      >
        {{ loading ? '分析中…' : '开始合盘' }}
      </button>
    </section>

    <ResultStateCard v-if="error" title="合盘失败" :message="error" />

    <template v-if="display">
      <section class="fs-card score-hero" data-testid="relation-result">
        <div class="score-row">
          <span class="score-num">{{ display.combinedScore.toFixed(1) }}</span>
          <span class="score-grade">{{ display.grade }}</span>
        </div>
        <p class="score-summary">{{ display.summary }}</p>
      </section>

      <section v-if="display.summaryCards.length" class="fs-card">
        <h2>要点</h2>
        <div class="card-grid">
          <article
            v-for="card in display.summaryCards"
            :key="card.id"
            class="summary-card"
            :class="cardToneClass(card.tone)"
          >
            {{ card.text }}
          </article>
        </div>
      </section>

      <section class="fs-card">
        <h2>分维得分</h2>
        <table class="dim-table">
          <thead>
            <tr><th>维度</th><th>得分</th><th>引擎</th><th>说明</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in display.dimensions" :key="d.id">
              <td>{{ d.label }}</td>
              <td>{{ d.score }}/{{ d.max_score }} ({{ dimensionPct(d) }}%)</td>
              <td>{{ d.engine || '—' }}</td>
              <td>{{ d.description }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="multiResult && multiResult.matrix.length >= 2" class="fs-card" data-testid="relation-multi-matrix">
        <h2>多人缘分矩阵</h2>
        <p class="matrix-harmony">团队和谐度 {{ multiResult.team_harmony_score }}%</p>
        <table class="matrix-table">
          <thead>
            <tr>
              <th />
              <th v-for="(label, idx) in multiLabels" :key="`col-${idx}`">{{ label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in multiResult.matrix" :key="`row-${i}`">
              <th>{{ multiLabels[i] }}</th>
              <td v-for="(score, j) in row" :key="`cell-${i}-${j}`">
                {{ matrixCellLabel(i, j, score) }}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="explainBlocks.length" class="fs-card inference-section">
        <button class="fs-btn fs-btn--ghost" data-testid="relation-explain-toggle" @click="showExplain = !showExplain">
          {{ showExplain ? '收起' : '展开' }}关系解读（cite / inference）
        </button>
        <ul v-if="showExplain" class="action-list">
          <li v-for="(block, idx) in explainBlocks" :key="idx" class="explain-line">
            <span class="layer-tag">{{ block.layer }}</span>
            {{ block.text }}
          </li>
        </ul>
      </section>

      <section v-if="display.palaceCross.length" class="fs-card">
        <h2>宫位互涉</h2>
        <ul class="palace-list">
          <li v-for="p in display.palaceCross" :key="p.pair_id">
            <strong>{{ p.a_palace }} ↔ {{ p.b_palace }}</strong>
            <span v-if="p.relation_tag"> · {{ p.relation_tag }}</span>
            <p>{{ p.summary }}</p>
          </li>
        </ul>
      </section>

      <section v-if="display.timeline.length" class="fs-card">
        <h2>共运时间轴</h2>
        <ul class="timeline-list">
          <li v-for="node in display.timeline" :key="node.year">
            <span class="tl-label">{{ node.label }}</span>
            <span v-if="node.risk_level" class="tl-risk">风险{{ node.risk_level }}</span>
            <p>{{ node.summary }}</p>
          </li>
        </ul>
      </section>

      <section class="fs-card inference-section">
        <button class="fs-btn fs-btn--ghost" @click="showInference = !showInference">
          {{ showInference ? '收起' : '展开' }}相处建议（推断层）
        </button>
        <ul v-if="showInference" class="action-list">
          <li v-for="item in display.actionItems" :key="item.id">{{ item.text }}</li>
        </ul>
      </section>

      <section v-if="display.tensions.length" class="fs-card tension-box">
        <h2>模块张力</h2>
        <p v-for="t in display.tensions" :key="t.code" class="tension-line">{{ t.message }}</p>
      </section>

      <p v-if="rawResult?.disclaimer_block?.text" class="disclaimer">{{ rawResult.disclaimer_block.text }}</p>
    </template>
  </main>
</template>

<style scoped>
.relation-page { gap: 14px; }

.type-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.type-chip {
  border: 1px solid var(--border-1, #ddd);
  background: var(--surface-1, #fff);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
}

.type-chip.active {
  border-color: var(--accent, #8b4513);
  background: var(--accent-soft, #f5ebe0);
}

.field-grid, .field-row {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: 12px;
}

.field { display: grid; gap: 4px; font-size: 13px; }

.third-toggle { margin: 8px 0 12px; }

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  cursor: pointer;
}

.matrix-harmony {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--text-2);
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid var(--border-1, #eee);
  padding: 8px 6px;
  text-align: center;
  vertical-align: top;
}

.explain-line {
  font-size: 13px;
  line-height: 1.55;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-1, #eee);
}

.layer-tag {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  background: var(--inset-tint, #f5f0e6);
  color: var(--text-3);
}

.score-hero { text-align: center; }

.score-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12px;
}

.score-num {
  font-size: 42px;
  font-family: var(--font-cn);
  color: var(--accent, #8b4513);
}

.score-grade { font-size: 18px; }

.score-summary {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-2);
}

.card-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.summary-card {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.55;
  border-left: 3px solid var(--border-1);
}

.tone-support { border-left-color: #2e7d32; background: #f1f8f4; }
.tone-conflict { border-left-color: #c62828; background: #fff5f5; }
.tone-action { border-left-color: #1565c0; background: #f0f7ff; }
.tone-neutral { border-left-color: #757575; background: #fafafa; }

.dim-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dim-table th, .dim-table td {
  border-bottom: 1px solid var(--border-1, #eee);
  padding: 8px 6px;
  text-align: left;
  vertical-align: top;
}

.palace-list, .timeline-list, .action-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.palace-list li, .timeline-list li {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-1, #eee);
  font-size: 13px;
}

.tl-label { font-weight: 600; margin-right: 8px; }
.tl-risk { font-size: 12px; color: #c62828; }

.tension-line { color: #c62828; font-size: 13px; }

.disclaimer {
  font-size: 12px;
  color: var(--text-3);
  text-align: center;
  margin: 0;
}
</style>
