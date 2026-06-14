<script setup lang="ts">
/**
 * NumerologyView.vue — 数字学（§7.1）
 * 皮达哥拉斯数字学（Pythagorean Numerology）+ 中文姓名笔画数字学
 */
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

// ── 表单 ──────────────────────────────────────────────────────
const form = ref({
  date: '',
  name: '',
})

// ── 中文姓名模式 ──────────────────────────────────────────────
const cnNameMode = ref(false)
const cnName = ref('')
const cnLoading = ref(false)
const cnError = ref('')

interface CharStrokeInfo { char: string; strokes: number; numerology_digit: number }
interface StrokesResponse {
  name: string; chars: CharStrokeInfo[]
  total_strokes: number; expression_number: number
}
const cnResult = ref<StrokesResponse | null>(null)

async function analyzeCnName() {
  if (!cnName.value.trim()) return
  cnLoading.value = true
  cnError.value = ''
  cnResult.value = null
  try {
    const { data } = await apiClient.post<StrokesResponse>('/api/v1/name/strokes', { name: cnName.value.trim() })
    cnResult.value = data
  } catch (e: any) {
    cnError.value = e?.response?.data?.detail ?? '查询失败，请稍后再试'
  } finally {
    cnLoading.value = false
  }
}


// ── 皮达哥拉斯字母-数字映射 ────────────────────────────────────
// 1=A,J,S  2=B,K,T  3=C,L,U  4=D,M,V  5=E,N,W  6=F,O,X  7=G,P,Y  8=H,Q,Z  9=I,R
const PYTH: Record<string, number> = {
  A:1, B:2, C:3, D:4, E:5, F:6, G:7, H:8, I:9,
  J:1, K:2, L:3, M:4, N:5, O:6, P:7, Q:8, R:9,
  S:1, T:2, U:3, V:4, W:5, X:6, Y:7, Z:8,
}

const VOWELS = new Set(['A', 'E', 'I', 'O', 'U'])

// ── 化减工具（保留主命数 11, 22, 33） ─────────────────────────
function reduce(n: number): number {
  if (n === 11 || n === 22 || n === 33) return n
  if (n < 10) return n
  const s = String(n).split('').reduce((acc, d) => acc + Number(d), 0)
  return reduce(s)
}

// ── 生命路径数（出生日期所有数字之和再化减） ─────────────────
const lifePath = computed<number | null>(() => {
  if (!form.value.date) return null
  const digits = form.value.date.replace(/-/g, '').split('').map(Number)
  const sum = digits.reduce((a, b) => a + b, 0)
  return reduce(sum)
})

// ── 生日数（仅日期两位数字） ──────────────────────────────────
const birthdayNum = computed<number | null>(() => {
  if (!form.value.date) return null
  const day = parseInt(form.value.date.slice(8, 10))
  return reduce(day)
})

// ── 名字数字计算 ──────────────────────────────────────────────
function nameNum(name: string, type: 'all' | 'vowels' | 'consonants'): number | null {
  if (!name.trim()) return null
  const letters = name.toUpperCase().replace(/[^A-Z]/g, '').split('')
  const filtered = type === 'vowels'
    ? letters.filter(l => VOWELS.has(l))
    : type === 'consonants'
    ? letters.filter(l => !VOWELS.has(l))
    : letters
  if (filtered.length === 0) return null
  const sum = filtered.reduce((s, l) => s + (PYTH[l] ?? 0), 0)
  return reduce(sum)
}

const expressionNum  = computed(() => nameNum(form.value.name, 'all'))
const soulUrgeNum    = computed(() => nameNum(form.value.name, 'vowels'))
const personalityNum = computed(() => nameNum(form.value.name, 'consonants'))

// ── 数字含义库 ────────────────────────────────────────────────
interface NumMeaning {
  title: string
  en: string
  keywords: string[]
  desc: string
  color: string
  bg: string
}

