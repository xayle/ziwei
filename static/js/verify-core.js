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
const HIST_KEY   = 'bazi_hist_v4';
const HIST_MAX   = 10;

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
    <div class="hist-item" onclick="histFill(${i})">
      <div class="hist-body">
        <div class="hist-dt">${esc(h.dt||'-')} | ${esc(h.userName||'匿名')}</div>
        <div class="hist-rid">${esc(h.rid||'-')}</div>
      </div>
      <div class="hist-ts">${esc(h.ts||'')}</div>
    </div>`).join('');
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
  localStorage.setItem('darkMode', isDark?'1':'0');
  const btn=$('btn-dark');
  if(btn){ btn.textContent=isDark?'☀️':'🌙'; btn.title=isDark?'切换到浅色模式':'切换到深色模式'; }
};

function initDarkMode() {
  const saved = localStorage.getItem('darkMode');
  const systemDark = window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved==='1' || (saved===null&&systemDark)) {
    document.documentElement.classList.add('dark-mode');
    const btn=$('btn-dark');
    if(btn){ btn.textContent='☀️'; btn.title='切换到浅色模式'; }
  }
}

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
  return { dt:dtEl.value, lon, tz, mode:$('mode')?.value||'dual', solar_time_enabled:$('solar_time_enabled')?.checked||false };
};

window.runVerify = async function() {
  setLoading(true);
  let payload;
  try { payload = buildPayload(); } catch(e) { setStatus(e.message,'warn'); setLoading(false); return; }
  ST.payload = payload;
  const t0 = performance.now();
  let res, text;
  try {
    res  = await fetch('/api/v1/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    text = await res.text();
  } catch(e) {
    setStatus(`网络错误: ${e}`,'bad'); setLoading(false); return;
  }
  const elapsed = Math.round(performance.now()-t0);
  setLoading(false);
  let json = null; try{ json=JSON.parse(text); } catch{}
  if (!res.ok || !json) { setStatus(`HTTP ${res.status}`,'bad'); return; }

  ST.result = json;
  ST.tabLoaded.clear();  // 清除懒加载缓存，强制重新渲染
  // 保存历史
  histSave({
    userName:$('userName')?.value, userGender:$('userGender')?.value,
    birthPlace:$('birthPlace')?.value, dt:payload.dt, tz:payload.tz,
    lon:payload.lon, mode:payload.mode, solar:payload.solar_time_enabled,
    rid:json.request_id, level:json.validation?.level, ts:new Date().toLocaleTimeString()
  });
  // 保存到历史命盘 (4.36 最多5条)
  pushProfile({ payload, json, ts:Date.now() });
  // 更新页面
  const activeTab = document.querySelector('.tab-panel.active');
  const activeId  = activeTab ? Number(activeTab.dataset.panel) : 0;
  loadPanel(activeId); // 渲染当前 tab
  // 状态栏
  const warnCount = (json?.validation?.warnings||[]).length;
  setStatus(`✓ 排盘完成 · ${elapsed}ms · 告警${warnCount}条`, warnCount?'warn':'ok');
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
  const map = { root_score:'根气得分', season_score:'旺相休囚', help_score:'帮扶力量', month_gi:'月令气场', dayun_trend:'大运趋势', shensha:'神煞影响', geju_level:'格局层次', yongshen_score:'用神得力', wuxing_balance:'五行均衡' };
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
