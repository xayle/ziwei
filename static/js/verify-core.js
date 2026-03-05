/**
 * verify-core.js  v4.0.20260301
 * M4: 全局状态 / Tab懒加载 / 城市选择器 / 分享链接 / 输入历史
 * 依赖: relation-shared.js (可选)
 */
;(function(){
'use strict';

/* ══════════════════════════════════════════════════
   1. 工具函数
═══════════════════════════════════════════════════ */
const $ = id => document.getElementById(id);
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
// 清洗 API 返回文本中的 "> 分隔符（后端模板注释残留），各段以 · 连接
const cleanText = s => String(s||'').split('">').map(p=>p.trim()).filter(Boolean).join(' · ');
// 短文本：清洗 + 转义（用于行内 kv / hint 字段）
const txt = s => esc(cleanText(s));
// 长段落：每段独立 <p>，适合 note / card 正文
const renderPara = s => { const segs=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return segs.length?segs.map(seg=>`<p style="margin:3px 0;line-height:1.65">${esc(seg)}</p>`).join(''):''; };
// 神煞/chip 名称：取 "> 分隔的最后一段（实际名称），前面的段全部移入 title tooltip
const chipName = s => { const parts=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return parts.length?esc(parts[parts.length-1]):esc(s||''); };
const chipTitle = s => { const parts=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return parts.length>1?esc(parts.slice(0,-1).join(' · ')):esc(s||''); };
const pretty = x => JSON.stringify(x ?? null, null, 2);
const clamp = (v,min,max) => Math.min(Math.max(v,min),max);
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(()=>fn(...a), ms); }; };
const throttle = (fn, ms) => { let last=0; return (...a) => { const n=Date.now(); if(n-last>=ms){fn(...a);last=n;} }; };
const copyText = async (text, btn) => {
  try { await navigator.clipboard.writeText(text); } catch { const ta=document.createElement('textarea'); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
  if(btn){ const old=btn.textContent; btn.textContent='已复制'; btn.classList.add('copied'); setTimeout(()=>{ btn.textContent=old; btn.classList.remove('copied'); },1600); }
};

/* ══════════════════════════════════════════════════
   2. 全局状态 (IIFE共享)
═══════════════════════════════════════════════════ */
window.__BAZI_STATE = window.__BAZI_STATE || {
  result: null,          // 最新 API 响应
  payload: null,         // 最新请求载荷
  tabLoaded: new Set(),  // 已加载的 Tab ID
  cities: [],            // 城市列表缓存
  compareData: null,     // 对比模式数据
  profiles: [],          // 历史命盘 (FIFO 最多5条)
  favorites: [],         // 收藏列表
};
const ST = window.__BAZI_STATE;

/* ══════════════════════════════════════════════════
   3. 翻译/映射表
═══════════════════════════════════════════════════ */
window.TEN_GOD_CN = {
  bi_jian:'比肩', jie_cai:'劫财',
  shi_shen:'食神', shang_guan:'伤官',
  pian_yin:'偏印', zheng_yin:'正印',
  pian_cai:'偏财', zheng_cai:'正财',
  qi_sha:'七杀', zheng_guan:'正官',
  ri_zhu:'日主',  // P64: 日柱标日主
};
window.TEN_GOD_DESC = {
  bi_jian:'同类帮扶，主兄弟合作', jie_cai:'同类争夺，主竞争破财',
  shi_shen:'我生之物，主才华温和', shang_guan:'我生之锐，主聪明叛逆',
  pian_yin:'偏学冷门，主偏艺孤独', zheng_yin:'正统学业，主贵人庇护',
  pian_cai:'投机大财，主偏财横财', zheng_cai:'稳定收入，主正财勤劳',
  qi_sha:'威权压力，主魄力开拓',   zheng_guan:'正统规矩，主事业声誉',
  ri_zhu:'日柱主星，代表自身',
};
window.TEN_GOD_TYPE = {
  bi_jian:'self', jie_cai:'self',
  shi_shen:'output', shang_guan:'output',
  pian_yin:'resource', zheng_yin:'resource',
  pian_cai:'wealth', zheng_cai:'wealth',
  qi_sha:'power', zheng_guan:'power',
};
window.WX_CN  = {wood:'木', fire:'火', earth:'土', metal:'金', water:'水'};
window.WX_CSS = {wood:'wx-wood', fire:'wx-fire', earth:'wx-earth', metal:'wx-metal', water:'wx-water'};
window.wxCN   = k => WX_CN[k] || k;
window.tenGodCN   = code => TEN_GOD_CN[code] || code || '—';
window.tenGodDesc = code => TEN_GOD_DESC[code] || '';
window.tenGodType = code => TEN_GOD_TYPE[code] || '';
window.GAN_WUXING = {'甲':'wood','乙':'wood','丙':'fire','丁':'fire','戊':'earth','己':'earth','庚':'metal','辛':'metal','壬':'water','癸':'water'};
window.GAN_CSS    = {'甲':'gan-mu','乙':'gan-mu','丙':'gan-huo','丁':'gan-huo','戊':'gan-tu','己':'gan-tu','庚':'gan-jin','辛':'gan-jin','壬':'gan-shui','癸':'gan-shui'};
window.ganClass   = g => `gan ${GAN_CSS[g]||''}`;
window.GAN_DESC   = {'甲':'阳木·参天大树','乙':'阴木·花草藤蔓','丙':'阳火·太阳烈焰','丁':'阴火·烛光星火','戊':'阳土·高山大地','己':'阴土·田园沃土','庚':'阳金·刀剑矿石','辛':'阴金·首饰珠玉','壬':'阳水·江河大海','癸':'阴水·雨露溪流'};

/* ══════════════════════════════════════════════════
   4. 状态栏 & 加载
═══════════════════════════════════════════════════ */
window.setStatus = (text, kind='muted') => {
  const bar=$('statusBar'); if(bar){bar.className=kind; bar.querySelector('#statusText').textContent=text||'';}
};
window.setLoading = on => {
  const sp=$('spinner'); if(sp) sp.classList.toggle('active',on);
  const btn=$('btn-run'); if(btn) btn.disabled=on;
  if(on) setStatus('计算中…');
};

/* ══════════════════════════════════════════════════
   5. 20-Tab 导航 + 懒加载 (M4.27)
═══════════════════════════════════════════════════ */
window.TAB_NAMES = ['总览','请求','命盘','格局','命宫','摘要','诊断','财运','事业','姻缘','健康','人际','性格','风水','饰品','开运','大运','流年','月运','案例'];
window.TAB_ICONS = ['☯','📋','🔮','🏆','🏠','📊','🔬','💰','💼','💑','🏥','👥','🧠','🏡','💎','🍀','📅','🗓','☽','📚'];

window.switchTab = function(idx) {
  const id = Number(idx);
  document.querySelectorAll('.tab-nav-item').forEach(b => {
    const active = Number(b.dataset.idx) === id;
    b.setAttribute('aria-selected', active ? 'true' : 'false');
    b.classList.toggle('active', active);
  });
  document.querySelectorAll('.tab-panel').forEach(p => {
    const active = Number(p.dataset.panel) === id;
    p.classList.toggle('active', active);
    if(active) p.setAttribute('aria-hidden','false');
    else p.setAttribute('aria-hidden','true');
  });
  // 更新 URL share tab 参数 (4.32)
  try {
    const url = new URL(location.href);
    url.searchParams.set('tab', id);
    history.replaceState(null,'',url.toString());
  } catch{}
  // 首次 click → 渲染该 tab
  loadPanel(id);
  // 更新移动端底导高亮
  updateBottomNav(id);
};

window.loadPanel = function(id) {
  if (ST.tabLoaded.has(id)) return; // 已加载，不重复渲染
  if (!ST.result) return; // 尚无数据，等待
  ST.tabLoaded.add(id);
  // 显示骨架屏
  const wrapper = document.querySelector(`[data-panel="${id}"] .skeleton-wrapper`);
  if (wrapper) wrapper.classList.add('active');
  // 延迟1帧后渲染（让骨架屏先显示）
  requestAnimationFrame(() => {
    if (wrapper) wrapper.classList.remove('active');
    if (typeof renderTabById === 'function') renderTabById(id, ST.result);
    // 术语 tooltip（task 4.14）
    const panelEl = document.querySelector(`[data-panel="${id}"]`);
    if (panelEl && window.__Glossary) window.__Glossary.apply(panelEl);
    // 更新 tab dot 状态
    const btn = document.querySelector(`.tab-nav-item[data-idx="${id}"]`);
    if (btn) {
      const dot = btn.querySelector('.tab-dot');
      if (dot) dot.classList.add('ready');
      btn.classList.add('has-data');
    }
  });
};

window.reloadAllTabs = function() {
  ST.tabLoaded.clear();
  const activePanel = document.querySelector('.tab-panel.active');
  if (activePanel) {
    const id = Number(activePanel.dataset.panel);
    loadPanel(id);
  }
};

/* ══════════════════════════════════════════════════
   6. 城市选择器 (M4.24)
═══════════════════════════════════════════════════ */
async function loadCities() {
  try {
    const r = await fetch('/api/v1/cities');
    if (!r.ok) return;
    const cities = await r.json();
    ST.cities = cities;
    const sel = $('citySelect');
    if (!sel) return;
    sel.innerHTML = '<option value="">— 选择城市（自动填入经度）—</option>';
    cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.lng;
      opt.dataset.name = c.name;
      opt.dataset.province = c.province || '';
      opt.textContent = `${c.name}（${c.province||''}）${c.lng}°E`;
      sel.appendChild(opt);
    });
    // 默认北京 (4.24)
    sel.value = '';
    setLonHint();
  } catch(e) {
    console.warn('城市列表加载失败:', e);
  }
}

