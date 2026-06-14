<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  listMembers, createMember, updateMember, deleteMember,
  type MemberResponse, type MemberCreateRequest,
} from '@/api/members'

const router = useRouter()

// ─── 状态 ────────────────────────────────────────────────────
const loading   = ref(false)
const error     = ref('')
const members   = ref<MemberResponse[]>([])
const total     = ref(0)
const nextCursor= ref<number | null>(null)

// 面板
const panelMode = ref<'none' | 'create' | 'edit'>('none')
const selected  = ref<MemberResponse | null>(null)

// 表单
const form = ref<MemberCreateRequest & { id?: number }>({
  name: '', birth_date: '', gender: 'male',
  birth_time_hour: undefined, birth_time_minute: undefined,
  birth_city: '', birth_longitude: undefined,
  solar_time_enabled: false, notes: '',
})
const formError = ref('')

// ─── 数据加载 ────────────────────────────────────────────────
async function loadMembers(append = false) {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, unknown> = { limit: 20 }
    if (append && nextCursor.value) params.last_id = nextCursor.value
    const res = await listMembers(params)
    members.value = append ? [...members.value, ...res.items] : res.items
    total.value = res.total
    nextCursor.value = res.next_cursor
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '加载失败'
  } finally {
    loading.value = false
  }
}

// ─── 操作 ────────────────────────────────────────────────────
function openCreate() {
  form.value = {
    name: '', birth_date: '', gender: 'male',
    birth_time_hour: undefined, birth_time_minute: undefined,
    birth_city: '', birth_longitude: undefined,
    solar_time_enabled: false, notes: '',
  }
  formError.value = ''
  panelMode.value = 'create'
}

function openEdit(m: MemberResponse) {
  selected.value = m
  form.value = {
    id: m.id,
    name: m.name,
    birth_date: m.birth_date,
    gender: m.gender,
    birth_time_hour: m.birth_time_hour ?? undefined,
    birth_time_minute: m.birth_time_minute ?? undefined,
    birth_city: m.birth_city ?? '',
    birth_longitude: m.birth_longitude ?? undefined,
    solar_time_enabled: m.solar_time_enabled,
    notes: m.notes ?? '',
  }
  formError.value = ''
  panelMode.value = 'edit'
}

function closePanel() {
  panelMode.value = 'none'
  selected.value = null
}

async function saveMember() {
  formError.value = ''
  if (!form.value.name.trim()) { formError.value = '姓名不能为空'; return }
  if (!form.value.birth_date) { formError.value = '出生日期不能为空'; return }
  if (!['male', 'female'].includes(form.value.gender)) { formError.value = '性别必须为 male 或 female'; return }

  try {
    if (panelMode.value === 'create') {
      const created = await createMember({
        name: form.value.name.trim(),
        birth_date: form.value.birth_date,
        gender: form.value.gender,
        birth_time_hour: form.value.birth_time_hour,
        birth_time_minute: form.value.birth_time_minute,
        birth_city: form.value.birth_city || undefined,
        birth_longitude: form.value.birth_longitude,
        solar_time_enabled: form.value.solar_time_enabled,
        notes: form.value.notes || undefined,
      })
      members.value.unshift(created)
      total.value++
    } else if (panelMode.value === 'edit' && selected.value) {
      const updated = await updateMember(selected.value.id, {
        name: form.value.name.trim(),
        gender: form.value.gender,
        birth_time_hour: form.value.birth_time_hour,
        birth_time_minute: form.value.birth_time_minute,
        birth_city: form.value.birth_city || undefined,
        birth_longitude: form.value.birth_longitude,
        solar_time_enabled: form.value.solar_time_enabled,
        notes: form.value.notes || undefined,
      })
      const idx = members.value.findIndex(m => m.id === updated.id)
      if (idx >= 0) members.value[idx] = updated
    }
    closePanel()
  } catch (e: unknown) {
    formError.value = (e as Error).message ?? '保存失败'
  }
}

async function removeMember(m: MemberResponse) {
  if (!confirm(`确认删除成员「${m.name}」？删除后不可恢复。`)) return
  try {
    await deleteMember(m.id)
    members.value = members.value.filter(x => x.id !== m.id)
    total.value--
    if (selected.value?.id === m.id) closePanel()
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '删除失败'
  }
}

function goToScenarios(m: MemberResponse) {
  router.push({ path: '/scenarios', query: { member_id: m.id } })
}

function formatGender(g: string) {
  return g === 'male' ? '♂ 男' : g === 'female' ? '♀ 女' : g
}

