<script setup lang="ts">
export type WorkbenchCaseHubStatusItem = {
  label: string
  value: string
}

export type WorkbenchCaseHubAction = {
  key: string
  title: string
  desc: string
  button: string
  route: string
  tone: 'accent' | 'ghost'
  disabled?: boolean
}

withDefaults(defineProps<{
  summary: string
  caseName: string
  birthLocalText: string
  locationText: string
  profileSynced?: boolean
  statusItems: WorkbenchCaseHubStatusItem[]
  actions: WorkbenchCaseHubAction[]
}>(), {
  profileSynced: false,
})

const emit = defineEmits<{
  openRoute: [route: string]
  editCase: []
}>()
</script>

<template>
  <div class="wb-hub-shell">
    <section class="wb-hub-hero wb-card">
      <div class="wb-hub-hero-main">
        <div class="wb-card-label">咨询流程</div>
        <h1 class="wb-hub-title">先确认资料，再进入分析、解读与报告。</h1>
        <p class="wb-hub-summary">{{ summary }}</p>
        <div class="wb-hub-meta">
          <span class="wb-hub-chip">{{ caseName }}</span>
          <span class="wb-hub-chip">{{ birthLocalText }}</span>
          <span class="wb-hub-chip">{{ locationText }}</span>
          <span v-if="profileSynced" class="wb-hub-chip">个人信息同步</span>
        </div>
      </div>
      <div class="wb-hub-toolbar">
        <button class="wb-btn-accent" type="button" @click="emit('openRoute', '/bazi')">进入八字分析</button>
        <button class="wb-btn-ghost" type="button" @click="emit('openRoute', '/ziwei')">进入紫微分析</button>
        <button class="wb-btn-ghost" type="button" @click="emit('editCase')">补充客户资料</button>
      </div>
    </section>

    <section class="wb-hub-grid">
      <article class="wb-card wb-hub-card">
        <div class="wb-hub-card-title">当前咨询状态</div>
        <div class="wb-hub-status-list">
          <div v-for="item in statusItems" :key="item.label" class="wb-hub-status-item">
            <span class="wb-hub-status-label">{{ item.label }}</span>
            <span class="wb-hub-status-value">{{ item.value }}</span>
          </div>
        </div>
      </article>

      <article class="wb-card wb-hub-card">
        <div class="wb-hub-card-title">推荐下一步</div>
        <div class="wb-hub-action-list">
          <div v-for="action in actions" :key="action.key" class="wb-hub-action-item">
            <div class="wb-hub-action-head">
              <div class="wb-hub-action-title">{{ action.title }}</div>
              <span v-if="action.disabled" class="wb-hub-action-tag">需先选案</span>
            </div>
            <div class="wb-hub-action-desc">{{ action.desc }}</div>
            <button
              class="wb-hub-action-btn"
              :class="action.tone === 'accent' ? 'is-accent' : 'is-ghost'"
              type="button"
              :disabled="action.disabled"
              @click="emit('openRoute', action.route)"
            >
              {{ action.button }}
            </button>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.wb-hub-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wb-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
}

.wb-card-label {
  font-size: 10px;
  color: var(--text-3);
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: .05em;
}

.wb-hub-hero {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 20px;
}

.wb-hub-hero-main {
  min-width: 0;
  flex: 1;
}

.wb-hub-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.35;
  color: var(--text);
  font-family: var(--font-cn);
}

.wb-hub-summary {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--text-2);
}

.wb-hub-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.wb-hub-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  font-size: 12px;
  color: var(--text-2);
}

.wb-hub-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.wb-hub-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.95fr) minmax(360px, 1.05fr);
  gap: 16px;
}

.wb-hub-card {
  padding: 18px 20px;
}

.wb-hub-card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 14px;
}

.wb-hub-status-list,
.wb-hub-action-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wb-hub-status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.wb-hub-status-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.wb-hub-status-label {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-3);
}

.wb-hub-status-value {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.wb-hub-action-item {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.wb-hub-action-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.wb-hub-action-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.wb-hub-action-tag {
  font-size: 10px;
  color: var(--text-3);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
}

.wb-hub-action-desc {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-2);
}

.wb-hub-action-btn,
.wb-btn-accent,
.wb-btn-ghost {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.wb-hub-action-btn {
  margin-top: 12px;
}

.wb-btn-accent,
.wb-hub-action-btn.is-accent {
  border: none;
  background: var(--accent);
  color: #fff;
}

.wb-btn-ghost,
.wb-hub-action-btn.is-ghost {
  border: 1px solid var(--border-md);
  background: #fff;
  color: var(--text-2);
}

.wb-hub-action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 1280px) {
  .wb-hub-grid { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  .wb-hub-hero { flex-direction: column; }
  .wb-hub-toolbar { justify-content: flex-start; }
}

@media (max-width: 768px) {
  .wb-hub-shell { padding-inline: 16px; }
}

@media (max-width: 560px) {
  .wb-hub-toolbar { flex-direction: column; }
}
</style>
