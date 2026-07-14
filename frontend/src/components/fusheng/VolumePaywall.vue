<script setup lang="ts">
import { computed, ref } from 'vue'
import type { LifeVolumeId } from '@/types/life-volume'
import { paywallCopyFor } from '@/constants/volumePaywall'
import { track } from '@/utils/analytics'
import { useAuthStore } from '@/stores/auth'
import { useEntitlementStore } from '@/stores/entitlement'
import { useFocusTrap } from '@/composables/useFocusTrap'

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
const rootRef = ref<HTMLElement | null>(null)

useFocusTrap(rootRef, {
  active: true,
  onEscape: () => {
    rootRef.value?.querySelector<HTMLElement>('[data-testid="volume-paywall-mock-unlock"]')?.focus()
  },
})

async function onMockUnlock() {
  track({
    event_type: 'volume_unlock_prompt',
    volume_id: String(props.volumeId),
    properties: { action: 'mock_unlock', sandbox: true },
  })
  // ENT-01：已登录必须 sandbox 成功才解锁；未登录仍允许本地演示 mock
  if (auth.isLoggedIn) {
    const plan =
      props.volumeId === 'vol5' || props.volumeId === 'vol6' ? 'full_book' : 'volume_pass'
    const ok = await entitlement.sandboxPurchase(plan)
    if (!ok) return
  }
  emit('mockUnlock')
}
</script>

<template>
  <aside
    ref="rootRef"
    class="volume-paywall"
    data-testid="volume-paywall"
    :data-volume-id="volumeId"
    role="dialog"
    aria-modal="true"
    :aria-label="`锁卷：${copy.need}`"
  >
    <div class="volume-paywall__seal" aria-hidden="true">锁</div>
    <div class="volume-paywall__body">
      <p class="volume-paywall__need">需{{ copy.need }}</p>
      <p class="volume-paywall__blurb">{{ detail?.trim() || copy.blurb }}</p>
      <p class="volume-paywall__hint">
        试读锁定。可用 Tab 在本区内切换；Esc 将焦点回到解锁按钮。
      </p>
      <button
        type="button"
        class="volume-paywall__cta"
        data-testid="volume-paywall-mock-unlock"
        :disabled="busy"
        @click="onMockUnlock"
      >
        {{ busy ? '开通中…' : copy.cta }}
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
  padding: 16px 18px;
  border: 1px solid var(--border-md, #d4c4a8);
  background: rgba(255, 250, 245, 0.72);
}

.volume-paywall__seal {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border: 1px solid var(--brand-cinnabar, #8b3a2a);
  color: var(--brand-cinnabar, #8b3a2a);
  font-family: var(--font-display, serif);
  font-size: 15px;
  letter-spacing: 0.12em;
}

.volume-paywall__need {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--brand-ink, #1a1410);
}

.volume-paywall__blurb {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-2);
}

.volume-paywall__hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--text-3);
}

.volume-paywall__cta {
  padding: 8px 14px;
  border: 1px solid var(--brand-gold-dark, #8b5e34);
  background: transparent;
  color: var(--brand-gold-dark, #8b5e34);
  font: inherit;
  cursor: pointer;
}

.volume-paywall__cta:disabled {
  opacity: 0.55;
  cursor: wait;
}

.volume-paywall__cta:focus-visible {
  outline: 2px solid var(--brand-gold, #b8894d);
  outline-offset: 2px;
}
</style>
