<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Home, ArrowLeft } from '@lucide/vue'
</script>

<template>
  <div class="not-found">
    <div class="nf-card">
      <div class="nf-code">404</div>
      <h1 class="nf-title">页面未找到</h1>
      <p class="nf-desc">您访问的页面不存在或已被移除</p>
      <div class="nf-actions">
        <RouterLink to="/" class="nf-btn nf-btn-primary">
          <Home :size="16" />
          <span>返回首页</span>
        </RouterLink>
        <button class="nf-btn nf-btn-ghost" @click="$router.go(-1)">
          <ArrowLeft :size="16" />
          <span>返回上页</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: var(--sp-4);
}
.nf-card {
  text-align: center;
  max-width: 420px;
}
.nf-code {
  font-size: 6rem;
  font-weight: 800;
  line-height: 1;
  color: var(--accent);
  opacity: 0.25;
  letter-spacing: -0.04em;
}
.nf-title {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text);
  margin-top: var(--sp-2);
}
.nf-desc {
  color: var(--text-2);
  margin-top: var(--sp-2);
  font-size: var(--fs-md);
}
.nf-actions {
  display: flex;
  gap: var(--sp-3);
  justify-content: center;
  margin-top: var(--sp-6);
}
.nf-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}
.nf-btn-primary {
  background: var(--accent);
  color: #fff;
}
.nf-btn-primary:hover {
  background: var(--accent-dark);
}
.nf-btn-ghost {
  background: transparent;
  color: var(--text-2);
  border: 1px solid var(--border);
}
.nf-btn-ghost:hover {
  background: var(--surface-2);
  color: var(--text);
}
</style>