   §16  生活建议交互增强  Life Suggestions Interaction
   ════════════════════════════════════════════════════════════ */

const _LSUG_LS_KEY = 'ziwei_lsug_state_v1';
let _lsugState = (() => {
  try { return JSON.parse(localStorage.getItem(_LSUG_LS_KEY) || '{}'); }
  catch { return {}; }
})();

function lsugSetAction(id, action) {
  _lsugState[id] = action;
  try { localStorage.setItem(_LSUG_LS_KEY, JSON.stringify(_lsugState)); } catch {}
  const item = document.querySelector(`[data-lsug-id="${id}"]`);
  if (!item) return;
  item.classList.remove('lsug-done', 'lsug-watching', 'lsug-ignored');
  if (action) item.classList.add('lsug-' + action);
  item.querySelectorAll('.lsug-act-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.action === action);
  });
  _lsugRefreshBadge();
}

function _lsugRefreshBadge() {
  const badge = document.querySelector('.lsug-summary-badge');
  if (!badge) return;
  const items = document.querySelectorAll('[data-lsug-id]');
  const total = items.length;
  const doneN = [...items].filter(i => _lsugState[i.dataset.lsugId] === 'done').length;
  const watchN = [...items].filter(i => _lsugState[i.dataset.lsugId] === 'watching').length;
  badge.textContent = `（${total}条 · 已实施${doneN} · 关注${watchN} · 传统命理参考）`;
}

function lsugApplyFilter() {
  const costSel  = document.getElementById('lsug-filter-cost');
  const stateSel = document.getElementById('lsug-filter-state');
  const cost  = costSel  ? costSel.value  : '';
  const state = stateSel ? stateSel.value : '';
  const prefs = lsugGetPrefs();
  document.querySelectorAll('[data-lsug-id]').forEach(item => {
    const itemCost  = item.dataset.cost  || '';
    const itemState = _lsugState[item.dataset.lsugId] || '';
    const costOk  = !cost  || itemCost  === cost;
    const stateOk = !state || itemState === state || (state === 'none' && !itemState);
    // 预算偏好软过滤（仅隐藏，不强制；用户可手动切花费筛选覆盖）
    const budgetOk = !prefs.budget
      || (prefs.budget === 'low'    && itemCost !== '高' && itemCost !== '中')
      || (prefs.budget === 'medium' && itemCost !== '高')
      || true; // budget 偏好以警告标签为主，不做硬隐藏
    item.style.display = (costOk && stateOk) ? '' : 'none';
  });
}