function setLonHint() {
  const lonEl = $('lon');
  if (lonEl && !lonEl.value) {
    lonEl.value = '116.41';
    const hint = $('lonHint');
    if (hint) hint.textContent = '使用默认北京经度（116.41°E）';
  }
}

/* ══════════════════════════════════════════════════
   7. 表单保存/加载 & 输入历史 (M4.33)
═══════════════════════════════════════════════════ */
const INPUTS_KEY = 'bazi_inputs_v4';
const HIST_KEY   = 'bazi_history';   // N5.01: Array<{id,ts,summary}>, FIFO 5
const HIST_MAX   = 5;

window.saveInputs = function() {
  try {
    localStorage.setItem(INPUTS_KEY, JSON.stringify({
      userName:$('userName')?.value,
      userGender:$('userGender')?.value,
      birthPlace:$('birthPlace')?.value,
      dt:$('dt')?.value,
      tz:$('tz')?.value,
      lon:$('lon')?.value,
      mode:$('mode')?.value,
      solar:$('solar_time_enabled')?.checked,
    }));
  } catch{}
};

window.loadInputs = function() {
  try {
    const d = JSON.parse(localStorage.getItem(INPUTS_KEY)||'null');
    if (!d) { setLonHint(); return; }
    if($('userName') && d.userName) $('userName').value = d.userName;
    if($('userGender') && d.userGender) $('userGender').value = d.userGender;
    if($('birthPlace') && d.birthPlace) $('birthPlace').value = d.birthPlace;
    if($('dt') && d.dt) $('dt').value = d.dt;
    if($('tz') && d.tz) $('tz').value = d.tz;
    if($('lon') && d.lon) { $('lon').value = d.lon; } else { setLonHint(); }
    if($('mode') && d.mode) $('mode').value = d.mode;
    if($('solar_time_enabled') && d.solar !== undefined) $('solar_time_enabled').checked = d.solar;
  } catch { setLonHint(); }
};

