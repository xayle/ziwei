<script setup lang="ts">
import type { CaseOut } from '@/api/report'

const props = defineProps<{
  caseDetail: CaseOut
  simpleView: boolean
  shareUrl: string | null
}>()

const emit = defineEmits<{
  toggleView: []
  syncProfile: []
  openReport: []
  reload: []
  edit: []
  share: []
  exportJson: []
  exportPdf: []
  print: []
  snapshots: []
  deleteCase: []
}>()

function fmtDate(dt: string | null): string {
  if (!dt) return '—'
  const [date, time] = dt.split('T')
  const [y, m, d] = date.split('-')
  const t = (time ?? '').slice(0, 5)
  return `${y}年${m}月${d}日  ${t}`
}

function genderLabel(g: string | null): string {
  if (g === 'female') return '女'
  if (g === 'male') return '男'
  return '—'
}
</script>

<template>
  <div class="wb-info-bar">
    <div class="wb-info-main">
      <div class="wb-info-left">
        <div class="wb-info-avatar">{{ props.caseDetail.name?.charAt(0) }}</div>
        <div>
          <div class="wb-info-title-row">
            <h1 class="wb-info-name">{{ props.caseDetail.name }}</h1>
            <span class="wb-case-badge">案例中心</span>
          </div>
          <p class="wb-info-sub">
            {{ genderLabel(props.caseDetail.gender) }} 命 ·
            {{ props.caseDetail.city ?? props.caseDetail.tz }}
          </p>
        </div>
      </div>

      <div class="wb-info-fields">
        <div class="wb-field">
          <span class="wb-field-key">阳历</span>
          <span class="wb-field-val">{{ fmtDate(props.caseDetail.birth_dt_local) }}</span>
        </div>
        <div class="wb-field">
          <span class="wb-field-key">时区</span>
          <span class="wb-field-val">{{ props.caseDetail.tz }}</span>
        </div>
        <div class="wb-field">
          <span class="wb-field-key">经度</span>
          <span class="wb-field-val">{{ props.caseDetail.lon }}° E</span>
        </div>
        <div class="wb-field">
          <span class="wb-field-key">真太阳时</span>
          <span class="wb-field-val">
            <span class="wb-bool" :class="props.caseDetail.solar_time_enabled ? 'on' : 'off'">
              {{ props.caseDetail.solar_time_enabled ? '已启用' : '未启用' }}
            </span>
          </span>
        </div>
      </div>
    </div>

    <div class="wb-info-actions">
      <button class="wb-btn-accent" @click="emit('openReport')">📋 查看完整报告</button>
      <button class="wb-btn-ghost" @click="emit('reload')">🔄 重算命盘</button>
      <button class="wb-btn-ghost" @click="emit('edit')">✏️ 编辑案例</button>
      <button class="wb-btn-ghost" :class="{ 'is-active': props.simpleView }" @click="emit('toggleView')">
        {{ props.simpleView ? '🧭 当前简洁视图' : '📚 切换完整视图' }}
      </button>

      <details class="wb-action-menu">
        <summary class="wb-btn-ghost">📤 导出与分享</summary>
        <div class="wb-menu-panel">
          <button class="wb-menu-item" @click="emit('share')">🔗 分享链接</button>
          <button class="wb-menu-item" @click="emit('exportJson')">📥 导出 JSON</button>
          <button class="wb-menu-item" @click="emit('exportPdf')">📄 导出 PDF</button>
          <button class="wb-menu-item" @click="emit('print')">🖨️ 打印</button>
        </div>
      </details>

      <details class="wb-action-menu">
        <summary class="wb-btn-ghost">⋯ 更多操作</summary>
        <div class="wb-menu-panel">
          <button class="wb-menu-item" @click="emit('syncProfile')">👤 同步个人信息</button>
          <button class="wb-menu-item" @click="emit('snapshots')">📸 查看快照</button>
          <button class="wb-menu-item wb-menu-danger" @click="emit('deleteCase')">🗑️ 删除案例</button>
        </div>
      </details>
    </div>

    <div v-if="props.shareUrl" class="wb-share-url">
      分享链接: <a :href="props.shareUrl" target="_blank">{{ props.shareUrl }}</a>
    </div>
  </div>
</template>

<style scoped>
.wb-info-bar {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 18px;
  padding: 20px 24px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.wb-info-main {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1 1 520px;
  min-width: 320px;
}

.wb-info-left { display: flex; align-items: center; gap: 14px; }

.wb-info-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.wb-info-avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-cn);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.wb-info-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}

.wb-case-badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.10);
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 600;
}

.wb-info-sub { font-size: 13px; color: var(--text-3); margin-top: 2px; }

.wb-info-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 12px;
}

.wb-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-2);
}

.wb-field-key { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.wb-field-val { font-size: 13px; color: var(--text); font-family: var(--font-mono); font-weight: 500; }
.wb-bool { font-size: 11px; padding: 2px 8px; border-radius: 99px; font-family: var(--font-ui); }
.wb-bool.on { background: #dcfce7; color: #15803d; }
.wb-bool.off { background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }

.wb-info-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-left: auto;
}

.wb-btn-ghost.is-active {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.10);
}

.wb-btn-accent {
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-fast);
  white-space: nowrap;
}
.wb-btn-accent:hover { background: var(--accent-dark); }

.wb-btn-ghost {
  padding: 8px 14px;
  background: transparent;
  border: 1px solid var(--border-md);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-2);
  cursor: pointer;
  transition: all var(--dur-fast);
  white-space: nowrap;
}

.wb-btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.wb-btn-danger { color: #dc2626; border-color: #fca5a5; }

.wb-action-menu {
  position: relative;
}

.wb-action-menu summary {
  list-style: none;
}

.wb-action-menu summary::-webkit-details-marker {
  display: none;
}

.wb-action-menu[open] summary {
  border-color: rgba(37, 99, 235, 0.45);
  background: rgba(37, 99, 235, 0.10);
}

.wb-menu-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 168px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 20;
}

.wb-menu-item {
  border: none;
  background: transparent;
  text-align: left;
  padding: 9px 10px;
  border-radius: 8px;
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
}

.wb-menu-item:hover {
  background: var(--surface-2);
  color: var(--accent-dark);
}

.wb-menu-danger {
  color: #dc2626;
}

.wb-share-url {
  width: 100%;
  font-size: 12px;
  color: var(--text-2);
}
.wb-share-url a { color: var(--accent-dark); text-decoration: underline; word-break: break-all; }

@media (max-width: 1080px) {
  .wb-info-actions {
    margin-left: 0;
  }
}

@media print {
  .wb-info-bar { border-bottom: 2px solid #000; padding: 12px 24px; }
  .wb-info-actions { display: none; }
  .wb-info-sub { display: none; }
  .wb-share-url { display: none; }
  .wb-btn-ghost, .wb-btn-accent { display: none; }
}
</style>
