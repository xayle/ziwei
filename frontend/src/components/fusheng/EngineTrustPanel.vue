<script setup lang="ts">
import type {
  DualTrackRow,
  IztroDisplay,
  PalaceStructuredRow,
  PillarDetailRow,
  ProvenanceRow,
} from '@/utils/buildEngineTrustDisplay'

defineProps<{
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
}>()
</script>

<template>
  <div class="engine-trust" :class="{ 'engine-trust--compact': compact }">
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
      <p>{{ missingFields.join('、') }}</p>
    </div>

    <section v-if="validationLines?.length" class="engine-trust__section">
      <h3>校验与置信度</h3>
      <ul class="engine-trust__list">
        <li v-for="(line, idx) in validationLines" :key="idx">{{ line }}</li>
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
  </div>
</template>

<style scoped>
.engine-trust {
  display: grid;
  gap: 14px;
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
  background: var(--surface-2);
  font-weight: 500;
}
</style>