window.histLoad = () => { try { return JSON.parse(localStorage.getItem(HIST_KEY)||'[]'); } catch { return []; } };
window.histSave = entry => {
  try {
    const a = histLoad(); a.unshift(entry);
    localStorage.setItem(HIST_KEY, JSON.stringify(a.slice(0, HIST_MAX)));
    histRender();
  } catch{}
};
window.histRender = function() {
  const list = $('histList'); if (!list) return;
  const items = histLoad();
  if (!items.length) { list.innerHTML = '<div class="hint" style="padding:8px">暂无历史记录</div>'; $('histCount').textContent='0'; return; }
  $('histCount').textContent = items.length;
  list.innerHTML = items.map((h,i) => `
    <div class="hist-item" data-hist-fill="${i}">
      <div class="hist-body">
        <div class="hist-dt">${esc(h.dt||'-')} | ${esc(h.userName||'匿名')}</div>
        ${h.summary ? `<div class="hist-summary" style="font-size:11px;color:var(--muted);margin-top:3px;display:flex;flex-wrap:wrap;gap:6px">
          <span>${esc(h.summary.day_stem||'—')}日主</span>
          <span>${esc(h.summary.geju||'—')}</span>
          <span>用神:${esc(h.summary.yongshen||'—')}</span>
          ${h.summary.annual_score!=null?`<span style="color:var(--ok)">本年:${h.summary.annual_score}分</span>`:''}
        </div>` : `<div class="hist-rid">${esc(h.rid||'-')}</div>`}
      </div>
      <div class="hist-ts">${esc(h.ts||'')}</div>
    </div>`).join('');
  if (items.length >= 2) {
    list.innerHTML += `<div style="padding:6px 4px 2px"><button data-action="histCompare" style="width:100%;font-size:12px;background:var(--input);border:1px solid var(--border);padding:6px 0;border-radius:6px;cursor:pointer">对比最近2条 →</button></div>`;
  }
};
window.histCompare = function() {
  const items = histLoad();
  if (items.length < 2) return;
  const [a, b] = [items[0], items[1]];
  const sa = a.summary||{}, sb = b.summary||{};
  const diffCls = (va, vb) => va !== vb ? 'style="color:var(--accent);font-weight:700"' : '';
  const modal = $('modalHistCompare');
  if (modal) {
    const body = modal.querySelector('.hist-compare-body');
    if (body) body.innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <thead><tr>
        <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)">项目</th>
        <th style="padding:6px 8px;border-bottom:1px solid var(--border);color:var(--accent)">${esc(a.ts||'最新')} ${esc(a.dt||'')}</th>
        <th style="padding:6px 8px;border-bottom:1px solid var(--border);color:var(--muted)">${esc(b.ts||'上条')} ${esc(b.dt||'')}</th>
      </tr></thead>
      <tbody>
        <tr><td style="padding:5px 8px;color:var(--muted)">日主</td><td ${diffCls(sa.day_stem,sb.day_stem)} style="padding:5px 8px">${esc(sa.day_stem||'—')}</td><td ${diffCls(sb.day_stem,sa.day_stem)} style="padding:5px 8px">${esc(sb.day_stem||'—')}</td></tr>
        <tr><td style="padding:5px 8px;color:var(--muted)">格局</td><td ${diffCls(sa.geju,sb.geju)} style="padding:5px 8px">${esc(sa.geju||'—')}</td><td ${diffCls(sb.geju,sa.geju)} style="padding:5px 8px">${esc(sb.geju||'—')}</td></tr>
        <tr><td style="padding:5px 8px;color:var(--muted)">用神</td><td ${diffCls(sa.yongshen,sb.yongshen)} style="padding:5px 8px">${esc(sa.yongshen||'—')}</td><td ${diffCls(sb.yongshen,sa.yongshen)} style="padding:5px 8px">${esc(sb.yongshen||'—')}</td></tr>
        <tr><td style="padding:5px 8px;color:var(--muted)">本年运势</td><td style="padding:5px 8px;font-weight:700;color:${sa.annual_score>=70?'var(--ok)':sa.annual_score>=50?'var(--warn)':'var(--bad)'}">${sa.annual_score!=null?sa.annual_score+'分':'—'}</td><td style="padding:5px 8px;font-weight:700;color:${sb.annual_score>=70?'var(--ok)':sb.annual_score>=50?'var(--warn)':'var(--bad)'}">${sb.annual_score!=null?sb.annual_score+'分':'—'}</td></tr>
      </tbody>
    </table>`;
    modal.classList.add('show');
    return;
  }
  // Fallback: inline compare panel
  const panel = $('histComparePanel');
  if (!panel) return;
  panel.innerHTML = `
  <div style="font-weight:700;font-size:13px;margin-bottom:10px">最近2条历史对比</div>
  <table style="width:100%;border-collapse:collapse;font-size:12px">
    <thead><tr>
      <th style="padding:4px 6px;text-align:left;border-bottom:1px solid var(--border)">项目</th>
      <th style="padding:4px 6px;border-bottom:1px solid var(--border);color:var(--accent)">最新 ${esc(a.dt||'')}</th>
      <th style="padding:4px 6px;border-bottom:1px solid var(--border);color:var(--muted)">上条 ${esc(b.dt||'')}</th>
    </tr></thead>
    <tbody>
      <tr><td style="padding:4px 6px;color:var(--muted)">格局</td><td ${diffCls(sa.geju,sb.geju)} style="padding:4px 6px">${esc(sa.geju||'—')}</td><td ${diffCls(sb.geju,sa.geju)} style="padding:4px 6px">${esc(sb.geju||'—')}</td></tr>
      <tr><td style="padding:4px 6px;color:var(--muted)">用神</td><td ${diffCls(sa.yongshen,sb.yongshen)} style="padding:4px 6px">${esc(sa.yongshen||'—')}</td><td ${diffCls(sb.yongshen,sa.yongshen)} style="padding:4px 6px">${esc(sb.yongshen||'—')}</td></tr>
      <tr><td style="padding:4px 6px;color:var(--muted)">本年运势</td><td style="padding:4px 6px;font-weight:700">${sa.annual_score!=null?sa.annual_score+'分':'—'}</td><td style="padding:4px 6px;font-weight:700">${sb.annual_score!=null?sb.annual_score+'分':'—'}</td></tr>
    </tbody>
  </table>`;
  panel.style.display = 'block';
};
window.histFill = i => {
  const items = histLoad(); const h = items[i]; if(!h) return;
  if(h.userName) $('userName').value=h.userName;
  if(h.userGender) $('userGender').value=h.userGender;
  if(h.birthPlace) $('birthPlace').value=h.birthPlace;
  if(h.dt && $('dt')) $('dt').value=h.dt;
  if(h.tz && $('tz')) $('tz').value=h.tz;
  if(h.lon && $('lon')) $('lon').value=h.lon;
  if(h.mode && $('mode')) $('mode').value=h.mode;
  if(h.solar !== undefined && $('solar_time_enabled')) $('solar_time_enabled').checked=h.solar;
  saveInputs();
  setStatus('历史参数已填入，请点击"开始排盘"','muted');
};

/* ══════════════════════════════════════════════════
   8. 分享链接 (M4.25, M4.32)
═══════════════════════════════════════════════════ */
window.buildShareURL = function() {
  const dt = $('dt')?.value||'';
  if (!dt) return null;
  const d = new Date(dt);
  const params = new URLSearchParams();
  params.set('y',  d.getFullYear());
  params.set('m',  d.getMonth()+1);
  params.set('d',  d.getDate());
  params.set('h',  d.getHours());
  params.set('mi', d.getMinutes());
  params.set('sex', $('userGender')?.value||'');
  params.set('lng', $('lon')?.value||'116.41');
  params.set('solar', $('solar_time_enabled')?.checked?'1':'0');
  params.set('share','1');
  // 当前 tab
  const activeTab = document.querySelector('.tab-nav-item.active');
  if (activeTab) params.set('tab', activeTab.dataset.tab||'0');
  return `${location.origin}${location.pathname}?${params.toString()}`;
};

window.showShareModal = function() {
  const url = buildShareURL();
  if (!url) { setStatus('请先填写出生时间', 'warn'); return; }
  const modal = $('modalShare');
  if (!modal) return;
  const inp = modal.querySelector('#shareUrlInput');
  if (inp) inp.value = url;
  modal.classList.add('show');
};

// 从 URL 参数回填表单
function fillFromShareParams() {
  const qp = new URLSearchParams(location.search);
  if (qp.get('share') !== '1') return;
  const y=qp.get('y'), m=qp.get('m'), d=qp.get('d'), h=qp.get('h'), mi=qp.get('mi');
  if (y&&m&&d&&h&&mi) {
    const pad = n=>String(n).padStart(2,'0');
    const dtVal = `${y}-${pad(m)}-${pad(d)}T${pad(h)}:${pad(mi)}`;
    if ($('dt')) $('dt').value = dtVal;
  }
  const lng=qp.get('lng'); if(lng && $('lon')) $('lon').value=lng;
  const sex=qp.get('sex'); if(sex && $('userGender')) $('userGender').value=sex;
  const solar=qp.get('solar'); if(solar && $('solar_time_enabled')) $('solar_time_enabled').checked=solar==='1';
  saveInputs();
  // 自动运行
  setTimeout(()=>{ const btn=$('btn-run'); if(btn) btn.click(); }, 400);
}

// URL参数恢复 tab (4.32)
function restoreTabFromURL() {
  const qp = new URLSearchParams(location.search);
  const tab = qp.get('tab');
  if (tab !== null && /^\d+$/.test(tab)) {
    const idx = clamp(Number(tab),0,19);
    setTimeout(()=>switchTab(idx), 100);
  }
}

/* ══════════════════════════════════════════════════
   9. 深色模式 (M4.31 已有, 增强)
═══════════════════════════════════════════════════ */
window.toggleDarkMode = function() {
  const html = document.documentElement;
  const isDark = html.classList.toggle('dark-mode');
  // N5.09: 双机制 — 也设置 data-theme 属性
  html.dataset.theme = isDark ? 'dark' : 'light';
  localStorage.setItem('darkMode', isDark?'1':'0');
  const btn=$('btn-dark');
  if(btn){ btn.textContent=isDark?'☀️':'🌙'; btn.title=isDark?'切换到浅色模式':'切换到深色模式'; }
};

function initDarkMode() {
  const saved = localStorage.getItem('darkMode');
  const systemDark = window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved==='1' || (saved===null&&systemDark)) {
    document.documentElement.classList.add('dark-mode');
    document.documentElement.dataset.theme = 'dark';
    const btn=$('btn-dark');
    if(btn){ btn.textContent='☀️'; btn.title='切换到浅色模式'; }
  } else if (saved==='0') {
    document.documentElement.dataset.theme = 'light';
  }
}

/* ══════════════════════════════════════════════════
   N5.08 移动端 Tab Select 初始化
═══════════════════════════════════════════════════ */
function initMobileTabSelect() {
  const tabNav = document.getElementById('tabNav');
  if (!tabNav) return;
  // 只在小屏幕上插入 select（也可在 resize 中处理，这里直接插入并用 CSS 控制显示）
  if (document.getElementById('tab-mobile-select')) return;
  const buttons = Array.from(tabNav.querySelectorAll('.tab-nav-item[data-idx]'));
  const sel = document.createElement('select');
  sel.id = 'tab-mobile-select';
  sel.setAttribute('aria-label', '功能面板导航');
  buttons.forEach(btn => {
    const opt = document.createElement('option');
    opt.value = btn.dataset.idx;
    // Extract text content without the dot span
    opt.textContent = btn.textContent.replace('●','').trim();
    sel.appendChild(opt);
  });
  sel.addEventListener('change', () => {
    switchTab(Number(sel.value));
  });
  // Insert before the tab nav
  tabNav.parentNode.insertBefore(sel, tabNav);
}

// 在 switchTab 中同步 select 值
const _origSwitchTab = window.switchTab;
window.switchTab = function(idx) {
  if (_origSwitchTab) _origSwitchTab(idx);
  const sel = document.getElementById('tab-mobile-select');
  if (sel && sel.value !== String(idx)) sel.value = String(idx);
};

/* ══════════════════════════════════════════════════
   10. 请求构建 & API 调用
═══════════════════════════════════════════════════ */
function normalizeTimezone(tz) {
  const map = {'北京时':'Asia/Shanghai','上海':'Asia/Shanghai','东八区':'Asia/Shanghai','UTC+8':'Asia/Shanghai','CST':'Asia/Shanghai'};
  return map[tz.trim()] || tz.trim() || 'Asia/Shanghai';
}

window.buildPayload = function() {
  const dtEl=$('dt'), lonEl=$('lon'), tzEl=$('tz');
  if (!dtEl?.value) { dtEl?.classList.add('err'); throw new Error('请填写出生时间'); }
  const lon = parseFloat(lonEl?.value);
  if (isNaN(lon)||lon<70||lon>140) { lonEl?.classList.add('err'); throw new Error('经度须在 70–140 之间'); }
  dtEl.classList.remove('err'); lonEl.classList.remove('err');
  const tz = normalizeTimezone(tzEl?.value||'Asia/Shanghai');
  const sexEl = $('sex');
  const gender = sexEl?.value === 'M' ? 'male' : sexEl?.value === 'F' ? 'female' : null;
  const payload = { dt:dtEl.value, lon, tz, mode:$('mode')?.value||'dual', solar_time_enabled:$('solar_time_enabled')?.checked||false };
  if (gender) payload.gender = gender;
  return payload;
};

/* §4.5.1: 带 AbortController 超时的 fetch（30s）*/
async function fetchWithTimeout(url, opts, ms) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: ctrl.signal });
  } finally {
    clearTimeout(timer);
  }
}

window.runVerify = async function() {
  setLoading(true);
  let payload;
  try { payload = buildPayload(); } catch(e) { setStatus(e.message,'warn'); setLoading(false); return; }
  ST.payload = payload;

  /* §4.5.1: 最多 2 次自动重试（仅针对 5xx / 网络超时）*/
  const MAX_RETRY = 2;
  let res, text, lastErr;
  for (let attempt = 0; attempt <= MAX_RETRY; attempt++) {
    try {
      const t0 = performance.now();
      res  = await fetchWithTimeout(
        '/api/v1/verify',
        { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) },
        30000   // 30 秒超时
      );
      text = await res.text();
      lastErr = null;
      // 4xx 立即停止，不重试
      if (res.status >= 400 && res.status < 500) break;
      // 5xx 若还有重试次数则继续
      if (res.status >= 500 && attempt < MAX_RETRY) {
        showToast(`服务器繁忙，正在重试（${attempt+1}/${MAX_RETRY}）…`, 'warn', 2000);
        continue;
      }
      break; // 2xx 或重试耗尽
    } catch(e) {
      lastErr = e;
      if (e.name === 'AbortError') {
        /* §4.5.1: 超时 → skeleton 保持，Tab 右上角 badge */
        setLoading(false);
        setStatus('请求超时（>30s），请检查网络后重试', 'bad');
        document.querySelectorAll('.tab-panel.active .tab-badge-timeout').forEach(b=>b.remove());
        const activePanel = document.querySelector('.tab-panel.active');
        if (activePanel) {
          const badge = document.createElement('span');
          badge.className = 'tab-badge-timeout';
          badge.textContent = '请求超时';
          badge.style.cssText = 'position:absolute;top:8px;right:8px;background:#C0392B;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;z-index:10';
          activePanel.style.position = 'relative';
          activePanel.appendChild(badge);
        }
        return;
      }
      if (attempt < MAX_RETRY) {
        showToast(`网络错误，正在重试（${attempt+1}/${MAX_RETRY}）…`, 'warn', 2000);
        continue;
      }
      // 重试耗尽
      setStatus(`网络错误: ${e}`, 'bad'); setLoading(false); return;
    }
  }

  const elapsed = Math.round(performance.now() - (performance.now() - 1)); // approx
  setLoading(false);

  /* §4.5.1: JSON 解析异常 */
  let json = null;
  try { json = JSON.parse(text); } catch(e) {
    console.error('[runVerify] JSON 解析异常:', e, text?.slice(0,200));
    const activePanel = document.querySelector('.tab-panel.active');
    if (activePanel) {
      activePanel.insertAdjacentHTML('afterbegin',
        '<p style="color:#C0392B;padding:12px">⚠ 数据解析异常，请刷新重试</p>');
    }
    setStatus('数据解析异常', 'bad'); return;
  }

  /* §4.5.1: 4xx → toast(error.detail)，不自动重试 */
  if (!res.ok) {
    const detail = json?.detail || `HTTP ${res.status}`;
    if (res.status >= 400 && res.status < 500) {
      showToast(detail, 'error', 4000);
      setStatus(detail, 'bad');
    } else {
      showToast('系统繁忙，请稍后重试', 'error', 4000);
      setStatus(`HTTP ${res.status}`, 'bad');
    }
    return;
  }
  if (!json) { setStatus('空响应', 'bad'); return; }

  ST.result = json;
  ST.tabLoaded.clear();  // 清除懒加载缓存，强制重新渲染
  // 保存历史 (N5.01: {id,ts,summary} + form fill fields, FIFO 5)
  const _thisYear = new Date().getFullYear();
  histSave({
    id: json.request_id || Date.now().toString(36),
    ts: new Date().toLocaleTimeString(),
    summary: {
      day_stem: json.pillars_primary?.day?.stem || null,
      geju: json.geju?.geju_name || json.geju?.name || null,
      yongshen: (json.yongshen?.favor||[]).join('/') || null,
      annual_score: (json.liunian_detail||[]).find(l=>l.year===_thisYear)?.annual_score ?? null,
    },
    userName:$('userName')?.value, userGender:$('userGender')?.value,
    birthPlace:$('birthPlace')?.value, dt:payload.dt, tz:payload.tz,
    lon:payload.lon, mode:payload.mode, solar:payload.solar_time_enabled,
    rid:json.request_id, level:json.validation?.level,
  });
  // 保存到历史命盘 (4.36 最多5条)
  pushProfile({ payload, json, ts:Date.now() });
  // 更新页面
  const activeTab = document.querySelector('.tab-panel.active');
  const activeId  = activeTab ? Number(activeTab.dataset.panel) : 0;
  loadPanel(activeId); // 渲染当前 tab
  // 状态栏
  const warnCount = (json?.validation?.warnings||[]).length;
  setStatus(`✓ 排盘完成 · 告警${warnCount}条`, warnCount?'warn':'ok');
};

/* ══════════════════════════════════════════════════
   11. 历史命盘 (M4.36, FIFO 5条)
═══════════════════════════════════════════════════ */
const PROFILES_KEY = 'bazi_profiles_v1';
function pushProfile(item) {
  try {
    const list = JSON.parse(localStorage.getItem(PROFILES_KEY)||'[]');
    list.unshift(item);
    localStorage.setItem(PROFILES_KEY, JSON.stringify(list.slice(0,5)));
    ST.profiles = list.slice(0,5);
  } catch{}
}
window.loadProfiles = function() {
  try { ST.profiles = JSON.parse(localStorage.getItem(PROFILES_KEY)||'[]'); } catch { ST.profiles=[]; }
  return ST.profiles;
};

/* ══════════════════════════════════════════════════
   12. 移动端底导 (M4.28)
═══════════════════════════════════════════════════ */
const BOTTOM_TABS = [
  {idx:0,icon:'☯',label:'总览'},
  {idx:2,icon:'🔮',label:'命盘'},
  {idx:16,icon:'📅',label:'大运'},
  {idx:17,icon:'🗓',label:'流年'},
  {idx:7,icon:'💰',label:'财运'},
];
function initBottomNav() {
  const inner = $('bottomNav'); if(!inner) return;
  BOTTOM_TABS.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'bottom-nav-btn';
    btn.dataset.tab = t.idx;
    btn.innerHTML = `<span class="bn-icon">${t.icon}</span><span>${t.label}</span>`;
    btn.addEventListener('click',()=>switchTab(t.idx));
    inner.appendChild(btn);
  });
  // 更多抽屉按钮
  const moreBtnWrap = $('bottomNavMore');
  if (moreBtnWrap) {
    moreBtnWrap.addEventListener('click', e=>{ e.stopPropagation(); $('moreDrawer')?.classList.toggle('open'); });
  }
  document.addEventListener('click',()=>{ $('moreDrawer')?.classList.remove('open'); });
}

window.updateBottomNav = function(activeIdx) {
  document.querySelectorAll('.bottom-nav-btn[data-tab]').forEach(btn => {
    btn.classList.toggle('active', Number(btn.dataset.tab)===activeIdx);
  });
};

/* ══════════════════════════════════════════════════
   13. 新手引导 (M4.14)
═══════════════════════════════════════════════════ */
const GUIDE_KEY = 'bazi_guide_done_v4';
function maybeShowOnboarding() {
  if (localStorage.getItem(GUIDE_KEY)) return;
  const overlay = $('onboardingOverlay');
  if (!overlay) return;
  overlay.style.display = 'flex';
}

window.nextOnboardingStep = function(step) {
  document.querySelectorAll('.onboarding-step').forEach((el,i)=>{ el.style.display=i===step?'block':'none'; });
  document.querySelectorAll('.onboarding-dot').forEach((d,i)=>{ d.classList.toggle('active',i===step); });
};

window.closeOnboarding = function() {
  const overlay = $('onboardingOverlay');
  if (overlay) overlay.style.display = 'none';
  localStorage.setItem(GUIDE_KEY,'1');
};

/* ══════════════════════════════════════════════════
   14. IndexedDB 缓存
═══════════════════════════════════════════════════ */
let _db = null;
function initDB() {
  return new Promise((resolve, reject) => {
    if (_db) { resolve(_db); return; }
    const req = indexedDB.open('bazi_results_v4', 2);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('results')) {
        const store = db.createObjectStore('results', {keyPath:'id',autoIncrement:true});
        store.createIndex('timestamp','timestamp',{unique:false});
      }
    };
    req.onsuccess = e => { _db=e.target.result; resolve(_db); };
    req.onerror   = () => reject(req.error);
  });
}

window.saveCacheResult = async function(item) {
  try {
    const db = await initDB();
    const tx = db.transaction('results','readwrite');
    tx.objectStore('results').add({...item, timestamp:Date.now()});
  } catch{}
};

/* ══════════════════════════════════════════════════
   15. helper: translateFactorName / Reason / Rationale
═══════════════════════════════════════════════════ */
window.translateFactorName = function(name) {
  const map = {
    root_score:'根气得分', season_score:'旺相休囚', help_score:'帮扶力量',
    month_gi:'月令气场', dayun_trend:'大运趋势', shensha:'神煞影响',
    geju_level:'格局层次', yongshen_score:'用神得力', wuxing_balance:'五行均衡',
    same_element_support:'同类帮扶', parent_element_support:'母生相助',
    child_element_drain:'泄耗子星', controlling_element:'克制用事',
    branch_root:'地支有根', stem_help:'天干帮扶', stem_clash:'天干相冲',
    branch_clash:'地支相冲', branch_combine:'地支相合', branch_penalty:'地支相刑',
    five_tiger:'五虎运', five_rat:'五鼠遁', nayin_score:'纳音影响',
    geju_score:'格局加成', special_geju:'特殊格局', kongliang:'空亡影响',
    dayun_stem:'大运天干', dayun_branch:'大运地支', liunian_impact:'流年影响'
  };
  return map[name] || name;
};
window.translateFactorReason = function(text) {
  const map = { inner_season:'月令主旺', outer_season:'月令休囚', root_in_branch:'地支有根', branch_clash:'地支相冲', direct_help:'天干帮扶', indirect_help:'间接帮扶' };
  return map[text] || text;
};
window.translateRationale = function(text) {
  if (!text) return '';
  const m = [{from:'strong',to:'身强'},{from:'weak',to:'身弱'},{from:'neutral',to:'中和'},{from:'extremely_strong',to:'极强'},{from:'extremely_weak',to:'极弱'}];
  let r = text;
  m.forEach(p=>{ r=r.replaceAll(p.from,p.to); });
  return r;
};

/* ══════════════════════════════════════════════════
   16. curl 生成
═══════════════════════════════════════════════════ */
window.makeCurl = function(p) {
  const j = JSON.stringify(p);
  const base = window.location.origin||'http://127.0.0.1:8000';
  return `curl -sS -X POST ${base}/api/v1/verify -H "Content-Type: application/json" -d '${j.replaceAll("'","'\\''")}' `;
};

/* ══════════════════════════════════════════════════
   17. 事件绑定 & 初始化
═══════════════════════════════════════════════════ */
function bindTabNav() {
  document.querySelectorAll('.tab-nav-item[data-idx]').forEach(btn => {
    btn.addEventListener('click', () => switchTab(Number(btn.dataset.idx)));
  });
}

function bindFormEvents() {
  $('btn-run')?.addEventListener('click', runVerify);
  $('btn-now')?.addEventListener('click', () => {
    const n=new Date(), p=n=>String(n).padStart(2,'0');
    if($('dt')) $('dt').value=`${n.getFullYear()}-${p(n.getMonth()+1)}-${p(n.getDate())}T${p(n.getHours())}:${p(n.getMinutes())}`;
    saveInputs();
  });
  $('btn-demo')?.addEventListener('click', () => {
    if($('userName'))  $('userName').value='张三';
    if($('userGender')) $('userGender').value='male';
    if($('birthPlace')) $('birthPlace').value='上海市浦东新区';
    if($('dt'))  $('dt').value='2002-03-13T14:36';
    if($('tz'))  $('tz').value='Asia/Shanghai';
    if($('lon')) $('lon').value='121.4737';
    if($('mode')) $('mode').value='dual';
    if($('solar_time_enabled')) $('solar_time_enabled').checked=false;
    saveInputs();
    setStatus('示例已填入，点击"开始排盘"','muted');
  });
  $('btn-curl')?.addEventListener('click', async () => {
    let p; try{p=buildPayload();}catch(e){setStatus(e.message,'warn');return;}
    await copyText(makeCurl(p), $('btn-curl'));
  });
  $('btn-dark')?.addEventListener('click', toggleDarkMode);
  $('btn-share')?.addEventListener('click', showShareModal);
  $('btn-compare')?.addEventListener('click', () => { if(typeof toggleCompare==='function') toggleCompare(); });
  $('btn-fav')?.addEventListener('click', () => { if(typeof showFavoritesModal==='function') showFavoritesModal(); });
  $('btn-add-fav')?.addEventListener('click', () => { if(typeof addFavorite==='function') addFavorite(); });
  $('btn-export-menu')?.addEventListener('click', () => { if(typeof toggleExportMenu==='function') toggleExportMenu(); });
  $('btn-hist-drawer')?.addEventListener('click', () => { $('historyDrawer')?.classList.toggle('open'); if(typeof renderHistoryDrawer==='function') renderHistoryDrawer(); });
  // 城市选择器
  $('citySelect')?.addEventListener('change', e => {
    const val = e.target.value;
    if (val && $('lon')) { $('lon').value = val; const hint=$('lonHint'); if(hint) hint.textContent=`${e.target.options[e.target.selectedIndex].dataset.name} ${val}°E`; }
  });
  // 分享 Modal 复制
  $('btn-copy-share')?.addEventListener('click', () => {
    const inp = $('shareUrlInput'); if(!inp) return;
    copyText(inp.value, $('btn-copy-share'));
  });
  // 新手引导关闭
  $('btn-onboarding-close')?.addEventListener('click', () => { if(typeof closeOnboarding==='function') closeOnboarding(); });
  // 防抖自动保存
  const ds = debounce(saveInputs, 400);
  ['dt','tz','lon','mode'].forEach(id=>{ $(id)?.addEventListener('change',ds); $(id)?.addEventListener('input',ds); });
  $('solar_time_enabled')?.addEventListener('change', ds);
  // 历史清空
  $('btn-clear-hist')?.addEventListener('click', () => { localStorage.removeItem(HIST_KEY); histRender(); });
}

function initPWA() {
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', async () => {
    const CLEANUP_KEY = 'sw_cleanup_v4';
    try {
      if (!localStorage.getItem(CLEANUP_KEY)) {
        const regs = await navigator.serviceWorker.getRegistrations();
        await Promise.all(regs.map(r=>r.unregister()));
        if ('caches' in window) { const ks=await caches.keys(); await Promise.all(ks.map(k=>caches.delete(k))); }
        localStorage.setItem(CLEANUP_KEY,'1');
      }
    } catch{}
    navigator.serviceWorker.register('/static/sw.js',{updateViaCache:'none'})
      .then(reg=>{ reg.update(); console.log('✓ SW registered'); })
      .catch(e=>console.warn('✗ SW failed:',e));
  });
}

// ARIA live region 状态通知 (M4.17)
function announceStatus(msg) {
  const live = $('ariaLiveStatus'); if(!live) return;
  live.textContent = msg;
  setTimeout(()=>{ live.textContent=''; }, 2000);
}
window.announceStatus = announceStatus;

/* task 4.23: 首次访问免责声明弹窗 (localStorage=bazi_disclaimer_v1) */
function initDisclaimer() {
  var KEY = 'bazi_disclaimer_v1';
  if (!localStorage.getItem(KEY)) {
    var el = document.getElementById('disclaimerOverlay');
    if (el) { el.style.display = 'flex'; }
    var btn = document.getElementById('disclaimerBtn');
    if (btn) {
      btn.addEventListener('click', function() {
        localStorage.setItem(KEY, '1');
        document.getElementById('disclaimerOverlay').style.display = 'none';
      });
    }
  }
}

/* 主初始化 */
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  bindTabNav();
  bindFormEvents();
  loadInputs();
  histRender();
  initBottomNav();
  loadCities();
  fillFromShareParams();
  restoreTabFromURL();
  initPWA();
  maybeShowOnboarding();
  initDisclaimer();  // task 4.23: 首次免责声明弹窗
  // N5.08: 移动端 Tab 下拉 select
  initMobileTabSelect();
  // Keyboard shortcut: Enter 提交
  document.addEventListener('keydown', e => {
    const tag = document.activeElement?.tagName;
    if (tag==='INPUT'||tag==='SELECT'||tag==='TEXTAREA') return;
    if (e.key==='Enter') { $('btn-run')?.click(); }
    if (e.key>='0'&&e.key<='9'&&!e.ctrlKey&&!e.altKey) { switchTab(Number(e.key)); }
  });
  // 默认显示 Tab 0
  switchTab(0);
});

/* ══════════════════════════════════════════════════
   通用 Toast 提示  [红线16: 禁止 alert/prompt]
   用法: showToast('消息', 'info'|'success'|'warn'|'error', 毫秒)
═══════════════════════════════════════════════════ */
window.showToast = function(msg, type, duration) {
  type = type || 'info';
  duration = duration || 2500;
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);z-index:99999;display:flex;flex-direction:column;align-items:center;gap:8px;pointer-events:none';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  const colors = {info:'#555',success:'#2E8B57',warn:'#B8860B',error:'#B22222'};
  t.style.cssText = `background:${colors[type]||colors.info};color:#fff;padding:9px 20px;border-radius:6px;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,.3);pointer-events:none;opacity:0;transition:opacity .25s`;
  t.textContent = msg;
  container.appendChild(t);
  requestAnimationFrame(()=>{ t.style.opacity='1'; });
  setTimeout(()=>{ t.style.opacity='0'; setTimeout(()=>t.remove(), 280); }, duration);
};

