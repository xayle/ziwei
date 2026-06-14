<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  listScenarios, createScenario, updateScenario, deleteScenario, simulateScenario,
  type ScenarioResponse, type SimulateResponse,
} from '@/api/scenarios'
import { listMembers, createMember, type MemberResponse } from '@/api/members'
import { useProfileStore } from '@/stores/profile'

// ─── 状态 ────────────────────────────────────────────────────
const route   = useRoute()
const profile = useProfileStore()
const loading   = ref(false)
const error     = ref('')
const scenarios = ref<ScenarioResponse[]>([])
const total     = ref(0)
const nextCursor= ref<number | null>(null)

// 筛选
const filterType= ref('')
const TYPES    = ['命局推演', '大运推演', '流年推演', '合盘推演', '自定义']
const RELATIONS = ['配偶/伴侣', '子女', '父母', '兄弟姐妹', '朋友', '同事', '其他']

// 当前用户的成员列表（用于自动填充 base_member_id）
const myMembers = ref<MemberResponse[]>([])

async function loadMyMembers() {
  try {
    const res = await listMembers({ limit: 50 })
    myMembers.value = res.items
  } catch {
    // 加载失败时静默处理，不影响页面主功能
  }
}

// 分析对象选择（创建模式用）
const selectedMemberKey = ref('')          // member id 字符串 或 'new'
const newMemberRelation = ref('')          // 与我的关系 → member.notes
const showNewMemberForm = computed(() => selectedMemberKey.value === 'new')

// 详情/编辑面板
const panelMode = ref<'none' | 'detail' | 'create' | 'edit'>('none')
const selected  = ref<ScenarioResponse | null>(null)

// 表单
const form = ref({
  base_member_id: 0,
  name: '',
  description: '',
  scenario_type: '命局推演',
  variations: '',
  results: '',
})
// ── 参数子表单（拆开的友好字段，保存时组装为 variations JSON）──────────
type PersonSub = { person_name: string; birth_date: string; birth_time: string; city: string; gender: string }
const emptyPerson = (): PersonSub => ({ person_name: '', birth_date: '', birth_time: '', city: '', gender: 'male' })
const sub  = ref<PersonSub>(emptyPerson())                            // 单人 / 合盘甲方
const subB = ref<PersonSub>({ ...emptyPerson(), gender: 'female' })  // 合盘乙方
// 是否合盘（多人）模式
const isMultiMode = computed(() => form.value.scenario_type === '合盘推演')
const formError = ref('')

// What-If 模拟
const simLoading = ref(false)
const simResult  = ref<SimulateResponse | null>(null)
const simOverride = ref({ birth_dt: '', longitude: '', gender: '', note: '' })

// ─── 计算 ────────────────────────────────────────────────────
const filteredScenarios = computed(() =>
  filterType.value
    ? scenarios.value.filter(s => s.scenario_type === filterType.value)
    : scenarios.value
)

// ─── 数据加载 ────────────────────────────────────────────────
async function loadScenarios(append = false) {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, unknown> = { limit: 20 }
    if (filterType.value) params.scenario_type = filterType.value
    if (append && nextCursor.value) params.last_id = nextCursor.value
    const res = await listScenarios(params)
    scenarios.value = append ? [...scenarios.value, ...res.items] : res.items
    total.value = res.total
    nextCursor.value = res.next_cursor
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '加载失败'
  } finally {
    loading.value = false
  }
}

// ─── 操作 ────────────────────────────────────────────────────
function openCreate(memberId?: number) {
  const autoMemberId = memberId ?? myMembers.value[0]?.id ?? 0

  // 设置分析对象选择器初始值，并同步 sub
  if (autoMemberId && myMembers.value.some(m => m.id === autoMemberId)) {
    selectedMemberKey.value = String(autoMemberId)
    const m = myMembers.value.find(m => m.id === autoMemberId)!
    sub.value = {
      person_name: m.name,
      birth_date:  m.birth_date,
      birth_time:  m.birth_time ?? '',
      city:        m.birth_city ?? '',
      gender:      m.gender,
    }
  } else {
    // 没有成员 → 新建模式，用首页数据预填
    selectedMemberKey.value = 'new'
    const [datePart = '', timePart = ''] = (profile.birthDt ?? '').split('T')
    sub.value = {
      person_name: profile.surname ?? '',
      birth_date:  datePart,
      birth_time:  timePart.slice(0, 5),
      city:        profile.cityName ?? '',
      gender:      profile.gender ?? 'male',
    }
  }
  newMemberRelation.value = ''
  subB.value = { ...emptyPerson(), gender: 'female' }

  form.value = {
    base_member_id: autoMemberId,
    name:           profile.surname ? `${profile.surname}-命局推演` : '',
    description:    '',
    scenario_type:  filterType.value || '命局推演',
    variations:     '',
    results:        '',
  }
  formError.value = ''
  simResult.value = null
  panelMode.value = 'create'
}

