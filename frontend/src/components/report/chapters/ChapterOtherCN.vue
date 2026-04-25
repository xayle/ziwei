<script setup lang="ts">
/**
 * ChapterOtherCN.vue — ⑥ 中国传统命理补充
 * 生肖合局纯前端计算（来自出生年份）
 */
import { computed } from 'vue'
import { useReportStore } from '@/stores/report'

const store = useReportStore()

// ─── 生肖数据 ──────────────────────────────────────────────────
const ZODIAC_LIST = [
  { name: '鼠', emoji: '🐭', element: '水', desc: '机智灵敏，善于交际，适应力强' },
  { name: '牛', emoji: '🐂', element: '土', desc: '勤勉踏实，意志坚强，忍耐力佳' },
  { name: '虎', emoji: '🐯', element: '木', desc: '勇敢果断，热情豪爽，领导力强' },
  { name: '兔', emoji: '🐰', element: '木', desc: '温和善良，谨慎细心，艺术天赋' },
  { name: '龙', emoji: '🐲', element: '土', desc: '威严霸气，才华横溢，充满魅力' },
  { name: '蛇', emoji: '🐍', element: '火', desc: '聪明深沉，直觉敏锐，理财有道' },
  { name: '马', emoji: '🐴', element: '火', desc: '活泼开朗，自由奔放，行动力强' },
  { name: '羊', emoji: '🐑', element: '土', desc: '温柔体贴，有同情心，富有创意' },
  { name: '猴', emoji: '🐵', element: '金', desc: '聪颖灵活，机智幽默，多才多艺' },
  { name: '鸡', emoji: '🐓', element: '金', desc: '勤劳守信，条理分明，分析力强' },
  { name: '狗', emoji: '🐶', element: '土', desc: '忠诚可靠，正义感强，善解人意' },
  { name: '猪', emoji: '🐷', element: '水', desc: '善良单纯，乐观知足，注重享受' },
]

// 三合: 每组差4
const SANHÉ_GROUPS = [[0,4,8],[1,5,9],[2,6,10],[3,7,11]]
// 六合
const LIUHÉ: Record<number, number> = { 0:1, 1:0, 2:11, 11:2, 3:10, 10:3, 4:9, 9:4, 5:8, 8:5, 6:7, 7:6 }
// 六冲 (idx + 6) % 12
const WX_CSS: Record<string, string> = {
  '木': 'var(--wx-wood)', '火': 'var(--wx-fire)', '土': 'var(--wx-earth)',
  '金': 'var(--wx-metal)', '水': 'var(--wx-water)',
}

// ─── 计算 ─────────────────────────────────────────────────────
const birthYear = computed(() => {
  const dt = store.caseData?.birth_dt_local ?? ''
  return dt ? parseInt(dt.slice(0, 4), 10) : null
})

const zodiacIdx = computed(() => {
  if (birthYear.value == null) return null
  return ((birthYear.value - 4) % 12 + 12) % 12
})

const zodiac = computed(() => {
  if (zodiacIdx.value == null) return null
  return ZODIAC_LIST[zodiacIdx.value]
})

const sanhe = computed(() => {
  if (zodiacIdx.value == null) return []
  const g = SANHÉ_GROUPS.find(g => g.includes(zodiacIdx.value!))
  return g ? g.filter(i => i !== zodiacIdx.value).map(i => ZODIAC_LIST[i]) : []
})

const liuhe = computed(() => {
  if (zodiacIdx.value == null) return null
  const partner = LIUHÉ[zodiacIdx.value]
  return partner != null ? ZODIAC_LIST[partner] : null
})

const liuchong = computed(() => {
  if (zodiacIdx.value == null) return null
  return ZODIAC_LIST[(zodiacIdx.value + 6) % 12]
})

// 命格标签 (来自八字数据的格局)
const gejuTags = computed(() => {
  return (store.baziData as any)?.geju?.inference_tags ?? []
})

function onChip(term: string) {
  store.setGlossaryTerm(term)
}
</script>