/* 输入弹窗替代 prompt()  [红线16] */
window.showInputModal = function(title, placeholder, callback) {
  let overlay = document.getElementById('inputModalOverlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'inputModalOverlay';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9999;align-items:center;justify-content:center';
    overlay.innerHTML = `<div style="background:#fff;border-radius:8px;padding:24px;min-width:280px;max-width:90vw">
      <p id="inputModalTitle" style="margin:0 0 12px;font-weight:600"></p>
      <input id="inputModalField" type="text" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #ccc;border-radius:4px;font-size:14px">
      <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px">
        <button id="inputModalCancel" style="padding:6px 16px;border:1px solid #ccc;border-radius:4px;cursor:pointer;background:#f5f5f5">取消</button>
        <button id="inputModalOk" style="padding:6px 16px;background:var(--accent-red,#B22222);color:#fff;border:none;border-radius:4px;cursor:pointer">确定</button>
      </div></div>`;
    document.body.appendChild(overlay);
  }
  overlay.querySelector('#inputModalTitle').textContent = title || '';
  const field = overlay.querySelector('#inputModalField');
  field.placeholder = placeholder || '';
  field.value = '';
  overlay.style.display = 'flex';
  field.focus();
  const finish = (val) => { overlay.style.display='none'; callback && callback(val); };
  overlay.querySelector('#inputModalOk').onclick = () => finish(field.value.trim());
  overlay.querySelector('#inputModalCancel').onclick = () => finish(null);
  overlay.onclick = (e) => { if(e.target===overlay) finish(null); };
  field.onkeydown = (e) => { if(e.key==='Enter') finish(field.value.trim()); if(e.key==='Escape') finish(null); };
};

})();