/** 用户切换「分析对象」下拉时触发 */
function onMemberChange() {
  const key = selectedMemberKey.value
  if (key === 'new') {
    sub.value = emptyPerson()
    newMemberRelation.value = ''
    form.value.base_member_id = 0
  } else {
    const m = myMembers.value.find(m => String(m.id) === key)
    if (m) {
      form.value.base_member_id = m.id
      sub.value = {
        person_name: m.name,
        birth_date:  m.birth_date,
        birth_time:  m.birth_time ?? '',
        city:        m.birth_city ?? '',
        gender:      m.gender,
      }
    }
  }
}

function openEdit(sc: ScenarioResponse) {
  selected.value = sc
  form.value = {
    base_member_id: sc.base_member_id,
    name:           sc.name,
    description:    sc.description ?? '',
    scenario_type:  sc.scenario_type,
    variations:     sc.variations ?? '',
    results:        sc.results ?? '',
  }
  // 从已有 variations 反解子表单
  try {
    const v = sc.variations ? JSON.parse(sc.variations) : {}
    if (v.mode === 'multi') {
      sub.value  = personFromObj(v.party_a ?? {})
      subB.value = personFromObj({ gender: 'female', ...(v.party_b ?? {}) })
    } else {
      sub.value  = personFromObj(v)
      subB.value = { ...emptyPerson(), gender: 'female' }
    }
  } catch {
    sub.value  = emptyPerson()
    subB.value = { ...emptyPerson(), gender: 'female' }
  }
  formError.value = ''
  simResult.value = null
  panelMode.value = 'edit'
}

function openDetail(sc: ScenarioResponse) {
  selected.value = sc
  simResult.value = null
  simOverride.value = { birth_dt: '', longitude: '', gender: '', note: '' }
  panelMode.value = 'detail'
}

function closePanel() {
  panelMode.value = 'none'
  selected.value = null
  simResult.value = null
}

/** PersonSub → JSON 对象（birth_date 拆成 year/month/day，birth_time 拆成 hour/minute） */
function buildPersonObj(s: PersonSub): Record<string, unknown> {
  const obj: Record<string, unknown> = {}
  if (s.person_name) obj.person_name = s.person_name
  if (s.birth_date) {
    const [y, mo, d] = s.birth_date.split('-').map(Number)
    if (!isNaN(y))  obj.birth_year  = y
    if (!isNaN(mo)) obj.birth_month = mo
    if (!isNaN(d))  obj.birth_day   = d
  }
  if (s.birth_time) {
    const [hh, mm] = s.birth_time.split(':').map(Number)
    if (!isNaN(hh)) obj.birth_hour   = hh
    if (!isNaN(mm)) obj.birth_minute = mm
  }
  if (s.city)   obj.city   = s.city
  if (s.gender) obj.gender = s.gender
  return obj
}

/** JSON 对象 → PersonSub */
function personFromObj(v: Record<string, unknown>): PersonSub {
  const pad = (n: unknown): string => String(n ?? '').padStart(2, '0')
  const y  = v.birth_year
  const mo = v.birth_month
  const d  = v.birth_day
  const hh = v.birth_hour
  const mm = v.birth_minute
  const birth_date = (y && mo && d)
    ? `${y}-${pad(mo)}-${pad(d)}`
    : String(v.birth_date ?? '')
  const birth_time = (hh != null)
    ? `${pad(hh)}:${pad(mm ?? 0)}`
    : String(v.birth_time ?? '')
  return {
    person_name: String(v.person_name ?? ''),
    birth_date,
    birth_time,
    city:   String(v.city   ?? ''),
    gender: String(v.gender ?? 'male'),
  }
}

