<script setup lang="ts">
type StarSearchItem = {
  name: string
  palace: string
  palaceIdx: number
  type: 'main' | 'aux'
  brightness?: string
  transforms?: string[]
}

const props = defineProps<{
  visible: boolean
  query: string
  results: StarSearchItem[]
}>()

const emit = defineEmits<{
  close: []
  'update:query': [value: string]
  select: [palaceIdx: number]
}>()

function handleInput(event: Event) {
  emit('update:query', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <transition name="fade">
    <div v-if="props.visible" class="star-search-modal no-print" @click.self="emit('close')">
      <div class="star-search-box card">
        <div class="ss-header">
          <span class="ss-title">🔍 全盘星曜搜索</span>
          <button class="ss-close" @click="emit('close')">✕</button>
        </div>
        <input
          :value="props.query"
          type="text"
          class="star-search-input"
          placeholder="输入星曜名称，如：紫微、天机、禄存..."
          @input="handleInput"
          @keydown.esc="emit('close')"
        />
        <div class="ss-results">
          <div v-if="props.query && props.results.length === 0" class="ss-empty">
            未找到匹配的星曜
          </div>
          <div
            v-for="item in props.results"
            :key="`${item.name}-${item.palaceIdx}`"
            class="ss-item"
            @click="emit('select', item.palaceIdx)"
          >
            <span :class="['ss-star', item.type === 'main' ? 'ss-main' : 'ss-aux']">{{ item.name }}</span>
            <span v-if="item.brightness" class="ss-brightness">{{ item.brightness }}</span>
            <span v-if="item.transforms?.length" class="ss-transforms">{{ item.transforms.join(' ') }}</span>
            <span class="ss-palace">{{ item.palace }}</span>
          </div>
        </div>
        <div class="ss-hint">
          <small>点击结果可跳转至对应宫位</small>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.star-search-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 1100;
}

.star-search-box {
  width: 400px;
  max-width: 90vw;
  max-height: 70vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

.ss-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
  margin-bottom: var(--sp-3);
}

.ss-title {
  font-size: var(--fs-md);
  font-weight: 700;
}

.ss-close {
  background: none;
  border: none;
  font-size: var(--fs-md);
  cursor: pointer;
  color: var(--text-3);
}

.ss-close:hover {
  color: var(--text);
}

.star-search-input {
  width: 100%;
  padding: var(--sp-3);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  font-size: var(--fs-md);
  margin-bottom: var(--sp-3);
  outline: none;
}

.star-search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(217,119,6,0.15);
}

.ss-results {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
}

.ss-empty {
  text-align: center;
  padding: var(--sp-5);
  color: var(--text-3);
}

.ss-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}

.ss-item:hover {
  background: var(--surface-2);
}

.ss-star {
  font-weight: 700;
  font-family: var(--font-cn);
}

.ss-main {
  color: var(--accent);
}

.ss-aux {
  color: var(--text-2);
}

.ss-brightness {
  font-size: var(--fs-xs);
  padding: 1px 5px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-3);
}

.ss-transforms {
  font-size: var(--fs-xs);
  color: #7c3aed;
}

.ss-palace {
  margin-left: auto;
  font-size: var(--fs-sm);
  color: var(--text-3);
}

.ss-hint {
  margin-top: var(--sp-3);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border);
  color: var(--text-3);
  text-align: center;
}
</style>