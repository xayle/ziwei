<script setup lang="ts">
/**
 * TarotView.vue — 塔罗牌（§7.2）
 * 功能：大阿尔卡那 22 张 | 出生牌计算 | 单抽 | 三牌阵（过去/现在/未来）
 * 全部前端计算，无需后端
 */
import { ref, computed } from 'vue'

// ── 大阿尔卡那数据 ───────────────────────────────────────────
interface Card {
  num:     number
  name:    string
  cn:      string
  emoji:   string
  keyword: string
  upright: string
  reversed: string
  advice:  string
  color:   string
}

const MAJOR_ARCANA: Card[] = [
  {
    num: 0, name: 'The Fool', cn: '愚者', emoji: '🃏',
    keyword: '新的开始·纯真·冒险',
    upright: '踏上全新旅程，以开放之心拥抱未知，充满纯真勇气。',
    reversed: '鲁莽草率，逃避现实，缺乏方向与计划。',
    advice: '勇敢踏出第一步，相信旅途自有引导。',
    color: '#f59e0b',
  },
  {
    num: 1, name: 'The Magician', cn: '魔术师', emoji: '🪄',
    keyword: '意志力·行动·创造',
    upright: '拥有实现目标所需一切资源，意志坚定，行动力强。',
    reversed: '操控他人，才华空转，缺乏专注。',
    advice: '集中意志，将内在潜能化为具体行动。',
    color: '#ef4444',
  },
  {
    num: 2, name: 'The High Priestess', cn: '女祭司', emoji: '🌙',
    keyword: '直觉·内在智慧·神秘',
    upright: '聆听内心直觉，深藏的智慧正在提示你答案。',
    reversed: '封闭内心，忽视直觉，秘密与隐藏。',
    advice: '静下心来，内在的声音才是你真正的向导。',
    color: '#6366f1',
  },
  {
    num: 3, name: 'The Empress', cn: '女皇', emoji: '🌸',
    keyword: '丰盛·创造力·滋养',
    upright: '生命力旺盛，丰盛到来，创造与自然之美。',
    reversed: '依赖、过度保护，或缺乏自我价值。',
    advice: '拥抱自然节律，滋养自己与周围的人。',
    color: '#22c55e',
  },
  {
    num: 4, name: 'The Emperor', cn: '皇帝', emoji: '👑',
    keyword: '权威·稳定·秩序',
    upright: '建立秩序与结构，以权威和耐心掌控局面。',
    reversed: '专制、刚愎自用，或缺乏掌控力，。',
    advice: '建立清晰边界和规则，成为自己生活的主导者。',
    color: '#f97316',
  },
  {
    num: 5, name: 'The Hierophant', cn: '教皇', emoji: '⛪',
    keyword: '传统·信仰·指导',
    upright: '遵循传统与制度，寻求精神指引和道德秩序。',
    reversed: '固执于旧规，反叛权威，盲目追从。',
    advice: '在传统智慧中寻找指引，同时保持独立判断。',
    color: '#8b5cf6',
  },
  {
    num: 6, name: 'The Lovers', cn: '恋人', emoji: '💑',
    keyword: '爱情·选择·价值观',
    upright: '深刻的情感连接，重要的价值观选择到来。',
    reversed: '关系失衡，与内心价值脱节，错误选择。',
    advice: '跟随内心真实的渴望做出选择。',
    color: '#ec4899',
  },
  {
    num: 7, name: 'The Chariot', cn: '战车', emoji: '⚔️',
    keyword: '意志力·掌控·胜利',
    upright: '以坚定意志和自律驾驭局面，走向胜利。',
    reversed: '失控、方向混乱，强行为之。',
    advice: '保持专注与自律，以意志力克服前进的阻碍。',
    color: '#3b82f6',
  },
  {
    num: 8, name: 'Strength', cn: '力量', emoji: '🦁',
    keyword: '内在力量·耐心·勇气',
    upright: '以柔克刚，温柔而坚韧，内在力量战胜困境。',
    reversed: '怀疑自我，压抑本能，软弱与怯懦。',
    advice: '相信内在的勇气，用温柔而坚定的方式面对挑战。',
    color: '#f97316',
  },
  {
    num: 9, name: 'The Hermit', cn: '隐者', emoji: '🏔️',
    keyword: '内省·独处·智慧',
    upright: '向内探索，智慧从沉思与孤独中涌现。',
    reversed: '孤立无援，拒绝建议，与世隔绝。',
    advice: '给自己独处的时间，答案就在内心深处。',
    color: '#475569',
  },
  {
    num: 10, name: 'Wheel of Fortune', cn: '命运之轮', emoji: '☸️',
    keyword: '命运·循环·转机',
    upright: '命运转轮开始运转，好运与机遇随之而来。',
    reversed: '逆境来临，感到命运摆布，抵制变化。',
    advice: '顺应宇宙节律，把握变化中的机遇。',
    color: '#f59e0b',
  },
  {
    num: 11, name: 'Justice', cn: '正义', emoji: '⚖️',
    keyword: '公正·真相·因果',
    upright: '公平的裁断到来，因果法则起作用。',
    reversed: '不公平、不诚实，逃避责任。',
    advice: '诚实面对自己的行动，因果终将显现。',
    color: '#6366f1',
  },
  {
    num: 12, name: 'The Hanged Man', cn: '倒吊人', emoji: '🙃',
    keyword: '暂停·牺牲·新视角',
    upright: '暂时放弃掌控，以全新视角看待局面。',
    reversed: '无谓的牺牲，拖延，缺乏放手的勇气。',
    advice: '放慢节奏，换个视角，静候时机。',
    color: '#0ea5e9',
  },
  {
    num: 13, name: 'Death', cn: '死神', emoji: '💀',
    keyword: '转变·终结·重生',
    upright: '旧事即将画上句号，新阶段的开始。',
    reversed: '抗拒改变，停滞不前，无法放下过去。',
    advice: '勇敢放手旧的，才能迎接新的开始。',
    color: '#1e293b',
  },
  {
    num: 14, name: 'Temperance', cn: '节制', emoji: '🏺',
    keyword: '平衡·节制·调和',
    upright: '在各种力量间找到和谐与平衡，耐心调配。',
    reversed: '失衡、过激行为，缺乏中庸之道。',
    advice: '慢下来，寻求中道，以平衡滋养生命。',
    color: '#10b981',
  },
  {
    num: 15, name: 'The Devil', cn: '恶魔', emoji: '😈',
    keyword: '束缚·欲望·阴影',
    upright: '受困于物质欲望或有害模式，需要正视阴影面。',
    reversed: '从束缚中解脱，直面恐惧与阴暗面。',
    advice: '意识到自己的枷锁，才能开始走向自由。',
    color: '#dc2626',
  },
  {
    num: 16, name: 'The Tower', cn: '高塔', emoji: '🗼',
    keyword: '破坏·突变·启示',
    upright: '突如其来的变故动摇基础，但清除了虚假结构。',
    reversed: '逃避必要的改变，或恐惧崩溃。',
    advice: '接受这场破坏，它将为更坚实的基础清路。',
    color: '#b45309',
  },
  {
    num: 17, name: 'The Star', cn: '星星', emoji: '⭐',
    keyword: '希望·疗愈·灵感',
    upright: '困境过后，清明与希望降临，内心得到疗愈。',
    reversed: '灰心丧气，失去信心，空洞的希望。',
    advice: '相信光明终将到来，以感恩之心接纳治愈。',
    color: '#38bdf8',
  },
  {
    num: 18, name: 'The Moon', cn: '月亮', emoji: '🌕',
    keyword: '幻象·潜意识·恐惧',
    upright: '潜意识浮现，事物并非表面所见，需要辨别幻象。',
    reversed: '面对潜意识恐惧，混乱渐散，真相浮现。',
    advice: '深入潜意识，分辨恐惧与直觉。',
    color: '#818cf8',
  },
  {
    num: 19, name: 'The Sun', cn: '太阳', emoji: '☀️',
    keyword: '喜悦·活力·成功',
    upright: '充满阳光与喜悦，真诚的自我得到彰显，成功在望。',
    reversed: '过于乐观，自恋，或缺乏方向的欢愉。',
    advice: '以真诚的喜悦生活，你的光芒将照耀四方。',
    color: '#eab308',
  },
  {
    num: 20, name: 'Judgement', cn: '审判', emoji: '📣',
    keyword: '觉醒·召唤·转化',
    upright: '内心的觉醒与呼唤，审视过去、做出顿悟。',
    reversed: '自我批判，拒绝内心召唤，无法释怀。',
    advice: '聆听内心深处的呼唤，是时候完成蜕变了。',
    color: '#f97316',
  },
  {
    num: 21, name: 'The World', cn: '世界', emoji: '🌍',
    keyword: '完成·成就·整合',
    upright: '一个重要循环圆满完成，充满成就感与整合。',
    reversed: '缺少收尾，半途而废，对完成感不满足。',
    advice: '庆祝你的旅程成就，带着完整感迎接下一段。',
    color: '#10b981',
  },
]