/** 卡片副标题：单人显示姓名，合盘显示"甲 × 乙" */
function getScenarioSubtitle(sc: ScenarioResponse): string {
  if (!sc.variations) return ''
  try {
    const v = JSON.parse(sc.variations) as Record<string, any>
    if (v.mode === 'multi') {
      const a = String(v.party_a?.person_name || '甲')
      const b = String(v.party_b?.person_name || '乙')
      return `${a} × ${b}`
    }
    return String(v.person_name || '')
  } catch {
    return ''
  }
}

/** 将子表单字段组装为 variations JSON 字符串 */
function buildVariations(): string | undefined {
  if (isMultiMode.value) {
    const a = buildPersonObj(sub.value)
    const b = buildPersonObj(subB.value)
    if (!Object.keys(a).length && !Object.keys(b).length) return undefined
    return JSON.stringify({ mode: 'multi', party_a: a, party_b: b })
  }
  const obj = buildPersonObj(sub.value)
  const gender = sub.value.gender || profile.gender
  if (gender)            obj.gender    = gender
  if (profile.lon != null) obj.longitude = profile.lon
  return Object.keys(obj).length ? JSON.stringify(obj) : undefined
}

async function saveScenario() {
  formError.value = ''
  if (!form.value.name.trim()) { formError.value = '名称不能为空'; return }
  try {
    // 若选择了「新建人员」，先创建成员记录
    if (panelMode.value === 'create' && showNewMemberForm.value) {
      if (!sub.value.person_name.trim()) { formError.value = '请填写甲方姓名'; return }
      if (!sub.value.birth_date)         { formError.value = '请填写甲方出生日期'; return }
      const [hh, mm] = sub.value.birth_time
        ? sub.value.birth_time.split(':').map(Number)
        : [NaN, NaN]
      const newM = await createMember({
        name:              sub.value.person_name.trim(),
        birth_date:        sub.value.birth_date,
        gender:            sub.value.gender || 'male',
        birth_time:        sub.value.birth_time || undefined,
        birth_time_hour:   isNaN(hh) ? undefined : hh,
        birth_time_minute: isNaN(mm) ? undefined : mm,
        birth_city:        sub.value.city || undefined,
        notes:             newMemberRelation.value || undefined,
      })
      myMembers.value.push(newM)
      form.value.base_member_id = newM.id
      selectedMemberKey.value   = String(newM.id)
    }
    if (!form.value.base_member_id) { formError.value = '请选择或新建分析对象'; return }
    if (panelMode.value === 'create') {
      const created = await createScenario({
        ...form.value,
        variations: buildVariations(),
        results:    form.value.results || undefined,
      })
      scenarios.value.unshift(created)
      total.value++
    } else if (panelMode.value === 'edit' && selected.value) {
      const updated = await updateScenario(selected.value.id, {
        name:          form.value.name,
        description:   form.value.description,
        scenario_type: form.value.scenario_type,
        variations:    buildVariations(),
        results:       form.value.results || undefined,
      })
      const idx = scenarios.value.findIndex(s => s.id === updated.id)
      if (idx >= 0) scenarios.value[idx] = updated
    }
    closePanel()
  } catch (e: unknown) {
    formError.value = (e as Error).message ?? '保存失败'
  }
}

async function removeScenario(sc: ScenarioResponse) {
  if (!confirm(`确认删除情景「${sc.name}」？`)) return
  try {
    await deleteScenario(sc.id)
    scenarios.value = scenarios.value.filter(s => s.id !== sc.id)
    total.value--
    if (selected.value?.id === sc.id) closePanel()
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '删除失败'
  }
}

async function runSimulate(sc: ScenarioResponse) {
  simLoading.value = true
  simResult.value = null
  try {
    const req: Record<string, unknown> = {}
    if (simOverride.value.birth_dt.trim())  req.birth_dt_override  = simOverride.value.birth_dt.trim()
    if (simOverride.value.longitude.trim()) req.longitude_override = Number(simOverride.value.longitude)
    if (simOverride.value.gender.trim())    req.gender_override    = simOverride.value.gender.trim()
    if (simOverride.value.note.trim())      req.note               = simOverride.value.note.trim()
    simResult.value = await simulateScenario(sc.id, req)
  } catch (e: unknown) {
    error.value = (e as Error).message ?? '模拟失败'
  } finally {
    simLoading.value = false
  }
}