function lsugExport() {
  const items = [...document.querySelectorAll('[data-lsug-id]')];
  const rows = items.map(item => {
    const title = item.querySelector('.lsug-title-text')?.textContent || item.querySelector('strong')?.textContent || '';
    const cost  = item.dataset.cost || '';
    const state = _lsugState[item.dataset.lsugId] || '未设置';
    return `<tr><td>${title}</td><td>${cost}</td><td>${state}</td></tr>`;
  }).join('');
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>生活化建议导出</title>
  <style>body{font-family:sans-serif;padding:24px}table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #ccc;padding:8px 12px;text-align:left}th{background:#f5f5f5}</style></head>
  <body><h2>生活化建议清单</h2><table><tr><th>建议内容</th><th>花费</th><th>执行状态</th></tr>${rows}</table></body></html>`;
  const w = window.open('', '_blank');
  w.document.write(html);
  w.document.close();
  setTimeout(() => w.print(), 400);
}

/* ════════════════════════════════════════════════════════════
   §19  生活建议用户偏好 + 证据跳转高亮
   ════════════════════════════════════════════════════════════ */
const _LSUG_PREFS_KEY = 'ziwei_lsug_prefs_v1';

function lsugGetPrefs() {
  try { return JSON.parse(localStorage.getItem(_LSUG_PREFS_KEY) || '{}'); }
  catch { return {}; }
}

function lsugSavePrefs() {
  const prefs = {
    has_pets: !!(document.getElementById('lsug-pref-pets')?.checked),
    allergy:  !!(document.getElementById('lsug-pref-allergy')?.checked),
    no_heavy: !!(document.getElementById('lsug-pref-noheavy')?.checked),
    budget:   document.getElementById('lsug-pref-budget')?.value || '',
  };
  localStorage.setItem(_LSUG_PREFS_KEY, JSON.stringify(prefs));
  // 重新渲染生活建议区域以刷新警告标签
  if (typeof lastRenderData !== 'undefined' && lastRenderData) {
    const wrap = document.querySelector('.lsug-wrap');
    if (wrap) {
      // 仅刷新警告标签，不重排整个区域（避免 scroll 跳动）
      document.querySelectorAll('[data-lsug-id]').forEach(item => {
        const id = item.dataset.lsugId || '';
        const cost = item.dataset.cost || '';
        const cat = item.dataset.cat || '';
        item.querySelectorAll('.lsug-pref-warn').forEach(el => el.remove());
        const p = lsugGetPrefs();
        const warns = [];
        if (p.has_pets && cat === 'plants') {
          const notesEl = item.querySelector('.lsug-notes');
          if (notesEl && /宠/.test(notesEl.textContent)) warns.push('🐾 家中有宠物：请确认此植物对宠物安全');
        }
        if (p.allergy && cat === 'plants') warns.push('🌸 植物过敏：请谨慎考虑此建议');
        if (p.no_heavy && cat === 'bed') warns.push('🚫 不宜移动大件：请量力而为');
        if (p.budget === 'low' && cost === '高') warns.push('💰 花费较高，与低预算偏好不符');
        else if (p.budget === 'medium' && cost === '高') warns.push('💰 花费较高，请酌情考虑');
        if (warns.length) {
          const hdr = item.querySelector('.lsug-header');
          warns.forEach(w => {
            const sp = document.createElement('span');
            sp.className = 'lsug-pref-warn';
            sp.textContent = w;
            item.insertBefore(sp, hdr);
          });
        }
      });
    }
  }
}

/* 从 evidence 文本中提取第一个宫位名（如 "命宫" "财帛宫" 等） */
function lsugExtractPalace(evidence) {
  if (!evidence) return null;
  const m = evidence.match(/(命宫|财帛宫|福德宫|夫妻宫|官禄宫|迁移宫|奴仆宫|疾厄宫|田宅宫|兄弟宫|子女宫|父母宫)/);
  return m ? m[1] : null;
}

/* 点击跳转并闪烁高亮对应宫位 */
function lsugJumpToPalace(palaceName) {
  const cell = document.querySelector(`[data-pname="${palaceName}"]`);
  if (!cell) { showToast && showToast(`未找到「${palaceName}」，请先排盘`, 'warn'); return; }
  // 先滚到命盘区域
  const chartEl = document.getElementById('cr');
  if (chartEl) chartEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  setTimeout(() => {
    cell.scrollIntoView({ behavior: 'smooth', block: 'center' });
    cell.classList.remove('pal-highlight-pulse');
    void cell.offsetWidth; // 强制重排以重启动画
    cell.classList.add('pal-highlight-pulse');
    setTimeout(() => cell.classList.remove('pal-highlight-pulse'), 2600);
  }, 350);
}

/* ════════════════════════════════════════════════════════════
   §20  格局宫位自动标注 + 跳转高亮
   ════════════════════════════════════════════════════════════ */
const _PAT_LVL_CLS = { '大吉': 'ppb-daji', '吉': 'ppb-ji', '凶': 'ppb-xiong', '大凶': 'ppb-daxiong' };

/* 在宫格底部注入格局徽章 */
function annotatePatternPalaces(patterns) {
  // 清除旧标注
  document.querySelectorAll('.pat-pal-badge-wrap').forEach(el => el.remove());
  if (!patterns || !patterns.length) return;
  // 聚合：每个宫位 → 涉及的格局列表
  const palMap = {};
  for (const pt of patterns) {
    for (const palName of (pt.palaces || [])) {
      if (!palMap[palName]) palMap[palName] = [];
      palMap[palName].push(pt);
    }
  }
  for (const [palName, pts] of Object.entries(palMap)) {
    const cell = document.querySelector(`[data-pname="${palName}"]`);
    if (!cell) continue;
    const wrap = document.createElement('div');
    wrap.className = 'pat-pal-badge-wrap';
    // 去重（同名格局只显示一次）
    const seen = new Set();
    for (const pt of pts) {
      if (seen.has(pt.name)) continue;
      seen.add(pt.name);
      const badge = document.createElement('span');
      badge.className = `pat-pal-badge ${_PAT_LVL_CLS[pt.level] || 'ppb-ji'}`;
      badge.textContent = pt.name;
      badge.title = `${pt.level} · ${pt.description}`;
      badge.onclick = (e) => {
        e.stopPropagation();
        cell.classList.remove('pal-highlight-pulse');
        void cell.offsetWidth;
        cell.classList.add('pal-highlight-pulse');
        setTimeout(() => cell.classList.remove('pal-highlight-pulse'), 2600);
      };
      wrap.appendChild(badge);
    }
    cell.appendChild(wrap);
  }
}

/* 从格局列表点击 → 滚动到对应宫格并高亮 */
function patJumpToPalace(palaceName) {
  const cell = document.querySelector(`[data-pname="${palaceName}"]`);
  if (!cell) { showToast && showToast(`未找到「${palaceName}」，请先排盘`, 'warn'); return; }
  const chartEl = document.getElementById('cr');
  if (chartEl) chartEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  setTimeout(() => {
    cell.scrollIntoView({ behavior: 'smooth', block: 'center' });
    cell.classList.remove('pal-highlight-pulse');
    void cell.offsetWidth;
    cell.classList.add('pal-highlight-pulse');
    setTimeout(() => cell.classList.remove('pal-highlight-pulse'), 2600);
  }, 350);
}

/* ════════════════════════════════════════════════════════════
   §22  命盘摘要分享卡  Share Summary Card
   ════════════════════════════════════════════════════════════ */

function openShareCard() {
  if (!_lastData) { showToast('请先排盘', 'warn'); return; }
  _renderShareCard(_lastData);
  document.getElementById('share-panel').classList.add('vis');
}

function closeShareCard() {
  document.getElementById('share-panel').classList.remove('vis');
  document.getElementById('share-status').textContent = '';
}

function _renderShareCard(data) {
  const esc = s => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const { birth_solar, life_palace_gz, body_palace_gz, wuxing_ju_name, gender, patterns, life_suggestions } = data;
  const namePart = (data.name && data.name !== '匿名') ? `${esc(data.name)} · ` : '';
  const genderPart = gender ? `${esc(gender)}命` : '';
  let h = `<div class="sc-title">☆ 紫微命盘摘要 ☆</div>`;
  h += `<div class="sc-born">${namePart}${esc(birth_solar) || ''}　${genderPart}</div>`;
  // 命宫 / 身宫 / 五行局
  h += `<div class="sc-row">
    <span class="sc-lbl">命宫 / 身宫：</span>
    <span class="sc-pal-chip top1">${esc(life_palace_gz || '—')}</span>
    <span class="sc-pal-chip">${esc(body_palace_gz || '—')}</span>
    <span class="sc-lbl" style="margin-left:4px">五行局：</span>
    <span class="sc-pal-chip">${esc(wuxing_ju_name || '—')}</span>
  </div>`;
  // 宫力 TOP-3
  if (data.palaces && data.palaces.length) {
    const sorted = [...data.palaces].sort((a, b) => palScore(b) - palScore(a)).slice(0, 3);
    h += `<div class="sc-row"><span class="sc-lbl">宫力 TOP 3：</span><div class="sc-pal-chips">`;
    for (const p of sorted) {
      const s = palScore(p);
      const col = s >= 75 ? '#16a34a' : s >= 55 ? '#b8862a' : '#dc2626';
      h += `<span class="sc-pal-chip" style="border-color:${col};color:${col}">${esc(p.name)} ${s}</span>`;
    }
    h += `</div></div>`;
  }
  // 格局摘要
  if (patterns && patterns.length) {
    const lvlCls = { '大吉': 'daji', '吉': 'ji', '凶': 'xiong', '大凶': 'daxiong' };
    h += `<hr class="sc-divider"><div class="sc-pat-row">
      <span class="sc-lbl">检测到的格局（${patterns.length} 个）：</span>
      <div class="sc-pat-chips">`;
    for (const pt of patterns) {
      h += `<span class="sc-pat-chip ${lvlCls[pt.level] || 'ji'}" title="${esc(pt.description)}">${esc(pt.name)}</span>`;
    }
    h += `</div></div>`;
  }
  // 生活建议（优先级最高的 3 条）
  if (life_suggestions && life_suggestions.length) {
    const top = life_suggestions.filter(s => s.priority === '立即' || s.priority === 1 || s.priority === '高').slice(0, 3);
    if (top.length) {
      h += `<hr class="sc-divider"><div class="sc-sug-row">
        <span class="sc-lbl">重点生活建议：</span>
        <ul class="sc-sug-list">`;
      for (const sg of top) {
        h += `<li>${esc(sg.title || sg.suggestion || sg.text || '')}</li>`;
      }
      h += `</ul></div>`;
    }
  }
  // 页脚
  const dt = new Date().toLocaleDateString('zh-CN');
  h += `<div class="sc-footer">由「紫微斗数 · 命盘推算」系统生成 · ${dt} · 仅供参考，不构成命运定论</div>`;
  document.getElementById('share-card-preview').innerHTML = h;
}

/* 复制独立 HTML */
async function copyShareHTML(btn) {
  const prev = document.getElementById('share-card-preview');
  if (!prev) return;
  const cardStyles = `body{font-family:sans-serif;background:#fdf8f0;padding:24px;max-width:520px;margin:auto}
.sc-title{font-size:1.05rem;font-weight:700;color:#8b1a1a;text-align:center;letter-spacing:.1em}
.sc-born{font-size:.78rem;color:#888;text-align:center;margin-bottom:10px}
.sc-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}.sc-lbl{font-size:.72rem;color:#888;white-space:nowrap}
.sc-pal-chip{font-size:.72rem;padding:3px 9px;border-radius:5px;background:#fff5e6;border:1px solid #d4b896;color:#7c3d12}
.sc-pal-chip.top1{background:#fef3c7;border-color:#b45309;font-weight:700}
.sc-pal-chips{display:flex;flex-wrap:wrap;gap:5px}
.sc-pat-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px}
.sc-pat-chip{font-size:.7rem;padding:2px 8px;border-radius:10px;font-weight:700}
.daji{background:#dcfce7;color:#15803d}.ji{background:#fef9c3;color:#92400e}
.xiong{background:#fee2e2;color:#b91c1c}.daxiong{background:#7f1d1d;color:#fca5a5}
.sc-sug-list{padding-left:1.1em;margin:4px 0 0}.sc-sug-list li{font-size:.76rem;line-height:1.7}
.sc-footer{font-size:.6rem;color:#888;text-align:center;margin-top:10px;padding-top:8px;border-top:1px dashed #d4b896}
.sc-divider{border:none;border-top:1px dashed #d4b896;margin:10px 0}`;
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>紫微命盘摘要</title><style>${cardStyles}</style></head><body>${prev.innerHTML}</body></html>`;
  try {
    await navigator.clipboard.writeText(html);
    const orig = btn.textContent;
    btn.textContent = '✓ 已复制';
    setTimeout(() => { btn.textContent = orig; }, 2000);
    document.getElementById('share-status').textContent = '已将独立 HTML 复制到剪贴板，可粘贴到任意编辑器保存';
  } catch (e) {
    document.getElementById('share-status').textContent = '复制失败：' + e.message;
  }
}

/* 截图导出 PNG */
async function screenshotShareCard(btn) {
  const prev = document.getElementById('share-card-preview');
  if (!prev) return;
  if (typeof html2canvas === 'undefined') {
    showToast('截图库未加载（需联网），可用「打印/PDF」替代', 'error'); return;
  }
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '生成中…';
  try {
    const canvas = await html2canvas(prev, { backgroundColor: '#fdf8f0', scale: 2, useCORS: true, logging: false });
    const link = document.createElement('a');
    const dt = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    link.download = `命盘摘要_${dt}.png`;
    link.href = canvas.toDataURL('image/png');
    document.body.appendChild(link);
    link.click();
    setTimeout(() => document.body.removeChild(link), 1000);
    document.getElementById('share-status').textContent = '分享卡图片已导出 ✓';
  } catch (e) {
    document.getElementById('share-status').textContent = '截图失败：' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

/* 打印 / PDF */
function printShareCard() {
  const prev = document.getElementById('share-card-preview');
  if (!prev) return;
  const win = window.open('', '_blank', 'width=620,height=750');
  if (!win) { showToast('请允许弹出窗口后重试', 'warn'); return; }
  const cardStyles = `body{font-family:sans-serif;background:#fdf8f0;padding:28px;max-width:520px;margin:auto}
.sc-title{font-size:1.05rem;font-weight:700;color:#8b1a1a;text-align:center;letter-spacing:.1em}
.sc-born{font-size:.78rem;color:#888;text-align:center;margin-bottom:10px}
.sc-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}.sc-lbl{font-size:.72rem;color:#888;white-space:nowrap}
.sc-pal-chip{font-size:.72rem;padding:3px 9px;border-radius:5px;background:#fff5e6;border:1px solid #d4b896;color:#7c3d12}
.sc-pal-chip.top1{background:#fef3c7;border-color:#b45309;font-weight:700}
.sc-pal-chips{display:flex;flex-wrap:wrap;gap:5px}
.sc-pat-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px}
.sc-pat-chip{font-size:.7rem;padding:2px 8px;border-radius:10px;font-weight:700}
.daji{background:#dcfce7;color:#15803d}.ji{background:#fef9c3;color:#92400e}
.xiong{background:#fee2e2;color:#b91c1c}.daxiong{background:#7f1d1d;color:#fca5a5}
.sc-sug-list{padding-left:1.1em;margin:4px 0 0}.sc-sug-list li{font-size:.76rem;line-height:1.7}
.sc-footer{font-size:.6rem;color:#888;text-align:center;margin-top:10px;padding-top:8px;border-top:1px dashed #d4b896}
.sc-divider{border:none;border-top:1px dashed #d4b896;margin:10px 0}
@media print{body{padding:0}}`;
  win.document.write(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>紫微命盘摘要</title><style>${cardStyles}</style></head><body>${prev.innerHTML}</body></html>`);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); win.close(); }, 400);
}

