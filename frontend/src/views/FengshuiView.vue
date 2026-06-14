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

<style src="./FengshuiView.css" scoped />
