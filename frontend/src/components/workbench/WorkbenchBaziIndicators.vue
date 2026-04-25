<script setup lang="ts">
interface ShenshaBriefItem {
  name?: string
}

interface BaziKeyIndicators {
  geju: string
  gejuLevel: string
  yongshen: string
  yongshenStar: string
  topGoodShensha: ShenshaBriefItem[]
  topBadShensha: ShenshaBriefItem[]
  weakList: string
}

interface ActiveIndicatorShensha {
  key: string
  name: string
  pillar?: string
  isBeneficial: boolean
  meaning: string
  advice: string
}

interface GejuInfo {
  geju_name?: string | null
  geju_level?: string | null
}

interface YongshenInfo {
  favor?: string[] | null
  avoid?: string[] | null
}

interface StrengthInfo {
  tier?: string | null
}

const props = defineProps<{
  keyIndicators?: BaziKeyIndicators | null
  activeIndicator?: ActiveIndicatorShensha | null
  geju?: GejuInfo | null
  yongshen?: YongshenInfo | null
  strength?: StrengthInfo | null
  dayStem?: string | null
  dayStemColor?: string
}>()

const emit = defineEmits<{
  (e: 'toggleIndicatorShensha', itemKey: string): void
}>()
</script>

<template>
  <div v-if="props.keyIndicators" class="wb-bazi-indicators-wrap">
    <div class="wb-indicator-bar">
      <span v-if="props.keyIndicators.geju" class="wb-indi-item">
        <span class="wb-indi-label">格局</span>
        <span class="wb-indi-value">{{ props.keyIndicators.geju }}<template v-if="props.keyIndicators.gejuLevel"> · {{ props.keyIndicators.gejuLevel }}</template></span>
      </span>
      <span v-if="props.keyIndicators.yongshen" class="wb-indi-item is-ys">
        <span class="wb-indi-label">用神</span>
        <span class="wb-indi-value">{{ props.keyIndicators.yongshen }}<template v-if="props.keyIndicators.yongshenStar"> · {{ props.keyIndicators.yongshenStar }}</template></span>
      </span>
      <span v-if="props.keyIndicators.weakList" class="wb-indi-item is-weak">
        <span class="wb-indi-label">忌行</span>
        <span class="wb-indi-value">{{ props.keyIndicators.weakList }}</span>
      </span>
      <template v-for="s in props.keyIndicators.topGoodShensha" :key="s.name">
        <button
          v-if="s.name"
          type="button"
          class="wb-indi-item is-good is-clickable"
          :class="{ active: props.activeIndicator?.key === `good-${s.name}` }"
          @click="emit('toggleIndicatorShensha', `good-${s.name}`)"
        >
          <span class="wb-indi-label">吉煞</span>
          <span class="wb-indi-value">{{ s.name }}</span>
        </button>
      </template>
      <template v-for="s in props.keyIndicators.topBadShensha" :key="s.name">
        <button
          v-if="s.name"
          type="button"
          class="wb-indi-item is-bad is-clickable"
          :class="{ active: props.activeIndicator?.key === `bad-${s.name}` }"
          @click="emit('toggleIndicatorShensha', `bad-${s.name}`)"
        >
          <span class="wb-indi-label">凶煞</span>
          <span class="wb-indi-value">{{ s.name }}</span>
        </button>
      </template>
    </div>

    <div v-if="props.activeIndicator" class="wb-shensha-detail-card" role="region" aria-label="神煞详情">
      <div class="wb-shensha-detail-head">
        <div class="wb-shensha-detail-title">{{ props.activeIndicator.name }}</div>
        <div class="wb-chip-list">
          <span :class="['wb-chip', props.activeIndicator.isBeneficial ? 'good' : 'bad']">{{ props.activeIndicator.isBeneficial ? '偏吉' : '偏凶' }}</span>
          <span v-if="props.activeIndicator.pillar" class="wb-chip">所在柱：{{ props.activeIndicator.pillar }}</span>
        </div>
      </div>
      <p class="wb-shensha-detail-text">含义：{{ props.activeIndicator.meaning }}</p>
      <p class="wb-shensha-detail-text">建议：{{ props.activeIndicator.advice }}</p>
    </div>
  </div>

  <div v-if="props.geju || props.yongshen || props.strength" class="wb-section wb-geju-row">
    <div v-if="props.geju" class="wb-card">
      <div class="wb-card-label">格局</div>
      <div class="wb-card-main">{{ props.geju.geju_name }}</div>
      <div class="wb-card-sub">{{ props.geju.geju_level }}</div>
    </div>
    <div v-if="props.yongshen" class="wb-card">
      <div class="wb-card-label">用神</div>
      <div class="wb-chips">
        <span v-for="s in props.yongshen.favor ?? []" :key="s" class="wb-chip favor">{{ s }}</span>
      </div>
    </div>
    <div v-if="props.yongshen" class="wb-card">
      <div class="wb-card-label">忌神</div>
      <div class="wb-chips">
        <span v-for="s in props.yongshen.avoid ?? []" :key="s" class="wb-chip avoid">{{ s }}</span>
      </div>
    </div>
    <div v-if="props.strength" class="wb-card">
      <div class="wb-card-label">日主</div>
      <div class="wb-card-main" :style="{ color: props.dayStemColor }">{{ props.dayStem ?? '—' }}</div>
      <div class="wb-card-sub">{{ props.strength.tier }}</div>
    </div>
  </div>
