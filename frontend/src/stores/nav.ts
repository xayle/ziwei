/**
 * stores/nav.ts — 导航树状态管理
 * 管理当前展开的章节、选中的小节
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { NAV_CHAPTERS, findChapterBySection, findSection, type NavChapter, type NavSection } from '@/data/navTree'

export const useNavStore = defineStore('nav', () => {
  // 当前展开的章节 id（手风琴：只允许一个展开）
  const expandedChapterId = ref<string | null>(null)

  // 当前选中的小节 id
  const currentSectionId = ref<string | null>(null)

  // 当前选中的小节对象
  const currentSection = computed<NavSection | undefined>(() =>
    currentSectionId.value ? findSection(currentSectionId.value) : undefined
  )

  // 当前选中小节所属章节对象
  const currentChapter = computed<NavChapter | undefined>(() =>
    currentSectionId.value ? findChapterBySection(currentSectionId.value) : undefined
  )

  /** 切换章节展开/折叠（手风琴） */
  function toggleChapter(id: string) {
    expandedChapterId.value = expandedChapterId.value === id ? null : id
  }

  /** 选中小节，自动展开所属章节 */
  function selectSection(sectionId: string) {
    currentSectionId.value = sectionId
    const ch = findChapterBySection(sectionId)
    if (ch) expandedChapterId.value = ch.id
  }

  /** 按路由 path 推断默认激活的章节（用于页面初始化） */
  function initFromRoute(routePath: string) {
    // 找到第一个 route 匹配的小节
    for (const ch of NAV_CHAPTERS) {
      for (const sec of ch.sections) {
        if (routePath.startsWith(sec.route ?? '')) {
          const selectedChapter = currentSectionId.value
            ? findChapterBySection(currentSectionId.value)
            : undefined

          // 默认行为：
          // 1) 未选中任何小节时，自动落到当前章节第一个小节
          // 2) 路由切换到新章节时，自动切到该章节第一个小节
          if (!currentSectionId.value || selectedChapter?.id !== ch.id) {
            currentSectionId.value = sec.id
          }
          expandedChapterId.value = ch.id
          return
        }
      }
    }
  }

  return {
    expandedChapterId,
    currentSectionId,
    currentSection,
    currentChapter,
    toggleChapter,
    selectSection,
    initFromRoute,
    NAV_CHAPTERS,
  }
})