// ── 出生牌计算 ───────────────────────────────────────────────
const birthDate = ref('')

function calcBirthCard(dateStr: string): Card | null {
  if (!dateStr) return null
  const [y, m, d] = dateStr.split('-').map(Number)
  if (!y || !m || !d) return null
  // 各位数字相加直到 ≤ 22
  const digits = `${y}${m}${d}`.split('').map(Number)
  let sum = digits.reduce((a, b) => a + b, 0)
  while (sum > 21) {
    sum = String(sum).split('').map(Number).reduce((a, b) => a + b, 0)
  }
  return MAJOR_ARCANA[sum] ?? MAJOR_ARCANA[0]
}

const birthCard = computed(() => calcBirthCard(birthDate.value))

// ── 抽牌（单张） ───────────────────────────────────────────
const drawnCard    = ref<{ card: Card; reversed: boolean } | null>(null)
const drawAnimating = ref(false)

function drawCard() {
  drawAnimating.value = true
  drawnCard.value = null
  setTimeout(() => {
    const card     = MAJOR_ARCANA[Math.floor(Math.random() * 22)]
    const reversed = Math.random() < 0.3
    drawnCard.value  = { card, reversed }
    drawAnimating.value = false
  }, 600)
}

// ── 三牌阵 ────────────────────────────────────────────────
interface SpreadCard { card: Card; reversed: boolean; position: string }

