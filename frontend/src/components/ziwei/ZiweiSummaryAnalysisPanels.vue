<script setup lang="ts">
interface MainStarItem {
  name: string
  brightness: string
  brightness_val: number
}

interface SihuaPathItem {
  star: string
  source: string
  sourcePalaceIdx: number
}

interface StarDistributionItem {
  palaceIdx: number
  palaceName: string
  total: number
  mainCount: number
  auxCount: number
  hasLu: boolean
  hasJi: boolean
}

interface WuxingDistributionItem {
  element: string
  count: number
  color: string
  stars: string[]
}

interface ComboItem {
  name: string
  palace: string
  stars: string[]
  desc: string
  type: string
}

defineProps<{
  analysis?: Record<string, string> | null
  lifePalaceMainStars: MainStarItem[]
  lifePalaceAuxStars: string[]
  sihuaPathList: SihuaPathItem[]
  sihuaByType: Record<string, SihuaPathItem[]>
  starDistribution: StarDistributionItem[]
  maxStarsInPalace: number
  wuxingDistribution: WuxingDistributionItem[]
  maxWuxingCount: number
  wuxingJu: number | string
  wuxingJuName?: string | null
  juColors: Record<string | number, string>
  detectedCombos: ComboItem[]
}>()

const emit = defineEmits<{
  (e: 'select-palace', palaceIdx: number): void
}>()
</script>