<template>
  <div class="chapter-other">

    <div v-if="!store.caseData" class="empty-hint">
      <p>请先选择命盘案例</p>
    </div>

    <template v-else>

      <!-- ══ 6-1 生肖与合局 ══════════════════════════════════════════ -->
      <section id="section-6-1" class="section-block">
        <div class="section-title-row">
          <span class="section-num">6-1</span>
          <h2 class="section-title">生肖与合局</h2>
        </div>

        <div v-if="zodiac" class="zodiac-main">
          <!-- 大图标 + 基本信息 -->
          <div class="zodiac-hero">
            <div class="zodiac-emoji" :style="{ background: WX_CSS[zodiac.element] }">
              {{ zodiac.emoji }}
            </div>
            <div class="zodiac-info">
              <p class="zodiac-name">{{ zodiac.name }}年</p>
              <p class="zodiac-year">{{ birthYear }} 年</p>
              <span class="zodiac-el-badge" :style="{ background: WX_CSS[zodiac.element] }">
                {{ zodiac.element }}行
              </span>
              <p class="zodiac-desc">{{ zodiac.desc }}</p>
            </div>
          </div>

          <!-- 合局关系 -->
          <div class="he-grid">

            <!-- 三合 -->
            <div class="he-card">
              <p class="he-title">三合局</p>
              <p class="he-note">同气相合，事业好搭档</p>
              <div class="he-animals">
                <div v-for="z in sanhe" :key="z.name" class="he-animal">
                  <span class="ha-emoji">{{ z.emoji }}</span>
                  <span class="ha-name">{{ z.name }}</span>
                </div>
              </div>
            </div>

            <!-- 六合 -->
            <div class="he-card he-liuhe" v-if="liuhe">
              <p class="he-title">六合</p>
              <p class="he-note">缘分之合，情感最佳</p>
              <div class="he-animals">
                <div class="he-animal">
                  <span class="ha-emoji">{{ liuhe.emoji }}</span>
                  <span class="ha-name">{{ liuhe.name }}</span>
                </div>
              </div>
            </div>

            <!-- 六冲 -->
            <div class="he-card he-chong" v-if="liuchong">
              <p class="he-title">六冲</p>
              <p class="he-note">相冲相克，注意化解</p>
              <div class="he-animals">
                <div class="he-animal">
                  <span class="ha-emoji">{{ liuchong.emoji }}</span>
                  <span class="ha-name">{{ liuchong.name }}</span>
                </div>
              </div>
            </div>

          </div><!-- he-grid -->

          <!-- 12生肖一览 -->
          <div class="zodiac-ring">
            <p class="ring-label-txt">十二生肖对照</p>
            <div class="ring-grid">
              <div
                v-for="(z, i) in ZODIAC_LIST"
                :key="z.name"
                class="ring-cell"
                :class="{
                  'ring-active':   i === zodiacIdx,
                  'ring-sanhe':    sanhe.some(s => s.name === z.name),
                  'ring-liuhe':    liuhe?.name === z.name,
                  'ring-chong':    liuchong?.name === z.name,
                }"
                @click="onChip(z.name + '年')"
              >
                <span class="rc-emoji">{{ z.emoji }}</span>
                <span class="rc-name">{{ z.name }}</span>
              </div>
            </div>
            <div class="ring-legend">
              <span class="leg active-leg">● 本命</span>
              <span class="leg sanhe-leg">● 三合</span>
              <span class="leg liuhe-leg">● 六合</span>
              <span class="leg chong-leg">● 六冲</span>
            </div>
          </div>

        </div><!-- zodiac-main -->

        <div v-else class="empty-hint"><p>未能获取出生年份</p></div>
      </section>

      <!-- ══ 6-2 命格标签 ══════════════════════════════════════════ -->
      <section id="section-6-2" class="section-block">
        <div class="section-title-row">
          <span class="section-num">6-2</span>
          <h2 class="section-title">命格标签</h2>
        </div>

        <div v-if="gejuTags.length" class="tags-wrap">
          <span
            v-for="tag in gejuTags"
            :key="tag"
            class="geju-tag"
            @click="onChip(tag)"
          >{{ tag }}</span>
        </div>

        <div v-else class="tags-empty">
          <p class="empty-sm">八字格局标签需要先完成八字分析获取</p>
          <button class="btn-sec" @click="store.loadChapterData(2)">加载八字数据</button>
        </div>
      </section>

    </template>

  </div>
</template>

<style scoped>
.chapter-other { display: flex; flex-direction: column; gap: var(--sp-6); }

