<script setup lang="ts">
/**
 * CasePicker.vue — 无 caseId 时的案例选择引导页
 */
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const router = useRouter()

const countdown = ref(3)
let timer: ReturnType<typeof setInterval> | null = null

const isLoading = ref(true)

onMounted(async () => {
  await store.loadCaseList()
  isLoading.value = false

  if (store.caseList.length === 0) {
    // 空列表：3秒倒计时跳转 /bazi
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer!)
        router.push('/bazi')
      }
    }, 1000)
  } else if (store.caseList.length === 1) {
    // 只有一个案例：自动跳转
    router.push(`/report/${store.caseList[0].id}`)
  }
})

function selectCase(id: string) {
  if (timer) clearInterval(timer)
  router.push(`/report/${id}`)
}

function goToBazi() {
  if (timer) clearInterval(timer)
  router.push('/bazi')
}

const isEmpty = computed(() => !isLoading.value && store.caseList.length === 0)
const hasMultiple = computed(() => !isLoading.value && store.caseList.length > 1)
</script>

<template>
  <div class="picker-wrap">
    <div class="picker-card">
      <h2 class="picker-title">📚 选择命理案例</h2>
      <p class="picker-sub">请选择要查看报告书的案例</p>

      <!-- 加载中 -->
      <div v-if="isLoading" class="picker-loading">
        <div class="skel-row" v-for="i in 3" :key="i" />
      </div>

      <!-- 空列表：引导提示 + 倒计时 -->
      <div v-else-if="isEmpty" class="picker-empty">
        <p class="picker-empty-txt">暂无案例，请先完成排盘并保存</p>
        <p class="picker-countdown">{{ countdown }} 秒后自动跳转到八字排盘…</p>
        <button class="btn-primary" @click="goToBazi">立即前往八字排盘</button>
      </div>

      <!-- 多案例列表 -->
      <div v-else-if="hasMultiple" class="case-list">
        <button
          v-for="c in store.caseList"
          :key="c.id"
          class="case-item"
          @click="selectCase(c.id)"
        >
          <span class="case-name">{{ c.name }}</span>
          <span class="case-gender">{{ c.gender === 'female' ? '女' : c.gender === 'male' ? '男' : '—' }}</span>
          <span class="case-dt">{{ c.birth_dt_local?.slice(0, 10) ?? '' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.picker-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}

.picker-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-8);
  width: min(520px, 90vw);
  box-shadow: var(--shadow);
}

.picker-title { font-size: var(--fs-2xl); font-weight: 700; color: var(--text); margin-bottom: var(--sp-2); }
.picker-sub { font-size: var(--fs-sm); color: var(--text-3); margin-bottom: var(--sp-6); }

/* 加载骨架 */
.picker-loading {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}
.skel-row {
  height: 52px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 400px;
  animation: shimmer 1.2s infinite;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  max-height: 400px;
  overflow-y: auto;
}

.case-item {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  transition: all var(--dur-fast);
}
.case-item:hover {
  border-color: var(--accent);
  background: var(--accent-lt);
}

.case-name { font-weight: 600; color: var(--text); flex: 1; font-family: var(--font-cn); }
.case-gender { font-size: var(--fs-xs); color: var(--text-3); width: 24px; text-align: center; }
.case-dt { font-size: var(--fs-xs); color: var(--text-3); font-family: var(--font-mono); }

.picker-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-6) 0;
  text-align: center;
}
.picker-empty-txt { color: var(--text-3); font-size: var(--fs-sm); }
.picker-countdown {
  font-size: var(--fs-xs);
  color: var(--accent-dark);
  background: var(--accent-lt);
  padding: 4px 12px;
  border-radius: 99px;
  border: 1px solid var(--accent-glow);
}
.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover { background: var(--accent-dark); }
</style>
