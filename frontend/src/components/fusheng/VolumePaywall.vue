<script setup lang="ts">
import { computed } from 'vue'
import type { LifeVolumeId } from '@/types/life-volume'
import { paywallCopyFor } from '@/constants/volumePaywall'
import { track } from '@/utils/analytics'
import { useAuthStore } from '@/stores/auth'
import { useEntitlementStore } from '@/stores/entitlement'

const props = defineProps<{
  volumeId: LifeVolumeId | string
  /** BE locked 节文案；有则覆盖默认 blurb */
  detail?: string | null
}>()

const emit = defineEmits<{
  mockUnlock: []
}>()

const auth = useAuthStore()
const entitlement = useEntitlementStore()
const copy = computed(() => paywallCopyFor(props.volumeId))
const busy = computed(() => entitlement.loading)

async function onMockUnlock() {
  track({
    event_type: 'volume_unlock_prompt',
    volume_id: String(props.volumeId),
    properties: { action: 'mock_unlock', sandbox: true },
  })
  if (auth.isLoggedIn) {
    const plan =
      props.volumeId === 'vol5' || props.volumeId === 'vol6' ? 'full_book' : 'volume_pass'
    await entitlement.sandboxPurchase(plan)
  }
  emit('mockUnlock')
}
</script>

<template>
  <aside
    class="volume-paywall"
    data-testid="volume-paywall"
    :data-volume-id="volumeId"
    role="region"
    :aria-label="`${volumeId} 未解锁`"
  >
    <div class="volume-paywall__seal" aria-hidden="true">锁</div>
    <div class="volume-paywall__body">
      <p class="volume-paywall__need">需{{ copy.need }}</p>
      <p class="volume-paywall__blurb">{{ detail?.trim() || copy.blurb }}</p>
      <p class="volume-paywall__hint">
        {{ auth.isLoggedIn ? '将调用沙箱支付写入权益（T093/T094）。' : '未登录：仅本会话模拟解锁。' }}
      </p>
      <button
        type="button"
        class="volume-paywall__cta"
        data-testid="volume-paywall-mock-unlock"
        :disabled="busy"
        @click="onMockUnlock"
      >
        {{ busy ? '处理中…' : copy.cta }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.volume-paywall {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: start;
  margin: 12px 0 8px;
  padding: 16px 14px;
  border: 1px solid var(--border-md, #d4c4a8);
  border-left: 3px solid var(--brand-cinnabar, #8b3a2a);
  background: var(--surface, #fffaf5);
  max-width: 100%;
  box-sizing: border-box;
}

.volume-paywall__seal {
  width: 2.25rem;
  height: 2.25rem;
  display: grid;
  place-items: center;
  border: 1px solid var(--brand-cinnabar, #8b3a2a);
  color: var(--brand-cinnabar, #8b3a2a);
  font-family: var(--font-display, "LXGW Neo ZhiSong", serif);
  font-size: 0.95rem;
  letter-spacing: 0.12em;
  flex-shrink: 0;
}

.volume-paywall__need {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--brand-ink, #1a1410);
}

.volume-paywall__blurb {
  margin: 0.45rem 0 0;
  font-size: 0.9rem;
  line-height: 1.65;
  color: var(--brand-mist, #6b5d4f);
}

.volume-paywall__hint {
  margin: 0.55rem 0 0;
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--text-3, #9a8b7a);
}

.volume-paywall__cta {
  margin-top: 0.85rem;
  padding: 0.55rem 0.9rem;
  border: 1px solid var(--brand-gold-dark, #8b5e34);
  background: transparent;
  color: var(--brand-gold-dark, #8b5e34);
  font: inherit;
  font-size: 0.88rem;
  letter-spacing: 0.06em;
  cursor: pointer;
}

.volume-paywall__cta:focus-visible {
  outline: 2px solid var(--brand-gold, #b8894d);
  outline-offset: 2px;
}
</style>
