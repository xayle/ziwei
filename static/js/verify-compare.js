/**
 * verify-compare.js  v4.0.20260301
 * M4.11 对比面板 | M4.12 收藏夹 | M4.36 历史抽屉 | M4.11 雷达图
 */
;(function(){
'use strict';

const $ = id => document.getElementById(id);
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');

/* ══════════════════════════════════════════════════
   收藏夹  M4.12
═══════════════════════════════════════════════════ */
const FAV_KEY = 'bazi_favorites_v4';

function loadFavorites() {
  try { return JSON.parse(localStorage.getItem(FAV_KEY)||'[]'); }
  catch(e) { return []; }
}
function saveFavorites(list) {
  try { localStorage.setItem(FAV_KEY, JSON.stringify(list.slice(0,20))); } catch(e){}
}

window.addFavorite = function(label) {
  const json = window.__BAZI_STATE?.result;
  if (!json) { alert('请先排盘'); return; }
  const list = loadFavorites();
  const key  = json.request_id || Date.now().toString(36);
  if (list.some(f=>f.id===key)) { alert('已收藏'); return; }
  const title = label || prompt('请输入收藏名称（可留空）','') || `命盘_${new Date().toLocaleDateString()}`;
  list.unshift({ id:key, title, ts:Date.now(), payload: window.__BAZI_STATE.payload, json });
  saveFavorites(list);
  alert('收藏成功！');
};

window.showFavoritesModal = function() {
  const list   = loadFavorites();
  const overlay= $('compareFavModal');
  if (!overlay) return;
  overlay.classList.add('open');
  const box = overlay.querySelector('.modal-body');
  if (!box) return;
  if (!list.length) {
    box.innerHTML = '<div class="hint" style="padding:24px 0;text-align:center">暂无收藏记录。排盘后可点击"收藏"保存。</div>';
    return;
  }
  box.innerHTML = `
  <div class="fav-list">
    ${list.map((f,i)=>`
      <div class="fav-item" id="fav-item-${i}">
        <div style="flex:1">
          <div style="font-weight:700;font-size:13px">${esc(f.title||'无标题')}</div>
          <div style="font-size:11px;color:var(--muted)">${new Date(f.ts).toLocaleString('zh-CN')}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button onclick="loadFavorite(${i})" style="font-size:12px">载入</button>
          <button onclick="deleteFavorite(${i})" style="font-size:12px;background:var(--bad);color:#fff">删除</button>
        </div>
      </div>`).join('')}
  </div>`;
};

window.loadFavorite = function(i) {
  const list = loadFavorites();
  const f = list[i];
  if (!f) return;
  window.__BAZI_STATE.result  = f.json;
  window.__BAZI_STATE.payload = f.payload;
  window.__BAZI_STATE.tabLoaded.clear();
  typeof loadPanel==='function' && loadPanel(typeof currentTabIdx!=='undefined'?currentTabIdx:0);
  $('compareFavModal')?.classList.remove('open');
  updateCompareBar && updateCompareBar(f.json);
};

window.deleteFavorite = function(i) {
  if (!confirm('确认删除此条收藏？')) return;
  const list = loadFavorites();
  list.splice(i, 1);
  saveFavorites(list);
  showFavoritesModal(); // 刷新列表
};

/* ══════════════════════════════════════════════════
   对比功能  M4.11
═══════════════════════════════════════════════════ */
let _compareData = null;

window.toggleCompare = function() {
  const json = window.__BAZI_STATE?.result;
  if (!json) { alert('请先排盘一次命盘再进行对比'); return; }
  if (!_compareData) {
    // 第一次：保存当前命盘到对比槽
    _compareData = { a: { json, payload: window.__BAZI_STATE.payload }, b: null };
    showCompareNotify('已记录命盘 A，请修改参数重新排盘后再次点击"对比"');
    return;
  }
  if (!_compareData.b) {
    _compareData.b = { json, payload: window.__BAZI_STATE.payload };
    showCompareResult(_compareData.a, _compareData.b);
  }
};

function showCompareNotify(msg) {
  const bar = $('compareNotifyBar');
  if (bar) { bar.textContent = msg; bar.style.display='block'; }
}

function updateCompareBar(json) {
  const bar = $('compareNotifyBar');
  if (bar && _compareData?.a) {
    bar.textContent='命盘已更新（比对槽 A 已记录）';
    bar.style.display='block';
  }
}

window.showCompareResult = function(slotA, slotB) {
  if (!slotA?.json || !slotB?.json) return;
  const overlay = $('compareModal');
  if (!overlay) { _renderCompareInline(slotA.json, slotB.json); return; }
  overlay.classList.add('open');
  const box = overlay.querySelector('.modal-body');
  if (!box) return;
  const a = slotA.json, b = slotB.json;
  const dims = ['wealth','career','marriage','health','overall'];
  const dimCN = {'wealth':'财运','career':'事业','marriage':'婚姻','health':'健康','overall':'综合'};
  const getScore = (json, dim) => {
    switch(dim) {
      case 'wealth':   return json.wealth_analysis?.wealth_score   ?? json.score_v2?.wealth   ?? 0;
      case 'career':   return json.career?.career_score            ?? json.score_v2?.career   ?? 0;
      case 'marriage': return json.marriage_analysis?.marriage_score?? json.score_v2?.marriage?? 0;
      case 'health':   return json.health?.health_score            ?? json.score_v2?.health   ?? 0;
      default:         return json.overall_score                   ?? json.score_v2?.overall  ?? 0;
    }
  };
  const rows = dims.map(d=>{
    const sa = getScore(a,d).toFixed(1), sb = getScore(b,d).toFixed(1);
    const winner = +sa>+sb?'A':+sa<+sb?'B':'平';
    return `<tr><td>${dimCN[d]}</td><td class="${winner==='A'?'ok-text':''}">${sa}</td><td class="${winner==='B'?'ok-text':''}">${sb}</td><td>${winner}</td></tr>`;
  }).join('');

  box.innerHTML = `
  <div id="compareRadarContainer" style="margin-bottom:16px"></div>
  <table style="width:100%;font-size:13px;border-collapse:collapse">
    <thead><tr style="font-weight:700"><th>维度</th><th>命盘 A</th><th>命盘 B</th><th>优势</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
  <div style="margin-top:10px;font-size:11px;color:var(--muted)">命盘A: ${esc(a.request_id||'?')} &nbsp;|&nbsp; 命盘B: ${esc(b.request_id||'?')}</div>
  <button onclick="window._compareData=null;$('compareModal')?.classList.remove('open')" style="margin-top:10px">清除对比</button>
  `;
  // 渲染雷达图
  renderCompareRadar(dims.map(d=>+getScore(a,d)), dims.map(d=>+getScore(b,d)), dims.map(d=>dimCN[d]), $('compareRadarContainer'));
  _compareData = null;
};

function _renderCompareInline(jsonA, jsonB) {
  const panel = document.querySelector('[data-panel="0"] .panel-content');
  if (!panel) return;
  const notice = document.createElement('div');
  notice.className = 'card';
  notice.style.marginTop = '12px';
  notice.innerHTML = '<p style="color:var(--muted);font-size:12px">对比面板：请使用收藏功能保存两份命盘后再对比。</p>';
  panel.appendChild(notice);
}

/* ══════════════════════════════════════════════════
   对比雷达图  Canvas  M4.11
═══════════════════════════════════════════════════ */
function renderCompareRadar(valuesA, valuesB, labels, container) {
  if (!container) return;
  const canvas = document.createElement('canvas');
  const SIZE = 220;
  canvas.width = SIZE; canvas.height = SIZE;
  canvas.style.cssText = 'width:220px;height:220px;display:block;margin:0 auto';
  container.appendChild(canvas);
  const ctx = canvas.getContext('2d'); if(!ctx) return;

  const cx = SIZE/2, cy = SIZE/2, R = 85;
  const N  = labels.length;
  const angle = i => -Math.PI/2 + (2*Math.PI/N)*i;
  const polarX = (val, i) => cx + R*(val/100)*Math.cos(angle(i));
  const polarY = (val, i) => cy + R*(val/100)*Math.sin(angle(i));

  // 背景网格
  ctx.strokeStyle = '#e5e7eb';
  for (let lv=20;lv<=100;lv+=20) {
    ctx.beginPath();
    for (let i=0;i<N;i++) {
      const x = cx + R*(lv/100)*Math.cos(angle(i));
      const y = cy + R*(lv/100)*Math.sin(angle(i));
      i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
    }
    ctx.closePath(); ctx.stroke();
  }
  // 轴
  for (let i=0;i<N;i++) {
    ctx.beginPath(); ctx.moveTo(cx,cy);
    ctx.lineTo(cx+R*Math.cos(angle(i)), cy+R*Math.sin(angle(i)));
    ctx.stroke();
  }

  // 标签
  ctx.font = '10px sans-serif'; ctx.fillStyle = '#6b7280';
  for (let i=0;i<N;i++) {
    const lx = cx + (R+14)*Math.cos(angle(i));
    const ly = cy + (R+14)*Math.sin(angle(i));
    ctx.textAlign = lx>cx+4?'left':lx<cx-4?'right':'center';
    ctx.fillText(labels[i], lx, ly+4);
  }

  // 数据 A
  const drawPoly = (vals, color) => {
    ctx.beginPath();
    for(let i=0;i<N;i++) i===0?ctx.moveTo(polarX(vals[i],i),polarY(vals[i],i)):ctx.lineTo(polarX(vals[i],i),polarY(vals[i],i));
    ctx.closePath();
    ctx.strokeStyle=color; ctx.lineWidth=2; ctx.stroke();
    ctx.fillStyle=color.replace(')',',0.15)').replace('rgb','rgba'); ctx.fill();
  };
  drawPoly(valuesA, 'rgb(178,34,34)');
  drawPoly(valuesB, 'rgb(37,99,235)');

  // 图例
  const leg = document.createElement('div');
  leg.style.cssText='display:flex;justify-content:center;gap:16px;font-size:11px;margin-top:6px';
  leg.innerHTML='<span style="display:flex;align-items:center;gap:4px"><span style="width:16px;height:3px;background:rgb(178,34,34);display:inline-block;border-radius:2px"></span>命盘A</span><span style="display:flex;align-items:center;gap:4px"><span style="width:16px;height:3px;background:rgb(37,99,235);display:inline-block;border-radius:2px"></span>命盘B</span>';
  container.appendChild(leg);
}

/* ══════════════════════════════════════════════════
   关闭 Modal 通用
═══════════════════════════════════════════════════ */
window.closeModal = function(id) {
  const el = typeof id==='string' ? document.getElementById(id) : id;
  el?.classList.remove('open');
};

/* ── 关闭按钮委托 ──────────────────────────────── */
document.addEventListener('click', e => {
  if (e.target.matches('.modal-overlay')) closeModal(e.target.id);
  if (e.target.matches('.modal-close')) closeModal(e.target.closest('.modal-overlay'));
  if (e.target.matches('.drawer-close')) {
    e.target.closest('.history-drawer')?.classList.remove('open');
  }
});

})();
