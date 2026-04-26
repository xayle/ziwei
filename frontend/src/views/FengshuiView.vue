<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getFengshuiOptions, analyzeRoomLayout, type FengshuiOptions, type RoomLayoutResponse } from '@/api/fengshui'
import { fetchFengshuiBagua, type FengshuiResponse } from '@/api/report'
import { useProfileStore } from '@/stores/profile'

type GenderZh = '男' | '女'

interface BoardCell {
  key: string
  direction: string
  directionLabel: string
  isCenter?: boolean
  selectedRoom?: string
  resultCell?: RoomLayoutResponse['cells'][number]
}

const route = useRoute()
const profile = useProfileStore()

const profileBirth = profile.parseBirthDt()
const defaultGender: GenderZh = profile.gender === 'female' ? '女' : '男'
const DIRECTION_RING = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
const BOARD_ORDER = ['NW', 'N', 'NE', 'W', 'C', 'E', 'SW', 'S', 'SE']

const form = ref({
  birthYear: profileBirth.year,
  gender: defaultGender as GenderZh,
  houseFacing: '',
})

const fengshuiOptions = ref<FengshuiOptions | null>(null)
const bagua = ref<FengshuiResponse | null>(null)
const roomAssignments = ref<Record<string, string>>({})
const roomResult = ref<RoomLayoutResponse | null>(null)

const pageLoading = ref(false)
const optionsLoading = ref(false)
const layoutLoading = ref(false)
const pageError = ref('')
const layoutError = ref('')
const initialized = ref(false)

function parseGender(value: unknown): GenderZh {
  return value === '女' ? '女' : '男'
}

function parseBirthYear(value: unknown): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= 1900 && parsed <= 2100 ? parsed : profileBirth.year
}

function syncFormFromRoute() {
  form.value.birthYear = parseBirthYear(route.query.birth_year)
  form.value.gender = parseGender(route.query.gender ?? defaultGender)
  form.value.houseFacing = typeof route.query.house_facing === 'string' ? route.query.house_facing : ''
}

function getDirectionLabel(direction: string): string {
  return fengshuiOptions.value?.directions_zh?.[direction] ?? direction
}

function getRoomTypeLabel(roomType: string): string {
  return fengshuiOptions.value?.room_type_options?.[roomType] ?? roomType
}

