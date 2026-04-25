<script setup lang="ts">
/**
 * NumerologyView.vue — 数字学（§7.1）
 * 皮达哥拉斯数字学（Pythagorean Numerology）
 * 纯前端计算，无需后端
 */
import { ref, computed } from 'vue'

// ── 表单 ──────────────────────────────────────────────────────
const form = ref({
  date: '',
  name: '',
})

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
      <p class="nm-subtitle">§7.1 皮达哥拉斯数字学（Pythagorean Numerology）—— 纯前端计算，无需网络</p>
    </div>

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
  </div>
</template>

<style scoped>
/* ── 布局 ───────────────────────────────────────────────────── */
.nm-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 56px;
}

.nm-header { margin-bottom: 20px; }
.nm-title  { font-size: 22px; font-weight: 700; color: var(--text); margin: 0; font-family: var(--font-cn); }
.nm-subtitle { font-size: 12px; color: var(--text-3); margin: 4px 0 0; }

/* ── 表单卡片 ───────────────────────────────────────────────── */
.nm-form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.nm-form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 14px;
}

.nm-field { display: flex; flex-direction: column; gap: 5px; }
.nm-field-wide { flex: 1; min-width: 260px; }

.nm-label {
  font-size: 11px; color: var(--text-3); font-weight: 500;
  letter-spacing: .04em; text-transform: uppercase;
}

.nm-input {
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  outline: none;
  transition: border-color .15s;
  font-family: var(--font-mono);
}
.nm-input:focus { border-color: var(--accent); }

/* ── 日期数字拆解 ─────────────────────────────────────────── */
.nm-digits-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 10px 12px;
  background: var(--surface-2);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-2);
  margin-bottom: 10px;
}
.nm-digits-hint { font-size: 11px; color: var(--text-3); margin-right: 4px; }
.nm-sep { font-size: 14px; color: var(--border); margin: 0 2px; }
.nm-digit-pill {
  width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 6px;
  font-weight: 700; font-size: 14px; font-family: var(--font-mono);
}
.nm-digit-year  { background: #e0f2fe; color: #0284c7; }
.nm-digit-month { background: #dcfce7; color: #16a34a; }
.nm-digit-day   { background: #fef9c3; color: #ca8a04; }
.nm-eq  { font-size: 12px; color: var(--text-3); margin-left: 6px; }
.nm-eq2 { font-size: 13px; color: var(--text-2); margin-left: 6px; }
.nm-eq2 strong { color: var(--accent); font-size: 15px; }

/* ── 名字字母 ───────────────────────────────────────────────── */
.nm-letters-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 10px 12px;
  background: var(--surface-2);
  border-radius: 8px;
  font-size: 13px;
}
.nm-letter-space { width: 12px; }
.nm-letter-pill {
  display: inline-flex; flex-direction: column; align-items: center;
  width: 28px; border-radius: 6px; padding: 3px 0;
}
.nm-vowel    { background: #fdf4ff; border: 1px solid #e9d5ff; }
.nm-consonant { background: #f0f9ff; border: 1px solid #bae6fd; }
.nm-lc { font-size: 12px; font-weight: 700; line-height: 1.2; }
.nm-lv { font-size: 10px; font-family: var(--font-mono); color: var(--text-3); line-height: 1.2; }

.nm-letter-legend {
  width: 100%; font-size: 11px; color: var(--text-3); margin-top: 4px;
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
}
.nm-legend-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.nm-vowel-dot { background: #fdf4ff; border: 1px solid #e9d5ff; }
.nm-cons-dot  { background: #f0f9ff; border: 1px solid #bae6fd; }

/* ── 数字卡片网格 ─────────────────────────────────────────── */
.nm-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.nm-card {
  display: flex;
  gap: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid;
  border-radius: 12px;
  padding: 18px 20px;
  align-items: flex-start;
}

.nm-big-num {
  width: 68px; height: 68px; min-width: 68px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 30px; font-weight: 900;
  font-family: var(--font-mono);
  letter-spacing: -1px;
  border: 2px solid currentColor;
  opacity: 0.9;
}

.nm-card-body { flex: 1; }
.nm-card-label {
  font-size: 11px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .07em; margin-bottom: 1px;
}
.nm-card-sub { font-size: 10px; color: var(--text-3); margin-bottom: 6px; }
.nm-card-meaning-title {
  font-size: 18px; font-weight: 700; color: var(--text);
  font-family: var(--font-cn); margin-bottom: 8px;
}
.nm-card-en {
  font-size: 12px; font-weight: 400; color: var(--text-3);
  font-family: var(--font-ui); margin-left: 6px;
}

.nm-keywords { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.nm-kw {
  font-size: 11px; padding: 3px 9px;
  border-radius: 99px; font-weight: 600;
  font-family: var(--font-cn);
}

.nm-card-desc {
  font-size: 13px; color: var(--text-2); line-height: 1.7;
  font-family: var(--font-cn); margin: 0 0 8px;
}
.nm-card-tip {
  font-size: 11px; color: var(--text-3); background: var(--surface-2);
  padding: 6px 10px; border-radius: 6px; font-family: var(--font-cn);
  line-height: 1.5;
}

/* ── 空态 ───────────────────────────────────────────────────── */
.nm-empty {
  display: flex; flex-direction: column;
  align-items: center; padding: 50px 20px; gap: 12px;
  color: var(--text-3);
}
.nm-empty-icon { font-size: 48px; opacity: 0.3; }
.nm-empty p { font-size: 14px; font-family: var(--font-cn); text-align: center; }
.nm-sys-note {
  max-width: 480px; font-size: 12px; color: var(--text-3);
  font-family: var(--font-cn); text-align: center; line-height: 1.6;
  background: var(--surface-2); border-radius: 8px; padding: 12px 16px;
}

/* ── 底部说明 ────────────────────────────────────────────────── */
.nm-footer-note {
  margin-top: 20px;
  padding: 10px 16px;
  background: var(--surface-2);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-3);
  font-family: var(--font-mono);
  line-height: 1.8;
}

/* ── 响应式 ─────────────────────────────────────────────────── */
@media (max-width: 600px) {
  .nm-card { flex-direction: column; }
  .nm-big-num { align-self: center; }
}
</style>
