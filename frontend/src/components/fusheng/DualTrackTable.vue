<script setup lang="ts">
export type DualTrackReferenceRow = {
  id: string
  topic?: string
  recorded: string
  engine: string
  note?: string
}

withDefaults(defineProps<{
  rows: DualTrackReferenceRow[]
  title?: string
  variant?: 'reference' | 'simple'
}>(), {
  title: '执业双轨对照表',
  variant: 'reference',
})
</script>

<template>
  <div class="dual-track-table" data-testid="dual-track-table">
    <h3 v-if="title">{{ title }}</h3>
    <table class="dual-track-table__grid">
      <thead>
        <tr>
          <th>编号</th>
          <th v-if="variant === 'reference'">主题</th>
          <th>古籍/对照</th>
          <th>引擎</th>
          <th>说明</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.id }}</td>
          <td v-if="variant === 'reference'">{{ row.topic || '—' }}</td>
          <td>{{ row.recorded }}</td>
          <td>{{ row.engine }}</td>
          <td>{{ row.note || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!rows.length" class="dual-track-table__empty">暂无双轨登记项。</p>
  </div>
</template>

<style scoped>
.dual-track-table h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: var(--brand-gold-dark);
}

.dual-track-table__grid {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dual-track-table__grid th,
.dual-track-table__grid td {
  border: 1px solid var(--border);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}

.dual-track-table__grid th {
  background: var(--inset-tint);
  color: var(--brand-gold-dark);
}

.dual-track-table__empty {
  margin: 8px 0 0;
  color: var(--text-3);
  font-size: 13px;
  font-style: italic;
}
</style>