function parseError(error: unknown, fallback: string): string {
  return (error as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
    ?? (error as { message?: string })?.message
    ?? fallback
}

async function loadOptions() {
  optionsLoading.value = true
  try {
    fengshuiOptions.value = await getFengshuiOptions()
  } catch (error: unknown) {
    pageError.value = parseError(error, '风水选项加载失败，请稍后重试')
  } finally {
    optionsLoading.value = false
  }
}

async function runBagua() {
  pageLoading.value = true
  pageError.value = ''
  roomResult.value = null
  try {
    bagua.value = await fetchFengshuiBagua({
      birth_year: Number(form.value.birthYear),
      gender: form.value.gender,
      house_facing: form.value.houseFacing || undefined,
    })
  } catch (error: unknown) {
    pageError.value = parseError(error, '命卦分析失败，请稍后重试')
  } finally {
    pageLoading.value = false
  }
}

async function runLayoutAssessment() {
  if (!Object.keys(roomAssignments.value).length) {
    layoutError.value = '请至少设置一个方位的房间类型'
    return
  }

  layoutLoading.value = true
  layoutError.value = ''
  try {
    roomResult.value = await analyzeRoomLayout({
      birth_year: Number(form.value.birthYear),
      gender: form.value.gender,
      house_facing: form.value.houseFacing || undefined,
      rooms: roomAssignments.value,
    })
  } catch (error: unknown) {
    layoutError.value = parseError(error, '九宫格布局评估失败，请稍后重试')
  } finally {
    layoutLoading.value = false
  }
}

function updateRoom(direction: string, value: string) {
  if (!value) {
    const next = { ...roomAssignments.value }
    delete next[direction]
    roomAssignments.value = next
    roomResult.value = null
    return
  }
  roomAssignments.value = {
    ...roomAssignments.value,
    [direction]: value,
  }
  roomResult.value = null
}

function resetLayout() {
  roomAssignments.value = {}
  roomResult.value = null
  layoutError.value = ''
}

function syncFromProfile() {
  const currentBirth = profile.parseBirthDt()
  form.value.birthYear = currentBirth.year
  form.value.gender = profile.gender === 'female' ? '女' : '男'
}

const directionLegend = computed(() => {
  if (!bagua.value) return []
  return [
    ...bagua.value.auspicious.map(item => ({ ...item, tone: 'good' })),
    ...bagua.value.inauspicious.map(item => ({ ...item, tone: 'bad' })),
  ]
})

const furnitureTips = computed(() => {
  if (!bagua.value) return []
  return [bagua.value.bed_tip, bagua.value.desk_tip, bagua.value.door_tip].filter(Boolean)
})

const layoutBoardCells = computed<BoardCell[]>(() => {
  const cellsMap = new Map((roomResult.value?.cells ?? []).map(cell => [cell.direction, cell]))
  return BOARD_ORDER.map(direction => {
    if (direction === 'C') {
      return {
        key: 'center',
        direction,
        directionLabel: '中宫',
        isCenter: true,
      }
    }
    return {
      key: direction,
      direction,
      directionLabel: getDirectionLabel(direction),
      selectedRoom: roomAssignments.value[direction],
      resultCell: cellsMap.get(direction),
    }
  })
})

const recommendedRooms = computed(() => {
  if (!roomResult.value) return []
  return Array.from(new Set(
    roomResult.value.cells
      .filter(cell => cell.assess_score >= 80)
      .map(cell => cell.room_zh || getRoomTypeLabel(cell.room_type)),
  ))
})

const avoidRooms = computed(() => {
  if (!roomResult.value) return []
  return Array.from(new Set(
    roomResult.value.cells
      .filter(cell => cell.assess_score <= 40)
      .map(cell => cell.room_zh || getRoomTypeLabel(cell.room_type)),
  ))
})

function getAssessClass(level?: string): string {
  if (!level) return ''
  if (level.includes('优') || level.includes('吉')) return 'is-good'
  if (level.includes('中')) return 'is-mid'
  return 'is-bad'
}

function getDirectionTag(direction: string): string {
  const item = directionLegend.value.find(entry => entry.direction === direction)
  return item?.label ?? '未标注'
}

syncFormFromRoute()

watch(() => route.fullPath, () => {
  syncFormFromRoute()
  if (initialized.value) {
    void runBagua()
  }
})

onMounted(async () => {
  await loadOptions()
  initialized.value = true
  await runBagua()
})
</script>

<template>
  <div class="wrap fengshui-view">
    <section class="hero-card">
      <div>
        <div class="hero-kicker">独立模块</div>
        <h1 class="page-title">风水助手</h1>
        <p class="hero-desc">
          将命卦、方位、人宅相合与九宫格布局评估从紫微超级页中独立出来，形成可直接操作的专项工作区。
        </p>
      </div>
      <div class="hero-actions">
        <button class="btn-primary" :disabled="pageLoading" @click="runBagua">
          {{ pageLoading ? '分析中…' : '刷新命卦分析' }}
        </button>
        <button class="btn-secondary" @click="syncFromProfile">同步个人信息</button>
      </div>
    </section>

    <section class="overview-grid">
      <article class="stat-card">
        <div class="stat-label">命卦</div>
        <div class="stat-value">{{ bagua ? `${bagua.gua_name} · ${bagua.life_gua}` : '—' }}</div>
        <div class="stat-note">{{ bagua?.gua_element || '待分析' }}</div>
      </article>
      <article class="stat-card">
        <div class="stat-label">命组</div>
        <div class="stat-value">{{ bagua?.group || '—' }}</div>
        <div class="stat-note">{{ bagua?.birth_year || form.birthYear }} 年生</div>
      </article>
      <article class="stat-card">
        <div class="stat-label">人宅相合</div>
        <div class="stat-value">{{ bagua?.compatibility || '未设置朝向' }}</div>
        <div class="stat-note">{{ bagua?.compatibility_note || '可在下方选择房屋朝向' }}</div>
      </article>
      <article class="stat-card">
        <div class="stat-label">布局评分</div>
        <div class="stat-value">{{ roomResult ? `${roomResult.score} 分` : '未评估' }}</div>
        <div class="stat-note">{{ roomResult?.grade || '先设置房间方位再评估' }}</div>
      </article>
    </section>

    <section class="workspace-grid">
      <article class="card config-card">
        <div class="section-head">
          <div>
            <h2>基础输入</h2>
            <p>按后端 `fengshui` 路由的真实能力组织输入项。</p>
          </div>
          <span v-if="optionsLoading" class="loading-chip">加载选项中…</span>
        </div>

        <div class="form-grid">
          <label class="form-field">
            <span>出生年</span>
            <input v-model.number="form.birthYear" type="number" min="1900" max="2100" />
          </label>
          <label class="form-field">
            <span>性别</span>
            <select v-model="form.gender">
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </label>
          <label class="form-field form-field-wide">
            <span>房屋朝向</span>
            <select v-model="form.houseFacing">
              <option value="">未设置</option>
              <option v-for="(label, key) in (fengshuiOptions?.house_facing_options || {})" :key="key" :value="key">
                {{ label }}
              </option>
            </select>
          </label>
        </div>

        <div v-if="pageError" class="error-box">{{ pageError }}</div>

        <div class="hint-box">
          <strong>模块说明：</strong>
          先做命卦分析，再按八方位配置房间用途，最后进行九宫格布局评估。
        </div>

        <div class="legend-block" v-if="directionLegend.length">
          <div class="legend-title">方位图例</div>
          <div class="legend-list">
            <span
              v-for="item in directionLegend"
              :key="`${item.tone}-${item.direction}`"
              class="legend-chip"
              :class="item.tone"
            >
              {{ item.direction_zh }} · {{ item.label }}
            </span>
          </div>
        </div>
      </article>

      <article class="card result-card">
        <div class="section-head">
          <div>
            <h2>命卦分析</h2>
            <p>对应 `/api/v1/fengshui/bagua` 的方位与家具建议。</p>
          </div>
        </div>

        <div v-if="bagua" class="result-body">
          <div class="bagua-summary">
            <div class="bagua-badge">{{ bagua.life_gua }}</div>
            <div>
              <div class="bagua-title">{{ bagua.gua_name }}命</div>
              <div class="bagua-meta">{{ bagua.gua_element }} · {{ bagua.group }}</div>
            </div>
          </div>

          <div class="dir-columns">
            <div class="dir-box">
              <div class="dir-title">四吉方</div>
              <div class="dir-list">
                <div v-for="item in bagua.auspicious" :key="`good-${item.direction}`" class="dir-item good">
                  <div class="dir-top">
                    <span>{{ item.direction_zh }}（{{ item.direction }}）</span>
                    <span>{{ item.label }}</span>
                  </div>
                  <div class="dir-desc">{{ item.desc }}</div>
                </div>
              </div>
            </div>

            <div class="dir-box">
              <div class="dir-title">四凶方</div>
              <div class="dir-list">
                <div v-for="item in bagua.inauspicious" :key="`bad-${item.direction}`" class="dir-item bad">
                  <div class="dir-top">
                    <span>{{ item.direction_zh }}（{{ item.direction }}）</span>
                    <span>{{ item.label }}</span>
                  </div>
                  <div class="dir-desc">{{ item.desc }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="furnitureTips.length" class="tips-grid">
            <div v-for="tip in furnitureTips" :key="`${tip.item}-${tip.direction}`" class="tip-card">
              <div class="tip-title">{{ tip.item }}</div>
              <div class="tip-meta">{{ tip.direction_zh }}（{{ tip.direction }}） · {{ tip.label }}</div>
              <div class="tip-reason">{{ tip.reason }}</div>
            </div>
          </div>

          <p v-if="bagua.disclaimer" class="disclaimer">⚠ {{ bagua.disclaimer }}</p>
        </div>

        <div v-else class="empty-state">命卦结果将在分析完成后显示。</div>
      </article>
    </section>

    <section class="card planner-card">
      <div class="section-head">
        <div>
          <h2>九宫格布局评估</h2>
          <p>对应 `/api/v1/fengshui/room-layout`，用专项工作区替代紫微页内联面板。</p>
        </div>
        <div class="planner-actions">
          <button class="btn-secondary" @click="resetLayout">清空布局</button>
          <button class="btn-primary" :disabled="layoutLoading" @click="runLayoutAssessment">
            {{ layoutLoading ? '评估中…' : '评估布局' }}
          </button>
        </div>
      </div>

      <div class="planner-grid">
        <div class="room-form-grid">
          <label v-for="direction in DIRECTION_RING" :key="direction" class="room-field">
            <span>{{ getDirectionLabel(direction) }}（{{ direction }}）</span>
            <select :value="roomAssignments[direction] || ''" @change="updateRoom(direction, ($event.target as HTMLSelectElement).value)">
              <option value="">不设置</option>
              <option v-for="(label, key) in (fengshuiOptions?.room_type_options || {})" :key="`${direction}-${key}`" :value="key">
                {{ label }}
              </option>
            </select>
          </label>
        </div>

        <div class="board-panel">
          <div class="board-grid">
            <div
              v-for="cell in layoutBoardCells"
              :key="cell.key"
              class="board-cell"
              :class="[
                cell.isCenter ? 'is-center' : getAssessClass(cell.resultCell?.assess_level),
              ]"
            >
              <div class="board-dir">{{ cell.directionLabel }}</div>
              <template v-if="!cell.isCenter">
                <div class="board-room">{{ cell.resultCell?.room_zh || (cell.selectedRoom ? getRoomTypeLabel(cell.selectedRoom) : '未设置') }}</div>
                <div class="board-tag">{{ cell.resultCell?.label || getDirectionTag(cell.direction) }}</div>
                <div v-if="cell.resultCell" class="board-score">{{ cell.resultCell.assess_score }} 分</div>
              </template>
              <template v-else>
                <div class="board-room">布局总览</div>
                <div class="board-tag">{{ roomResult?.grade || '待评估' }}</div>
              </template>
            </div>
          </div>

          <div v-if="layoutError" class="error-box">{{ layoutError }}</div>

          <template v-if="roomResult">
            <div class="planner-summary">
              <div class="planner-score">{{ roomResult.grade }} · {{ roomResult.score }} 分</div>
              <div class="planner-note">{{ roomResult.gua_name }}命 · {{ roomResult.disclaimer }}</div>
            </div>

            <div v-if="recommendedRooms.length || avoidRooms.length" class="planner-tags">
              <div v-if="recommendedRooms.length" class="tag-group">
                <div class="tag-group-title">推荐房型</div>
                <div class="tag-list">
                  <span v-for="item in recommendedRooms" :key="item" class="tag-chip good">{{ item }}</span>
                </div>
              </div>
              <div v-if="avoidRooms.length" class="tag-group">
                <div class="tag-group-title">避开房型</div>
                <div class="tag-list">
                  <span v-for="item in avoidRooms" :key="item" class="tag-chip bad">{{ item }}</span>
                </div>
              </div>
            </div>

            <div class="result-badges">
              <div
                v-for="cell in roomResult.cells"
                :key="`${cell.direction}-${cell.room_type}`"
                class="result-badge"
                :class="getAssessClass(cell.assess_level)"
              >
                {{ cell.room_zh || getRoomTypeLabel(cell.room_type) }}@{{ cell.direction_zh }} · {{ cell.assess_note }}
              </div>
            </div>

            <ul v-if="roomResult.suggestions.length" class="suggestion-list">
              <li v-for="(item, index) in roomResult.suggestions" :key="index">{{ item }}</li>
            </ul>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.fengshui-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card,
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 24px 28px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08), rgba(20, 184, 166, 0.08));
}