<template>
  <div class="summary-analysis-panels">
    <div v-if="analysis && Object.keys(analysis).length" class="analysis-dimensions">
      <h4 class="sec-label sec-label-top">各维度详解</h4>
      <div class="dimension-grid">
        <div v-for="(text, domain) in analysis" :key="domain" class="dimension-item">
          <span class="dimension-label">{{ domain }}</span>
          <p class="dimension-text">{{ text }}</p>
        </div>
      </div>
    </div>

    <div v-if="lifePalaceMainStars.length" class="stars-section">
      <h4 class="sec-label">命宫主星</h4>
      <div class="stars-tags">
        <span
          v-for="star in lifePalaceMainStars"
          :key="star.name"
          class="star-tag"
          :class="{
            lucky: star.brightness_val >= 3,
            neutral: star.brightness_val === 2,
            unlucky: star.brightness_val <= 1,
          }"
        >
          {{ star.name }} <small>{{ star.brightness }}</small>
        </span>
      </div>
    </div>

    <div v-if="lifePalaceAuxStars.length" class="stars-section">
      <h4 class="sec-label">命宫辅曜</h4>
      <div class="stars-tags">
        <span v-for="star in lifePalaceAuxStars" :key="star" class="star-tag neutral">{{ star }}</span>
      </div>
    </div>

    <div v-if="sihuaPathList.length" class="sihua-tracking-section">
      <h4 class="sec-label">命盘四化 <span class="count-badge">{{ sihuaPathList.length }}</span></h4>
      <div class="sihua-track-grid">
        <div v-for="(paths, type) in sihuaByType" :key="type" class="sihua-track-col">
          <div :class="['stc-header', `stc-${type}`]">
            <span class="stc-type">{{ type }}</span>
            <span class="stc-count">{{ paths.length }}</span>
          </div>
          <div class="stc-list">
            <div
              v-for="path in paths"
              :key="`${path.star}-${path.source}`"
              class="stc-item"
              @click="emit('select-palace', path.sourcePalaceIdx)"
            >
              <span class="stc-star">{{ path.star }}</span>
              <span class="stc-arrow">→</span>
              <span class="stc-palace">{{ path.source }}</span>
            </div>
            <div v-if="paths.length === 0" class="stc-empty">无</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="starDistribution.length" class="star-distribution-section">
      <h4 class="sec-label">十二宫星曜分布</h4>
      <div class="star-dist-chart">
        <div
          v-for="item in starDistribution"
          :key="item.palaceIdx"
          class="sdc-bar-wrap"
          @click="emit('select-palace', item.palaceIdx)"
        >
          <div class="sdc-bar" :style="{ height: (item.total / maxStarsInPalace * 60 + 20) + 'px' }">
            <div class="sdc-main" :style="{ height: (item.mainCount / item.total * 100) + '%' }"></div>
            <div class="sdc-aux" :style="{ height: (item.auxCount / item.total * 100) + '%' }"></div>
            <span class="sdc-count">{{ item.total }}</span>
          </div>
          <div class="sdc-label">{{ item.palaceName.replace('宫', '') }}</div>
          <div class="sdc-markers">
            <span v-if="item.hasLu" class="sdc-lu">禄</span>
            <span v-if="item.hasJi" class="sdc-ji">忌</span>
          </div>
        </div>
      </div>
      <div class="sdc-legend">
        <span class="sdc-leg-item"><span class="sdc-leg-main"></span>主星</span>
        <span class="sdc-leg-item"><span class="sdc-leg-aux"></span>辅星</span>
      </div>
    </div>

    <div v-if="wuxingDistribution.length" class="wuxing-distribution-section">
      <h4 class="sec-label">命盘五行分布</h4>
      <div class="wuxing-dist-chart">
        <div v-for="item in wuxingDistribution" :key="item.element" class="wdc-bar-wrap">
          <div
            class="wdc-bar"
            :style="{
              height: (item.count / maxWuxingCount * 50 + 16) + 'px',
              background: `linear-gradient(180deg, ${item.color} 0%, ${item.color}88 100%)`,
            }"
          >
            <span class="wdc-count">{{ item.count }}</span>
          </div>
          <div class="wdc-label" :style="{ color: item.color }">{{ item.element }}</div>
          <div v-if="item.stars.length" class="wdc-stars" :title="item.stars.join('、')">
            {{ item.stars.slice(0, 2).join('、') }}{{ item.stars.length > 2 ? '...' : '' }}
          </div>
        </div>
      </div>
      <div class="wuxing-summary">
        <span v-if="wuxingJuName" class="ws-item">
          五行局：<b :style="{ color: juColors[wuxingJu] }">{{ wuxingJuName }}</b>
        </span>
      </div>
    </div>

    <div v-if="detectedCombos.length" class="star-combos-section">
      <h4 class="sec-label">星曜组合提示 <span class="count-badge">{{ detectedCombos.length }}</span></h4>
      <div class="star-combos-grid">
        <div v-for="(combo, idx) in detectedCombos" :key="`${combo.name}-${idx}`" :class="['combo-card', `combo-${combo.type}`]">
          <div class="combo-header">
            <span class="combo-name">{{ combo.name }}</span>
            <span class="combo-palace">{{ combo.palace }}</span>
          </div>
          <div class="combo-stars">
            <span v-for="star in combo.stars" :key="star" class="combo-star">{{ star }}</span>
          </div>
          <p class="combo-desc">{{ combo.desc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sec-label {
  font-size: var(--fs-sm);
  color: var(--text-3);
  margin-bottom: var(--sp-3);
  font-weight: 500;
}

.sec-label-top {
  margin-top: var(--sp-4);
}

.analysis-dimensions { margin-top: var(--sp-4); }
.dimension-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--sp-4);
}
.dimension-item {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.dimension-label {
  display: inline-block;
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--accent);
  padding: 2px 10px;
  background: rgba(217,119,6,.1);
  border-radius: 10px;
  margin-bottom: var(--sp-2);
}
.dimension-text {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.6;
  margin: 0;
}

