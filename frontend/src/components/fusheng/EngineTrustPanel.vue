<script setup lang="ts">
import { computed } from 'vue'
import type {
  DualTrackRow,
  IztroDisplay,
  PalaceStructuredRow,
  PillarDetailRow,
  ProvenanceRow,
} from '@/utils/buildEngineTrustDisplay'
import { formatMissingFieldLine, formatTrustValidationLine } from '@/utils/buildEngineTrustDisplay'

const props = defineProps<{
  missingFields?: string[]
  provenanceRows?: ProvenanceRow[]
  dualTracks?: DualTrackRow[]
  validationLines?: string[]
  iztro?: IztroDisplay | null
  liuri?: {
    date?: string
    day: string
    hour: string
    flow: string
    links: string[]
    score?: string
  } | null
  pillarDetails?: PillarDetailRow[]
  relations?: string[]
  strengthFactorLines?: string[]
  baziStructural?: string[]
  ziweiStructural?: string[]
  palaceStructured?: PalaceStructuredRow[]
  crossValidationItems?: Array<{ label: string; status: string; detail: string }>
  compact?: boolean
  layout?: 'default' | 'register'
}>()

const isRegister = computed(() => props.layout === 'register')

const crossWarnItems = computed(() =>
  props.crossValidationItems?.filter((item) => item.status === 'warn' || item.status === 'fail') ?? [],
)

const badgeForTone = (tone: 'ok' | 'drift' | 'missing') => {
  if (tone === 'missing') return { label: '缺失', class: 'trust-badge--missing' }
  if (tone === 'drift') return { label: '校勘', class: 'trust-badge--drift' }
  return { label: '核对', class: '' }
}

const iconForTone = (tone: 'ok' | 'drift' | 'missing') => {
  if (tone === 'missing') return '!'
  if (tone === 'drift') return '△'
  return '✓'
}

const detailSections = computed(() => {
  const sections: Array<{ id: string; title: string; open: boolean }> = []
  if (props.provenanceRows?.length) {
    sections.push({ id: 'provenance', title: `可信度分层（${props.provenanceRows.length}）`, open: !props.compact })
  }
  if (props.dualTracks?.length) sections.push({ id: 'dual', title: '双轨口径', open: false })
  if (props.pillarDetails?.length) sections.push({ id: 'pillar', title: '四柱细目', open: false })
  if (props.strengthFactorLines?.length) sections.push({ id: 'strength', title: '旺衰因子', open: false })
  if (props.relations?.length) sections.push({ id: 'relations', title: '刑冲合害', open: false })
  if (props.baziStructural?.length) sections.push({ id: 'structural', title: '结构摘要', open: false })
  if (props.liuri) sections.push({ id: 'liuri', title: '流日 / 流时', open: false })
  if (props.iztro) sections.push({ id: 'iztro', title: 'iztro 交叉核验', open: false })
  return sections
})

function crossTone(status: string): 'ok' | 'drift' | 'missing' {
  if (status === 'fail') return 'missing'
  if (status === 'warn') return 'drift'
  return 'ok'
}
</script>

