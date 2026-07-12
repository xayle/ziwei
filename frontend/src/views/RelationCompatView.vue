<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VolumeHead from '@/components/fusheng/VolumeHead.vue'
import ResultStateCard from '@/components/new/ResultStateCard.vue'
import { useProfileStore } from '@/stores/profile'
import {
  RELATION_TYPE_OPTIONS,
  relationFull,
  type RelationFullResponse,
  type RelationType,
} from '@/api/relation'
import { buildRelationCompat, cardToneClass, dimensionPct } from '@/utils/buildRelationCompat'
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
const supervisorId = ref<'a' | 'b'>('a')
const showInference = ref(false)
const loading = ref(false)
const error = ref('')
const rawResult = ref<RelationFullResponse | null>(null)

const display = computed(() => (rawResult.value ? buildRelationCompat(rawResult.value) : null))

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

  try {
    rawResult.value = await relationFull({
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
        tz: 'Asia/Shanghai',
        longitude: 116.41,
        gender: partnerGender.value,
        label: partnerLabel.value.trim() || '对方',
      },
      options: { include_bazi: true, include_ziwei: true, liunian_year: new Date().getFullYear() },
    })
  } catch {
    error.value = '关系合盘分析失败，请检查输入后重试。'
  } finally {
    loading.value = false
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
            <tr><th>维度</th><th>得分</th><th>说明</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in display.dimensions" :key="d.id">
              <td>{{ d.label }}</td>
              <td>{{ d.score }}/{{ d.max_score }} ({{ dimensionPct(d) }}%)</td>
              <td>{{ d.description }}</td>
            </tr>
          </tbody>
        </table>
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