.stars-section { margin-top: var(--sp-4); }
.stars-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.star-tag {
  font-size: var(--fs-sm);
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 600;
  background: rgba(217, 119, 6, 0.1);
  color: #d97706;
}
.star-tag.lucky { background: rgba(34,197,94,.1); color: #16a34a; border: 1px solid rgba(34,197,94,.2); }
.star-tag.unlucky { background: rgba(239,68,68,.1); color: #dc2626; border: 1px solid rgba(239,68,68,.2); }

.sihua-tracking-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.sihua-track-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.sihua-track-col {
  background: var(--bg);
  border-radius: 8px;
  overflow: hidden;
}
.stc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  font-weight: 600;
}
.stc-header.stc-禄 { background: rgba(34, 197, 94, 0.15); color: #15803d; }
.stc-header.stc-权 { background: rgba(234, 179, 8, 0.15); color: #a16207; }
.stc-header.stc-科 { background: rgba(139, 92, 246, 0.15); color: #7c3aed; }
.stc-header.stc-忌 { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
.stc-type { font-size: var(--fs-md); }
.stc-count {
  font-size: var(--fs-xs);
  padding: 2px 6px;
  background: rgba(255,255,255,0.5);
  border-radius: 10px;
}
.stc-list { padding: 8px; }
.stc-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 6px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.stc-item:hover { background: var(--primary-bg); }
.stc-star { font-weight: 500; color: var(--text); }
.stc-arrow { color: var(--text-2); font-size: 10px; }
.stc-palace { color: var(--text-2); }
.stc-empty {
  color: var(--text-2);
  font-size: var(--fs-xs);
  text-align: center;
  padding: 8px;
}
.count-badge {
  font-size: var(--fs-xs);
  font-weight: normal;
  padding: 2px 6px;
  background: var(--primary);
  color: #fff;
  border-radius: 10px;
  margin-left: 6px;
}

.star-distribution-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.star-dist-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 4px;
  margin-top: 12px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  min-height: 120px;
}
.sdc-bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.15s;
}
.sdc-bar-wrap:hover { transform: translateY(-2px); }
.sdc-bar {
  width: 100%;
  max-width: 32px;
  display: flex;
  flex-direction: column;
  border-radius: 4px 4px 0 0;
  overflow: hidden;
  position: relative;
}
.sdc-main { background: linear-gradient(180deg, #7c3aed 0%, #a78bfa 100%); }
.sdc-aux { background: linear-gradient(180deg, #3b82f6 0%, #93c5fd 100%); }
.sdc-count {
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.sdc-label {
  font-size: 10px;
  color: var(--text-2);
  margin-top: 4px;
  white-space: nowrap;
}
.sdc-markers { display: flex; gap: 2px; margin-top: 2px; }
.sdc-lu, .sdc-ji {
  font-size: 9px;
  padding: 1px 3px;
  border-radius: 2px;
}
.sdc-lu { background: rgba(34, 197, 94, 0.2); color: #15803d; }
.sdc-ji { background: rgba(239, 68, 68, 0.2); color: #dc2626; }
.sdc-legend {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 8px;
  font-size: var(--fs-xs);
  color: var(--text-2);
}
.sdc-leg-item { display: flex; align-items: center; gap: 4px; }
.sdc-leg-main, .sdc-leg-aux {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.sdc-leg-main { background: linear-gradient(180deg, #7c3aed 0%, #a78bfa 100%); }
.sdc-leg-aux { background: linear-gradient(180deg, #3b82f6 0%, #93c5fd 100%); }

.wuxing-distribution-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.wuxing-dist-chart {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  margin-top: 12px;
  padding: 16px;
  background: var(--bg);
  border-radius: 8px;
  min-height: 100px;
}
.wdc-bar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}
.wdc-bar {
  width: 36px;
  border-radius: 4px 4px 0 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
  transition: height 0.3s;
}
.wdc-count {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}
.wdc-label {
  font-size: var(--fs-md);
  font-weight: 600;
  margin-top: 6px;
}
.wdc-stars {
  font-size: 10px;
  color: var(--text-2);
  margin-top: 2px;
  max-width: 60px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wuxing-summary {
  text-align: center;
  margin-top: 12px;
  font-size: var(--fs-sm);
  color: var(--text-2);
}
.ws-item b { font-size: var(--fs-md); }

.star-combos-section {
  margin-top: var(--sp-4);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border);
}
.star-combos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.combo-card {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
}
.combo-card.combo-auspicious {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.05);
}
.combo-card.combo-inauspicious {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
}
.combo-card.combo-neutral {
  border-color: rgba(234, 179, 8, 0.3);
  background: rgba(234, 179, 8, 0.05);
}
.combo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.combo-name { font-weight: 600; font-size: var(--fs-sm); }
.combo-auspicious .combo-name { color: #15803d; }
.combo-inauspicious .combo-name { color: #dc2626; }
.combo-neutral .combo-name { color: #a16207; }
.combo-palace {
  font-size: var(--fs-xs);
  color: var(--text-2);
  background: var(--bg-card);
  padding: 2px 6px;
  border-radius: 4px;
}
.combo-stars {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}
.combo-star {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-card);
  border-radius: 4px;
  color: var(--text);
}
.combo-desc {
  font-size: var(--fs-xs);
  color: var(--text-2);
  margin: 0;
  line-height: 1.4;
}
</style>
