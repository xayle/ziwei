<script setup lang="ts">
import type { ZiweiChartNote, ZiweiNoteTarget } from '@/composables/useZiweiInteractionState'

const props = defineProps<{
  visible: boolean
  notes: ZiweiChartNote[]
  editingNote: ZiweiChartNote | null
  noteInput: string
  noteTarget: ZiweiNoteTarget
  noteTargetName: string
}>()

const emit = defineEmits<{
  close: []
  'update:noteInput': [value: string]
  'update:noteTarget': [value: ZiweiNoteTarget]
  'update:noteTargetName': [value: string]
  addNote: []
  updateNote: []
  cancelEdit: []
  startEdit: [note: ZiweiChartNote]
  deleteNote: [id: string]
}>()
</script>

<template>
  <div v-if="props.visible" class="notes-panel">
    <div class="np-header">
      <span>命盘笔记 ({{ props.notes.length }})</span>
      <button class="np-close" @click="emit('close')">✕</button>
    </div>
    <div class="np-content">
      <div class="np-add-form">
        <select
          :value="props.noteTarget"
          class="np-target-select"
          @change="emit('update:noteTarget', ($event.target as HTMLSelectElement).value as ZiweiNoteTarget)"
        >
          <option value="general">全盘</option>
          <option value="palace">宫位</option>
          <option value="star">星曜</option>
        </select>
        <input
          v-if="props.noteTarget !== 'general'"
          :value="props.noteTargetName"
          class="np-target-name"
          :placeholder="props.noteTarget === 'palace' ? '宫名如:命宫' : '星名如:紫微'"
          @input="emit('update:noteTargetName', ($event.target as HTMLInputElement).value)"
        />
        <textarea
          :value="props.noteInput"
          class="np-textarea"
          rows="2"
          placeholder="输入笔记内容..."
          @input="emit('update:noteInput', ($event.target as HTMLTextAreaElement).value)"
        />
        <div class="np-btns">
          <button v-if="props.editingNote" class="np-cancel" @click="emit('cancelEdit')">取消</button>
          <button v-if="props.editingNote" class="np-save" @click="emit('updateNote')">保存修改</button>
          <button v-else class="np-add" @click="emit('addNote')">添加笔记</button>
        </div>
      </div>
      <div v-if="props.notes.length" class="np-list">
        <div v-for="note in props.notes" :key="note.id" class="np-item">
          <div class="np-item-head">
            <span class="np-item-target" :class="'np-' + note.target">{{ note.targetName }}</span>
            <span class="np-item-time">{{ new Date(note.updatedAt).toLocaleDateString() }}</span>
          </div>
          <div class="np-item-content">{{ note.content }}</div>
          <div class="np-item-actions">
            <button @click="emit('startEdit', note)">编辑</button>
            <button @click="emit('deleteNote', note.id)">删除</button>
          </div>
        </div>
      </div>
      <div v-else class="np-empty">暂无笔记，快来记录你的心得吧</div>
    </div>
  </div>
</template>

<style scoped>
.notes-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: #fff;
  border: 1px solid var(--border-md);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  width: 340px;
  max-height: 420px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}

.np-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
  color: #7c3aed;
}

.np-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--text-3);
}

.np-close:hover {
  color: var(--danger);
}

.np-content {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
}

.np-add-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed var(--border);
}

.np-target-select,
.np-target-name {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}

.np-textarea {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  resize: vertical;
  min-height: 50px;
}

.np-btns {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.np-add,
.np-save {
  padding: 6px 14px;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}

.np-add:hover,
.np-save:hover {
  background: #6d28d9;
}

.np-cancel {
  padding: 6px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--fs-sm);
}

.np-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.np-item {
  padding: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.np-item-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.np-item-target {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 500;
}

.np-general { background: #e0e7ff; color: #4338ca; }
.np-palace { background: #dcfce7; color: #166534; }
.np-star { background: #fef3c7; color: #b45309; }

.np-item-time {
  font-size: 10px;
  color: var(--text-3);
}

.np-item-content {
  font-size: var(--fs-sm);
  color: var(--text);
  line-height: 1.5;
  white-space: pre-wrap;
}

.np-item-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.np-item-actions button {
  font-size: 11px;
  color: var(--text-3);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}

.np-item-actions button:hover {
  color: var(--accent);
}

.np-empty {
  text-align: center;
  color: var(--text-3);
  font-size: var(--fs-sm);
  padding: 20px;
}
</style>