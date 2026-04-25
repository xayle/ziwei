<script setup lang="ts">
/**
 * CardNotes.vue — 卡4：笔记
 * 按 sectionId 独立存储到 localStorage[report:notes:{sectionId}]
 * debounce 500ms 实时保存；右下角字数计数
 */
import { ref, computed, watch } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()
const isCollapsed  = computed(() => store.cardCollapsed['notes'] ?? false)
const activeSec    = computed(() => store.activeSection)
const noteText     = ref('')
const LSKEY        = (id: string) => `report:notes:${id}`

// 切换 section 时加载对应笔记
watch(activeSec, (id) => {
  if (!id) { noteText.value = ''; return }
  noteText.value = localStorage.getItem(LSKEY(id)) ?? ''
}, { immediate: true })

// 500ms debounce 存储
let _debounceTimer: ReturnType<typeof setTimeout> | null = null
function handleInput(e: Event) {
  const v = (e.target as HTMLTextAreaElement).value
  noteText.value = v
  if (_debounceTimer) clearTimeout(_debounceTimer)
  if (activeSec.value) {
    _debounceTimer = setTimeout(() => {
      localStorage.setItem(LSKEY(activeSec.value!), v)
    }, 500)
  }
}

function clearNote() {
  if (!activeSec.value) return
  if (_debounceTimer) clearTimeout(_debounceTimer)
  noteText.value = ''
  localStorage.removeItem(LSKEY(activeSec.value))
}

const hasNote      = computed(() => noteText.value.trim().length > 0)
const charCount    = computed(() => noteText.value.length)
const sectionLabel = computed(() => activeSec.value ? `[${activeSec.value}]` : '')
</script>

<template>
  <div class="card" :class="{ collapsed: isCollapsed }">
    <button class="card-header" @click="store.toggleCard('notes')">
      <span class="card-title">📝 笔记</span>
      <span class="note-badge" v-if="hasNote">●</span>
      <span class="card-toggle">{{ isCollapsed ? '▸' : '▾' }}</span>
    </button>
    <div class="card-body" v-show="!isCollapsed">
      <div class="sec-label" v-if="activeSec">当前节 {{ sectionLabel }}</div>
      <div v-if="!activeSec" class="card-empty">选择报告章节后即可记录笔记</div>
      <template v-else>
        <textarea
          class="note-area"
          placeholder="在此记录心得、解读或提醒…"
          :value="noteText"
          @input="handleInput"
          rows="5"
        />
        <div class="note-actions">
          <button class="btn-clear" @click="clearNote" :disabled="!hasNote">清除</button>
          <span class="note-count">{{ charCount }} 字</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
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
.note-badge { font-size: 8px; color: var(--accent); margin-left: auto; line-height: 1; }
.card-body { padding: var(--sp-3); border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: var(--sp-2); }
.card-empty { font-size: var(--fs-xs); color: var(--text-3); text-align: center; padding: var(--sp-2) 0; }

/* Section 标签 */
.sec-label {
  font-size: 10px; color: var(--text-3);
  background: var(--bg); padding: 1px 8px; border-radius: 99px;
  display: inline-block;
}

/* 笔记文本域 */
.note-area {
  width: 100%; box-sizing: border-box;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-sm); color: var(--text);
  font-size: var(--fs-xs); font-family: var(--font-cn);
  line-height: 1.7; padding: var(--sp-2);
  resize: vertical; outline: none;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.note-area:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(217,119,6,.15); }

/* 操作行 */
.note-actions { display: flex; align-items: center; justify-content: space-between; }
.btn-clear {
  font-size: 11px; padding: 2px 10px;
  background: transparent; border: 1px solid var(--border-md);
  border-radius: var(--radius-sm); cursor: pointer; color: var(--text-3);
  transition: border-color var(--dur-fast), color var(--dur-fast);
}
.btn-clear:hover:not(:disabled) { border-color: var(--danger); color: var(--danger); }
.btn-clear:disabled { opacity: .45; cursor: not-allowed; }
.note-count { font-size: 10px; color: var(--text-3); }
</style>