function formatDate(iso: string) {
  return iso ? new Date(iso).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''
}

// ─── 生命周期 ────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadScenarios(), loadMyMembers()])
  const mid = route.query.member_id
  if (mid) {
    openCreate(Number(mid))
  }
})
</script>

<template>
  <div class="scenario-view">
    <!-- 页头 -->
    <div class="sv-header">
      <div class="sv-header-left">
        <h1 class="sv-title">🔮 情景推演</h1>
        <span class="sv-count" v-if="total > 0">共 {{ total }} 条</span>
      </div>
      <div class="sv-header-right">
        <!-- 类型筛选 -->
        <select class="sv-select" v-model="filterType" @change="loadScenarios()">
          <option value="">全部类型</option>
          <option v-for="t in TYPES" :key="t" :value="t">{{ t }}</option>
        </select>
        <button class="sv-btn sv-btn-primary" @click="openCreate()">+ 新建推演</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="sv-error">{{ error }}</div>

    <!-- 主体：列表 + 侧边面板 -->
    <div class="sv-main">
      <!-- 列表 -->
      <div class="sv-list" :class="{ 'sv-list-narrow': panelMode !== 'none' }">
        <div v-if="loading && scenarios.length === 0" class="sv-empty">加载中…</div>
        <div v-else-if="filteredScenarios.length === 0" class="sv-empty">暂无情景推演，点击「新建推演」开始</div>

        <div
          v-for="sc in filteredScenarios"
          :key="sc.id"
          class="sv-card"
          :class="{ 'sv-card-active': selected?.id === sc.id }"
          @click="openDetail(sc)"
        >
          <div class="sv-card-top">
            <span class="sv-card-name">{{ sc.name }}</span>
            <span class="sv-type-badge">{{ sc.scenario_type }}</span>
          </div>
          <div class="sv-card-subtitle" v-if="getScenarioSubtitle(sc)">{{ getScenarioSubtitle(sc) }}</div>
          <div class="sv-card-desc" v-if="sc.description">{{ sc.description }}</div>
          <div class="sv-card-meta">
            <span>{{ formatDate(sc.updated_at) }}</span>
          </div>
          <div class="sv-card-actions" @click.stop>
            <button class="sv-btn-icon" title="编辑" @click="openEdit(sc)">✏️</button>
            <button class="sv-btn-icon sv-btn-danger" title="删除" @click="removeScenario(sc)">🗑</button>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="nextCursor" class="sv-load-more">
          <button class="sv-btn" @click="loadScenarios(true)" :disabled="loading">
            {{ loading ? '加载中…' : '加载更多' }}
          </button>
        </div>
      </div>

      <!-- 侧边面板 -->
      <div v-if="panelMode !== 'none'" class="sv-panel" :class="{ 'sv-panel-wide': isMultiMode && panelMode !== 'detail' }">
        <!-- 新建/编辑表单 -->
        <template v-if="panelMode === 'create' || panelMode === 'edit'">
          <div class="sv-panel-header">
            <span>{{ panelMode === 'create' ? '新建情景推演' : '编辑情景推演' }}</span>
            <button class="sv-close-btn" @click="closePanel">✕</button>
          </div>
          <div class="sv-form">
            <label class="sv-label">名称 <span class="sv-req">*</span></label>
            <input class="sv-input" v-model="form.name" placeholder="输入推演名称" />

            <label class="sv-label">推演类型</label>
            <div class="sv-type-tabs">
              <button
                v-for="t in TYPES" :key="t"
                class="sv-type-tab"
                :class="{ 'sv-type-tab-active': form.scenario_type === t }"
                @click="form.scenario_type = t"
              >{{ t }}</button>
            </div>

            <label class="sv-label">描述</label>
            <textarea class="sv-textarea" v-model="form.description" placeholder="简要描述此推演的目的或背景…" rows="2" />

            <!-- ── 单人模式 ──────────────────────────────── -->
            <template v-if="!isMultiMode">
              <!-- 分析对象选择（仅创建） -->
              <template v-if="panelMode === 'create'">
                <label class="sv-label">分析对象</label>
                <select class="sv-select sv-full" v-model="selectedMemberKey" @change="onMemberChange">
                  <option v-for="m in myMembers" :key="m.id" :value="String(m.id)">{{ m.name }}（{{ m.birth_date }}）</option>
                  <option value="new">＋ 新建人员…</option>
                </select>
              </template>

              <label class="sv-label">姓名</label>
              <input class="sv-input" v-model="sub.person_name" placeholder="当事人姓名" />

              <label class="sv-label">性别</label>
              <select class="sv-select sv-full" v-model="sub.gender">
                <option value="male">男</option>
                <option value="female">女</option>
              </select>

              <label class="sv-label">出生日期</label>
              <input class="sv-input" type="date" v-model="sub.birth_date" />

              <label class="sv-label">出生时间</label>
              <input class="sv-input" type="time" v-model="sub.birth_time" />

              <label class="sv-label">出生地</label>
              <input class="sv-input" v-model="sub.city" placeholder="如 安徽省 池州" />

              <template v-if="panelMode === 'create' && showNewMemberForm">
                <label class="sv-label">与我的关系</label>
                <select class="sv-select sv-full" v-model="newMemberRelation">
                  <option value="">请选择…</option>
                  <option v-for="r in RELATIONS" :key="r" :value="r">{{ r }}</option>
                </select>
              </template>
            </template>

            <!-- ── 合盘模式（甲方 / 乙方）─────────────────── -->
            <template v-else>
              <div class="sv-parties-grid">
                <!-- 甲方 -->
                <div class="sv-party sv-party-a">
                  <div class="sv-party-header">甲方</div>
                  <template v-if="panelMode === 'create'">
                    <label class="sv-label">选择成员</label>
                    <select class="sv-select sv-full" v-model="selectedMemberKey" @change="onMemberChange">
                      <option v-for="m in myMembers" :key="m.id" :value="String(m.id)">{{ m.name }}</option>
                      <option value="new">＋ 新建…</option>
                    </select>
                  </template>
                  <label class="sv-label">姓名</label>
                  <input class="sv-input" v-model="sub.person_name" placeholder="甲方姓名" />
                  <label class="sv-label">性别</label>
                  <select class="sv-select sv-full" v-model="sub.gender">
                    <option value="male">男</option>
                    <option value="female">女</option>
                  </select>
                  <label class="sv-label">出生日期</label>
                  <input class="sv-input" type="date" v-model="sub.birth_date" />
                  <label class="sv-label">出生时间</label>
                  <input class="sv-input" type="time" v-model="sub.birth_time" />
                  <label class="sv-label">出生地</label>
                  <input class="sv-input" v-model="sub.city" placeholder="如 北京" />
                </div>

                <!-- 乙方 -->
                <div class="sv-party sv-party-b">
                  <div class="sv-party-header">乙方</div>
                  <label class="sv-label">姓名</label>
                  <input class="sv-input" v-model="subB.person_name" placeholder="乙方姓名" />
                  <label class="sv-label">性别</label>
                  <select class="sv-select sv-full" v-model="subB.gender">
                    <option value="male">男</option>
                    <option value="female">女</option>
                  </select>
                  <label class="sv-label">出生日期</label>
                  <input class="sv-input" type="date" v-model="subB.birth_date" />
                  <label class="sv-label">出生时间</label>
                  <input class="sv-input" type="time" v-model="subB.birth_time" />
                  <label class="sv-label">出生地</label>
                  <input class="sv-input" v-model="subB.city" placeholder="如 上海" />
                </div>
              </div>
            </template>

            <div v-if="formError" class="sv-form-error">{{ formError }}</div>
            <div class="sv-form-actions">
              <button class="sv-btn" @click="closePanel">取消</button>
              <button class="sv-btn sv-btn-primary" @click="saveScenario">保存</button>
            </div>
          </div>
        </template>

        <!-- 详情 + What-If 模拟 -->
        <template v-else-if="panelMode === 'detail' && selected">
          <div class="sv-panel-header">
            <span>{{ selected.name }}</span>
            <button class="sv-close-btn" @click="closePanel">✕</button>
          </div>
          <div class="sv-detail">
            <div class="sv-detail-row">
              <span class="sv-detail-key">类型</span>
              <span class="sv-type-badge">{{ selected.scenario_type }}</span>
            </div>
            <div class="sv-detail-row" v-if="selected.description">
              <span class="sv-detail-key">描述</span>
              <span>{{ selected.description }}</span>
            </div>
            <div class="sv-detail-row">
              <span class="sv-detail-key">创建时间</span>
              <span>{{ formatDate(selected.created_at) }}</span>
            </div>
            <div class="sv-detail-row">
              <span class="sv-detail-key">更新时间</span>
              <span>{{ formatDate(selected.updated_at) }}</span>
            </div>
            <div class="sv-detail-row sv-detail-col" v-if="selected.variations">
              <span class="sv-detail-key">参数变体</span>
              <pre class="sv-pre">{{ selected.variations }}</pre>
            </div>
            <div class="sv-detail-row sv-detail-col" v-if="selected.results">
              <span class="sv-detail-key">历史结果</span>
              <pre class="sv-pre">{{ selected.results }}</pre>
            </div>
          </div>

          <!-- What-If 模拟区 -->
          <div class="sv-simulate-section">
            <div class="sv-sim-title">⚡ What-If 模拟</div>
            <div class="sv-sim-desc">覆盖参数后重新演算，结果自动写入情景记录</div>
            <div class="sv-form">
              <label class="sv-label">生辰覆盖 (ISO, 可留空)</label>
              <input class="sv-input" v-model="simOverride.birth_dt" placeholder="如 1990-07-17T08:30:00" />
              <label class="sv-label">经度覆盖 (可留空)</label>
              <input class="sv-input" v-model="simOverride.longitude" placeholder="如 116.4" />
              <label class="sv-label">性别覆盖 (male/female, 可留空)</label>
              <input class="sv-input" v-model="simOverride.gender" placeholder="male / female" />
              <label class="sv-label">备注</label>
              <input class="sv-input" v-model="simOverride.note" placeholder="本次模拟的说明…" />
              <button class="sv-btn sv-btn-primary sv-sim-btn" @click="runSimulate(selected)" :disabled="simLoading">
                {{ simLoading ? '模拟中…' : '运行 What-If 模拟' }}
              </button>
            </div>

            <!-- 模拟结果 -->
            <div v-if="simResult" class="sv-sim-result">
              <div class="sv-sim-result-title">模拟结果</div>
              <div class="sv-sim-row"><span class="sv-sim-key">格局</span><span>{{ simResult.geju_name }}</span></div>
              <div class="sv-sim-row">
                <span class="sv-sim-key">喜用神</span>
                <span class="sv-tags">
                  <span v-for="f in simResult.yongshen_favor" :key="f" class="sv-tag sv-tag-favor">{{ f }}</span>
                </span>
              </div>
              <div class="sv-sim-row">
                <span class="sv-sim-key">忌神</span>
                <span class="sv-tags">
                  <span v-for="a in simResult.yongshen_avoid" :key="a" class="sv-tag sv-tag-avoid">{{ a }}</span>
                </span>
              </div>
              <div class="sv-sim-row">
                <span class="sv-sim-key">五行</span>
                <span class="sv-tags">
                  <span v-for="(v, k) in simResult.wuxing_scores" :key="k" class="sv-tag">{{ k }}: {{ v.toFixed(2) }}</span>
                </span>
              </div>
              <div class="sv-sim-row" v-if="simResult.note">
                <span class="sv-sim-key">备注</span><span>{{ simResult.note }}</span>
              </div>
              <div class="sv-sim-row sv-sim-time">{{ formatDate(simResult.simulated_at) }}</div>
            </div>
          </div>

          <div class="sv-panel-footer">
            <button class="sv-btn" @click="openEdit(selected)">✏️ 编辑</button>
            <button class="sv-btn sv-btn-danger" @click="removeScenario(selected)">🗑 删除</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scenario-view { padding: var(--sp-4) var(--sp-5); max-width: 1200px; margin: 0 auto; }

