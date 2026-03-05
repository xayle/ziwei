/**
 * verify-guide.js — 术语 Tooltip 引擎 (spec §4.2, task 4.14)
 *
 * 功能：
 *   1. 从 /api/v1/glossary 加载 65 个命理术语定义（首次渲染时预取）
 *   2. window.__Glossary.apply(el) — 扫描容器内文本节点，自动包裹 .glossary-term span
 *   3. window.__Glossary.load()   — 返回 Promise<{term: definition}>（可外部 await）
 *
 * 依赖：verify-render.js（已渲染的 DOM 内容），verify-core.js 的 loadPanel() 调用 apply()
 * tooltip 展示方式：HTML title 属性（原生浏览器 tooltip，零 JS 依赖，无障碍友好）
 */
(function () {
  'use strict';

  /** @type {Record<string, string>|null} 术语 → 定义映射的缓存 */
  let _cache = null;
  /** @type {Promise<Record<string, string>>|null} 进行中的加载 Promise */
  let _loading = null;

  /**
   * 加载词汇表（幂等，只请求一次）
   * @returns {Promise<Record<string, string>>}
   */
  function loadGlossary() {
    if (_cache !== null) return Promise.resolve(_cache);
    if (_loading) return _loading;

    _loading = fetch('/api/v1/glossary')
      .then(function (resp) {
        if (!resp.ok) throw new Error('glossary fetch failed: ' + resp.status);
        return resp.json();
      })
      .then(function (items) {
        _cache = {};
        if (Array.isArray(items)) {
          items.forEach(function (item) {
            if (item && item.term && item.definition) {
              _cache[item.term] = item.definition;
            }
          });
        }
        return _cache;
      })
      .catch(function (err) {
        console.warn('[verify-guide] 词汇表加载失败:', err.message);
        _cache = {};
        return _cache;
      });

    return _loading;
  }

  /**
   * 对容器内所有文本节点进行术语标注
   * @param {Element} container
   */
  function applyGlossaryTooltips(container) {
    if (!container) return;

    loadGlossary().then(function (glossary) {
      var terms = Object.keys(glossary);
      if (!terms.length) return;

      // 按词长倒序排列，避免短词先匹配破坏长词
      terms.sort(function (a, b) { return b.length - a.length; });

      // 构建 TreeWalker，仅遍历文本节点
      var walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: function (node) {
            var p = node.parentElement;
            if (!p) return NodeFilter.FILTER_SKIP;
            // 跳过脚本/代码块/已处理的节点
            if (p.closest('script,code,pre,input,textarea,.glossary-term')) {
              return NodeFilter.FILTER_SKIP;
            }
            // 跳过纯空白节点
            if (!node.textContent.trim()) return NodeFilter.FILTER_SKIP;
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );

      // 收集所有文本节点（不能边 walk 边修改 DOM）
      var nodes = [];
      var n;
      while ((n = walker.nextNode())) nodes.push(n);

      for (var i = 0; i < nodes.length; i++) {
        var node = nodes[i];
        var text = node.textContent;
        var changed = false;

        for (var j = 0; j < terms.length; j++) {
          var term = terms[j];
          if (text.indexOf(term) !== -1) {
            var def = glossary[term].replace(/&/g, '&amp;').replace(/"/g, '&quot;');
            text = text.split(term).join(
              '<span class="glossary-term" title="' + def + '">' + term + '</span>'
            );
            changed = true;
          }
        }

        if (changed) {
          // 清洗残留的 "> 分隔符（后端模板注释），避免被 innerHTML 渲染成可见文字
          text = text.replace(/&quot;>/g, ' · ').replace(/">/g, ' · ');
          var span = document.createElement('span');
          span.className = 'glossary-inline-host';
          span.innerHTML = text;
          if (node.parentNode) {
            node.parentNode.replaceChild(span, node);
          }
        }
      }
    });
  }

  /** 公开 API */
  window.__Glossary = {
    apply: applyGlossaryTooltips,
    load: loadGlossary
  };

  // 页面加载时预取词汇表（避免首次渲染时的网络延迟）
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadGlossary);
  } else {
    // 空闲时预取，不阻塞主线程
    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(loadGlossary);
    } else {
      setTimeout(loadGlossary, 500);
    }
  }
})();
