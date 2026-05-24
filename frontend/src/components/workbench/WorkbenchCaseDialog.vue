<script setup lang="ts">
/**
 * WorkbenchCaseDialog.vue — 新建/编辑案例弹窗
 *
 * Props 对应 useWorkbenchCaseCrud() 的状态。
 * 通过 v-model 绑定 formData 各字段，通过 emit 触发保存/取消。
 */
defineProps<{
  showCreateDialog: boolean
  showEditDialog:   boolean
  formData: {
    name: string
    birth_dt_local: string
    gender: string
    solar_time_enabled: boolean
  }
  formSaving: boolean
}>()

const emit = defineEmits<{
  'update:formDataName':            [v: string]
  'update:formDataBirthDtLocal':    [v: string]
  'update:formDataGender':          [v: string]
  'update:formDataSolarTimeEnabled':[v: boolean]
  'close': []
  'submit': []
}>()
</script>

<template>
  <Teleport to="body">
    <div
      v-if="showCreateDialog || showEditDialog"
      class="wb-modal-mask"
      @click.self="emit('close')"
    >
      <div class="wb-modal">
        <h2 class="wb-modal-title">{{ showEditDialog ? '编辑案例' : '新建案例' }}</h2>
        <div class="wb-form-grid">
          <label class="wb-form-item">
            <span class="wb-form-label">姓名</span>
            <input
              :value="formData.name"
              class="wb-form-input"
              placeholder="例：张三"
              @input="emit('update:formDataName', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label v-if="!showEditDialog" class="wb-form-item">
            <span class="wb-form-label">出生时间</span>
            <input
              :value="formData.birth_dt_local"
              type="datetime-local"
              class="wb-form-input"
              @input="emit('update:formDataBirthDtLocal', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label class="wb-form-item">
            <span class="wb-form-label">性别</span>
            <select
              :value="formData.gender"
              class="wb-form-input"
              @change="emit('update:formDataGender', ($event.target as HTMLSelectElement).value)"
            >
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </label>
          <label v-if="!showEditDialog" class="wb-form-item">
            <span class="wb-form-label">
              <input
                type="checkbox"
                :checked="formData.solar_time_enabled"
                @change="emit('update:formDataSolarTimeEnabled', ($event.target as HTMLInputElement).checked)"
              />
              启用真太阳时
            </span>
          </label>
        </div>
        <div class="wb-modal-actions">
          <button class="wb-btn-ghost" @click="emit('close')">取消</button>
          <button
            class="wb-btn-accent"
            :disabled="formSaving"
            @click="emit('submit')"
          >
            {{ formSaving ? '保存中…' : (showEditDialog ? '保存修改' : '创建') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.wb-modal-mask {
  position: fixed; inset: 0; background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.wb-modal {
  background: var(--surface); border-radius: var(--radius-md);
  padding: var(--sp-6); width: min(480px, 92vw);
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
}
.wb-modal-title { font-size: var(--fs-lg); font-weight: 700; margin-bottom: var(--sp-4); }
.wb-form-grid { display: flex; flex-direction: column; gap: var(--sp-3); margin-bottom: var(--sp-5); }
.wb-form-item { display: flex; flex-direction: column; gap: var(--sp-1); }
.wb-form-label { font-size: var(--fs-sm); color: var(--text-2); font-weight: 500; }
.wb-form-input { padding: 7px 10px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); background: var(--surface); color: var(--text-1); width: 100%; box-sizing: border-box; }
.wb-modal-actions { display: flex; gap: var(--sp-3); justify-content: flex-end; }
.wb-btn-ghost { padding: 8px 18px; background: transparent; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-md); cursor: pointer; color: var(--text-2); }
.wb-btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.wb-btn-accent { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-sm); font-size: var(--fs-md); font-weight: 600; cursor: pointer; }
.wb-btn-accent:hover { background: var(--accent-dark); }
.wb-btn-accent:disabled { opacity: .6; cursor: not-allowed; }
</style>
