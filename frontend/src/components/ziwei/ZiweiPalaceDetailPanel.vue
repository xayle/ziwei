<script setup lang="ts">
import type { PalaceResponse } from '@/api/ziwei'

defineProps<{
  selectedPalace: PalaceResponse | null
  starredStarsDistribution: Array<{ star: string; palaces: string[] }>
  showStarTooltip: (starName: string, event: MouseEvent) => void
  hideStarTooltip: () => void
  toggleStarStar: (starName: string) => void
  isStarStarred: (starName: string) => boolean
  tfColorStyle: (transform: string) => Record<string, string>
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <transition name="slide">
    <div v-if="selectedPalace" class="palace-detail card">
      <div class="detail-header">
        <h3>
          {{ selectedPalace.name }}
          <span class="detail-branch">{{ selectedPalace.branch }}</span>
        </h3>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <div class="detail-layout">
        <div class="detail-left">
          <div v-if="selectedPalace.main_stars.length" class="detail-stars">
            <span
              v-for="star in selectedPalace.main_stars"
              :key="star.name"
              class="detail-star"
              @mouseenter="showStarTooltip(star.name, $event)"
              @mouseleave="hideStarTooltip"
            >
              <b class="star-name-hover">{{ star.name }}</b>
              <button
                class="star-fav-btn"
                :class="{ starred: isStarStarred(star.name) }"
                :title="isStarStarred(star.name) ? '取消关注' : '关注此星'"
                @click.stop="toggleStarStar(star.name)"
              >
                {{ isStarStarred(star.name) ? '♥' : '♡' }}
              </button>
              <span class="star-br">{{ star.brightness }}</span>
              <span v-if="star.transforms.length" class="star-tf">
                {{ star.transforms.join(' ') }}
              </span>
            </span>
          </div>

          <div v-if="Object.keys(selectedPalace.flying_out || {}).length" class="detail-flying detail-panel">
            <span class="detail-sec-label">飞出四化：</span>
            <span
              v-for="(val, star) in selectedPalace.flying_out"
              :key="star"
              class="pc-tf detail-tf"
              :style="tfColorStyle(val)"
            >
              {{ star }}{{ val.slice(1) }}
            </span>
          </div>

          <div v-if="selectedPalace.analysis_tags?.length" class="detail-tags detail-panel">
            <span v-for="tag in selectedPalace.analysis_tags" :key="tag" class="detail-tag">{{ tag }}</span>
          </div>

          <div v-if="selectedPalace.xiaoxian_ages?.length || selectedPalace.opposition_name" class="detail-shens detail-panel">
            <span v-if="selectedPalace.xiaoxian_ages?.length" class="shen-item">
              小限年龄：<b>{{ selectedPalace.xiaoxian_ages.join('、') }}</b>
            </span>
            <span v-if="selectedPalace.opposition_name" class="shen-item">
              对宫：<b>{{ selectedPalace.opposition_name }}</b>
            </span>
          </div>

          <div v-if="selectedPalace.changsheng" class="detail-shens detail-panel">
            <span class="shen-item">长生：<b>{{ selectedPalace.changsheng }}</b></span>
            <span v-if="selectedPalace.jiangqian_star" class="shen-item">将前：<b>{{ selectedPalace.jiangqian_star }}</b></span>
            <span v-if="selectedPalace.suiqian_star" class="shen-item">岁前：<b>{{ selectedPalace.suiqian_star }}</b></span>
          </div>

          <div v-if="selectedPalace.dayun_boshi && Object.keys(selectedPalace.dayun_boshi).length" class="detail-shens detail-panel">
            <span class="shen-item">大运博士星：</span>
            <span v-for="(branch, star) in selectedPalace.dayun_boshi" :key="star" class="boshi-tag">
              {{ star }}·{{ branch }}
            </span>
          </div>

          <div v-if="starredStarsDistribution.length" class="detail-starred-stars detail-panel">
            <span class="shen-item">关注星曜分布：</span>
            <span v-for="item in starredStarsDistribution" :key="item.star" class="starred-star-item">
              <b>{{ item.star }}</b>在{{ item.palaces.join('、') }}
            </span>
          </div>
        </div>

        <div class="detail-right detail-panel">
          <p v-if="selectedPalace.conclusion" class="detail-conclusion">
            {{ selectedPalace.conclusion }}
          </p>
          <p v-if="selectedPalace.explanation" class="detail-explanation">
            {{ selectedPalace.explanation }}
          </p>
          <p v-if="selectedPalace.suggestion" class="detail-suggestion">
            💡 {{ selectedPalace.suggestion }}
          </p>
          <p v-else-if="selectedPalace.analysis" class="detail-explanation">
            {{ selectedPalace.analysis }}
          </p>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all .25s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.palace-detail {
  margin-bottom: var(--sp-5);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-3);
}

.detail-header h3 {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-family: var(--font-cn);
}

.detail-branch {
  font-size: var(--fs-sm);
  color: var(--text-3);
  margin-left: var(--sp-2);
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.2fr);
  gap: var(--sp-3);
}

.detail-left,
.detail-right {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.detail-panel {
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-3);
  font-size: var(--fs-lg);
  padding: 0 4px;
}

.close-btn:hover {
  color: var(--danger-dark);
}

.detail-stars {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.detail-star {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  cursor: help;
}

.detail-star:hover {
  background: var(--surface);
}

.star-name-hover {
  transition: color 0.15s;
}

.detail-star:hover .star-name-hover {
  color: var(--accent);
}

.star-br {
  color: var(--text-3);
  font-size: var(--fs-xs);
}

.star-tf {
  color: var(--accent);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.detail-conclusion {
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--sp-2);
}

.detail-explanation {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.7;
  margin-bottom: var(--sp-2);
  white-space: pre-line;
}

.detail-suggestion {
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  background: rgba(217,119,6,.08);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
}

.detail-flying {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  padding: var(--sp-2) 0;
  margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border);
}

.detail-sec-label {
  font-size: var(--fs-xs);
  color: var(--text-3);
  flex-shrink: 0;
}

.detail-tf {
  font-size: 11px !important;
  padding: 1px 5px !important;
}

.detail-shens {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  padding: var(--sp-2) 0;
  margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border);
  font-size: var(--fs-sm);
}

.shen-item {
  color: var(--text-2);
}

.shen-item b {
  color: var(--text);
}

.boshi-tag {
  font-size: 9px;
  padding: 1px 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  color: var(--text-3);
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  padding: var(--sp-2) 0;
  margin-bottom: var(--sp-2);
  border-top: 1px solid var(--border);
}

.detail-tag {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  background: rgba(37,99,235,.08);
  color: #1d4ed8;
  border: 1px solid rgba(37,99,235,.2);
  border-radius: 10px;
}

.star-fav-btn {
  padding: 0 2px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: #d1d5db;
  transition: all 0.2s;
  vertical-align: baseline;
}

.star-fav-btn:hover,
.star-fav-btn.starred {
  color: #ec4899;
}

.detail-starred-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 8px 0;
  font-size: var(--fs-sm);
}

.starred-star-item {
  padding: 3px 8px;
  background: #fdf2f8;
  border: 1px solid #fbcfe8;
  border-radius: 12px;
  color: #be185d;
  font-size: 11px;
}

.starred-star-item b {
  color: #db2777;
  margin-right: 2px;
}

@media (max-width: 960px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>