/* 页头 */
.sv-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--sp-4); flex-wrap: wrap; gap: var(--sp-2); }
.sv-header-left { display: flex; align-items: center; gap: var(--sp-3); }
.sv-title { font-size: var(--fs-xl); font-weight: 700; margin: 0; }
.sv-count { font-size: var(--fs-sm); color: var(--text-2); background: var(--surface-alt); padding: 2px 8px; border-radius: 12px; }
.sv-header-right { display: flex; align-items: center; gap: var(--sp-2); }

/* 主体 */
.sv-main { display: flex; gap: var(--sp-4); align-items: flex-start; }

/* 列表 */
.sv-list { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--sp-2); }
.sv-list-narrow { max-width: 420px; flex: 0 0 auto; }
.sv-empty { text-align: center; color: var(--text-3); padding: var(--sp-8) 0; font-size: var(--fs-md); }

/* 卡片 */
.sv-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--sp-3) var(--sp-4); cursor: pointer; transition: border-color var(--dur-fast), box-shadow var(--dur-fast); position: relative; }
.sv-card:hover { border-color: var(--accent); }
.sv-card-active { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 20%, transparent); }
.sv-card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--sp-1); }
.sv-card-name { font-weight: 600; font-size: var(--fs-md); }
.sv-card-desc { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sv-card-meta { display: flex; align-items: center; justify-content: space-between; font-size: var(--fs-xs); color: var(--text-3); }
.sv-card-actions { position: absolute; top: var(--sp-2); right: var(--sp-2); display: flex; gap: 4px; opacity: 0; transition: opacity var(--dur-fast); }
.sv-card:hover .sv-card-actions { opacity: 1; }

/* 侧边面板 */
.sv-panel { width: 420px; flex: 0 0 auto; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); overflow: hidden; }
.sv-panel-header { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-3) var(--sp-4); border-bottom: 1px solid var(--border); font-weight: 600; font-size: var(--fs-md); }
.sv-close-btn { background: none; border: none; cursor: pointer; font-size: var(--fs-md); color: var(--text-2); padding: 2px 6px; border-radius: var(--radius-sm); }
.sv-close-btn:hover { background: var(--surface-alt); }