</template>

<style scoped>
.wb-bazi-indicators-wrap {
  display: contents;
}

.wb-section {
  background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.88));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: var(--shadow-xs);
}

.wb-geju-row { display: flex; gap: 12px; flex-wrap: wrap; }
.wb-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  min-width: 100px;
}
.wb-card-label { font-size: 10px; color: var(--text-3); margin-bottom: 4px; text-transform: uppercase; letter-spacing: .05em; }
.wb-card-main  { font-size: 18px; font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.wb-card-sub   { font-size: 11px; color: var(--text-3); margin-top: 2px; }
.wb-chips { display: flex; flex-wrap: wrap; gap: 4px; }

.wb-indicator-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 14px;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 12px;
}

.wb-indi-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
  font-size: 12px;
}

.wb-indi-label { font-size: 10px; color: var(--text-3); font-weight: 700; }
.wb-indi-value { color: var(--text-1); font-family: var(--font-cn); }
.wb-indi-item.is-ys { background: #eff6ff; border-color: #bfdbfe; }
.wb-indi-item.is-ys .wb-indi-value { color: #1e40af; }
.wb-indi-item.is-good { background: #ecfdf5; border-color: #a7f3d0; }
.wb-indi-item.is-good .wb-indi-value { color: #065f46; }
.wb-indi-item.is-bad { background: #fff1f2; border-color: #fecdd3; }
.wb-indi-item.is-bad .wb-indi-value { color: #9f1239; }
.wb-indi-item.is-weak { background: #fefce8; border-color: #fde68a; }
.wb-indi-item.is-weak .wb-indi-value { color: #92400e; }
.wb-indi-item.is-clickable {
  appearance: none;
  cursor: pointer;
  transition: transform .12s, box-shadow .12s, border-color .12s;
}
.wb-indi-item.is-clickable:hover { transform: translateY(-1px); }
.wb-indi-item.is-clickable.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(99,102,241,.12);
}

.wb-chip-list { display: flex; gap: 8px; flex-wrap: wrap; }
.wb-chip {
  font-size: 12px;
  padding: 2px 9px;
  border-radius: 99px;
  font-family: var(--font-cn);
  background: var(--surface-2, #f8fafc);
  color: var(--text-2);
  border: 1px solid var(--border);
}
.wb-chip.good, .wb-chip.favor { background: #dcfce7; color: #15803d; }
.wb-chip.bad, .wb-chip.avoid { background: #fee2e2; color: #b91c1c; }

.wb-shensha-detail-card {
  margin-top: -4px;
  margin-bottom: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(99,102,241,.05), transparent 52%), var(--surface);
  padding: 12px 14px;
}
.wb-shensha-detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.wb-shensha-detail-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-1);
  font-family: var(--font-cn);
}
.wb-shensha-detail-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-2);
  font-family: var(--font-cn);
}
.wb-shensha-detail-text + .wb-shensha-detail-text { margin-top: 2px; }

@media (max-width: 768px) {
  .wb-indicator-bar { gap: 5px; padding: 8px 10px; }
  .wb-indi-item { font-size: 11px; padding: 3px 8px; }
  .wb-shensha-detail-head { flex-direction: column; align-items: flex-start; }
  .wb-shensha-detail-card { padding: 10px 12px; }
}
</style>