const spreadCards  = ref<SpreadCard[]>([])
const spreadAnim   = ref(false)
const POSITIONS    = ['过去', '现在', '未来']

function drawSpread() {
  spreadAnim.value = true
  spreadCards.value = []
  const indices = new Set<number>()
  while (indices.size < 3) indices.add(Math.floor(Math.random() * 22))
  setTimeout(() => {
    spreadCards.value = Array.from(indices).map((i, j) => ({
      card:     MAJOR_ARCANA[i],
      reversed: Math.random() < 0.3,
      position: POSITIONS[j],
    }))
    spreadAnim.value = false
  }, 700)
}

// ── 选中卡详情 ────────────────────────────────────────────
const selectedCard = ref<{ card: Card; reversed: boolean } | null>(null)
</script>

<template>
  <div class="tr-wrap">
    <!-- 标题 -->
    <div class="tr-header">
      <h1 class="tr-title">塔罗牌 · 大阿尔卡那</h1>
      <p class="tr-subtitle">§7.2 出生牌 · 单张占卜 · 三牌阵（22 张大阿尔卡那）</p>
    </div>

    <!-- ── 三大功能区 ── -->
    <div class="tr-sections">

      <!-- §1 出生牌 -->
      <section class="tr-section">
        <h2 class="tr-sec-title">出生牌计算</h2>
        <p class="tr-sec-desc">输入生日，推算你的灵魂牌与生命牌。算法：出生年月日所有数字相加 → 化简至 0–21。</p>
        <div class="tr-birth-row">
          <input v-model="birthDate" type="date" class="tr-input" />
          <button class="tr-btn tr-btn-sm" v-if="birthDate" @click="birthDate = ''">清除</button>
        </div>
        <transition name="tr-fade">
          <div v-if="birthCard" class="tr-birth-result">
            <div class="tr-card-chip" :style="{ background: birthCard.color + '22', borderColor: birthCard.color }">
              <span class="tr-card-emoji">{{ birthCard.emoji }}</span>
              <div>
                <div class="tr-card-num">{{ String(birthCard.num).padStart(2,'0') }}</div>
                <div class="tr-card-cn" :style="{ color: birthCard.color }">{{ birthCard.cn }}</div>
                <div class="tr-card-en">{{ birthCard.name }}</div>
              </div>
            </div>
            <div class="tr-card-kw">关键词：{{ birthCard.keyword }}</div>
            <div class="tr-card-text">{{ birthCard.upright }}</div>
            <div class="tr-card-advice">建议：{{ birthCard.advice }}</div>
          </div>
        </transition>
      </section>

      <!-- §2 单张抽牌 -->
      <section class="tr-section">
        <h2 class="tr-sec-title">单张占卜</h2>
        <p class="tr-sec-desc">心中默念你的问题，再抽取一张牌。</p>
        <button class="tr-btn" :disabled="drawAnimating" @click="drawCard">
          {{ drawAnimating ? '牌正在翻转…' : '🔮 抽一张牌' }}
        </button>
        <transition name="tr-fade">
          <div v-if="drawnCard && !drawAnimating" class="tr-single-result">
            <div class="tr-card-big" :style="{ borderColor: drawnCard.card.color }" @click="selectedCard = drawnCard">
              <div class="tr-card-header" :style="{ background: drawnCard.card.color }">
                <span class="tr-num-badge">{{ String(drawnCard.card.num).padStart(2,'0') }}</span>
                <span v-if="drawnCard.reversed" class="tr-rev-badge">逆位</span>
              </div>
              <div class="tr-big-emoji">{{ drawnCard.card.emoji }}</div>
              <div class="tr-big-cn" :style="{ color: drawnCard.card.color }">{{ drawnCard.card.cn }}</div>
              <div class="tr-big-en">{{ drawnCard.card.name }}</div>
              <div class="tr-big-kw">{{ drawnCard.card.keyword }}</div>
            </div>
            <div class="tr-card-meaning">
              <div class="tr-meaning-badge" :style="{ color: drawnCard.reversed ? '#ef4444' : '#22c55e' }">
                {{ drawnCard.reversed ? '逆位含义' : '正位含义' }}
              </div>
              <p class="tr-meaning-text">{{ drawnCard.reversed ? drawnCard.card.reversed : drawnCard.card.upright }}</p>
              <div class="tr-meaning-badge" style="color: var(--accent)">建议</div>
              <p class="tr-meaning-text">{{ drawnCard.card.advice }}</p>
            </div>
          </div>
        </transition>
      </section>

      <!-- §3 三牌阵 -->
      <section class="tr-section">
        <h2 class="tr-sec-title">三牌阵 · 过去 · 现在 · 未来</h2>
        <p class="tr-sec-desc">三张牌分别代表时间轴上的三个维度，揭示事件脉络。</p>
        <button class="tr-btn" :disabled="spreadAnim" @click="drawSpread">
          {{ spreadAnim ? '牌阵展开中…' : '🃏 展开三牌阵' }}
        </button>
        <transition name="tr-fade">
          <div v-if="spreadCards.length === 3 && !spreadAnim" class="tr-spread">
            <div class="tr-spread-col" v-for="sc in spreadCards" :key="sc.position">
              <div class="tr-pos-label">{{ sc.position }}</div>
              <div class="tr-card-big tr-spread-card"
                :style="{ borderColor: sc.card.color, transform: sc.reversed ? 'rotate(180deg)' : 'none' }"
                @click="selectedCard = sc">
                <div class="tr-card-header" :style="{ background: sc.card.color }">
                  <span class="tr-num-badge">{{ String(sc.card.num).padStart(2,'0') }}</span>
                  <span v-if="sc.reversed" class="tr-rev-badge">逆</span>
                </div>
                <div class="tr-big-emoji">{{ sc.card.emoji }}</div>
                <div class="tr-big-cn" :style="{ color: sc.card.color }">{{ sc.card.cn }}</div>
                <div class="tr-big-en">{{ sc.card.name }}</div>
              </div>
              <!-- 含义（不翻转显示） -->
              <div class="tr-spread-meaning" :style="{ transform: sc.reversed ? 'rotate(180deg)' : 'none' }">
                <strong style="font-size:11px; color: var(--text-3)">{{ sc.reversed ? '逆位' : '正位' }}</strong>
                <p class="tr-spread-text">{{ sc.reversed ? sc.card.reversed : sc.card.upright }}</p>
              </div>
            </div>
          </div>
        </transition>
      </section>
    </div>

    <!-- ── 牌库浏览 ── -->
    <section class="tr-section tr-section-gallery">
      <h2 class="tr-sec-title">大阿尔卡那牌库（22 张）</h2>
      <div class="tr-gallery">
        <button
          v-for="card in MAJOR_ARCANA" :key="card.num"
          class="tr-mini-card"
          :style="{ borderColor: card.color }"
          @click="selectedCard = { card, reversed: false }"
        >
          <span class="tr-mini-emoji">{{ card.emoji }}</span>
          <span class="tr-mini-num" :style="{ color: card.color }">{{ String(card.num).padStart(2,'0') }}</span>
          <span class="tr-mini-cn">{{ card.cn }}</span>
        </button>
      </div>
    </section>

    <!-- ── 详情蒙层 ── -->
    <transition name="tr-fade">
      <div v-if="selectedCard" class="tr-overlay" @click.self="selectedCard = null">
        <div class="tr-modal">
          <button class="tr-close" @click="selectedCard = null">✕</button>
          <div class="tr-modal-header" :style="{ background: selectedCard.card.color }">
            <span class="tr-modal-emoji">{{ selectedCard.card.emoji }}</span>
            <div>
              <div class="tr-modal-num">{{ String(selectedCard.card.num).padStart(2,'0') }}</div>
              <div class="tr-modal-cn">{{ selectedCard.card.cn }}</div>
              <div class="tr-modal-en">{{ selectedCard.card.name }}</div>
            </div>
          </div>
          <div class="tr-modal-body">
            <div class="tr-modal-kw">关键词：{{ selectedCard.card.keyword }}</div>
            <div class="tr-modal-sec">正位含义</div>
            <p class="tr-modal-text">{{ selectedCard.card.upright }}</p>
            <div class="tr-modal-sec">逆位含义</div>
            <p class="tr-modal-text">{{ selectedCard.card.reversed }}</p>
            <div class="tr-modal-sec">建议</div>
            <p class="tr-modal-text">{{ selectedCard.card.advice }}</p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.tr-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}
