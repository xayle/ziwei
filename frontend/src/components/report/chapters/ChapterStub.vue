<script setup lang="ts">
import { computed } from 'vue'
import { CHAPTERS } from '@/data/toc'

const props = defineProps<{ chapterNum: number }>()

const chapterDef = computed(() => CHAPTERS.find(c => c.num === props.chapterNum))

// ─── 各 Stub 章节预计功能 ─────────────────────────────────────
interface FeatureGroup { icon: string; title: string; items: string[] }
const STUB_FEATURES: Record<number, FeatureGroup[]> = {
  7: [
    {
      icon: '🌐',
      title: '出生盘（Natal Chart）',
      items: [
        '12宫位行星落座分析',
        '上升星座 / 下降星座 / 中天',
        '月亮星座 / 太阳星座',
        '行星相位（合相·六分·方形·拱形·对分）',
      ],
    },
    {
      icon: '📐',
      title: '相位图分析',
      items: [
        'T-square 十字型困难相位',
        'Grand Trine 大三角吉祥相位',
        'Yod 神之手特殊构型',
        '命运轴（N/S节点）解读',
      ],
    },
    {
      icon: '🔭',
      title: '时间预测',
      items: [
        '行星过境（Transit）触发分析',
        '太阳回归图（Solar Return）',
        '推运（Progression）',
        '太阳弧（Solar Arc）',
      ],
    },
  ],
  8: [
    {
      icon: '🪄',
      title: '奇门遁甲',
      items: [
        '时家奇门排盘（年/月/日/时）',
        '三奇六仪布局显示',
        '八门八神方位吉凶',
        '奇门预测与出行指引',
      ],
    },
    {
      icon: '📓',
      title: '六爻纳甲',
      items: [
        '铜钱起卦 / 问题起卦',
        '用神世应分析',
        '动爻变卦与应期推断',
        '六亲分析（父母/妻财/子孙/官鬼/兄弟）',
      ],
    },
    {
      icon: '🌙',
      title: '梅花易数',
      items: [
        '时间起卦法 / 数字起卦法',
        '体用生克互动判断',
        '变卦反卦互卦综合解读',
        '梅花心易六十四卦备查',
      ],
    },
  ],
}

const features = computed<FeatureGroup[]>(() => STUB_FEATURES[props.chapterNum] ?? [])
</script>

<template>
  <div class="chapter-stub">
    <!-- 章节标题 -->
    <div class="stub-header">
      <span class="stub-icon">{{ chapterDef?.icon }}</span>
      <div>
        <h2>{{ chapterDef?.label }}</h2>
        <p class="stub-sub">后端接口开发中 · 敬请期待</p>
      </div>
      <span class="stub-badge">🔒 即将上线</span>
    </div>

    <!-- 功能预览卡 -->
    <div class="feature-grid">
      <div
        v-for="group in features"
        :key="group.title"
        class="feature-card"
      >
        <div class="fc-header">
          <span class="fc-icon">{{ group.icon }}</span>
          <span class="fc-title">{{ group.title }}</span>
        </div>
        <ul class="fc-list">
          <li v-for="item in group.items" :key="item" class="fc-item">
            <span class="fc-bullet">·</span>{{ item }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 无预览数据时的占位 -->
    <div v-if="!features.length" class="stub-placeholder">
      <p class="placeholder-text">{{ chapterDef?.label }} — 功能规划中</p>
    </div>

    <!-- 底部 CTA -->
    <div class="stub-footer">
      <p class="footer-txt">如有功能建议或需要提前试用，欢迎联系开发团队</p>
      <a href="mailto:dev@example.com" class="btn-contact">📧 联系开发</a>
    </div>
  </div>
</template>

<style scoped>
.chapter-stub { display: flex; flex-direction: column; gap: var(--sp-5); }

.stub-header {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.stub-icon { font-size: 36px; flex-shrink: 0; }

h2 {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text);
  font-family: var(--font-cn);
}

.stub-sub {
  font-size: var(--fs-xs);
  color: var(--text-3);
  margin-top: 2px;
}

.stub-badge {
  margin-left: auto;
  font-size: var(--fs-xs);
  padding: 4px 12px;
  border-radius: 99px;
  background: #fef9c3;
  color: #854d0e;
  border: 1px solid #fde047;
  white-space: nowrap;
}

/* ─── 功能卡片网格 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--sp-4);
}

.feature-card {
  min-height: 280px;
  padding: var(--sp-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.fc-header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: 1px solid var(--border);
}

.fc-icon  { font-size: 20px; }
.fc-title { font-size: var(--fs-md); font-weight: 700; color: var(--text); font-family: var(--font-cn); }

.fc-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-2); flex: 1; }
.fc-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  font-size: var(--fs-sm);
  color: var(--text-2);
  line-height: 1.5;
}
.fc-bullet { color: var(--text-3); flex-shrink: 0; font-weight: 700; }

/* ─── 占位 & 底栏 */
.stub-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  background: var(--surface);
}
.placeholder-text { color: var(--text-3); font-size: var(--fs-md); font-family: var(--font-cn); }

.stub-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.footer-txt { font-size: var(--fs-xs); color: var(--text-3); }
.btn-contact {
  font-size: var(--fs-xs);
  padding: 4px 14px;
  background: var(--surface);
  border: 1px solid var(--border-md);
  border-radius: var(--radius-sm);
  color: var(--text-2);
  text-decoration: none;
  white-space: nowrap;
}
</style>