const MEANINGS: Record<number, NumMeaning> = {
  1: {
    title: '独立领袖', en: 'The Leader',
    keywords: ['独立', '创新', '领导', '意志力'],
    color: '#ef4444', bg: '#fef2f2',
    desc: '数字 1 代表新的开始与独立精神。您天生具有领导才能，勇于开拓，不惧挑战。执行力强，善于开创局面，但需警惕过于固执或忽视他人意见。',
  },
  2: {
    title: '和谐伙伴', en: 'The Cooperator',
    keywords: ['合作', '直觉', '平衡', '体贴'],
    color: '#f97316', bg: '#fff7ed',
    desc: '数字 2 象征合作与敏感。您善于倾听、调解与维系关系，直觉敏锐，注重细节。天生适合外交、咨询与艺术领域，但需避免优柔寡断或过度依赖他人。',
  },
  3: {
    title: '创意表达', en: 'The Creator',
    keywords: ['创意', '表达', '乐观', '社交'],
    color: '#f59e0b', bg: '#fffbeb',
    desc: '数字 3 代表创意与自我表达。您充满活力、乐观向上，擅长沟通与艺术创作，善于鼓励他人。在写作、音乐、演讲领域有天赋，需避免注意力分散。',
  },
  4: {
    title: '稳固建设', en: 'The Builder',
    keywords: ['稳定', '规律', '实际', '勤奋'],
    color: '#22c55e', bg: '#f0fdf4',
    desc: '数字 4 象征秩序与稳定，您是天生的实干家，做事认真负责、脚踏实地。善于组织、规划与管理，是团队的可靠支柱。需注意避免过于保守或抗拒变化。',
  },
  5: {
    title: '自由先锋', en: 'The Freedom Seeker',
    keywords: ['自由', '变化', '冒险', '适应力'],
    color: '#3b82f6', bg: '#eff6ff',
    desc: '数字 5 象征自由与变革。您追求多样化体验，充满好奇心，适应能力极强。天生的探险家和沟通者，在媒体、销售、旅行领域有优势，需警惕急躁冲动。',
  },
  6: {
    title: '爱与责任', en: 'The Nurturer',
    keywords: ['责任', '关怀', '家庭', '服务'],
    color: '#8b5cf6', bg: '#f5f3ff',
    desc: '数字 6 代表爱与服务。您天生关爱他人，对家庭和社区有强烈的责任感。善于调解冲突，在医疗、教育、服务行业表现出色，需学会在奉献与自我之间保持边界。',
  },
  7: {
    title: '智慧内省', en: 'The Seeker',
    keywords: ['智慧', '分析', '内省', '神秘'],
    color: '#06b6d4', bg: '#ecfeff',
    desc: '数字 7 代表智慧与灵性探求。您具有深刻的分析能力和探索精神，倾向独立思考，喜欢追寻深层真相。在研究、哲学、科技领域有天赋，需避免过度孤僻封闭。',
  },
  8: {
    title: '丰盛权威', en: 'The Achiever',
    keywords: ['权威', '成就', '物质', '管理'],
    color: '#64748b', bg: '#f8fafc',
    desc: '数字 8 象征权力与物质成功。您具有出色的商业头脑和管理才能，追求效率与成就。在商界、金融、管理领域有强大优势，需注意在物质追求与精神滋养之间保持平衡。',
  },
  9: {
    title: '博爱慈悲', en: 'The Humanitarian',
    keywords: ['博爱', '慈悲', '智慧', '完成'],
    color: '#ec4899', bg: '#fdf2f8',
    desc: '数字 9 是生命路径中最具灵性的数字，代表完成与博爱。您富有同理心，心胸宽广，天生的人道主义者。在艺术、心理、慈善领域有杰出表现，需学会放下执念，活在当下。',
  },
  11: {
    title: '灵感大师', en: 'Master 11',
    keywords: ['直觉', '灵感', '洞察', '精神使命'],
    color: '#a855f7', bg: '#faf5ff',
    desc: '主命数 11，又称「灵感大师」，是最高灵性数字之一。您具有超凡的直觉与精神洞察力，能感知他人情绪与宇宙规律。使命是将灵性启示带给世界，须注意高敏感带来的情绪管理挑战。',
  },
  22: {
    title: '建筑大师', en: 'Master 22',
    keywords: ['宏图', '实践', '建设', '宏观'],
    color: '#0ea5e9', bg: '#f0f9ff',
    desc: '主命数 22，又称「建筑大师」，将灵感与实践完美结合。您能将宏伟蓝图化为现实，具有巨大影响力。适合承担大型项目或领导社会变革，须注意压力管理与团队协作。',
  },
  33: {
    title: '疗愈大师', en: 'Master 33',
    keywords: ['疗愈', '奉献', '慈悲', '真理'],
    color: '#10b981', bg: '#ecfdf5',
    desc: '主命数 33，又称「疗愈大师」，是博爱与慈悲的最高体现。您的使命是以无条件的爱疗愈世界。在达到此层次之前，需先展现 22（建设）和 11（灵感）的双重能量。',
  },
}