.hero-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
  margin-bottom: 8px;
}

.page-title {
  margin: 0;
  font-size: 32px;
}

.hero-desc {
  margin: 10px 0 0;
  max-width: 720px;
  color: var(--text-2);
  line-height: 1.75;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
}

.overview-grid,
.workspace-grid {
  display: grid;
  gap: 16px;
}

.overview-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.stat-card {
  padding: 18px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-3);
}

.stat-value {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
}

.stat-note {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-2);
}

.workspace-grid {
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
}

.card {
  padding: 22px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.section-head h2 {
  margin: 0;
  font-size: 20px;
}

.section-head p {
  margin: 6px 0 0;
  color: var(--text-2);
  line-height: 1.6;
}

.loading-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 600;
}

.form-grid,
.room-form-grid {
  display: grid;
  gap: 14px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.room-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-field,
.room-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-field-wide {
  grid-column: span 2;
}

.form-field span,
.room-field span {
  font-size: 13px;
  color: var(--text-2);
  font-weight: 600;
}

input,
select {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
}

.btn-primary,
.btn-secondary {
  min-height: 42px;
  padding: 0 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #fff;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-secondary {
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text);
}

.hint-box,
.error-box,
.disclaimer {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  line-height: 1.7;
}

.hint-box {
  background: #f8fafc;
  color: var(--text-2);
}

