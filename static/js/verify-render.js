/**
 * verify-render.js  v4.0.20260305Q
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
// 以下与 verify-core.js 保持一致（两个 IIFE 作用域隔离，各自维护副本）
const cleanText = s => String(s||'').split('">').map(p=>p.trim()).filter(Boolean).join(' · ');
const txt       = s => esc(cleanText(s));
const renderPara= s => { const segs=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return segs.length?segs.map(seg=>`<p style="margin:3px 0;line-height:1.65">${esc(seg)}</p>`).join(''):''; };
const chipName  = s => { const parts=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return parts.length?esc(parts[parts.length-1]):esc(s||''); };
const chipTitle = s => { const parts=String(s||'').split('">').map(p=>p.trim()).filter(Boolean); return parts.length>1?esc(parts.slice(0,-1).join(' · ')):esc(s||''); };

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

  /* ── Hero Summary Card（命局速览）──*/
  const dayStem   = json.pillars_primary?.day?.stem || '—';
  const dayDesc   = (window.GAN_DESC||{})[dayStem] || '';
  const gejuName  = json.geju?.geju_name || json.geju?.name || '—';
  const gejuLevel = json.geju?.geju_level || '';
  const gejuConf  = typeof json.geju?.confidence === 'number' ? Math.round(json.geju.confidence*100) : null;
  const yongshenFavor = (json.yongshen?.favor||[]).map(f=>typeof wxCN==='function'?wxCN(f):f).join('\u00b7') || '—';
  const yearScore = thisLiunian?.annual_score;
  const scoreColor = yearScore>=70 ? '#22c55e' : yearScore>=50 ? '#f8c13c' : '#ef4444';
  const top3 = cf?.top3_actions || [];
  const heroHtml = `<div class="hero-summary">
    <div style="flex:1;min-width:180px">
      <div class="hs-label">命局速览</div>
      <div class="hs-day">
        <span class="hs-day-stem">${esc(dayStem)}</span>
        ${dayDesc ? `<span class="hs-day-desc">${esc(dayDesc)}</span>` : ''}
      </div>
      <div class="hs-geju">${esc(gejuName)}${gejuLevel ? ` \u00b7 ${esc(gejuLevel)}` : ''}${gejuConf!==null ? `<span class="hs-conf">${gejuConf}%</span>` : ''}</div>
      <div class="hs-yongshen">用神：${esc(yongshenFavor)}</div>
      ${(arc?.inference_tags||[]).length ? `<div class="hero-action-pills">${arc.inference_tags.slice(0,5).map(a=>`<span class="hero-action-pill">${esc(a)}</span>`).join('')}</div>` : ''}
      ${top3.length ? `<div class="hero-action-pills">${top3.slice(0,3).map(a=>{const s=txt(a);const short=s.length>28?s.slice(0,27)+'\u2026':s;return `<span class="hero-action-pill" title="${esc(s)}">\u2726 ${esc(short)}</span>`;}).join('')}</div>` : ''}
    </div>
    ${yearScore !== undefined ? `<div class="hero-score">
      <div class="hs-score-num" style="color:${scoreColor}">${yearScore}</div>
      <div class="hs-score-label">${thisYear}年运势</div>
    </div>` : ''}
  </div>`;

  const tierBadge = (tier) => {
    const cls = tier==='局高'?'high':tier==='局中'?'mid':'low';
    return `<span class="geju-tier-badge ${cls}">${esc(tier||'—')}</span>`;
  };

  const formatDayun = (d) => d?`${d.stem||''}${d.branch||''} 起于${d.start_age||'?'}岁`:'';
  const peakDayun = arc?.peak_periods?.[0] || '尚未推算';
  const cautionDayuns = arc?.caution_periods?.length ? arc.caution_periods.map(d=>`<span class="chip warn">${esc(d)}</span>`).join(' ') : '—';

  // 当前大运详情
  const _dyItems = json.dayun?.items || [];
  const curDayunItem = _dyItems.find(d=>d.start_year<=thisYear&&(d.start_year||0)+10>thisYear) || _dyItems.slice(-1)[0] || null;

  el.innerHTML = heroHtml + `
  <div class="life-arc-card" style="margin-bottom:16px">
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px">
      <div>
        <div style="font-size:11px;color:var(--accent-gold);font-weight:700;text-transform:uppercase;margin-bottom:4px">人生格局</div>
        <div class="life-arc-tier">${tierBadge(arc?.overall_tier||'—')}</div>
      </div>
      <div>
        <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:4px">命局总述</div>
        <div style="font-size:13px;color:var(--text)">${arc?.life_motto?txt(arc.life_motto):'—'}</div>
      </div>
    </div>
    <div class="life-arc-segments">
      ${arc?.early_fortune?`<div class="life-arc-seg"><div class="life-arc-seg-label">早年（0-30）</div><div class="life-arc-seg-text">${renderPara(arc.early_fortune)}</div></div>`:''}
      ${arc?.mid_fortune  ?`<div class="life-arc-seg"><div class="life-arc-seg-label">中年（30-60）</div><div class="life-arc-seg-text">${renderPara(arc.mid_fortune)}</div></div>`:''}
      ${arc?.late_fortune ?`<div class="life-arc-seg"><div class="life-arc-seg-label">晚年（60+）</div><div class="life-arc-seg-text">${renderPara(arc.late_fortune)}</div></div>`:''}
    </div>
    <div class="kv" style="margin-top:12px">
      <div class="k">顶峰大运</div><div>${esc(peakDayun)}</div>
      <div class="k">注意大运</div><div>${cautionDayuns||'—'}</div>
    </div>
    ${arc?.interpretation_text ? `<div class="note" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px"><div style="font-size:13px;line-height:1.75;color:var(--text)">${renderPara(arc.interpretation_text)}</div></div>` : ''}
  </div>

  <div class="current-fortune-card">
    <div style="font-size:11px;color:var(--accent);font-weight:700;text-transform:uppercase;margin-bottom:12px">当前运势卡</div>
    <div class="fortune-row">
      <div>
        <div class="fortune-item-label">当前大运</div>
        <div class="fortune-item-value">${cf?.current_dayun ? esc(cf.current_dayun) : (()=>{ const items=json.dayun?.items||[]; const now=new Date().getFullYear(); const cur=items.find(d=>d.start_year<=now&&(d.start_year||0)+10>now)||items.slice(-1)[0]; return cur?esc((cur.stem||'')+(cur.branch||'')):'—'; })()}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:2px;display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          ${cf?.dayun_years_remaining !== undefined ? `<span>剩余约${cf.dayun_years_remaining}年</span>` : ''}
          ${curDayunItem?.ten_god ? `<span class="tengod-badge ${typeof tenGodType==='function'?tenGodType(curDayunItem.ten_god):''}" style="font-size:10px;padding:1px 5px">${typeof tenGodCN==='function'?tenGodCN(curDayunItem.ten_god):curDayunItem.ten_god}</span>` : ''}
        </div>
      </div>
      <div>
        <div class="fortune-item-label">当前流年（${thisYear}）</div>
        <div class="fortune-item-value">${thisLiunian ? esc((thisLiunian.ganzhi||thisLiunian.year||thisYear)+'') : esc(String(thisYear))}</div>
        ${thisLiunian?.ten_god ? `<div style="margin-top:2px"><span class="tengod-badge ${typeof tenGodType==='function'?tenGodType(thisLiunian.ten_god_code||thisLiunian.ten_god):''}" style="font-size:10px;padding:1px 5px">${typeof tenGodCN==='function'?tenGodCN(thisLiunian.ten_god_code||thisLiunian.ten_god):thisLiunian.ten_god}</span></div>` : ''}
      </div>
    </div>
    ${(curDayunItem?.narrative || curDayunItem?.wealth_hint || curDayunItem?.health_hint || curDayunItem?.love_hint) ? `
    <details style="margin-top:8px">
      <summary style="cursor:pointer;font-size:11px;color:var(--accent);font-weight:600">▦ 当前大运叙事 &amp; 提示</summary>
      <div style="margin-top:8px;padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px">
        ${curDayunItem?.narrative ? `<div style="font-size:12px;line-height:1.65;color:var(--text);margin-bottom:8px">${renderPara(curDayunItem.narrative)}</div>` : ''}
        ${(curDayunItem?.wealth_hint||curDayunItem?.health_hint||curDayunItem?.love_hint) ? `
        <div style="display:flex;flex-direction:column;gap:5px">
          ${curDayunItem?.wealth_hint ? `<div style="font-size:11px;line-height:1.5"><span style="color:var(--accent-gold);font-weight:700">💰 财：</span>${txt(curDayunItem.wealth_hint)}</div>` : ''}
          ${curDayunItem?.health_hint ? `<div style="font-size:11px;line-height:1.5"><span style="color:var(--ok);font-weight:700">🏃 健：</span>${txt(curDayunItem.health_hint)}</div>` : ''}
          ${curDayunItem?.love_hint   ? `<div style="font-size:11px;line-height:1.5"><span style="color:#f43f5e;font-weight:700">♡ 婚：</span>${txt(curDayunItem.love_hint)}</div>` : ''}
        </div>` : ''}
      </div>
    </details>` : ''}
    ${(thisLiunian?.domain_forecasts || cf?.this_year_domains) ? `
    <div class="fortune-4d-grid">
      ${['财运','事业','婚恋','健康'].map(k=>{
        const val = (thisLiunian?.domain_forecasts||cf?.this_year_domains||{})[k]||'暂无';
        const isBad = /(注意|不佳|凶|差|衰|难|险)/.test(val);
        const isGood = /(顺|旺|吉|好|升|进|佳)/.test(val);
        const borderCol = isBad?'#fca5a5':isGood?'#86efac':'var(--line)';
        return `<div class="fortune-4d-item" style="border-bottom:3px solid ${borderCol}">
          <div class="fortune-4d-label">${k}</div>
          <div class="fortune-4d-text">${txt(val)}</div>
        </div>`;
      }).join('')}
    </div>` : ''}
    ${arc?.optimal_action ? `<div style="margin-top:10px;padding:8px 12px;background:var(--accent-gold-bg,rgba(224,139,0,0.08));border-radius:8px;font-size:12px;line-height:1.6"><span style="font-weight:700;color:var(--accent-gold)">📌 行动建议：</span>${esc(arc.optimal_action)}</div>` : ''}
  </div>

  <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
    <button data-switch-tab="2">查看命盘 →</button>
    <button data-switch-tab="5">查看摘要 →</button>
    <button data-switch-tab="16">查看大运 →</button>
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
  const p  = json.pillars_primary || {};
  const tg = json.ten_gods || {};
  const st = json.day_master_strength || {};
  const wx = json.wuxing_score || {};
  const yn = json.yongshen || {};

  const dayGan  = p.day?.stem || '';
  const dayElem = GAN_WUXING ? (GAN_WUXING[dayGan] || '') : '';
  const tierCls = st.tier==='strong'||st.tier==='extremely_strong' ? 'ok'
                : st.tier==='weak'  ||st.tier==='extremely_weak'   ? 'bad' : 'warn';

  /* ── 强弱诠释文字 ─────────────────────────────── */
  const TIER_INSIGHT = {
    extremely_strong: '日主太旺，命局偏强。用神宜取财星、官杀耗泄，忌印绶比劫再扶。',
    strong:           '日主身强，喜财官食伤耗泄，逢财官大运多可建功立业。',
    balanced:         '日主中和，命局最为理想，用神随时势灵活调配，进退有据。',
    neutral:          '日主中和，命局最为理想，用神随时势灵活调配，进退有据。',
    weak:             '日主身弱，喜印绶、比劫帮扶，忌财官消耗；扶助之运易出成绩。',
    extremely_weak:   '日主极弱，宜察是否属从格；非从格须大力扶助，方向用神有别。<button class="tier-geju-link" onclick="document.getElementById(\'tab-btn-3\').click()">→ 查看格局</button>',
  };
  const tierInsight = TIER_INSIGHT[st.tier] || '';

  /* ── 安全引用外部 window 函数 ────────────────── */
  const _zhiCss  = typeof ZHI_CSS    !== 'undefined' ? ZHI_CSS    : {};
  const _hidden  = typeof ZHI_HIDDEN !== 'undefined' ? ZHI_HIDDEN : {};
  const _tgDesc  = typeof tenGodDesc === 'function'  ? tenGodDesc : () => '';
  const _wxCN    = typeof wxCN       === 'function'  ? wxCN       : s => s;
  const _nayin   = typeof NAYIN      !== 'undefined' ? NAYIN      : {};
  const _ZHI_ROLE = ['本气','中气','余气'];

  /* ── 命盘概览条 ──────────────────────────────── */
  const overviewHtml = dayGan ? `
  <div class="bazi-overview">
    <span class="bov-tag">日主</span>
    <span class="bov-gan ${GAN_CSS[dayGan]||''}" title="${esc(GAN_DESC[dayGan]||'')}">${esc(dayGan)}</span>
    <span class="bov-elem-chip wx-${dayElem}">${_wxCN(dayElem)}</span>
    <span class="bov-div">·</span>
    <span class="level-badge ${tierCls}">${esc(translateRationale(st.tier)||'—')}</span>
    ${st.score!=null ? `<span class="bov-score-text">${st.score.toFixed(2)}分</span>` : ''}
    ${(yn.favor||[]).length ? `<span class="bov-div">·</span><span class="bov-yn-lbl-ok">用神</span>${(yn.favor||[]).map(f=>`<span class="chip ok bov-wxchip">${_wxCN(f)}</span>`).join('')}` : ''}
    ${(yn.avoid||[]).length ? `<span class="bov-yn-lbl-bad">忌神</span>${(yn.avoid||[]).map(f=>`<span class="chip bad bov-wxchip">${_wxCN(f)}</span>`).join('')}` : ''}
  </div>` : '';

  /* ── 四柱卡片 ───────────────────────────────── */
  const PILLAR_KEYS = {year:'年',month:'月',day:'日',hour:'时'};
  const pillarsCards = ['hour','day','month','year'].map(key => {
    const pillar   = p[key] || {};
    const isDay    = key === 'day';
    const tgCode   = isDay ? 'ri_zhu' : (tg[key] || '');
    const ganCls   = GAN_CSS[pillar.stem] || '';
    const zhiCls   = _zhiCss[pillar.branch] || '';
    const elemName = GAN_WUXING ? (GAN_WUXING[pillar.stem] || '') : '';
    const cardBg   = isDay ? 'pc-card-self' : (elemName ? `pc-card-${elemName}` : '');
    const ganTip   = esc(GAN_DESC[pillar.stem] || '');
    const tgTip    = tgCode ? esc(_tgDesc(tgCode)) : '';
    const hiddenGs = _hidden[pillar.branch] || [];
    const hiddenHtml = hiddenGs.length
      ? `<div class="pc-hidden-stems" title="藏干（本气·中气·余气）">${hiddenGs.map((g, idx) =>
          `<span class="pc-hidden-gan ${GAN_CSS[g]||''}" title="${_ZHI_ROLE[idx]||''}：${esc(GAN_DESC[g]||g)}"><sup class="pc-hidden-role">${_ZHI_ROLE[idx]||''}</sup>${esc(g)}</span>`
        ).join('')}</div>`
      : '';
    const nayinStr = _nayin[`${pillar.stem||''}${pillar.branch||''}`] || '';
    return `
    <div class="pillar-card ${cardBg}${isDay?' day-master':''}">
      ${isDay ? '<div class="day-master-badge">日主</div>' : ''}
      <div class="pc-label">${PILLAR_KEYS[key]}柱</div>
      <div class="pc-stem ${ganCls}" title="${ganTip}">${esc(pillar.stem||'—')}</div>
      ${elemName ? `<div class="pc-elem-tag wx-${elemName}">${_wxCN(elemName)}</div>` : ''}
      <div class="pc-divider"></div>
      <div class="pc-branch ${zhiCls}">${esc(pillar.branch||'—')}</div>
      ${nayinStr ? `<div class="pc-nayin">${esc(nayinStr)}</div>` : ''}
      ${hiddenHtml}
      <div class="pc-tg">${tgCode
        ? `<span class="tengod-badge ${tenGodType(tgCode)}" title="${tgTip}">${tenGodCN(tgCode)}</span>`
        : '<span class="tengod-badge">—</span>'}</div>
    </div>`;
  }).join('');

  /* ── 五行条形图 ──────────────────────────────── */
  const wxTotal = (wx.wood||0)+(wx.fire||0)+(wx.earth||0)+(wx.metal||0)+(wx.water||0);
  const wxBars = [['wood','木'],['fire','火'],['earth','土'],['metal','金'],['water','水']].map(([k,cn]) => {
    const v   = wx[k] || 0;
    const pct = wxTotal ? Math.round(v/wxTotal*100) : 0;
    return `<div class="wx-bar-row">
      <div class="wx-bar-label wx-${k}">${cn}</div>
      <div class="wx-bar-track"><div class="wx-bar-fill ${k}" style="width:${pct}%"></div></div>
      <div class="wx-bar-val">${v > 0
        ? `${v.toFixed(1)}<span class="wx-pct">${pct}%</span>`
        : '<span class="wx-missing">缺</span>'}</div>
    </div>`;
  }).join('');

  /* ── 因素原因中文化 ──────────────────────────── */
  const _ec = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};
  const translateReason = r => (!r ? '' : r
    .replace(/\b(wood|fire|earth|metal|water)\b/g, e => _ec[e]||e)
    .replace(/\bcount\b/gi, '同类总量')
    .replace(/\bgenerates\b/gi, '生'));

  /* ── 用神/忌神 chips ─────────────────────────── */
  const favorChips = (yn.favor||[]).map(f=>`<span class="chip ok">${_wxCN(f)}</span>`).join('');
  const avoidChips = (yn.avoid||[]).map(f=>`<span class="chip bad">${_wxCN(f)}</span>`).join('');

  /* ── 日主因素列表 ────────────────────────────── */
  const factorRows = (st.factors||[]).map(f => {
    const cn = translateFactorName(f.name);
    const rt = f.reason ? translateReason(cleanText(f.reason)) : '';
    const sc = f.score || 0;
    const scoreCls = sc >= 2 ? ' sfr-ok' : sc >= 1 ? ' sfr-mid' : '';
    return `<div class="strength-factor-row">
      <span class="sfr-name">${esc(cn)}</span>
      <span class="sfr-score${scoreCls}">${sc.toFixed(2)}</span>
      ${rt ? `<span class="sfr-reason">${esc(rt)}</span>` : ''}
    </div>`;
  }).join('');

  /* ── 强弱仪表进度 ────────────────────────────── */
  const meterPct = Math.min(100, Math.round((st.score||0) / 6 * 100));

  /* ── 主体 HTML ───────────────────────────────── */
  el.innerHTML = `
  ${overviewHtml}

  <!-- 四柱排盘 -->
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot"></span>四柱排盘
      <span class="card-title-sub">时｜日｜月｜年（从左到右）</span>
    </p>
    <div class="pillar-cards">${pillarsCards}</div>
    <div class="pillar-footnote">
      《三命通会》《子平真诠》 · 节气历：sxtwl VSOP87 · 藏干：子平通行版（悬停查看）
    </div>
  </div>

  <!-- 五行格局 ｜ 日主分析 -->
  <div class="g2" style="margin-bottom:14px">

    <!-- 左：五行格局 -->
    <div class="card">
      <p class="card-title"><span class="dot"></span>五行格局</p>
      <div class="wx-bar-wrap" style="margin-top:10px">${wxBars}</div>
      <div id="wuxingRingContainer" style="margin-top:14px"></div>
      ${favorChips||avoidChips ? `
      <div class="yn-section">
        ${favorChips ? `<div class="yn-row"><span class="yn-lbl-ok">▲ 用神</span><span class="yn-chips">${favorChips}</span></div>` : ''}
        ${avoidChips ? `<div class="yn-row"><span class="yn-lbl-bad">▼ 忌神</span><span class="yn-chips">${avoidChips}</span></div>` : ''}
        ${yn.rationale ? `<div class="yn-rationale">${renderPara(yn.rationale)}</div>` : ''}
      </div>` : ''}
      ${(json.wuxing_weak?.length||json.wuxing_strong?.length||json.balance_advice||json.wuxing_balance_score!=null) ? `
      <div class="yn-section" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px">
        ${json.wuxing_balance_score!=null ? `<div style="margin-bottom:8px">
          <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:4px">五行均衡分</div>
          <div class="strength-meter" style="height:8px">
            <div class="strength-meter-fill ${json.wuxing_balance_score>=70?'ok':json.wuxing_balance_score>=40?'warn':'bad'}" style="width:${Math.min(100,json.wuxing_balance_score||0)}%"></div>
          </div>
          <div style="font-size:11px;margin-top:2px;color:var(--muted)">${(json.wuxing_balance_score||0).toFixed(1)} / 100</div>
        </div>` : ''}
        ${json.wuxing_weak?.length ? `<div class="yn-row"><span class="yn-lbl-bad" style="font-size:11px">偏缺</span><span class="yn-chips">${json.wuxing_weak.map(f=>`<span class="chip bad">${typeof wxCN==='function'?wxCN(f):f}</span>`).join('')}</span></div>` : ''}
        ${json.wuxing_strong?.length ? `<div class="yn-row"><span class="yn-lbl-ok" style="font-size:11px">偏旺</span><span class="yn-chips">${json.wuxing_strong.map(f=>`<span class="chip warn">${typeof wxCN==='function'?wxCN(f):f}</span>`).join('')}</span></div>` : ''}
        ${json.balance_advice ? `<div class="tier-insight" style="margin-top:6px">${esc(json.balance_advice)}</div>` : ''}
      </div>` : ''}
    </div>

    <!-- 右：日主分析 -->
    <div class="card">
      <p class="card-title"><span class="dot"></span>日主分析</p>
      <div class="strength-hero">
        <div class="strength-score-block">
          <div class="strength-score-num">${st.score!=null ? st.score.toFixed(2) : '—'}</div>
          <div class="strength-score-lbl">强弱分值</div>
        </div>
        <span class="level-badge ${tierCls}" style="font-size:14px;padding:5px 14px">${esc(translateRationale(st.tier)||'—')}</span>
      </div>
      <div class="strength-meter">
        <div class="strength-meter-fill ${tierCls}" style="width:${meterPct}%"></div>
      </div>
      ${tierInsight ? `<div class="tier-insight">${tierInsight}</div>` : ''}
      ${factorRows ? `
      <div class="strength-factors" style="margin-top:12px">
        <div class="sfr-header">评分因素</div>
        ${factorRows}
      </div>` : ''}
    </div>

  </div>
  `;

  /* 渲染五行环形图 */
  if (typeof renderWuxingRingChart === 'function') {
    renderWuxingRingChart(wx, $('wuxingRingContainer'), json);
  }

  /* ── 五行详细贡献（天干/地支/藏干） ─────────────── */
  const wb = json.wuxing_breakdown;
  if (wb && (wb.stem_contrib || wb.branch_contrib || wb.hidden_contrib)) {
    const WX_KEYS = ['wood','fire','earth','metal','water'];
    const WX_CN_MAP = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};
    const card = document.createElement('details');
    card.className = 'card'; card.style.marginBottom = '14px';
    const rows = WX_KEYS.map(k => {
      const s = (wb.stem_contrib?.[k]||0).toFixed(2);
      const b = (wb.branch_contrib?.[k]||0).toFixed(2);
      const h = (wb.hidden_contrib?.[k]||0).toFixed(2);
      const total = ((wb.stem_contrib?.[k]||0)+(wb.branch_contrib?.[k]||0)+(wb.hidden_contrib?.[k]||0)).toFixed(2);
      return `<tr><td class="wx-${k}" style="font-weight:700;padding:4px 8px">${WX_CN_MAP[k]}</td><td style="padding:4px 8px;text-align:right">${s}</td><td style="padding:4px 8px;text-align:right">${b}</td><td style="padding:4px 8px;text-align:right;color:var(--muted)">${h}</td><td style="padding:4px 8px;text-align:right;font-weight:600">${total}</td></tr>`;
    }).join('');
    card.innerHTML = `<summary style="cursor:pointer;padding:8px 10px;font-size:12px;color:var(--muted);font-weight:600">⊞ 五行分量明细（天干 / 地支 / 藏干）</summary>
    <div style="overflow-x:auto;padding:8px 10px">
      <table style="font-size:12px;border-collapse:collapse;width:100%">
        <thead><tr><th style="padding:3px 8px;text-align:left;color:var(--muted)">五行</th><th style="padding:3px 8px;text-align:right;color:var(--muted)">天干</th><th style="padding:3px 8px;text-align:right;color:var(--muted)">地支</th><th style="padding:3px 8px;text-align:right;color:var(--muted)">藏干</th><th style="padding:3px 8px;text-align:right;color:var(--muted)">合计</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
    el.appendChild(card);
  }

  /* ── 干支互动 ────────────────────────────────── */
  const dzRels    = json.dizhi_relations  || [];
  const tgClashes = json.tiangan_clashes  || [];
  if (!dzRels.length && !tgClashes.length) return;

  const REL_ICON = {
    '三合':'◎','六合':'○','半合':'◑','三会':'●',
    '冲':'↔','三刑':'✕','自刑':'×','刑':'⊗','害':'⊘','破':'⊡',
  };
  const REL_MEANING = {
    '三合': r => `三合${r.element||''}局——三方同气，${r.element ? _wxCN(r.element) : ''}气大旺，大运流年逢此五行大利`,
    '六合': r => `六合——阴阳调和，主合作顺利、感情婚姻运较顺`,
    '半合': r => `半合${r.element||''}——半局之合，力略薄，仍有聚力效用`,
    '三会': r => `三会${r.element||''}方——地支方位全聚，力超三合，${r.element ? _wxCN(r.element) : ''}气极旺`,
    '三刑': r => `三刑——主是非官非或因刑得贵，性格执拗，视格局而定`,
    '自刑': r => `自刑——主自我矛盾、重复失误，宜守成慎行`,
    '冲':   r => `相冲（${(r.positions||[]).join('→')}）——主变动迁移，有冲则有动，防动荡损身`,
    '刑':   r => `相刑（${(r.positions||[]).join('→')}）——主官非口舌或身体灾伤，三刑尤重`,
    '害':   r => `相害（${(r.positions||[]).join('→')}）——主小人暗算、人际受损，宜慎合伙`,
    '破':   r => `相破（${(r.positions||[]).join('→')}）——主事业反复难善终，防始善终恶`,
  };
  const TG_MEANING = {
    '克': c => `天干相克（${(c.positions||c.stems||[]).join('→')}）——两干对立，主内部消耗，防竞争内耗`,
    '合': c => `天干相合化${c.element||'?'}——调和但失本气，合中有制`,
  };

  const makeRow = (r, isTg) => {
    const relType  = r.type || '';
    const isHarm   = /冲|刑|害|破|克/.test(relType);
    const matchKey = isTg
      ? Object.keys(TG_MEANING).find(k => relType.includes(k))
      : Object.keys(REL_MEANING).find(k => relType.includes(k));
    const chars = (isTg ? (r.stems||[]) : (r.branches||[])).map(c=>esc(c)).join('');
    const icon  = REL_ICON[matchKey||relType] || (isHarm ? '⊗' : '○');
    const desc  = matchKey
      ? (isTg ? TG_MEANING[matchKey](r) : REL_MEANING[matchKey](r))
      : relType;
    return `<div class="rel-row">
      <span class="rel-icon ${isHarm?'rel-icon-bad':'rel-icon-ok'}">${icon}</span>
      <span class="chip ${isHarm?'bad':'ok'} rel-chip">${chars} ${esc(relType)}</span>
      <span class="rel-desc">${esc(desc)}</span>
    </div>`;
  };

  const relRows   = dzRels.map(r => makeRow(r, false)).join('');
  const clashRows = tgClashes.map(c => makeRow(c, true)).join('');

  const relCard = document.createElement('div');
  relCard.className = 'card';
  relCard.innerHTML = `
    <p class="card-title">
      <span class="dot"></span>
      ${dzRels.length >= 3 ? '<span class="rel-star">★</span>' : ''}干支互动
      <span class="card-title-sub">地支 ${dzRels.length} 条${tgClashes.length ? ` · 天干 ${tgClashes.length} 条` : ''}</span>
    </p>
    <div class="rel-legend">
      <span class="rel-legend-ok">○ / ◎ = 有利之象</span>
      <span class="rel-legend-bad">⊗ / ↔ = 宜防之象</span>
    </div>
    <div class="rel-list">
      ${relRows || '<div class="rel-empty">地支无显著关系</div>'}
      ${clashRows ? `<div class="rel-tg-section">${clashRows}</div>` : ''}
    </div>
  `;
  el.appendChild(relCard);
}

/* ══════════════════════════════════════════════════
   Tab 3: 格局 (GejuModel)
═══════════════════════════════════════════════════ */
function renderTab3(json, el) {
  const g = json.geju;
  if (!g) {
    el.innerHTML = `<div class="geju-empty"><div style="font-size:40px;margin-bottom:10px">⊞</div><div>格局数据尚未计算，请先排盘。</div></div>`;
    return;
  }
  const tierCls = (g.tier==='高'||g.geju_level==='上格') ? 'high' : (g.tier==='中'||g.geju_level==='中格') ? 'mid' : 'low';
  const confPct  = typeof g.confidence === 'number' ? Math.round(g.confidence * 100) : null;
  const uncertain = confPct !== null && confPct < 50;
  const levelLabel = g.geju_level==='上格' ? '▲ 上格' : g.geju_level==='中格' ? '◆ 中格' : g.geju_level==='下格' ? '▽ 下格' : (g.geju_level||'');

  // 印章：取格局名前2-4字
  const fullName = g.geju_name || g.name || '未知';
  const sealChars = fullName.replace(/格$/, '').slice(0, 4);
  const sealLines = sealChars.length <= 2
    ? [sealChars]
    : [sealChars.slice(0, 2), sealChars.slice(2)];

  const confBarHtml = confPct !== null ? `
    <div class="geju-conf-row">
      <span class="geju-conf-label">置信度</span>
      <div class="geju-conf-track"><div class="geju-conf-fill geju-conf-${confPct>=70?'ok':confPct>=40?'mid':'low'}" style="width:${confPct}%"></div></div>
      <span class="geju-conf-val">${confPct}%</span>
    </div>` : '';

  const heroHtml = `
  <div class="geju-hero card" style="margin-bottom:12px">
    <div class="geju-seal geju-seal-${tierCls}">
      ${sealLines.map(l=>`<div class="geju-seal-ln">${esc(l)}</div>`).join('')}
      ${g.score !== undefined ? `<div class="geju-seal-score">${Math.round(g.score)}</div>` : ''}
    </div>
    <div class="geju-hero-body">
      <div class="geju-hero-name">
        ${esc(fullName)}
        ${uncertain ? `<span class="tag-uncertain" title="置信度${confPct}%，格局尚不确定">待定</span>` : ''}
      </div>
      ${levelLabel ? `<div class="geju-tier-badge ${tierCls}" style="margin-bottom:10px">${levelLabel}</div>` : ''}
      ${confBarHtml}
    </div>
  </div>`;

  const classicRefText = g.classic_ref || '';
  const classicRefCount = classicRefText ? classicRefText.split('\n').filter(l => l.trim()).length : 0;
  const classicRefHtml = classicRefText ? `
  <details class="geju-classic card" style="margin-bottom:12px">
    <summary>📜 古籍引用${classicRefCount > 1 ? `（共${classicRefCount}条）` : ''}</summary>
    <div class="geju-classic-body">${txt(classicRefText)}</div>
  </details>` : '';

  // geju_detail 用作格局释义（API 字段名），g.description 是兜底
  const _detailText = (g.geju_detail || g.description || '').trim();
  const _showDetailCard = _detailText && _detailText !== (g.interpretation_text||'').trim();

  const brokenBadge = g.is_broken === true
    ? `<div class="card" style="margin-bottom:12px;border-left:3px solid var(--bad)"><div style="display:flex;align-items:center;gap:8px"><span style="font-size:18px">⚠️</span><div><div style="font-weight:700;color:var(--bad)">格局已破</div><div style="font-size:12px;color:var(--muted);margin-top:2px">命局存在破格因素，格局力量受限，解读需结合大运调候</div></div></div></div>`
    : g.is_broken === false
    ? `<div style="margin-bottom:12px;font-size:11px;color:var(--ok);padding:4px 8px;background:rgba(34,197,94,0.08);border-radius:6px;display:inline-block">✓ 格局完整（未见破格）</div>`
    : '';

  el.innerHTML = heroHtml + brokenBadge + `
  ${_showDetailCard ? `<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>格局释义</p><div class="geju-text">${renderPara(_detailText)}</div></div>` : ''}
  ${g.interpretation_text ? `<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>深度解读</p><div class="geju-text">${renderPara(g.interpretation_text)}</div>${_detailText&&!_showDetailCard?`<div style="margin-top:6px;font-size:11px;color:var(--muted)">📐 判断依据：${esc(_detailText)}</div>`:''}${g.month_stem_shishen?`<div style="margin-top:4px;font-size:11px;color:var(--muted)">月令十神：<code>${esc(g.month_stem_shishen)}</code></div>`:''}</div>` : ''}
  ${g.inference_tags?.length ? `<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>分析标签</p><div class="row">${g.inference_tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div></div>` : ''}
  ${classicRefHtml}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 4: 命宫 (PalaceModel)
