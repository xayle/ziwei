<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ziweiBatch } from '@/api/ziwei'

const route = useRoute()
const router = useRouter()

const selectedFile = ref<File | null>(null)
const templateVersion = ref('')
const loading = ref(false)
const status = ref('请选择 CSV 文件后开始批量排盘。')
const error = ref('')

const sourceHint = computed(() => route.query.from === 'ziwei'
  ? '你正在从紫微模块进入批量排盘工作区。'
  : '这是独立的紫微批量排盘工作区。')

function downloadBlobFile(blob: Blob, fileName: string) {
  const href = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  setTimeout(() => URL.revokeObjectURL(href), 1200)
}

function handleFileChange(event: Event) {
  const files = (event.target as HTMLInputElement).files
  selectedFile.value = files?.[0] ?? null
  error.value = ''
  status.value = selectedFile.value
    ? `已选择：${selectedFile.value.name}`
    : '请选择 CSV 文件后开始批量排盘。'
}

function downloadSample() {
  const csv = 'name,year,month,day,hour,minute,gender,liunian_year\n'
    + '张三,1990,5,20,8,30,男,2026\n'
    + '李四,1985,9,15,14,0,女,2026\n'
    + '王五,2000,1,1,0,0,男,\n'
  downloadBlobFile(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }), 'ziwei_batch_sample.csv')
}

async function runBatch() {
  if (!selectedFile.value || loading.value) return

  loading.value = true
  error.value = ''
  status.value = '上传并计算中，请稍候…'
  try {
    const blob = await ziweiBatch(selectedFile.value, templateVersion.value.trim() || undefined)
    const dt = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    downloadBlobFile(blob, `ziwei_batch_${dt}.zip`)
    status.value = '批量排盘完成，ZIP 已开始下载。'
  } catch (e: unknown) {
    error.value = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as Error).message
      ?? '批量排盘失败，请稍后重试'
    status.value = '批量排盘失败。'
  } finally {
    loading.value = false
  }
}

function backToZiwei() {
  router.push('/ziwei')
}
</script>

<template>
  <main class="batch-view">
    <section class="hero card">
      <div>
        <p class="hero-kicker">效率工具</p>
        <h1 class="hero-title">紫微批量排盘</h1>
        <p class="hero-desc">把 CSV 上传、模板版本设置和 ZIP 下载从紫微超级页中拆出来，形成独立批量工作区。</p>
      </div>
      <div class="hero-actions">
        <button class="btn-secondary" @click="backToZiwei">返回紫微模块</button>
      </div>
    </section>

    <section class="card info-card">
      <div class="info-title">当前来源</div>
      <div class="info-desc">{{ sourceHint }}</div>
    </section>

    <section class="workspace-grid">
      <article class="card editor-card">
        <div class="section-head">
          <div>
            <h2>上传与配置</h2>
            <p>支持上传 CSV 后批量生成紫微命盘压缩包。</p>
          </div>
          <button class="btn-secondary" @click="downloadSample">下载 CSV 模板</button>
        </div>

        <div class="form-grid">
          <label class="field field-wide">
            <span>模板版本（可选）</span>
            <input v-model="templateVersion" type="text" placeholder="standard / pro / simple" />
          </label>
        </div>

        <label class="upload-box">
          <input class="file-input" type="file" accept=".csv,text/csv" @change="handleFileChange" />
          <div class="upload-inner">
            <strong>{{ selectedFile ? '重新选择 CSV 文件' : '选择 CSV 文件' }}</strong>
            <span>{{ selectedFile ? `已选择：${selectedFile.name}` : '点击此处上传，随后生成 ZIP 压缩包。' }}</span>
          </div>
        </label>

        <div class="status-row">{{ status }}</div>
        <div v-if="error" class="error-box">{{ error }}</div>

        <div class="action-row">
          <button class="btn-primary" :disabled="!selectedFile || loading" @click="runBatch">
            {{ loading ? '批量处理中…' : '开始批量排盘' }}
          </button>
        </div>

        <div class="hint-box">
          结果会下载为 ZIP，包含每个命盘的 JSON 输出与汇总文件。
        </div>
      </article>

      <aside class="card guide-card">
        <h2>操作说明</h2>
        <ol>
          <li>先下载模板，按列填入姓名、年月日时、性别与流年。</li>
          <li>上传 CSV 后，可按需填写模板版本。</li>
          <li>开始批量排盘后，等待 ZIP 下载完成。</li>
        </ol>
        <div class="guide-note">如果失败，优先检查 CSV 列名、时间范围和性别字段是否符合模板示例。</div>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.batch-view {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: var(--shadow-sm);
}

.hero {
  padding: 28px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.08), rgba(59, 130, 246, 0.08));
}

.hero-kicker {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #c2410c;
}

.hero-title {
  margin: 0;
  font-size: 30px;
  color: var(--text);
}

.hero-desc {
  margin: 12px 0 0;
  max-width: 720px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-2);
}

.hero-actions,
.action-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.info-card,
.editor-card,
.guide-card {
  padding: 20px;
}

.info-title,
.section-head h2,
.guide-card h2 {
  margin: 0;
  font-weight: 700;
  color: var(--text);
}

.info-desc,
.section-head p,
.guide-note,
.hint-box,
.status-row {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.workspace-grid {
  display: grid;
  grid-template-columns: 1.5fr .8fr;
  gap: 20px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.form-grid {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field span {
  font-size: 12px;
  color: var(--text-3);
}

.field-wide {
  max-width: 320px;
}

input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
}

.upload-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 132px;
  margin-top: 18px;
  padding: 16px;
  border: 1px dashed var(--border-md);
  border-radius: 14px;
  background: var(--bg);
  color: var(--text-2);
  cursor: pointer;
  text-align: center;
}

.file-input {
  display: none;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-box {
  margin-top: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff1f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 13px;
}

.hint-box {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #f8fafc;
}

.guide-card ol {
  margin: 14px 0 0;
  padding-left: 18px;
  color: var(--text-2);
  line-height: 1.9;
}

.guide-note {
  margin-top: 14px;
}

.btn-primary,
.btn-secondary {
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary {
  padding: 10px 16px;
  border: none;
  background: var(--accent);
  color: #fff;
}

.btn-primary:disabled {
  opacity: .65;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 16px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.86);
  color: var(--text);
}

@media (max-width: 960px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .batch-view {
    padding: 16px;
  }

  .hero,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .field-wide {
    max-width: none;
  }
}
</style>
