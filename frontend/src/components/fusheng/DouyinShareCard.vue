<script setup lang="ts">
import { computed, ref } from 'vue'
import { downloadCaseShareCard, saveShareCardPng } from '@/api/exportCard'
import { mintH5PreviewToken } from '@/api/auth'
import { copyTextToClipboard } from '@/utils/copyText'
import { track } from '@/utils/analytics'

const props = withDefaults(
  defineProps<{
    brand?: string
    volumeTitle: string
    factLines: string[]
    gejuLine?: string | null
    disclaimer?: string | null
    /** 有 case 时可调用 BE 导出 PNG / 签发 H5 试读 */
    caseId?: string | null
    source?: string
  }>(),
  {
    brand: '浮生',
    gejuLine: null,
    disclaimer: '传统文化与自我认知参考，非命运断言。',
    caseId: null,
    source: 'report',
  },
)

const exporting = ref(false)
const exportError = ref('')
const exportOk = ref(false)

const minting = ref(false)
const mintStatus = ref('')

const lines = computed(() => props.factLines.filter((t) => t.trim()).slice(0, 4))
const canExport = computed(() => Boolean(props.caseId?.trim()))

function buildLandingPreviewUrl(caseId: string, token: string): string {
  const url = new URL(`${window.location.origin}/landing`)
  url.searchParams.set('case_id', caseId)
  url.searchParams.set('token', token)
  return url.toString()
}

async function onExport() {
  const id = props.caseId?.trim()
  if (!id || exporting.value) return
  exporting.value = true
  exportError.value = ''
  exportOk.value = false
  try {
    const blob = await downloadCaseShareCard(id, 'douyin')
    saveShareCardPng(blob, '浮生-douyin-分享卡')
    exportOk.value = true
    track({
      event_type: 'share_card_export',
      case_id: id,
      properties: {
        layout: 'douyin',
        source: props.source,
        fact_count: lines.value.length,
      },
    })
  } catch {
    exportError.value = '导出失败，请稍后重试。'
  } finally {
    exporting.value = false
  }
}

/** SHARE-02：签发短 token 并复制落地页试读链接 */
async function onMintPreviewLink() {
  const id = props.caseId?.trim()
  if (!id || minting.value) return
  minting.value = true
  mintStatus.value = ''
  try {
    const minted = await mintH5PreviewToken(id)
    const link = buildLandingPreviewUrl(minted.case_id || id, minted.access_token)
    const ok = await copyTextToClipboard(link)
    mintStatus.value = ok
      ? `试读链接已复制（约 ${Math.round(minted.expires_in / 60)} 分钟有效）`
      : `复制失败，请手动复制：${link}`
    track({
      event_type: 'funnel_step',
      case_id: id,
      properties: {
        step: 'h5_preview_mint',
        source: props.source,
        expires_in: minted.expires_in,
      },
    })
  } catch {
    mintStatus.value = '签发失败：请确认已登录且档案已同步云端。'
  } finally {
    minting.value = false
  }
}
</script>

<template>
  <section
    class="douyin-share"
    data-testid="douyin-share-card"
    aria-label="抖音竖版分享预览"
  >
    <header class="douyin-share__head">
      <div>
        <p class="douyin-share__kicker">竖版分享 · 9:16</p>
        <p class="douyin-share__hint">纸纹底 · 卷名 · 事实句</p>
      </div>
      <div class="douyin-share__actions">
        <button
          v-if="canExport"
          type="button"
          class="douyin-share__export"
          data-testid="douyin-share-export"
          :disabled="exporting"
          @click="onExport"
        >
          {{ exporting ? '导出中…' : exportOk ? '已导出 PNG' : '导出 PNG' }}
        </button>
        <button
          v-if="canExport"
          type="button"
          class="douyin-share__export"
          data-testid="douyin-h5-preview-mint"
          :disabled="minting"
          @click="onMintPreviewLink"
        >
          {{ minting ? '签发中…' : '复制试读链接' }}
        </button>
        <p v-else class="douyin-share__export-hint">登录建档后可导出 PNG / 试读链接</p>
      </div>
    </header>

    <p
      v-if="mintStatus"
      class="douyin-share__mint-status"
      role="status"
      aria-live="polite"
      data-testid="douyin-h5-preview-status"
    >
      {{ mintStatus }}
    </p>

    <div class="douyin-share__stage">
      <article class="douyin-card" data-testid="douyin-share-preview" aria-hidden="true">
        <p class="douyin-card__brand">{{ brand }}</p>
        <p class="douyin-card__tag">人生六卷 · 命书可读</p>
        <p class="douyin-card__volume">{{ volumeTitle }}</p>
        <p v-if="gejuLine" class="douyin-card__geju">格局 · {{ gejuLine }}</p>
        <ul class="douyin-card__facts">
          <li v-for="(line, i) in lines" :key="i">{{ line }}</li>
          <li v-if="!lines.length">命盘事实已就绪，展开六卷可读细节。</li>
        </ul>
        <p v-if="disclaimer" class="douyin-card__disclaimer">{{ disclaimer }}</p>
      </article>
    </div>

    <p v-if="exportError" class="douyin-share__error" data-testid="douyin-share-error">
      {{ exportError }}
    </p>
  </section>