.tr-header { margin-bottom: 24px; }
.tr-title { font-size: 22px; font-weight: 700; color: var(--text); font-family: var(--font-cn); margin: 0; }
.tr-subtitle { font-size: 12px; color: var(--text-3); margin: 4px 0 0; }

/* ── 功能区 ─────────────────────────────────────────────────── */
.tr-sections { display: flex; flex-direction: column; gap: 28px; margin-bottom: 32px; }
.tr-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 24px;
}
.tr-section-gallery { padding: 22px 24px; }
.tr-sec-title { font-size: 16px; font-weight: 700; color: var(--text); font-family: var(--font-cn); margin: 0 0 6px; }
.tr-sec-desc  { font-size: 12px; color: var(--text-3); font-family: var(--font-cn); margin: 0 0 14px; line-height: 1.6; }

/* ── 出生牌 ─────────────────────────────────────────────────── */
.tr-birth-row { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.tr-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  font-family: var(--font-mono);
  outline: none;
}
.tr-input:focus { border-color: var(--accent); }

.tr-birth-result { display: flex; flex-direction: column; gap: 10px; }
.tr-card-chip {
  display: flex; align-items: center; gap: 14px;
  border: 2px solid; border-radius: 12px;
  padding: 14px 18px;
  max-width: 340px;
}
.tr-card-emoji { font-size: 36px; }
.tr-card-num { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }
.tr-card-cn  { font-size: 20px; font-weight: 800; font-family: var(--font-cn); }
.tr-card-en  { font-size: 12px; color: var(--text-3); }
.tr-card-kw  { font-size: 13px; font-weight: 600; color: var(--text); font-family: var(--font-cn); }
.tr-card-text { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.6; }
.tr-card-advice { font-size: 12px; color: var(--accent); font-family: var(--font-cn); line-height: 1.6; }