<template>
  <div
    class="engine-trust"
    :class="{
      'engine-trust--compact': compact,
      'engine-trust--register': isRegister,
      'trust-footnote': isRegister,
    }"
  >
    <template v-if="isRegister">
      <p class="trust-footnote__title">引擎校验 · 跋前脚注</p>

      <div
        v-for="(item, idx) in crossWarnItems"
        :key="`cross-${idx}`"
        class="trust-row"
        :class="`trust-row--${crossTone(item.status)}`"
        data-testid="cross-validation-hint"
      >
        <span class="trust-icon">{{ iconForTone(crossTone(item.status)) }}</span>
        <span class="trust-badge" :class="badgeForTone(crossTone(item.status)).class">互证</span>
        <span>{{ item.label }}：{{ item.detail }}</span>
      </div>

      <div v-if="missingFields?.length" data-testid="missing-fields">
        <div
          v-for="field in missingFields"
          :key="`missing-${field}`"
          class="trust-row trust-row--missing"
        >
          <span class="trust-icon">!</span>
          <span class="trust-badge trust-badge--missing">缺失</span>
          <span class="trust-row__body">
            {{ formatMissingFieldLine(field).main }}
            <span v-if="formatMissingFieldLine(field).note" class="trust-row__note">{{ formatMissingFieldLine(field).note }}</span>
          </span>
        </div>
      </div>

      <div
        v-for="(line, idx) in validationLines"
        :key="`validation-${idx}`"
        class="trust-row"
        :class="`trust-row--${formatTrustValidationLine(line).tone}`"
      >
        <span class="trust-icon">{{ iconForTone(formatTrustValidationLine(line).tone) }}</span>
        <span class="trust-badge" :class="badgeForTone(formatTrustValidationLine(line).tone).class">
          {{ badgeForTone(formatTrustValidationLine(line).tone).label }}
        </span>
        <span class="trust-row__body">
          {{ formatTrustValidationLine(line).main }}
          <span v-if="formatTrustValidationLine(line).note" class="trust-row__note">{{ formatTrustValidationLine(line).note }}</span>
        </span>
      </div>

      <p
        v-if="!missingFields?.length && !validationLines?.length && !crossWarnItems.length && !detailSections.length"
        class="trust-row trust-row--ok"
      >
        <span class="trust-icon">✓</span>
        <span class="trust-badge">核对</span>
        <span>引擎字段完整，暂无校勘项。</span>
      </p>

      <details
        v-if="provenanceRows?.length"
        class="trust-register"
        data-testid="provenance-section"
        :open="!compact"
      >
        <summary class="trust-register__summary">可信度分层</summary>
        <div class="trust-register__body">
          <table class="trust-register__table">
            <thead>
              <tr><th>域</th><th>层级</th><th>置信度</th><th>备注</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in provenanceRows" :key="idx">
                <td>{{ row.domain }}</td>
                <td><span class="layer-tag" :data-layer="row.layer">{{ row.layer }}</span></td>
                <td>{{ row.confidence != null ? `${Math.round(row.confidence * 100)}%` : '—' }}</td>
                <td>{{ row.note || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>

      <details v-if="dualTracks?.length && !compact" class="trust-register" data-testid="report-bazi-dual-track">
        <summary class="trust-register__summary">双轨口径</summary>
        <div class="trust-register__body">
          <table class="trust-register__table">
            <thead><tr><th>用例</th><th>古籍/录入</th><th>引擎</th><th>说明</th></tr></thead>
            <tbody>
              <tr v-for="row in dualTracks" :key="row.id">
                <td>{{ row.id }}</td>
                <td>{{ row.recorded }}</td>
                <td>{{ row.engine }}</td>
                <td>{{ row.note || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>

      <details v-if="pillarDetails?.length && !compact" class="trust-register">
        <summary class="trust-register__summary">四柱细目</summary>
        <div class="trust-register__body">
          <table class="trust-register__table">
            <thead><tr><th>柱</th><th>空亡</th><th>神煞</th><th>藏干</th></tr></thead>
            <tbody>
              <tr v-for="row in pillarDetails" :key="row.pillar">
                <td>{{ row.pillar }}</td>
                <td>{{ row.kongwang }}</td>
                <td>{{ row.shensha }}</td>
                <td>{{ row.hidden }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>

      <details v-if="strengthFactorLines?.length && !compact" class="trust-register">
        <summary class="trust-register__summary">旺衰因子</summary>
        <div class="trust-register__body">
          <ul class="engine-trust__list">
            <li v-for="(line, idx) in strengthFactorLines" :key="idx">{{ line }}</li>
          </ul>
        </div>
      </details>

      <details v-if="relations?.length && !compact" class="trust-register">
        <summary class="trust-register__summary">刑冲合害 / 天干冲</summary>
        <div class="trust-register__body">
          <ul class="engine-trust__list">
            <li v-for="(line, idx) in relations" :key="idx">{{ line }}</li>
          </ul>
        </div>
      </details>

      <details v-if="baziStructural?.length && !compact" class="trust-register">
        <summary class="trust-register__summary">八字结构摘要</summary>
        <div class="trust-register__body">
          <ul class="engine-trust__list">
            <li v-for="(line, idx) in baziStructural" :key="idx">{{ line }}</li>
          </ul>
        </div>
      </details>

      <details v-if="liuri && !compact" class="trust-register">
        <summary class="trust-register__summary">流日 / 流时</summary>
        <div class="trust-register__body">
          <p class="engine-trust__lead">{{ liuri.date }} · 日柱 {{ liuri.day }} · 时柱 {{ liuri.hour }}</p>
          <p>{{ liuri.flow }}</p>
          <p v-if="liuri.links.length" class="hint">{{ liuri.links.join(' · ') }}</p>
          <p v-if="liuri.score" class="hint">联动评分 {{ liuri.score }}</p>
        </div>
      </details>

      <details v-if="iztro && !compact" class="trust-register" data-testid="iztro-crosscheck">
        <summary class="trust-register__summary">iztro 交叉核验</summary>
        <div class="trust-register__body">
          <p class="engine-trust__lead">状态 {{ iztro.status }} · 主星 {{ iztro.mainMatch }}<span v-if="iztro.lifePalace"> · {{ iztro.lifePalace }}</span></p>
          <p>{{ iztro.message }}</p>
        </div>
      </details>
    </template>

    <template v-else>
      <div
        v-if="crossValidationItems?.some((item) => item.status === 'warn' || item.status === 'fail')"
        class="engine-trust__alert engine-trust__alert--cross"
        data-testid="cross-validation-hint"
      >
        <strong>八字·紫微互证</strong>
        <ul class="engine-trust__list">
          <li v-for="(item, idx) in crossValidationItems" :key="idx" :data-status="item.status">
            {{ item.label }}：{{ item.detail }}
          </li>
        </ul>
      </div>

      <div v-if="missingFields?.length" class="engine-trust__alert" data-testid="missing-fields">
        <strong>缺失字段</strong>
        <ul class="engine-trust__list">
          <li v-for="field in missingFields" :key="field">
            {{ formatMissingFieldLine(field).main }}
          </li>
        </ul>
      </div>

      <section v-if="validationLines?.length" class="engine-trust__section">
        <h3>校验与置信度</h3>
        <ul class="engine-trust__list">
          <li v-for="(line, idx) in validationLines" :key="idx">
            {{ formatTrustValidationLine(line).main }}
          </li>
        </ul>
      </section>

      <section v-if="iztro" class="engine-trust__section" data-testid="iztro-crosscheck">
        <h3>iztro 交叉核验</h3>
        <p class="engine-trust__lead">状态 {{ iztro.status }} · 主星 {{ iztro.mainMatch }}<span v-if="iztro.lifePalace"> · {{ iztro.lifePalace }}</span></p>
        <p>{{ iztro.message }}</p>
        <table v-if="iztro.showDualTrackTable" class="engine-trust__table">
          <thead>
            <tr><th>轨道</th><th>命宫</th><th>主星</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>引擎主盘</td>
              <td>{{ iztro.engineLifePalaceGz || '—' }}</td>
              <td>{{ iztro.mainMatch }}</td>
            </tr>
            <tr v-if="iztro.dualTrack">
              <td>{{ iztro.dualTrack.label }}</td>
              <td>{{ iztro.dualTrack.lifePalaceGz }}</td>
              <td>{{ iztro.dualTrack.mainMatch }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="dualTracks?.length" class="engine-trust__section" data-testid="report-bazi-dual-track">
        <h3>双轨口径（recorded vs engine）</h3>
        <table class="engine-trust__table">
          <thead><tr><th>用例</th><th>古籍/录入</th><th>引擎</th><th>说明</th></tr></thead>
          <tbody>
            <tr v-for="row in dualTracks" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.recorded }}</td>
              <td>{{ row.engine }}</td>
              <td>{{ row.note || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="provenanceRows?.length" class="engine-trust__section" data-testid="provenance-section">
        <h3>可信度分层（provenance）</h3>
        <table class="engine-trust__table">
          <thead><tr><th>域</th><th>层级</th><th>置信度</th><th>备注</th></tr></thead>
          <tbody>
            <tr v-for="(row, idx) in provenanceRows" :key="idx">
              <td>{{ row.domain }}</td>
              <td><span class="layer-tag" :data-layer="row.layer">{{ row.layer }}</span></td>
              <td>{{ row.confidence != null ? `${Math.round(row.confidence * 100)}%` : '—' }}</td>
              <td>{{ row.note || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="liuri" class="engine-trust__section">
        <h3>流日 / 流时</h3>
        <p class="engine-trust__lead">{{ liuri.date }} · 日柱 {{ liuri.day }} · 时柱 {{ liuri.hour }}</p>
        <p>{{ liuri.flow }}</p>
        <p v-if="liuri.links.length" class="hint">{{ liuri.links.join(' · ') }}</p>
        <p v-if="liuri.score" class="hint">联动评分 {{ liuri.score }}</p>
      </section>

      <section v-if="pillarDetails?.length" class="engine-trust__section">
        <h3>四柱细目（空亡 / 神煞 / 藏干）</h3>
        <table class="engine-trust__table">
          <thead><tr><th>柱</th><th>空亡</th><th>神煞</th><th>藏干</th></tr></thead>
          <tbody>
            <tr v-for="row in pillarDetails" :key="row.pillar">
              <td>{{ row.pillar }}</td>
              <td>{{ row.kongwang }}</td>
              <td>{{ row.shensha }}</td>
              <td>{{ row.hidden }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="strengthFactorLines?.length" class="engine-trust__section">
        <h3>旺衰因子（B-02）</h3>
        <ul class="engine-trust__list">
          <li v-for="(line, idx) in strengthFactorLines" :key="idx">{{ line }}</li>
        </ul>
      </section>

      <section v-if="relations?.length" class="engine-trust__section">
        <h3>刑冲合害 / 天干冲</h3>
        <ul class="engine-trust__list">
          <li v-for="(line, idx) in relations" :key="idx">{{ line }}</li>
        </ul>
      </section>

      <section v-if="baziStructural?.length" class="engine-trust__section">
        <h3>八字结构摘要</h3>
        <ul class="engine-trust__list">
          <li v-for="(line, idx) in baziStructural" :key="idx">{{ line }}</li>
        </ul>
      </section>

      <section v-if="ziweiStructural?.length" class="engine-trust__section">
        <h3>紫微结构摘要</h3>
        <ul class="engine-trust__list">
          <li v-for="(line, idx) in ziweiStructural" :key="idx">{{ line }}</li>
        </ul>
      </section>

      <section v-if="palaceStructured?.length && !compact" class="engine-trust__section">
        <h3>十二宫结构化解读</h3>
        <article v-for="row in palaceStructured" :key="row.name" class="engine-trust__palace">
          <h4>{{ row.name }} <span v-if="row.tags.length">{{ row.tags.join('、') }}</span></h4>
          <p><strong>结论</strong> — {{ row.conclusion }}</p>
          <p v-if="row.explanation">{{ row.explanation }}</p>
          <p v-if="row.suggestion" class="hint">建议：{{ row.suggestion }}</p>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.engine-trust {
  display: grid;
  gap: 14px;
}

.engine-trust--register {
  gap: 0;
}

.engine-trust__alert {
  padding: 8px 12px;
  border-radius: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-cinnabar);
  color: var(--brand-cinnabar);
  font-size: 12px;
}

.engine-trust__alert p {
  margin: 6px 0 0;
}

.engine-trust__section h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--brand-ink, #2b2118);
}

.engine-trust__section h4 {
  margin: 0 0 6px;
  font-size: 13px;
}

.engine-trust__section h4 span {
  font-weight: 400;
  color: var(--text-3, #8a7a6a);
  font-size: 12px;
}

.engine-trust__lead {
  margin: 0 0 6px;
  font-size: 13px;
}

.engine-trust__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.engine-trust__table th,
.engine-trust__table td {
  border: 1px solid var(--border-md, #e8dcc8);
  padding: 6px 8px;
  text-align: left;
}

.engine-trust__table th {
  background: var(--bg-muted, #faf8f5);
}

.engine-trust__list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}

.engine-trust__palace {
  padding: 10px 0;
  border-top: 1px dashed var(--border-md, #e8dcc8);
}

.engine-trust__palace:first-of-type {
  border-top: none;
  padding-top: 0;
}

.layer-tag[data-layer='典籍'] {
  color: var(--brand-gold-dark);
}

.layer-tag[data-layer='引擎'] {
  color: var(--brand-mist);
}

.layer-tag[data-layer='启发式'] {
  color: var(--brand-cinnabar);
}

.hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-3, #8a7a6a);
}

.engine-trust--compact .engine-trust__section h3 {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--text-2);
  text-transform: none;
}

.engine-trust--compact .engine-trust__table th {
  background: var(--inset-tint);
  font-weight: 500;
}
</style>
