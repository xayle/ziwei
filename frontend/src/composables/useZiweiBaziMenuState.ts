/**
 * useZiweiBaziMenuState.ts — 八字分析子菜单本地状态
 *
 * 提供：
 *  - baziMenuActive     当前激活的八字分析子菜单 key
 *  - baziDayunFocusIdx  聚焦大运索引（-1 表示无聚焦）
 *  - baziCopyDone       复制成功的短暂标记
 *  - baziMenuItems      菜单项定义（readonly 常量）
 */
import { ref } from 'vue'

export type BaziMenuKey =
  | 'shengchen' | 'sizhu'     | 'ribuzhu'    | 'wuxing'
  | 'canggan'   | 'shenshai'  | 'chonghehexpo' | 'geju'
  | 'dayun'     | 'shishen'

export const BAZI_MENU_ITEMS = {
  'shengchen':     '1.1 生辰数据',
  'sizhu':         '1.2 四柱基础',
  'ribuzhu':       '1.3 日主与十神',
  'wuxing':        '1.4 五行分析',
  'canggan':       '1.5 藏干/纳音/生肖',
  'shenshai':      '1.6 神煞与定位',
  'chonghehexpo':  '1.7 冲合刑破',
  'geju':          '1.8 格局判定与用神',
  'dayun':         '1.9 大运/流年/流月',
  'shishen':       '1.10 十神宫位用法',
} as const

export function useZiweiBaziMenuState() {
  const baziMenuActive    = ref<BaziMenuKey>('sizhu')
  const baziDayunFocusIdx = ref<number>(-1)
  const baziCopyDone      = ref(false)

  return {
    baziMenuActive,
    baziDayunFocusIdx,
    baziCopyDone,
    baziMenuItems: BAZI_MENU_ITEMS,
  }
}
