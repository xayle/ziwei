/**
 * verify-init.js — 初始化脚本
 *
 * 将原 verify.html 内的内联事件处理器（onclick="..."）和 Service Worker
 * 注册代码统一抽出到此文件，使页面符合 CSP script-src 'self'（不需要
 * 'unsafe-inline'），消除浏览器控制台 CSP 违规告警。
 *
 * 依赖：verify-core.js 必须在本文件之前加载（提供 switchTab、exportResult 等函数）
 */

// ─── Service Worker 注册 ──────────────────────────────────────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/static/sw.js')
      .then(function (reg) { console.log('[SW] registered, scope:', reg.scope); })
      .catch(function (err) { console.warn('[SW] registration failed:', err); });
  });
}

// ─── DOM 就绪后绑定所有按钮事件 ───────────────────────────────────────────────
// 此脚本在 </body> 前加载，DOMContentLoaded 尚未触发，使用监听确保元素可用
(function bindEvents() {
  function ready(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function () {
    // ── 导出下拉菜单 ── (exportDropdown 内的 5 个按钮)
    var elJson  = document.getElementById('btn-export-json');
    var elCsv   = document.getElementById('btn-export-csv');
    var elExcel = document.getElementById('btn-export-excel');
    var elPrint = document.getElementById('btn-export-print');
    var elCard  = document.getElementById('btn-export-share-card');

    if (elJson)  elJson.addEventListener('click',  function () { exportResult('json'); });
    if (elCsv)   elCsv.addEventListener('click',   function () { exportResult('csv'); });
    if (elExcel) elExcel.addEventListener('click', function () { exportResult('excel'); });
    if (elPrint) elPrint.addEventListener('click', function () { exportResult('print'); });
    if (elCard)  elCard.addEventListener('click',  function () { exportShareCard(); });

    // ── 工具栏按钮 ── (已有 id)
    var elFav     = document.getElementById('btn-fav');
    var elCompare = document.getElementById('btn-compare');
    var elShare   = document.getElementById('btn-share');
    var elDark    = document.getElementById('btn-dark');

    if (elFav)     elFav.addEventListener('click',     function () { showFavoritesModal(); });
    if (elCompare) elCompare.addEventListener('click', function () { toggleCompare(); });
    if (elShare)   elShare.addEventListener('click',   function () { showShareModal(); });
    if (elDark)    elDark.addEventListener('click',    function () { toggleDarkMode(); });

    // ── 欢迎屏「前往请求」按钮 ──
    var elGotoReq = document.getElementById('btn-goto-request');
    if (elGotoReq) elGotoReq.addEventListener('click', function () { switchTab(1); });
  });
}());

// ─── 事件委托：处理 innerHTML 注入的动态元素（替代 inline onclick） ──────────────
// JS 文件通过 innerHTML 插入带 data-* 属性的元素，此处统一侦听
document.addEventListener('click', function (e) {
  var el = e.target.closest(
    '[data-switch-tab],[data-hist-fill],[data-action],' +
    '[data-copy-text],[data-copy-el],[data-toggle],' +
    '[data-load-favorite],[data-delete-favorite],[data-load-history-profile]'
  );
  if (!el) return;

  if (el.dataset.switchTab !== undefined) {
    // 切换 Tab (switchTab 由 verify-core.js 定义)
    if (typeof switchTab === 'function') switchTab(+el.dataset.switchTab);

  } else if (el.dataset.histFill !== undefined) {
    // 历史记录填充表单
    if (typeof histFill === 'function') histFill(+el.dataset.histFill);

  } else if (el.dataset.copyText !== undefined) {
    // 复制固定文本（request_id 等）
    if (typeof copyText === 'function') copyText(el.dataset.copyText, el);

  } else if (el.dataset.copyEl !== undefined) {
    // 复制指定元素的文本内容（Raw JSON）
    var copyTarget = document.getElementById(el.dataset.copyEl);
    if (copyTarget && typeof copyText === 'function') copyText(copyTarget.textContent, el);

  } else if (el.dataset.toggle !== undefined) {
    // 折叠/展开行（大运流年子表格）
    var toggleEl = document.getElementById(el.dataset.toggle);
    if (toggleEl) toggleEl.style.display = (toggleEl.style.display === 'none' ? '' : 'none');

  } else if (el.dataset.loadFavorite !== undefined) {
    if (typeof loadFavorite === 'function') loadFavorite(+el.dataset.loadFavorite);

  } else if (el.dataset.deleteFavorite !== undefined) {
    if (typeof deleteFavorite === 'function') deleteFavorite(+el.dataset.deleteFavorite);

  } else if (el.dataset.loadHistoryProfile !== undefined) {
    if (typeof loadHistoryProfile === 'function') loadHistoryProfile(+el.dataset.loadHistoryProfile);

  } else if (el.dataset.action === 'histCompare') {
    if (typeof histCompare === 'function') histCompare();

  } else if (el.dataset.action === 'clearCompare') {
    window._compareData = null;
    var modal = document.getElementById('compareModal');
    if (modal) modal.classList.remove('open');
  }
});
