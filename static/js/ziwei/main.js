/**
 * ziwei/main.js — 紫微斗数页面入口（最后加载）
 *
 * 脚本加载顺序（ziwei.html 中定义）：
 *   1. constants.js          — 常量 & 工具函数 (bi/sc/branchRel/esc…)
 *   2. render.js             — 命盘渲染核心 (go/demo/render + P3.4 增量)
 *   3. analysis.js           — 解读渲染 (renderAna/swt/togMonth…)
 *   4. export-cases.js       — 导出 / 案例库 / 历史记录
 *   5. compat.js             — 合盘功能
 *   6. glossary.js           — 词汇表面板
 *   7. charts-svg.js         — SVG 图表 (五行/大运/雷达…)
 *   8. panels-review.js      — 审核面板 & 批量排盘 & 相似盘检索
 *   9. panel-llm.js          — LLM 草稿面板
 *  10. panel-zeri-export.js  — 择日推荐 + 命盘导出
 *  11. panel-fengshui.js     — 风水方位助手
 *  12. panel-life-share.js   — 生活建议 + 分享卡
 *  13. panel-stats-ab.js     — 全局统计 + AB 实验
 *  14. panel-sim-concepts.js — 快速对比模拟 + 概念文档
 *  15. main.js               — 本文件：初始化 + 键盘快捷键（此处）
 *  16. vue-panels.js         — Vue 3 组件（概念文档 / AI 模块解读）
 */

"use strict";

/* ── 页面初始化 ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initCities();
  initCompatCities();
  renderHistory();
  if (readUrlParams()) await go();
});

/* ── @media print 时间戳注入 ─────────────────────────────── */
window.addEventListener('beforeprint', () => {
  const now = new Date().toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
  document.body.setAttribute('data-print-time', now);
  const av = (_lastData && _lastData.algorithm_version) || '\u2014';
  const tv = (_lastData && _lastData.template_version) || 'standard';
  document.body.setAttribute('data-algo-ver', av);
  document.body.setAttribute('data-tpl-ver', tv);
});

/* ── 键盘快捷键 ──────────────────────────────────────────── */
document.addEventListener('keydown', e => {
  // Ctrl+Enter → 排盘
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault();
    go();
    return;
  }
  // Escape → 关闭所有打开的面板 / 弹窗
  if (e.key === 'Escape') {
    const closers = [
      'closeStarInfo', 'closeNoteModal', 'closeReviewPanel', 'closeLlmPanel',
      'closeSimSearchPanel', 'closeZeriPanel', 'closeExportPanel', 'closeFsPanel',
      'closeAbPanel', 'closeShareCard', 'closeBatchPanel', 'closeStatsPanel',
      'closeSimPanel', 'closeConceptsPanel', 'closeCasesPanel',
    ];
    for (const fn of closers) {
      if (typeof window[fn] === 'function') { try { window[fn](); } catch (_) {} }
    }
  }
});

/* ── 本地历史记录 (moved from export-cases.js) ── */
function saveHistory(body,chart){
  const hist=_lsGet();
  const label=`${body.year}-${String(body.month).padStart(2,'0')}-${String(body.day).padStart(2,'0')} ${body.gender}`;
  const item={...body,ts:Date.now(),label,wuxing:chart.wuxing_ju_name||'',life_gz:chart.life_palace_gz||''};
  const deduped=hist.filter(h=>!(h.year===item.year&&h.month===item.month&&h.day===item.day&&h.hour===item.hour&&h.gender===item.gender));
  deduped.unshift(item);
  if(deduped.length>5)deduped.splice(5);
  _lsSet(deduped);renderHistory();
}

function renderHistory(){
  const hist=_lsGet(),hlist=document.getElementById('hlist'),hbtn=document.getElementById('hbtn');
  if(!hlist||!hbtn)return;
  const badge=hist.length?`<span style="font-size:.6rem;background:var(--accent);color:#fff;border-radius:8px;padding:0 4px;margin-left:3px">${hist.length}</span>`:'';
  hbtn.innerHTML='历史'+badge;
  if(!hist.length){hlist.innerHTML='<span style="font-size:.8rem;color:var(--muted);padding:4px 0;display:block">暂无记录</span>';return;}
  hlist.innerHTML=hist.map((item,i)=>
    `<div class="hist-item" onclick="applyHist(${i})">
      <span>${esc(item.label)}</span>
      <span class="hi-gz">${esc(item.life_gz)} ${esc(item.wuxing)}</span>
      <span class="hi-del" onclick="delHist(${i},event)" title="删除">×</span>
    </div>`).join('');
}

function toggleHist(){document.getElementById('hbar').classList.toggle('show');}

function applyHist(idx){
  const item=_lsGet()[idx];if(!item)return;
  document.getElementById('fy').value=item.year;
  document.getElementById('fm').value=item.month;
  document.getElementById('fd').value=item.day;
  document.getElementById('fh').value=item.hour;
  document.getElementById('fmin').value=item.minute;
  document.getElementById('fgender').value=item.gender;
  document.getElementById('flo').value=item.longitude!=null?item.longitude:'';
  document.getElementById('fln').value=item.liunian_year!=null?item.liunian_year:'';
  document.getElementById('hbar').classList.remove('show');
  go();
}

function delHist(idx,e){
  e.stopPropagation();
  const hist=_lsGet();hist.splice(idx,1);_lsSet(hist);renderHistory();
}

function clearAllHist(){
  _lsSet([]);renderHistory();
  document.getElementById('hbar').classList.remove('show');
}


/* ── 合盘功能 ────────────────────────────────────────────── */