/* ── 按钮 ────────────────────────────────────────────────────── */
.tr-btn {
  padding: 10px 24px;
  background: var(--accent);
  color: #fff;
  border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  font-family: var(--font-cn);
  margin-bottom: 16px;
}
.tr-btn:hover:not(:disabled) { background: var(--accent-dark); }
.tr-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.tr-btn-sm { padding: 6px 14px; font-size: 13px; margin: 0; }

/* ── 大牌 ────────────────────────────────────────────────────── */
.tr-single-result { display: flex; align-items: flex-start; gap: 20px; flex-wrap: wrap; }
.tr-card-big {
  width: 140px; border: 2px solid; border-radius: 12px;
  overflow: hidden; cursor: pointer;
  transition: transform .2s;
  flex-shrink: 0;
}
.tr-card-big:hover { transform: scale(1.04); }
.tr-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 10px;
}
.tr-num-badge  { font-size: 11px; font-weight: 800; color: rgba(255,255,255,.9); font-family: var(--font-mono); }
.tr-rev-badge  { font-size: 10px; background: rgba(0,0,0,.3); color: #fff; padding: 1px 5px; border-radius: 6px; font-family: var(--font-cn); }
.tr-big-emoji  { font-size: 44px; text-align: center; padding: 12px 0 6px; display: block; }
.tr-big-cn     { font-size: 16px; font-weight: 800; text-align: center; font-family: var(--font-cn); display: block; }
.tr-big-en     { font-size: 10px; color: var(--text-3); text-align: center; padding: 4px 0 6px; display: block; }
.tr-big-kw     { font-size: 10px; color: var(--text-3); text-align: center; padding: 0 6px 10px; display: block; font-family: var(--font-cn); line-height: 1.4; }

.tr-card-meaning { flex: 1; min-width: 200px; }
.tr-meaning-badge { font-size: 12px; font-weight: 700; font-family: var(--font-cn); margin-bottom: 4px; margin-top: 12px; }
.tr-meaning-text  { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.7; margin: 0; }

/* ── 三牌阵 ─────────────────────────────────────────────────── */
.tr-spread { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 16px; }
.tr-spread-col { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.tr-pos-label { font-size: 14px; font-weight: 700; font-family: var(--font-cn); color: var(--text); }
.tr-spread-card { width: 110px; transition: transform .3s; }
.tr-spread-meaning { text-align: center; max-width: 160px; }
.tr-spread-text { font-size: 11px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.6; margin: 4px 0 0; }

/* ── 牌库 ────────────────────────────────────────────────────── */
.tr-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 10px;
}
.tr-mini-card {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  border: 1.5px solid; border-radius: 10px;
  padding: 10px 4px; background: var(--bg);
  cursor: pointer; transition: all .2s;
}
.tr-mini-card:hover { background: var(--surface); transform: translateY(-2px); }
.tr-mini-emoji { font-size: 22px; }
.tr-mini-num   { font-size: 10px; font-family: var(--font-mono); }
.tr-mini-cn    { font-size: 12px; font-weight: 700; font-family: var(--font-cn); color: var(--text); }

/* ── 蒙层 ────────────────────────────────────────────────────── */
.tr-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.tr-modal {
  width: 380px; max-width: 92vw;
  background: var(--surface);
  border-radius: 16px; overflow: hidden;
  position: relative;
}
.tr-close {
  position: absolute; top: 12px; right: 14px;
  background: rgba(0,0,0,.3); color: #fff;
  border: none; width: 28px; height: 28px;
  border-radius: 50%; cursor: pointer; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
  z-index: 1;
}
.tr-modal-header {
  display: flex; align-items: center; gap: 14px;
  padding: 24px 22px; color: #fff;
}
.tr-modal-emoji { font-size: 46px; }
.tr-modal-num { font-size: 12px; opacity: 0.8; font-family: var(--font-mono); }
.tr-modal-cn  { font-size: 22px; font-weight: 800; font-family: var(--font-cn); }
.tr-modal-en  { font-size: 13px; opacity: 0.85; }
.tr-modal-body { padding: 20px 22px; }
.tr-modal-kw  { font-size: 13px; font-weight: 600; color: var(--text); font-family: var(--font-cn); margin-bottom: 14px; }
.tr-modal-sec { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-3); letter-spacing: .05em; margin: 12px 0 4px; }
.tr-modal-text { font-size: 13px; color: var(--text-2); font-family: var(--font-cn); line-height: 1.7; margin: 0; }

/* ── 动画 ────────────────────────────────────────────────────── */
.tr-fade-enter-active, .tr-fade-leave-active { transition: opacity .3s, transform .3s; }
.tr-fade-enter-from, .tr-fade-leave-to { opacity: 0; transform: translateY(8px); }

/* ── 响应式 ─────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .tr-spread { grid-template-columns: 1fr; }
  .tr-single-result { flex-direction: column; }
}
</style>
