<script setup lang="ts">
/**
 * HumanDesignView.vue — 人类设计工作区（§T3.3）
 * 类型、策略、权威、中心与轮廓说明
 */
import { ref, computed } from 'vue'

// ── 类型数据 ────────────────────────────────────────────────
interface HDType {
  id: string
  name: string
  en: string
  icon: string
  color: string
  bg: string
  population: string
  strategy: string
  authority_hint: string
  signature: string
  not_self: string
  desc: string
  aura: string
  keywords: string[]
}

const TYPES: HDType[] = [
  {
    id: 'manifestor',
    name: '显化者', en: 'Manifestor',
    icon: '⚡', color: '#ef4444', bg: '#fef2f2',
    population: '约9%',
    strategy: '告知（Inform Before Acting）',
    authority_hint: '情感权威 / 本我中心权威',
    signature: '平和（Peace）',
    not_self: '愤怒（Anger）',
    aura: '封闭且排斥——如同一道无形的墙，让周围人感到距离',
    desc: '显化者是唯一能够直接发起行动的类型。他们拥有与喉轮相连的电机中心或根部，能够直接将冲动化为现实。策略是"告知"身边的人，而不是获得许可。',
    keywords: ['先行者', '发起', '独立', '告知', '冲击', '催化'],
  },
  {
    id: 'generator',
    name: '生产者', en: 'Generator',
    icon: '🔥', color: '#f97316', bg: '#fff7ed',
    population: '约36%',
    strategy: '等待（Wait to Respond）',
    authority_hint: '骶骨权威 / 情感权威',
    signature: '满足（Satisfaction）',
    not_self: '沮丧（Frustration）',
    aura: '开放且包容——自然吸引他人和机会',
    desc: '生产者是世界的建设力量，拥有持续旺盛的骶骨能量。核心是"等待回应"——当骶骨对外部刺激发出"嗯哼（Uh-huh）"的响应时，才是正确的行动信号。强迫发起会导致沮丧和能量耗损。',
    keywords: ['持续力', '回应', '建设', '骶骨', '满足', '工作'],
  },
  {
    id: 'manifesting-generator',
    name: '显化生产者', en: 'Manifesting Generator',
    icon: '🌀', color: '#f59e0b', bg: '#fffbeb',
    population: '约32%',
    strategy: '等待回应，告知后行动（Wait to Respond, then Inform）',
    authority_hint: '骶骨权威 / 情感权威',
    signature: '满足与平和',
    not_self: '沮丧与愤怒',
    aura: '开放、包容且有冲劲',
    desc: '显化生产者兼具生产者的回应力与显化者的行动速度。他们非线性、跳跃式地工作，擅长快速试错。须先等待骶骨回应，再告知他人，跳过步骤会引发混乱。',
    keywords: ['多线程', '速度', '回应', '非线性', '试错', '活力'],
  },
  {
    id: 'projector',
    name: '投射者', en: 'Projector',
    icon: '🔭', color: '#8b5cf6', bg: '#f5f3ff',
    population: '约21%',
    strategy: '等待邀请（Wait for the Invitation）',
    authority_hint: '情感权威 / 脾脏权威 / 心/意志中心 / 自我投射 / 无（月亮）',
    signature: '成功（Success）',
    not_self: '痛苦（Bitterness）',
    aura: '专注且穿透——能深入看透他人',
    desc: '投射者是人类设计中的引导者，拥有在管理、指引和优化他人方面的天赋。但这种天赋只有在被"邀请"时才能发挥作用。未经邀请就提供建议会遭遇抵制，等待认可后才能成功。',
    keywords: ['引导', '管理', '等待邀请', '识别', '效率', '智慧'],
  },
  {
    id: 'reflector',
    name: '反映者', en: 'Reflector',
    icon: '🌕', color: '#64748b', bg: '#f8fafc',
    population: '约1%',
    strategy: '等待月亮周期（Wait a Lunar Cycle, ~28 days）',
    authority_hint: '月亮周期（Lunar Authority）',
    signature: '惊喜（Surprise & Delight）',
    not_self: '失望（Disappointment）',
    aura: '采样且反映——映照出周围环境的真实状态',
    desc: '反映者是极为罕见的存在，所有能量中心均开放，高度敏感。他们如同社区的"健康晴雨表"，能真实反映出集体的能量状态。重大决策需要等待完整的月亮周期（约28天）以获得清晰感。',
    keywords: ['稀有', '反映', '环境', '月亮', '采样', '社区健康'],
  },
]