.error-box {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.legend-block {
  margin-top: 18px;
}

.legend-title,
.dir-title,
.tag-group-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-2);
  margin-bottom: 10px;
}

.legend-list,
.tag-list,
.result-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-chip,
.tag-chip,
.result-badge {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.legend-chip.good,
.tag-chip.good {
  background: #dcfce7;
  color: #166534;
}

.legend-chip.bad,
.tag-chip.bad {
  background: #fee2e2;
  color: #b91c1c;
}

.bagua-summary {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
}

.bagua-badge {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #0f766e;
  color: #fff;
  font-size: 24px;
  font-weight: 700;
}

.bagua-title {
  font-size: 20px;
  font-weight: 700;
}

.bagua-meta {
  margin-top: 4px;
  color: var(--text-2);
}

.dir-columns,
.tips-grid,
.planner-grid {
  display: grid;
  gap: 16px;
  margin-top: 18px;
}

.dir-columns {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.tips-grid,
.planner-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.dir-box,
.tip-card,
.board-panel {
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 14px;
  padding: 14px;
}

.dir-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dir-item {
  padding: 12px;
  border-radius: 12px;
}

.dir-item.good {
  background: #ecfdf5;
}

.dir-item.bad {
  background: #fef2f2;
}

.dir-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-weight: 700;
}

.dir-desc,
.tip-reason,
.planner-note,
.empty-state {
  margin-top: 6px;
  color: var(--text-2);
  line-height: 1.7;
}

.tip-title {
  font-weight: 700;
}

.tip-meta {
  margin-top: 4px;
  color: #0f766e;
  font-size: 13px;
}

.planner-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.board-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.board-cell {
  min-height: 112px;
  padding: 12px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.board-cell.is-center {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(20, 184, 166, 0.08));
}

.board-cell.is-good {
  background: #ecfdf5;
}

.board-cell.is-mid {
  background: #fff7ed;
}

.board-cell.is-bad {
  background: #fef2f2;
}

.board-dir {
  font-size: 12px;
  color: var(--text-3);
}

.board-room {
  margin-top: 8px;
  font-weight: 700;
}

.board-tag,
.board-score,
.planner-score {
  margin-top: 6px;
  font-size: 13px;
}

.planner-score {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.planner-summary,
.planner-tags,
.suggestion-list {
  margin-top: 16px;
}

.planner-tags {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.suggestion-list {
  padding-left: 18px;
  color: var(--text-2);
  line-height: 1.8;
}

@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-grid,
  .planner-grid,
  .tips-grid,
  .dir-columns {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-card {
    flex-direction: column;
  }

  .overview-grid,
  .form-grid,
  .room-form-grid,
  .planner-tags {
    grid-template-columns: 1fr;
  }

  .form-field-wide {
    grid-column: span 1;
  }
}
</style>