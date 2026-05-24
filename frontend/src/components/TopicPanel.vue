<script setup lang="ts">
/**
 * TopicPanel.vue — 右侧阅读辅助面板
 * 显示：摘要 | 当前案例上下文 | 本节看点 | 阅读顺序 | 下一步动作 | AI 解释
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNavStore } from '@/stores/nav'
import { useAiStore } from '@/stores/ai'
import type { CaseOut } from '@/api/report'
import { useReportStore } from '@/stores/report'

type QuickAction = 'adjust' | 'copy' | 'export' | 'share' | 'notes' | 'calendar' | 'compare' | 'bookmarks'
type ActionTone = 'primary' | 'neutral' | 'ghost'

interface NextAction {
  label: string
  route?: string
  sectionId?: string
  tone?: ActionTone
  command?: 'ask-ai'
}

interface SectionGuide {
  title: string
  summary: string
  highlights: string[]
  readingSteps: string[]
  helper?: string
  caution?: string
  caseRequired?: boolean
  nextActions: NextAction[]
}

const router = useRouter()
const nav = useNavStore()
const ai = useAiStore()
const store = useReportStore()

const section = computed(() => nav.currentSection)
const chapter = computed(() => nav.currentChapter)
const selectedCase = computed<CaseOut | null>(() => {
  const caseId = ai.currentCaseId
  return store.caseList.find((item) => item.id === caseId) ?? null
})
const currentRoutePath = computed(() => router.currentRoute.value.path)
const reportRoute = computed(() => selectedCase.value ? `/report/${selectedCase.value.id}` : '/report')

const accentStyle = computed(() => ({ '--topic-accent': chapter.value?.color ?? 'var(--color-brand)' }))

const caseContextItems = computed(() => {
  const item = selectedCase.value
  if (!item) return []
  return [
    { label: '姓名', value: item.name || '未命名案例' },
    { label: '性别', value: formatGender(item.gender) },
    { label: '出生地', value: item.city || '待补充' },
    { label: '出生时间', value: formatDateTime(item.birth_dt_local) },
    { label: '时区', value: item.tz || '待补充' },
    { label: '真太阳时', value: item.solar_time_enabled ? '已启用' : '未启用' },
  ]
})

const sectionGuide = computed<SectionGuide | null>(() => {
  if (!section.value) return null
  return buildGuide(section.value.id, section.value.label, section.value.route)
})

function formatGender(gender: string | null | undefined): string {
  if (gender === 'male') return '男'
  if (gender === 'female') return '女'
  return '未填写'
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '待补充'
  return value.slice(0, 16).replace('T', ' ')
}

function emitQuickAction(action: QuickAction) {
  window.dispatchEvent(new CustomEvent<QuickAction>('ziwei:quick-action', { detail: action }))
}

function makeAction(label: string, route?: string, sectionId?: string, tone: ActionTone = 'neutral', command?: 'ask-ai'): NextAction {
  return { label, route, sectionId, tone, command }
}

function moduleLabel(route: string): string {
  switch (route) {
    case '/cases': return '案例中心'
    case '/bazi': return '八字工作区'
    case '/ziwei': return '紫微主盘'
    case '/name': return '姓名学工作区'
    case '/zeri': return '择日工作区'
    case '/fengshui': return '风水工作区'
    case '/compat': return '合婚工作区'
    case '/compat/synastry': return '合盘工作区'
    case '/western': return '西方占星工作区'
    case '/numerology': return '数字学工作区'
    case '/tarot': return '塔罗工作区'
    case '/report': return '报告工作区'
    case '/llm/drafts': return 'AI 草稿工作区'
    case '/admin': return '管理后台'
    default: return '对应模块'
  }
}

function genericGuide(label: string, route: string): SectionGuide {
  const moduleName = moduleLabel(route)
  return {
    title: `${label}阅读提示`,
    summary: `这一节更适合承担“解释你现在看到什么、先看什么、下一步去哪”的工作，而不是继续堆叠功能说明。`,
    highlights: [
      '先确认页面正在展示的主结论，再看支撑该结论的数据与标签。',
      '把本节理解成一个过渡层：它负责帮你定位模块，不负责承载全部分析。',
      '如果你已经明确目标，可以直接进入对应工作区继续处理。',
    ],
    readingSteps: [
      '先看页面顶部摘要，确认本节处理的问题是什么。',
      '再看当前页面提供的核心图表或卡片，抓住一条主线。',
      `最后进入${moduleName}，完成编辑、比对、导出或审核。`,
    ],
    helper: '右栏现在优先承担“阅读辅助”和“动作分发”，不再重复页面主体内容。',
    nextActions: [
      makeAction(`进入${moduleName}`, route, undefined, 'primary'),
      makeAction('查看报告视角', reportRoute.value),
    ],
  }
}

function buildGuide(sectionId: string, label: string, route: string): SectionGuide {
  switch (sectionId) {
    case 'bazi-birth':
      return {
        title: '先确认输入，再开始解读',
        summary: '命理分析的第一步不是直接看结论，而是确认出生时间、地点、时区和真太阳时处理是否可靠。基础输入不稳，后面的推演都会偏。',
        highlights: [
          '出生时间优先核对到分钟，至少明确是否存在时辰不确定。',
          '出生地、经纬度和时区共同影响换日、节气与真太阳时。',
          '如果当前案例资料仍不完整，应先回到案例中心补录。',
        ],
        readingSteps: [
          '先核对姓名、性别、出生地和本地出生时间。',
          '再确认时区、经度与真太阳时是否启用。',
          '确认无误后，再进入八字页查看四柱、五行与流年。',
        ],
        helper: '这一节主要解决“盘算得准不准”的前置问题。',
        caution: '未选中案例时，右栏只提供阅读指引，不应假装展示分析结果。',
        caseRequired: true,
        nextActions: [
          makeAction('返回案例中心补充资料', '/cases', 'bazi-birth', 'primary'),
          makeAction('进入八字工作区', '/bazi'),
          makeAction('查看报告草稿', reportRoute.value),
        ],
      }
    case 'bazi-pillars':
      return {
        title: '先看四柱骨架，再理解日主位置',
        summary: '四柱决定命盘的基本结构。这里最重要的不是把术语全部背下来，而是先看年、月、日、时四柱如何分工，再看日主处在什么环境中。',
        highlights: [
          '月柱通常更接近整体气候与环境背景。',
          '日柱最靠近自我核心，日主判断从这里展开。',
          '四柱之间的对应关系，要结合后续五行和十神一起看。',
        ],
        readingSteps: [
          '先看四柱干支排列，建立命盘骨架。',
          '再看日主强弱提示，避免单看某一柱下结论。',
          '最后进入八字页，对照十神和五行分布继续读。',
        ],
        helper: '如果你只记一件事：日主不是孤立看的，要放在四柱结构里理解。',
        caseRequired: true,
        nextActions: [
          makeAction('进入八字工作区', '/bazi', undefined, 'primary'),
          makeAction('回到生辰数据复核', '/cases', 'bazi-birth'),
          makeAction('生成报告草稿', reportRoute.value),
        ],
      }
    case 'bazi-wuxing':
      return {
        title: '五行不是“缺什么补什么”那么简单',
        summary: '五行阅读重点是看分布、旺衰和平衡度，不是只看数量。强弱关系、时令环境与藏干支撑，决定了用神判断是否成立。',
        highlights: [
          '看“失衡方向”比看“数量多少”更重要。',
          '藏干会改变表层五行的真实力量。',
          '用神建议应和格局、流年联动，不宜单独断。',
        ],
        readingSteps: [
          '先看五行分布图，识别明显偏强或偏弱。',
          '再看藏干、纳音、生肖等补充信息。',
          '最后带着问题进入八字页验证用神与建议。',
        ],
        helper: '右栏负责把“怎么读图”说清楚，而不是替代图表本身。',
        caseRequired: true,
        nextActions: [
          makeAction('查看八字概览', '/bazi', undefined, 'primary'),
          makeAction('转到格局与流年', '/cases', 'bazi-dayun'),
          makeAction('打开报告视角', reportRoute.value),
        ],
      }
    case 'bazi-shensha':
      return {
        title: '神煞适合辅助判断，不应压过主结构',
        summary: '神煞、冲合这类信息更像“提醒层”，适合帮助你发现显著事件点、风险点和易感方向，但不宜覆盖四柱、日主、五行这些主结构。',
        highlights: [
          '先看是否与主结构结论一致，再决定权重。',
          '神煞更适合做提示、分层和注记。',
          '涉及流年冲克时，要结合时间轴阅读。',
        ],
        readingSteps: [
          '先找出最强的吉凶标签与冲合关系。',
          '再判断它们是否改变主结论，还是仅作提醒。',
          '最后把这些提示带入流年或报告表达里。',
        ],
        helper: '把神煞当作辅助证据层，阅读会更稳定。',
        caseRequired: true,
        nextActions: [
          makeAction('进入八字工作区', '/bazi', undefined, 'primary'),
          makeAction('继续看格局与流年', '/cases', 'bazi-dayun'),
          makeAction('用 AI 解释本节', undefined, undefined, 'ghost', 'ask-ai'),
        ],
      }
    case 'bazi-dayun':
      return {
        title: '把结论放到时间轴里，才更接近可行动建议',
        summary: '格局、用神和流年价值最高的地方，在于把静态命盘转成动态阶段判断。这里要关注的是“什么时候更明显”“哪些主题正在增强”。',
        highlights: [
          '先看大运阶段，再看流年细化。',
          '判断建议时要回到事业、关系、健康等现实主题。',
          '这部分最适合沉淀成报告摘要与行动建议。',
        ],
        readingSteps: [
          '先确认格局与用神结论。',
          '再看大运时间轴中的阶段变化。',
          '最后提炼成报告短答或咨询建议。',
        ],
        helper: '如果你准备出报告，这一节通常是最有表达价值的部分。',
        caseRequired: true,
        nextActions: [
          makeAction('进入八字工作区', '/bazi', undefined, 'primary'),
          makeAction('直接查看报告', reportRoute.value),
          makeAction('回案例中心总览', '/cases'),
        ],
      }
    case 'ziwei-palaces':
      return {
        title: '先读宫位结构，再看星曜细节',
        summary: '紫微主盘阅读建议先抓宫位骨架：命宫、身宫和十二宫分布决定了主视角。先有结构，再看每颗星怎么落进去。',
        highlights: [
          '命宫负责核心气质，身宫帮助理解行为重心。',
          '先建立十二宫心智，再深入宫内星曜。',
          '宫位层适合做总览，不宜一开始就陷入碎片化解释。',
        ],
        readingSteps: [
          '先看命宫、身宫与十二宫分布。',
          '再进入主盘，对照每宫核心标签。',
          '最后结合星曜详情解释重点宫位。',
        ],
        helper: '紫微阅读顺序很重要，顺序错了就容易被细节淹没。',
        caseRequired: true,
        nextActions: [
          makeAction('进入紫微主盘', '/ziwei', undefined, 'primary'),
          makeAction('继续看星曜详情', '/ziwei', 'ziwei-stars'),
          makeAction('查看紫微案例区', '/ziwei/cases'),
        ],
      }
    case 'ziwei-stars':
      return {
        title: '星曜解释要回到落宫场景里',
        summary: '单独背星曜意义帮助有限。真正有用的是：这颗星落在什么宫、与哪些星互动、它对当前主题产生什么倾向。',
        highlights: [
          '主星先看稳定主轴，辅星再看修饰。',
          '化曜更适合做趋势判断与提醒。',
          '同一颗星在不同宫位的表现差异很大。',
        ],
        readingSteps: [
          '先看当前主题对应的宫位。',
          '再读主星、辅星与化曜提示。',
          '最后回到主盘确认这些解释是否相互支持。',
        ],
        caseRequired: true,
        nextActions: [
          makeAction('进入紫微主盘', '/ziwei', undefined, 'primary'),
          makeAction('继续看宫位关系', '/ziwei', 'ziwei-relations'),
          makeAction('生成报告摘要', reportRoute.value),
        ],
      }
    case 'ziwei-relations':
      return {
        title: '关系线比单点更重要',
        summary: '会照、对冲、宫斗这些内容的价值，在于帮助你理解命盘内部是如何互相拉扯、放大或抵消的。这里重点不是点，而是线。',
        highlights: [
          '优先关注对命宫、事业、关系等主题影响最大的连线。',
          '把关系线理解成结构张力，而不是单独凶吉判断。',
          '读到明显冲突时，要回主盘确认是否还有辅助星化解。',
        ],
        readingSteps: [
          '先锁定当前最关键的宫位。',
          '再看它与对宫、三方四正的关系。',
          '最后沉淀为一条可复述的关系判断。',
        ],
        caseRequired: true,
        nextActions: [
          makeAction('进入紫微主盘', '/ziwei', undefined, 'primary'),
          makeAction('查看紫微格局与流年', '/ziwei', 'ziwei-gejv'),
          makeAction('打开 AI 对话', '/llm/drafts'),
        ],
      }
    case 'ziwei-gejv':
      return {
        title: '把紫微结构转成阶段判断',
        summary: '格局与流年部分负责把主盘解读转换成阶段性变化、机会点和波动点，是从“懂盘”过渡到“能给建议”的关键。',
        highlights: [
          '先有盘面主轴，再读大限和流年。',
          '阶段性判断更适合形成咨询话术。',
          '高波动年份应附带风险和边界提示。',
        ],
        readingSteps: [
          '先复述当前格局主结论。',
          '再看大限与流年对应的变化。',
          '最后输出建议、报告或后续跟进事项。',
        ],
        caseRequired: true,
        nextActions: [
          makeAction('进入紫微主盘', '/ziwei', undefined, 'primary'),
          makeAction('查看报告', reportRoute.value),
          makeAction('进入 AI 草稿区', '/llm/drafts'),
        ],
      }
    case 'report-gen':
      return {
        title: '报告不是简单导出，而是结论编排',
        summary: '报告视角的重点在于“把复杂分析压缩成可读结构”。你需要确认摘要、段落顺序、风险提示和导出形式是否服务最终读者。',
        highlights: [
          '摘要要先于术语，先让人看懂。',
          '复杂图表应有一句解释性短答。',
          '报告输出要区分咨询内部版本和对外版本。',
        ],
        readingSteps: [
          '先看报告目录与摘要卡。',
          '再确认模块段落是否符合阅读顺序。',
          '最后处理导出、签名和分享。',
        ],
        helper: '报告页承担最后的阅读收口。',
        nextActions: [
          makeAction('进入报告工作区', reportRoute.value, undefined, 'primary'),
          makeAction('回案例中心继续整理', '/cases'),
          makeAction('打开 AI 草稿区', '/llm/drafts'),
        ],
      }
    case 'report-templates':
      return {
        title: '模板应该帮助复用，而不是制造更多碎片',
        summary: '模板库的价值在于让高频表达、审核口径和段落顺序稳定下来。好的模板应该让你更快表达，而不是增加维护成本。',
        highlights: [
          '优先沉淀高频短答和标准提示语。',
          '模板要和审核状态、版本信息一起使用。',
          '不要为低频场景创建过多模板。',
        ],
        readingSteps: [
          '先看模板分类。',
          '再确认哪些内容适合复用。',
          '最后回到报告页插入并调整。',
        ],
        nextActions: [
          makeAction('进入报告工作区', '/report', undefined, 'primary'),
          makeAction('前往管理后台', '/admin'),
        ],
      }
    case 'report-cases':
      return {
        title: '案例库更像检索与复盘中心',
        summary: '案例库的意义不只是存档，而是帮助你快速找到相似案例、理解处理路径，并把经验回流到报告和咨询表达中。',
        highlights: [
          '先看案例摘要，再决定是否深入。',
          '相似案例更适合做复盘参考，不宜直接套用。',
          '好的案例库会把来源、时间线和流转动作放在一起。',
        ],
        readingSteps: [
          '先搜同类主题或标签。',
          '再看快照与处理结果。',
          '最后决定是否流转到报告或 AI 草稿。',
        ],
        nextActions: [
          makeAction('进入紫微案例区', '/ziwei/cases', undefined, 'primary'),
          makeAction('回案例中心', '/cases'),
          makeAction('打开 AI 草稿区', '/llm/drafts'),
        ],
      }
    case 'ai-chat':
      return {
        title: 'AI 最适合做解释和草稿，不适合越权定论',
        summary: 'AI 协同层最有价值的地方，是快速生成解释稿、整理术语、压缩长文本和形成备选表达。最终判断仍应回到案例与专家。',
        highlights: [
          '先给 AI 足够上下文，再问具体问题。',
          '要求 AI 输出时，最好指定口吻、长度和目标读者。',
          '涉及结论性建议时，应保留人工校核环节。',
        ],
        readingSteps: [
          '先确认当前案例和当前主题。',
          '再让 AI 输出摘要、解释或草稿。',
          '最后人工筛选并流转到报告。',
        ],
        helper: '右栏聊天适合即时解释，草稿工作区适合沉淀可复用文本。',
        nextActions: [
          makeAction('进入 AI 草稿工作区', '/llm/drafts', undefined, 'primary'),
          makeAction('查看报告', reportRoute.value),
          makeAction('回案例中心', '/cases'),
        ],
      }
    default:
      if (sectionId.startsWith('ziwei-')) {
        return genericGuide(label, '/ziwei')
      }
      if (sectionId.startsWith('name-')) {
        return genericGuide(label, '/name')
      }
      if (sectionId.startsWith('fengshui-')) {
        return genericGuide(label, '/fengshui')
      }
      if (sectionId.startsWith('heyin-')) {
        return genericGuide(label, route)
      }
      if (sectionId.startsWith('astro-')) {
        return genericGuide(label, '/western')
      }
      if (sectionId.startsWith('ai-')) {
        return genericGuide(label, route)
      }
      return genericGuide(label, route)
  }
}

function openAction(action: NextAction) {
  if (action.command === 'ask-ai') {
    askAI()
    return
  }
  if (action.sectionId) nav.selectSection(action.sectionId)
  if (action.route && action.route !== currentRoutePath.value) {
    router.push(action.route)
  }
}

function askAI() {
  if (!section.value || !sectionGuide.value) return
  const caseLine = selectedCase.value ? `\n当前案例：${selectedCase.value.name || '未命名案例'}，${formatGender(selectedCase.value.gender)}，${selectedCase.value.city || '出生地待补充'}` : ''
  const prompt = `请围绕当前命理课题给出面向用户的解释。\n章节：${chapter.value?.label} › ${section.value.label}${caseLine}\n本节重点：${sectionGuide.value.highlights.join('；')}\n请输出：1）一句话结论 2）三点解释 3）下一步建议。`
  ai.sendMessage(prompt)
}
</script>

<template>
  <div v-if="section && sectionGuide" class="topic-panel" :style="accentStyle">
    <div class="breadcrumb">
      <span class="bc-chapter">{{ chapter?.num }}. {{ chapter?.label }}</span>
      <span class="bc-sep">›</span>
      <span class="bc-section">{{ section.num }} {{ section.label }}</span>
    </div>

    <div class="hero-block">
      <div class="hero-eyebrow">阅读辅助</div>
      <div class="hero-title">{{ sectionGuide.title }}</div>
      <p class="hero-summary">{{ sectionGuide.summary }}</p>
      <div v-if="sectionGuide.helper" class="hero-note">{{ sectionGuide.helper }}</div>
      <div v-if="sectionGuide.caution" class="hero-note caution">{{ sectionGuide.caution }}</div>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">🧾</span>
        <span>当前案例</span>
      </div>
      <div v-if="selectedCase" class="context-grid">
        <div v-for="item in caseContextItems" :key="item.label" class="context-item">
          <div class="context-label">{{ item.label }}</div>
          <div class="context-value">{{ item.value }}</div>
        </div>
      </div>
      <div v-else class="callout" :class="{ warning: sectionGuide.caseRequired }">
        {{ sectionGuide.caseRequired ? '当前未选中案例。建议先到案例中心选择或创建案例，再继续阅读本节。' : '当前没有绑定案例，也可以先阅读本节说明。' }}
      </div>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">✨</span>
        <span>本节看点</span>
      </div>
      <ul class="bullet-list">
        <li v-for="item in sectionGuide.highlights" :key="item">{{ item }}</li>
      </ul>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">🪜</span>
        <span>阅读顺序</span>
      </div>
      <div class="step-list">
        <div v-for="(item, index) in sectionGuide.readingSteps" :key="item" class="step-item">
          <span class="step-index">{{ index + 1 }}</span>
          <span class="step-text">{{ item }}</span>
        </div>
      </div>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">➡</span>
        <span>下一步</span>
      </div>
      <div class="actions-grid">
        <button
          v-for="action in sectionGuide.nextActions"
          :key="`${action.label}-${action.route ?? ''}-${action.sectionId ?? ''}`"
          class="action-btn"
          :class="action.tone ?? 'neutral'"
          type="button"
          @click="openAction(action)"
        >
          {{ action.label }}
        </button>
      </div>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">📚</span>
        <span>本节课题</span>
        <span class="count-badge">{{ section.topics.length }}</span>
      </div>
      <div class="topic-grid">
        <div v-for="topic in section.topics" :key="topic.id" class="topic-chip">
          <span class="chip-dot"></span>
          <span>{{ topic.label }}</span>
        </div>
      </div>
    </div>

    <div class="block">
      <div class="block-title">
        <span class="block-icon">🖥</span>
        <span>本页会显示</span>
      </div>
      <div class="display-list">
        <div v-for="(item, index) in section.displays" :key="item" class="display-item">
          <span class="di-idx">{{ index + 1 }}</span>
          <span class="di-text">{{ item }}</span>
        </div>
      </div>
    </div>

    <div class="ai-action-row">
      <button class="ai-btn" :disabled="ai.streaming" @click="askAI">
        <span>🤖</span>
        <span>{{ ai.streaming ? 'AI 分析中…' : `AI 帮我解释：${section.label}` }}</span>
      </button>
    </div>

    <div class="block quick-actions-block">
      <div class="block-title">
        <span class="block-icon">🧰</span>
        <span>快捷操作</span>
      </div>
      <div class="quick-actions-grid">
        <button class="qa-btn qa-adjust" type="button" @click="emitQuickAction('adjust')">⏱ 定盘</button>
        <button class="qa-btn qa-copy" type="button" @click="emitQuickAction('copy')">📋 复制</button>
        <button class="qa-btn qa-export" type="button" @click="emitQuickAction('export')">📷 导出</button>
        <button class="qa-btn qa-share" type="button" @click="emitQuickAction('share')">🔗 分享</button>
        <button class="qa-btn qa-notes" type="button" @click="emitQuickAction('notes')">📝 笔记</button>
        <button class="qa-btn qa-calendar" type="button" @click="emitQuickAction('calendar')">📅 日历</button>
        <button class="qa-btn qa-compare" type="button" @click="emitQuickAction('compare')">⚖ 对比</button>
        <button class="qa-btn qa-bookmarks" type="button" @click="emitQuickAction('bookmarks')">★ 收藏</button>
      </div>
    </div>
  </div>

  <div v-else class="empty-state">
    <div class="empty-icon">☯</div>
    <div class="empty-title">阅读辅助面板</div>
    <div class="empty-sub">从左侧选择一个章节小节，右侧会告诉你先看什么、怎么理解、下一步去哪。</div>
    <div class="chapter-pills">
      <button
        v-for="ch in nav.NAV_CHAPTERS"
        :key="ch.id"
        class="ch-pill"
        :style="`background: ${ch.color}16; color: ${ch.color}; border-color: ${ch.color}2e`"
        @click="nav.toggleChapter(ch.id)"
      >
        <span>{{ ch.icon }}</span>
        <span>{{ ch.label }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.topic-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
  height: 100%;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 12px 14px 8px;
  font-size: 0.75rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.bc-chapter {
  color: var(--topic-accent);
  font-weight: 700;
}

.bc-sep {
  color: var(--color-text-muted);
}

.bc-section {
  color: var(--color-text-secondary);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-block {
  padding: 14px;
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(180deg, color-mix(in srgb, var(--topic-accent) 10%, white) 0%, transparent 100%);
}

.hero-eyebrow {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--topic-accent);
  margin-bottom: 6px;
}

.hero-title {
  font-size: 0.9375rem;
  line-height: 1.4;
  font-weight: 700;
  color: var(--color-text-primary);
}

.hero-summary {
  margin: 8px 0 0;
  font-size: 0.78125rem;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.hero-note {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  line-height: 1.6;
}

.hero-note.caution {
  border: 1px solid color-mix(in srgb, var(--topic-accent) 28%, var(--color-border));
}

.block {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
}

.block-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.02em;
}

.block-icon {
  font-size: 13px;
}

.count-badge {
  margin-left: auto;
  font-size: 0.625rem;
  background: var(--color-bg-tertiary);
  color: var(--color-text-muted);
  padding: 1px 6px;
  border-radius: 99px;
  font-weight: 600;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.context-item {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 8px 10px;
}

.context-label {
  font-size: 0.625rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 4px;
}

.context-value {
  font-size: 0.75rem;
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.callout {
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  line-height: 1.6;
}

.callout.warning {
  border: 1px dashed var(--topic-accent);
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.75rem;
  line-height: 1.65;
  color: var(--color-text-secondary);
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.step-index {
  width: 20px;
  height: 20px;
  border-radius: 99px;
  background: color-mix(in srgb, var(--topic-accent) 14%, white);
  color: var(--topic-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-text {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  line-height: 1.65;
}

.actions-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.action-btn {
  width: 100%;
  border-radius: 8px;
  padding: 9px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: transform var(--transition-fast), opacity var(--transition-fast), border-color var(--transition-fast);
}

.action-btn:hover {
  transform: translateY(-1px);
}

.action-btn.primary {
  border: none;
  background: var(--topic-accent);
  color: #fff;
}

.action-btn.neutral {
  border: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.action-btn.ghost {
  border: 1px dashed var(--color-border);
  background: transparent;
  color: var(--color-text-secondary);
}

.topic-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.topic-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--color-bg-secondary);
  border-radius: 6px;
  font-size: 0.75rem;
  color: var(--color-text-primary);
  line-height: 1.5;
}

.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--topic-accent);
  flex-shrink: 0;
}

.display-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.display-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.di-idx {
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: color-mix(in srgb, var(--topic-accent) 14%, white);
  color: var(--topic-accent);
  font-size: 0.625rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.di-text {
  flex: 1;
  line-height: 1.5;
}

.ai-action-row {
  padding: 12px 14px;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--topic-accent);
  border-radius: 8px;
  background: transparent;
  color: var(--topic-accent);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-ui);
  justify-content: center;
}

.ai-btn:hover:not(:disabled) {
  background: var(--topic-accent);
  color: #fff;
}

.ai-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-actions-block {
  padding-top: 8px;
  padding-bottom: 14px;
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.qa-btn {
  border: none;
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  line-height: 1;
  font-family: var(--font-ui);
  transition: transform var(--transition-fast), filter var(--transition-fast);
}

.qa-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.qa-adjust,
.qa-copy {
  background: #f1f5f9;
  color: #475569;
}

.qa-export,
.qa-share {
  background: #4f46e5;
  color: #fff;
}

.qa-notes {
  background: #7c3aed;
  color: #fff;
}

.qa-calendar {
  background: #059669;
  color: #fff;
}

.qa-compare {
  background: #f97316;
  color: #fff;
}

.qa-bookmarks {
  background: #f59e0b;
  color: #fff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 16px;
  gap: 8px;
}

.empty-icon {
  font-size: 36px;
  opacity: 0.3;
}

.empty-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.empty-sub {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-align: center;
  line-height: 1.6;
}

.chapter-pills {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  margin-top: 10px;
}

.ch-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid;
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-ui);
  transition: opacity var(--transition-fast);
  text-align: left;
}

.ch-pill:hover {
  opacity: 0.8;
}

@media (max-width: 1279px) {
  .context-grid,
  .quick-actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