function getMeaning(n: number | null): NumMeaning | null {
  if (n === null) return null
  return MEANINGS[n] ?? MEANINGS[Math.max(1, Math.min(9, n))] ?? null
}

// ── 出生日期数字拆解（视觉用） ─────────────────────────────────
interface DatePart { digit: number; section: 'year' | 'month' | 'day' }

const dateBreakdown = computed<DatePart[]>(() => {
  if (!form.value.date) return []
  const [y, m, d] = form.value.date.split('-')
  return [
    ...y.split('').map(n => ({ digit: Number(n), section: 'year' as const })),
    ...m.split('').map(n => ({ digit: Number(n), section: 'month' as const })),
    ...d.split('').map(n => ({ digit: Number(n), section: 'day' as const })),
  ]
})

// ── 名字字母高亮（元音/辅音区分显示） ──────────────────────────
interface LetterInfo { char: string; value: number; isVowel: boolean }

const nameLetters = computed<LetterInfo[]>(() => {
  return form.value.name
    .toUpperCase()
    .replace(/[^A-Z ]/g, '')
    .split('')
    .map(c => ({
      char: c,
      value: PYTH[c] ?? 0,
      isVowel: VOWELS.has(c),
    }))
})

// ── 数字卡片配置列表（用于遍历） ───────────────────────────────
interface NumCard {
  label: string
  sub: string
  val: number | null
  tip: string
}

const numCards = computed<NumCard[]>(() => [
  {
    label: '生命路径数',
    sub: 'Life Path Number',
    val: lifePath.value,
    tip: '出生日期所有数字之和化减，代表您此生的使命与旅程方向。',
  },
  {
    label: '表达数',
    sub: 'Expression Number',
    val: expressionNum.value,
    tip: '姓名所有字母数值之和，代表您的天赋才能与对外展现。',
  },
  {
    label: '灵魂冲动数',
    sub: 'Soul Urge Number',
    val: soulUrgeNum.value,
    tip: '姓名中元音字母之和，代表您内心深处的渴望与动机。',
  },
  {
    label: '性格数',
    sub: 'Personality Number',
    val: personalityNum.value,
    tip: '姓名中辅音字母之和，代表您呈现给外界的第一印象与形象。',
  },
  {
    label: '生日数',
    sub: 'Birthday Number',
    val: birthdayNum.value,
    tip: '出生日（1–31）化减后，代表您的特别天赋与才能。',
  },
])
</script>

