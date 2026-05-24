<script setup lang="ts">
import PlannedModulePage from '@/components/PlannedModulePage.vue'

const milestones = [
  {
    title: '当前定位',
    text: '人类设计暂时作为独立预留区存在，不再混入案例中心，避免案例页继续膨胀成超级页。',
  },
  {
    title: '后续承接',
    text: '未来会承接类型、权限、中心与策略说明，并与案例、AI 草稿、术语词库形成联动。',
  },
  {
    title: '现在可做',
    text: '如果当前任务是阅读命盘或整理案例，请先进入八字、紫微或案例中心。',
  },
]

const roadmap = [
  {
    phase: 'Phase 1',
    title: '建立独立工作区',
    text: '先把人类设计从案例中心剥离，明确它是未来独立模块，而不是混在现有命盘页里的附属说明。',
  },
  {
    phase: 'Phase 2',
    title: '补齐基础阅读层',
    text: '接入类型、策略、权威、定义方式与中心说明，先解决“怎么看”和“先理解什么”。',
  },
  {
    phase: 'Phase 3',
    title: '联动案例与 AI',
    text: '把人类设计结果与案例库、术语词库、AI 草稿连接起来，形成完整的阅读与输出链路。',
  },
]

const prepChecklist = [
  '先准备好出生时间、地点与时区，避免后续工作区上线后仍要回头补资料。',
  '先在术语词库里建立基础阅读习惯，后续切入类型、权威和中心时会更顺。',
  '如果当前目标是出结论或写报告，先从八字、紫微和案例中心推进现阶段任务。',
]

const heroActions = [
  {
    label: '去案件枢纽',
    to: '/cases',
    tone: 'primary' as const,
  },
  {
    label: '去八字分析',
    to: '/bazi',
    tone: 'secondary' as const,
  },
]

const relatedModules = [
  {
    label: '案例中心',
    description: '先完成案件选择、资料校对和后续工作流分发。',
    to: '/cases',
  },
  {
    label: '八字工作区',
    description: '当前最完整的阅读型分析页，适合承接命盘理解任务。',
    to: '/bazi',
  },
  {
    label: '紫微主盘页',
    description: '适合查看主星、宫位和时间线结构。',
    to: '/ziwei',
  },
]

const nextActions = [
  {
    label: '返回案件枢纽',
    description: '先整理案例、选择对象，再进入专项分析页。',
    to: '/cases',
  },
  {
    label: '进入八字页',
    description: '需要完整命盘阅读时，优先从八字概览开始。',
    to: '/bazi',
  },
  {
    label: '打开术语词库',
    description: '先建立术语理解，再回到具体命盘阅读。',
    to: '/glossary',
  },
]
</script>

<template>
  <PlannedModulePage
    title="人类设计工作区"
    description="这里保留为独立模块入口，用来承接后续的人类设计能力。当前版本先不把未完成内容塞回案例中心，而是明确标记为预留区。"
    :hero-actions="heroActions"
    :milestones="milestones"
    :roadmap="roadmap"
    :prep-checklist="prepChecklist"
    :related-modules="relatedModules"
    :next-actions="nextActions"
  />
</template>
