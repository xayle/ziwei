import { computed, ref, type ComputedRef, type Ref } from 'vue'

type UseWorkbenchGuideOptions = {
  simpleView: Ref<boolean>
  showNewbieGuide: Ref<boolean>
  isZiweiSection: ComputedRef<boolean>
}

type WorkbenchGuideStep = {
  title: string
  desc: string
}

type UseWorkbenchGuideReturn = {
  currentGuideStep: Ref<number>
  toggleSimpleView: () => void
  closeNewbieGuide: () => void
  clearGuideDemoTimers: () => void
  focusGuideStep: (step: number) => void
  goPrevGuideStep: () => void
  goNextGuideStep: () => void
  playGuideDemo: () => void
  guideProgressPercent: ComputedRef<string>
  newbieGuideSteps: ComputedRef<WorkbenchGuideStep[]>
}

export function useWorkbenchGuide(options: UseWorkbenchGuideOptions): UseWorkbenchGuideReturn {
  const currentGuideStep = ref(1)
  let guideDemoTimers: ReturnType<typeof setTimeout>[] = []

  function toggleSimpleView() {
    options.simpleView.value = !options.simpleView.value
    try {
      localStorage.setItem('workbench:simple-view', options.simpleView.value ? '1' : '0')
    } catch (_error) {
    }
  }

  function closeNewbieGuide() {
    options.showNewbieGuide.value = false
    try {
      localStorage.setItem('workbench:newbie-guide', '0')
    } catch (_error) {
    }
  }

  function flashGuideTarget(el: Element | null) {
    if (!(el instanceof HTMLElement)) return
    el.classList.remove('wb-guide-focus-target')
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    requestAnimationFrame(() => {
      el.classList.add('wb-guide-focus-target')
      setTimeout(() => el.classList.remove('wb-guide-focus-target'), 1800)
    })
  }

  function clearGuideDemoTimers() {
    guideDemoTimers.forEach(timer => clearTimeout(timer))
    guideDemoTimers = []
  }

  function focusGuideStep(step: number) {
    currentGuideStep.value = Math.min(3, Math.max(1, step))
    const root = document.querySelector('.wb-detail')
    if (!root) return

    if (step === 1) {
      flashGuideTarget(root.querySelector('.wb-chart-summary'))
      return
    }

    if (step === 2) {
      if (options.isZiweiSection.value) {
        flashGuideTarget(root.querySelector('.zw-layout'))
      } else {
        flashGuideTarget(root.querySelector('.wb-pillar-table-wrap'))
      }
      return
    }

    flashGuideTarget(root.querySelector('.wb-info-actions'))
  }

  function goPrevGuideStep() {
    if (currentGuideStep.value <= 1) return
    focusGuideStep(currentGuideStep.value - 1)
  }

  function goNextGuideStep() {
    if (currentGuideStep.value >= 3) return
    focusGuideStep(currentGuideStep.value + 1)
  }

  function playGuideDemo() {
    clearGuideDemoTimers()
    currentGuideStep.value = 1
    ;[1, 2, 3].forEach((step, idx) => {
      const timer = setTimeout(() => focusGuideStep(step), idx * 1100)
      guideDemoTimers.push(timer)
    })
  }

  const guideProgressPercent = computed<string>(() => `${(currentGuideStep.value / 3) * 100}%`)

  const newbieGuideSteps = computed<WorkbenchGuideStep[]>(() => {
    if (options.isZiweiSection.value) {
      return [
        {
          title: '先看哪里',
          desc: '先看顶部四张速览卡：命宫/身宫、五行局、当前大限与本月流月。先建立全局判断。',
        },
        {
          title: '再点哪里',
          desc: '再点“十二宫与主星”里的任一宫位，右侧会展开该宫主星、对宫、四化飞出/流入关系。',
        },
        {
          title: '最后做什么',
          desc: '最后用右上“重算/完整报告书/PDF”输出结论；不确定时切到“完整视图”补看细节。',
        },
      ]
    }

    return [
      {
        title: '先看哪里',
        desc: '先看顶部四张速览卡：当前大运、当年流年、本月流月、五行平衡分。先抓主线。',
      },
      {
        title: '再点哪里',
        desc: '再点“四柱表”的年/月/日/时柱，查看该柱藏干、纳音和神煞；再看大运与流年时间轴。',
      },
      {
        title: '最后做什么',
        desc: '最后根据建议执行“重算/完整报告书/PDF导出”；想深挖时切到“完整视图”。',
      },
    ]
  })

  return {
    currentGuideStep,
    toggleSimpleView,
    closeNewbieGuide,
    clearGuideDemoTimers,
    focusGuideStep,
    goPrevGuideStep,
    goNextGuideStep,
    playGuideDemo,
    guideProgressPercent,
    newbieGuideSteps,
  }
}