// ── 权威类型 ────────────────────────────────────────────────
interface Authority {
  id: string; name: string; en: string; icon: string; desc: string
}
const AUTHORITIES: Authority[] = [
  { id: 'emotional', name: '情感权威', en: 'Emotional Authority', icon: '🌊',
    desc: '通过情绪波浪来决策。在做任何重要决定时，需要等到情绪平静明朗（非高波峰也非低谷时）再行动。"不要在情绪高峰或低谷做决定"。' },
  { id: 'sacral', name: '骶骨权威', en: 'Sacral Authority', icon: '🔥',
    desc: '只属于生产者/显化生产者。通过骶骨发出的即时声音信号（嗯哼/嗯嗯）来决策。这是一种身体的直接响应，不经大脑分析。' },
  { id: 'splenic', name: '脾脏权威', en: 'Splenic Authority', icon: '⚡',
    desc: '当下即刻的直觉感知。脾脏只说一次，转瞬即逝。需要学会信任那一闪而过的感知，而非在事后强行回忆。' },
  { id: 'ego', name: '心/意志中心权威', en: 'Ego/Heart Manifested Authority', icon: '❤️',
    desc: '通过意志力和自身欲望决策。"如果我想要它，我就做；如果不想要，我就不做。"只在显化者中出现。' },
  { id: 'self', name: '自我投射权威', en: 'Self-Projected Authority', icon: '🎯',
    desc: '通过说话来明确方向。大声说出来之后，自己会从语言的流动中分辨出什么是真实的方向。找对的人谈话非常重要。' },
  { id: 'outer', name: '外部权威', en: 'Mental/Outer Authority', icon: '🌐',
    desc: '没有内在权威，需要通过与信任的人交谈来理清思路（但由自己做决定）。对环境高度敏感，注意自己置身的空间与人群。' },
  { id: 'lunar', name: '月亮权威', en: 'Lunar Authority', icon: '🌕',
    desc: '只属于反映者。在月亮完整运行约28天后，通过多次与不同人的交流来累积感知，在周期结束时才能获得清晰。' },
]

// ── 九大中心 ────────────────────────────────────────────────
interface Center {
  id: string; name: string; en: string; icon: string
  defined_meaning: string; open_meaning: string; function_desc: string
}
const CENTERS: Center[] = [
  { id: 'head', name: '头部', en: 'Head Center', icon: '💭',
    function_desc: '灵感与压力、存在性问题',
    defined_meaning: '持续稳定的灵感来源，有固定的思考方式',
    open_meaning: '容易被他人想法影响，但能整合多方灵感' },
  { id: 'ajna', name: '意识/智慧中心', en: 'Ajna Center', icon: '👁️',
    function_desc: '概念化、分析、理性处理',
    defined_meaning: '思维方式固定且持续，有自己的分析框架',
    open_meaning: '思维灵活，能从多角度分析，但容易被"应该确定"的压力绑架' },
  { id: 'throat', name: '喉轮', en: 'Throat Center', icon: '🎤',
    function_desc: '表达、显化与沟通',
    defined_meaning: '表达方式稳定，能持续有效地传递信息',
    open_meaning: '表达受情境影响，可模仿多种风格，但需留意"为说而说"的惯性' },
  { id: 'g', name: '自我/本我中心', en: 'G Center', icon: '❤️',
    function_desc: '身份认同、方向感、爱',
    defined_meaning: '强烈的身份感，知道自己是谁，方向稳定',
    open_meaning: '身份随环境变化，通过场所与人来寻找方向，是旅行者' },
  { id: 'heart', name: '心/意志中心', en: 'Heart/Ego Center', icon: '💪',
    function_desc: '意志力、自我价值感、物质',
    defined_meaning: '意志力充足，能持续承诺并兑现',
    open_meaning: '不适合无限承诺，需学会说"不"，自我价值感不需证明' },
  { id: 'solar-plexus', name: '丹田/情绪中心', en: 'Solar Plexus Center', icon: '🌊',
    function_desc: '情绪、情感与精神波浪',
    defined_meaning: '有内在情绪波浪，决策需等待波浪平静',
    open_meaning: '如实吸收并放大他人情绪，须区分"这是我的情绪吗"' },
  { id: 'sacral', name: '骶骨中心', en: 'Sacral Center', icon: '🔥',
    function_desc: '生命力、性能量与工作动力',
    defined_meaning: '持续旺盛的能量源，适合持续工作（生产者/显化生产者）',
    open_meaning: '能量不稳定，不适合长时间持续工作，需要充分休息' },
  { id: 'spleen', name: '脾脏/直觉中心', en: 'Spleen Center', icon: '⚡',
    function_desc: '直觉、恐惧、免疫力与生存本能',
    defined_meaning: '通灵直觉持续且可靠，当下即刻的感知值得信任',
    open_meaning: '直觉忽强忽弱，容易受他人脾脏影响，须注意健康与安全信号' },
  { id: 'root', name: '根部', en: 'Root Center', icon: '🌳',
    function_desc: '肾上腺与压力、进化动力',
    defined_meaning: '持续的压力驱动，有固定的推进节奏',
    open_meaning: '压力随外部变化，容易累积来自他人的肾上腺压力，需学会减压' },
]