<template>
  <div class="nm-wrap">
    <!-- 标题 -->
    <div class="nm-header">
      <h1 class="nm-title">数字学 · 使命数解析</h1>
      <p class="nm-subtitle">§7.1 皮达哥拉斯数字学（Pythagorean Numerology）+ 中文姓名笔画数字学</p>
    </div>

    <!-- 模式切换 -->
    <div class="nm-mode-bar">
      <button class="nm-mode-btn" :class="{ active: !cnNameMode }" @click="cnNameMode = false">
        🔤 英文 / 拼音模式
      </button>
      <button class="nm-mode-btn" :class="{ active: cnNameMode }" @click="cnNameMode = true">
        汉 中文笔画模式
      </button>
    </div>

    <!-- ── 英文/拼音模式 ─────────────────────────────────────── -->
    <template v-if="!cnNameMode">
    <!-- 输入表单 -->
    <div class="nm-form-card">
      <div class="nm-form-row">
        <div class="nm-field">
          <label class="nm-label">出生日期</label>
          <input v-model="form.date" type="date" class="nm-input" />
        </div>
        <div class="nm-field nm-field-wide">
          <label class="nm-label">姓名（英文 / 拼音，用于名字数字）</label>
          <input v-model="form.name" type="text" class="nm-input"
            placeholder="如 Zhang Wei / John Smith" maxlength="60" />
        </div>
      </div>

      <!-- 出生日期数字拆解视图 -->
      <div v-if="dateBreakdown.length" class="nm-digits-row">
        <span class="nm-digits-hint">出生日期数字：</span>
        <template v-for="(p, i) in dateBreakdown" :key="i">
          <span class="nm-sep" v-if="i === 4 || i === 6">·</span>
          <span class="nm-digit-pill" :class="'nm-digit-' + p.section">{{ p.digit }}</span>
        </template>
        <span class="nm-eq">→ 合计 {{ form.date.replace(/-/g,'').split('').map(Number).reduce((a,b)=>a+b,0) }}</span>
        <span class="nm-eq2" v-if="lifePath !== null">→ 生命路径数
          <strong>{{ lifePath }}</strong>
        </span>
      </div>

      <!-- 名字字母分析 -->
      <div v-if="nameLetters.length" class="nm-letters-row">
        <span class="nm-digits-hint">名字字母解析：</span>
        <template v-for="(l, i) in nameLetters" :key="i">
          <span v-if="l.char === ' '" class="nm-letter-space"></span>
          <span v-else class="nm-letter-pill" :class="l.isVowel ? 'nm-vowel' : 'nm-consonant'"
            :title="l.isVowel ? '元音' : '辅音'">
            <span class="nm-lc">{{ l.char }}</span>
            <span class="nm-lv">{{ l.value }}</span>
          </span>
        </template>
        <div class="nm-letter-legend">
          <span class="nm-legend-dot nm-vowel-dot"></span>元音（灵魂冲动数）
          <span class="nm-legend-dot nm-cons-dot" style="margin-left:10px"></span>辅音（性格数）
        </div>
      </div>
    </div>

    <!-- 数字结果卡片 -->
    <div v-if="lifePath !== null || expressionNum !== null" class="nm-cards-grid">
      <template v-for="card in numCards" :key="card.label">
        <div v-if="card.val !== null" class="nm-card"
          :style="{ borderLeftColor: getMeaning(card.val)?.color ?? '#94a3b8' }">
          <!-- 数字大圆 -->
          <div class="nm-big-num"
            :style="{
              color: getMeaning(card.val)?.color ?? '#94a3b8',
              background: getMeaning(card.val)?.bg ?? '#f8fafc',
            }">
            {{ card.val }}
          </div>
          <!-- 文字区 -->
          <div class="nm-card-body">
            <div class="nm-card-label">{{ card.label }}</div>
            <div class="nm-card-sub">{{ card.sub }}</div>
            <div class="nm-card-meaning-title">
              {{ getMeaning(card.val)?.title ?? '' }}
              <span class="nm-card-en">{{ getMeaning(card.val)?.en }}</span>
            </div>
            <!-- 关键词 -->
            <div class="nm-keywords">
              <span
                v-for="kw in getMeaning(card.val)?.keywords"
                :key="kw"
                class="nm-kw"
                :style="{ background: (getMeaning(card.val)?.color ?? '#94a3b8') + '22',
                          color: getMeaning(card.val)?.color ?? '#64748b' }"
              >{{ kw }}</span>
            </div>
            <p class="nm-card-desc">{{ getMeaning(card.val)?.desc }}</p>
            <div class="nm-card-tip">💡 {{ card.tip }}</div>
          </div>
        </div>
      </template>
    </div>

    <!-- 空态 -->
    <div v-if="!lifePath && !expressionNum" class="nm-empty">
      <div class="nm-empty-icon">🔢</div>
      <p>请填写出生日期，可选填姓名（英文/拼音）以获取全套数字解析</p>
      <div class="nm-sys-note">
        <strong>数字系统说明：</strong>皮达哥拉斯方法将 A–Z 分别映射到 1–9，
        逐步化减（保留主命数 11、22、33），揭示宇宙蓝图中的使命编码。
      </div>
    </div>

    <!-- 系统说明 -->
    <div v-else class="nm-footer-note">
      <strong>皮达哥拉斯系统：</strong>
      A=1 B=2 C=3 D=4 E=5 F=6 G=7 H=8 I=9 &nbsp;|&nbsp;
      J=1 K=2 L=3 M=4 N=5 O=6 P=7 Q=8 R=9 &nbsp;|&nbsp;
      S=1 T=2 U=3 V=4 W=5 X=6 Y=7 Z=8
    </div>
    </template>

    <!-- ── 中文笔画数字学模式 ─────────────────────────────────── -->
    <template v-else>
      <div class="nm-form-card">
        <div class="nm-form-row">
          <div class="nm-field">
            <label class="nm-label">出生日期（可选，用于生命路径数）</label>
            <input v-model="form.date" type="date" class="nm-input" />
          </div>
          <div class="nm-field nm-field-wide">
            <label class="nm-label">中文姓名</label>
            <div class="nm-cn-row">
              <input v-model="cnName" type="text" class="nm-input nm-input-cn"
                placeholder="如：张伟 / 李晓月" maxlength="10"
                @keyup.enter="analyzeCnName" />
              <button class="nm-cn-btn" :disabled="cnLoading || !cnName.trim()" @click="analyzeCnName">
                {{ cnLoading ? '计算中…' : '计算笔画' }}
              </button>
            </div>
          </div>
        </div>
        <p v-if="cnError" class="nm-cn-error">{{ cnError }}</p>
      </div>

      <!-- 中文笔画结果 -->
      <template v-if="cnResult">
        <!-- 每字笔画拆解 -->
        <div class="nm-cn-breakdown">
          <span class="nm-digits-hint">逐字笔画：</span>
          <div v-for="ci in cnResult.chars" :key="ci.char" class="nm-cn-char-pill">
            <span class="nm-cn-char">{{ ci.char }}</span>
            <span class="nm-cn-strokes">{{ ci.strokes }}画</span>
            <span class="nm-cn-digit" :style="{ color: getMeaning(ci.numerology_digit)?.color }">→ {{ ci.numerology_digit }}</span>
          </div>
          <span class="nm-eq">总笔画 {{ cnResult.total_strokes }}</span>
        </div>

        <!-- 生命路径数（若填了日期） + 表达数 -->
        <div class="nm-cards-grid">
          <div v-if="lifePath !== null" class="nm-card"
            :style="{ borderLeftColor: getMeaning(lifePath)?.color ?? '#94a3b8' }">
            <div class="nm-big-num"
              :style="{ color: getMeaning(lifePath)?.color, background: getMeaning(lifePath)?.bg }">
              {{ lifePath }}
            </div>
            <div class="nm-card-body">
              <div class="nm-card-label">生命路径数</div>
              <div class="nm-card-sub">Life Path Number</div>
              <div class="nm-card-meaning-title">
                {{ getMeaning(lifePath)?.title }}
                <span class="nm-card-en">{{ getMeaning(lifePath)?.en }}</span>
              </div>
              <div class="nm-keywords">
                <span v-for="kw in getMeaning(lifePath)?.keywords" :key="kw" class="nm-kw"
                  :style="{ background: (getMeaning(lifePath)?.color ?? '#94a3b8') + '22', color: getMeaning(lifePath)?.color }">{{ kw }}</span>
              </div>
              <p class="nm-card-desc">{{ getMeaning(lifePath)?.desc }}</p>
            </div>
          </div>

          <div class="nm-card"
            :style="{ borderLeftColor: getMeaning(cnResult.expression_number)?.color ?? '#94a3b8' }">
            <div class="nm-big-num"
              :style="{ color: getMeaning(cnResult.expression_number)?.color, background: getMeaning(cnResult.expression_number)?.bg }">
              {{ cnResult.expression_number }}
            </div>
            <div class="nm-card-body">
              <div class="nm-card-label">表达数（笔画化减）</div>
              <div class="nm-card-sub">Expression Number · Stroke-based</div>
              <div class="nm-card-meaning-title">
                {{ getMeaning(cnResult.expression_number)?.title }}
                <span class="nm-card-en">{{ getMeaning(cnResult.expression_number)?.en }}</span>
              </div>
              <div class="nm-keywords">
                <span v-for="kw in getMeaning(cnResult.expression_number)?.keywords" :key="kw" class="nm-kw"
                  :style="{ background: (getMeaning(cnResult.expression_number)?.color ?? '#94a3b8') + '22', color: getMeaning(cnResult.expression_number)?.color }">{{ kw }}</span>
              </div>
              <p class="nm-card-desc">{{ getMeaning(cnResult.expression_number)?.desc }}</p>
              <div class="nm-card-tip">💡 中文姓名「{{ cnResult.name }}」总笔画 {{ cnResult.total_strokes }}，化减为表达数 {{ cnResult.expression_number }}。</div>
            </div>
          </div>
        </div>
      </template>

      <!-- 空态 -->
      <div v-else class="nm-empty">
        <div class="nm-empty-icon">汉</div>
        <p>输入中文姓名，系统将逐字查询笔画数并进行命理化减</p>
        <div class="nm-sys-note">
          <strong>笔画数字学：</strong>每个汉字的笔画数对应数字能量，
          全名笔画总数经过命理化减（保留主命数11/22/33），得出表达数。
          适合结合八字用神、五行喜忌选择姓名。
        </div>
      </div>
    </template>
  </div>
</template>

<style src="./NumerologyView.css" scoped />