</template>

<style scoped>
.douyin-share {
  margin: 1.25rem 0 1.5rem;
  padding: 1rem 0.9rem 1rem;
  border-top: 1px solid var(--border-md, #d4c4a8);
  border-bottom: 1px solid var(--border-md, #d4c4a8);
  max-width: 100%;
  box-sizing: border-box;
}

.douyin-share__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.douyin-share__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  justify-content: flex-end;
  align-items: flex-start;
}

.douyin-share__kicker {
  margin: 0;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  color: var(--brand-mist, #6b5d4f);
}

.douyin-share__hint {
  margin: 0.2rem 0 0;
  font-size: 0.85rem;
  color: var(--brand-ink, #1a1410);
  letter-spacing: 0.04em;
}

.douyin-share__export {
  flex-shrink: 0;
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--brand-gold-dark, #8b5e34);
  background: transparent;
  color: var(--brand-gold-dark, #8b5e34);
  font: inherit;
  font-size: 0.8rem;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.douyin-share__export:disabled {
  opacity: 0.55;
  cursor: wait;
}

.douyin-share__export:focus-visible {
  outline: 2px solid var(--brand-gold, #b8894d);
  outline-offset: 2px;
}

.douyin-share__export-hint {
  margin: 0;
  font-size: 0.72rem;
  color: var(--text-3, #9a8b7a);
  max-width: 9rem;
  text-align: right;
  line-height: 1.4;
}

.douyin-share__mint-status {
  margin: 0 0 0.75rem;
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--brand-mist, #6b5d4f);
  word-break: break-all;
}

.douyin-share__stage {
  display: flex;
  justify-content: center;
}

/* 预览按 9:16 缩放，不占满屏 */
.douyin-card {
  width: min(100%, 270px);
  aspect-ratio: 9 / 16;
  box-sizing: border-box;
  padding: 1.35rem 1.1rem 1rem;
  display: flex;
  flex-direction: column;
  color: var(--brand-ink, #1a1410);
  border: 1px solid var(--border-md, #d4c4a8);
  background-color: var(--brand-paper, #f5f0e6);
  background-image: radial-gradient(
    ellipse 90% 55% at 50% -5%,
    rgba(184, 137, 77, 0.14),
    transparent 55%
  );
  font-family: var(--font-display, "LXGW Neo ZhiSong", serif);
  overflow: hidden;
}

.douyin-card__brand {
  margin: 0;
  font-size: 1.45rem;
  letter-spacing: 0.28em;
  font-weight: 600;
}

.douyin-card__tag {
  margin: 0.35rem 0 0;
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  color: var(--brand-mist, #6b5d4f);
}

.douyin-card__volume {
  margin: 1.35rem 0 0;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  border-left: 3px solid var(--brand-cinnabar, #8b3a2a);
  padding-left: 0.55rem;
  line-height: 1.35;
}

.douyin-card__geju {
  margin: 0.55rem 0 0;
  font-size: 0.72rem;
  color: var(--brand-gold-dark, #8b5e34);
  letter-spacing: 0.06em;
}

.douyin-card__facts {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
  flex: 1;
}

.douyin-card__facts li {
  margin: 0 0 0.55rem;
  font-size: 0.78rem;
  line-height: 1.55;
  letter-spacing: 0.03em;
}

.douyin-card__facts li::before {
  content: "·";
  color: var(--brand-gold, #b8894d);
  margin-right: 0.3rem;
}

.douyin-card__disclaimer {
  margin-top: auto;
  padding-top: 0.65rem;
  border-top: 1px solid var(--border-md, #d4c4a8);
  font-size: 0.58rem;
  line-height: 1.45;
  color: var(--text-3, #9a8b7a);
}

.douyin-share__error {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
  color: var(--brand-cinnabar, #8b3a2a);
}
</style>
