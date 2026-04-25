<script setup lang="ts">
interface ZiweiRemedyItem {
  id: string | number
  name: string
  valid_scope?: string
  evidence?: string
  actions?: string[]
}

interface ZiweiSuggestionItem {
  id: string | number
  category_label?: string
  name: string
}

const props = defineProps<{
  remedies: ZiweiRemedyItem[]
  suggestions: ZiweiSuggestionItem[]
}>()
</script>

<template>
  <section class="zw-advice-card">
    <h2 class="zw-advice-title">建议与调理</h2>

    <div v-if="props.remedies.length" class="zw-advice-list">
      <div v-for="item in props.remedies.slice(0, 4)" :key="item.id" class="zw-advice-item">
        {{ item.name }} · {{ item.valid_scope }} · {{ item.actions?.[0] ?? item.evidence }}
      </div>
    </div>

    <div v-if="props.suggestions.length" class="zw-advice-chip-list">
      <span v-for="item in props.suggestions.slice(0, 6)" :key="item.id" class="zw-advice-chip">
        {{ item.category_label }} · {{ item.name }}
      </span>
    </div>

    <div v-if="!props.remedies.length && !props.suggestions.length" class="zw-advice-empty">
      暂无可展示的调理建议。
    </div>
  </section>
</template>

<style scoped>
.zw-advice-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  padding: 14px 16px;
}

.zw-advice-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 800;
  color: var(--text-1);
  letter-spacing: .01em;
}

.zw-advice-list {
  display: grid;
  gap: 8px;
}

.zw-advice-item {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface-2, #f8fafc);
  color: var(--text-2);
  line-height: 1.7;
  font-size: 12px;
  font-family: var(--font-cn);
}

.zw-advice-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.zw-advice-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-2);
  font-family: var(--font-cn);
}

.zw-advice-empty {
  padding: 12px 0 2px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.7;
  font-family: var(--font-cn);
}
</style>