═══════════════════════════════════════════════════ */
function renderTab4(json, el) {
  const palace = json.palace;
  if (!palace) { el.innerHTML = '<div class="hint" style="padding:16px">命宫数据尚未计算。</div>'; return; }

  // ── 命宫·身宫 宫位卡槽 ──
  const makePalaceSlot = (p, lbl) => {
    if (!p) return `<div class="palace-slot"><div class="ps-title">${lbl}</div><div class="hint" style="font-size:12px">暂无</div></div>`;
    const wCls  = (window.ZHI_CSS||{})[p.dizhi] || '';
    const tgCode = p.ten_god_code || p.shishen || '';
    const tgCN   = typeof tenGodCN   === 'function' ? tenGodCN(tgCode)   : (p.shishen||tgCode||'');
    const tgType = typeof tenGodType === 'function' ? tenGodType(tgCode) : '';
    return `<div class="palace-slot">
      <div class="ps-title">${lbl}</div>
      <div class="ps-zhi ${wCls}">${esc(p.dizhi||'—')}</div>
      ${p.tiangan?`<div style="font-size:10px;color:var(--muted);margin-top:1px">干：${esc(p.tiangan)}</div>`:''}
      ${p.strength ? `<div class="ps-str">${esc(p.strength)}</div>` : ''}
      ${tgCN ? `<span class="tengod-badge ${tgType} ps-tg" title="${typeof tenGodDesc==='function'?tenGodDesc(tgCode):''}">${tgCN}</span>` : ''}
    </div>`;
  };

  const palaceCard = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>命宫 · 身宫</p>
    <div class="palace-pair">
      ${makePalaceSlot(palace.ming_gong, '命宫')}
      ${makePalaceSlot(palace.shen_gong, '身宫')}
    </div>
    ${palace.interpretation_text ? `<div class="note" style="margin-top:10px"><div style="font-size:12px;line-height:1.6">${renderPara(palace.interpretation_text)}</div></div>` : palace.note ? `<div class="note" style="margin-top:10px"><div style="font-size:12px">${renderPara(palace.note)}</div></div>` : ''}
    ${palace.inference_tags?.length ? `<div class="row" style="margin-top:8px;flex-wrap:wrap">${palace.inference_tags.map(t=>`<span class="chip" style="font-size:11px">${esc(t)}</span>`).join('')}</div>` : ''}
  </div>`;

  // ── 神煞 分级分类展示 ──
  let shenshaCard = '';
  const ss = json.shensha || [];
  if (ss.length) {
    const aOk  = ss.filter(s => s.priority==='A' &&  s.is_beneficial);
    const aBad = ss.filter(s => s.priority==='A' && !s.is_beneficial);
    const bOk  = ss.filter(s => s.priority!=='A' &&  s.is_beneficial);
    const bBad = ss.filter(s => s.priority!=='A' && !s.is_beneficial);

    const makeGroup = (items, label, cls) => {
      if (!items.length) return '';
      const chips = items.map(s => {
        const sn  = chipName(s.name || '');
        const pc  = {year:'年',month:'月',day:'日',hour:'时'}[s.pillar] || s.pillar || '';
        const tt  = [chipTitle(s.name||''), txt(s.meaning||''), s.classic_source?`出自${s.classic_source}`:''].filter(Boolean).join('\n');
        return `<span class="ss-chip ${cls}" title="${tt}">${s.is_star?'★ ':''}<strong>${sn}</strong>${pc?` <small class="hint">${pc}</small>`:''}</span>`;
      }).join('');
      return `<div class="ss-group">
        <div class="ss-group-lbl ${cls}">${label} <span class="ss-cnt">${items.length}</span></div>
        <div class="ss-chips">${chips}</div>
      </div>`;
    };

    shenshaCard = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>神煞 <span class="card-title-sub">共${ss.length}种</span></p>
    <div class="ss-groups">
      ${makeGroup(aOk,  'A级·吉', 'ss-a-ok')}
      ${makeGroup(aBad, 'A级·凶', 'ss-a-bad')}
      ${makeGroup(bOk,  'B级·吉', 'ss-b-ok')}
      ${makeGroup(bBad, 'B级·凶', 'ss-b-bad')}
    </div>
  </div>`;
  } else {
    shenshaCard = `<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>神煞</p><div class="hint">暂无神煞数据</div></div>`;
  }

  // ── 十二宫位 网格 ──
  const houses = palace.twelve_palaces || palace.houses || [];
  const houseGrid = houses.length ? `
  <div class="card">
    <p class="card-title"><span class="dot"></span>十二宫位</p>
    <div class="twelve-palace-grid">
      ${houses.map((h, i) => {
        const wCls = (window.ZHI_CSS||{})[h.dizhi] || '';
        const hShishen = h.shishen || h.ten_god || '';
        const hTgCode  = hShishen;
        const hTgCN    = hShishen ? (typeof tenGodCN  ==='function' ? tenGodCN(hTgCode)  : hShishen) : '';
        const hTgType  = hShishen ? (typeof tenGodType==='function' ? tenGodType(hTgCode) : '')      : '';
        return `<div class="tpc">
          <div class="tpc-name">${esc(h.palace_name||`宫${i+1}`)}</div>
          <div class="tpc-zhi ${wCls}">${esc(h.dizhi||'—')}</div>
          ${h.tiangan ? `<div style="font-size:9px;color:var(--muted);margin-top:1px;letter-spacing:.03em">干：${esc(h.tiangan)}</div>` : ''}
          ${hTgCN ? `<div style="margin-top:2px"><span class="tengod-badge ${hTgType}" style="font-size:9px;padding:1px 4px">${hTgCN}</span></div>` : ''}
          ${h.strength ? `<div class="tpc-str">${esc(h.strength)}</div>` : ''}
          ${h.note||h.description ? `<div class="tpc-note">${txt(h.note||h.description)}</div>` : ''}
        </div>`;
      }).join('')}
    </div>
  </div>` : '';

  el.innerHTML = palaceCard + shenshaCard + houseGrid;
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

  /* ── 人生命局卡 ──────────────────────────────── */
  const tierBadge5 = (tier) => {
    const cls = tier==='局高'?'high':tier==='局中'?'mid':'low';
    return tier ? `<span class="geju-tier-badge ${cls}">${esc(tier)}</span>` : '';
  };
  const arcCard = (arc.overall_tier || arc.interpretation_text || arc.early_fortune) ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent-gold)"></span>人生命局总论</p>
    ${arc.overall_tier ? `<div style="margin-bottom:10px">${tierBadge5(arc.overall_tier)}${arc.life_motto ? `<span style="font-size:13px;color:var(--text);margin-left:10px;font-style:italic">"${esc(arc.life_motto)}"</span>` : ''}</div>` : ''}
    ${arc.interpretation_text ? `<div style="font-size:13px;line-height:1.75;margin-bottom:12px">${renderPara(arc.interpretation_text)}</div>` : ''}
    ${(arc.early_fortune||arc.mid_fortune||arc.late_fortune) ? `
    <div class="g3" style="gap:10px;margin-bottom:10px">
      ${arc.early_fortune?`<div class="card" style="padding:10px;margin:0"><div style="font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:4px">早年（0–30岁）</div><div style="font-size:12px;line-height:1.6">${renderPara(arc.early_fortune)}</div></div>`:''}
      ${arc.mid_fortune?`<div class="card" style="padding:10px;margin:0"><div style="font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:4px">中年（30–60岁）</div><div style="font-size:12px;line-height:1.6">${renderPara(arc.mid_fortune)}</div></div>`:''}
      ${arc.late_fortune?`<div class="card" style="padding:10px;margin:0"><div style="font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:4px">晚年（60岁+）</div><div style="font-size:12px;line-height:1.6">${renderPara(arc.late_fortune)}</div></div>`:''}
    </div>` : ''}
    ${(arc.peak_periods?.length||arc.caution_periods?.length) ? `
    <div class="kv" style="margin-top:4px">
      ${arc.peak_periods?.length ? `<div class="k">顶峰大运</div><div>${arc.peak_periods.map(p=>`<span class="chip ok">${esc(p)}</span>`).join(' ')}</div>` : ''}
      ${arc.caution_periods?.length ? `<div class="k">注意大运</div><div>${arc.caution_periods.map(p=>`<span class="chip warn">${esc(p)}</span>`).join(' ')}</div>` : ''}
    </div>` : ''}
    ${arc.optimal_action ? `<div style="margin-top:10px;padding:8px 12px;background:var(--accent-gold-bg,rgba(224,139,0,0.08));border-radius:8px;font-size:12px"><span style="font-weight:700;color:var(--accent-gold)">📌 行动建议：</span>${esc(arc.optimal_action)}</div>` : ''}
  </div>` : '';

  /* ── 人生里程碑时间轴 ─────────────────────────── */
  const milestones = json.milestones || [];
  const MS_ICON = {'犯太岁':'⚡','岁运并临':'🌟','大运交接':'🔄','社会节点':'👥','流年冲关':'⚡','本命年':'🔥','人生节点':'📍','节气节点':'🌿','事业节点':'💼','婚恋节点':'💞','健康节点':'🏥'};
  const msHtml = milestones.length ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent)"></span>人生里程碑 <span class="card-title-sub">共${milestones.length}个节点</span></p>
    <div style="display:flex;flex-direction:column;gap:8px;margin-top:8px">
      ${milestones.map(m => {
        const rlCls = m.risk_level==='高'?'bad':m.risk_level==='中'?'warn':'ok';
        const typeIcon = MS_ICON[m.milestone_type] || '📌';
        const showTypeTag = m.milestone_type && m.description && m.description !== m.milestone_type;
        return `<div style="display:flex;gap:10px;padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;align-items:flex-start">
          <div style="min-width:56px;text-align:center;flex-shrink:0">
            <div style="font-size:16px;font-weight:800;color:var(--accent)">${m.age}岁</div>
            <div style="font-size:10px;color:var(--muted)">${m.year}年</div>
          </div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px">
              ${showTypeTag ? `<span style="font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(var(--accent-rgb,99,102,241),0.1);color:var(--accent);font-weight:600">${typeIcon} ${esc(m.milestone_type)}</span>` : ''}
              <span style="font-size:13px;font-weight:600">${showTypeTag ? '' : typeIcon+' '}${esc(m.description||m.milestone_type)}</span>
              ${m.risk_level?`<span class="chip ${rlCls}" style="font-size:10px;padding:1px 6px">${esc(m.risk_level)}</span>`:''}
              ${m.ganzhi_context?`<span style="font-size:11px;color:var(--muted)">${esc(m.ganzhi_context)}</span>`:''}
            </div>
            ${m.advice?`<div style="font-size:12px;color:var(--muted);line-height:1.5">💡 ${esc(m.advice)}</div>`:''}
          </div>
        </div>`;
      }).join('')}
    </div>
  </div>` : '';

  /* ── 6D评分 + 技术数据（折叠） ───────────────── */
  const techHtml = `
  <div class="summary-grid">
    <div class="summary-card"><div class="summary-label">校验级别</div><div class="summary-value">${esc(v.level||'—')}</div><span class="summary-pill ${lvlCls}">${{L0:'无差异',L1:'时柱差异',L2:'月柱差异',L3:'多柱差异'}[v.level]||'—'}</span></div>
    <div class="summary-card"><div class="summary-label">告警数</div><div class="summary-value">${warnings.length}</div><span class="summary-pill ${warnings.length?'warn':'ok'}">${warnings.length?'有告警':'正常'}</span></div>
    <div class="summary-card"><div class="summary-label">格局</div><div class="summary-value">${esc(arc.overall_tier||json.geju?.geju_level||'—')}</div></div>
    <div class="summary-card"><div class="summary-label">日主</div><div class="summary-value">${esc(translateRationale(json.day_master_strength?.tier)||'—')}</div></div>
  </div>
  <div id="scoringRadarContainer" style="margin:12px 0"></div>
  ${warnings.length?`<div class="card" style="margin-bottom:12px;border-left:3px solid var(--warn)"><p class="card-title"><span class="dot" style="background:var(--warn)"></span>告警列表 <span class="chip warn" style="font-size:10px;padding:1px 6px">${warnings.length}条</span></p><div class="warnlist">${warnings.map(w=>`<div class="warnitem"><div class="wcode">${esc(w.code||w.type||'WARN')}</div><div class="wmsg">${esc(w.message||w.msg||'')}</div></div>`).join('')}</div></div>`:''}
  <details style="margin-bottom:12px">
    <summary style="cursor:pointer;padding:8px 0;font-size:12px;color:var(--muted);font-weight:600">⚙ 技术详情（校验 / 版本 / 调试）</summary>
    <div class="kv card" style="margin-top:8px">
      <div class="k">推算模式</div><div>${esc(json.mode_requested||'?')} → ${esc(json.mode_effective||'?')}</div>
      <div class="k">request_id</div><div><code>${esc(json.request_id||'—')}</code> <button data-copy-text="${esc(json.request_id||'')}" style="font-size:11px;padding:2px 8px">复制</button></div>
      <div class="k">API版本</div><div>${esc(json.api_version||'—')}</div>
      <div class="k">引擎版本</div><div>${esc(json.engine_version||'—')}</div>
      <div class="k">计算耗时</div><div>${json.calc_ms!=null?json.calc_ms.toFixed(1)+' ms':'—'}</div>
      <div class="k">规则版本</div><div>${esc(json.rule_version||'—')}</div>
      <div class="k">太阳时偏移</div><div>${nn(json.solar_time_offset_minutes)} 分钟</div>
    </div>
    ${Object.keys(rt).length?`<div class="card" style="margin-top:8px"><p class="card-title"><span class="dot"></span>规则版本明细</p><div class="kv">${Object.entries(rt).map(([k,v])=>`<div class="k">${esc(k)}</div><div><code>${esc(v)}</code></div>`).join('')}</div></div>`:''}
  </details>`;

  el.innerHTML = arcCard + msHtml + techHtml;

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
      <button data-copy-el="rawPre">复制 JSON</button>
    </div>
    <pre id="rawPre" style="margin-top:8px">${esc(JSON.stringify(json,null,2))}</pre>
  </details>
  `;
}

/* ══════════════════════════════════════════════════
   Tab 7: 财运 (WealthAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab7(json, el) {
  const w  = json.wealth_analysis||{};
  const wo = json.wealth||{};
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);
  const score = w.wealth_score ?? wo.score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)';

  const heroHtml = `
  <div class="fortune-hero card" style="margin-bottom:12px">
    <div class="fh-score-block">
      <div class="fh-icon">💰</div>
      <div class="fh-score" style="color:${scoreColor}">${score!=null?score.toFixed(0):'—'}</div>
      <div class="fh-label">财运评分</div>
    </div>
    <div class="fh-body">
      ${w.wealth_tier||wo.wealth_range?.label?`<div class="fh-tier">${esc(w.wealth_tier||wo.wealth_range?.label||'')}</div>`:''}
      ${w.annual_range?`<div class="fh-range">年收入参考：<strong>${esc(w.annual_range)}</strong></div>`:''}
      ${score!=null?`<div class="fh-bar"><div class="fh-bar-fill" style="width:${clamp(score,0,100)}%;background:linear-gradient(90deg,#f59e0b,#fbbf24)"></div></div>`:''}
      ${w.fact_data?.wealth_tier?`<div class="fh-fact">实证：${txt(w.fact_data.wealth_tier)}</div>`:''}
    </div>
  </div>`;

  const tagHtml = w.inference_tags?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运标签</p>
    <div class="row">${w.inference_tags.map(t=>`<span class="chip ok">${esc(t)}</span>`).join('')}</div>
  </div>` : '';

  // 只使用新模型的Chinese行业列表，丢弃旧WealthModel.industry_tags(English)
  const indList = (w.industries||[]);
  const indHtml = indList.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>适合行业</p>
    <div class="row">${indList.map(t=>`<span class="chip">🏢 ${esc(t)}</span>`).join('')}</div>
  </div>` : '';

  const interpHtml = w.interpretation_text ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运解读</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(w.interpretation_text)}</div>
  </div>` : '';

  const stratHtml = w.strategy ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运策略</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(w.strategy)}</div>
  </div>` : '';

  const riskHtml = wo.risk_hint ? `
  <div class="card" style="margin-bottom:12px;border-left:3px solid var(--warn)">
    <p class="card-title"><span class="dot" style="background:var(--warn)"></span>风险提示</p>
    <div style="font-size:12px;line-height:1.6">${txt(wo.risk_hint)}</div>
  </div>` : '';

  const noteHtml = wo.note ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运注解</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(wo.note)}</div>
  </div>` : '';

  const dayunHtml = w.dayun_forecast?.length ? `
  <div class="card">
    <p class="card-title"><span class="dot"></span>大运财运周期</p>
    <div class="dayun-forecast-list">
      ${w.dayun_forecast.map(fc=>`<div class="dfc-row"><div class="dfc-gz">${esc(fc.ganzhi||'')}</div><div class="dfc-trend">${txt(fc.trend||'')}</div>${fc.description?`<div class="dfc-desc">${txt(fc.description)}</div>`:''}</div>`).join('')}
    </div>
  </div>` : '';

  const wealthDimsHtml = (w.investment_preference || w.financial_taboos || w.wealth_accumulation_phases) ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运深度分析</p>
    ${w.investment_preference ? `<div style="margin-bottom:10px"><div class="advice-section-lbl">📈 投资偏好</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(w.investment_preference)}</div></div>` : ''}
    ${w.financial_taboos ? `<div style="margin-bottom:10px"><div class="advice-section-lbl" style="color:var(--bad)">🚫 财务禁区</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(w.financial_taboos)}</div></div>` : ''}
    ${w.wealth_accumulation_phases ? `<div><div class="advice-section-lbl">🗓 三阶段规划</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(w.wealth_accumulation_phases)}</div></div>` : ''}
  </div>` : '';

  el.innerHTML = heroHtml + tagHtml + indHtml + interpHtml + stratHtml + wealthDimsHtml + riskHtml + noteHtml + dayunHtml;
  el.insertAdjacentHTML('beforeend','<div class="disclaimer-note" style="margin-top:8px">▲ 年收入区间为基于五行推断的模糊参考，非精密测算，不构成任何投资或财务建议。</div>');
}

/* ══════════════════════════════════════════════════
   Tab 8: 事业 (CareerAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab8(json, el) {
  const c = json.career||{};
  if (!c.career_directions?.length && !c.interpretation_text && !c.career_score) {
    el.innerHTML = '<div style="padding:16px;color:var(--muted);font-size:13px">事业分析需根据格局和用神进一步推算，请先完成命盘排盘。</div>'; return;
  }
  const score = c.career_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)';

  const heroHtml = `
  <div class="fortune-hero card" style="margin-bottom:12px">
    <div class="fh-score-block">
      <div class="fh-icon">⚡</div>
      <div class="fh-score" style="color:${scoreColor}">${score!=null?score.toFixed(1):'—'}</div>
      <div class="fh-label">事业评分</div>
    </div>
    <div class="fh-body">
      ${c.optimal_move_timing?`<div class="fh-tier">最佳时机：${txt(c.optimal_move_timing)}</div>`:''}
      ${c.leadership_potential!==undefined?`<div class="fh-fact${c.leadership_potential?' fh-fact-ok':''}">${c.leadership_potential?'⭐ 具备领导力潜质':'⎼ 领导力潜质一般'}</div>`:''}
      ${score!=null?`<div class="fh-bar"><div class="fh-bar-fill" style="width:${Math.min(score,100)}%;background:linear-gradient(90deg,var(--accent),#60a5fa)"></div></div>`:''}
    </div>
  </div>`;

  const CAREER_ICON = {'管理':'🏛','教育':'📚','技术':'💻','金融':'📈','医疗':'⚕','法律':'⚖','艺术':'🎨','传媒':'📡','销售':'📢','建筑':'🏗','农':'🌾','军':'⚔','行政':'📋'};
  const getCareerIcon = d => Object.entries(CAREER_ICON).find(([k])=>d.includes(k))?.[1]||'▸';

  const dirHtml = c.career_directions?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>职业方向</p>
    <div class="row">${c.career_directions.map(d=>`<span class="chip career-chip">${getCareerIcon(d)} ${esc(d)}</span>`).join('')}</div>
    ${c.interpretation_text?`<div style="margin-top:10px;font-size:13px;line-height:1.6">${renderPara(c.interpretation_text)}</div>`:''}
  </div>` : (c.interpretation_text?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>事业解读</p><div style="font-size:13px;line-height:1.7">${renderPara(c.interpretation_text)}</div></div>`:'');

  el.innerHTML = heroHtml + dirHtml + `
  ${c.development_advice?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>发展建议</p><div style="font-size:13px;line-height:1.7">${renderPara(c.development_advice)}</div></div>`:''}
  ${c.entrepreneurship_assessment?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>创业vs职场评估</p><div style="font-size:13px;line-height:1.7">${renderPara(c.entrepreneurship_assessment)}</div></div>`:''}
  ${c.five_year_roadmap?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>五年职业路线图</p><div style="font-size:13px;line-height:1.7">${renderPara(c.five_year_roadmap)}</div></div>`:''}
  ${c.collaboration_style?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>最佳协作风格</p><div style="font-size:13px;line-height:1.7">${renderPara(c.collaboration_style)}</div></div>`:''}
  ${c.suitable_industries?.length?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>适合行业</p><div class="row">${c.suitable_industries.map(i=>`<span class="chip">🏢 ${esc(i)}</span>`).join('')}</div></div>`:''}
  ${c.inference_tags?.length?`<div class="card"><p class="card-title"><span class="dot"></span>分析标签</p><div class="row">${c.inference_tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 9: 姻缘 (MarriageAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab9(json, el) {
  const ma = json.marriage_analysis||{};
  const so = json.social||{};
  const score = ma.marriage_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)';

  // 桃花状态
  const pb = ma.peach_blossom||'';
  const pbLabel = pb==='旺'?'🌸 桃花旺，姻缘活跃':pb==='中'?'🌸 桃花中等':pb==='弱'?'桃花较弱，需主动经营':'';

  const heroHtml = `
  <div class="fortune-hero card" style="margin-bottom:12px">
    <div class="fh-score-block">
      <div class="fh-icon">♡</div>
      <div class="fh-score" style="color:${scoreColor}">${score!=null?score.toFixed(1):'—'}</div>
      <div class="fh-label">婚姻评分</div>
    </div>
    <div class="fh-body">
      ${ma.marriage_windows?.length?`<div class="fh-tier">婚期：${ma.marriage_windows.slice(0,2).map(w=>esc(w)).join('，')}</div>`:''}
      ${ma.optimal_marriage_age?`<div class="fh-tier">最佳婚龄：${esc(ma.optimal_marriage_age)}</div>`:''}
      ${pbLabel?`<div class="fh-fact ${pb==='旺'?'fh-fact-ok':''}">${pbLabel}</div>`:`${so.taohua_hit?'<div class="fh-fact fh-fact-ok">🌸 命中桃花星</div>':'<div class="fh-fact">暂无桃花星</div>'}`}
      ${score!=null?`<div class="fh-bar"><div class="fh-bar-fill" style="width:${Math.min(score,100)}%;background:linear-gradient(90deg,#f43f5e,#fb7185)"></div></div>`:''}
    </div>
  </div>`;

  const profileHtml = ma.partner_profile ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:#f43f5e"></span>理想配偶画像</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(ma.partner_profile)}</div>
    ${ma.partner_wuxing?`<div style="margin-top:6px;font-size:12px;color:var(--muted)">配偶五行：<span class="chip" style="font-size:11px">${esc(ma.partner_wuxing)}</span></div>`:''}
    ${ma.partner_direction?`<div style="margin-top:4px;font-size:12px;color:var(--muted)">觅缘方位：${esc(ma.partner_direction)}</div>`:''}
    ${ma.interpretation_text?`<div class="note" style="margin-top:8px"><div style="font-size:12px">${renderPara(ma.interpretation_text)}</div></div>`:''}
  </div>` : (ma.interpretation_text?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>婚恋分析</p><div style="font-size:13px;line-height:1.7">${renderPara(ma.interpretation_text)}</div></div>`:'');

  const childHtml = (ma.children_outlook||ma.children_timing) ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>子女缘</p>
    ${ma.children_outlook?`<div class="note" style="margin-bottom:6px"><div style="font-size:13px">${txt(ma.children_outlook)}</div></div>`:''}
    ${ma.children_timing?`<div style="font-size:12px;color:var(--muted);padding:0 4px">${txt(ma.children_timing)}</div>`:''}
  </div>` : '';

  // 桃花流年命中
  const taohuaYearsHtml = so.taohua_year_hit?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:#f43f5e"></span>🌸 桃花流年</p>
    <div class="row" style="flex-wrap:wrap">${so.taohua_year_hit.map(y=>`<span class="chip ok" style="font-size:14px;padding:4px 10px">${y}年</span>`).join('')}</div>
  </div>` : '';

  // 社交/感情提示（来自 social 模型）
  const socialHintHtml9 = so.social_hint ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>感情社交提示</p>
    <div style="font-size:13px;line-height:1.7">${txt(so.social_hint)}</div>
    ${so.relation_conflict!==undefined?`<div style="margin-top:6px;font-size:12px;color:${so.relation_conflict?'var(--bad)':'var(--ok)'}">${so.relation_conflict?'⚠ 命局有人际冲突倾向':'✓ 人际关系基础较顺'}</div>`:''}
  </div>` : '';

  // 官杀混杂 / 夫妻宫冲克 来自老 marriage 模型
  const mf = json.marriage?.marriage_flags||{};
  const mfHtml = (mf.guansha_mix!=null || mf.spouse_palace_conflict!=null) ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>命局婚姻信号</p>
    <div class="row" style="flex-wrap:wrap;gap:6px">
      ${mf.guansha_mix!=null?`<span class="chip ${mf.guansha_mix?'warn':'ok'}">${mf.guansha_mix?'⚠ 官杀混杂，感情多变':'✓ 官杀清晰，感情稳定'}</span>`:''}
      ${mf.spouse_palace_conflict!=null?`<span class="chip ${mf.spouse_palace_conflict?'warn':'ok'}">${mf.spouse_palace_conflict?'⚠ 夫妻宫受冲':'✓ 夫妻宫稳固'}</span>`:''}
      ${mf.allow_interpret===false?`<span class="chip bad">⛔ 命局不建议深度解读婚姻</span>`:''}
    </div>
  </div>` : '';

  const loveWindowHtml = (json.marriage?.love_window||[]).length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:#f43f5e"></span>💑 婚恋时间窗口</p>
    <div class="row" style="flex-wrap:wrap;gap:8px">
      ${(json.marriage.love_window).map(w=>`<div class="chip ok" style="font-size:12px;padding:4px 10px">${esc(w.label||'')} <span style="color:var(--muted);font-size:11px">${w.age_from!=null?w.age_from+'–'+(w.age_to||'')+'岁':''}</span></div>`).join('')}
    </div>
  </div>` : '';

  el.innerHTML = heroHtml + profileHtml + loveWindowHtml + taohuaYearsHtml + childHtml + mfHtml + socialHintHtml9 + `
  ${ma.emotional_pitfalls?`<div class="card" style="margin-bottom:12px;border-left:3px solid var(--bad)"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>情感禁区</p><div style="font-size:13px;line-height:1.7">${renderPara(ma.emotional_pitfalls)}</div></div>`:''}
  ${ma.second_marriage_indicator?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>再婚 / 感情波折指标</p><div style="font-size:13px;line-height:1.7">${renderPara(ma.second_marriage_indicator)}</div></div>`:''}
  ${ma.inference_tags?.length?`<div class="card"><p class="card-title"><span class="dot"></span>分析标签</p><div class="row">${ma.inference_tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 10: 健康 (HealthAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab10(json, el) {
  const h = json.health||{};
  const score = h.health_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)';

  const heroHtml = `
  <div class="fortune-hero card" style="margin-bottom:12px">
    <div class="fh-score-block">
      <div class="fh-icon">♡</div>
      <div class="fh-score" style="color:${scoreColor}">${score!=null?score.toFixed(1):'—'}</div>
      <div class="fh-label">健康评分</div>
    </div>
    <div class="fh-body">
      ${h.risk_organs?.length
        ?`<div class="row" style="gap:4px;flex-wrap:wrap">${h.risk_organs.map(r=>`<span class="chip warn">⚠ ${esc(r)}</span>`).join('')}</div>`
        :'<div class="fh-fact fh-fact-ok">✓ 无明显高风险脏腑</div>'}
      ${h.risk_level?`<div class="fh-tier">风险等级：${h.risk_level}</div>`:''}
      ${score!=null?`<div class="fh-bar" style="margin-top:6px"><div class="fh-bar-fill" style="width:${Math.min(score,100)}%;background:linear-gradient(90deg,#22c55e,#86efac)"></div></div>`:''}
    </div>
  </div>`;

  // 五行默认器官（用于参考展示）
  const WX_DEFAULT_ORGANS = {'木':'肝·胆','火':'心·小肠','土':'脾·胃','金':'肺·大肠','水':'肾·膀胱'};
  const WX_EN = {'木':'wood','火':'fire','土':'earth','金':'metal','水':'water'};
  const organMapHtml = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>五行器官简表</p>
    <div class="organ-map">
      ${Object.entries(WX_DEFAULT_ORGANS).map(([cn, organs]) => {
        const isRisk = h.risk_organs?.some(r=>organs.includes(r)||r.includes(cn));
        return `<div class="organ-row wx-${WX_EN[cn]}" ${isRisk?'style="font-weight:600"':''}><span class="organ-elem">${cn}</span><span class="organ-name">${esc(organs)}</span>${isRisk?'<span class="chip warn" style="font-size:10px;padding:1px 5px;margin-left:4px">⚠</span>':''}</div>`;
      }).join('')}
    </div>
  </div>`;

  const hInferTagHtml = h.inference_tags?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>健康标签</p>
    <div class="row" style="flex-wrap:wrap">${h.inference_tags.map(t=>`<span class="chip${/风险|高|注意|警/.test(t)?' warn':''}">${/风险|高|注意|警/.test(t)?'⚠ ':''}${esc(t)}</span>`).join('')}</div>
  </div>` : '';

  el.innerHTML = heroHtml + hInferTagHtml + organMapHtml + `
  <div class="g2" style="margin-bottom:12px">
    <div class="card">
      <p class="card-title"><span class="dot"></span>养生建议</p>
      ${h.diet?.length?`<div style="margin-bottom:8px"><div class="advice-section-lbl">🍃 饮食</div><ul class="panel-list">${h.diet.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
      ${h.exercise?.length?`<div style="margin-bottom:8px"><div class="advice-section-lbl">🏃 运动</div><ul class="panel-list">${h.exercise.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
      ${h.health_advice?`<div><div class="advice-section-lbl">💡 综合建议</div><div style="font-size:12px;line-height:1.6;margin-top:4px">${txt(h.health_advice)}</div></div>`:''}
    </div>
    ${h.interpretation_text?`<div class="card"><p class="card-title"><span class="dot"></span>健康解读</p><div style="font-size:12px;line-height:1.6">${renderPara(h.interpretation_text)}</div></div>`:''}
  </div>
  ${h.peak_period?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>健康旺盛期</p><div style="font-size:13px">${txt(h.peak_period)}</div></div>`:''}
  ${(h.seasonal_health||h.mental_health_advice||h.constitution_type)?`
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>深度健康分析</p>
    ${h.constitution_type?`<div style="margin-bottom:10px"><div class="advice-section-lbl">🔬 体质辨识</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(h.constitution_type)}</div></div>`:''}
    ${h.seasonal_health?`<div style="margin-bottom:10px"><div class="advice-section-lbl">🌿 季节调养</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(h.seasonal_health)}</div></div>`:''}
    ${h.mental_health_advice?`<div><div class="advice-section-lbl">🧠 心理健康</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(h.mental_health_advice)}</div></div>`:''}
  </div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 11: 人际 (RelationshipAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab11(json, el) {
  const r = json.relationship||{};
  const nobles = r.noble_people||[];
  const pettys = r.petty_people||[];
  const score = r.relationship_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)';

  const heroHtml = score != null ? `
  <div class="fortune-hero card" style="margin-bottom:12px">
    <div class="fh-score-block">
      <div class="fh-icon">🤝</div>
      <div class="fh-score" style="color:${scoreColor}">${score.toFixed(0)}</div>
      <div class="fh-label">人际评分</div>
    </div>
    <div class="fh-body">
      ${r.inference_tags?.length?`<div class="row" style="flex-wrap:wrap;gap:4px">${r.inference_tags.slice(0,5).map(t=>`<span class="chip">${esc(t)}</span>`).join('')}</div>`:''}
      <div class="fh-bar" style="margin-top:8px"><div class="fh-bar-fill" style="width:${Math.min(score,100)}%;background:linear-gradient(90deg,var(--accent),#a78bfa)"></div></div>
    </div>
  </div>` : '';

  const peopleHtml = (nobles.length||pettys.length) ? `
  <div class="g2" style="margin-bottom:12px">
    ${nobles.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--ok)"></span>贵人方向</p><div class="people-grid">${nobles.map(p=>`<span class="ppl-chip ok">★ ${esc(p)}</span>`).join('')}</div></div>`:''}
    ${pettys.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>小人方向</p><div class="people-grid">${pettys.map(p=>`<span class="ppl-chip bad">✕ ${esc(p)}</span>`).join('')}</div></div>`:''}
  </div>` : '';

  /* 六亲解读（始终渲染, 不与 interpretation_text 互斥） */
  const _LQ_ICON = {'父':'👴','母':'👵','兄弟':'👬','姊妹':'👭','妻':'👫','夫':'💑',
    '子女':'🧒','子女(男)':'👦','子女(女)':'👧','子':'🧒','女':'👧','祖父':'🏛','祖母':'🏡'};
  const liuQinHtml = r.liu_qin && Object.keys(r.liu_qin).length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>六亲分析</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin-top:6px">
      ${Object.entries(r.liu_qin).map(([k,v])=>`
      <div style="padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;border:1px solid var(--line)">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
          <span style="font-size:18px">${_LQ_ICON[k]||'👤'}</span>
          <strong style="font-size:12px;color:var(--accent)">${esc(k)}</strong>
        </div>
        <div style="font-size:11px;line-height:1.65;color:var(--text)">${txt(v)}</div>
      </div>`).join('')}
    </div>
  </div>` : '';

  el.innerHTML = heroHtml + `
  ${r.interpretation_text?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>六亲关系</p><div style="font-size:13px;line-height:1.7">${renderPara(r.interpretation_text)}</div></div>`:''}
  ${liuQinHtml}
  ${peopleHtml}
  ${r.social_strategy?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>交际策略</p><div style="font-size:13px;line-height:1.7;padding-left:10px;border-left:2px solid var(--accent)">${txt(r.social_strategy)}</div></div>`:''}
  ${(()=>{const so11=json.social||{};return (so11.social_hint||so11.relation_conflict!==undefined)?`<div class="card"><p class="card-title"><span class="dot"></span>社交备注</p>${so11.social_hint?`<div style="font-size:13px;line-height:1.7;margin-bottom:6px">${txt(so11.social_hint)}</div>`:''} ${so11.relation_conflict!==undefined?`<div style="font-size:12px;color:${so11.relation_conflict?'var(--bad)':'var(--ok)'}">${so11.relation_conflict?'⚠ 命局有人际冲突倾向':'✓ 人际关系基础较顺'}</div>`:''}</div>`:''})()}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 12: 性格 (PersonalityModel)
═══════════════════════════════════════════════════ */
function renderTab12(json, el) {
  const p = json.personality||{};
  const dayStem = json.pillars_primary?.day?.stem || '—';
  const stemElem = (window.GAN_WUXING||{})[dayStem] || '';

  const stemHeroHtml = `
  <div class="bazi-overview" style="margin-bottom:12px">
    <span class="bov-tag">日主性格</span>
    <span class="bov-gan ${(window.GAN_CSS||{})[dayStem]||''}">${esc(dayStem)}</span>
    ${stemElem?`<span class="bov-elem-chip wx-${stemElem}">${typeof wxCN==='function'?wxCN(stemElem):stemElem}</span>`:''}
    ${p.inference_tags?.length?`<span class="bov-div">·</span>${p.inference_tags.slice(0,4).map(t=>`<span class="chip" style="font-size:11px">${esc(t)}</span>`).join('')}`:''}
  </div>`;

  el.innerHTML = stemHeroHtml + `
  ${p.interpretation_text||p.day_stem_trait?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>性格综述</p><div style="font-size:13px;line-height:1.7">${renderPara(p.interpretation_text||p.day_stem_trait)}</div>${p.strength_modifier?`<div style="font-size:11px;color:var(--muted);margin-top:6px">${txt('（'+p.strength_modifier+'）')}</div>`:''}</div>`:''}
  <div class="g2" style="margin-bottom:12px">
    ${p.advantages?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--ok)"></span>优势特质</p><ul class="pro-con-list">${p.advantages.map(s=>`<li class="pro-item">✓ ${esc(s)}</li>`).join('')}</ul></div>`:''}
    ${p.disadvantages?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>需注意之处</p><ul class="pro-con-list">${p.disadvantages.map(s=>`<li class="con-item">✕ ${esc(s)}</li>`).join('')}</ul></div>`:''}
  </div>
  ${p.growth_advice?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>成长建议</p><div style="font-size:13px;line-height:1.7">${renderPara(p.growth_advice)}</div></div>`:''}
  ${(p.communication_style||p.stress_coping_mode||p.potential_activation)?`
  <div class="card">
    <p class="card-title"><span class="dot"></span>性格深度维度</p>
    ${p.communication_style?`<div style="margin-bottom:10px"><div class="advice-section-lbl">💬 沟通风格</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(p.communication_style)}</div></div>`:''}
    ${p.stress_coping_mode?`<div style="margin-bottom:10px"><div class="advice-section-lbl">⚙ 压力应对</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(p.stress_coping_mode)}</div></div>`:''}
    ${p.potential_activation?`<div><div class="advice-section-lbl">✨ 潜能激活</div><div style="font-size:13px;line-height:1.7;margin-top:4px">${renderPara(p.potential_activation)}</div></div>`:''}
  </div>`:''}
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
      <div class="row" style="flex-wrap:wrap">${(f.auspicious_directions||[]).map(d=>`<span class="chip ok">↗ ${esc(d)}</span>`).join('')||'<span style="color:var(--muted);font-size:12px">建议结合实际房屋格局判断</span>'}</div>
      ${f.lucky_colors?.length?`<div style="margin-top:10px"><strong style="font-size:12px;color:var(--muted)">吉利颜色：</strong><div class="row" style="flex-wrap:wrap;margin-top:4px">${f.lucky_colors.map(c=>`<span class="chip">${esc(c)}</span>`).join('')}</div></div>`:''}
    </div>
    <div class="card">
      <p class="card-title"><span class="dot"></span>布局建议</p>
      ${f.decor?.length?`<ul class="panel-list">${f.decor.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:'<div class="hint">暂无</div>'}
    </div>
  </div>
  ${f.plants?.length||f.taboo?.length?`<div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>植物 & 注意事项</p>
    ${f.plants?.length?`<div class="row" style="margin-bottom:8px">${f.plants.map(p=>`<span class="chip">${esc(p)}</span>`).join('')}</div>`:''}
    ${f.taboo?.length?`<ul class="panel-list">${f.taboo.map(t=>`<li style="color:var(--bad)">${esc(t)}</li>`).join('')}</ul>`:''}
  </div>`:''}
  ${f.interpretation_text?`<div class="card"><p class="card-title"><span class="dot"></span>风水解读</p><div style="font-size:13px;line-height:1.7">${renderPara(f.interpretation_text)}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 14: 饰品 (JewelryModel, M4.05)
═══════════════════════════════════════════════════ */
function renderTab14(json, el) {
  const j = json.jewelry||{};

  // primary / secondary JewelryItemModel { material, gemstone, position, wuxing }
  const renderJewelItem = (item, label) => {
    if (!item) return '';
    const title = [item.material, item.gemstone].filter(Boolean).join('·');
    const detail = item.position ? `佩戴位置：${item.position}` : '';
    const wxTag  = item.wuxing   ? `<span class="chip" style="font-size:11px">${esc(item.wuxing)}</span>` : '';
    return `<div class="card">
      <p class="card-title"><span class="dot"></span>${label}</p>
      ${title?`<div style="font-size:14px;font-weight:600;margin-bottom:6px">💎 ${esc(title)}</div>`:''}
      ${wxTag}
      ${detail?`<div style="font-size:12px;color:var(--muted);margin-top:4px">${esc(detail)}</div>`:''}
    </div>`;
  };

  el.innerHTML = `
  <div class="g2" style="margin-bottom:12px">
    ${renderJewelItem(j.primary, '首选饰品')}
    ${renderJewelItem(j.secondary, '次选饰品')}
  </div>
  ${j.combination?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>搭配组合</p><div style="font-size:13px;line-height:1.6">${txt(j.combination)}</div></div>`:''}
  ${j.taboo?.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>禁忌饰品</p><div class="row">${j.taboo.map(t=>`<span class="chip bad">✕ ${esc(t)}</span>`).join('')}</div></div>`:''}
  ${j.interpretation_text?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>饰品解读</p><div style="font-size:13px;line-height:1.7">${renderPara(j.interpretation_text)}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 15: 开运 (LuckyModel + LifestyleModel)
═══════════════════════════════════════════════════ */
function renderTab15(json, el) {
  const lk = json.lucky||{};
  const ls = json.lifestyle||{};

  // 幸运数字 — 大砖格
  const numHtml = lk.lucky_numbers?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>幸运数字</p>
    <div class="lucky-num-grid">${lk.lucky_numbers.map(n=>`<div class="lucky-num">${n}</div>`).join('')}</div>
  </div>` : '';

  // 幸运颜色 — 色块 + 文字
  const COLOR_HEX = {'红':'#ef4444','橙':'#f97316','黄':'#eab308','绿':'#22c55e','青':'#06b6d4',
    '蓝':'#3b82f6','紫':'#a855f7','白':'#94a3b8','黑':'#334155','金':'#f59e0b',
    '棕':'#92400e','粉':'#f43f5e','灰':'#6b7280'};
  const getHex = c => Object.entries(COLOR_HEX).find(([k])=>c.includes(k))?.[1]||'var(--accent)';
  const colorHtml = lk.lucky_colors?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>幸运颜色</p>
    <div class="lucky-color-row">
      ${lk.lucky_colors.map(c=>`<div class="lucky-color-chip"><div class="lcc-swatch" style="background:${getHex(c)}"></div><div class="lcc-name">${esc(c)}</div></div>`).join('')}
    </div>
  </div>` : '';

  // 吉利方位 — lucky_direction 是单个字符串
  const DIR_SYM = {'东北':'↗','东南':'↘','西南':'↙','西北':'↖','东':'→','南':'↓','西':'←','北':'↑'};
  const getDirSym = d => Object.entries(DIR_SYM).find(([k])=>d.startsWith(k))?.[1]||'↗';
  const dirStr = lk.lucky_direction||'';
  const dirHtml = dirStr ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>吉利方位</p>
    <div class="row"><span class="chip ok" style="font-size:14px">${getDirSym(dirStr)} ${esc(dirStr)}</span></div>
  </div>` : '';

  el.innerHTML = numHtml + colorHtml + dirHtml + `
  ${lk.lucky_item?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>开运物品</p><div style="font-size:14px;font-weight:600">🔮 ${esc(lk.lucky_item)}</div></div>`:''}
  <div class="g2">
    ${ls.travel_direction?`<div class="card"><p class="card-title"><span class="dot"></span>出行建议</p><div style="font-size:13px">${txt(ls.travel_direction)}</div></div>`:''}
    ${ls.sleep_advice?`<div class="card"><p class="card-title"><span class="dot"></span>作息建议</p><div style="font-size:13px">${renderPara(ls.sleep_advice)}</div>${ls.best_times?`<div style="font-size:11px;color:var(--muted);margin-top:4px">最佳时段：${txt(ls.best_times)}</div>`:''}</div>`:''}
  </div>
  ${ls.diet?.length?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>饮食调养</p><ul class="panel-list">${ls.diet.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
  ${ls.exercise?.length?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>运动锻炼</p><ul class="panel-list">${ls.exercise.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div>`:''}
  ${ls.interpretation_text?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>生活方式综述</p><div style="font-size:13px;line-height:1.75">${renderPara(ls.interpretation_text)}</div></div>`:''}
  ${lk.interpretation_text?`<div class="card" style="margin-top:12px"><p class="card-title"><span class="dot"></span>开运综述</p><div style="font-size:13px;line-height:1.75">${renderPara(lk.interpretation_text)}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 16: 大运（可展开叙事 + 真实走势图 M4.08 + N5.07）
═══════════════════════════════════════════════════ */
// N5.07 前端六十甲子速算 (year 1984=甲子)
function _yearGanzhi(year) {
  const GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸'];
  const ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
  const idx = ((year - 4) % 60 + 60) % 60;
  return GAN[idx % 10] + ZHI[idx % 12];
}

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

  // N5.07: 顺/逆行方向
  const directionCN = dy.direction === 'forward' ? '顺行' : dy.direction === 'backward' ? '逆行' : '—';
  const startAgeHtml = dy.start_age != null ? `起运岁数：<strong>${dy.start_age}岁</strong>` : '';
  const directionHtml = dy.direction
    ? `<div class="k">行运方向</div><div><span class="chip ${dy.direction==='forward'?'ok':'warn'}">${directionCN}</span><span class="hint" style="margin-left:6px;font-size:11px" title="${txt(dy.direction_basis?.basis_text||dy.direction_basis?.summary||'')}">${txt(dy.direction_basis?.basis_text||dy.direction_basis?.summary||'')}</span></div>`
    : '';
  // 优先使用顶级精确起运年龄（如 0.7岁），fallback 到 DaYunModel 整数值
  const preciseStartAge = json.start_dayun_age ?? dy.start_age;

  el.innerHTML = singleModeNotice + `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>大运推算方法</p>
    <div class="kv">
      <div class="k">方法</div><div>${esc(dy.method||'—')}</div>
      <div class="k">边界</div><div>${esc(dy.boundary||'—')}</div>
      ${preciseStartAge != null ? `<div class="k">起运岁数</div><div><strong>${preciseStartAge}岁</strong>${dy.start_age_months?` (${dy.start_age_months}月)`:''}</div>` : ''}
      ${directionHtml}
      ${dy.anchor_jieqi_name?`<div class="k">参考节气</div><div>${esc(dy.anchor_jieqi_name)}${dy.anchor_jieqi_dt?` <span style="color:var(--muted);font-size:11px">(${esc(dy.anchor_jieqi_dt.slice(0,10))})</span>`:''}</div>`:''}
    </div>
  </div>
  <div id="dayunChartContainer" style="margin-bottom:16px"></div>
  <div class="dayun-table-wrapper" style="overflow-x:auto">
    <table class="dayun-table">
      <thead><tr><th>干支</th><th>起年</th><th>起岁</th><th>十神</th><th>财运</th><th>健康</th><th>感情</th><th>叙事/古籍</th></tr></thead>
      <tbody>
        ${items.map((d,di)=>{
          const cur = isCurrent(d);
          // N5.07: 流年展开行 (此行 data-dayun-idx 供 JS 展开用)
          const liunianRows = (() => {
            const sy = d.start_year;
            if (!sy) return '';
            // 优先用 json.liunian_detail 中的数据（适用于当前大运）
            const liunianSrc = cur ? (json.liunian_detail||[]) : [];
            const years = Array.from({length:10},(_,i)=>sy+i);
            const cells = years.map(y=>{
              const ld = liunianSrc.find(l=>l.year===y);
              const gz = ld ? (ld.ganzhi||(ld.stem||'')+(ld.branch||'')) : _yearGanzhi(y);
              const score = ld?.annual_score;
              const isCurYear = y===thisYear;
              // 构建四域预测 tooltip
              const df = ld?.domain_forecasts || {};
              const dfTooltip = ['财运','事业','婚恋','健康'].filter(k=>df[k]).map(k=>`${k}：${df[k]}`).join('\n');
              return `<td style="padding:3px 6px;text-align:center;white-space:nowrap${isCurYear?';font-weight:700;color:var(--accent)':''}" title="${dfTooltip?`${y}年四域预测\n${dfTooltip}`:''}">
                ${y}<br><span style="font-size:11px">${gz}</span>${score!=null?`<br><span style="font-size:10px;color:${score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)'}">${score}</span>`:''}
                ${dfTooltip?`<br><span style="font-size:9px;color:var(--muted)" title="${esc(dfTooltip)}">▦四域</span>`:''}
              </td>`;
            }).join('');
            return `<tr class="dayun-liunian-row" id="dayun-ln-${di}" style="display:none"><td colspan="8" style="padding:0"><div style="overflow-x:auto"><table style="font-size:11px;width:100%;border-collapse:collapse"><tbody><tr>${cells}</tr></tbody></table></div></td></tr>`;
          })();
          return `
          <tr class="${cur?'dayun-current':''}" style="cursor:pointer${cur?';border-left:3px solid var(--accent)':''}" data-toggle="dayun-ln-${di}" title="点击展开/收起流年">
            <td style="${cur?'padding-left:8px':''}"><div class="dayun-gz ${GAN_CSS[d.stem]||''}">${esc(d.stem||'')}${esc(d.branch||'')}</div>${cur?`<div style="font-size:10px;color:var(--accent);margin-top:2px;font-weight:700">▶ 当前大运</div>`:''}</td>
            <td>${d.start_year||'—'}</td>
            <td>${d.start_age!==undefined?d.start_age+'岁':'—'}</td>
            <td>${d.ten_god?`<span class="tengod-badge ${tenGodType(d.ten_god)}">${tenGodCN(d.ten_god)}</span>`:'—'}</td>
            <td>${d.wealth_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${txt(d.wealth_hint)}">${txt(d.wealth_hint)}</div>`:'—'}</td>
            <td>${d.health_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${txt(d.health_hint)}">${txt(d.health_hint)}</div>`:'—'}</td>
            <td>${d.love_hint?`<div style="font-size:11px;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${txt(d.love_hint)}">${txt(d.love_hint)}</div>`:'—'}</td>
            <td>
              ${d.narrative?`<details><summary style="cursor:pointer;font-size:11px;color:var(--accent)">查看叙事</summary><div style="font-size:12px;line-height:1.6;padding:8px;max-width:300px">${renderPara(d.narrative)}</div></details>`:''}  
              ${(d.refs&&d.refs.length)?`<details style="margin-top:4px"><summary style="cursor:pointer;font-size:11px;color:var(--accent-gold)">查看古籍引用</summary><div style="font-size:11px;line-height:1.7;padding:6px 8px;max-width:320px;font-style:italic;font-family:var(--font-title)">${d.refs.map(r=>`<div style="margin-bottom:4px"><span style="color:var(--accent-gold)">《${esc(r.source||'')}》</span>${txt(r.text||'')}</div>`).join('')}</div></details>`:''}
              ${d.child_hint?`<div style="margin-top:4px;font-size:11px;color:var(--muted)">👶 ${txt(d.child_hint)}</div>`:''}
              ${!d.narrative&&!(d.refs&&d.refs.length)&&!d.child_hint?'—':''}
            </td>
          </tr>${liunianRows}`;
        }).join('')||'<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无数据</td></tr>'}
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
  // 合并 liunian_detail（5年精细）与 yearly_fortune（10年简版）
  const liunianRich = json.liunian_detail||[];
  const liunianSimple = json.yearly_fortune||[];
  // 用 liunian_detail 覆盖 yearly_fortune 的重复年份
  const richYears = new Set(liunianRich.map(l=>l.year));
  const merged = [
    ...liunianRich,
    ...liunianSimple.filter(l=>!richYears.has(l.year)),
  ].sort((a,b)=>a.year-b.year);
  if (!merged.length) { el.innerHTML='<div class="hint" style="padding:16px">流年数据尚未计算。</div>'; return; }

  const thisYear = new Date().getFullYear();
  el.innerHTML = `
  <div class="liunian-timeline">
    ${merged.map(item => {
      const isCurrentYear = item.year === thisYear;
      const isFanTaisui = (item.tai_sui_relations?.length > 0) || item.fan_taisui || !!item.clash || false;
      const taisuiLabel = item.tai_sui_relations?.[0] || '';
      const gz = item.ganzhi || (item.stem||'')+(item.branch||'');
      return `
      <div class="liunian-item${isFanTaisui?' fan-taisui':''}${isCurrentYear?' liunian-current-year':''}">
        <div>
          <div class="liunian-year" style="${isCurrentYear?'color:var(--accent-red)':''}">\n            ${isCurrentYear?'<span style="font-size:10px;background:var(--accent-red);color:#fff;border-radius:4px;padding:1px 5px;margin-bottom:3px;display:block">▶ 今年</span>':''}
            ${item.year||'—'}</div>
          <div class="liunian-gz">${esc(gz)}</div>
          ${item.ten_god?`<div style="margin-top:4px"><span class="tengod-badge ${tenGodType(item.ten_god_code||item.ten_god)}">${tenGodCN(item.ten_god_code||item.ten_god)}</span></div>`:''}
          ${taisuiLabel?`<div style="font-size:10px;color:var(--bad);margin-top:3px">⚡ ${esc(taisuiLabel)}</div>`:''}
          ${item.clash?`<div style="font-size:10px;color:var(--bad);margin-top:3px">⚡ ${esc(item.clash)}</div>`:''}
        </div>
        <div>
          ${item.flow_wuxing?`<div style="margin-bottom:6px"><span style="font-size:11px;color:var(--muted)">流年五行：</span><strong>${esc(typeof wxCN==='function'?wxCN(item.flow_wuxing):item.flow_wuxing)}</strong></div>`:''}
          ${item.annual_score!==undefined?`<div style="margin-bottom:8px"><div style="font-size:11px;color:var(--muted);font-weight:700">年运评分</div><div style="font-size:18px;font-weight:800;color:${item.annual_score>=70?'var(--ok)':item.annual_score>=50?'var(--warn)':'var(--bad)'}">${item.annual_score}</div><div style="height:4px;background:var(--line);border-radius:2px;overflow:hidden;margin-top:2px"><div style="height:100%;width:${Math.min(item.annual_score,100)}%;border-radius:2px;background:${item.annual_score>=70?'var(--ok)':item.annual_score>=50?'var(--warn)':'var(--bad)'}">&nbsp;</div></div></div>`:''}
          ${item.domain_forecasts?`
          <div class="liunian-domains">
            ${['财运','事业','婚恋','健康'].map(k=>`
              <div class="liunian-domain">
                <div class="ld-label">${k}</div>
                <div class="ld-text">${txt(item.domain_forecasts[k]||'—')}</div>
              </div>`).join('')}
          </div>`:''}
          ${item.notable_months?.length?`<div style="margin-top:6px;font-size:11px;color:var(--muted)">重点月份：${item.notable_months.map(m=>`<span class="chip" style="font-size:10px;padding:1px 5px">${m}月</span>`).join('')}</div>`:''}
          ${item.clash_pillars?.length?`<div style="margin-top:5px;font-size:10px;color:var(--bad)">冲柱：${item.clash_pillars.map(c=>`<span class="chip bad" style="font-size:9px;padding:1px 4px">${esc(c)}</span>`).join('')}</div>`:''}
          ${item.optimal_action?`<div style="margin-top:6px;padding:4px 8px;background:var(--accent-gold-bg,rgba(224,139,0,0.08));border-radius:6px;font-size:11px"><span style="font-weight:700;color:var(--accent-gold)">📌 </span>${esc(item.optimal_action)}</div>`:''}
          ${item.inference_tags?.length?`<div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:3px">${item.inference_tags.map(t=>`<span class="chip" style="font-size:9px;padding:1px 5px">${esc(t)}</span>`).join('')}</div>`:''}
          ${item.interpretation_text?`<div style="margin-top:6px;font-size:11px;line-height:1.55;color:var(--muted)">${esc(item.interpretation_text.slice(0,60))}${item.interpretation_text.length>60?`…<details style="display:inline"><summary style="font-size:10px;color:var(--accent);cursor:pointer;margin-left:4px">全文</summary><div style="font-size:11px;line-height:1.65;padding:6px 8px;margin-top:4px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:6px;max-width:300px">${renderPara(item.interpretation_text)}</div></details>`:''}</div>`:''}
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
  if (!mf.length) { el.innerHTML='<div class="hint" style="padding:16px">月运数据尚未计算，请先完成排盘。</div>'; return; }
  const MONTHS = ['一','二','三','四','五','六','七','八','九','十','十一','十二'];
  // 月运五行色调映射（兼容旧文字键和新十六进制格式）
  const _colorMap = {'白/金':'#e2e8f0','绿/青':'#86efac','黑/蓝':'#93c5fd','红/紫':'#fca5a5','黄/棕':'#fde68a'};
  el.innerHTML = `
  <div class="month-disclaimer">⚠ 月运为大方向参考，吉凶判断受出生地精度、时辰误差等影响，请结合当下实际情况综合判断，不作为行动依据。</div>
  <div class="monthly-grid">
    ${mf.map((m,i)=>{
      const cls = m.luck_level==='吉'?'good':m.luck_level==='凶'?'bad':'neutral';
      const borderColor = _colorMap[m.color_hint] || (typeof m.color_hint==='string'&&m.color_hint.startsWith('#') ? m.color_hint : 'var(--line)');
      const gz = m.month_ganzhi || m.month_dizhi || '';
      const tgBadge = m.relation_to_rizhu
        ? `<div style="margin:2px 0"><span class="tengod-badge ${tenGodType(m.relation_to_rizhu)}" style="font-size:9px;padding:1px 4px">${tenGodCN(m.relation_to_rizhu)}</span></div>`
        : '';
      const dyCtx = m.dayun_stem ? `<div style="font-size:9px;color:var(--muted);margin-top:2px">${esc(m.dayun_stem)}运</div>` : '';
      return `
      <div class="month-item ${cls}" style="border-bottom:3px solid ${borderColor}">
        <div class="month-num">${MONTHS[i]||i+1}月</div>
        <div class="month-gz">${esc(gz)}</div>
        ${tgBadge}
        <div class="month-luck" style="font-size:11px;font-weight:700;color:${cls==='good'?'var(--ok)':cls==='bad'?'var(--bad)':'var(--muted)'}">${esc(m.luck_level||'平')}</div>
        <div class="month-hint">${txt(m.tip||'—')}</div>
        ${m.clash_with?`<div style="font-size:9px;color:var(--bad);margin-top:2px">冲：${esc(m.clash_with)}</div>`:''}
        ${dyCtx}
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
    <div class="profile-item" data-load-history-profile="${i}">
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
