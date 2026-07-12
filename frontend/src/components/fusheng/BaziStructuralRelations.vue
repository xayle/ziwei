<script setup lang="ts">
import type { PillarDetailRow } from '@/utils/buildEngineTrustDisplay'

const props = defineProps<{
  relations?: string[]
  pillarDetails?: PillarDetailRow[]
  missingFields?: string[]
}>()

const hasRelations = () => (props.relations?.length ?? 0) > 0
const hasPillarDetails = () => (props.pillarDetails?.length ?? 0) > 0
</script>

<template>
  <section class="bazi-structural" data-testid="bazi-structural-relations">
    <header class="bazi-structural__head">
      <h2>结构关系</h2>
      <p class="bazi-structural__lead">刑冲合害、天干冲、柱级神煞与空亡；无数据时显式标注「缺失」。</p>
    </header>

    <div v-if="missingFields?.length" class="bazi-structural__alert" data-testid="bazi-structural-missing">
      <strong>引擎未覆盖</strong>
      <p>{{ missingFields.join('、') }}</p>
    </div>

    <section class="bazi-structural__section">
      <h3>刑冲合害 / 天干冲</h3>
      <ul v-if="hasRelations()" class="bazi-structural__list">
        <li v-for="(line, idx) in relations" :key="idx">{{ line }}</li>
      </ul>
      <p v-else class="bazi-structural__empty">缺失</p>
    </section>

    <section class="bazi-structural__section">
      <h3>四柱细目（空亡 / 神煞 / 藏干）</h3>
      <table v-if="hasPillarDetails()" class="bazi-structural__table">
        <thead>
          <tr><th>柱</th><th>空亡</th><th>神煞</th><th>藏干</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in pillarDetails" :key="row.pillar">
            <td>{{ row.pillar }}</td>
            <td>{{ row.kongwang || '缺失' }}</td>
            <td>{{ row.shensha || '缺失' }}</td>
            <td>{{ row.hidden || '缺失' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="bazi-structural__empty">缺失</p>
    </section>
  </section>
</template>

<style scoped>
.bazi-structural {
  display: grid;
  gap: 14px;
}

.bazi-structural__head h2 {
  margin: 0;
  font-family: var(--font-cn);
  color: var(--brand-ink);
}

.bazi-structural__lead {
  margin: 6px 0 0;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.6;
}

.bazi-structural__alert {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--brand-cinnabar);
  color: var(--brand-ink);
  font-size: 13px;
}

.bazi-structural__alert p {
  margin: 6px 0 0;
}

.bazi-structural__section h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--brand-gold-dark);
}

.bazi-structural__list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-2);
  line-height: 1.75;
  font-size: 14px;
}

.bazi-structural__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.bazi-structural__table th,
.bazi-structural__table td {
  border: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
}

.bazi-structural__table th {
  background: var(--surface-2);
  color: var(--brand-gold-dark);
}

.bazi-structural__empty {
  margin: 0;
  color: var(--text-3);
  font-size: 14px;
  font-style: italic;
}
</style>