function formatTime(m: MemberResponse) {
  if (m.birth_time) return m.birth_time
  if (m.birth_time_hour != null) {
    const h = String(m.birth_time_hour).padStart(2, '0')
    const min = String(m.birth_time_minute ?? 0).padStart(2, '0')
    return `${h}:${min}`
  }
  return '—'
}

onMounted(() => loadMembers())
</script>

<template>
  <div class="member-view">
    <!-- 页头 -->
    <div class="mv-header">
      <div class="mv-header-left">
        <h1 class="mv-title">👥 成员管理</h1>
        <span class="mv-count" v-if="total > 0">共 {{ total }} 位成员</span>
      </div>
      <button class="mv-btn mv-btn-primary" @click="openCreate">+ 新增成员</button>
    </div>

    <div v-if="error" class="mv-error">{{ error }}</div>

    <!-- 主体 -->
    <div class="mv-main">
      <!-- 表格 -->
      <div class="mv-table-wrap">
        <div v-if="loading && members.length === 0" class="mv-empty">加载中…</div>
        <div v-else-if="members.length === 0" class="mv-empty">暂无成员，点击「新增成员」开始</div>

        <table v-else class="mv-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>姓名</th>
              <th>性别</th>
              <th>出生日期</th>
              <th>出生时间</th>
              <th>出生地</th>
              <th>备注</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in members" :key="m.id">
              <td class="mv-id">{{ m.id }}</td>
              <td class="mv-name">{{ m.name }}</td>
              <td>{{ formatGender(m.gender) }}</td>
              <td>{{ m.birth_date }}</td>
              <td>{{ formatTime(m) }}</td>
              <td>{{ m.birth_city || '—' }}</td>
              <td class="mv-notes">{{ m.notes || '—' }}</td>
              <td class="mv-actions">
                <button class="mv-btn-icon" title="查看推演" @click="goToScenarios(m)">🔮</button>
                <button class="mv-btn-icon" title="编辑" @click="openEdit(m)">✏️</button>
                <button class="mv-btn-icon mv-btn-danger" title="删除" @click="removeMember(m)">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="nextCursor" class="mv-load-more">
          <button class="mv-btn" @click="loadMembers(true)" :disabled="loading">
            {{ loading ? '加载中…' : '加载更多' }}
          </button>
        </div>
      </div>

      <!-- 侧边面板：新建/编辑 -->
      <div v-if="panelMode !== 'none'" class="mv-panel">
        <div class="mv-panel-header">
          <span>{{ panelMode === 'create' ? '新增成员' : '编辑成员' }}</span>
          <button class="mv-close-btn" @click="closePanel">✕</button>
        </div>
        <div class="mv-form">
          <label class="mv-label">姓名 <span class="mv-req">*</span></label>
          <input class="mv-input" v-model="form.name" placeholder="成员姓名" />

          <template v-if="panelMode === 'create'">
            <label class="mv-label">出生日期 <span class="mv-req">*</span></label>
            <input class="mv-input" type="date" v-model="form.birth_date" />
          </template>
          <div v-else class="mv-info-row">
            <span class="mv-info-key">出生日期</span>
            <span class="mv-info-val">{{ selected?.birth_date }}（创建后不可修改）</span>
          </div>

          <label class="mv-label">性别 <span class="mv-req">*</span></label>
          <select class="mv-input" v-model="form.gender">
            <option value="male">♂ 男</option>
            <option value="female">♀ 女</option>
          </select>

          <label class="mv-label">出生时辰（时）</label>
          <input class="mv-input" type="number" min="0" max="23" v-model.number="form.birth_time_hour" placeholder="如 8（8点）" />

          <label class="mv-label">出生时辰（分）</label>
          <input class="mv-input" type="number" min="0" max="59" v-model.number="form.birth_time_minute" placeholder="如 30" />

          <label class="mv-label">出生城市</label>
          <input class="mv-input" v-model="form.birth_city" placeholder="如 北京" />

          <label class="mv-label">出生经度</label>
          <input class="mv-input" type="number" step="0.01" v-model.number="form.birth_longitude" placeholder="如 116.4" />

          <label class="mv-label mv-checkbox-label">
            <input type="checkbox" v-model="form.solar_time_enabled" />
            启用真太阳时校正
          </label>

          <label class="mv-label">备注</label>
          <textarea class="mv-textarea" v-model="form.notes" placeholder="可填写咨询背景、特殊说明…" rows="3" />

          <div v-if="formError" class="mv-form-error">{{ formError }}</div>
          <div class="mv-form-actions">
            <button class="mv-btn" @click="closePanel">取消</button>
            <button class="mv-btn mv-btn-primary" @click="saveMember">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style src="./MemberView.css" scoped />