// ── 轮廓（Profile）数据 ─────────────────────────────────────
const PROFILES = [
  { profile: '1/3', name: '研究者/烈士', desc: '基础建立者，通过亲身试错积累真实经验。需要先打好基础才有安全感，碰触正确机缘后才真正开启自己的人生。' },
  { profile: '1/4', name: '研究者/机会主义者', desc: '以坚实基础建立影响力网络。知识储备赋予其权威感，从友情与人脉网络中获得机会，稳定而外向。' },
  { profile: '2/4', name: '隐士/机会主义者', desc: '天生才能被他人邀请激活。需要独处时间来深化自己的才华，通过核心的人际网络施展作用。' },
  { profile: '2/5', name: '隐士/异端', desc: '带有实际解决问题的光环，常被他人投射为救世主。需要在被"召唤"时出现，保留大量独处空间。' },
  { profile: '3/5', name: '烈士/异端', desc: '通过试错发现什么有效，并将方法提供给大众。充满混乱与发现，人际关系短暂但深刻。' },
  { profile: '3/6', name: '烈士/典范', desc: '人生分为三阶段：试错期、退隐观察期、最终成为鲜活的生活典范。是活出可能性的见证者。' },
  { profile: '4/6', name: '机会主义者/典范', desc: '以自身生命的示范来影响专属网络。在稳固的人际基础上施展能量，逐步成为值得信赖的典范。' },
  { profile: '4/1', name: '机会主义者/研究者', desc: '稳固的外部网络与内在知识基础并重。通过可信赖的连接获得机会，喜欢在熟悉的领域深耕。' },
  { profile: '5/1', name: '异端/研究者', desc: '被投射为实际问题解决者，需以坚实知识基础承接他人期待。避免在没有准备时被推上台。' },
  { profile: '5/2', name: '异端/隐士', desc: '在专属呼召到来前保持隐退。具备解决大众难题的能力，需要极大的独处空间和正确的召唤时刻。' },
  { profile: '6/2', name: '典范/隐士', desc: '三段人生弧线的最终目标是成为没有评判的活人典范，同时保留大量退隐更新的时间。' },
  { profile: '6/3', name: '典范/烈士', desc: '经历大量试错后，在第三阶段成为真实鲜活的生命典范。碰触正确机缘才能进入下一阶段。' },
]

// ── 当前选中状态 ────────────────────────────────────────────
const selectedTypeId = ref<string | null>(null)
const selectedCenterState = ref<Record<string, 'defined' | 'open'>>({})
const activeTab = ref<'types' | 'authority' | 'centers' | 'profile'>('types')

const selectedType = computed(() => TYPES.find(t => t.id === selectedTypeId.value) ?? null)

function toggleCenter(id: string) {
  if (selectedCenterState.value[id] === 'defined') {
    selectedCenterState.value[id] = 'open'
  } else if (selectedCenterState.value[id] === 'open') {
    delete selectedCenterState.value[id]
  } else {
    selectedCenterState.value[id] = 'defined'
  }
}

function centerState(id: string) {
  return selectedCenterState.value[id] ?? 'unknown'
}

