/**
 * verify-render.js  v4.0.20260301
 * M4: 20个 Tab 渲染 / 命盘 / 五行 / 大运 / 流年 / 月运 / 总览 / 格局 / 命宫 等
 * 依赖: verify-core.js
 */
;(function(){
'use strict';

/* ── 便捷工具 ─────────────────────────────────── */
const $  = id => document.getElementById(id);
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const nn  = v => v === null || v === undefined ? '—' : v;
const pct = (v,total) => total ? Math.round(v/total*100) : 0;

/* ══════════════════════════════════════════════════
   路由: renderTabById
═══════════════════════════════════════════════════ */
window.renderTabById = function(id, json) {
  const fn = [
    renderTab0, renderTab1, renderTab2, renderTab3, renderTab4,
    renderTab5, renderTab6, renderTab7, renderTab8, renderTab9,
    renderTab10, renderTab11, renderTab12, renderTab13, renderTab14,
    renderTab15, renderTab16, renderTab17, renderTab18, renderTab19,
  ][id];
  if (fn && json) {
    const panel = document.querySelector(`[data-panel="${id}"] .panel-content`);
    if (panel) fn(json, panel);
  }
};

/* ══════════════════════════════════════════════════
   Tab 0: 总览 (M4.35)
═══════════════════════════════════════════════════ */
function renderTab0(json, el) {
  const arc = json.life_arc;
  const cf  = json.current_fortune_summary;
  const liunianDetail = (json.liunian_detail||[]);
  const thisYear = new Date().getFullYear();
  const thisLiunian = liunianDetail.find(l=>l.year===thisYear)||liunianDetail[0];

  const tierBadge = (tier) => {
    const cls = tier==='局高'?'high':tier==='局中'?'mid':'low';
    return `<span class="geju-tier-badge ${cls}">${esc(tier||'—')}</span>`;
  };

  const formatDayun = (d) => d?`${d.stem||''}${d.branch||''} 起于${d.start_age||'?'}岁`:'';
  const peakDayun = arc?.peak_periods?.[0] || '尚未推算';
  const cautionDayuns = arc?.caution_periods?.length ? arc.caution_periods.map(d=>`<span class="chip warn">${esc(d)}</span>`).join(' ') : '—';

  el.innerHTML = `
  <div class="life-arc-card" style="margin-bottom:16px">
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px">
      <div>
        <div style="font-size:11px;color:var(--accent-gold);font-weight:700;text-transform:uppercase;margin-bottom:4px">人生格局</div>
        <div class="life-arc-tier">${tierBadge(arc?.overall_tier||'—')}</div>
      </div>
      <div>
        <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:4px">命局总述</div>
        <div style="font-size:13px;color:var(--text)">${arc?.life_motto?esc(arc.life_motto):'—'}</div>
      </div>
    </div>
    <div class="life-arc-segments">
      ${arc?.early_fortune?`<div class="life-arc-seg"><div class="life-arc-seg-label">早年（0-30）</div><div class="life-arc-seg-text">${esc(arc.early_fortune)}</div></div>`:''}
      ${arc?.mid_fortune  ?`<div class="life-arc-seg"><div class="life-arc-seg-label">中年（30-60）</div><div class="life-arc-seg-text">${esc(arc.mid_fortune)}</div></div>`:''}
      ${arc?.late_fortune ?`<div class="life-arc-seg"><div class="life-arc-seg-label">晚年（60+）</div><div class="life-arc-seg-text">${esc(arc.late_fortune)}</div></div>`:''}
    </div>
    <div class="kv" style="margin-top:12px">
      <div class="k">顶峰大运</div><div>${esc(peakDayun)}</div>
      <div class="k">注意大运</div><div>${cautionDayuns||'—'}</div>
    </div>
  </div>

  <div class="current-fortune-card">
    <div style="font-size:11px;color:var(--accent);font-weight:700;text-transform:uppercase;margin-bottom:12px">当前运势卡</div>
    <div class="fortune-row">
      <div>
        <div class="fortune-item-label">当前大运</div>
        <div class="fortune-item-value">${cf?.dayun_gz ? esc(cf.dayun_gz) : (()=>{ const items=json.dayun?.items||[]; const now=new Date().getFullYear(); const cur=items.find(d=>d.start_year<=now&&(d.start_year||0)+10>now)||items.slice(-1)[0]; return cur?esc((cur.stem||'')+(cur.branch||'')):'—'; })()}</div>
        <div style="font-size:11px;color:var(--muted)">${cf?.dayun_remaining_years !== undefined ? `剩余约${cf.dayun_remaining_years}年` : ''}</div>
      </div>
      <div>
        <div class="fortune-item-label">当前流年（${thisYear}）</div>
        <div class="fortune-item-value">${thisLiunian ? esc((thisLiunian.ganzhi||thisLiunian.year||thisYear)+'') : esc(String(thisYear))}</div>
      </div>
    </div>
    ${thisLiunian?.domain_forecasts ? `
    <div class="fortune-4d-grid">
      ${['财运','事业','婚恋','健康'].map(k=>`
        <div class="fortune-4d-item">
          <div class="fortune-4d-label">${k}</div>
          <div class="fortune-4d-text">${esc(thisLiunian.domain_forecasts[k]||'暂无')}</div>
        </div>`).join('')}
    </div>` : ''}
  </div>

  <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
    <button onclick="switchTab(2)">查看命盘 →</button>
    <button onclick="switchTab(5)">查看摘要 →</button>
    <button onclick="switchTab(16)">查看大运 →</button>
    <button id="btn-history-drawer" class="no-print">历史对比</button>
  </div>
  <div style="margin-top:8px;font-size:11px;color:var(--muted)">⚠ 仅供参考，不作为任何决策依据。《三命通会》《渊海子平》《子平真诠》</div>
  `;
  // 重新绑定历史对比按钮
  $('btn-history-drawer')?.addEventListener('click',()=>{ $('historyDrawer')?.classList.toggle('open'); if(typeof renderHistoryDrawer==='function') renderHistoryDrawer(); });
}

/* ══════════════════════════════════════════════════
   Tab 1: 请求（表单已在 HTML 中，仅补充历史渲染）
═══════════════════════════════════════════════════ */
function renderTab1(json, el) {
  // Tab1 是静态表单，数据填充在 verify-core.js 中
  // 这里仅更新历史统计显示
  const level = json.validation?.level||'?';
  const el2 = el.querySelector('#reqResult');
  if (el2) el2.innerHTML = `<span class="pill ok">上次请求: ${esc(level)} · ${esc(json.request_id||'')}</span>`;
}

/* ══════════════════════════════════════════════════
   Tab 2: 命盘（四柱网格 M4.29 + 五行 + 日主 + 十神）
═══════════════════════════════════════════════════ */
function renderTab2(json, el) {
  const p = json.pillars_primary || {};
  const tg = json.ten_gods || {};
  const st = json.day_master_strength || {};
  const wx = json.wuxing_score || {};
  const yn = json.yongshen || {};
  const breakdown = json.wuxing_breakdown || {};

  const PILLAR_NAMES = {year:'年柱',month:'月柱',day:'日柱',hour:'时柱'};

  // 四柱网格（右→左：时日月年）
  const pillarsOrder = ['hour','day','month','year'];
  const pillarsCards = pillarsOrder.map(key => {
    const pillar = p[key]||{};
    const tenGodCode = tg[key];
    const isDay = key==='day';
    const tgCode = isDay ? 'ri_zhu' : tenGodCode;
    const ganWx = GAN_WUXING[pillar.stem]||'';
    const ganCssClass = GAN_CSS[pillar.stem]||'';
    return `
    <div class="pillar-card${isDay?' day-master':''}">
      ${isDay?'<div class="day-master-badge">日主</div>':''}
      <div class="pc-label">${PILLAR_NAMES[key]}</div>
      <div class="pc-stem ${ganCssClass}" data-tip="${esc(GAN_DESC[pillar.stem]||'')}"><span class="term">${esc(pillar.stem||'—')}</span></div>
      <div class="pc-branch">${esc(pillar.branch||'—')}</div>
      ${pillar.ganzhi?`<div class="pc-gz">${esc(pillar.ganzhi)}</div>`:''}
      <div class="pc-tg">${tgCode?`<span class="tengod-badge ${tenGodType(tgCode)}">${tenGodCN(tgCode)}</span>`:'—'}</div>
    </div>`;
  }).join('');

  // 五行条形图
  const wxTotal = (wx.wood||0)+(wx.fire||0)+(wx.earth||0)+(wx.metal||0)+(wx.water||0);
  const wxBars = [['wood','木'],[' fire','火'],['earth','土'],['metal','金'],['water','水']].map(([k,cn])=>{
    const raw = k.trim();
    const v = wx[raw]||0;
    const pct = wxTotal ? Math.round(v/wxTotal*100) : 0;
    return `<div class="wx-bar-row"><div class="wx-bar-label wx-${raw}">${cn}</div><div class="wx-bar-track"><div class="wx-bar-fill ${raw}" style="width:${pct}%">${pct}%</div></div><div style="font-size:11px;color:var(--muted);width:28px">${v.toFixed(1)}</div></div>`;
  }).join('');

  // 用神/忌神
  const favorList = (yn.favor||[]).map(f=>`<span class="chip favor-chip" data-tip="${f} 为用神，大运流年逢此五行则顺遂">${wxCN(f)}</span>`).join('');
  const avoidList = (yn.avoid||[]).map(f=>`<span class="chip avoid-chip" data-tip="${f} 为忌神，逢此五行宜小心">${wxCN(f)}</span>`).join('');

  el.innerHTML = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>四柱排盘（右→左 时日月年）</p>
    <div class="pillar-cards">${pillarsCards}</div>
    <div style="margin-top:10px;font-size:12px;color:var(--muted)">
      ★ 数据来源：《三命通会》《子平真诠》；算法：sxtwl节气历
    </div>
  </div>
  <div class="g2">
    <div class="card">
      <p class="card-title"><span class="dot"></span>五行得分</p>
      <div class="wx-bar-wrap">${wxBars}</div>
      <div id="wuxingRingContainer" style="margin-top:16px"></div>
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>日主强弱</p>
      <div class="kv">
        <div class="k">强弱分</div><div><strong>${st.score?.toFixed(2)||'—'}</strong></div>
        <div class="k">级别</div><div><span class="level-badge ${st.tier==='strong'||st.tier==='extremely_strong'?'ok':st.tier==='weak'||st.tier==='extremely_weak'?'bad':'warn'}">${esc(translateRationale(st.tier)||'—')}</span></div>
      </div>
      ${st.factors?.length?`<div style="margin-top:8px">${st.factors.map(f=>`<div style="display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid var(--line)"><span class="k">${esc(translateFactorName(f.name))}</span><span>${f.score?.toFixed(2)||0} ${f.reason?`<span class="hint">${esc(f.reason)}</span>`:''}</span></div>`).join('')}</div>`:''}
      <div style="margin-top:12px">
        <p class="card-title" style="margin-bottom:6px"><span class="dot" style="background:var(--ok)"></span>用神</p>
        <div class="row">${favorList||'<span class="hint">暂无</span>'}</div>
        <p class="card-title" style="margin-bottom:6px;margin-top:10px"><span class="dot" style="background:var(--bad)"></span>忌神</p>
        <div class="row">${avoidList||'<span class="hint">暂无</span>'}</div>
      </div>
      ${yn.rationale?`<div class="note" style="margin-top:10px"><div style="font-size:12px;color:var(--muted)">${esc(yn.rationale)}</div></div>`:''}
    </div>
  </div>
  `;
  // 渲染五行环形图 (M4.30)
  if (typeof renderWuxingRingChart === 'function') {
    renderWuxingRingChart(wx, $('wuxingRingContainer'));
  }

  // Task 4.20 [P69]: 地支关系★标记渲染
  const dzRels = json.dizhi_relations||[];
  const tgClashes = json.tiangan_clashes||[];
  if (dzRels.length || tgClashes.length) {
    const starMark = dzRels.length >= 3 ? '<span style="color:var(--accent-gold);font-size:16px;font-weight:900" title="地支多关系≥3条★">★</span> ' : '';
    const relChips = dzRels.map(r => {
      const brs = (r.branches||[]).join('');
      const status = r.status ? `<small class="hint">${esc(r.status)}</small>` : '';
      const elem = r.element ? `<small style="color:var(--muted)">${esc(r.element)}</small>` : '';
      const relType = r.type||'';
      const isHarm = relType.includes('冲') || relType.includes('刑') || relType.includes('害') || relType.includes('破');
      return `<span class="chip${isHarm?' bad':' ok'}" title="${esc(relType)}: ${esc(r.positions?.join('→')||'')}">
        ${esc(brs)} ${esc(relType)} ${status} ${elem}
      </span>`;
    }).join('');
    const clashChips = tgClashes.map(c => {
      const stems = (c.stems||[]).join('');
      const scope = c.scope ? `<small class="hint">${esc(c.scope)}</small>` : '';
      return `<span class="chip bad" title="${esc(c.type||'克')}: ${esc(c.positions?.join('→')||'')}">
        ${esc(stems)} 克 ${scope}
      </span>`;
    }).join('');
    const relCard = document.createElement('div');
    relCard.className = 'card';
    relCard.style.marginTop = '12px';
    relCard.innerHTML = `
      <p class="card-title"><span class="dot"></span>${starMark}地支关系（${dzRels.length}条）${tgClashes.length?` · 天干相克（${tgClashes.length}条）`:''}</p>
      ${relChips?`<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:${tgClashes.length?'10px':'0'}">${relChips}</div>`:''}
      ${clashChips?`<div style="display:flex;flex-wrap:wrap;gap:6px">${clashChips}</div>`:''}
    `;
    el.appendChild(relCard);
  }
}

/* ══════════════════════════════════════════════════
   Tab 3: 格局 (GejuModel)
═══════════════════════════════════════════════════ */
function renderTab3(json, el) {
  const g = json.geju;
  if (!g) { el.innerHTML = '<div class="hint" style="padding:16px">格局数据尚未计算，请先排盘。</div>'; return; }
  const tierMap = {high:'high',mid:'mid',低:'low'};
  const tierCls = g.tier==='高'?'high':g.tier==='中'?'mid':'low';
  // classic_ref 是字符串（格局古籍引用，"\n"分隔多条）
  const classicRefText = g.classic_ref || '';
  const classicRefHtml = classicRefText
    ? `<div class="card" style="margin-bottom:12px">
         <details>
           <summary style="cursor:pointer;font-size:12px;color:var(--accent-gold);font-weight:600;padding:4px 0">查看古籍引用</summary>
           <div style="margin-top:8px;font-size:12px;line-height:1.8;color:var(--text);font-family:var(--font-title);font-style:italic;white-space:pre-wrap">${esc(classicRefText)}</div>
         </details>
       </div>`
    : '';
  el.innerHTML = `
  <div class="card" style="margin-bottom:12px">
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div>
        <div style="font-size:11px;color:var(--muted);text-transform:uppercase;font-weight:700;margin-bottom:6px">格局名称</div>
        <div style="font-size:28px;font-weight:800;color:var(--text);font-family:var(--font-title)">
          ${esc(g.geju_name||g.name||'未知格局')}
          ${(typeof g.confidence==='number'&&g.confidence<0.5)?`<span class="tag-uncertain" title="置信度${Math.round((g.confidence||0)*100)}%，格局尚不确定">待定</span>`:''}
        </div>
        ${g.geju_level?`<div class="geju-tier-badge ${tierCls}" style="margin-top:8px;font-size:14px">${g.geju_level==='上格'?'▲ 上格':g.geju_level==='中格'?'◆ 中格':g.geju_level==='下格'?'▽ 下格':g.geju_level}</div>`:''}
        ${(typeof g.confidence==='number')?`<div style="font-size:11px;color:var(--muted);margin-top:4px">置信度 ${Math.round(g.confidence*100)}%</div>`:''}
      </div>
      ${g.score!==undefined?`<div style="text-align:center"><div style="font-size:11px;color:var(--muted);font-weight:700">格局评分</div><div style="font-size:36px;font-weight:800;color:var(--accent-gold)">${g.score.toFixed(0)}</div></div>`:''}
    </div>
  </div>
  ${g.description?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>格局释义</p><div style="font-size:13px;line-height:1.7;color:var(--text)">${esc(g.description)}</div></div>`:''}
  ${g.interpretation_text?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>深度解读</p><div style="font-size:13px;line-height:1.7;color:var(--text)">${esc(g.interpretation_text)}</div></div>`:''}
  ${classicRefHtml}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 4: 命宫 (PalaceModel)
═══════════════════════════════════════════════════ */
function renderTab4(json, el) {
  const palace = json.palace;
  if (!palace) { el.innerHTML = '<div class="hint" style="padding:16px">命宫数据尚未计算。</div>'; return; }
  // 十二宫位 6×2 网格
  const palaceNames = ['命','财帛','兄弟','田宅','男女','奴仆','迁移','疾厄','财帛','官禄','福德','父母'];
  const housesHtml = (palace.houses||[]).map((h,i)=>`
    <div style="border:1px solid var(--line);border-radius:10px;padding:10px;font-size:12px">
      <div style="font-weight:700;color:var(--accent);margin-bottom:4px">${palaceNames[i]||`宫${i+1}`}</div>
      <div style="font-size:14px;font-weight:700">${esc(h.branch||'—')}</div>
      <div style="color:var(--muted);font-size:11px;margin-top:3px">${esc(h.note||h.description||'')}</div>
    </div>`).join('');

  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>命宫</p>
      <div class="kv">
        <div class="k">命宫支</div><div style="font-size:20px;font-weight:800">${esc(palace.ming_gong_branch||palace.ming_gong||'—')}</div>
        <div class="k">身宫支</div><div style="font-size:20px;font-weight:800">${esc(palace.shen_gong_branch||palace.shen_gong||'—')}</div>
      </div>
      ${palace.note?`<div class="note" style="margin-top:10px"><div style="font-size:12px">${esc(palace.note)}</div></div>`:''}
    </div>
    ${json.shensha?.length?`
    <div class="card">
      <p class="card-title"><span class="dot"></span>神煞（全部${json.shensha.length}种·专业视图）</p>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        ${json.shensha.map(s=>`<span class="chip${s.is_beneficial?' ok':' bad'}" title="${esc(s.meaning||'')} [${s.priority||'B'}级]">
          ${s.is_star?'★ ':s.priority==='A'?'◎ ':''}${esc(s.name||'')}
          ${s.pillar?`<small class="hint">${esc(s.pillar)}</small>`:''}
          <small style="opacity:.5">${s.priority||'B'}</small>
        </span>`).join('')}
      </div>
    </div>`:'<div class="card"><p class="card-title"><span class="dot"></span>神煞</p><div class="hint">暂无神煞数据</div></div>'}
  </div>
  ${housesHtml?`<div class="card"><p class="card-title"><span class="dot"></span>十二宫位</p><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px">${housesHtml}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 5: 摘要（验证级别 + LifeArcModel + 6D雷达图）
═══════════════════════════════════════════════════ */
function renderTab5(json, el) {
  const v = json.validation||{};
  const arc = json.life_arc||{};
  const lvlCls = {L0:'ok',L1:'ok',L2:'warn',L3:'bad'}[v.level]||'warn';
  const warnings = (v.warnings||[]);
  const rt = json.rule_version_detail||{};
  el.innerHTML = `
  <div class="summary-grid">
    <div class="summary-card"><div class="summary-label">校验级别</div><div class="summary-value">${esc(v.level||'—')}</div><span class="summary-pill ${lvlCls}">${{L0:'无差异',L1:'时柱差异',L2:'月柱差异',L3:'多柱差异'}[v.level]||'—'}</span></div>
    <div class="summary-card"><div class="summary-label">告警数</div><div class="summary-value">${warnings.length}</div><span class="summary-pill ${warnings.length?'warn':'ok'}">${warnings.length?'有告警':'正常'}</span></div>
    <div class="summary-card"><div class="summary-label">格局</div><div class="summary-value">${esc(json.geju?.overall_tier||arc.overall_tier||'—')}</div></div>
    <div class="summary-card"><div class="summary-label">日主</div><div class="summary-value">${esc(translateRationale(json.day_master_strength?.tier)||'—')}</div></div>
  </div>
  <div id="scoringRadarContainer" style="margin:12px 0"></div>
  <div class="kv card" style="margin-bottom:12px">
    <div class="k">推算模式</div><div>${esc(json.mode_requested||'?')} → ${esc(json.mode_effective||'?')}</div>
    <div class="k">request_id</div><div><code>${esc(json.request_id||'—')}</code> <button onclick="copyText('${esc(json.request_id||'')}',this)" style="font-size:11px;padding:2px 8px">复制</button></div>
    <div class="k">API版本</div><div>${esc(json.api_version||'—')}</div>
    <div class="k">规则版本</div><div>${esc(json.rule_version||'—')}</div>
    <div class="k">太阳时偏移</div><div>${nn(json.solar_time_offset_minutes)} 分钟</div>
  </div>
  ${warnings.length?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>告警列表</p><div class="warnlist">${warnings.map(w=>`<div class="warnitem"><div class="wcode">${esc(w.code||w.type||'WARN')}</div><div class="wmsg">${esc(w.message||w.msg||'')}</div></div>`).join('')}</div></div>`:''}
  ${Object.keys(rt).length?`<div class="card"><p class="card-title"><span class="dot"></span>规则版本明细</p><div class="kv">${Object.entries(rt).map(([k,v])=>`<div class="k">${esc(k)}</div><div><code>${esc(v)}</code></div>`).join('')}</div></div>`:''}
  `;
  // 调用 6D 雷达图
  if (typeof renderScoringBars === 'function') {
    renderScoringBars(json, $('scoringRadarContainer'));
  }
}

/* ══════════════════════════════════════════════════
   Tab 6: 诊断（双引擎 + Raw JSON）
═══════════════════════════════════════════════════ */
function renderTab6(json, el) {
  const v = json.validation||{};
  const rf = v.risk_flags||{};
  const diffFields = v.diff_fields||[];
  const p1 = json.pillars_primary;
  const p2 = json.pillars_secondary;
  const renderPillars = (p, diff=[]) => {
    if (!p) return '<div class="hint">无数据</div>';
    return `<table class="pillar-table"><thead><tr><th>柱</th><th>天干</th><th>地支</th><th>干支</th></tr></thead><tbody>
      ${['year','month','day','hour'].map(k=>`<tr class="${diff.includes(k)?'diff-row':''}"><td>${{year:'年',month:'月',day:'日',hour:'时'}[k]}</td><td class="${GAN_CSS[p[k]?.stem]||''}">${esc(p[k]?.stem||'—')}</td><td>${esc(p[k]?.branch||'—')}</td><td>${esc(p[k]?.ganzhi||'—')}</td></tr>`).join('')}
    </tbody></table>`;
  };
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card"><p class="card-title"><span class="dot"></span>主引擎四柱</p>${renderPillars(p1,diffFields)}</div>
    <div class="card"><p class="card-title"><span class="dot" style="background:var(--muted)"></span>校验引擎四柱</p>${renderPillars(p2,diffFields)}</div>
  </div>
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>边界风险</p>
      <div class="kv">
        <div class="k">时辰边界</div><div><span class="${rf.near_shichen_boundary?'tag bad':'tag ok'}">${rf.near_shichen_boundary?'⚠ 临界':'✓ 安全'}</span> ${nn(rf.minutes_to_shichen_boundary)}分钟</div>
        <div class="k">节气边界</div><div><span class="${rf.near_jieqi_boundary?'tag bad':'tag ok'}">${rf.near_jieqi_boundary?'⚠ 临界':'✓ 安全'}</span> ${nn(rf.minutes_to_jieqi_boundary)}分钟</div>
        <div class="k">节气数据</div><div>${rf.jieqi_boundary_status==='ok'?'<span class="tag ok">可用</span>':'<span class="tag warn">不可用</span>'}</div>
      </div>
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>差异字段</p>
      <div class="row">${diffFields.length?diffFields.map(f=>`<span class="chip warn">${{year:'年柱',month:'月柱',day:'日柱',hour:'时柱'}[f]||f}</span>`).join(''):'<span class="chip ok">无差异</span>'}</div>
    </div>
  </div>
  <details style="margin-top:8px">
    <summary>Raw JSON（调试用）</summary>
    <div class="row" style="margin:8px 0;gap:6px">
      <button onclick="copyText(document.getElementById('rawPre').textContent,this)">复制 JSON</button>
    </div>
    <pre id="rawPre" style="margin-top:8px">${esc(JSON.stringify(json,null,2))}</pre>
  </details>
  `;
}

/* ══════════════════════════════════════════════════
   Tab 7: 财运 (WealthAnalysisModel, M4.06重做)
═══════════════════════════════════════════════════ */
function renderTab7(json, el) {
  const w  = json.wealth_analysis||{};
  const wo = json.wealth||{};
  const makeBar = (score, label) => `
    <div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px">
      <div style="width:60px;color:var(--muted)">${label}</div>
      <div style="flex:1;height:12px;background:#f1f5f9;border-radius:6px;overflow:hidden">
        <div style="width:${clamp(score||0,0,100)}%;height:100%;background:linear-gradient(90deg,var(--accent-gold),#fbbf24);border-radius:6px;transition:width .5s"></div>
      </div>
      <div style="width:32px;text-align:right;font-weight:700">${(score||0).toFixed(0)}</div>
    </div>`;
  const clamp = (v,a,b)=>Math.min(Math.max(v,a),b);

  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>财运评分</p>
      ${makeBar(w.wealth_score, '财运')}
      ${w.fact_data?`<div style="margin-top:8px;font-size:12px;color:var(--muted)"><strong>实证层：</strong>${esc(w.fact_data.wealth_tier||'')} ${esc(w.fact_data.annual_range||'')}</div>`:''}
      ${w.inference_tags?.length?`<div style="font-size:12px;color:var(--muted)"><strong>推断层：</strong>${w.inference_tags.map(t=>esc(t)).join('、')}</div>`:''}
      ${w.interpretation_text?`<div style="font-size:12px;color:var(--text)"><strong>解读层：</strong>${esc(w.interpretation_text)}</div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>财富区间估算</p>
      <div class="kv">
        <div class="k">财富年估值</div><div style="font-size:18px;font-weight:800;color:var(--accent-gold)">${esc(w.annual_range||wo.wealth_range?.label||'—')}</div>
        <div class="k">财运评级</div><div>${esc(w.wealth_tier||'—')}</div>
        <div class="k">财运评分</div><div>${w.wealth_score!==undefined?w.wealth_score:'—'}</div>
      </div>
      ${wo.risk_hint?`<div class="note" style="margin-top:8px"><div style="font-size:12px">${esc(wo.risk_hint)}</div></div>`:''}
    </div>
  </div>
  ${(w.industries||wo.industry_tags||[]).length?`
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>适合行业</p>
    <div class="row">${[...(w.industries||[]),(wo.industry_tags||[])].flat().map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div>
  </div>`:''}
  ${w.strategy?`
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运策略</p>
    <div style="font-size:13px;line-height:1.7">${esc(w.strategy)}</div>
  </div>`:''}
  ${w.dayun_forecast?.length?`
  <div class="card">
    <p class="card-title"><span class="dot"></span>大运财运周期</p>
    <div style="display:grid;gap:8px">${w.dayun_forecast.map(c=>`
      <div style="border:1px solid var(--line);border-radius:10px;padding:10px;font-size:12px">
        <div style="font-weight:700">${esc(c.ganzhi||'')} — ${esc(c.trend||'')}</div>
      </div>`).join('')}
    </div>
  </div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 8: 事业 (CareerAnalysisModel, M4.07)
═══════════════════════════════════════════════════ */
function renderTab8(json, el) {
  const c = json.career||{};
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>职业方向</p>
      <div class="row" style="flex-wrap:wrap">${(c.career_directions||[]).map(d=>`<span class="chip">${esc(d)}</span>`).join('')||'<span class="hint">暂无</span>'}</div>
      ${c.interpretation_text?`<div style="margin-top:10px;font-size:13px;line-height:1.6">${esc(c.interpretation_text)}</div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>事业评分</p>
      <div class="kv">
        <div class="k">事业分</div><div style="font-size:22px;font-weight:800">${c.career_score?.toFixed(1)||'—'}</div>
        <div class="k">最佳时机</div><div>${esc(c.optimal_move_timing||'—')}</div>
      </div>
    </div>
  </div>
  ${c.development_advice?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>发展建议</p><div style="font-size:13px;line-height:1.7">${esc(c.development_advice)}</div></div>`:''}
  ${c.suitable_industries?.length?`<div class="card"><p class="card-title"><span class="dot"></span>适合行业</p><div class="row">${c.suitable_industries.map(i=>`<span class="chip">${esc(i)}</span>`).join('')}</div></div>`:''}
  ${c.inference_tags?.length?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>分析标签</p><div class="row">${c.inference_tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 9: 姻缘 (MarriageAnalysisModel, M4.06重做含桃花)
═══════════════════════════════════════════════════ */
function renderTab9(json, el) {
  const ma = json.marriage_analysis||{};
  const mo = json.marriage||{};
  const so = json.social||{};

  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>婚姻分析</p>
      ${ma.partner_profile?`<div style="font-size:13px;line-height:1.7;margin-bottom:8px">${esc(ma.partner_profile)}</div>`:''}
      <div class="kv">
        <div class="k">婚姻分</div><div style="font-size:18px;font-weight:800">${ma.marriage_score?.toFixed(1)||'—'}</div>
        <div class="k">婚期窗口</div><div>${(mo.love_window||[]).map(w=>`${w.age_from||'?'}–${w.age_to||'?'}岁`).join('，')||'—'}</div>
      </div>
      ${ma.interpretation_text?`<div class="note" style="margin-top:10px"><div style="font-size:12px">${esc(ma.interpretation_text)}</div></div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>桃花 / 社交</p>
      <div class="kv">
        <div class="k">桃花星</div><div>${so.taohua_hit?'<span class="tag ok">命中桃花</span>':'<span class="tag">无桃花</span>'}</div>
        <div class="k">社交倾向</div><div>${esc(so.social_hint||ma.social_tendency||'—')}</div>
      </div>
      ${so.taohua_year_hit?.length?`<div style="margin-top:8px"><div class="card-title" style="margin-bottom:4px"><span class="dot"></span>桃花年</div><div class="row">${so.taohua_year_hit.map(y=>`<span class="chip">${y}</span>`).join('')}</div></div>`:''}
    </div>
  </div>
  ${ma.child_hint?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>子女缘</p><div class="kv"><div class="k">头胎</div><div>${esc(ma.child_hint?.first||mo.child_hint?.first||'—')}</div><div class="k">次胎</div><div>${esc(ma.child_hint?.second||mo.child_hint?.second||'—')}</div></div></div>`:''}
  ${ma.compatibility_factors?.length?`<div class="card"><p class="card-title"><span class="dot"></span>合婚要素</p><ul class="panel-list">${ma.compatibility_factors.map(f=>`<li>${esc(f)}</li>`).join('')}</ul></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 10: 健康 (HealthAnalysisModel, M4.07)
═══════════════════════════════════════════════════ */
function renderTab10(json, el) {
  const h = json.health||{};
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>健康风险</p>
      <div class="kv">
        <div class="k">健康分</div><div style="font-size:18px;font-weight:800">${h.health_score?.toFixed(1)||'—'}</div>
      </div>
      ${h.risk_areas?.length?`<div style="margin-top:8px"><div class="row">${h.risk_areas.map(r=>`<span class="chip warn">${esc(r)}</span>`).join('')}</div></div>`:''}
      ${h.wuxing_organ_map?`<div class="kv" style="margin-top:8px">${Object.entries(h.wuxing_organ_map).map(([wxKey,organs])=>`<div class="k" style="color:var(--text)">${wxCN(wxKey)}</div><div>${Array.isArray(organs)?esc(organs.join('、')):esc(organs||'')}</div>`).join('')}</div>`:''}
      ${h.interpretation_text?`<div class="note" style="margin-top:10px"><div style="font-size:12px;line-height:1.6">${esc(h.interpretation_text)}</div></div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>养生建议</p>
      ${h.diet_advice?.length?`<div style="margin-bottom:8px"><strong style="font-size:12px;color:var(--muted)">饮食：</strong><ul class="panel-list">${h.diet_advice.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
      ${h.exercise_advice?.length?`<div style="margin-bottom:8px"><strong style="font-size:12px;color:var(--muted)">运动：</strong><ul class="panel-list">${h.exercise_advice.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
      ${h.lifestyle_advice?.length?`<div><strong style="font-size:12px;color:var(--muted)">作息：</strong><ul class="panel-list">${h.lifestyle_advice.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
    </div>
  </div>
  ${h.three_layer?.fact?`<div class="card"><p class="card-title"><span class="dot"></span>三层模型</p><div class="kv"><div class="k">实证层</div><div>${esc(h.three_layer.fact)}</div><div class="k">推断层</div><div>${esc(h.three_layer.inference||'—')}</div><div class="k">解读层</div><div>${esc(h.three_layer.interpretation||'—')}</div></div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 11: 人际 (RelationshipAnalysisModel, M4.07)
═══════════════════════════════════════════════════ */
function renderTab11(json, el) {
  const r = json.relationship||{};
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>六亲关系</p>
      ${r.interpretation_text?`<div style="font-size:13px;line-height:1.7">${esc(r.interpretation_text)}</div>`:(r.liu_qin?`<div style="font-size:12px;line-height:1.6">${Object.entries(r.liu_qin).map(([k,v])=>`<div><strong>${esc(k)}：</strong>${esc(v)}</div>`).join('')}</div>`:'')}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>贵人 & 小人</p>
      ${r.noble_people?.length?`<div style="font-size:12px;color:var(--ok);margin-bottom:4px">贵人：${r.noble_people.map(p=>esc(p)).join('、')}</div>`:''}
      ${r.petty_people?.length?`<div style="font-size:12px;color:var(--bad);margin-bottom:4px">小人：${r.petty_people.map(p=>esc(p)).join('、')}</div>`:''}
      ${r.social_strategy?`<div style="font-size:12px;line-height:1.6">${esc(r.social_strategy)}</div>`:''}
    </div>
  </div>
  `;
}

/* ══════════════════════════════════════════════════
   Tab 12: 性格 (PersonalityModel, M4.07)
═══════════════════════════════════════════════════ */
function renderTab12(json, el) {
  const p = json.personality||{};
  el.innerHTML = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>性格特征（日主: ${esc(json.pillars_primary?.day?.stem||'—')}）</p>
    ${p.inference_tags?.length?`<div class="row" style="margin-bottom:10px">${p.inference_tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div>`:''}
    ${p.interpretation_text||p.day_stem_trait?`<div style="font-size:13px;line-height:1.7">${esc(p.interpretation_text||p.day_stem_trait)}</div>`:`<div style="font-size:12px;color:var(--muted);padding:8px 0">${esc((p.day_stem||'')||'待排盘')}</div>`}
  </div>
  <div class="g2">
    ${p.advantages?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--ok)"></span>优势</p><ul class="panel-list">${p.advantages.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></div>`:''}
    ${p.disadvantages?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>劣势</p><ul class="panel-list">${p.disadvantages.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></div>`:''}
  </div>
  ${p.growth_advice?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>成长建议</p><div style="font-size:13px;line-height:1.7">${esc(p.growth_advice)}</div></div>`:''}
  ${p.day_stem_trait?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>日主特质</p><div style="font-size:13px;line-height:1.7">${esc(p.day_stem_trait)} ${p.strength_modifier?esc('（'+p.strength_modifier+'）'):''}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 13: 风水 (FengshuiModel, M4.05)
═══════════════════════════════════════════════════ */
function renderTab13(json, el) {
  const f = json.fengshui||{};
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>吉利方位</p>
      <div class="row" style="flex-wrap:wrap">${(f.auspicious_directions||[]).map(d=>`<span class="chip ok">↗ ${esc(d)}</span>`).join('')||'<span class="hint">暂无</span>'}</div>
      ${f.auspicious_colors?.length?`<div style="margin-top:10px"><strong style="font-size:12px;color:var(--muted)">吉利颜色：</strong><div class="row" style="flex-wrap:wrap;margin-top:4px">${f.auspicious_colors.map(c=>`<span class="chip">${esc(c)}</span>`).join('')}</div></div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>布局建议</p>
      ${f.arrangement_tips?.length?`<ul class="panel-list">${f.arrangement_tips.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:'<div class="hint">暂无</div>'}
    </div>
  </div>
  ${f.plants?.length||f.pets_advice?`<div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>植物 & 注意事项</p>
    ${f.plants?.length?`<div class="row" style="margin-bottom:8px">${f.plants.map(p=>`<span class="chip">${esc(p)}</span>`).join('')}</div>`:''}
    ${f.avoidance_tips?.length?`<ul class="panel-list">${f.avoidance_tips.map(t=>`<li style="color:var(--bad)">${esc(t)}</li>`).join('')}</ul>`:''}
  </div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 14: 饰品 (JewelryModel, M4.05)
═══════════════════════════════════════════════════ */
function renderTab14(json, el) {
  const j = json.jewelry||{};
  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>首选饰品</p>
      <div class="row" style="flex-wrap:wrap">${(j.primary_items||[]).map(i=>`<span class="chip ok">💎 ${esc(i)}</span>`).join('')||'<span class="hint">暂无</span>'}</div>
      ${j.primary_reason?`<div class="note" style="margin-top:8px"><div style="font-size:12px">${esc(j.primary_reason)}</div></div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>次选饰品</p>
      <div class="row" style="flex-wrap:wrap">${(j.secondary_items||[]).map(i=>`<span class="chip">${esc(i)}</span>`).join('')||'<span class="hint">暂无</span>'}</div>
    </div>
  </div>
  ${j.combinations?.length?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>组合搭配</p><ul class="panel-list">${j.combinations.map(c=>`<li>${esc(c)}</li>`).join('')}</ul></div>`:''}
  ${j.taboo_items?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>禁忌饰品</p><div class="row">${j.taboo_items.map(t=>`<span class="chip bad">✕ ${esc(t)}</span>`).join('')}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 15: 开运 (LuckyModel + LifestyleModel, M4.05)
═══════════════════════════════════════════════════ */
function renderTab15(json, el) {
  const lk = json.lucky||{};
  const ls = json.lifestyle||{};
  el.innerHTML = `
  <div class="g3" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>幸运数字</p>
      <div class="row">${(lk.lucky_numbers||[]).map(n=>`<span class="chip" style="font-size:16px;font-weight:800">${n}</span>`).join('')||'—'}</div>
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>幸运颜色</p>
      <div class="row">${(lk.lucky_colors||[]).map(c=>`<span class="chip" style="background:var(--input)">${esc(c)}</span>`).join('')||'—'}</div>
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>吉利方位</p>
      <div class="row">${(lk.lucky_directions||[]).map(d=>`<span class="chip">↗ ${esc(d)}</span>`).join('')||'—'}</div>
    </div>
  </div>
  <div class="g2">
    ${ls.travel_direction?`<div class="card"><p class="card-title"><span class="dot"></span>出行建议</p><div style="font-size:13px">${esc(ls.travel_direction)}</div></div>`:''}
    ${ls.sleep_advice?`<div class="card"><p class="card-title"><span class="dot"></span>作息建议</p><div style="font-size:13px">${esc(ls.sleep_advice)}</div>${ls.best_times?`<div style="font-size:11px;color:var(--muted);margin-top:4px">最佳时段：${esc(ls.best_times)}</div>`:''}</div>`:''}
  </div>
  `;
}

/* ══════════════════════════════════════════════════
   Tab 16: 大运（可展开叙事 + 真实走势图 M4.08）
═══════════════════════════════════════════════════ */
function renderTab16(json, el) {
  const dy = json.dayun||{};
  const items = dy.items||[];
  const thisYear = new Date().getFullYear();
  const isCurrent = item => item.start_year <= thisYear && (item.start_year||0)+10 > thisYear;
  // M4.18: 单库模式提示
  const isSingleMode = json.mode_effective === 'single' || json.mode_requested === 'single';
  const singleModeNotice = isSingleMode
    ? `<div class="card" style="margin-bottom:12px;border-left:3px solid var(--warn,#e6a817)">
        <div style="display:flex;align-items:center;gap:8px;color:var(--warn,#b87a0a)">
          <span style="font-size:16px">⚠️</span>
          <span style="font-weight:600">单库模式 — 无节气数据</span>
        </div>
        <div style="font-size:12px;color:var(--muted);margin-top:6px">当前使用单节气库推算，大运起止年份精度受限，仅供学术参考。</div>
       </div>` : '';

  el.innerHTML = singleModeNotice + `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>大运推算方法</p>
    <div class="kv">
      <div class="k">方法</div><div>${esc(dy.method||'—')}</div>
      <div class="k">边界</div><div>${esc(dy.boundary||'—')}</div>
    </div>
  </div>
  <div id="dayunChartContainer" style="margin-bottom:16px"></div>
  <div class="dayun-table-wrapper" style="overflow-x:auto">
    <table class="dayun-table">
      <thead><tr><th>干支</th><th>起年</th><th>起岁</th><th>十神</th><th>财运</th><th>健康</th><th>感情</th><th>叙事/古籍</th></tr></thead>
      <tbody>
        ${items.map(d=>`
          <tr class="${isCurrent(d)?'dayun-current':''}">
            <td><div class="dayun-gz ${GAN_CSS[d.stem]||''}">${esc(d.stem||'')}${esc(d.branch||'')}</div></td>
            <td>${d.start_year||'—'}</td>
            <td>${d.start_age!==undefined?d.start_age+'岁':'—'}</td>
            <td>${d.ten_god?`<span class="tengod-badge ${tenGodType(d.ten_god)}">${tenGodCN(d.ten_god)}</span>`:'—'}</td>
            <td>${d.wealth_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(d.wealth_hint)}">${esc(d.wealth_hint)}</div>`:'—'}</td>
            <td>${d.health_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(d.health_hint)}">${esc(d.health_hint)}</div>`:'—'}</td>
            <td>${d.love_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(d.love_hint)}">${esc(d.love_hint)}</div>`:'—'}</td>
            <td>
              ${d.narrative_text?`<details><summary style="cursor:pointer;font-size:11px;color:var(--accent)">查看叙事</summary><div style="font-size:12px;line-height:1.6;padding:8px;max-width:300px;white-space:pre-wrap">${esc(d.narrative_text)}</div></details>`:''}
              ${(d.refs&&d.refs.length)?`<details style="margin-top:4px"><summary style="cursor:pointer;font-size:11px;color:var(--accent-gold)">查看古籍引用</summary><div style="font-size:11px;line-height:1.7;padding:6px 8px;max-width:320px;font-style:italic;font-family:var(--font-title)">${d.refs.map(r=>`<div style="margin-bottom:4px"><span style="color:var(--accent-gold)">【${esc(r.source||'')}】</span>${esc(r.text||'')}</div>`).join('')}</div></details>`:''}
              ${!d.narrative_text&&!(d.refs&&d.refs.length)?'—':''}
            </td>
          </tr>`).join('')||'<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无数据</td></tr>'}
      </tbody>
    </table>
  </div>
  `;
  // 渲染大运走势图
  if (typeof renderDayunTrendChart === 'function') {
    renderDayunTrendChart(items, $('dayunChartContainer'));
  }
}

/* ══════════════════════════════════════════════════
   Tab 17: 流年（时间轴 + 犯太岁❗ + 四维, M4.09）
═══════════════════════════════════════════════════ */
function renderTab17(json, el) {
  const liunian = json.liunian_detail||[];
  if (!liunian.length) { el.innerHTML='<div class="hint" style="padding:16px">流年数据尚未计算。</div>'; return; }

  const thisYear = new Date().getFullYear();
  el.innerHTML = `
  <div class="liunian-timeline">
    ${liunian.map(item => {
      const isCurrentYear = item.year === thisYear;
      const isFanTaisui = (item.tai_sui_relations?.length > 0) || item.fan_taisui || item.clash_type || false;
      const taisuiLabel = item.tai_sui_relations?.[0] || '';
      return `
      <div class="liunian-item${isFanTaisui?' fan-taisui':''}${isCurrentYear?' dayun-current':''}">
        <div>
          <div class="liunian-year">${item.year||'—'}</div>
          <div class="liunian-gz">${esc(item.ganzhi||(item.stem||'')+(item.branch||''))}</div>
          ${item.ten_god?`<div style="margin-top:4px"><span class="tengod-badge ${tenGodType(item.ten_god_code||item.ten_god)}">${tenGodCN(item.ten_god_code||item.ten_god)}</span></div>`:''}
          ${taisuiLabel?`<div style="font-size:10px;color:var(--bad);margin-top:3px">⚡ ${esc(taisuiLabel)}</div>`:''}
          ${item.clash_note?`<div style="font-size:10px;color:var(--bad);margin-top:3px">${esc(item.clash_note)}</div>`:''}
        </div>
        <div>
          ${item.annual_score!==undefined?`<div style="margin-bottom:8px"><div style="font-size:11px;color:var(--muted);font-weight:700">年运评分</div><div style="font-size:18px;font-weight:800;color:${item.annual_score>=70?'var(--ok)':item.annual_score>=50?'var(--warn)':'var(--bad)'}">${item.annual_score}</div></div>`:''}
          ${item.domain_forecasts?`
          <div class="liunian-domains">
            ${['财运','事业','婚恋','健康'].map(k=>`
              <div class="liunian-domain">
                <div class="ld-label">${k}</div>
                <div class="ld-text">${esc(item.domain_forecasts[k]||'—')}</div>
              </div>`).join('')}
          </div>`:''}
          ${item.monthly_highlights?.length?`<details style="margin-top:8px"><summary style="font-size:11px;color:var(--accent)">月份提示</summary><ul class="panel-list" style="font-size:11px">${item.monthly_highlights.map(m=>`<li>${esc(m)}</li>`).join('')}</ul></details>`:''}
        </div>
      </div>`;
    }).join('')}
  </div>`;
}

/* ══════════════════════════════════════════════════
   Tab 18: 月运（12月网格 + 吉凶色标 M4.10）
═══════════════════════════════════════════════════ */
function renderTab18(json, el) {
  const mf = json.monthly_fortune||[];
  if (!mf.length) { el.innerHTML='<div class="hint" style="padding:16px">月运数据尚未计算。</div>'; return; }
  const MONTHS = ['一','二','三','四','五','六','七','八','九','十','十一','十二'];
  el.innerHTML = `
  <div class="monthly-grid">
    ${mf.map((m,i)=>{
      const cls = m.is_favorable===true?'good':m.is_favorable===false?'bad':'neutral';
      const colorHint = m.color_hint;
      return `
      <div class="month-item ${cls}" style="${colorHint?`border-bottom:3px solid ${esc(colorHint)}`:''}">
        <div class="month-num">${MONTHS[i]||i+1}月</div>
        <div class="month-gz">${esc(m.ganzhi||m.stem||'')}</div>
        <div class="month-hint">${esc(m.hint||m.note||'—')}</div>
      </div>`;
    }).join('')}
  </div>
  <div class="row" style="margin-top:12px;gap:12px;font-size:11px">
    <span style="display:flex;align-items:center;gap:4px"><span style="width:12px;height:12px;border-radius:50%;background:#86efac;display:inline-block"></span>吉月</span>
    <span style="display:flex;align-items:center;gap:4px"><span style="width:12px;height:12px;border-radius:50%;background:#fca5a5;display:inline-block"></span>凶月</span>
    <span style="display:flex;align-items:center;gap:4px"><span style="width:12px;height:12px;border-radius:50%;background:var(--line);display:inline-block"></span>一般</span>
  </div>`;
}

/* ══════════════════════════════════════════════════
   Tab 19: 案例（搜索 + 关系匹配，重用原有 casesHub）
═══════════════════════════════════════════════════ */
function renderTab19(json, el) {
  // 案例面板渲染：注入 iframe
  if (el.querySelector('iframe')) return; // 已注入
  el.innerHTML = `
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <input id="caseSearchBox19" type="text" placeholder="🔍 搜索案例" style="max-width:220px" />
      <button id="btnReloadCases19">刷新</button>
      <a class="pill" href="/static/cases.html?standalone=1" target="_blank" rel="noopener">新窗口</a>
    </div>
  </div>
  <iframe id="casesHubFrame19" src="/static/cases.html?embedded=1" title="案例速览" style="width:100%;min-height:680px;border:1px solid var(--line);border-radius:12px;background:#fff"></iframe>
  `;
  el.querySelector('#btnReloadCases19')?.addEventListener('click',()=>{ const f=el.querySelector('iframe'); if(f) f.src='/static/cases.html?embedded=1'; });
  el.querySelector('#caseSearchBox19')?.addEventListener('input', debounce(e=>{
    const f=el.querySelector('iframe'); if(f?.contentWindow) f.contentWindow.postMessage({type:'search',keyword:e.target.value},'*');
  },300));
}

/* ── 辅助: levelBadge ─────────────────────────── */
window.levelBadge = function(level) {
  const cls = {L0:'ok',L1:'ok',L2:'warn',L3:'bad'}[level]||'warn';
  return `<span class="level-badge ${cls}">${esc(level||'—')}</span>`;
};

/* ── 辅助: 历史抽屉渲染 (M4.36) ──────────────── */
window.renderHistoryDrawer = function() {
  const drawer = $('historyDrawer'); if(!drawer) return;
  const profiles = window.__BAZI_STATE?.profiles || [];
  const content  = drawer.querySelector('.history-drawer-content');
  if (!content) return;
  if (!profiles.length) { content.innerHTML='<div class="hint" style="padding:8px">暂无历史命盘</div>'; return; }
  content.innerHTML = profiles.map((p,i)=>`
    <div class="profile-item" onclick="loadHistoryProfile(${i})">
      <div style="font-size:12px;font-weight:700">${esc(p.payload?.dt?.slice(0,10)||'未知时间')}</div>
      <div style="font-size:11px;color:var(--muted)">${esc(p.json?.validation?.level||'—')} | ${esc(p.payload?.lon||'')}°E</div>
    </div>`).join('');
};

window.loadHistoryProfile = function(i) {
  const profiles = window.__BAZI_STATE?.profiles||[];
  const p = profiles[i]; if(!p) return;
  window.__BAZI_STATE.result = p.json;
  window.__BAZI_STATE.tabLoaded.clear();
  loadPanel(0); // 重新渲染总览
  $('historyDrawer')?.classList.add('open');
};

// debounce (局部可用)
function debounce(fn, ms) { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; }

})();
