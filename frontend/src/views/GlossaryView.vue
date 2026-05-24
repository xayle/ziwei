<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getGlossary, type GlossaryItem } from '@/api/static-data'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const search = ref('')
const category = ref('')
const items = ref<GlossaryItem[]>([])
const copiedTerm = ref('')

const categoryOptions = ['格局', '神煞', '五行', '十神', '大运', '其他'] as const

const suggestedTerms = computed(() => {
  const raw = route.query.suggested
  if (!raw) return [] as string[]
  const list = Array.isArray(raw) ? raw : [raw]
  return Array.from(new Set(list.map(item => String(item).trim()).filter(Boolean))).slice(0, 10)
})

const sourceLabel = computed(() => route.query.from === 'ziwei' ? '来自紫微命盘联想词条' : '独立术语检索工作区')

function getRelatedTerms(item: GlossaryItem) {
  return items.value
    .filter((candidate) => candidate.term !== item.term && (
      candidate.category === item.category
      || candidate.definition.includes(item.term)
      || item.definition.includes(candidate.term)
    ))
    .slice(0, 3)
}

async function loadGlossary() {
  loading.value = true
  error.value = ''
  try {
    items.value = await getGlossary({
      q: search.value.trim() || undefined,
      category: category.value || undefined,
      limit: 30,
    })
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '词汇加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function applySuggestedTerm(term: string) {
  search.value = term
  void loadGlossary()
}

async function copyGlossaryItem(item: GlossaryItem) {
  const copyText = [item.term, item.definition, item.classic_source ? `典籍：${item.classic_source}` : '']
    .filter(Boolean)
    .join('\n')

  try {
    await navigator.clipboard.writeText(copyText)
    copiedTerm.value = item.term
  } catch {
    error.value = '复制失败，请手动复制'
  }
}

function backToZiwei() {
  router.push('/ziwei')
}

onMounted(() => {
  if (typeof route.query.q === 'string') {
    search.value = route.query.q
  }
  void loadGlossary()
})

watch(() => route.query.q, (value) => {
  if (typeof value === 'string' && value !== search.value) {
    search.value = value
    void loadGlossary()
  }
})
</script>

<template>
  <main class="glossary-view">
    <section class="hero card">
      <div>
        <p class="hero-kicker">内容与知识资产</p>
        <h1 class="hero-title">术语词库</h1>
        <p class="hero-desc">独立承接术语检索、命盘联想词条与复制引用，不再挤在紫微超级页的浮层里。</p>
      </div>
      <div class="hero-actions">
        <button v-if="route.query.from === 'ziwei'" class="btn-secondary" @click="backToZiwei">返回紫微模块</button>
      </div>
    </section>

    <section class="toolbar card">
      <div class="toolbar-main">
        <label class="field field-search">
          <span>搜索术语</span>
          <input
            v-model="search"
            type="text"
            placeholder="如：紫府同宫 / 化忌 / 天乙贵人"
            @keydown.enter.prevent="loadGlossary"
          >
        </label>
        <label class="field">
          <span>分类</span>
          <select v-model="category" @change="loadGlossary">
            <option value="">全部分类</option>
            <option v-for="item in categoryOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <button class="btn-primary" :disabled="loading" @click="loadGlossary">{{ loading ? '查询中…' : '查询' }}</button>
      </div>
      <div class="toolbar-note">{{ sourceLabel }}</div>
      <div v-if="suggestedTerms.length" class="suggest-row">
        <span class="suggest-label">命盘联想</span>
        <button v-for="term in suggestedTerms" :key="term" class="suggest-chip" @click="applySuggestedTerm(term)">{{ term }}</button>
      </div>
    </section>

    <section v-if="error" class="state-card error card">{{ error }}</section>
    <section v-else-if="loading" class="state-card card">加载中…</section>
    <section v-else-if="items.length === 0" class="state-card card">
      {{ search ? `未找到“${search}”相关词汇` : '暂无词汇，可尝试上方联想词条或手动输入关键词。' }}
    </section>

    <section v-else class="glossary-list">
      <article v-for="item in items" :key="item.term" class="glossary-card card">
        <div class="card-top">
          <div>
            <h2 class="term-title">{{ item.term }}</h2>
            <div v-if="item.pinyin" class="term-pinyin">{{ item.pinyin }}</div>
          </div>
          <div class="card-actions">
            <span class="category-chip">{{ item.category }}</span>
            <button class="copy-btn" @click="copyGlossaryItem(item)">{{ copiedTerm === item.term ? '已复制' : '复制' }}</button>
          </div>
        </div>
        <p class="term-definition">{{ item.definition || '暂无定义' }}</p>
        <div v-if="item.classic_source" class="term-source">典籍：{{ item.classic_source }}</div>
        <div v-if="getRelatedTerms(item).length" class="related-row">
          <span class="related-label">相关词条</span>
          <button
            v-for="related in getRelatedTerms(item)"
            :key="`${item.term}-${related.term}`"
            class="related-chip"
            @click="applySuggestedTerm(related.term)"
          >
            {{ related.term }}
          </button>
        </div>
      </article>
    </section>
  </main>
</template>

<style scoped>
.glossary-view {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow-sm);
}

.hero {
  padding: 28px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.08), rgba(29, 78, 216, 0.08));
}

.hero-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #6d28d9;
}

.hero-title {
  margin: 0;
  font-size: 30px;
  color: var(--text);
}

.hero-desc {
  margin: 12px 0 0;
  max-width: 760px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-2);
}

.toolbar {
  padding: 20px;
}

.toolbar-main {
  display: flex;
  gap: 12px;
  align-items: end;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 180px;
}

.field-search {
  flex: 1;
  min-width: 280px;
}

.field span,
.toolbar-note,
.suggest-label,
.related-label,
.term-source,
.term-pinyin {
  font-size: 12px;
  color: var(--text-3);
}

input,
select {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
}

.btn-primary,
.btn-secondary,
.copy-btn,
.suggest-chip,
.related-chip {
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  padding: 10px 16px;
  border: none;
  background: var(--accent);
  color: #fff;
}

.btn-primary:disabled {
  opacity: .65;
  cursor: not-allowed;
}

.btn-secondary,
.copy-btn,
.suggest-chip,
.related-chip {
  padding: 9px 14px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.86);
  color: var(--text);
}

.toolbar-note {
  margin-top: 12px;
}

.suggest-row,
.related-row,
.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.suggest-row {
  margin-top: 14px;
}

.suggest-chip,
.related-chip,
.category-chip {
  border-radius: 999px;
}

.category-chip {
  padding: 4px 10px;
  background: var(--surface-2);
  color: var(--text-2);
  font-size: 11px;
  font-weight: 700;
}

.state-card {
  padding: 18px 20px;
  color: var(--text-2);
}

.state-card.error {
  border-color: #fecaca;
  background: #fff1f2;
  color: #dc2626;
}

.glossary-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.glossary-card {
  padding: 18px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.term-title {
  margin: 0;
  font-size: 18px;
  color: var(--text);
}

.term-pinyin {
  margin-top: 4px;
}

.term-definition {
  margin: 14px 0 10px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text);
}

.related-row {
  margin-top: 12px;
}

@media (max-width: 760px) {
  .glossary-view {
    padding: 16px;
  }

  .hero,
  .toolbar-main,
  .card-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .field,
  .field-search {
    width: 100%;
    min-width: 0;
  }

  .glossary-list {
    grid-template-columns: 1fr;
  }
}
</style>
