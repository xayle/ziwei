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
    <div class="wb-info-left">
      <div class="wb-info-avatar">{{ props.caseDetail.name?.charAt(0) }}</div>
      <div>
        <h1 class="wb-info-name">{{ props.caseDetail.name }}</h1>
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
    <div class="wb-info-actions">
      <button class="wb-btn-ghost" :class="{ 'is-active': props.simpleView }" @click="emit('toggleView')">
        {{ props.simpleView ? '🧭 简洁视图' : '📚 完整视图' }}
      </button>
      <button class="wb-btn-ghost" @click="emit('syncProfile')">👤 同步个人信息</button>
      <button class="wb-btn-accent" @click="emit('openReport')">📋 完整报告书</button>
      <button class="wb-btn-ghost" @click="emit('reload')">🔄 重算</button>
      <button class="wb-btn-ghost" @click="emit('edit')">✏️ 编辑</button>
      <button class="wb-btn-ghost" @click="emit('share')">🔗 分享</button>
      <button class="wb-btn-ghost" @click="emit('exportJson')">📥 JSON</button>
      <button class="wb-btn-ghost" @click="emit('exportPdf')">📄 PDF</button>
      <button class="wb-btn-ghost" @click="emit('print')">🖨️ 打印</button>
      <button class="wb-btn-ghost" @click="emit('snapshots')">📸 快照</button>
      <button class="wb-btn-ghost wb-btn-danger" @click="emit('deleteCase')">🗑️ 删除</button>
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
  gap: 16px;
  padding: 20px 24px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.wb-info-left { display: flex; align-items: center; gap: 14px; }

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

.wb-info-sub { font-size: 13px; color: var(--text-3); margin-top: 2px; }
.wb-info-fields { display: flex; gap: 16px; flex-wrap: wrap; align-items: center; flex: 1; }
.wb-field { display: flex; flex-direction: column; gap: 2px; }
.wb-field-key { font-size: 10px; color: var(--text-3); text-transform: uppercase; letter-spacing: .04em; }
.wb-field-val { font-size: 13px; color: var(--text); font-family: var(--font-mono); font-weight: 500; }
.wb-bool { font-size: 11px; padding: 2px 8px; border-radius: 99px; font-family: var(--font-ui); }
.wb-bool.on { background: #dcfce7; color: #15803d; }
.wb-bool.off { background: var(--surface-2); color: var(--text-3); border: 1px solid var(--border); }
.wb-info-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
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
.wb-share-url {
  width: 100%;
  font-size: 12px;
  color: var(--text-2);
}
.wb-share-url a { color: var(--accent-dark); text-decoration: underline; word-break: break-all; }

@media print {
  .wb-info-bar { border-bottom: 2px solid #000; padding: 12px 24px; }
  .wb-info-actions { display: none; }
  .wb-info-sub { display: none; }
  .wb-share-url { display: none; }
  .wb-btn-ghost, .wb-btn-accent { display: none; }
}
</style>