</script>

<template>
  <div class="hd-wrap">
    <!-- 标题 -->
    <div class="hd-header">
      <h1 class="hd-title">人类设计工作区</h1>
      <p class="hd-subtitle">Human Design System — 类型 · 策略 · 权威 · 中心 · 轮廓</p>
    </div>

    <!-- 导航 Tab -->
    <div class="hd-tabs">
      <button v-for="tab in [
        { id: 'types', label: '类型 & 策略' },
        { id: 'authority', label: '权威' },
        { id: 'centers', label: '九大中心' },
        { id: 'profile', label: '轮廓' },
      ]" :key="tab.id"
        class="hd-tab" :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id as any">
        {{ tab.label }}
      </button>
    </div>

    <!-- ── 类型 Tab ──────────────────────────────────────────── -->
    <div v-if="activeTab === 'types'" class="hd-tab-content">
      <p class="hd-tab-intro">
        人类设计将人分为5种类型，每种类型有独特的能量场（Aura）、策略与使命。
        点击任一类型卡片查看详情。
      </p>
      <div class="hd-type-grid">
        <div v-for="t in TYPES" :key="t.id"
          class="hd-type-card" :class="{ selected: selectedTypeId === t.id }"
          :style="{ borderLeftColor: t.color }"
          @click="selectedTypeId = t.id === selectedTypeId ? null : t.id">
          <div class="hd-type-icon" :style="{ background: t.bg }">{{ t.icon }}</div>
          <div class="hd-type-info">
            <div class="hd-type-name">{{ t.name }} <span class="hd-type-en">{{ t.en }}</span></div>
            <div class="hd-type-pop">占人口 {{ t.population }}</div>
            <div class="hd-type-strategy-mini">策略：{{ t.strategy }}</div>
          </div>
          <div class="hd-sig-badge" :style="{ background: t.color + '22', color: t.color }">
            ✨ {{ t.signature }}
          </div>
        </div>
      </div>

      <Transition name="fade">
        <div v-if="selectedType" class="hd-type-detail"
          :style="{ borderColor: selectedType.color }">
          <div class="hd-td-header" :style="{ background: selectedType.bg }">
            <span class="hd-td-icon">{{ selectedType.icon }}</span>
            <div>
              <h2 class="hd-td-name">{{ selectedType.name }}</h2>
              <p class="hd-td-en">{{ selectedType.en }}</p>
            </div>
          </div>
          <div class="hd-td-body">
            <p class="hd-td-desc">{{ selectedType.desc }}</p>
            <div class="hd-td-grid">
              <div class="hd-td-item"><label>策略</label><span>{{ selectedType.strategy }}</span></div>
              <div class="hd-td-item"><label>常见权威</label><span>{{ selectedType.authority_hint }}</span></div>
              <div class="hd-td-item"><label>能量场（Aura）</label><span>{{ selectedType.aura }}</span></div>
              <div class="hd-td-item">
                <label>签名（活出自己时的感受）</label>
                <span :style="{ color: selectedType.color }">✨ {{ selectedType.signature }}</span>
              </div>
              <div class="hd-td-item">
                <label>非自己主题（偏离时的感受）</label>
                <span style="color:#ef4444">⚠️ {{ selectedType.not_self }}</span>
              </div>
            </div>
            <div class="hd-td-kws">
              <span v-for="kw in selectedType.keywords" :key="kw" class="hd-kw"
                :style="{ background: selectedType.color + '22', color: selectedType.color }">{{ kw }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- ── 权威 Tab ──────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'authority'" class="hd-tab-content">
      <p class="hd-tab-intro">
        内在权威（Inner Authority）是每个人在做重要决策时真正应该依赖的声音。
        它比类型更个人化，决定了你"如何"在类型策略的指引下做出具体选择。
      </p>
      <div class="hd-auth-list">
        <div v-for="auth in AUTHORITIES" :key="auth.id" class="hd-auth-card">
          <div class="hd-auth-icon">{{ auth.icon }}</div>
          <div>
            <div class="hd-auth-name">{{ auth.name }}</div>
            <div class="hd-auth-en">{{ auth.en }}</div>
            <p class="hd-auth-desc">{{ auth.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 中心 Tab ──────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'centers'" class="hd-tab-content">
      <p class="hd-tab-intro">
        九大能量中心对应着人体不同的功能区域。
        <strong>已定义（Defined）</strong>的中心能量稳定固定，<strong>开放（Open）</strong>的中心接收并放大外界能量。
        点击每个中心切换状态：<span class="hd-tag-defined">已定义</span> → <span class="hd-tag-open">开放</span> → 未选。
      </p>
      <div class="hd-centers-grid">
        <div v-for="c in CENTERS" :key="c.id"
          class="hd-center-card" :class="'state-' + centerState(c.id)"
          @click="toggleCenter(c.id)">
          <div class="hd-center-icon">{{ c.icon }}</div>
          <div class="hd-center-name">{{ c.name }}</div>
          <div class="hd-center-en">{{ c.en }}</div>
          <div class="hd-center-func">{{ c.function_desc }}</div>
          <div class="hd-center-state-badge">
            <template v-if="centerState(c.id) === 'defined'">
              <span class="hd-tag-defined">已定义</span>
              <p class="hd-center-meaning">{{ c.defined_meaning }}</p>
            </template>
            <template v-else-if="centerState(c.id) === 'open'">
              <span class="hd-tag-open">开放</span>
              <p class="hd-center-meaning">{{ c.open_meaning }}</p>
            </template>
            <template v-else>
              <span class="hd-tag-unknown">点击选择</span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 轮廓 Tab ──────────────────────────────────────────── -->
    <div v-else-if="activeTab === 'profile'" class="hd-tab-content">
      <p class="hd-tab-intro">
        轮廓（Profile）由易经两条爻线组成，揭示了你扮演的人生角色与主题。
        共有12种轮廓，每种都有独特的人生弧线与使命方向。
      </p>
      <div class="hd-profile-grid">
        <div v-for="p in PROFILES" :key="p.profile" class="hd-profile-card">
          <div class="hd-profile-num">{{ p.profile }}</div>
          <div class="hd-profile-name">{{ p.name }}</div>
          <p class="hd-profile-desc">{{ p.desc }}</p>
        </div>
      </div>
    </div>

    <div class="hd-footer-note">
      <strong>数据来源：</strong>人类设计系统由 Ra Uru Hu 于1987年接收并整合，
      融合了占星学、易经、卡巴拉生命之树、脉轮系统与量子物理学。
      本页面仅提供参考性介绍，完整的个人人类设计图需结合确切出生时间、日期和地点计算。
    </div>
  </div>
</template>

<style scoped>
.hd-wrap { max-width: 1100px; margin: 0 auto; padding: 24px 20px 56px; }
.hd-header { margin-bottom: 20px; }
.hd-title  { font-size: 22px; font-weight: 700; color: var(--text); margin: 0; font-family: var(--font-cn); }
.hd-subtitle { font-size: 12px; color: var(--text-3); margin: 4px 0 0; }

.hd-tabs { display: flex; gap: 6px; margin-bottom: 20px; flex-wrap: wrap; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
.hd-tab {
  padding: 7px 16px; border-radius: 8px 8px 0 0;
  border: 1px solid var(--border); border-bottom: none;
  background: var(--surface-2); color: var(--text-2);
  cursor: pointer; font-size: 13px; font-family: var(--font-cn); transition: all .15s;
}
.hd-tab.active { background: var(--surface); color: var(--accent); border-color: var(--accent); font-weight: 600; }

.hd-tab-intro {
  font-size: 13px; color: var(--text-2); line-height: 1.7; margin-bottom: 20px;
  font-family: var(--font-cn); padding: 12px 16px;
  background: var(--surface-2); border-radius: 8px;
}

.hd-type-grid { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.hd-type-card {
  display: flex; align-items: center; gap: 14px; padding: 14px 16px;
  background: var(--surface); border: 1px solid var(--border);
  border-left: 4px solid; border-radius: 10px; cursor: pointer; transition: box-shadow .15s;
}
.hd-type-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.1); }
.hd-type-card.selected { box-shadow: 0 0 0 2px var(--accent); }
.hd-type-icon { width: 44px; height: 44px; border-radius: 10px; min-width: 44px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.hd-type-info { flex: 1; }
.hd-type-name { font-size: 15px; font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.hd-type-en { font-size: 11px; color: var(--text-3); font-weight: 400; margin-left: 6px; }
.hd-type-pop { font-size: 11px; color: var(--text-3); margin-top: 2px; }
.hd-type-strategy-mini { font-size: 12px; color: var(--text-2); margin-top: 1px; }
.hd-sig-badge { font-size: 12px; padding: 4px 12px; border-radius: 99px; font-family: var(--font-cn); white-space: nowrap; }

.hd-type-detail { border: 2px solid; border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.hd-td-header { display: flex; align-items: center; gap: 14px; padding: 16px 20px; }
.hd-td-icon { font-size: 32px; }
.hd-td-name { font-size: 20px; font-weight: 700; font-family: var(--font-cn); margin: 0; }
.hd-td-en   { font-size: 12px; color: var(--text-3); margin: 2px 0 0; }
.hd-td-body { padding: 16px 20px; }
.hd-td-desc { font-size: 14px; color: var(--text-2); line-height: 1.7; font-family: var(--font-cn); margin: 0 0 16px; }
.hd-td-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 10px; margin-bottom: 14px; }
.hd-td-item { background: var(--surface-2); border-radius: 8px; padding: 10px 12px; }
.hd-td-item label { font-size: 10px; font-weight: 600; color: var(--text-3); text-transform: uppercase; letter-spacing: .05em; display: block; margin-bottom: 4px; }
.hd-td-item span { font-size: 13px; font-family: var(--font-cn); color: var(--text); line-height: 1.5; }
.hd-td-kws { display: flex; flex-wrap: wrap; gap: 6px; }
.hd-kw { font-size: 12px; padding: 3px 10px; border-radius: 99px; font-family: var(--font-cn); font-weight: 600; }

.hd-auth-list { display: flex; flex-direction: column; gap: 12px; }
.hd-auth-card { display: flex; gap: 16px; padding: 16px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
.hd-auth-icon { font-size: 28px; min-width: 36px; }
.hd-auth-name { font-size: 15px; font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.hd-auth-en   { font-size: 11px; color: var(--text-3); margin-bottom: 6px; }
.hd-auth-desc { font-size: 13px; color: var(--text-2); line-height: 1.7; font-family: var(--font-cn); margin: 0; }

.hd-centers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.hd-center-card { padding: 14px; border: 1.5px solid var(--border); border-radius: 10px; background: var(--surface); cursor: pointer; transition: all .15s; text-align: center; }
.hd-center-card.state-defined { border-color: #22c55e; background: #f0fdf4; }
.hd-center-card.state-open    { border-color: #f97316; background: #fff7ed; }
.hd-center-icon { font-size: 24px; margin-bottom: 6px; }
.hd-center-name { font-size: 14px; font-weight: 700; font-family: var(--font-cn); }
.hd-center-en   { font-size: 10px; color: var(--text-3); margin-bottom: 4px; }
.hd-center-func { font-size: 11px; color: var(--text-2); font-family: var(--font-cn); margin-bottom: 8px; line-height: 1.4; }
.hd-center-meaning { font-size: 11px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.5; margin: 6px 0 0; text-align: left; }
.hd-tag-defined { font-size: 11px; padding: 2px 10px; border-radius: 99px; background: #dcfce7; color: #16a34a; font-weight: 600; }
.hd-tag-open    { font-size: 11px; padding: 2px 10px; border-radius: 99px; background: #ffedd5; color: #ea580c; font-weight: 600; }
.hd-tag-unknown { font-size: 11px; color: var(--text-3); }

.hd-profile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.hd-profile-card { padding: 16px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
.hd-profile-num  { font-size: 26px; font-weight: 900; font-family: var(--font-mono); color: var(--accent); }
.hd-profile-name { font-size: 14px; font-weight: 700; font-family: var(--font-cn); margin-bottom: 8px; }
.hd-profile-desc { font-size: 12px; color: var(--text-2); line-height: 1.7; font-family: var(--font-cn); margin: 0; }

.hd-footer-note { margin-top: 28px; padding: 12px 16px; background: var(--surface-2); border-radius: 8px; font-size: 12px; color: var(--text-3); font-family: var(--font-cn); line-height: 1.7; }

.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 600px) {
  .hd-type-card { flex-direction: column; align-items: flex-start; }
  .hd-sig-badge { align-self: flex-start; }
}
</style>
