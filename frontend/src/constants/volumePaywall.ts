/** 卷锁定态与付费墙文案（FE-GTM-03 / T092） */

import type { LifeVolumeId } from '@/types/life-volume'

export const VOLUME_LOCK_DEMO_STORAGE_KEY = 'fusheng-demo-volume-locks'

export type VolumePaywallCopy = {
  need: string
  blurb: string
  cta: string
}

const DEFAULT_COPY: VolumePaywallCopy = {
  need: '更高权益',
  blurb: '本卷全文需解锁后方可阅读。当前为试读锁定态。',
  cta: '模拟解锁（沙箱）',
}

export const VOLUME_PAYWALL_BY_ID: Partial<Record<LifeVolumeId, VolumePaywallCopy>> = {
  vol2: {
    need: '读卷 Pass',
    blurb: '卷二·业之象需读卷 Pass。建档后可先阅卷一；此处为锁定预览。',
    cta: '模拟开通读卷 Pass',
  },
  vol3: {
    need: '读卷 Pass',
    blurb: '卷三·运之波含大运与流年细目，需读卷 Pass 后方可展全文。',
    cta: '模拟开通读卷 Pass',
  },
  vol4: {
    need: '读卷 Pass',
    blurb: '卷四·宫之图含紫微宫盘细读，需读卷 Pass。',
    cta: '模拟开通读卷 Pass',
  },
  vol5: {
    need: '全书权益',
    blurb: '卷五·事之理为推断层详析，需全书权益（full_book）。',
    cta: '模拟开通全书',
  },
  vol6: {
    need: '全书权益',
    blurb: '卷六·问书含主动展开的问答与批注空间，需全书权益。',
    cta: '模拟开通全书',
  },
}

export function paywallCopyFor(volumeId: LifeVolumeId | string): VolumePaywallCopy {
  return VOLUME_PAYWALL_BY_ID[volumeId as LifeVolumeId] ?? DEFAULT_COPY
}

/** E2E / 本地演示：localStorage=1 时强制锁 vol2–vol6（不改 BE） */
export function demoVolumeLocksEnabled(): boolean {
  try {
    return localStorage.getItem(VOLUME_LOCK_DEMO_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export const DEMO_LOCKED_VOLUME_IDS: LifeVolumeId[] = ['vol2', 'vol3', 'vol4', 'vol5', 'vol6']
