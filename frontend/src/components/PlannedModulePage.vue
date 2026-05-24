<script setup lang="ts">
import { useRouter } from 'vue-router'

export type PlannedModuleAction = {
  label: string
  description?: string
  to: string
  tone?: 'primary' | 'secondary'
}

export type PlannedModuleTextCard = {
  title: string
  text: string
}

export type PlannedModuleRoadmapItem = {
  phase: string
  title: string
  text: string
}

const props = withDefaults(defineProps<{
  badge?: string
  title: string
  description: string
  heroActions?: PlannedModuleAction[]
  milestones?: PlannedModuleTextCard[]
  roadmap?: PlannedModuleRoadmapItem[]
  prepChecklist?: string[]
  relatedModules?: PlannedModuleAction[]
  nextActions?: PlannedModuleAction[]
}>(), {
  badge: '规划中模块',
  heroActions: () => [],
  milestones: () => [],
  roadmap: () => [],
  prepChecklist: () => [],
  relatedModules: () => [],
  nextActions: () => [],
})

const router = useRouter()

function openAction(action: PlannedModuleAction) {
  if (!action?.to) return
  router.push(action.to)
}
</script>

<template>
  <div class="pm-wrap">
    <section class="pm-hero card">
      <div class="pm-badge">{{ badge }}</div>
      <h1 class="pm-title">{{ title }}</h1>
      <p class="pm-desc">{{ description }}</p>
      <div v-if="heroActions.length" class="pm-actions">
        <button
          v-for="action in heroActions"
          :key="`${action.label}-${action.to}`"
          :class="['pm-btn', action.tone === 'primary' ? 'pm-btn-primary' : '']"
          type="button"
          @click="openAction(action)"
        >
          {{ action.label }}
        </button>
      </div>
    </section>

    <section v-if="milestones.length" class="pm-grid">
      <article v-for="item in milestones" :key="item.title" class="pm-card card">
        <div class="pm-card-label">{{ item.title }}</div>
        <p class="pm-card-text">{{ item.text }}</p>
      </article>
    </section>

    <section v-if="roadmap.length" class="pm-roadmap card">
      <div class="pm-section-title">建设路线</div>
      <div class="pm-roadmap-list">
        <article v-for="item in roadmap" :key="item.phase" class="pm-roadmap-item">
          <div class="pm-roadmap-phase">{{ item.phase }}</div>
          <div class="pm-roadmap-title">{{ item.title }}</div>
          <p class="pm-roadmap-text">{{ item.text }}</p>
        </article>
      </div>
    </section>

    <section v-if="prepChecklist.length || relatedModules.length" class="pm-dual-grid">
      <section v-if="prepChecklist.length" class="pm-block card">
        <div class="pm-section-title">现在先准备什么</div>
        <div class="pm-prep-list">
          <div v-for="item in prepChecklist" :key="item" class="pm-prep-item">
            <span class="pm-prep-index">✓</span>
            <span class="pm-prep-text">{{ item }}</span>
          </div>
        </div>
      </section>

      <section v-if="relatedModules.length" class="pm-block card">
        <div class="pm-section-title">相关工作区</div>
        <div class="pm-related-list">
          <button
            v-for="item in relatedModules"
            :key="`${item.label}-${item.to}`"
            class="pm-related-item"
            type="button"
            @click="openAction(item)"
          >
            <span class="pm-related-label">{{ item.label }}</span>
            <span class="pm-related-desc">{{ item.description }}</span>
          </button>
        </div>
      </section>
    </section>

    <section v-if="nextActions.length" class="pm-next card">
      <div class="pm-section-title">建议下一步</div>
      <div class="pm-next-list">
        <button
          v-for="item in nextActions"
          :key="`${item.label}-${item.to}`"
          class="pm-next-item"
          type="button"
          @click="openAction(item)"
        >
          <span class="pm-next-label">{{ item.label }}</span>
          <span class="pm-next-desc">{{ item.description }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pm-wrap {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.pm-hero,
.pm-card,
.pm-roadmap,
.pm-block,
.pm-next {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.pm-hero {
  padding: 24px;
  background: linear-gradient(180deg, #fffaf0 0%, var(--surface) 100%);
}

.pm-badge {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  background: #fff;
  color: #92400e;
  border: 1px solid #fcd34d;
  font-size: 12px;
  font-weight: 700;
}

.pm-title {
  margin: 12px 0 8px;
  font-size: 30px;
  line-height: 1.2;
  color: var(--text);
}

.pm-desc {
  max-width: 760px;
  margin: 0;
  font-size: var(--fs-md);
  line-height: 1.8;
  color: var(--text-2);
}

.pm-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.pm-btn {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid var(--border-md);
  background: #fff;
  color: var(--text-2);
  cursor: pointer;
  font-weight: 700;
}

.pm-btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.pm-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.pm-card {
  padding: 18px;
}

.pm-card-label,
.pm-section-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
  color: var(--text-3);
  text-transform: uppercase;
}

.pm-card-text {
  margin: 10px 0 0;
  font-size: var(--fs-sm);
  line-height: 1.8;
  color: var(--text-2);
}

.pm-roadmap,
.pm-block,
.pm-next {
  padding: 18px;
}

.pm-roadmap-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 12px;
}

.pm-roadmap-item {
  padding: 16px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.pm-roadmap-phase {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--accent-dark);
}

.pm-roadmap-title {
  margin-top: 8px;
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text);
}

.pm-roadmap-text {
  margin: 8px 0 0;
  font-size: var(--fs-xs);
  line-height: 1.8;
  color: var(--text-2);
}

.pm-dual-grid {
  display: grid;
  grid-template-columns: 1.1fr .9fr;
  gap: 14px;
}

.pm-prep-list,
.pm-related-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.pm-prep-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.pm-prep-index {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-lt);
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.pm-prep-text {
  font-size: var(--fs-sm);
  line-height: 1.8;
  color: var(--text-2);
}

.pm-related-item,
.pm-next-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-2);
  cursor: pointer;
  text-align: left;
}

.pm-related-label,
.pm-next-label {
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--text);
}

.pm-related-desc,
.pm-next-desc {
  font-size: var(--fs-xs);
  line-height: 1.7;
  color: var(--text-3);
}

.pm-next-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}

@media (max-width: 960px) {
  .pm-roadmap-list,
  .pm-dual-grid,
  .pm-grid,
  .pm-next-list {
    grid-template-columns: 1fr;
  }
}
</style>
