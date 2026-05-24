<script setup lang="ts">
import { computed } from 'vue'
import type { CaseOut } from '@/api/report'

const props = defineProps<{
  modelValue: string
  cases: CaseOut[]
  selectedId: string | null
  profileSyncTag: string
  currentDayunLabel?: string | null
  ziweiSummaryText?: string | null
  baziSummaryLine?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  create: []
  selectCase: [item: CaseOut]
}>()

const searchProxy = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})

function genderLabel(gender: string | null | undefined): string {
  if (gender === 'female') return '女'
  if (gender === 'male') return '男'
  return '—'
}
</script>

<template>
  <section class="wb-caselist">
    <div class="wb-caselist-header">
      <div>
        <div class="wb-caselist-title">咨询队列</div>
        <div class="wb-caselist-sub">先选客户，再继续分析与交付</div>
      </div>
      <button class="btn-new" @click="emit('create')" title="新建咨询">＋</button>
    </div>

    <div class="wb-search-wrap">
      <input
        v-model="searchProxy"
        class="wb-search"
        placeholder="搜索客户姓名、城市或标签…"
      />
    </div>

    <div class="wb-caselist-body">
      <div
        v-for="item in props.cases"
        :key="item.id"
        class="wb-case-item"
        :class="{ active: props.selectedId === item.id }"
        @click="emit('selectCase', item)"
      >
        <div class="wb-case-avatar">
          {{ item.name?.charAt(0) ?? '？' }}
        </div>
        <div class="wb-case-info">
          <div class="wb-case-name">
            {{ item.name }}
            <span class="wb-case-gender" :class="item.gender">
              {{ genderLabel(item.gender) }}
            </span>
            <span v-if="item.tags?.includes(props.profileSyncTag)" class="wb-case-sync">个人信息</span>
          </div>
          <div class="wb-case-date">{{ item.birth_dt_local?.slice(0, 10) ?? '—' }}</div>
          <div class="wb-case-meta">
            <span>{{ item.birth_dt_local?.slice(11, 16) || '—:—' }}</span>
            <span>·</span>
            <span>{{ item.city || item.tz || '—' }}</span>
          </div>
          <div v-if="item.id === props.selectedId && props.currentDayunLabel" class="wb-case-dayun">
            当前大运：{{ props.currentDayunLabel }}
          </div>
          <div v-if="item.id === props.selectedId && props.ziweiSummaryText" class="wb-case-ziwei">
            {{ props.ziweiSummaryText }}
          </div>
          <div v-if="item.id === props.selectedId && props.baziSummaryLine" class="wb-case-bazi-summary">
            {{ props.baziSummaryLine }}
          </div>
          <div v-if="item.tags?.length" class="wb-case-tags">
            <span v-for="tag in item.tags" :key="tag" class="wb-tag">{{ tag }}</span>
          </div>
        </div>
      </div>

      <div v-if="props.cases.length === 0" class="wb-empty-hint">
        {{ props.modelValue ? '没有找到匹配客户' : '还没有咨询客户' }}
      </div>
    </div>
  </section>
</template>

<style scoped>
.wb-caselist {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  height: 100%;
  overflow: hidden;
}

.wb-caselist-header {
  padding: 16px 16px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.wb-caselist-title { font-size: 13px; font-weight: 700; color: var(--text); }

.wb-caselist-sub {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-3);
}

.btn-new {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border-md);
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  color: var(--accent);
  font-size: 18px;
  line-height: 1;
  font-weight: 300;
  display: grid;
  place-items: center;
  transition: all var(--dur-fast);
}

.btn-new:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

.wb-search-wrap { padding: 10px 12px 8px; flex-shrink: 0; }

.wb-search {
  width: 100%;
  box-sizing: border-box;
  padding: 7px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text);
  outline: none;
  transition: border-color var(--dur-fast);
}

.wb-search:focus { border-color: var(--accent); }
.wb-search::placeholder { color: var(--text-3); }

.wb-caselist-body { flex: 1; overflow-y: auto; padding: 4px 8px 12px; }

.wb-case-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background var(--dur-fast);
  border: 1px solid transparent;
  margin-bottom: 2px;
}

.wb-case-item:hover { background: var(--surface-2); }
.wb-case-item.active { background: var(--accent-lt); border-color: var(--accent-glow); }

.wb-case-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 15px;
  font-weight: 700;
  font-family: var(--font-cn);
  flex-shrink: 0;
}

.wb-case-item.active .wb-case-avatar { background: var(--accent-dark); }

.wb-case-info { flex: 1; min-width: 0; }

.wb-case-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--font-cn);
  display: flex;
  align-items: center;
  gap: 6px;
}

.wb-case-gender {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 99px;
  font-family: var(--font-ui);
}

.wb-case-gender.male { background: #dbeafe; color: #1d4ed8; }
.wb-case-gender.female { background: #fce7f3; color: #be185d; }

.wb-case-date {
  font-size: 11px;
  color: var(--text-3);
  margin-top: 2px;
  font-family: var(--font-mono);
}

.wb-case-meta {
  margin-top: 2px;
  font-size: 11px;
  color: var(--text-3);
  display: inline-flex;
  gap: 6px;
  align-items: center;
}

.wb-case-tags { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }

.wb-case-sync {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 7px;
  border: 1px solid var(--border-md);
  border-radius: 999px;
  font-size: 10px;
  color: var(--text-2);
  background: var(--surface-2);
}

.wb-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 99px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-3);
}

.wb-case-dayun,
.wb-case-ziwei,
.wb-case-bazi-summary {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wb-case-dayun {
  font-size: 10px;
  color: var(--accent, #6366f1);
  margin-top: 2px;
  font-family: var(--font-cn);
}

.wb-case-ziwei {
  font-size: 10px;
  color: #7c3aed;
  margin-top: 2px;
  font-family: var(--font-cn);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wb-case-bazi-summary {
  font-size: 10px;
  color: var(--text-3);
  margin-top: 3px;
  font-family: var(--font-cn);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: .85;
}

.wb-empty-hint { text-align: center; padding: 40px 16px; font-size: 13px; color: var(--text-3); }

@media print {
  .wb-caselist { display: none; }
  .wb-search-wrap { display: none; }
}
</style>