/* ─── 章节块 ─────────────────────────────────────────────────── */
.section-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-6);
  scroll-margin-top: 64px;
}
.section-title-row {
  display: flex; align-items: center; gap: var(--sp-3);
  margin-bottom: var(--sp-5); padding-bottom: var(--sp-3);
  border-bottom: 1px solid var(--border);
}
.section-num {
  font-size: var(--fs-xs); color: var(--text-3);
  font-family: var(--font-mono); background: var(--bg);
  padding: 2px 8px; border-radius: 99px; border: 1px solid var(--border);
}
.section-title { font-size: var(--fs-xl); font-weight: 700; color: var(--text); font-family: var(--font-cn); }

/* ─── 生肖主体 ───────────────────────────────────────────────── */
.zodiac-main { display: flex; flex-direction: column; gap: var(--sp-6); }

.zodiac-hero {
  display: flex;
  gap: var(--sp-5);
  align-items: flex-start;
}

.zodiac-emoji {
  font-size: 72px;
  line-height: 1;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  flex-shrink: 0;
  opacity: .9;
}

.zodiac-info { flex: 1; }
.zodiac-name { font-size: 32px; font-weight: 900; color: var(--text); font-family: var(--font-cn); }
.zodiac-year { font-size: var(--fs-sm); color: var(--text-3); font-family: var(--font-mono); margin-bottom: var(--sp-2); }
.zodiac-el-badge {
  display: inline-block; font-size: var(--fs-xs); color: #fff;
  padding: 2px 10px; border-radius: 99px; margin-bottom: var(--sp-3);
}
.zodiac-desc { font-size: var(--fs-sm); color: var(--text-2); line-height: 1.7; font-family: var(--font-cn); }

/* ─── 合局卡片 ───────────────────────────────────────────────── */
.he-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-4);
}

.he-card {
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.he-liuhe { border-color: var(--accent); }
.he-chong { border-color: var(--danger-dark); background: #fef2f2; }

.he-title { font-size: var(--fs-md); font-weight: 700; color: var(--text); font-family: var(--font-cn); margin-bottom: 2px; }
.he-note { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: var(--sp-3); }

.he-animals { display: flex; gap: var(--sp-3); flex-wrap: wrap; }
.he-animal { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.ha-emoji { font-size: 28px; }
.ha-name { font-size: var(--fs-xs); color: var(--text-2); font-family: var(--font-cn); }

/* ─── 12生肖圆盘 ─────────────────────────────────────────────── */
.zodiac-ring {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--sp-4);
}

.ring-label-txt { font-size: var(--fs-xs); color: var(--text-3); margin-bottom: var(--sp-3); }

.ring-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}

.ring-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--sp-2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background .15s;
  border: 1px solid transparent;
}
.ring-cell:hover { background: var(--bg); }
.ring-active { background: var(--accent-lt) !important; border-color: var(--accent) !important; }
.ring-sanhe { background: rgba(16,185,129,.08) !important; border-color: rgba(16,185,129,.3) !important; }
.ring-liuhe { background: rgba(245,158,11,.1) !important; border-color: rgba(245,158,11,.3) !important; }
.ring-chong { background: #fef2f2 !important; border-color: rgba(239,68,68,.3) !important; }

.rc-emoji { font-size: 22px; }
.rc-name { font-size: 11px; color: var(--text-3); font-family: var(--font-cn); }

.ring-legend {
  display: flex;
  gap: var(--sp-4);
  margin-top: var(--sp-3);
  font-size: 11px;
}
.leg { color: var(--text-3); }
.active-leg { color: var(--accent-dark); }
.sanhe-leg { color: #059669; }
.liuhe-leg { color: #b45309; }
.chong-leg { color: var(--danger-dark); }

/* ─── 命格标签 ───────────────────────────────────────────────── */
.tags-wrap { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.geju-tag {
  padding: 5px 12px;
  background: var(--accent-lt);
  border: 1px solid rgba(217,119,6,.25);
  border-radius: 99px;
  font-size: var(--fs-sm);
  color: var(--accent-dark);
  cursor: pointer;
  font-family: var(--font-cn);
  transition: background .15s;
}
.geju-tag:hover { background: rgba(217,119,6,.15); }

.tags-empty { display: flex; flex-direction: column; align-items: flex-start; gap: var(--sp-3); }
.empty-sm { font-size: var(--fs-sm); color: var(--text-3); }

/* ─── 通用 ─────────────────────────────────────────────────── */
.empty-hint { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-8) 0; color: var(--text-3); }
.btn-sec { padding: 5px 14px; background: transparent; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: var(--fs-sm); cursor: pointer; color: var(--text-2); }
</style>
