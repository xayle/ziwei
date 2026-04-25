<script setup lang="ts">
/**
 * ChapterPersonal.vue — ① 个人信息章节
 * 数据来源: CaseOut（无 API 调用）
 */
import { computed } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const c = computed(() => store.caseData)

const genderLabel = computed(() => {
  if (!c.value?.gender) return '未知'
  return c.value.gender === 'female' ? '女' : '男'
})

const birthFormatted = computed(() => {
  if (!c.value?.birth_dt_local) return ''
  const [datePart, timePart] = c.value.birth_dt_local.split('T')
  const [y, m, d] = datePart.split('-')
  const [h, mi] = (timePart ?? '00:00').split(':')
  return `${y}年${m}月${d}日 ${h}:${mi}`
})

// 农历（简单推算 - 仅用于展示，精确农历由后端提供）
const lonFormatted = computed(() => {
  if (!c.value) return ''
  return `东经 ${c.value.lon.toFixed(2)}°`
})
</script>

<template>
  <div class="chapter-personal" v-if="c">

    <!-- ═══ 1-1 基本档案 ═══ -->
    <section id="section-1-1" class="section-block">
      <div class="section-title-row">
        <span class="section-num">1-1</span>
        <h2 class="section-title">基本档案</h2>
      </div>

      <!-- 结论段落 -->
      <div class="conclusion-block">
        <p class="conclusion-text">
          <strong>{{ c.name }}</strong>，{{ genderLabel }}命。
          出生于 {{ birthFormatted }}，{{ c.city ? `籍贯 ${c.city}` : '' }}。
          <span v-if="c.tags?.length" class="tags-inline">
            <span v-for="tag in c.tags" :key="tag" class="badge">{{ tag }}</span>
          </span>
        </p>
      </div>

      <!-- 数据区: 两列信息卡 -->
      <div class="info-grid">
        <!-- 左列 -->
        <div class="info-col">
          <div class="info-row">
            <span class="info-label">姓名</span>
            <span class="info-value name-val">{{ c.name }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">性别</span>
            <span class="info-value">
              <span class="gender-badge" :class="c.gender">{{ genderLabel }}</span>
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">城市</span>
            <span class="info-value">{{ c.city ?? '未填写' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">出生时间</span>
            <span class="info-value mono">{{ birthFormatted }}</span>
          </div>
        </div>
        <!-- 右列 -->
        <div class="info-col">
          <div class="info-row">
            <span class="info-label">时区</span>
            <span class="info-value mono">{{ c.tz }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">经度</span>
            <span class="info-value mono">{{ lonFormatted }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">真太阳时</span>
            <span class="info-value">
              <span class="bool-badge" :class="{ on: c.solar_time_enabled }">
                {{ c.solar_time_enabled ? '已启用' : '未启用' }}
              </span>
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">标签</span>
            <span class="info-value">
              <span v-if="c.tags?.length">
                <span v-for="tag in c.tags" :key="tag" class="badge">{{ tag }}</span>
              </span>
              <span v-else class="muted">无</span>
            </span>
          </div>
        </div>
      </div>

      <!-- 备注（若有） -->
      <div v-if="c.notes" class="notes-block">
        <p class="notes-label">备注</p>
        <blockquote class="notes-text">{{ c.notes }}</blockquote>
      </div>
    </section>

    <!-- ═══ 1-2 出生参数 ═══ -->
    <section id="section-1-2" class="section-block">
      <div class="section-title-row">
        <span class="section-num">1-2</span>
        <h2 class="section-title">出生参数</h2>
      </div>

      <!-- 结论段落 -->
      <div class="conclusion-block">
        <p class="conclusion-text">
          出生于 <strong>{{ birthFormatted }}</strong>，位于 <strong>{{ lonFormatted }}</strong>，
          采用 <strong>{{ c.tz }}</strong> 时区进行排盘。
          <span v-if="c.solar_time_enabled">已启用真太阳时校正，实际分析使用经度修正后的时间。</span>
          <span v-else>未启用真太阳时，使用标准时区时间。</span>
        </p>
      </div>

      <!-- 参数对照表 -->
      <div class="param-table-wrap">
        <table class="param-table">
          <tbody>
            <tr>
              <td class="pt-key">本地出生时间</td>
              <td class="pt-val mono">{{ c.birth_dt_local }}</td>
            </tr>
            <tr>
              <td class="pt-key">时区</td>
              <td class="pt-val mono">{{ c.tz }}</td>
            </tr>
            <tr>
              <td class="pt-key">出生经度</td>
              <td class="pt-val mono">{{ c.lon }}</td>
            </tr>
            <tr>
              <td class="pt-key">真太阳时</td>
              <td class="pt-val">
                <span class="bool-badge" :class="{ on: c.solar_time_enabled }">
                  {{ c.solar_time_enabled ? '已启用' : '未启用' }}
                </span>
              </td>
            </tr>
            <tr v-if="c.birth_dt">
              <td class="pt-key">UTC时间</td>
              <td class="pt-val mono">{{ c.birth_dt }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 真太阳时说明 -->
      <div v-if="c.solar_time_enabled" class="tip-block tip-green">
        <strong>真太阳时已启用：</strong>根据出生地经度（{{ c.lon }}°）与标准子午线的差值，
        对时间进行修正。每偏东/西 15° 约修正 1 小时，精确到分钟。
      </div>
      <div v-else class="tip-block tip-gray">
        <strong>提示：</strong>如需更精确的排盘，可在案例编辑中启用真太阳时，
        系统将根据出生地经度自动校正时间。
      </div>
    </section>

  </div>
</template>

<style scoped>
.chapter-personal {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
}

/* ─── 章节块 ─────────────────────────────────────────── */
.section-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-6);
  scroll-margin-top: 64px;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}

.section-num {
  font-size: var(--fs-xs);
  color: var(--text-3);
  font-family: var(--font-mono);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: 99px;
  border: 1px solid var(--border);
}

.section-title {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}

/* ─── 结论块 ─────────────────────────────────────────── */
.conclusion-block {
  padding: var(--sp-4);
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
  margin-bottom: var(--sp-5);
}

.conclusion-text {
  font-size: var(--fs-md);
  color: var(--text);
  line-height: 1.8;
  font-family: var(--font-cn);
}

.tags-inline { display: inline-flex; gap: 4px; flex-wrap: wrap; vertical-align: middle; }

/* ─── 信息网格 ────────────────────────────────────────── */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.info-col {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.info-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border);
}
.info-row:last-child { border-bottom: none; }

.info-label {
  width: 70px;
  flex-shrink: 0;
  font-size: var(--fs-xs);
  color: var(--text-3);
}

.info-value {
  flex: 1;
  font-size: var(--fs-sm);
  color: var(--text);
}

.info-value.mono { font-family: var(--font-mono); }
.info-value.name-val { font-size: var(--fs-md); font-family: var(--font-cn); font-weight: 600; }

/* ─── 徽章 ──────────────────────────────────────────── */
.badge {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 99px;
  background: var(--accent-lt);
  color: var(--accent-dark);
  border: 1px solid rgba(217,119,6,.2);
}

.gender-badge.male { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
.gender-badge.female { background: #fce7f3; color: #9d174d; border: 1px solid #fbcfe8; }

.bool-badge {
  font-size: var(--fs-xs);
  padding: 2px 8px;
  border-radius: 99px;
  background: var(--bg);
  color: var(--text-3);
  border: 1px solid var(--border);
}
.bool-badge.on {
  background: #dcfce7;
  color: #15803d;
  border-color: #86efac;
}

.muted { color: var(--text-3); font-size: var(--fs-xs); }

/* ─── 备注块 ─────────────────────────────────────────── */
.notes-block { margin-top: var(--sp-4); }
.notes-label { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: var(--sp-2); }
.notes-text {
  background: var(--surface-2);
  border-left: 3px solid var(--border-md);
  padding: var(--sp-3) var(--sp-4);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: var(--fs-sm);
  color: var(--text-2);
  font-family: var(--font-cn);
  line-height: 1.8;
}

/* ─── 参数对照表 ─────────────────────────────────────── */
.param-table-wrap { margin-bottom: var(--sp-4); }
.param-table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
.param-table tr { border-bottom: 1px solid var(--border); }
.param-table tr:last-child { border-bottom: none; }
.pt-key { padding: var(--sp-2) var(--sp-3); color: var(--text-3); width: 140px; }
.pt-val { padding: var(--sp-2) var(--sp-3); color: var(--text); }
.pt-val.mono { font-family: var(--font-mono); }

/* ─── 提示块 ─────────────────────────────────────────── */
.tip-block {
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  line-height: 1.7;
}
.tip-green { background: #f0fdf4; color: #15803d; border: 1px solid #86efac; }
.tip-gray { background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }
</style>