/* 表单 */
.sv-form { padding: var(--sp-3) var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-2); }
.sv-label { font-size: var(--fs-sm); color: var(--text-2); font-weight: 500; }
.sv-req { color: var(--danger, #ef4444); }
.sv-input { border: 1px solid var(--border-md); border-radius: var(--radius-sm); padding: 7px 10px; font-size: var(--fs-sm); background: var(--bg); color: var(--text-1); width: 100%; box-sizing: border-box; }
.sv-input:focus { outline: none; border-color: var(--accent); }
.sv-textarea { border: 1px solid var(--border-md); border-radius: var(--radius-sm); padding: 7px 10px; font-size: var(--fs-sm); background: var(--bg); color: var(--text-1); width: 100%; box-sizing: border-box; resize: vertical; }
.sv-textarea.sv-mono { font-family: monospace; }
.sv-form-error { color: var(--danger, #ef4444); font-size: var(--fs-sm); }
.sv-form-actions { display: flex; gap: var(--sp-2); justify-content: flex-end; padding-top: var(--sp-1); }

/* 详情 */
.sv-detail { padding: var(--sp-3) var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-2); }
.sv-detail-row { display: flex; align-items: flex-start; gap: var(--sp-2); font-size: var(--fs-sm); }
.sv-detail-col { flex-direction: column; }
.sv-detail-key { color: var(--text-2); min-width: 72px; flex-shrink: 0; font-weight: 500; }
.sv-pre { font-family: monospace; font-size: var(--fs-xs); background: var(--surface-alt); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: var(--sp-2); margin: 0; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }

/* 模拟区 */
.sv-simulate-section { border-top: 1px solid var(--border); padding: var(--sp-3) var(--sp-4); }
.sv-sim-title { font-weight: 700; font-size: var(--fs-md); margin-bottom: 4px; }
.sv-sim-desc { font-size: var(--fs-xs); color: var(--text-2); margin-bottom: var(--sp-2); }
.sv-sim-btn { margin-top: var(--sp-1); }
.sv-sim-result { margin-top: var(--sp-3); background: var(--surface-alt); border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--sp-3); display: flex; flex-direction: column; gap: 6px; }
.sv-sim-result-title { font-weight: 600; font-size: var(--fs-sm); margin-bottom: 4px; }
.sv-sim-row { display: flex; align-items: flex-start; gap: var(--sp-2); font-size: var(--fs-sm); }
.sv-sim-key { color: var(--text-2); min-width: 60px; flex-shrink: 0; }
.sv-sim-time { color: var(--text-3); font-size: var(--fs-xs); justify-content: flex-end; }

/* 面板底部 */
.sv-panel-footer { border-top: 1px solid var(--border); padding: var(--sp-2) var(--sp-4); display: flex; gap: var(--sp-2); justify-content: flex-end; }

/* 通用 */
.sv-select { border: 1px solid var(--border-md); border-radius: var(--radius-sm); padding: 7px 10px; font-size: var(--fs-sm); background: var(--bg); color: var(--text-1); }
.sv-select.sv-full { width: 100%; }
.sv-error { background: color-mix(in srgb, var(--danger,#ef4444) 10%, transparent); border: 1px solid color-mix(in srgb, var(--danger,#ef4444) 30%, transparent); border-radius: var(--radius-sm); padding: var(--sp-2) var(--sp-3); font-size: var(--fs-sm); color: var(--danger, #ef4444); margin-bottom: var(--sp-3); }
.sv-type-badge { font-size: var(--fs-xs); background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); border-radius: 10px; padding: 2px 8px; white-space: nowrap; }
.sv-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.sv-tag { font-size: var(--fs-xs); background: var(--surface-alt); border: 1px solid var(--border); border-radius: 8px; padding: 2px 7px; }
.sv-tag-favor { background: color-mix(in srgb, #22c55e 12%, transparent); border-color: color-mix(in srgb, #22c55e 30%, transparent); color: #15803d; }
.sv-tag-avoid { background: color-mix(in srgb, #ef4444 10%, transparent); border-color: color-mix(in srgb, #ef4444 25%, transparent); color: #b91c1c; }
.sv-load-more { text-align: center; padding: var(--sp-2) 0; }
.sv-btn { padding: 7px 16px; border: 1px solid var(--border-md); background: var(--surface); color: var(--text-1); border-radius: var(--radius-sm); font-size: var(--fs-sm); cursor: pointer; transition: border-color var(--dur-fast); }
.sv-btn:hover { border-color: var(--accent); color: var(--accent); }
.sv-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sv-btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.sv-btn-primary:hover { background: color-mix(in srgb, var(--accent) 85%, #000); border-color: color-mix(in srgb, var(--accent) 85%, #000); color: #fff; }
.sv-btn-danger { color: var(--danger, #ef4444); border-color: color-mix(in srgb, var(--danger,#ef4444) 30%, transparent); }
.sv-btn-danger:hover { background: color-mix(in srgb, var(--danger,#ef4444) 10%, transparent); }
.sv-btn-icon { background: none; border: none; cursor: pointer; font-size: 14px; padding: 4px; border-radius: 4px; line-height: 1; }

/* 推演类型 tab 按钮 */
.sv-type-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.sv-type-tab { padding: 5px 13px; border: 1px solid var(--border-md); border-radius: 14px; background: var(--surface); color: var(--text-2); font-size: var(--fs-sm); cursor: pointer; transition: all var(--dur-fast); }
.sv-type-tab:hover { border-color: var(--accent); color: var(--accent); }
.sv-type-tab-active { background: var(--accent); color: #fff !important; border-color: var(--accent); }

/* 宽面板（合盘模式）*/
.sv-panel-wide { width: 680px; }

/* 甲方 / 乙方双列布局 */
.sv-parties-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.sv-party { border-radius: var(--radius-md); padding: var(--sp-3); display: flex; flex-direction: column; gap: 6px; }
.sv-party-a { border: 2px solid #ef4444; background: color-mix(in srgb, #ef4444 4%, transparent); }
.sv-party-b { border: 2px solid #3b82f6; background: color-mix(in srgb, #3b82f6 4%, transparent); }
.sv-party-header { font-weight: 700; font-size: var(--fs-sm); padding-bottom: 4px; border-bottom: 1px solid; margin-bottom: 2px; }
.sv-party-a .sv-party-header { color: #ef4444; border-color: color-mix(in srgb, #ef4444 30%, transparent); }
.sv-party-b .sv-party-header { color: #3b82f6; border-color: color-mix(in srgb, #3b82f6 30%, transparent); }

/* 卡片副标题（当事人姓名）*/
.sv-card-subtitle { font-size: var(--fs-sm); color: var(--text-1); font-weight: 500; margin-bottom: 2px; }
</style>
