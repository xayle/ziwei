/**
 * vue-panels.js — Sprint 5/6 Vue 3 CDN 面板
 * 功能：① 概念文档面板  ② AI 分模块解读面板
 * 依赖：Vue 3 CDN（已在 ziwei.html 引入）
 */
(function () {
  'use strict';
  if (typeof Vue === 'undefined') {
    console.warn('[vue-panels] Vue 3 未加载，面板不可用');
    return;
  }
  const { createApp, ref, computed, onMounted } = Vue;

  /* ══════════════════════════════════════════════════════════
     § 1. 概念文档面板  GET /api/v1/docs/concepts
  ══════════════════════════════════════════════════════════ */
  const ConceptsApp = createApp({
    setup() {
      const all      = ref([]);      // 全量数据（初次加载后缓存）
      const shown    = ref([]);      // 当前显示列表
      const loading  = ref(false);
      const query    = ref('');
      const category = ref('');      // '' | 'bazi' | 'ziwei'
      const expandId = ref(null);
      let debouncer  = null;

      /* ---- 数据拉取 ---- */
      async function fetchAll(cat = '') {
        loading.value = true;
        try {
          const url = cat ? `/api/v1/docs/concepts?category=${cat}` : '/api/v1/docs/concepts';
          const r   = await fetch(url);
          if (r.ok) {
            const data = await r.json();
            all.value  = data;
            shown.value = data;
          }
        } catch { /* 静默 */ }
        loading.value = false;
      }

      async function searchServer() {
        if (debouncer) clearTimeout(debouncer);
        debouncer = setTimeout(async () => {
          const q = query.value.trim();
          if (!q) { shown.value = localFilter(all.value); return; }
          loading.value = true;
          try {
            const qs  = new URLSearchParams();
            if (q)            qs.set('q', q);
            if (category.value) qs.set('category', category.value);
            const r = await fetch(`/api/v1/docs/concepts?${qs}`);
            if (r.ok) { const d = await r.json(); shown.value = d; }
          } catch { shown.value = localFilter(all.value); }
          loading.value = false;
        }, 280);
      }

      function localFilter(data) {
        let d = data;
        if (category.value) d = d.filter(c => c.category === category.value);
        const q = query.value.trim().toLowerCase();
        if (q) d = d.filter(c =>
          (c.term||'').toLowerCase().includes(q) ||
          (c.definition||'').toLowerCase().includes(q) ||
          (c.aliases||[]).some(a => a.toLowerCase().includes(q))
        );
        return d;
      }

      function setCategory(cat) {
        category.value = cat;
        query.value    = '';
        expandId.value = null;
        fetchAll(cat);
      }

      function toggle(id) {
        expandId.value = expandId.value === id ? null : id;
      }

      onMounted(() => fetchAll());

      return { shown, loading, query, category, expandId,
               setCategory, toggle, searchServer };
    },

    template: `
      <div class="cpt-inner">
        <!-- 分类标签 -->
        <div class="cpt-tabs">
          <button :class="['cpt-tab', category==='' && 'act']"
                  @click="setCategory('')">全部</button>
          <button :class="['cpt-tab', category==='bazi' && 'act']"
                  @click="setCategory('bazi')">八字</button>
          <button :class="['cpt-tab', category==='ziwei' && 'act']"
                  @click="setCategory('ziwei')">紫微</button>
        </div>
        <!-- 搜索框 -->
        <input class="cpt-search"
               v-model="query"
               @input="searchServer"
               placeholder="搜索概念、别名或释义…" />
        <!-- 计数 -->
        <div class="cpt-count" v-if="!loading">
          共 {{ shown.length }} 条
        </div>
        <div class="cpt-count" v-else>加载中…</div>
        <!-- 列表 -->
        <div class="cpt-list">
          <div v-if="shown.length === 0 && !loading"
               style="padding:30px;text-align:center;color:var(--muted);font-size:.82rem">
            暂无匹配结果
          </div>
          <div v-for="c in shown" :key="c.id"
               class="cpt-item"
               :class="{ open: expandId === c.id }"
               @click="toggle(c.id)">
            <div class="cpt-item-hdr">
              <span class="cpt-term">{{ c.term }}</span>
              <span class="cpt-cat-badge"
                    :class="c.category === 'bazi' ? 'bazi' : 'ziwei'">
                {{ c.category === 'bazi' ? '八字' : '紫微' }}
              </span>
              <span class="cpt-chevron">{{ expandId === c.id ? '▲' : '▼' }}</span>
            </div>
            <div v-if="expandId === c.id" class="cpt-detail">
              <p class="cpt-def">{{ c.definition }}</p>
              <div v-if="c.aliases && c.aliases.length" class="cpt-aliases">
                别名：{{ c.aliases.join('、') }}
              </div>
              <div v-if="c.related && c.related.length" class="cpt-related">
                相关：
                <span v-for="(rel, ri) in c.related" :key="ri" class="cpt-rel-tag">{{ rel }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `
  });

  // DOM 准备好后挂载
  if (document.getElementById('concepts-app-root')) {
    ConceptsApp.mount('#concepts-app-root');
  }

  /* ══════════════════════════════════════════════════════════
     § 2. AI 分模块解读  POST /api/v1/llm/interpret-module
  ══════════════════════════════════════════════════════════ */
  const MODULE_LABELS = {
    'dayun_narrative':     '大运叙述',
    'liunian_advice':      '流年建议',
    'career_detail':       '事业详解',
    'marriage_detail':     '婚恋详解',
    'wealth_detail':       '财运详解',
    'fengshui_suggestion': '风水调候',
  };

  const AiModuleApp = createApp({
    setup() {
      const caseId   = ref('');
      const module   = ref('');
      const context  = ref('');
      const result   = ref('');
      const loading  = ref(false);
      const errMsg   = ref('');
      const genAt    = ref('');

      const modules = Object.entries(MODULE_LABELS).map(([k, v]) => ({ key: k, label: v }));

      function selectModule(k) {
        module.value = k;
        result.value = '';
        errMsg.value = '';
        genAt.value  = '';
      }

      async function generate() {
        if (!caseId.value.trim()) { errMsg.value = '请输入八字案例 ID（case_id）'; return; }
        if (!module.value)        { errMsg.value = '请选择解读模块'; return; }
        loading.value = true;
        errMsg.value  = '';
        result.value  = '';
        genAt.value   = '';
        try {
          const tok = getToken();
          const r   = await fetch('/api/v1/llm/interpret-module', {
            method:  'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(tok ? { Authorization: 'Bearer ' + tok } : {}),
            },
            body: JSON.stringify({
              case_id: caseId.value.trim(),
              module:  module.value,
              context: context.value.trim() || undefined,
            }),
          });
          if (!r.ok) {
            const e = await r.json().catch(() => ({}));
            if (r.status === 401) errMsg.value = '请先登录后再使用 AI 模块解读';
            else if (r.status === 404) errMsg.value = '案例 ID 不存在，请检查后重试';
            else if (r.status === 429) errMsg.value = '请求过于频繁，请稍后再试（每分钟限 10 次）';
            else errMsg.value = '错误：' + (e.detail || r.status);
          } else {
            const d       = await r.json();
            result.value  = d.interpretation || '';
            genAt.value   = d.generated_at   || '';
          }
        } catch (e) {
          errMsg.value = '网络错误：' + e.message;
        }
        loading.value = false;
      }

      async function copyResult() {
        if (!result.value) return;
        try {
          await navigator.clipboard.writeText(result.value);
          window._showToastIfAvail('已复制到剪贴板');
        } catch { /* 静默 */ }
      }

      return { caseId, module, context, result, loading, errMsg, genAt,
               modules, MODULE_LABELS, selectModule, generate, copyResult };
    },

    template: `
      <div class="llm-mod-inner">
        <!-- 案例 ID 输入 -->
        <div class="llm-mod-row">
          <label class="llm-mod-lbl">八字案例 ID（case_id）</label>
          <input class="llm-mod-input" v-model="caseId"
                 placeholder="如 GT01 或数字 ID，需已保存到案例库" />
        </div>
        <!-- 模块选择 -->
        <div class="llm-mod-row">
          <label class="llm-mod-lbl">解读模块</label>
          <div class="llm-mod-btns">
            <button v-for="m in modules" :key="m.key"
                    :class="['llm-mod-btn', module === m.key && 'act']"
                    @click="selectModule(m.key)">
              {{ m.label }}
            </button>
          </div>
        </div>
        <!-- 可选附加背景 -->
        <div class="llm-mod-row">
          <label class="llm-mod-lbl">附加背景（可选）</label>
          <textarea class="llm-mod-ctx" v-model="context"
                    placeholder="如「近期创业，主要关注资金流向」，可不填" rows="2" />
        </div>
        <!-- 操作 -->
        <div class="llm-mod-actions">
          <button class="llm-gen-btn" :disabled="loading" @click="generate">
            {{ loading ? '生成中…' : '⚡ 生成模块解读' }}
          </button>
          <button v-if="result" class="llm-copy-btn" @click="copyResult">📋 复制</button>
        </div>
        <!-- 错误 -->
        <div v-if="errMsg" class="llm-mod-err">{{ errMsg }}</div>
        <!-- 结果 -->
        <div v-if="result" class="llm-mod-result">
          <div class="llm-mod-result-hdr">
            {{ MODULE_LABELS[module] }} 解读结果
            <span v-if="genAt" style="font-size:.68rem;color:var(--muted);margin-left:8px">{{ genAt }}</span>
          </div>
          <div class="llm-mod-result-body">{{ result }}</div>
        </div>
        <!-- 空态提示 -->
        <div v-if="!result && !loading && !errMsg" class="llm-mod-hint">
          ① 输入已保存的八字案例 ID &nbsp;→&nbsp; ② 选择解读模块 &nbsp;→&nbsp; ③ 点击生成
        </div>
        <div class="llm-disclaimer" style="margin-top:12px;display:block">
          ⚠ 以上内容由 AI 辅助生成，仅供参考，请命理师复核后使用。
        </div>
      </div>
    `
  });

  if (document.getElementById('llm-module-app-root')) {
    AiModuleApp.mount('#llm-module-app-root');
  }

  /* ── 工具函数：供 Vue app 调用主页面的 showToast ── */
  window._showToastIfAvail = function (msg, type) {
    if (typeof showToast === 'function') showToast(msg, type || 'info');
  };

})();
