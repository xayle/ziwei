<script setup lang="ts">
/**
 * CardOverview.vue — 卡1：命盘概要
 * 固定显示，不随章节变化
 * 来源：CaseOut + BaziResponse（若已加载）
 */
import { computed } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const isCollapsed = computed(() => store.cardCollapsed['overview'] ?? false)
</script>

<template>
  <div class="card" :class="{ collapsed: isCollapsed }">
    <button class="card-header" @click="store.toggleCard('overview')">
      <span class="card-title">📊 命盘概要</span>
      <span class="card-toggle">{{ isCollapsed ? '▸' : '▾' }}</span>
    </button>
    <div class="card-body" v-show="!isCollapsed">

      <!-- 案例基本信息 -->
      <div v-if="store.caseData" class="case-info">
        <p class="case-name">{{ store.caseData.name }}</p>
        <p class="case-meta">
          {{ store.caseData.gender === 'male' ? '男' : '女' }}
          · {{ store.caseData.birth_dt_local?.slice(0, 10) ?? '—' }}
        </p>
      </div>
      <p v-else class="card-empty">未加载案例</p>

      <!-- 八字核心指标 -->
      <template v-if="store.baziData">
        <div class="kv-sep" />

        <!-- 五行迷你图（高度 8px，紧凑版）-->
        <div class="wxbar-wrap">
          <div class="wxbar-row">
            <div class="wxbar-seg" style="background:var(--wx-wood)"  :style="{ flex: store.baziData.wuxing_score.wood }" />
            <div class="wxbar-seg" style="background:var(--wx-fire)"  :style="{ flex: store.baziData.wuxing_score.fire }" />
            <div class="wxbar-seg" style="background:var(--wx-earth)" :style="{ flex: store.baziData.wuxing_score.earth }" />
            <div class="wxbar-seg" style="background:var(--wx-metal)" :style="{ flex: store.baziData.wuxing_score.metal }" />
            <div class="wxbar-seg" style="background:var(--wx-water)" :style="{ flex: store.baziData.wuxing_score.water }" />
          </div>
          <div class="wxbar-labels">
            <span style="color:var(--wx-wood)">木{{ store.baziData.wuxing_score.wood }}</span>
            <span style="color:var(--wx-fire)">火{{ store.baziData.wuxing_score.fire }}</span>
            <span style="color:var(--wx-earth)">土{{ store.baziData.wuxing_score.earth }}</span>
            <span style="color:var(--wx-metal)">金{{ store.baziData.wuxing_score.metal }}</span>
            <span style="color:var(--wx-water)">水{{ store.baziData.wuxing_score.water }}</span>
          </div>
        </div>

        <div class="badges-row">
          <span class="info-badge">{{ store.baziData.pillars_primary?.day?.stem }} 日主</span>
          <span v-if="store.baziData.geju" class="info-badge accent">{{ store.baziData.geju.geju_name }}</span>
          <span v-if="store.baziData.day_master_strength?.tier" class="info-badge">{{ store.baziData.day_master_strength.tier }}</span>
        </div>

        <div class="kv-row" v-if="store.baziData.yongshen?.favor?.length">
          <span class="kv-key">用神</span>
          <span class="kv-val">
            <span v-for="f in store.baziData.yongshen.favor" :key="f" class="wx-tag">{{ f }}</span>
          </span>
        </div>
      </template>
      <p v-else-if="store.caseData" class="card-empty sm">八字未计算</p>

    </div>
  </div>
</template>

<style scoped>
/* ── 卡片容器 ───────────────────────────────────────────────── */
.card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-2);
  overflow: hidden;
  transition: box-shadow var(--dur-fast);
  flex-shrink: 0;
}
.card:hover { box-shadow: var(--shadow); }

.card-header {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; padding: var(--sp-2) var(--sp-3);
  background: transparent; border: none; cursor: pointer; gap: var(--sp-2);
}
.card-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.card-toggle { font-size: 12px; color: var(--text-3); }
.card-body { padding: var(--sp-3); border-top: 1px solid var(--border); }
.card-empty { font-size: var(--fs-xs); color: var(--text-3); text-align: center; padding: var(--sp-2) 0; }
.card-empty.sm { padding: var(--sp-1) 0; }

/* ── 案例信息 ─────────────────────────────────────────────── */
.case-info { margin-bottom: var(--sp-2); }
.case-name { font-size: var(--fs-md); font-weight: 700; color: var(--text); font-family: var(--font-cn); }
.case-meta { font-size: var(--fs-xs); color: var(--text-3); margin-top: 1px; }

.kv-sep { height: 1px; background: var(--border); margin: var(--sp-2) 0; }

/* ── 五行迷你图 ──────────────────────────────────────────── */
.wxbar-wrap { margin-bottom: var(--sp-2); }
.wxbar-row { display: flex; height: 8px; border-radius: 4px; overflow: hidden; gap: 1px; }
.wxbar-seg { min-width: 4px; transition: flex .4s ease; }
.wxbar-labels { display: flex; justify-content: space-between; margin-top: 3px; font-size: 10px; font-family: var(--font-mono); }

/* ── 徽章行 ────────────────────────────────────────────── */
.badges-row { display: flex; flex-wrap: wrap; gap: 4px; margin: var(--sp-2) 0; }
.info-badge {
  font-size: 11px; padding: 2px 7px; border-radius: 99px;
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-2);
}
.info-badge.accent { background: var(--accent-lt); border-color: rgba(217,119,6,.25); color: var(--accent-dark); }

/* ── KV 行 ─────────────────────────────────────────────── */
.kv-row { display: flex; align-items: center; gap: var(--sp-2); padding: 3px 0; font-size: var(--fs-xs); border-bottom: 1px solid var(--border); }
.kv-row:last-child { border-bottom: none; }
.kv-key { width: 40px; flex-shrink: 0; color: var(--text-3); }
.kv-val { color: var(--text); flex: 1; display: flex; flex-wrap: wrap; gap: 3px; }
.wx-tag { padding: 1px 5px; border-radius: 3px; font-size: 11px; background: var(--accent-lt); color: var(--accent-dark); }
</style>
