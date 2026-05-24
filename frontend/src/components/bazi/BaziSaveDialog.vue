<script setup lang="ts">
defineProps<{
  open:         boolean
  birthDt:      string
  cityName:     string
  initCity:     string
  gender:       'male' | 'female' | ''
  saveCaseName: string
  saveCaseNotes: string
  saveCaseSaving: boolean
  saveCaseError:  string
}>()

const emit = defineEmits<{
  (e: 'update:saveCaseName',  val: string): void
  (e: 'update:saveCaseNotes', val: string): void
  (e: 'close'): void
  (e: 'save'):  void
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="bazi-modal-mask" @click.self="emit('close')">
      <div class="bazi-modal">
        <h2 class="bazi-modal-title">保存案例</h2>
        <p class="bazi-modal-desc">把当前八字排盘保存到案例库，后续可生成深度解读报告与运营工作流。</p>
        <div class="bazi-modal-body">
          <label class="bazi-form-item">
            <span class="bazi-form-label">案例名称</span>
            <input
              :value="saveCaseName"
              class="bazi-form-input"
              placeholder="请输入案例名称"
              @input="emit('update:saveCaseName', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label class="bazi-form-item">
            <span class="bazi-form-label">备注</span>
            <textarea
              :value="saveCaseNotes"
              class="bazi-form-textarea"
              rows="3"
              placeholder="可选：记录客户背景、关注问题或备注"
              @input="emit('update:saveCaseNotes', ($event.target as HTMLTextAreaElement).value)"
            ></textarea>
          </label>
          <div class="bazi-save-summary">
            <span>出生：{{ birthDt }}</span>
            <span>城市：{{ cityName || initCity }}</span>
            <span>性别：{{ gender === 'male' ? '男' : gender === 'female' ? '女' : '不指定' }}</span>
          </div>
          <p v-if="saveCaseError" class="error-msg bazi-save-error">{{ saveCaseError }}</p>
        </div>
        <div class="bazi-modal-actions">
          <button class="btn-sec" @click="emit('close')">取消</button>
          <button class="btn-primary" :disabled="saveCaseSaving" @click="emit('save')">
            {{ saveCaseSaving ? '保存中…' : '确认保存' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.bazi-modal-mask {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  padding: var(--sp-4);
}
.bazi-modal {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  padding: var(--sp-6);
  width: 100%; max-width: 480px;
}
.bazi-modal-title { font-size: var(--fs-xl); font-weight: 700; margin-bottom: var(--sp-2); color: var(--text); }
.bazi-modal-desc { font-size: var(--fs-sm); color: var(--text-2); margin-bottom: var(--sp-4); }
.bazi-modal-body { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-4); }
.bazi-form-item { display: flex; flex-direction: column; gap: 6px; }
.bazi-form-label { font-size: var(--fs-sm); font-weight: 600; color: var(--text-2); }
.bazi-form-input, .bazi-form-textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-2);
  color: var(--text);
  font-size: var(--fs-sm);
  font-family: var(--font-cn);
}
.bazi-form-input:focus, .bazi-form-textarea:focus {
  outline: none; border-color: var(--accent);
}
.bazi-form-textarea { resize: vertical; min-height: 72px; }
.bazi-save-summary {
  display: flex; flex-wrap: wrap; gap: var(--sp-3);
  font-size: var(--fs-xs); color: var(--text-3);
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-2);
  border-radius: 6px;
}
.bazi-save-error { margin: 0; }
.bazi-modal-actions { display: flex; justify-content: flex-end; gap: var(--sp-3); }
</style>
