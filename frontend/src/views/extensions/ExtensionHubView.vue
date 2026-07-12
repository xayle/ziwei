<script setup lang="ts">
import { useRouter } from 'vue-router'
import '@/assets/fusheng-page.css'

const router = useRouter()

const modules = [
  {
    id: 'relation',
    title: '关系合盘（统一）',
    desc: '情侣/友人/亲子/同事/合伙/上下级 — 六类关系，八字+紫微统一评分。',
    path: '/relation/new?type=couple',
  },
  {
    id: 'compat',
    title: '八字合婚（旧）',
    desc: '已迁移至关系合盘；此入口保留兼容。',
    path: '/extensions/compat',
  },
  {
    id: 'ziwei-compat',
    title: '紫微合盘',
    desc: '命宫/五行/夫妻宫等维度双人合盘（heuristic 层，仅供参考）。',
    path: '/extensions/ziwei-compat',
  },
  {
    id: 'similarity',
    title: '相似命盘',
    desc: '基于命盘哈希检索库内相似案例，辅助对照研究。',
    path: '/extensions/similarity',
  },
  {
    id: 'zeri',
    title: '择日推荐',
    desc: '结合紫微命宫与五行局，按用途推荐当月吉日。',
    path: '/extensions/zeri',
  },
]
</script>

<template>
  <main class="fs-page extension-hub">
    <p class="fs-page-lead">合婚、相似盘与择日为独立路由，不影响主路径档案与报告。</p>
    <div class="fs-page-actions">
      <button class="fs-btn fs-btn--ghost" @click="router.push('/')">返回首页</button>
    </div>

    <section class="module-grid">
      <article v-for="item in modules" :key="item.id" class="fs-card module-card">
        <h2>{{ item.title }}</h2>
        <p>{{ item.desc }}</p>
        <button class="fs-btn fs-btn--primary" @click="router.push(item.path)">进入</button>
      </article>
    </section>
  </main>
</template>

<style scoped>
.extension-hub { gap: 14px; }

.module-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.module-card {
  display: grid;
  gap: 10px;
}

.module-card h2 {
  margin: 0;
  font-family: var(--font-cn);
  font-size: 18px;
}

.module-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-2);
}
</style>
