/**
 * verify-render.js  v4.0.20260307
 * M4: 20个 Tab 渲染 / 命盘 / 五行 / 大运 / 流年 / 月运 / 总览 / 格局 / 命宫 等
 * @requires verify-core.js（必须先于本文件加载）
 * 全局依赖（由 verify-core.js 注入）: wxCN, GAN_CSS, GAN_DESC, _ZHI_ROLE
 */
;(function(){
'use strict';
console.log('[verify-render] version=20260312ZL loaded');

/* ── 便捷工具 ─────────────────────────────────── */
const $  = id => document.getElementById(id);
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const nn  = v => v === null || v === undefined ? '—' : v;
const pct = (v,total) => total ? Math.round(v/total*100) : 0;
// 以下与 verify-core.js 保持一致（两个 IIFE 作用域隔离，各自维护副本）
const cleanText = s => String(s||'').split('">').map(p=>p.trim()).filter(Boolean).join(' · ');
const txt       = s => esc(cleanText(s));
// 在 ASCII 数字/括号序列前后插入 <wbr>，提供断行机会（彻底解决溢出截断）
const wbr       = s => s.replace(/([【】\[\]]|(\d+(?:[.\-]\d+)*))/g, '<wbr>$1');
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
    renderTab20,
  ][id];
  if (fn && json) {
    const panel = document.querySelector(`[data-panel="${id}"] .panel-content`);
    if (panel) {
      try {
        fn(json, panel);
      } catch(e) {
        console.error(`[Tab ${id}] 渲染失败:`, e);
        panel.innerHTML = `<div style="padding:24px;text-align:center;color:var(--muted);font-size:13px">
          <div style="font-size:28px;margin-bottom:8px">⚠️</div>
          <div>此面板渲染出错，请刷新页面重试</div>
          <div style="font-size:11px;margin-top:4px;opacity:.6">${e.message||''}</div>
        </div>`;
      }
    }
  }
};

/* ══════════════════════════════════════════════════
   Tab 0: 总览 (M4.35)
═══════════════════════════════════════════════════ */
/* ──────────────────────────────────────────────────
   Tab 0：总览仪表板
   职责：命局核心速览 + 当年四域运势 + 行动建议摘要
         + 大运精简卡（进度/跳转）
   长内容（人生三阶段/命局详述/幸运元素）→ Tab5（摘要）
   大运详情（财/健/婚/子 4D）         → Tab16（大运）
────────────────────────────────────────────────── */
function renderTab0(json, el) {
  const arc  = json.life_arc;
  const cf   = json.current_fortune_summary;
  const thisYear = new Date().getFullYear();
  const liunianDetail = json.liunian_detail || [];
  const thisLiunian   = liunianDetail.find(l => l.year === thisYear) || liunianDetail[0];

  const p            = json.pillars_primary || {};
  const gejuName     = json.geju?.geju_name || json.geju?.name || '—';
  const gejuLevel    = json.geju?.geju_level || '';
  const gejuConf     = typeof json.geju?.confidence === 'number' ? Math.round(json.geju.confidence * 100) : null;
  const yongshenFavor = (json.yongshen?.favor || []).map(f => typeof wxCN === 'function' ? wxCN(f) : f).join('·') || '—';
  const yongshenAvoid = (json.yongshen?.avoid || []).map(f => typeof wxCN === 'function' ? wxCN(f) : f).join('·') || '';
  const yearScore    = thisLiunian?.annual_score;
  const scoreColor   = yearScore >= 80 ? '#16a34a' : yearScore >= 65 ? '#f59e0b' : yearScore >= 45 ? '#ea580c' : '#dc2626';
  const scoreBg      = yearScore >= 80 ? 'rgba(22,163,74,.08)' : yearScore >= 65 ? 'rgba(245,158,11,.08)' : yearScore >= 45 ? 'rgba(234,88,12,.08)' : 'rgba(220,38,38,.08)';
  const top3         = cf?.top3_actions || [];
  const _dyItems     = json.dayun?.items || [];
  const curDayunItem  = _dyItems.find(d => d.start_year <= thisYear && (d.start_year || 0) + 10 > thisYear) || _dyItems.slice(-1)[0] || null;
  const nextDayunItem = curDayunItem ? _dyItems.find(d => (d.start_year || 0) > (curDayunItem.start_year || 0)) : null;
  const dyProgress   = curDayunItem ? (() => {
    const elapsed = Math.max(0, thisYear - (curDayunItem.start_year || thisYear));
    return { elapsed, pct: Math.min(100, elapsed / 10 * 100) };
  })() : null;
  const wxWeak   = json.wuxing_weak  || [];
  const wxStrong = json.wuxing_strong || [];
  const _pers    = json.personality;
  const _sysTags = /^局[高中小]$|评分\d+|^流年$|^大运$/;
  const displayTags = (arc?.inference_tags || []).filter(t => !_sysTags.test(t));

  const tierBadge = tier => {
    const cls = tier === '局高' ? 'high' : tier === '局中' ? 'mid' : 'low';
    return `<span class="geju-tier-badge ${cls}">${esc(tier || '—')}</span>`;
  };

  /* ── 四柱速览 ────────────────────────────── */
  const pillarLabels = { year: '年', month: '月', day: '日', hour: '时' };
  const pillarsStrip = ['year', 'month', 'day', 'hour'].map(k => {
    const pl = p[k] || {};
    const isDay = k === 'day';
    const ganCls = GAN_CSS[pl.stem] || '';
    return `<div style="flex:1;text-align:center;padding:8px 4px;border-radius:8px;background:${isDay ? 'rgba(184,122,10,0.1)' : 'var(--bg2,rgba(0,0,0,0.04))'};${isDay ? 'border:1px solid rgba(184,122,10,0.3)' : ''}">
      <div style="font-size:9px;color:var(--muted);margin-bottom:2px">${pillarLabels[k]}</div>
      <div style="font-size:17px;font-weight:800;line-height:1.15" class="${ganCls}">${esc(pl.stem || '—')}</div>
      <div style="font-size:13px;font-weight:600">${esc(pl.branch || '—')}</div>
      ${isDay ? '<div style="font-size:9px;color:var(--accent-gold,#b87a0a);font-weight:700;margin-top:1px">日主</div>' : ''}
    </div>`;
  }).join('');

  /* ── 四域运势（2×2，吉凶背景色）────────── */
  const domains4Html = (thisLiunian?.domain_forecasts || cf?.this_year_domains) ? (() => {
    const DM = thisLiunian?.domain_forecasts || cf?.this_year_domains || {};
    const icons = { 财运: '💰', 事业: '⚡', 婚恋: '❤️', 健康: '🏥' };
    return ['财运', '事业', '婚恋', '健康'].map(k => {
      const val = DM[k] || '暂无';
      const bad  = /(注意|不佳|凶|差|衰|难|险|弱)/.test(val);
      const good = /(顺|旺|吉|好|升|进|佳)/.test(val);
      const bc   = bad ? 'var(--bad)' : good ? 'var(--ok)' : 'var(--line)';
      const bg   = bad ? 'rgba(220,38,38,.07)' : good ? 'rgba(22,163,74,.07)' : 'rgba(0,0,0,.03)';
      const firstDot = val.indexOf('。');
      const summary  = firstDot > 0 ? val.slice(0, firstDot + 1) : val;
      const rest     = firstDot > 0 ? val.slice(firstDot + 1).trim() : '';
      return '<div style="box-sizing:border-box;width:100%;padding:10px;border-radius:8px;background:' + bg + ';border-left:3px solid ' + bc + ';overflow:visible">'
        + '<div style="display:flex;align-items:center;gap:4px;margin-bottom:5px">'
        + '<span style="font-size:13px">' + icons[k] + '</span>'
        + '<span style="font-size:11px;font-weight:700;color:' + bc + '">' + k + '</span>'
        + (bad ? '<span style="margin-left:auto;font-size:9px;padding:1px 5px;border-radius:4px;background:rgba(220,38,38,.15);color:#dc2626;font-weight:700">注意</span>' : good ? '<span style="margin-left:auto;font-size:9px;padding:1px 5px;border-radius:4px;background:rgba(22,163,74,.15);color:#16a34a;font-weight:700">利好</span>' : '')
        + '</div>'
        + '<div class="domain-text" style="font-size:11px;line-height:1.5;word-break:break-all;overflow-wrap:anywhere;white-space:normal;overflow:visible;width:100%;box-sizing:border-box">' + wbr(esc(summary)) + '</div>'
        + (rest ? '<div style="margin-top:4px">'
          + '<div onclick="var n=this.nextElementSibling;var v=n.style.display===\'block\';this.textContent=v?\'展开 ▾\':\'收起 ▴\';n.style.display=v?\'none\':\'block\'" style="font-size:10px;color:var(--accent);cursor:pointer;user-select:none;padding:2px 0">展开 ▾</div>'
          + '<div class="domain-rest" style="display:none;font-size:11px;line-height:1.6;margin-top:4px;color:var(--text);word-break:break-all;overflow-wrap:anywhere;white-space:normal;overflow:visible;width:100%;max-width:100%;box-sizing:border-box">' + wbr(esc(rest)) + '</div>'
          + '</div>' : '')
        + '</div>';
    }).join('');
  })() : '';

  /* ── 流年主题（首句 + 重点月份 + 标签）── */
  const liunianInsightHtml = thisLiunian ? (() => {
    const parts = [];
    if (thisLiunian.interpretation_text) {
      const first = thisLiunian.interpretation_text.split(/[。！？]/).filter(Boolean)[0];
      if (first) parts.push(`<div style="font-size:12px;line-height:1.6;color:var(--text);margin-bottom:6px">${esc(first)}。</div>`);
    }
    if (thisLiunian.notable_months?.length) {
      parts.push(`<div style="font-size:11px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px;align-items:center">重点月份：${thisLiunian.notable_months.map(m => `<span class="chip ok" style="font-size:10px;padding:1px 6px">${m}月</span>`).join('')}</div>`);
    }
    if (thisLiunian.inference_tags?.length) {
      parts.push(`<div style="margin-top:5px;display:flex;flex-wrap:wrap;gap:3px">${thisLiunian.inference_tags.slice(0, 5).map(t => `<span class="chip" style="font-size:10px;padding:2px 6px">${esc(t)}</span>`).join('')}</div>`);
    }
    return parts.join('');
  })() : '';

  /* ── 行动建议（仅前 2 条 + 跳转 Tab5）── */
  const _oaSrc = arc?.optimal_action || thisLiunian?.optimal_action || '';
  const _oaHtml = _oaSrc ? (() => {
    const segs = _oaSrc.split('；').map(s => s.trim()).filter(Boolean);
    const shown = segs.slice(0, 2);
    const hasMore = segs.length > 2;
    const items = shown.map(s =>
      '<div class="oa-item" style="display:flex;align-items:flex-start;gap:6px;font-size:12px;line-height:1.8;padding:5px 0;border-bottom:1px solid var(--line);word-break:break-all;overflow-wrap:anywhere;white-space:normal">'
      + '<span style="color:var(--accent-gold,#b87a0a);font-size:15px;line-height:1.3;flex-shrink:0">•</span>'
      + '<span>' + wbr(esc(s)) + '</span></div>'
    ).join('');
    return '<div class="card" style="margin-bottom:12px;border-left:4px solid #b87a0a">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">'
      + '<div style="font-size:11px;font-weight:700;color:#b87a0a">📌 行动建议</div>'
      + (hasMore ? `<button data-switch-tab="5" style="font-size:10px;padding:2px 8px;background:transparent;border:1px solid var(--accent);color:var(--accent);border-radius:4px;cursor:pointer">全部 ${segs.length} 条 →</button>` : '')
      + '</div>' + items + '</div>';
  })() : '';

  /* ── 性格一句话 ─────────────────────────── */
  const persSnippet = _pers?.day_stem_trait
    ? `<div style="margin-top:8px;padding:8px 10px;background:rgba(99,102,241,.06);border-radius:8px;border-left:3px solid #6366f1;font-size:12px;line-height:1.6"><span style="font-size:11px;font-weight:700;color:#6366f1">👤 </span>${esc(_pers.day_stem_trait)}${_pers.strength_modifier ? `<span style="font-size:10px;color:var(--muted);margin-left:6px">${esc(_pers.strength_modifier)}</span>` : ''}</div>`
    : '';

  el.innerHTML = `
  <!-- ① 命局核心 -->
  <div class="card" style="margin-bottom:12px">
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:12px">${pillarsStrip}</div>
    <div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px">
      <div style="flex:1;min-width:120px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:2px">格局</div>
        <div style="font-size:14px;font-weight:700">${esc(gejuName)}${gejuLevel ? `<span style="font-size:11px;color:var(--muted);margin-left:4px">${esc(gejuLevel)}</span>` : ''}${gejuConf !== null ? `<span style="font-size:10px;color:var(--muted);margin-left:4px">${gejuConf}%</span>` : ''}${(gejuConf !== null && gejuConf < 50) ? '<span class="tag-uncertain">待定</span>' : ''}</div>
      </div>
      <div style="flex:1;min-width:100px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:2px">${yongshenAvoid ? '用神 · 忌神' : '用神'}</div>
        <div style="font-size:12px"><span style="color:var(--ok);font-weight:600">${esc(yongshenFavor)}</span>${yongshenAvoid ? `<span style="color:var(--muted);margin:0 4px">/</span><span style="color:var(--bad)">${esc(yongshenAvoid)}</span>` : ''}</div>
      </div>
      ${arc?.overall_tier ? `<div>${tierBadge(arc.overall_tier)}</div>` : ''}
      ${yearScore != null ? `<div style="text-align:center;min-width:52px;padding:4px 8px;border-radius:8px;background:${scoreBg}">
        <div style="font-size:26px;font-weight:800;line-height:1;color:${scoreColor}">${yearScore}</div>
        <div style="font-size:9px;color:var(--muted);margin-top:1px">${thisYear}年运</div>
        <div style="height:3px;background:var(--line);border-radius:2px;overflow:hidden;margin-top:3px"><div style="height:100%;width:${Math.min(yearScore, 100)}%;border-radius:2px;background:${scoreColor}"></div></div>
      </div>` : ''}
    </div>
    ${(wxWeak.length || wxStrong.length) ? `<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:5px;align-items:center">
      ${wxStrong.length ? `<span style="font-size:10px;color:var(--muted)">偏旺：</span>${wxStrong.map(f => `<span class="chip warn" style="font-size:10px;padding:1px 7px">${typeof wxCN === 'function' ? wxCN(f) : f}</span>`).join('')}` : ''}
      ${wxWeak.length ? `${wxStrong.length ? '<span style="color:var(--line)">|</span>' : ''}<span style="font-size:10px;color:var(--muted)">偏缺：</span>${wxWeak.map(f => `<span class="chip bad" style="font-size:10px;padding:1px 7px">${typeof wxCN === 'function' ? wxCN(f) : f}</span>`).join('')}` : ''}
    </div>` : ''}
    ${persSnippet}
    ${arc?.life_motto ? `<div style="margin-top:8px;padding:8px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;font-size:12px;font-style:italic;color:var(--muted)">"${txt(arc.life_motto)}"</div>` : ''}
    ${displayTags.length ? `<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">${displayTags.slice(0, 6).map(t => `<span class="chip" style="font-size:10px">${esc(t)}</span>`).join('')}</div>` : ''}
  </div>

  <!-- ② 当年四域运势 -->
  ${(domains4Html || liunianInsightHtml) ? `<div class="card" style="margin-bottom:12px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <div style="font-size:11px;color:var(--accent);font-weight:700">${thisYear}年运势${cf?.current_liunian ? ` · ${cf.current_liunian}` : thisLiunian?.ganzhi ? ` · ${thisLiunian.ganzhi}` : ''}</div>
      ${thisLiunian?.flow_wuxing ? `<span style="font-size:10px;padding:2px 7px;border-radius:5px;background:var(--bg2);color:var(--muted)">流年五行 ${typeof wxCN === 'function' ? wxCN(thisLiunian.flow_wuxing) : thisLiunian.flow_wuxing}</span>` : ''}
    </div>
    ${liunianInsightHtml ? `<div style="margin-bottom:10px;padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;border:1px solid var(--line)">${liunianInsightHtml}</div>` : ''}
    ${domains4Html ? `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;box-sizing:border-box">${domains4Html}</div>` : ''}
    ${(!_oaSrc && top3.length) ? `<ul style="margin:8px 0 0;padding-left:16px">${top3.slice(0, 3).map(a => `<li style="font-size:12px;line-height:1.5">${txt(a)}</li>`).join('')}</ul>` : ''}
  </div>` : ''}

  <!-- ③ 行动建议（前2条） -->
  ${_oaHtml}

  <!-- ④ 当前大运精简卡（进度 + 跳转，无4D详情） -->
  ${curDayunItem ? `<div class="card" style="margin-bottom:12px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
      <div style="font-size:11px;color:var(--accent);font-weight:700">▶ 当前大运</div>
      <button data-switch-tab="16" style="font-size:10px;padding:2px 8px;background:transparent;border:1px solid var(--accent);color:var(--accent);border-radius:4px;cursor:pointer">详情 →</button>
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <div class="dayun-gz ${GAN_CSS[curDayunItem.stem] || ''}" style="font-size:18px;padding:6px 10px;flex-shrink:0">${esc(curDayunItem.stem || '')}${esc(curDayunItem.branch || '')}</div>
      <div style="flex:1">
        <div style="font-size:12px">${curDayunItem.start_year || '?'}–${(curDayunItem.start_year || 0) + 10}年 · ${curDayunItem.start_age || '?'}–${(curDayunItem.start_age || 0) + 10}岁</div>
        ${curDayunItem.ten_god ? `<div style="margin-top:3px"><span class="tengod-badge ${typeof tenGodType === 'function' ? tenGodType(curDayunItem.ten_god) : ''}">${typeof tenGodCN === 'function' ? tenGodCN(curDayunItem.ten_god) : curDayunItem.ten_god}</span></div>` : ''}
        ${nextDayunItem ? `<div style="font-size:10px;color:var(--muted);margin-top:4px">下运：${esc((nextDayunItem.stem || '') + (nextDayunItem.branch || ''))} ${nextDayunItem.start_year || ''}年起（${nextDayunItem.start_age || '?'}–${(nextDayunItem.start_age || 0) + 10}岁）</div>` : ''}
      </div>
    </div>
    ${dyProgress ? `<div style="background:var(--bg2,rgba(0,0,0,0.07));border-radius:4px;height:6px;overflow:hidden"><div style="height:100%;width:${dyProgress.pct}%;background:var(--accent);border-radius:4px"></div></div>
    <div style="font-size:10px;color:var(--muted);margin-top:4px;text-align:right">已走 ${dyProgress.elapsed} 年${cf?.dayun_years_remaining != null ? ` · 剩余 ${cf.dayun_years_remaining} 年` : ' / 10 年'}</div>` : ''}
  </div>` : ''}

  <!-- ⑤ 快捷导航 -->
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px">
    <button data-switch-tab="2" style="font-size:12px">✦ 命盘</button>
    <button data-switch-tab="7" style="font-size:12px">💰 财运</button>
    <button data-switch-tab="8" style="font-size:12px">⚡ 事业</button>
    <button data-switch-tab="9" style="font-size:12px">❤️ 姻缘</button>
    <button data-switch-tab="5"  style="font-size:12px">📋 摘要</button>
    <button id="btn-history-drawer" class="no-print" style="font-size:12px">📂 历史</button>
  </div>
  <div style="font-size:10px;color:var(--muted);text-align:center;padding:4px 0">⚠ 仅供参考，不作为任何决策依据。</div>
  `;
  $('btn-history-drawer')?.addEventListener('click', () => { $('historyDrawer')?.classList.toggle('open'); if (typeof renderHistoryDrawer === 'function') renderHistoryDrawer(); });
}

/* ══════════════════════════════════════════════════
   Tab 1: 请求（表单已在 HTML 中，仅补充历史渲染）
═══════════════════════════════════════════════════ */
function renderTab1(json, el) {
  const level       = json.validation?.level || '?';
  const warnings    = json.validation?.warnings || [];
  const rid         = json.request_id || '—';
  const p           = json.pillars_primary || {};
  const dayStem     = p.day?.stem || '—';
  const gejuName    = json.geju?.geju_name || json.geju?.name || '—';
  const yongshen    = (json.yongshen?.favor || []).join(' / ') || '—';
  const _thisYear   = new Date().getFullYear();
  const lnNow       = (json.liunian_detail || []).find(l => l.year === _thisYear);
  const annualScore = lnNow?.annual_score ?? null;
  const scoreCls    = annualScore != null ? (annualScore >= 70 ? 'ok' : annualScore >= 50 ? 'warn' : 'bad') : '';
  const levelCls    = level === 'L0' ? 'ok' : level === 'L1' ? 'warn' : 'bad';

  const warnHtml = warnings.length
    ? `<details style="margin-top:8px">
        <summary style="font-size:12px;cursor:pointer;color:var(--warn);font-weight:700;user-select:none">⚠ ${warnings.length} 条告警</summary>
        <div style="margin-top:6px;display:flex;flex-direction:column;gap:4px">
          ${warnings.map(w => `<div style="font-size:11px;color:var(--muted);padding:4px 8px;background:rgba(245,158,11,.07);border-radius:6px;border-left:2px solid var(--warn)">${esc(w.message || String(w))}</div>`).join('')}
        </div>
      </details>`
    : `<div style="margin-top:6px;font-size:11px;color:var(--ok)">✓ 无告警</div>`;

  const el2 = el.querySelector('#reqResult');
  if (!el2) return;
  el2.innerHTML = `
    <div style="border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--panel);margin-top:8px">
      <div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px">
        <span class="level-badge ${levelCls}">${esc(level)}</span>
        ${annualScore != null ? `<span class="tag ${scoreCls}" title="${_thisYear}年运势分">本年 ${annualScore}分</span>` : ''}
        <span style="font-size:11px;color:var(--muted);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(rid)}">${esc(rid)}</span>
        <button data-copy-text="${esc(rid)}" style="font-size:11px;padding:3px 8px" title="复制 request_id">复制ID</button>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">
        <div style="padding:7px 10px;background:var(--bg2,rgba(0,0,0,.04));border-radius:8px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:2px">日主</div>
          <div style="font-weight:800;font-size:15px">${esc(dayStem)}</div>
        </div>
        <div style="padding:7px 10px;background:var(--bg2,rgba(0,0,0,.04));border-radius:8px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:2px">格局</div>
          <div style="font-weight:700;font-size:11px;line-height:1.4">${esc(gejuName)}</div>
        </div>
        <div style="padding:7px 10px;background:var(--bg2,rgba(0,0,0,.04));border-radius:8px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:2px">用神</div>
          <div style="font-weight:700;font-size:11px">${esc(yongshen)}</div>
        </div>
      </div>
      ${warnHtml}
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;padding-top:10px;border-top:1px solid var(--line);align-items:center">
        <span style="font-size:11px;color:var(--muted)">查看详情：</span>
        <button data-switch-tab="2"  style="font-size:11px;padding:4px 10px">命盘</button>
        <button data-switch-tab="3"  style="font-size:11px;padding:4px 10px">格局</button>
        <button data-switch-tab="5"  style="font-size:11px;padding:4px 10px">摘要</button>
        <button data-switch-tab="16" style="font-size:11px;padding:4px 10px">大运</button>
        <button data-switch-tab="17" style="font-size:11px;padding:4px 10px">流年</button>
        <button data-switch-tab="20" style="font-size:11px;padding:4px 10px">紫微</button>
      </div>
    </div>`;
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

  // ── 当前大运 banner ──────────────────────────
  const _thisYear2 = new Date().getFullYear();
  const _curDY2 = (json.dayun?.items||[]).find(d=>d.start_year<=_thisYear2&&(d.start_year||0)+10>_thisYear2)||null;
  const dayunBannerHtml = _curDY2 ? `
  <div style="margin-bottom:12px;padding:8px 14px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:10px;display:flex;align-items:center;flex-wrap:wrap;gap:10px;border-left:3px solid var(--accent)">
    <span style="font-size:11px;color:var(--accent);font-weight:700">▶ 当前大运</span>
    <span style="font-size:16px;font-weight:800;letter-spacing:2px;color:var(--text)">${esc((_curDY2.stem||'')+(_curDY2.branch||''))}</span>
    ${_curDY2.start_year?`<span style="font-size:11px;color:var(--muted)">${_curDY2.start_year}–${_curDY2.start_year+9}年 · <button data-switch-tab="16" style="font-size:11px;padding:2px 6px">查看大运详情</button></span>`:''}
    ${_curDY2.wealth_hint?`<span style="font-size:11px;color:var(--ok);flex:1;min-width:160px" title="${esc(_curDY2.wealth_hint)}">💰 ${esc(_curDY2.wealth_hint.length>42?_curDY2.wealth_hint.slice(0,42)+'…':_curDY2.wealth_hint)}</span>`:''}
  </div>` : '';

  /* ── 强弱诠释文字 ─────────────────────────────── */
  const TIER_INSIGHT = {
    extremely_strong: '日主太旺，命局偏强。用神宜取财星、官杀耗泄，忌印绶比劫再扶。',
    strong:           '日主身强，喜财官食伤耗泄，逢财官大运多可建功立业。',
    balanced:         '日主中和，命局最为理想，用神随时势灵活调配，进退有据。',
    neutral:          '日主中和，命局最为理想，用神随时势灵活调配，进退有据。',
    weak:             '日主身弱，喜印绶、比劫帮扶，忌财官消耗；扶助之运易出成绩。',
    extremely_weak:   '日主极弱，宜察是否属从格；非从格须大力扶助，方向用神有别。<button class="tier-geju-link" data-switch-tab="3">→ 查看格局</button>',
  };
  const tierInsight = TIER_INSIGHT[st.tier] || '';

  /* ── 注释辅助函数 ───────────────────────────── */
  const helpBanner = (html) => `<div class="help-note" style="font-size:11px;color:var(--muted);background:rgba(99,102,241,.05);border-radius:6px;padding:7px 11px;margin:4px 0 10px;border-left:2px solid rgba(99,102,241,.4);line-height:1.65;overflow:visible;height:auto;max-height:none;white-space:normal;word-break:break-all;overflow-wrap:anywhere;width:100%;box-sizing:border-box">${html}</div>`;

  /* ── 十神释义表 ─────────────────────────────── */
  const TG_EXPLAIN = {
    zheng_guan: '正官：规矩法度·官运权威。身强者大利，身弱者易感压制',
    pian_guan:  '七杀（偏官）：竞争压力·进取开拓。需制化，过旺则伤身',
    zheng_yin:  '正印：贵人保护·文书学问。利印绶之运，主稳健涵养',
    pian_yin:   '偏印（枭神）：偏门技艺·直觉灵感。见食神时须防枭夺食',
    zheng_cai:  '正财：稳定财富·配偶缘。务实勤劳，主理财守业',
    pian_cai:   '偏财：意外之财·父缘。灵活逐利，主投机商运',
    shi_shen:   '食神：才华输出·口福享乐。创造力强，利子女艺术',
    shang_guan: '伤官：才华外发·叛逆创新。主聪慧但易犯官非，需善用',
    bi_jian:    '比肩：兄弟朋友·自立自主。主独立，身弱时互助，身强时竞争',
    jie_cai:    '劫财：争夺竞争·拼搏冒险。主魄力，但防财散人离',
    ri_zhu:     '日主：代表命主本身，此柱不另论十神',
  };

  /* ── 十神释义展开行（四柱十神说明） ─────────── */
  const tgLegendHtml = (() => {
    const codes = ['hour','month','year'].map(k => tg[k]).filter(Boolean);
    if (!codes.length) return '';
    const uniq = [...new Set(codes)];
    const rows = uniq.map(code => {
      const desc = TG_EXPLAIN[code] || '';
      if (!desc) return '';
      const cn   = typeof tenGodCN   === 'function' ? tenGodCN(code)   : code;
      const type = typeof tenGodType === 'function' ? tenGodType(code) : '';
      return `<div style="display:flex;align-items:baseline;gap:7px;margin-bottom:5px">
        <span class="tengod-badge ${type}" style="font-size:10px;white-space:nowrap;flex-shrink:0">${esc(cn)}</span>
        <span style="font-size:11px;color:var(--muted);line-height:1.55">${esc(desc)}</span>
      </div>`;
    }).filter(Boolean).join('');
    if (!rows) return '';
    return `<details style="margin-top:6px">
      <summary style="font-size:11px;color:var(--muted);cursor:pointer;user-select:none;padding:4px 2px">📌 十神释义（点击展开）</summary>
      <div style="margin-top:6px;padding:9px 12px;background:rgba(0,0,0,.03);border-radius:6px">${rows}</div>
    </details>`;
  })();

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
  ${dayunBannerHtml}
  ${overviewHtml}

  <!-- 四柱排盘 -->
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot"></span>四柱排盘
      <span class="card-title-sub">时｜日｜月｜年（从左到右）</span>
    </p>
    ${helpBanner('📖 <strong>读盘指引：</strong>每柱上方为<strong>天干</strong>（甲乙丙丁…十干），下方为<strong>地支</strong>（子丑寅卯…十二支）。<strong>日柱天干即日主</strong>，代表命主本人。<em>藏干</em>是地支所含天干（悬停可查本气/中气/余气）。卡片底部色块为该柱天干与日主的<strong>十神</strong>关系，反映该领域与命主的互动方式。<em>纳音</em>为六十甲子对应的音律名称（如"石榴木"），供古法辅助参考。')}
    <div class="pillar-cards">${pillarsCards}</div>
    ${tgLegendHtml}
    <div class="pillar-footnote">
      《三命通会》《子平真诠》 · 节气历：sxtwl VSOP87 · 藏干：子平通行版（悬停查看）
    </div>
  </div>

  <!-- 五行偏重警示 -->
  ${(()=>{const wxArr=[['wood',wx.wood||0],['fire',wx.fire||0],['earth',wx.earth||0],['metal',wx.metal||0],['water',wx.water||0]];const tot=wxArr.reduce((s,[,v])=>s+v,0);const dom=wxArr.filter(([,v])=>tot&&v/tot>0.45);return dom.length?`<div style="margin-bottom:12px;padding:7px 12px;background:rgba(192,57,43,0.06);border-radius:8px;border-left:3px solid var(--bad);font-size:12px"><span style="color:var(--bad);font-weight:700">⚠ 命局偏重：</span>${dom.map(([k])=>`<span class="wx-${k}" style="font-weight:700">${{wood:'木',fire:'火',earth:'土',metal:'金',water:'水'}[k]}</span>`).join('+')} 偏旺，注意用神调候。</div>`:'';})()
  }

  <!-- 五行格局 ｜ 日主分析 -->
  <div class="g2" style="margin-bottom:14px">

    <!-- 左：五行格局 -->
    <div class="card">
      <p class="card-title"><span class="dot"></span>五行格局</p>
      ${helpBanner('🌱 <strong>五行</strong>（木/火/土/金/水）代表五种能量，命局越均衡越稳健。<strong>用神</strong>是命局最需补充的五行，大运流年逢用神方向大利；<strong>忌神</strong>与用神相克或形成消耗，宜回避。<em>均衡分</em>越高表示五行越平均（满分100分，&gt;70属优秀）。')}
      <div class="wx-bar-wrap" style="margin-top:10px">${wxBars}</div>
      <div id="wuxingRingContainer" style="margin-top:14px"></div>
      ${favorChips||avoidChips ? `
      <div class="yn-section">
        ${favorChips ? `
        <div class="yn-row"><span class="yn-lbl-ok">▲ 用神</span><span class="yn-chips">${favorChips}</span></div>
        <div class="help-note" style="font-size:10.5px;color:var(--muted);padding:3px 4px 7px;line-height:1.6">大运/流年逢<strong>用神五行</strong>十年段整体顺畅，行业/环境/颜色偏向用神方向有益。</div>` : ''}
        ${avoidChips ? `
        <div class="yn-row"><span class="yn-lbl-bad">▼ 忌神</span><span class="yn-chips">${avoidChips}</span></div>
        <div class="help-note" style="font-size:10.5px;color:var(--muted);padding:3px 4px 7px;line-height:1.6">大运/流年逢<strong>忌神五行</strong>宜守成谨慎，减少大额投资或重大变动。</div>` : ''}
        ${yn.rationale ? `<div class="yn-rationale">${renderPara(yn.rationale)}</div>` : ''}
      </div>` : ''}
      ${(json.wuxing_weak?.length||json.wuxing_strong?.length||json.balance_advice||json.wuxing_balance_score!=null) ? `
      <div class="yn-section" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px">
        ${json.wuxing_balance_score!=null ? (() => {
          const s = json.wuxing_balance_score||0;
          const tier = s>=70 ? ['ok','优秀','五行分布较为均衡，整体命局稳健，运势起伏温和。']
                     : s>=55 ? ['warn','良好','五行略有偏差，整体仍属平稳，注意用神方向即可。']
                     : s>=40 ? ['warn','一般','五行偏差明显，需借大运/流年补充偏缺五行来平衡格局。']
                     :         ['bad', '偏弱','五行悬殊较大，命局需强力调候，用神方向非常关键。'];
          return `<div style="margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
              <span style="font-size:11px;color:var(--muted);font-weight:700">五行均衡分</span>
              <span class="level-badge ${tier[0]}" style="font-size:10px;padding:1px 8px">${tier[1]}</span>
              <span style="font-size:11px;color:var(--muted)">${s.toFixed(1)} / 100</span>
            </div>
            <div class="strength-meter" style="height:8px">
              <div class="strength-meter-fill ${tier[0]}" style="width:${Math.min(100,s)}%"></div>
            </div>
            <div style="font-size:10.5px;color:var(--muted);margin-top:5px;line-height:1.55;border-left:2px solid rgba(99,102,241,.25);padding-left:8px">
              ℹ ${tier[2]}<br>满分100分：&gt;70 优秀 · 55–70 良好 · 40–55 一般 · &lt;40 偏弱
            </div>
          </div>`;
        })() : ''}
        ${json.wuxing_weak?.length ? `
        <div class="yn-row">
          <span class="yn-lbl-bad" style="font-size:11px">偏缺</span>
          <span class="yn-chips">${json.wuxing_weak.map(f=>`<span class="chip bad">${typeof wxCN==='function'?wxCN(f):f}</span>`).join('')}</span>
        </div>
        <div class="help-note" style="font-size:10.5px;color:var(--muted);line-height:1.6;padding:4px 6px 6px;overflow:visible;height:auto;max-height:none;white-space:normal;word-break:break-all;overflow-wrap:anywhere;width:100%;box-sizing:border-box">
          命局缺少此五行能量。可通过<strong>颜色</strong>（穿戴偏缺五行对应色）、<strong>环境方位</strong>（如水属北方对应蓝黑）、<strong>行业偏向</strong>及大运流年来补充——逢偏缺五行之大运往往有转机。
        </div>` : ''}
        ${json.wuxing_strong?.length ? `
        <div class="yn-row" style="margin-top:4px">
          <span class="yn-lbl-ok" style="font-size:11px">偏旺</span>
          <span class="yn-chips">${json.wuxing_strong.map(f=>`<span class="chip warn">${typeof wxCN==='function'?wxCN(f):f}</span>`).join('')}</span>
        </div>
        <div class="help-note" style="font-size:10.5px;color:var(--muted);line-height:1.6;padding:4px 6px 6px;overflow:visible;height:auto;max-height:none;white-space:normal;word-break:break-all;overflow-wrap:anywhere;width:100%;box-sizing:border-box">
          命局此五行偏旺，相应特质（如火旺性急、金旺执拗）较突出。大运流年再逢同五行宜守成；逢相克五行反可耗旺调候——此时用神方向格外关键。
        </div>` : ''}
        ${json.balance_advice ? `<div class="tier-insight" style="margin-top:8px">💡 ${esc(json.balance_advice)}</div>` : ''}
      </div>` : ''}
    </div>

    <!-- 右：日主分析 -->
    <div class="card">
      <p class="card-title"><span class="dot"></span>日主分析</p>
      ${helpBanner('⚖ <strong>强弱分值参考（满分6.0）：</strong>≤2.0 极弱 · 2.0–2.8 身弱 · 2.8–3.5 中和（最稳健）· 3.5–4.5 身强 · ≥4.5 极强。<strong>身强</strong>宜以财、官杀、食伤来耗泄日主；<strong>身弱</strong>宜以印绶、比劫来扶助日主；<strong>中和</strong>最为理想，可顺势灵活调配。')}
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

  if (dzRels.length || tgClashes.length) {
    const REL_ICON = {
      '三合':'◎','六合':'○','半合':'◑','三会':'●',
      '冲':'↔','三刑':'✕','自刑':'×','刑':'⊗','害':'⊘','破':'⊡',
    };
    const _REL_MEANING = {
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
    const _TG_MEANING = {
      '克': c => `天干相克（${(c.positions||c.stems||[]).join('→')}）——两干对立，主内部消耗，防竞争内耗`,
      '合': c => `天干相合化${c.element||'?'}——调和但失本气，合中有制`,
    };
    const makeRelRow = (r, isTg) => {
      const relType  = r.type || '';
      const isHarm   = /冲|刑|害|破|克/.test(relType);
      const matchKey = isTg
        ? Object.keys(_TG_MEANING).find(k => relType.includes(k))
        : Object.keys(_REL_MEANING).find(k => relType.includes(k));
      const chars = (isTg ? (r.stems||[]) : (r.branches||[])).map(c=>esc(c)).join('');
      const icon  = REL_ICON[matchKey||relType] || (isHarm ? '⊗' : '○');
      const desc  = matchKey
        ? (isTg ? _TG_MEANING[matchKey](r) : _REL_MEANING[matchKey](r))
        : relType;
      return `<div class="rel-row">
        <span class="rel-icon ${isHarm?'rel-icon-bad':'rel-icon-ok'}">${icon}</span>
        <span class="chip ${isHarm?'bad':'ok'} rel-chip">${chars} ${esc(relType)}</span>
        <span class="rel-desc">${esc(desc)}</span>
      </div>`;
    };
    const relRows   = dzRels.map(r => makeRelRow(r, false)).join('');
    const clashRows = tgClashes.map(c => makeRelRow(c, true)).join('');
    const relCard = document.createElement('div');
    relCard.className = 'card';
    relCard.style.marginBottom = '14px';
    relCard.innerHTML = `
      <p class="card-title">
        <span class="dot"></span>
        ${dzRels.length >= 3 ? '<span class="rel-star">★</span>' : ''}干支互动
        <span class="card-title-sub">地支 ${dzRels.length} 条${tgClashes.length ? ` · 天干 ${tgClashes.length} 条` : ''}</span>
      </p>
      ${helpBanner('🔗 <strong>合</strong>（三合/六合/三会）为聚力，主合作顺利·感情婚事；<strong>冲</strong>为破力，主变动迁移·开拓改变；<strong>刑</strong>主是非官非；<strong>害/破</strong>主小损·人际暗耗。大运/流年逢相同关系时效果尤甚——冲动忌神反利，冲动用神宜慎。')}
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

  /* ── 命局综合总评 (bazi_summary) ──────────────── */
  if (json.bazi_summary) {
    const _summaryCard = document.createElement('details');
    _summaryCard.className = 'card';
    _summaryCard.style.marginBottom = '14px';
    const _summaryPreview = cleanText(json.bazi_summary).slice(0, 100);
    _summaryCard.innerHTML = `
      <summary>
        <span class="dot"></span>
        <span style="font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.07em">命局综合总评</span>
        <span style="flex:1;font-size:11px;color:var(--muted);font-weight:400;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-left:8px">${esc(_summaryPreview)}…</span>
      </summary>
      <div class="card-body">
        <div style="font-size:13px;line-height:1.85">${renderPara(json.bazi_summary)}</div>
      </div>
    `;
    el.appendChild(_summaryCard);
  }

  /* ── 日主性格速览 (personality) ──────────────── */
  const _pers = json.personality;
  if (_pers) {
    const _advHtml = (_pers.advantages||[]).slice(0,4).map(s =>
      `<div style="padding:5px 10px;background:rgba(22,163,74,.07);border-radius:7px;border-left:3px solid var(--ok);font-size:12px;line-height:1.5">✓ ${esc(s)}</div>`
    ).join('');
    const _disHtml = (_pers.disadvantages||[]).slice(0,4).map(s =>
      `<div style="padding:5px 10px;background:rgba(220,38,38,.07);border-radius:7px;border-left:3px solid var(--bad);font-size:12px;line-height:1.5">✕ ${esc(s)}</div>`
    ).join('');
    const _persCard = document.createElement('details');
    _persCard.className = 'card';
    _persCard.style.marginBottom = '14px';
    _persCard.innerHTML = `
      <summary>
        <span class="dot" style="background:var(--accent-gold,#b8860b)"></span>
        <span style="font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.07em">性格特质</span>
        ${_pers.strength_modifier ? `<span class="card-title-sub">${esc(_pers.strength_modifier)}</span>` : ''}
        ${(_pers.inference_tags||[]).slice(0,3).map(t=>`<span class="chip" style="font-size:10px;padding:2px 7px">${esc(t)}</span>`).join('')}
      </summary>
      <div class="card-body">
        ${_pers.day_stem_trait ? `<div class="tier-insight" style="margin-bottom:10px">📌 ${txt(_pers.day_stem_trait)}</div>` : ''}
        ${_advHtml ? `<div style="font-size:11px;color:var(--ok);font-weight:700;margin-bottom:5px;letter-spacing:.04em">▲ 优势特质</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:5px;margin-bottom:12px">${_advHtml}</div>` : ''}
        ${_disHtml ? `<div style="font-size:11px;color:var(--bad);font-weight:700;margin-bottom:5px;letter-spacing:.04em">▼ 注意之处</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:5px;margin-bottom:12px">${_disHtml}</div>` : ''}
        ${_pers.growth_advice ? `<div class="tier-insight">💡 成长建议：${txt(_pers.growth_advice)}</div>` : ''}
        ${_pers.communication_style ? `<div style="font-size:12px;color:var(--muted);margin-top:8px;line-height:1.6">💬 沟通风格：${txt(_pers.communication_style)}</div>` : ''}
        <div style="margin-top:10px;text-align:right">
          <button data-switch-tab="12" style="font-size:11px;padding:3px 10px">查看完整性格分析 →</button>
        </div>
      </div>
    `;
    el.appendChild(_persCard);
  }

  /* ── 神煞速览 (A级) ──────────────────────────── */
  const _ssAll = json.shensha || [];
  const _ssA   = _ssAll.filter(s => s.priority === 'A');
  if (_ssA.length) {
    const _ssAOk  = _ssA.filter(s =>  s.is_beneficial);
    const _ssABad = _ssA.filter(s => !s.is_beneficial);
    const _makeSsGrp = (items, label, cls) => {
      if (!items.length) return '';
      const chips = items.map(s => {
        const sn = chipName(s.name || '');
        const pc = {year:'年',month:'月',day:'日',hour:'时'}[s.pillar] || '';
        const tt = [chipTitle(s.name||''), txt(s.meaning||'')].filter(Boolean).join('\n');
        return `<span class="ss-chip ${cls}" title="${tt}">${s.is_star?'★ ':''}<strong>${sn}</strong>${pc?` <small class="hint">${pc}</small>`:''}</span>`;
      }).join('');
      return `<div class="ss-group"><div class="ss-group-lbl ${cls}">${label}</div><div class="ss-chips">${chips}</div></div>`;
    };
    const _ssCard = document.createElement('div');
    _ssCard.className = 'card';
    _ssCard.style.marginBottom = '14px';
    _ssCard.innerHTML = `
      <p class="card-title">
        <span class="dot"></span>命局神煞
        <span class="card-title-sub">A级 ${_ssA.length} 种 · <button data-switch-tab="4" style="font-size:11px;padding:1px 7px">查看全部</button></span>
      </p>
      ${helpBanner('✨ <strong>神煞</strong>是古命理对特定干支组合的定性标记（不同于五行计算）。<strong>A级吉神</strong>（如天乙贵人、文昌、华盖）增益相应领域运势；<strong>A级凶煞</strong>（如羊刃、七杀星、孤辰寡宿）需结合整体格局判断——有制化者凶可化吉。<em>悬停各徽章</em>可查看具体含义与所在柱位。')}
      <div class="ss-groups">
        ${_makeSsGrp(_ssAOk,  'A级·吉', 'ss-a-ok')}
        ${_makeSsGrp(_ssABad, 'A级·凶', 'ss-a-bad')}
      </div>
    `;
    el.appendChild(_ssCard);
  }

  /* ── 命局建议速览 (lifestyle + lucky) ────────── */
  const _lk = json.lucky    || {};
  const _ls = json.lifestyle || {};
  const _hasLucky = _lk.lucky_numbers?.length || _lk.lucky_colors?.length || _lk.lucky_direction || _lk.lucky_item;
  const _hasLife  = _ls.exercise?.length || _ls.diet?.length || _ls.sleep_advice || _ls.travel_direction;
  if (_hasLucky || _hasLife) {
    const _COLOR_HEX = {
      '红':'#ef4444','橙':'#f97316','黄':'#eab308','绿':'#22c55e','青':'#06b6d4',
      '蓝':'#3b82f6','紫':'#a855f7','白':'#94a3b8','黑':'#334155','金':'#f59e0b',
      '粉':'#f43f5e','棕':'#92400e','灰':'#6b7280',
    };
    const _getHex = c => Object.entries(_COLOR_HEX).find(([k])=>c.includes(k))?.[1]||'var(--accent)';
    const _adviceCard = document.createElement('details');
    _adviceCard.className = 'card';
    _adviceCard.innerHTML = `
      <summary>
        <span class="dot" style="background:var(--ok)"></span>
        <span style="font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.07em">命局建议</span>
        ${_lk.lucky_direction ? `<span class="chip ok" style="font-size:10px;padding:1px 8px;margin-left:6px">吉方 ${esc(_lk.lucky_direction)}</span>` : ''}
        ${_lk.lucky_item ? `<span class="chip" style="font-size:10px;padding:1px 8px">🔮 ${esc(_lk.lucky_item)}</span>` : ''}
      </summary>
      <div class="card-body">
        ${_lk.lucky_numbers?.length ? `
        <div style="margin-bottom:12px">
          <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:6px">幸运数字</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px">
            ${_lk.lucky_numbers.map(n=>`<div class="lucky-num" style="width:42px;height:42px;font-size:18px">${n}</div>`).join('')}
          </div>
        </div>` : ''}
        ${_lk.lucky_colors?.length ? `
        <div style="margin-bottom:12px">
          <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:6px">幸运颜色</div>
          <div class="lucky-color-row">
            ${_lk.lucky_colors.slice(0,6).map(c=>`<div class="lucky-color-chip"><div class="lcc-swatch" style="background:${_getHex(c)}"></div><div class="lcc-name">${esc(c)}</div></div>`).join('')}
          </div>
        </div>` : ''}
        <div class="g2" style="gap:8px;margin-bottom:8px">
          ${_ls.exercise?.length ? `
          <div>
            <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:5px">运动建议</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px">${_ls.exercise.slice(0,4).map(e=>`<span class="chip">${esc(e)}</span>`).join('')}</div>
          </div>` : ''}
          ${_ls.diet?.length ? `
          <div>
            <div style="font-size:11px;color:var(--muted);font-weight:700;margin-bottom:5px">饮食调养</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px">${_ls.diet.slice(0,4).map(e=>`<span class="chip">${esc(e)}</span>`).join('')}</div>
          </div>` : ''}
        </div>
        ${_ls.sleep_advice ? `<div class="tier-insight" style="margin-bottom:8px">🌙 ${txt(_ls.sleep_advice)}</div>` : ''}
        ${_ls.travel_direction ? `<div style="font-size:12px;color:var(--muted);margin-bottom:6px">🧭 出行方向：${txt(_ls.travel_direction)}</div>` : ''}
        <div style="text-align:right;margin-top:6px">
          <button data-switch-tab="15" style="font-size:11px;padding:3px 10px">查看完整开运建议 →</button>
        </div>
      </div>
    `;
    el.appendChild(_adviceCard);
  }

  /* ── 名词速查 (折叠) ─────────────────────────── */
  const _glossCard = document.createElement('details');
  _glossCard.className = 'card';
  _glossCard.style.marginBottom = '14px';
  _glossCard.innerHTML = `
    <summary style="cursor:pointer;padding:6px 2px">
      <span class="dot" style="background:var(--muted)"></span>
      <span style="font-size:12px;font-weight:700;color:var(--muted);letter-spacing:.05em">📚 命理名词速查</span>
      <span style="font-size:11px;color:var(--muted);font-weight:400;margin-left:8px">（点击展开·常见术语释义）</span>
    </summary>
    <div style="padding:10px 4px 4px;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;font-size:11px;line-height:1.65">
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>天干</strong>：甲乙丙丁戊己庚辛壬癸十干，分阴阳，配五行，主能量属性。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>地支</strong>：子丑寅卯辰巳午未申酉戌亥十二支，含月令、时令与藏干信息。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>日主</strong>：日柱天干，代表命主本人，命局全部强弱分析均以此为基准。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>藏干</strong>：地支内所含天干（本气/中气/余气），参与五行计分，影响深层能量。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>十神</strong>：日主与其余天干的生克关系，涵盖正官/七杀/正印/偏印/正财/偏财/食神/伤官/比肩/劫财。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>用神</strong>：命局最需要补充的五行能量，行该五行大运/流年有利。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>忌神</strong>：克制用神或令命局失衡的五行，行该方向大运宜守成谨慎。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>大运</strong>：以十年为一节律的运程，按出生后起步年计算，影响整体大方向。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>流年</strong>：逐年运程，与大运叠加形成年度综合影响，每年一个干支。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>三合/六合</strong>：地支相合，聚力顺遂，有利合作与感情，行合运有助团队与婚缘。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>冲</strong>：地支相冲（如子午冲），主变动迁移，冲用神则损，冲忌神则可借力改变。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>纳音</strong>：六十甲子对应的音律名称（如"石榴木""海中金"），源自古代五音理论，供辅助参考。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>格局</strong>：命局的整体结构定性（如正格·从格·专旺格），决定用神取法方向，影响整体运势上限。</div>
      <div style="padding:8px 10px;background:var(--bg2);border-radius:7px"><strong>神煞</strong>：古代对特定干支组合标记的吉凶符号（如天乙贵人、羊刃），需结合格局强弱综合判断。</div>
    </div>
  `;
  el.appendChild(_glossCard);
}

/* ══════════════════════════════════════════════════
   Tab 3: 格局 (GejuModel)
   布局规划（4模块，无内容重复）：
   ① 格局总览  ── 格局名/层级/置信度/破格/格局喜忌
   ② 命局配合  ── 日主强弱/用神忌神/判断依据（去掉在命盘Tab已有的五行条）
   ③ 大运共振  ── 顺逆时间轴 + 当前大运状态（不重复大运Tab的详细内容）
   ④ 格局解读  ── 深度解读文字 + 五域特质 + 古籍引用
═══════════════════════════════════════════════════ */
function renderTab3(json, el) {
  const g = json.geju;
  if (!g) {
    el.innerHTML = `<div class="geju-empty"><div style="font-size:40px;margin-bottom:10px">⊞</div><div>格局数据尚未计算，请先排盘。</div></div>`;
    return;
  }

  const fullName  = g.geju_name || g.name || '未知';
  const tierCls   = (g.tier==='高'||g.geju_level==='上格') ? 'high' : (g.tier==='中'||g.geju_level==='中格') ? 'mid' : 'low';
  const confPct   = typeof g.confidence === 'number' ? Math.round(g.confidence * 100) : null;
  const uncertain = confPct !== null && confPct < 50;
  const levelLabel= g.geju_level==='上格' ? '▲ 上格' : g.geju_level==='中格' ? '◆ 中格' : g.geju_level==='下格' ? '▽ 下格' : (g.geju_level||'');
  const _thisYear3= new Date().getFullYear();
  const _curDY3   = (json.dayun?.items||[]).find(d=>d.start_year<=_thisYear3&&(d.start_year||0)+10>_thisYear3)||null;

  // ── 知识库：格局喜忌十神 ─────────────────────
  const GEJU_LIKE_TG = {
    '正官格':['正印','偏印','正财','偏财'], '偏官格':['正印','食神'], '七杀格':['正印','食神'],
    '正印格':['正官','偏官','比肩'],        '偏印格':['偏官','七杀'],
    '正财格':['食神','伤官','比肩'],        '偏财格':['食神','伤官','比肩','劫财'],
    '食神格':['偏财','正财','比肩'],        '伤官格':['正财','偏财'],
    '建禄格':['正官','食神','财'],          '羊刃格':['正官','偏官'],
  };
  const GEJU_DISLIKE_TG = {
    '正官格':['伤官','劫财','比肩'],        '偏官格':['财过多'],     '七杀格':['财过多'],
    '正印格':['偏财','正财过多'],           '偏印格':['食神'],
    '正财格':['比肩','劫财'],              '偏财格':['比肩','劫财过多'],
    '食神格':['偏印','枭神'],              '伤官格':['正官'],
    '建禄格':['劫财过多'],                 '羊刃格':['比肩','劫财'],
  };
  const GEJU_DOMAIN = {
    '正官格': {w:'薪俸稳定，忌冒进投机',c:'仕途管理首选，公务员/企业中高层/法律',m:'婚姻守礼，伴侣多稳重可依靠',h:'过谨慎易压抑，注意肝胆情志',s:'人缘中正，处事讲规矩'},
    '偏官格': {w:'财运起伏，竞争性行业方有大利',c:'军警律法/竞技/创业，需制化成大器',m:'感情激烈，得正印制化趋稳定',h:'注意骨伤意外，压力需宣泄',s:'江湖气重，义气但易树敌'},
    '七杀格': {w:'财运起伏，敢闯有大利',c:'军警律法/创业，需制化方成大器',m:'感情激烈易动荡，制化则稳',h:'注意骨伤，阳刚冲力强',s:'江湖气重，人脉广'},
    '正印格': {w:'平稳偏清贫，靠知识技能生财',c:'文教医疗/学术，官印相生显贵气',m:'含蓄温柔，重心灵契合',h:'体质偏弱，利于修心静养',s:'敦厚亲和，易得贵人'},
    '偏印格': {w:'财路偏门，艺术技艺型收入',c:'偏门技艺/玄学/创意，不宜大众服务',m:'感情内敛，需思想深度相合之人',h:'注意精神压力与抑郁',s:'内向独立，知己少而精'},
    '正财格': {w:'正财丰厚，稳健积累',c:'财务/企业经营/房产',m:'踏实务实，伴侣多勤俭持家',h:'注意过劳与消化系统',s:'交际有度，朋友圈稳固'},
    '偏财格': {w:'偏财活跃，财来财去较快',c:'贸易/投资/娱乐餐饮，多线并行',m:'桃花旺，需防感情不专，晚婚宜',h:'精力充沛，注意肾与内分泌',s:'八面玲珑，人脉广财缘好'},
    '食神格': {w:'衣食丰足，靠一技之长生财',c:'餐饮美食/艺术创作/教育培训',m:'感情温馨，重生活品质',h:'体质偏丰，注意控制饮食',s:'温和亲切，有口才亲和力'},
    '伤官格': {w:'靠才华技艺巧赚，适合自由职业',c:'艺术/技术/律师媒体，不宜循规',m:'感情复杂，婚姻需磨合',h:'精神旺但易神经紧张',s:'个性鲜明，真朋友很铁'},
    '建禄格': {w:'稳定自力更生，专业技能型',c:'专业技术/自营事业，贵在实力',m:'感情严肃，婚姻较晚但求质量',h:'体格健壮，注意过劳',s:'自立自强，社交圈专注深厚'},
    '羊刃格': {w:'大起大落，适合高风险高回报',c:'军警医外科/法律竞技，需制化',m:'感情炽烈，容易冲突，需包容',h:'体格强健，注意外伤血光',s:'强势有领导气质，宜交有方向感之友'},
  };
  const likeTg    = GEJU_LIKE_TG[fullName]   || [];
  const dislikeTg = GEJU_DISLIKE_TG[fullName] || [];
  const domainMap = GEJU_DOMAIN[fullName]     || null;

  // ── 英文字段翻译表 ─────────────────────────────
  const ELEMENT_EN_CN = {metal:'金',wood:'木',water:'水',fire:'火',earth:'土',jin:'金',mu:'木',shui:'水',huo:'火',tu:'土'};
  const SHISHEN_EN_CN = {zheng_guan:'正官',pian_guan:'偏官',qi_sha:'七杀',zheng_yin:'正印',pian_yin:'偏印',shi_shen:'食神',shang_guan:'伤官',zheng_cai:'正财',pian_cai:'偏财',bi_jian:'比肩',jie_cai:'劫财'};
  const STRENGTH_EN_CN = {extremely_weak:'极弱',very_weak:'极弱',weak:'身弱',slightly_weak:'偏弱',neutral:'中和',balanced:'中和',moderate:'中和',slightly_strong:'偏强',strong:'身强',very_strong:'极强',extremely_strong:'极强'};
  const _TIER_NORM = {balanced:'neutral',moderate:'neutral',very_weak:'extremely_weak',very_strong:'extremely_strong',slightly_weak:'weak',slightly_strong:'strong'};
  function _valCN(v){if(!v)return v;const k=(v+'').toLowerCase().replace(/-/g,'_').replace(/ /g,'_');return ELEMENT_EN_CN[k]||SHISHEN_EN_CN[k]||v;}

  // ── 格局简介 ─────────────────────────────────
  const GEJU_INTRO = {
    '正官格':'月令正官为用，主威权秩序，贵仕途官职，性守礼有责任感。',
    '偏官格':'月令偏官（七杀）为用，主威猛进取，利军警竞技，宜制化方成大器。',
    '七杀格':'月令七杀为用，主将帅气貌，利创业军警律法，得制化方发大贵。',
    '正印格':'月令正印为用，主仁慈学识，利文教医疗，贵官印相生。',
    '偏印格':'月令偏印（枞神）为用，主偏才异能，利艺术玄学，忌食神被夺。',
    '正财格':'月令正财为用，主稳健积累，利财务经营，性勤俦务实。',
    '偏财格':'月令偏财为用，主活跃流通，利贸易投资娱乐，财来财去较快。',
    '食神格':'月令食神为用，主才艺丰衣衣食，利餐饮艺术教培，性温和有口丹。',
    '伤官格':'月令伤官为用，主才华横溢，利艺术技术律法，性高恐忌见正官。',
    '建禄格':'月令比肩（建禄）为用，主自立自强，贵专业实力，宜官食财辅助。',
    '羊刃格':'月令劫财（羊刃）为用，主将帅气貌，利军警医外科，宜官杀制化。',
  };

  // ── 颜色 / 星级 / 印章 ──────────────────────
  const tierColor = tierCls==='high' ? '#d97706' : tierCls==='mid' ? '#6366f1' : '#94a3b8';
  const tierStars = tierCls==='high' ? '★★★'    : tierCls==='mid' ? '★★☆'    : '★☆☆';
  const sealChars = fullName.replace(/格$/, '').slice(0, 4);
  const sealLines = sealChars.length <= 2 ? [sealChars] : [sealChars.slice(0,2), sealChars.slice(2)];

  /* ══ 模块①：格局总览 ════════════════════════
     格局名 / 层级星级 / 置信度 / 破格状态 / 喜忌十神
  ════════════════════════════════════════════════ */
  const brokenChip = g.is_broken === true
    ? `<span style="font-size:11px;color:var(--bad);background:rgba(239,68,68,0.1);border-radius:5px;padding:2px 8px;border:1px solid rgba(239,68,68,0.3)">⚠️ 格局已破</span>`
    : g.is_broken === false
    ? `<span style="font-size:11px;color:var(--ok);background:rgba(34,197,94,0.1);border-radius:5px;padding:2px 8px;border:1px solid rgba(34,197,94,0.3)">✓ 格局完整</span>`
    : '';

  const likeChips    = likeTg.map(t=>`<span style="font-size:11px;padding:2px 7px;border-radius:5px;background:rgba(34,197,94,0.1);color:var(--ok);border:1px solid rgba(34,197,94,0.3)">${esc(t)}</span>`).join('');
  const dislikeChips = dislikeTg.map(t=>`<span style="font-size:11px;padding:2px 7px;border-radius:5px;background:rgba(239,68,68,0.08);color:var(--bad);border:1px solid rgba(239,68,68,0.25)">${esc(t)}</span>`).join('');

  const mod1 = `
  <div class="card" style="margin-bottom:12px;overflow:hidden;padding:0">
    <div style="height:3px;background:linear-gradient(90deg,${tierColor},${tierColor}55)"></div>
    <div style="padding:14px 12px">
      <div style="display:flex;align-items:flex-start;gap:12px">
        <div class="geju-seal geju-seal-${tierCls}">
          ${sealLines.map(l=>`<div class="geju-seal-ln">${esc(l)}</div>`).join('')}
          ${confPct != null && confPct > 0 ? `<div class="geju-seal-score">${confPct}%</div>` : ''}
        </div>
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:5px">
            <span class="geju-hero-name">${esc(fullName)}</span>
            ${levelLabel ? `<span class="geju-tier-badge ${tierCls}">${levelLabel}</span>` : ''}
            ${brokenChip}
          </div>
          ${GEJU_INTRO[fullName] ? `<div style="font-size:11px;color:var(--muted);line-height:1.55;margin-bottom:7px;padding-right:4px">${esc(GEJU_INTRO[fullName])}</div>` : ''}
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:9px">
            <span style="font-size:15px;letter-spacing:3px;color:${tierColor}">${tierStars}</span>
            ${confPct !== null ? `<div style="display:flex;align-items:center;gap:5px;flex:1;min-width:0">
              <div style="flex:1;height:5px;background:var(--line);border-radius:3px;overflow:hidden">
                <div style="height:100%;width:${confPct}%;background:${confPct>=70?'var(--ok)':confPct>=40?'var(--warn)':'var(--bad)'};border-radius:3px"></div>
              </div>
              <span style="font-size:10px;color:var(--muted);white-space:nowrap">置信度 ${confPct}%${uncertain?' (待定)':''}</span>
            </div>` : ''}
          </div>
          ${likeChips ? `<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:4px">
            <span style="font-size:10px;color:var(--ok);font-weight:700;flex-shrink:0">喜行：</span>${likeChips}
          </div>` : ''}
          ${dislikeChips ? `<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
            <span style="font-size:10px;color:var(--bad);font-weight:700;flex-shrink:0">忌行：</span>${dislikeChips}
          </div>` : ''}
        </div>
      </div>
    </div>
  </div>`;

  /* ══ 模块②：命局配合 ═════════════════════════
     月令十神 / 日主强弱五段仪表 / 用神忌神 / 判断依据
  ════════════════════════════════════════════════ */
  const ys = json.yongshen || {};
  const st = json.day_master_strength || {};
  const STRENGTH_TIERS  = ['extremely_weak','weak','neutral','strong','extremely_strong'];
  const STRENGTH_LABELS = ['极弱','身弱','中和','身强','极强'];
  const _stTier  = _TIER_NORM[st.tier] || st.tier || '';
  const strIdx   = STRENGTH_TIERS.indexOf(_stTier);
  const strLabel = strIdx >= 0 ? STRENGTH_LABELS[strIdx] : (STRENGTH_EN_CN[st.tier] || st.tier || '—');
  const strColor = (_stTier==='neutral') ? 'var(--ok)' : (_stTier==='weak'||_stTier==='extremely_weak') ? 'var(--bad)' : '#f59e0b';
  const strengthGauge = `<div style="display:flex;gap:2px;margin-top:6px">
    ${STRENGTH_TIERS.map((t,i)=>`<div style="flex:1;text-align:center">
      <div style="height:5px;border-radius:2px;background:${i===strIdx?strColor:'var(--line)'};margin-bottom:3px"></div>
      <div style="font-size:9px;color:${i===strIdx?strColor:'var(--muted)'};font-weight:${i===strIdx?'700':'400'}">${STRENGTH_LABELS[i]}</div>
    </div>`).join('')}
  </div>`;
  const favorChips2 = (ys.favor||[]).map(f=>`<span class="chip" style="background:rgba(34,197,94,0.1);color:var(--ok);border:1px solid rgba(34,197,94,0.3)">${esc(_valCN(f))}</span>`).join('');
  const avoidChips2 = (ys.avoid||[]).map(f=>`<span class="chip" style="background:rgba(239,68,68,0.08);color:var(--bad);border:1px solid rgba(239,68,68,0.25)">${esc(_valCN(f))}</span>`).join('');

  const mod2 = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>命局配合</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
      <div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;text-align:center">
        <div style="font-size:10px;color:var(--muted);margin-bottom:4px">月令十神</div>
        <div style="font-size:26px;font-weight:800;font-family:var(--font-title,serif);letter-spacing:.05em">${esc(g.month_stem_shishen || fullName.replace(/格$/,'') || '—')}</div>
        <div style="font-size:10px;color:var(--muted);margin-top:3px">${g.month_stem_shishen ? '月令得令' : '格局取象(推算)'}</div>
      </div>
      <div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px">
        <div style="font-size:10px;color:var(--muted);text-align:center;margin-bottom:2px">日主强弱</div>
        <div style="font-size:22px;font-weight:800;color:${strColor};text-align:center">${strLabel}${st.score != null?`<span style="font-size:10px;color:var(--muted);font-weight:400;margin-left:4px">${typeof st.score==='number'?st.score.toFixed(1):st.score}/6</span>`:''}
        </div>
        ${strengthGauge}
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:${g.geju_detail?'10px':'0'}">
      <div style="padding:10px 12px;background:rgba(34,197,94,0.06);border-radius:8px;border-left:3px solid rgba(34,197,94,0.4)">
        <div style="font-size:10px;color:var(--ok);font-weight:700;margin-bottom:6px">▲ 用神（宜行）</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">${favorChips2||'<span style="font-size:11px;color:var(--muted)">—</span>'}</div>
        ${ys.rationale ? `<div style="font-size:10px;color:var(--muted);margin-top:6px;padding-top:5px;border-top:1px solid rgba(34,197,94,0.2);line-height:1.5">${esc(ys.rationale.slice(0,70))}${ys.rationale.length>70?'…':''}</div>` : ''}
      </div>
      <div style="padding:10px 12px;background:rgba(239,68,68,0.06);border-radius:8px;border-left:3px solid rgba(239,68,68,0.3)">
        <div style="font-size:10px;color:var(--bad);font-weight:700;margin-bottom:6px">▽ 忌神（宜守）</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">${avoidChips2||'<span style="font-size:11px;color:var(--muted)">—</span>'}</div>
      </div>
    </div>
    ${g.geju_detail ? `<div style="padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:6px;border-left:3px solid var(--accent);font-size:12px;color:var(--muted);line-height:1.6">📐 <strong>判断依据：</strong>${esc(g.geju_detail)}</div>` : ''}
  </div>`;

  /* ══ 模块③：大运共振 ════════════════════════
     顺逆时间轴（格局视角）+ 当前大运概况
     注：不重复大运Tab的流年/详细解读
  ════════════════════════════════════════════════ */
  const allDYItems = (json.dayun?.items||[]).slice(0, 8);
  let mod3 = '';
  if (allDYItems.length) {
    // 时间轴
    const pills = allDYItems.map(d => {
      const dtg   = d.ten_god || '';
      const dtgCN = typeof tenGodCN==='function' ? tenGodCN(dtg) : dtg;
      const isCur = d.start_year <= _thisYear3 && _thisYear3 < (d.start_year||0)+10;
      const isGood= likeTg.some(l => dtgCN.includes(l)||l.includes(dtgCN));
      const isBad = dislikeTg.some(d2 => dtgCN.includes(d2.replace(/过多$/,''))||d2.replace(/过多$/,'').includes(dtgCN));
      const bg = isCur ? 'var(--accent)' : isGood ? 'rgba(34,197,94,0.15)' : isBad ? 'rgba(239,68,68,0.12)' : 'var(--bg2,rgba(0,0,0,0.04))';
      const co = isCur ? '#fff' : isGood ? 'var(--ok)' : isBad ? 'var(--bad)' : 'var(--muted)';
      const gz = esc((d.stem||'')+(d.branch||''));
      const yr = d.start_year ? String(d.start_year) : '';
      const tag = isCur ? '<div style="font-size:9px;color:rgba(255,255,255,.85);margin-top:1px">▶今</div>' : isGood ? '<div style="font-size:9px;color:var(--ok);margin-top:1px">顺</div>' : isBad ? '<div style="font-size:9px;color:var(--bad);margin-top:1px">逆</div>' : '';
      return `<div title="${yr}年${dtgCN?'·十神:'+dtgCN:''}" style="flex:1;min-width:0;padding:6px 4px;background:${bg};border-radius:6px;text-align:center;border:1px solid ${isGood&&!isCur?'rgba(34,197,94,.3)':isBad&&!isCur?'rgba(239,68,68,.25)':'transparent'}">
        <div style="font-size:13px;font-weight:700;font-family:var(--font-title,serif);color:${co}">${gz}</div>
        ${yr?`<div style="font-size:9px;color:${isCur?'rgba(255,255,255,.65)':'var(--muted)'};margin-top:1px">${yr.slice(-2)}年</div>`:''}
        ${tag}
      </div>`;
    }).join('');

    // 当前大运概况（只显示与格局的共振结论，不重复财/情/健细节）
    let curDYBlock = '';
    if (_curDY3) {
      const dyGZ    = esc((_curDY3.stem||'')+(_curDY3.branch||''));
      const dyTG    = _curDY3.ten_god || '';
      const dyTgCN  = typeof tenGodCN==='function' ? tenGodCN(dyTG) : dyTG;
      const isLike  = likeTg.some(l => dyTgCN.includes(l)||l.includes(dyTgCN));
      const isDislike = dislikeTg.some(d => dyTgCN.includes(d.replace(/过多$/,''))||d.replace(/过多$/,'').includes(dyTgCN));
      const resColor = isLike ? 'var(--ok)' : isDislike ? 'var(--bad)' : 'var(--warn)';
      const resLabel = isLike ? '🔥 顺格大运 · 格局能量充分发挥' : isDislike ? '⚠️ 逆格大运 · 宜守成稳进' : '〜 中性大运 · 视流年调整';
      const start = _curDY3.start_year||'?'; const end = ((_curDY3.start_year||0)+10)||'?';
      curDYBlock = `
      <div style="margin-top:8px;padding:10px 12px;border-radius:8px;background:var(--bg2,rgba(0,0,0,0.04));border-left:3px solid ${resColor}">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
          <span style="font-size:12px;font-weight:700;color:${resColor}">▶ 当前 ${dyGZ}（${start}–${end}）</span>
          ${dyTgCN?`<span class="tengod-badge ${typeof tenGodType==='function'?tenGodType(dyTG):''}">${dyTgCN}</span>`:''}
        </div>
        <div style="font-size:12px;color:var(--text);font-weight:600">${resLabel}</div>
        ${likeTg.length ? `<div style="font-size:11px;color:var(--muted);margin-top:4px">顺格：行 ${likeTg.join('/')} 运时格局力量最强</div>` : ''}
        ${dislikeTg.length ? `<div style="font-size:11px;color:var(--muted)">逆格：逢 ${dislikeTg.map(t=>t.replace(/过多$/,'')).join('/')} 宜守成</div>` : ''}
      </div>`;
    }

    mod3 = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>大运顺逆</p>
    <div style="display:flex;gap:4px;overflow-x:auto;padding-bottom:2px">${pills}</div>
    <div style="display:flex;gap:12px;font-size:10px;color:var(--muted);margin-top:6px;flex-wrap:wrap">
      <span style="display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:2px;background:rgba(34,197,94,0.3);border:1px solid rgba(34,197,94,.5);display:inline-block"></span>顺格</span>
      <span style="display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:2px;background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,.4);display:inline-block"></span>逆格</span>
      <span style="display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:2px;background:var(--accent);display:inline-block"></span>当前</span>
      <span style="color:var(--accent);cursor:pointer;text-decoration:underline" onclick="document.querySelector('[data-tab=\\'16\\']')?.click()">→ 大运详情</span>
    </div>
    ${curDYBlock}
  </div>`;
  }

  /* ══ 模块④：格局解读 ════════════════════════
     深度解读文字 + 五域特质（紧凑2列）+ 标签 + 古籍
  ════════════════════════════════════════════════ */
  // 深度解读（只保留一份，去掉末尾重复的月令十神）
  const _detailText = (g.geju_detail || g.description || '').trim();
  const interpHtml = g.interpretation_text ? `
    <div style="margin-bottom:12px">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:6px;letter-spacing:.04em">深度解读</div>
      <div class="geju-text">${renderPara(g.interpretation_text)}</div>
    </div>` : (_detailText ? `
    <div style="margin-bottom:12px">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:6px;letter-spacing:.04em">格局释义</div>
      <div class="geju-text">${renderPara(_detailText)}</div>
    </div>` : '');

  // 五域特质——2列网格，紧凑
  const domainGrid = domainMap ? `
    <div style="margin-bottom:12px">
      <div style="font-size:11px;font-weight:600;color:var(--muted);margin-bottom:6px;letter-spacing:.04em">格局特质</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        ${[['💰','财运',domainMap.w],['🏢','事业',domainMap.c],['❤️','婚姻',domainMap.m],['🌿','健康',domainMap.h],['🤝','人际',domainMap.s]].map(([icon,lbl,txt2],idx)=>`
        <div style="padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px${idx===4?';grid-column:span 2':''}">
          <div style="font-size:11px;font-weight:700;color:var(--text);margin-bottom:3px">${icon} ${lbl}</div>
          <div style="font-size:11px;color:var(--muted);line-height:1.55;word-break:break-all;overflow-wrap:anywhere">${esc(txt2)}</div>
        </div>`).join('')}
      </div>
    </div>` : '';

  // 分析标签（去掉重复，只保留推论标签+格局层级）
  const allTags = Array.from(new Set([...(g.inference_tags||[]), g.geju_level||''].filter(Boolean)));
  const tagsRow = allTags.length ? `
    <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px">
      ${allTags.map(t=>`<span class="chip" style="font-size:11px">${esc(t)}</span>`).join('')}
    </div>` : '';

  // 古籍引用（折叠）
  const classicRefText  = g.classic_ref || '';
  const classicRefCount = classicRefText ? classicRefText.split('\n').filter(l=>l.trim()).length : 0;
  const classicHtml     = classicRefText ? `
    <details class="geju-classic" style="border-radius:8px;border:1px solid var(--line);padding:10px 12px">
      <summary style="font-size:11px;color:var(--accent-gold,#b45309);font-weight:600;cursor:pointer;user-select:none">📜 古籍引用${classicRefCount>1?`（共${classicRefCount}条）`:''}</summary>
      <div class="geju-classic-body" style="margin-top:8px">${txt(classicRefText)}</div>
    </details>` : '';

  const mod4 = (interpHtml || domainGrid || tagsRow || classicHtml) ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>格局解读</p>
    ${interpHtml}${domainGrid}${tagsRow}${classicHtml}
  </div>` : '';

  el.innerHTML = mod1 + mod2 + mod3 + mod4;
}

/* ══════════════════════════════════════════════════
   Tab 4: 命宫 (PalaceModel)
═══════════════════════════════════════════════════ */
function renderTab4(json, el) {
  const palace = json.palace;
  if (!palace) { el.innerHTML = '<div class="hint" style="padding:16px">命宫数据尚未计算。</div>'; return; }

  // ── 当前大运与神煞联动提示 ──────────────────
  const _thisYear4 = new Date().getFullYear();
  const _curDY4 = (json.dayun?.items||[]).find(d=>d.start_year<=_thisYear4&&(d.start_year||0)+10>_thisYear4)||null;
  const palaceDayunHtml = _curDY4 ? `
  <div style="margin-bottom:12px;padding:7px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-left:3px solid var(--accent);font-size:12px">
    <span style="font-size:11px;color:var(--accent);font-weight:700">▶ 当前大运 ${esc((_curDY4.stem||'')+(_curDY4.branch||''))}</span>
    ${_curDY4.health_hint?`<span style="margin-left:10px;color:var(--muted)">${esc(_curDY4.health_hint.slice(0,60))}</span>`:''}
  </div>` : '';

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
        <details style="margin-top:6px"><summary style="font-size:11px;cursor:pointer;color:var(--accent);user-select:none">查看详解 ▾</summary>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px;margin-top:8px">
            ${items.map(s=>{
              const pc2={year:'年柱',month:'月柱',day:'日柱',hour:'时柱'}[s.pillar]||s.pillar||'';
              return `<div style="padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-left:3px solid ${s.is_beneficial?'var(--ok)':'var(--bad)'}">
                <div style="font-weight:700;font-size:12px;margin-bottom:3px">${esc(s.name||'')}${pc2?`<span style="font-size:10px;color:var(--muted);font-weight:400;margin-left:4px">${pc2}</span>`:''}${s.dizhi?`<span style="font-size:10px;color:var(--muted);margin-left:4px">(${esc(s.dizhi)})</span>`:''}</div>
                ${s.meaning?`<div style="font-size:11px;line-height:1.55;color:var(--muted)">${esc(s.meaning)}</div>`:''}
                ${s.classic_source?`<div style="font-size:10px;color:var(--accent);margin-top:4px;font-style:italic">出自《${esc(s.classic_source)}》</div>`:''}
              </div>`;
            }).join('')}
          </div>
        </details>
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

  el.innerHTML = (palaceDayunHtml||'') + palaceCard + shenshaCard + houseGrid;
}

/* ══════════════════════════════════════════════════
   Tab 5: 摘要
   职责：命盘全局摘要 — 命局总论 / 人生里程碑 /
         核心分析要点 / 6D评分 / 技术数据
   数据源：life_arc / milestones / geju / yongshen /
           marriage_analysis / health / career /
           personality / shensha / validation
═══════════════════════════════════════════════════ */
function renderTab5(json, el) {
  const v       = json.validation || {};
  const arc     = json.life_arc   || {};
  const lvlCls  = {L0:'ok',L1:'ok',L2:'warn',L3:'bad'}[v.level] || 'warn';
  const warnings= v.warnings || [];
  const rt      = json.rule_version_detail || {};

  // ── 常用字段快捷 ──────────────────────────────
  const _gj5    = json.geju                || {};
  const _ys5    = json.yongshen            || {};
  const _st5    = json.day_master_strength || {};
  const _mar5   = json.marriage_analysis   || {};
  const _hlt5   = json.health              || {};
  const _crr5   = json.career              || {};
  const _per5   = json.personality         || {};
  const _fe5    = json.five_elements       || {};
  const _sh5    = json.shensha             || {};

  // ── 翻译映射（五行英文→中文） ──────────────────
  const _EL5 = {metal:'金',wood:'木',water:'水',fire:'火',earth:'土',
                jin:'金',mu:'木',shui:'水',huo:'火',tu:'土',
                jin4:'金',mu4:'木',shui3:'水',huo3:'火',tu3:'土'};
  const _SH5 = {zheng_guan:'正官',pian_guan:'偏官',qi_sha:'七杀',zheng_yin:'正印',
                pian_yin:'偏印',shi_shen:'食神',shang_guan:'伤官',zheng_cai:'正财',
                pian_cai:'偏财',bi_jian:'比肩',jie_cai:'劫财'};
  const _cn5 = v => { if (!v) return v; const k=(v+'').toLowerCase().replace(/-/g,'_').replace(/ /g,'_'); return _EL5[k]||_SH5[k]||v; };

  // ── 强弱中文 ───────────────────────────────────
  const _strCN5 = (t) => ({extremely_weak:'极弱',very_weak:'极弱',weak:'身弱',slightly_weak:'偏弱',neutral:'中和',balanced:'中和',strong:'身强',slightly_strong:'偏强',very_strong:'极强',extremely_strong:'极强'}[t] || t || '—');

  // ── 层级徽章 ───────────────────────────────────
  const tierBadge5 = (tier) => {
    const cls = tier==='局高'?'high':tier==='局中'?'mid':'low';
    return tier ? `<span class="geju-tier-badge ${cls}">${esc(tier)}</span>` : '';
  };

  // ── 从 arc.interpretation_text 中提取总评分 ──
  let _lifeScore = null;
  let _arcIntro  = arc.interpretation_text || '';
  const _scoreMatch = _arcIntro.match(/命局综合评分\s*([0-9]+(?:\.[0-9]+)?)/);
  if (_scoreMatch) {
    _lifeScore = parseFloat(_scoreMatch[1]);
    // 将评分句从段落中剥离，单独展示
    _arcIntro = _arcIntro.replace(/命局综合评分\s*[0-9]+(?:\.[0-9]+)?\s*[，,。.]?\s*/, '').trim();
  }

  // ── 行动建议：先尝试换行分割，再按；分割 ─────
  const _splitActions = (str) => {
    if (!str) return [];
    const byLine = str.split(/[\n\r]+/).map(s => s.trim()).filter(Boolean);
    if (byLine.length > 1) return byLine;
    return str.split('；').map(s => s.trim()).filter(Boolean);
  };

  /* ══ 卡片①：命盘快览横条 ════════════════════════
     格局名/层级 · 用神 · 忌神 · 日主强弱 · 总评分
  ════════════════════════════════════════════════ */
  const gejuName5  = _gj5.geju_name || _gj5.name || '';
  const gejuLevel5 = _gj5.geju_level || '';
  const gejuConf5  = typeof _gj5.confidence === 'number' ? Math.round(_gj5.confidence * 100) : null;
  const favorList5 = (_ys5.favor || []).map(_cn5).join(' · ') || '—';
  const avoidList5 = (_ys5.avoid || []).map(_cn5).join(' · ') || '—';
  const strLabel5  = _strCN5(_st5.tier);
  const strCols5   = _st5.tier==='neutral'||_st5.tier==='balanced' ? 'var(--ok)' : (_st5.tier||'').includes('weak') ? 'var(--bad)' : '#f59e0b';

  const overviewStrip = (gejuName5 || gejuLevel5 || favorList5 !== '—' || strLabel5 !== '—') ? `
  <div class="card" style="margin-bottom:12px;padding:10px 14px">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px">
      <div style="text-align:center;padding:8px 6px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">命局格局</div>
        ${gejuName5 ? `<div style="font-size:15px;font-weight:800;font-family:var(--font-title,serif)">${esc(gejuName5)}</div>` : ''}
        ${gejuLevel5 ? `<div style="font-size:12px;font-weight:700;color:var(--accent);margin-top:2px">${esc(gejuLevel5)}${gejuConf5 !== null ? '<span style="font-size:10px;font-weight:400"> · 置信'+gejuConf5+'%</span>' : ''}</div>` : ''}
        <div style="font-size:9px;color:var(--muted);margin-top:3px;line-height:1.4">月令十神成格，决定一生<br>运势走向与发挥空间</div>
      </div>
      <div style="text-align:center;padding:8px 6px;background:rgba(34,197,94,0.06);border-radius:8px;border:1px solid rgba(34,197,94,0.2)">
        <div style="font-size:10px;color:var(--ok);font-weight:700;margin-bottom:4px">▲ 用神（宜行）</div>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:3px;margin-bottom:4px">${(_ys5.favor||[]).length ? (_ys5.favor||[]).map(e=>`<span style="display:inline-block;padding:2px 9px;border-radius:12px;background:rgba(34,197,94,0.18);color:var(--ok);font-size:13px;font-weight:800">${esc(_cn5(e))}</span>`).join('') : `<span style="font-size:12px;color:var(--muted)">—</span>`}</div>
        <div style="font-size:9px;color:var(--muted);line-height:1.4">大运走此五行有利<br>格局发挥，宜积极进取</div>
      </div>
      <div style="text-align:center;padding:8px 6px;background:rgba(239,68,68,0.06);border-radius:8px;border:1px solid rgba(239,68,68,0.2)">
        <div style="font-size:10px;color:var(--bad);font-weight:700;margin-bottom:4px">▽ 忌神（宜守）</div>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:3px;margin-bottom:4px">${(_ys5.avoid||[]).length ? (_ys5.avoid||[]).map(e=>`<span style="display:inline-block;padding:2px 9px;border-radius:12px;background:rgba(239,68,68,0.12);color:var(--bad);font-size:13px;font-weight:800">${esc(_cn5(e))}</span>`).join('') : `<span style="font-size:12px;color:var(--muted)">—</span>`}</div>
        <div style="font-size:9px;color:var(--muted);line-height:1.4">大运逢此五行格局受克<br>宜守成稳进，避免激进</div>
      </div>
      <div style="text-align:center;padding:8px 6px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">日主强弱</div>
        <div style="font-size:17px;font-weight:800;color:${strCols5}">${esc(strLabel5)}</div>
        ${_st5.score != null ? `<div style="font-size:9px;color:var(--muted);margin-top:1px">${typeof _st5.score==='number'?_st5.score.toFixed(1):_st5.score}/6</div>` : ''}
        <div style="font-size:9px;color:var(--muted);margin-top:3px;line-height:1.4">日元自身能量比率，<br>影响喜忌取用神方向</div>
      </div>
      ${_lifeScore !== null ? `<div style="text-align:center;padding:8px 6px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">命局综合评分</div>
        <div style="font-size:20px;font-weight:800;color:${_lifeScore>=75?'var(--ok)':_lifeScore>=55?'#f59e0b':'var(--bad)'}">${_lifeScore}</div>
        <div style="font-size:9px;color:var(--muted);margin-top:2px">${_lifeScore>=75?'上等命局':_lifeScore>=55?'中等命局':'下等命局'}</div>
        <div style="font-size:9px;color:var(--muted);margin-top:3px;line-height:1.4">综合格局/用神/六维<br>加权综合评分</div>
      </div>` : ''}
    </div>
  </div>` : '';

  /* ══ 卡片②：人生命局总论 ═════════════════════════
     总论 / 人生三阶段 / 顶峰注意大运 / 行动建议
  ════════════════════════════════════════════════ */
  const _actionItems = _splitActions(arc.optimal_action);
  const arcCard = (arc.overall_tier || _arcIntro || arc.early_fortune) ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent-gold)"></span>人生命局总论</p>

    ${arc.overall_tier ? `<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px">
      ${tierBadge5(arc.overall_tier)}
      ${(arc.life_motto||'').trim().length > 1 ? `<span style="font-size:13px;color:var(--text);font-style:italic">&#8220;${esc(arc.life_motto.trim())}&#8221;</span>` : ''}
    </div>` : ''}

    ${_arcIntro ? `<div style="font-size:13px;line-height:1.75;color:var(--text);margin-bottom:12px">${renderPara(_arcIntro)}</div>` : ''}

    ${(arc.early_fortune||arc.mid_fortune||arc.late_fortune) ? `
    <div class="g3" style="gap:10px;margin-bottom:12px">
      ${arc.early_fortune ? `<div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-top:2px solid var(--accent-gold)">
        <div style="font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:5px">早年（0–30岁）</div>
        <div style="font-size:12px;line-height:1.65;color:var(--text)">${renderPara(arc.early_fortune)}</div>
      </div>` : ''}
      ${arc.mid_fortune ? `<div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-top:2px solid var(--accent)">
        <div style="font-size:11px;font-weight:700;color:var(--accent);margin-bottom:5px">中年（30–60岁）</div>
        <div style="font-size:12px;line-height:1.65;color:var(--text)">${renderPara(arc.mid_fortune)}</div>
      </div>` : ''}
      ${arc.late_fortune ? `<div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-top:2px solid var(--muted)">
        <div style="font-size:11px;font-weight:700;color:var(--muted);margin-bottom:5px">晚年（60岁+）</div>
        <div style="font-size:12px;line-height:1.65;color:var(--text)">${renderPara(arc.late_fortune)}</div>
      </div>` : ''}
    </div>` : ''}

    ${(arc.peak_periods?.length || arc.caution_periods?.length) ? `
    <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:${_actionItems.length?'12px':'0'}">
      ${arc.peak_periods?.length ? `<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span style="font-size:10px;color:var(--ok);font-weight:700;white-space:nowrap;flex-shrink:0">▲ 顶峰大运</span>
        ${arc.peak_periods.map(p=>`<span class="chip ok" style="font-size:11px" title="此大运格局能量最强，宜积极进取">${esc(p)}</span>`).join('')}
        <span style="font-size:10px;color:var(--muted)">— 格局全力发挥，宜大力进取</span>
      </div>` : ''}
      ${arc.caution_periods?.length ? `<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span style="font-size:10px;color:var(--warn);font-weight:700;white-space:nowrap;flex-shrink:0">▽ 注意大运</span>
        ${arc.caution_periods.map(p=>`<span class="chip warn" style="font-size:11px" title="此大运需谨慎行事，宜守成稳进">${esc(p)}</span>`).join('')}
        <span style="font-size:10px;color:var(--muted)">— 宜守成稳进，勿贸然决策</span>
      </div>` : ''}
    </div>` : ''}

    ${_actionItems.length ? `<div style="padding:10px 12px;background:var(--accent-gold-bg,rgba(224,139,0,0.08));border-radius:8px;border-left:3px solid var(--accent-gold)">
      <div style="font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:6px">📌 行动建议</div>
      ${_actionItems.map((s,i)=>`<div style="font-size:12px;line-height:1.8;padding:4px 0;overflow-wrap:anywhere;word-break:break-word;${i<_actionItems.length-1?'border-bottom:1px solid rgba(180,113,10,0.12)':''}">• ${esc(s)}</div>`).join('')}
    </div>` : ''}
  </div>` : '';

  /* ══ 卡片③：大运时间轴 + 人生里程碑 ════════════════
     类型标注：
     犯太岁 = 流年地支与命支相同，本命年宜低调守成
     岁运并临 = 流年与大运干支同步，运势正负均放大
     大运交接 = 大运交替约18个月过渡期，防剧变
     社会节点 = 普遍人生关键年龄节点（毕业/婚育/职业等）
  ════════════════════════════════════════════════ */
  const milestones  = json.milestones || [];
  const _dyItems    = (json.dayun || {}).items || [];
  const _favorSet   = new Set((_ys5.favor || []).map(x => x.toLowerCase()));
  const _avoidSet   = new Set((_ys5.avoid || []).map(x => x.toLowerCase()));

  // 大运元素映射（stem/branch → wuxing element 粗略） 
  const _GZ2EL = {甲:'wood',乙:'wood',丙:'fire',丁:'fire',戊:'earth',己:'earth',
                  庚:'metal',辛:'metal',壬:'water',癸:'water',
                  子:'water',丑:'earth',寅:'wood',卯:'wood',辰:'earth',巳:'fire',
                  午:'fire',未:'earth',申:'metal',酉:'metal',戌:'earth',亥:'water'};

  // 判断大运干支是否走喜/忌
  const _dyFavor = (dy) => {
    const gz = (dy.ganzhi || dy.stem+dy.branch || '');
    const els = gz.split('').map(c => _GZ2EL[c]).filter(Boolean);
    const favorCnt = els.filter(e => _favorSet.has(e)).length;
    const avoidCnt = els.filter(e => _avoidSet.has(e)).length;
    if (favorCnt > avoidCnt) return 'favor';
    if (avoidCnt > favorCnt) return 'avoid';
    return 'neutral';
  };

  // 查找某年龄所在大运
  const _findDY = (age) => {
    if (!_dyItems.length) return null;
    return _dyItems.find(d => {
      const s = d.start_age ?? 0;
      const e = d.end_age  ?? (s + 10);
      return age >= s && age < e;
    }) || null;
  };

  const MS_ICON  = {'犯太岁':'⚡','岁运并临':'🌟','大运交接':'🔄','社会节点':'👥',
                    '流年冲关':'⚡','本命年':'🔥','人生节点':'📍','节气节点':'🌿',
                    '事业节点':'💼','婚恋节点':'💞','健康节点':'🏥'};
  const MS_HINT  = {
    '犯太岁'  : '流年地支与命支/日支相同，本命年宜低调守成，避免大动作决策',
    '岁运并临': '大运干支与流年同步共振，运势正负均放大，宜顺势行事',
    '大运交接': '进入新十年大运，约18个月过渡期，防剧烈变动，宜审时度势',
    '社会节点': '人生普遍关键年龄节点，结合个人大运流年综合研判',
    '本命年'  : '流年地支与出生年支相同，宜静守，忌大动作',
    '流年冲关': '流年与命中关键地支形成冲克，需格外谨慎应对',
  };
  const MS_TYPE_COLOR = {
    '犯太岁':'rgba(239,68,68,0.07)', '岁运并临':'rgba(245,158,11,0.07)',
    '大运交接':'rgba(99,102,241,0.07)', '社会节点':'rgba(34,197,94,0.05)',
    '本命年':'rgba(239,68,68,0.07)', '流年冲关':'rgba(239,68,68,0.09)',
  };

  // ── 大运时间轴横条 ────────────────────────────────
  const dayunTimeline = _dyItems.length ? (() => {
    const barItems = _dyItems.map(dy => {
      const favStatus = _dyFavor(dy);
      const gz = dy.ganzhi || ((dy.stem||'')+(dy.branch||''));
      const sa = dy.start_age ?? '?';
      const ea = dy.end_age  ?? (typeof sa==='number'?sa+10:'?');
      const col = favStatus==='favor'?'rgba(34,197,94,0.12)':favStatus==='avoid'?'rgba(239,68,68,0.10)':'rgba(0,0,0,0.04)';
      const brd = favStatus==='favor'?'var(--ok)':favStatus==='avoid'?'var(--bad)':'var(--muted)';
      const lbl = favStatus==='favor'?'喜':favStatus==='avoid'?'忌':'中';
      const lblcol = favStatus==='favor'?'var(--ok)':favStatus==='avoid'?'var(--bad)':'var(--muted)';
      const narrative = dy.narrative ? dy.narrative.replace(/[\r\n]+/g,' ').slice(0,80)+'…' : null;
      return `<div style="flex:1;min-width:60px;text-align:center;padding:7px 5px;background:${col};border-radius:7px;border:1px solid ${brd};position:relative" title="${esc(narrative||gz+'大运')}">
        <div style="font-size:13px;font-weight:800;font-family:var(--font-title,serif)">${esc(gz)}</div>
        <div style="font-size:9px;color:var(--muted);margin-top:1px">${sa}–${ea}岁</div>
        <div style="font-size:10px;font-weight:700;color:${lblcol};margin-top:2px">${lbl}</div>
      </div>`;
    }).join('');
    return `<div style="margin-bottom:10px">
      <div style="font-size:10px;color:var(--muted);margin-bottom:4px;font-weight:600">📅 大运时间轴 — <span style="color:var(--ok)">●喜</span>/<span style="color:var(--bad)">●忌</span>/<span style="color:var(--muted)">●中</span>（按用神判断）</div>
      <div style="display:flex;gap:4px;flex-wrap:wrap">${barItems}</div>
    </div>`;
  })() : '';

  const msHtml = (milestones.length || _dyItems.length) ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent)"></span>大运与人生里程碑
      ${milestones.length ? `<span class="card-title-sub">里程碑 ${milestones.length} 项</span>` : ''}
    </p>
    ${dayunTimeline}
    ${milestones.length ? `<div style="display:flex;flex-direction:column;gap:6px;margin-top:4px">
      ${milestones.map(m => {
        const rlCls    = m.risk_level==='高'?'bad':m.risk_level==='中'?'warn':'ok';
        const typeIcon = MS_ICON[m.milestone_type] || '📍';
        const typeHint = MS_HINT[m.milestone_type] || '';
        const typeBg   = MS_TYPE_COLOR[m.milestone_type] || 'rgba(0,0,0,0.03)';
        const isDayunChange = m.milestone_type === '大运交接';
        const isHighRisk    = m.risk_level === '高';
        const borderCol = isHighRisk?'var(--bad)':isDayunChange?'var(--accent)':m.risk_level==='中'?'var(--warn)':'transparent';
        const showTypeTag = m.milestone_type && m.description && m.description !== m.milestone_type;
        // 查找所处大运
        const _dy = _findDY(m.age);
        const _dyGz = _dy ? (_dy.ganzhi||(_dy.stem||'')+(_dy.branch||'')) : null;
        const _dyFavStat = _dy ? _dyFavor(_dy) : 'neutral';
        const _dyFavCol = _dyFavStat==='favor'?'var(--ok)':_dyFavStat==='avoid'?'var(--bad)':'var(--muted)';
        const _dyFavLbl = _dyFavStat==='favor'?'喜运':_dyFavStat==='avoid'?'忌运':'中性';
        const _dyNarr   = _dy?.narrative ? _dy.narrative.replace(/[\r\n]+/g,' ') : null;
        return `<div style="display:flex;gap:10px;padding:9px 11px;background:${typeBg};border-radius:8px;align-items:flex-start;border-left:2px solid ${borderCol}">
          <div style="min-width:52px;text-align:center;flex-shrink:0">
            <div style="font-size:17px;font-weight:800;color:var(--accent)">${m.age}岁</div>
            <div style="font-size:10px;color:var(--muted)">${m.year}年</div>
            ${_dyGz ? `<div style="font-size:10px;color:${_dyFavCol};font-weight:700;margin-top:2px" title="所处大运">${esc(_dyGz)}</div>` : ''}
          </div>
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:3px">
              ${showTypeTag ? `<span style="font-size:10px;padding:1px 6px;border-radius:4px;background:rgba(99,102,241,0.1);color:var(--accent);font-weight:600;cursor:help" title="${esc(typeHint)}">${typeIcon} ${esc(m.milestone_type)}</span>` : ''}
              ${m.description && m.description !== m.milestone_type ? `<span style="font-size:13px;font-weight:600">${esc(m.description)}</span>` : `<span style="font-size:13px;font-weight:600">${typeIcon} ${esc(m.milestone_type||m.description)}</span>`}
              ${m.risk_level ? `<span class="chip ${rlCls}" style="font-size:10px;padding:1px 6px">${esc(m.risk_level)}</span>` : ''}
              ${_dyGz ? `<span style="font-size:10px;padding:1px 5px;border-radius:4px;background:rgba(0,0,0,0.05);color:${_dyFavCol};font-weight:600">${esc(_dyGz)}大运·${_dyFavLbl}</span>` : ''}
              ${m.ganzhi_context && m.ganzhi_context !== _dyGz ? `<span style="font-size:11px;color:var(--muted)">${esc(m.ganzhi_context)}</span>` : ''}
            </div>
            ${typeHint ? `<div style="font-size:10px;color:var(--muted);margin-bottom:3px;overflow-wrap:anywhere">📖 ${esc(typeHint)}</div>` : ''}
            ${m.description && showTypeTag ? `<div style="font-size:12px;line-height:1.55;color:var(--text);margin-bottom:3px;overflow-wrap:anywhere;word-break:break-word">${esc(m.description)}</div>` : ''}
            ${(m.advice||_dyNarr) ? `<details style="margin-top:3px"><summary style="font-size:10px;color:var(--accent);cursor:pointer;padding:3px 7px;background:rgba(99,102,241,0.07);border-radius:4px;display:inline-block;list-style:none;user-select:none">💡 建议与大运详情 ▸</summary><div style="margin-top:5px;display:flex;flex-direction:column;gap:5px">${m.advice?`<div style="font-size:12px;line-height:1.65;overflow-wrap:anywhere;word-break:break-word;padding:6px 8px;background:rgba(245,158,11,0.07);border-radius:5px;border-left:2px solid var(--accent-gold,#b87a0a)">💡 ${esc(m.advice)}</div>`:''} ${_dyNarr?`<div style="font-size:11px;color:var(--muted);line-height:1.6;padding:5px 8px;background:rgba(99,102,241,0.05);border-radius:5px;overflow-wrap:anywhere;word-break:break-word">📋 ${esc(_dyNarr)}</div>`:''}</div></details>` : ''}
          </div>
        </div>`;
      }).join('')}
    </div>` : ''}
  </div>` : '';

  /* ══ 卡片④：命局核心分析要点 ═══════════════════
     整合多个子模型的核心要点，带分析注释
  ════════════════════════════════════════════════ */

  // 性格特质
  const _perText = _per5.core_traits || _per5.description || _per5.summary || '';
  // 神煞精华（只取前3个有名字的）
  const _shenshaList = (_sh5.items || []).filter(s => s.name).slice(0,4);
  const _shenshaChips = _shenshaList.map(s => {
    const isGood = (s.is_auspicious === true || s.type === 'auspicious' || (s.effect||'').includes('吉'));
    return `<span class="chip ${isGood?'ok':'warn'}" title="${esc(s.description||s.effect||'')}">${esc(s.name)}</span>`;
  }).join('');
  // 五行偏差（使用 wuxing_weak/strong/balance_advice 字段）
  const _feStrong = (json.wuxing_strong || []).map(_cn5).join('、');
  const _feWeak   = (json.wuxing_weak   || []).map(_cn5).join('、');
  const _feAdvice = json.balance_advice || '';
  const _feSummary = (_feStrong||_feWeak) ? `${_feStrong?'偏旺：'+_feStrong:''}${_feStrong&&_feWeak?' / ':''}${_feWeak?'偏缺：'+_feWeak:''}${_feAdvice?'\n建议：'+_feAdvice:''}` : '';
  // 事业时机（多字段fallback）
  const _careerText = _crr5.optimal_move_timing || _crr5.career_overview || _crr5.description || '';
  // 婚姻/感情
  const _marText = _mar5.emotional_pitfalls || _mar5.marriage_overview || _mar5.description || '';
  // 健康体质
  const _hltText = _hlt5.constitution_type || _hlt5.health_overview || _hlt5.description || '';
  // 逆运警示（完整版）
  const _cautionText = arc.caution_periods?.length
    ? `注意大运：${arc.caution_periods.join('、')}，此阶段逢格局忌神，宜守成稳进，勿贸然决策。${arc.optimal_action ? '\n策略：'+arc.optimal_action : ''}`
    : '';

  const _coreItems = [
    _gj5.geju_detail        ? {icon:'🏛', label:'命局格局分析',  note:'格局层面综合判断', text:_gj5.geju_detail}       : null,
    _perText                ? {icon:'🧠', label:'性格与行为特质', note:'基于日主及格局推演', text:_perText}             : null,
    _shenshaList.length     ? {icon:'✨', label:'主要神煞',       note:'命中关键神煞影响', chips:_shenshaChips, text:''}: null,
    _feSummary              ? {icon:'⚖️', label:'五行偏差',      note:'元素强弱与用忌关联', text:_feSummary}           : null,
    _cautionText            ? {icon:'⚡', label:'逆运警示',      note:'大运走忌神时段建议', text:_cautionText}          : null,
    _marText                ? {icon:'💞', label:'感情与婚姻',    note:'婚姻隐患与感情模式', text:_marText}             : null,
    _hltText                ? {icon:'🌿', label:'健康体质',      note:'体质倾向与调理方向', text:_hltText}: null,
    _careerText             ? {icon:'💼', label:'事业时机',      note:'最佳进取窗口与策略', text:_careerText}          : null,
  ].filter(Boolean);

  const coreContradictionHtml = _coreItems.length ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent-gold,#b87a0a)"></span>命局核心分析要点</p>
    <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px">
      ${_coreItems.map(c => `
      <div style="display:flex;gap:10px;align-items:flex-start;padding:8px 10px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px">
        <span style="font-size:18px;flex-shrink:0;line-height:1">${c.icon}</span>
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:4px;flex-wrap:wrap">
            <span style="font-size:12px;font-weight:700;color:var(--text)">${esc(c.label)}</span>
            ${c.note ? `<span style="font-size:10px;color:var(--muted);font-style:italic">${esc(c.note)}</span>` : ''}
          </div>
          ${c.chips ? `<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:${c.text?'5px':'0'}">${c.chips}</div>` : ''}
          ${c.text ? (c.text.length > 80 ? `<details><summary style="cursor:pointer;list-style:none;font-size:12px;line-height:1.65;color:var(--muted);overflow-wrap:anywhere">${esc(c.text.split('\n')[0].slice(0,70))}${(c.text.split('\n')[0].length>70||c.text.includes('\n'))?'\u2026 <span style="color:var(--accent);font-size:10px">▸ 展开</span>':''}</summary><div style="font-size:11px;line-height:1.7;color:var(--muted);white-space:pre-line;overflow-wrap:anywhere;margin-top:4px">${esc(c.text)}</div></details>` : `<div style="font-size:12px;line-height:1.65;color:var(--muted);white-space:pre-line;overflow-wrap:anywhere;word-break:break-word">${esc(c.text)}</div>`) : ''}
        </div>
      </div>`).join('')}
    </div>
  </div>` : '';

  /* ══ 卡片⑤：校验数据 + 六维评分 + 技术详情 ════
  ════════════════════════════════════════════════ */
  const techHtml = `
  <div class="summary-grid" style="margin-bottom:12px">
    <div class="summary-card"><div class="summary-label">校验级别</div><div class="summary-value">${esc(v.level||'—')}</div><span class="summary-pill ${lvlCls}">${{L0:'无差异',L1:'时柱差异',L2:'月柱差异',L3:'多柱差异'}[v.level]||'—'}</span></div>
    <div class="summary-card"><div class="summary-label">告警数</div><div class="summary-value">${warnings.length}</div><span class="summary-pill ${warnings.length?'warn':'ok'}">${warnings.length?'有告警':'正常'}</span></div>
    <div class="summary-card"><div class="summary-label">格局</div><div class="summary-value" style="font-size:14px">${esc(arc.overall_tier||_gj5.geju_level||'—')}</div></div>
    <div class="summary-card"><div class="summary-label">日主强弱</div><div class="summary-value" style="font-size:14px;color:${strCols5}">${esc(strLabel5)}</div></div>
  </div>
  <div id="scoringRadarContainer" style="margin:0 0 12px"></div>
  ${warnings.length ? `<div class="card" style="margin-bottom:12px;border-left:3px solid var(--warn)">
    <p class="card-title"><span class="dot" style="background:var(--warn)"></span>告警列表 <span class="chip warn" style="font-size:10px;padding:1px 6px">${warnings.length}条</span></p>
    <div class="warnlist">${warnings.map(w=>`<div class="warnitem"><div class="wcode">${esc(w.code||w.type||'WARN')}</div><div class="wmsg">${esc(w.message||w.msg||'')}</div></div>`).join('')}</div>
  </div>` : ''}
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
    ${Object.keys(rt).length ? `<div class="card" style="margin-top:8px"><p class="card-title"><span class="dot"></span>规则版本明细</p><div class="kv">${Object.entries(rt).map(([k,vv])=>`<div class="k">${esc(k)}</div><div><code>${esc(vv)}</code></div>`).join('')}</div></div>` : ''}
  </details>`;

  el.innerHTML = overviewStrip + arcCard + msHtml + coreContradictionHtml + techHtml;

  // 6D 评分条
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

  // 状态汇总横条
  const lvl6 = v.level||'—';
  const lvlColor6 = {L0:'var(--ok)',L1:'var(--ok)',L2:'var(--warn)',L3:'var(--bad)'}[lvl6]||'var(--muted)';
  const warnCount6 = (v.warnings||[]).length;
  const diffCount6 = diffFields.length;
  const statusBannerHtml = `
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px">
    <div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;border-left:3px solid ${lvlColor6}">
      <div style="font-size:10px;color:var(--muted);font-weight:700">校验级别</div>
      <div style="font-size:20px;font-weight:800;color:${lvlColor6}">${esc(lvl6)}</div>
      <div style="font-size:11px;color:var(--muted)">${{L0:'无差异',L1:'时柱差异',L2:'月柱差异',L3:'多柱差异'}[lvl6]||'—'}</div>
    </div>
    <div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;border-left:3px solid ${warnCount6?'var(--warn)':'var(--ok)'}">
      <div style="font-size:10px;color:var(--muted);font-weight:700">告警数量</div>
      <div style="font-size:20px;font-weight:800;color:${warnCount6?'var(--warn)':'var(--ok)'}">${warnCount6}</div>
      <div style="font-size:11px;color:var(--muted)">${warnCount6?'存在告警':'运行正常'}</div>
    </div>
    <div style="padding:10px 12px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;border-left:3px solid ${diffCount6?'var(--bad)':'var(--ok)'}">
      <div style="font-size:10px;color:var(--muted);font-weight:700">差异字段</div>
      <div style="font-size:20px;font-weight:800;color:${diffCount6?'var(--bad)':'var(--ok)'}">${diffCount6}</div>
      <div style="font-size:11px;color:var(--muted)">${diffCount6?diffFields.map(f=>({year:'年',month:'月',day:'日',hour:'时'}[f]||f)).join('/'):'无差异'}</div>
    </div>
  </div>`;

  const renderPillars = (p, diff=[]) => {
    if (!p) return '<div class="hint">无数据</div>';
    return `<table class="pillar-table"><thead><tr><th>柱</th><th>天干</th><th>地支</th><th>干支</th></tr></thead><tbody>
      ${['year','month','day','hour'].map(k=>`<tr class="${diff.includes(k)?'diff-row':''}"><td>${{year:'年',month:'月',day:'日',hour:'时'}[k]}</td><td class="${GAN_CSS[p[k]?.stem]||''}">${esc(p[k]?.stem||'—')}</td><td>${esc(p[k]?.branch||'—')}</td><td>${esc(p[k]?.ganzhi||'—')}</td></tr>`).join('')}
    </tbody></table>`;
  };
  el.innerHTML = statusBannerHtml + `
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
  const w  = json.wealth_analysis || {};
  const wo = json.wealth || {};
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);

  const score      = w.wealth_score ?? wo.wealth_score;
  const tier       = w.wealth_tier  || wo.wealth_range?.label || '';
  const tierColor  = tier==='上'?'var(--ok)':tier==='中'?'#f59e0b':'var(--bad)';
  const scoreColor = score>=70?'var(--ok)':score>=50?'#f59e0b':'var(--bad)';
  const incomeRange= w.annual_range || (wo.wealth_range?.min!=null
    ? `${wo.wealth_range.min}–${wo.wealth_range.max}万/年` : '');

  // ── 当前大运 ────────────────────────────────────────────────────────
  const thisYear7 = new Date().getFullYear();
  const curDY7 = (json.dayun?.items||[]).find(d => {
    const sy = d.start_year ?? (new Date().getFullYear() - (d.start_age ?? 0) + (json.birth_year ?? 0));
    return sy <= thisYear7 && sy + 10 > thisYear7;
  }) || null;
  const curDYGz7   = curDY7 ? (curDY7.ganzhi || (curDY7.stem||'')+(curDY7.branch||'')) : '';

  // ── 用神/忌神 参考（为大运趋势着色） ─────────────────────────────────
  const _favor7 = new Set((json.yongshen?.favor||[]).map(x=>x.toLowerCase()));
  const _avoid7 = new Set((json.yongshen?.avoid||[]).map(x=>x.toLowerCase()));
  const _GZ2EL7 = {甲:'wood',乙:'wood',丙:'fire',丁:'fire',戊:'earth',己:'earth',
                   庚:'metal',辛:'metal',壬:'water',癸:'water',
                   子:'water',丑:'earth',寅:'wood',卯:'wood',辰:'earth',巳:'fire',
                   午:'fire',未:'earth',申:'metal',酉:'metal',戌:'earth',亥:'water'};
  const _trendColor7 = (trend) =>
    trend==='上升'?'var(--ok)':trend==='下降'?'var(--bad)':'#f59e0b';
  const _trendIcon7  = (trend) =>
    trend==='上升'?'▲':trend==='下降'?'▼':'▶';

  /* ═══ 卡片①：英雄区 — 评分 + 层级 + 年收入 ═══════════════════════ */
  const heroCard = `
  <div class="card" style="margin-bottom:14px;padding:16px">
    <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
      <!-- 左：评分圆环 -->
      <div style="text-align:center;min-width:90px">
        <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px">财运综合评分</div>
        <div style="position:relative;display:inline-block">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${score!=null?clamp(score,0,100)*2.136:0} 213.6"
              stroke-dashoffset="53.4" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <div style="font-size:22px;font-weight:900;color:${scoreColor};line-height:1">${score!=null?Math.round(score):'—'}</div>
            <div style="font-size:9px;color:var(--muted)">/ 100</div>
          </div>
        </div>
      </div>
      <!-- 右：层级 + 收入 + 进度条 -->
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          ${tier ? `<span style="font-size:22px;font-weight:900;color:${tierColor}">${esc(tier)}等财运</span>` : ''}
          ${incomeRange ? `<span style="padding:3px 12px;background:rgba(34,138,78,0.1);border-radius:20px;font-size:13px;font-weight:700;color:var(--ok)">💵 ${esc(incomeRange)}</span>` : ''}
        </div>
        ${score!=null ? `
        <div style="margin-bottom:8px">
          <div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;overflow:hidden">
            <div style="height:100%;width:${clamp(score,0,100)}%;background:linear-gradient(90deg,${scoreColor},${scoreColor}aa);border-radius:3px;transition:width .5s"></div>
          </div>
        </div>` : ''}
        ${w.inference_tags?.length ? `<div style="display:flex;flex-wrap:wrap;gap:4px">
          ${w.inference_tags.map(t => {
            const isWarn = t.includes('弱')||t.includes('警示')||t.includes('贫');
            return `<span style="display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;background:${isWarn?'rgba(239,68,68,0.1)':'rgba(34,197,94,0.1)'};color:${isWarn?'var(--bad)':'var(--ok)'}">${esc(t)}</span>`;
          }).join('')}
        </div>` : ''}
        ${w.fact_data?.wealth_tier ? `<div style="font-size:10px;color:var(--muted);margin-top:6px">实证层级：${esc(w.fact_data.wealth_tier)}</div>` : ''}
      </div>
    </div>
    ${(curDY7 && curDYGz7) ? `
    <div style="margin-top:12px;padding:10px 12px;background:rgba(34,197,94,0.07);border-radius:8px;border-left:3px solid var(--ok)">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;flex-wrap:wrap">
        <span style="font-size:10px;font-weight:700;color:var(--ok)">▶ 当前大运 · ${esc(curDYGz7)}</span>
        ${curDY7.start_age!=null?`<span style="font-size:10px;color:var(--muted)">${curDY7.start_age}–${(curDY7.end_age??((curDY7.start_age||0)+10))}岁</span>`:''}
      </div>
      ${curDY7.wealth_hint ? `<div style="font-size:13px;line-height:1.7">${esc(curDY7.wealth_hint)}</div>` : ''}
      ${curDY7.wealth_range?.min!=null ? `<div style="font-size:12px;color:var(--ok);margin-top:4px;font-weight:600">💵 本运年收 ${curDY7.wealth_range.min}–${curDY7.wealth_range.max} 万元</div>` : ''}
    </div>` : ''}
  </div>`;

  /* ═══ 卡片②：财运解读 ════════════════════════════════════════════ */
  const interpCard = w.interpretation_text ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent-gold,#b87a0a)"></span>财运综合解读
      <span style="font-size:10px;color:var(--muted);margin-left:6px;font-weight:400">基于财星力量 · 用神匹配 · 日主强弱</span>
    </p>
    <div style="font-size:13px;line-height:1.8;color:var(--text)">${renderPara(w.interpretation_text)}</div>
  </div>` : '';

  /* ═══ 卡片③：分类分析 — 策略 + 投资偏好 + 财务禁区 ══════════════ */
  const analysisItems = [];

  if (w.strategy) {
    const stratColor = tier==='上'?'var(--ok)':tier==='中'?'#f59e0b':'var(--bad)';
    analysisItems.push(`
    <div style="padding:12px;background:rgba(0,0,0,0.03);border-radius:8px;border-left:3px solid ${stratColor}">
      <div style="font-size:11px;font-weight:700;color:${stratColor};margin-bottom:6px">📋 财运核心策略
        <span style="font-size:10px;font-weight:400;color:var(--muted);margin-left:6px">${tier==='上'?'旺运期—主动进取':tier==='中'?'中运期—稳中求进':'弱运期—守成减负'}</span>
      </div>
      <div style="font-size:13px;line-height:1.75;color:var(--text)">${renderPara(w.strategy)}</div>
    </div>`);
  }

  if (w.investment_preference) {
    analysisItems.push(`
    <div style="padding:12px;background:rgba(34,197,94,0.05);border-radius:8px;border-left:3px solid var(--ok)">
      <div style="font-size:11px;font-weight:700;color:var(--ok);margin-bottom:6px">📈 投资偏好与配置建议
        <span style="font-size:10px;font-weight:400;color:var(--muted);margin-left:6px">基于正财/偏财占比判断</span>
      </div>
      <div style="font-size:13px;line-height:1.75;color:var(--text)">${renderPara(w.investment_preference)}</div>
    </div>`);
  }

  if (w.financial_taboos) {
    // 预构建行 HTML（避免深层模板嵌套中 esc() 失效）
    var _tabooParts = w.financial_taboos.split(/[；;]/).map(function(s){return s.trim();}).filter(Boolean);
    var _tabooRowsHtml = '';
    _tabooParts.forEach(function(p, i) {
      var _sep = i < _tabooParts.length - 1
        ? 'margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(239,68,68,0.12)' : '';
      _tabooRowsHtml +=
        '<div style="display:flex;gap:10px;align-items:flex-start;' + _sep + '">'
        + '<span style="flex-shrink:0;font-weight:700;color:var(--bad);font-size:15px;line-height:1.6;margin-top:1px">⚠</span>'
        + '<div style="flex:1;font-size:12px;line-height:1.75;overflow-wrap:anywhere;word-break:break-word">' + esc(p) + '</div>'
        + '</div>';
    });
    var _tabooHtml =
      '<div style="padding:12px;background:rgba(239,68,68,0.05);border-radius:8px;border-left:3px solid var(--bad)">'
      + '<div style="font-size:11px;font-weight:700;color:var(--bad);margin-bottom:8px">🚫 财务禁区（忌神方向）'
      + '<span style="font-size:10px;font-weight:400;color:var(--muted);margin-left:6px">高风险行业 · 财务操作红线</span></div>'
      + _tabooRowsHtml
      + '</div>';
    analysisItems.push(_tabooHtml);
  }

  if (w.wealth_accumulation_phases) {
    // 先预构建阶段HTML（避免深层模板嵌套）
    const _phaseColors = ['var(--accent-gold,#b87a0a)','var(--ok)','var(--accent)'];
    const _phaseRe = /【([^】]+)】([^【]*)/g;
    const _phaseParts = [];
    let _pm;
    while ((_pm = _phaseRe.exec(w.wealth_accumulation_phases)) !== null) {
      const _txt = _pm[2].trim();
      if (_txt) _phaseParts.push({ label: _pm[1], text: _txt });
    }
    let _phaseRowsHtml = '';
    if (_phaseParts.length) {
      _phaseParts.forEach(function(ph, i) {
        const sepStyle = i < _phaseParts.length - 1
          ? 'margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(99,102,241,0.1)' : '';
        const numBg = _phaseColors[i] || 'var(--muted)';
        _phaseRowsHtml +=
          '<div style="display:flex;gap:10px;align-items:flex-start;' + sepStyle + '">'
          + '<div style="flex-shrink:0;width:22px;height:22px;border-radius:50%;background:' + numBg + ';display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;margin-top:1px">' + (i+1) + '</div>'
          + '<div style="flex:1;min-width:0">'
          + '<div style="font-size:11px;font-weight:700;color:' + numBg + ';margin-bottom:3px">' + esc(ph.label) + '</div>'
          + '<div style="font-size:12px;line-height:1.75;overflow-wrap:anywhere;word-break:break-word">' + esc(ph.text) + '</div>'
          + '</div></div>';
      });
    } else {
      // 降级：以换行分割或直接展示
      const _rawLines = w.wealth_accumulation_phases.split(/\n+/).map(s=>s.trim()).filter(Boolean);
      _rawLines.forEach(function(line, i) {
        _phaseRowsHtml +=
          '<div style="font-size:12px;line-height:1.75;margin-bottom:6px;overflow-wrap:anywhere">' + esc(line) + '</div>';
      });
    }
    analysisItems.push(
      '<div style="padding:12px;background:rgba(99,102,241,0.04);border-radius:8px;border-left:3px solid var(--accent)">'
      + '<div style="font-size:11px;font-weight:700;color:var(--accent);margin-bottom:8px">🗓 财富积累阶段规划'
      + '<span style="font-size:10px;font-weight:400;color:var(--muted);margin-left:6px">按大运周期制定理财路线图</span></div>'
      + _phaseRowsHtml
      + '</div>'
    );
  }

  const analysisCard = analysisItems.length ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent)"></span>财运专项分析</p>
    <div style="display:flex;flex-direction:column;gap:10px;margin-top:6px">
      ${analysisItems.join('')}
    </div>
  </div>` : '';

  /* ═══ 卡片④：适合行业 ════════════════════════════════════════════ */
  const indList = w.industries || [];
  const _indIcons = {'金融':'🏦','律政':'⚖️','机械制造':'⚙️','珠宝':'💎',
    '教育':'📚','医药':'💊','农林':'🌿','食品':'🍱','出版':'📖',
    '贸易':'🤝','运输':'🚛','IT':'💻','资讯':'📡','旅游':'✈️',
    '传媒':'📺','餐饮':'🍜','能源':'⚡','娱乐演艺':'🎭',
    '房地产':'🏢','保险':'🛡️','建筑':'🏗️','农业':'🌾'};
  const indCard = indList.length ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--ok)"></span>适合行业领域
      <span style="font-size:10px;color:var(--muted);margin-left:6px;font-weight:400">基于用神五行方向推荐</span>
    </p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-top:6px">
      ${indList.map((t,i)=>`<div style="text-align:center;padding:10px 8px;background:rgba(34,197,94,0.06);border-radius:8px;border:1px solid rgba(34,197,94,0.15)">
        <div style="font-size:20px;margin-bottom:4px">${_indIcons[t]||'🏢'}</div>
        <div style="font-size:12px;font-weight:700">${esc(t)}</div>
        ${i===0?`<div style="font-size:9px;color:var(--ok);margin-top:2px;font-weight:600">首选</div>`:''}
      </div>`).join('')}
    </div>
  </div>` : '';

  /* ═══ 卡片⑤：大运财运周期 ═════════════════════════════════════════ */
  const fcList = w.dayun_forecast || [];
  const dayunCard = fcList.length ? `
  <div class="card" style="margin-bottom:14px">
    <p class="card-title"><span class="dot" style="background:var(--accent-gold,#b87a0a)"></span>大运财运周期
      <span style="font-size:10px;color:var(--muted);margin-left:6px;font-weight:400">按十年大运逐段拆解财运走势</span>
    </p>
    <!-- 走势概览横条 -->
    <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:12px">
      ${fcList.map(fc=>{
        const tColor = _trendColor7(fc.trend);
        const tIcon  = _trendIcon7(fc.trend);
        return `<div style="flex:1;min-width:56px;text-align:center;padding:7px 5px;background:${fc.trend==='上升'?'rgba(34,197,94,0.08)':fc.trend==='下降'?'rgba(239,68,68,0.08)':'rgba(0,0,0,0.04)'};border-radius:7px;border:1px solid ${tColor}40" title="${esc(fc.description||'')}">
          <div style="font-size:12px;font-weight:800;font-family:var(--font-title,serif)">${esc(fc.ganzhi||'')}</div>
          <div style="font-size:9px;color:var(--muted)">${fc.start_age!=null?fc.start_age+'岁':''}</div>
          <div style="font-size:11px;font-weight:700;color:${tColor}">${tIcon} ${esc(fc.trend||'—')}</div>
        </div>`;
      }).join('')}
    </div>
    <!-- 详情列 -->
    <div style="display:flex;flex-direction:column;gap:6px">
      ${fcList.map(fc=>{
        const tColor = _trendColor7(fc.trend);
        const tIcon  = _trendIcon7(fc.trend);
        const isUp   = fc.trend==='上升';
        const isDown = fc.trend==='下降';
        // 预构建 description 内容（避免 Chrome flex-on-summary 渲染 bug）
        const _fcDescHtml = fc.description
          ? '<div style="padding:10px 12px;font-size:12px;line-height:1.8;background:rgba(0,0,0,0.02);overflow-wrap:anywhere;word-break:break-word;border-top:1px solid ' + tColor + '20">' + esc(fc.description) + '</div>'
          : (fc.trend
            ? '<div style="padding:8px 12px;font-size:11px;color:var(--muted);line-height:1.7">此大运财运走势为【' + esc(fc.trend||'') + '】，暂无详细分析说明。</div>'
            : '');
        return '<details style="border-radius:8px;overflow:hidden;border:1px solid ' + tColor + '30">'
          + '<summary style="list-style:none;cursor:pointer;user-select:none">'
          + '<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:' + (isUp?'rgba(34,197,94,0.06)':isDown?'rgba(239,68,68,0.06)':'rgba(0,0,0,0.03)') + '">'
          + '<span style="font-size:14px;font-weight:800;font-family:var(--font-title,serif);min-width:28px">' + esc(fc.ganzhi||'') + '</span>'
          + '<span style="font-size:11px;font-weight:700;color:' + tColor + ';padding:2px 8px;background:' + tColor + '22;border-radius:10px">' + tIcon + ' ' + esc(fc.trend||'—') + '</span>'
          + (fc.start_age!=null ? '<span style="font-size:10px;color:var(--muted)">' + fc.start_age + '–' + (fc.end_age!=null?fc.end_age:fc.start_age+10) + '岁</span>' : '')
          + '<span style="margin-left:auto;font-size:10px;color:var(--muted)">▸ 展开详情</span>'
          + '</div></summary>'
          + _fcDescHtml
          + '</details>';
      }).join('')}
    </div>
  </div>` : '';

  /* ═══ 底部：风险提示 + 注解 ══════════════════════════════════════ */
  const riskCard = wo.risk_hint ? `
  <div class="card" style="margin-bottom:12px;border-left:3px solid var(--warn)">
    <p class="card-title"><span class="dot" style="background:var(--warn)"></span>风险提示</p>
    <div style="font-size:12px;line-height:1.7">${txt(wo.risk_hint)}</div>
  </div>` : '';

  const noteCard = wo.note ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>财运注解</p>
    <div style="font-size:13px;line-height:1.75">${renderPara(wo.note)}</div>
  </div>` : '';

  el.innerHTML = heroCard + interpCard + analysisCard + indCard + dayunCard + riskCard + noteCard;
  el.insertAdjacentHTML('beforeend',
    '<div class="disclaimer-note" style="margin-top:8px;font-size:10px;color:var(--muted);padding:6px 8px">▲ 年收入区间为基于五行推断的模糊参考，非精密测算，不构成任何投资或财务建议。</div>');
}

/* ══════════════════════════════════════════════════
   Tab 8: 事业 (CareerAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab8(json, el) {
  const c = json.career||{};
  if (!c.career_directions?.length && !c.interpretation_text && !c.career_score) {
    el.innerHTML = '<div style="padding:16px;color:var(--muted);font-size:13px">事业分析需根据格局和用神进一步推算，请先完成命盘排盘。</div>'; return;
  }
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);
  const score = c.career_score;
  const scoreColor = score>=75?'var(--ok)':score>=50?'#f59e0b':'var(--bad)';
  const CAREER_ICON = {'管理':'🏛','教育':'📚','技术':'💻','金融':'📈','医疗':'🏥','法律':'⚖','艺术':'🎨','传媒':'📡','销售':'📢','建筑':'🏗','农':'🌾','军':'⚔','行政':'📋','咨询':'💼','科研':'🔬','餐饮':'🍽'};
  const getCareerIcon = d => Object.entries(CAREER_ICON).find(([k])=>d.includes(k))?.[1]||'▸';
  // 当前大运（无截断）
  const thisYear8 = new Date().getFullYear();
  const curDY8 = (json.dayun?.items||[]).find(d=>d.start_year<=thisYear8&&(d.start_year||0)+10>thisYear8)||null;
  const curDYGz8 = curDY8 ? (curDY8.stem||'')+(curDY8.branch||'') : '';

  /* ── 英雄区：SVG 评分圆环 ── */
  const heroCard = `
  <div class="card" style="margin-bottom:14px;padding:16px">
    <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
      <div style="text-align:center;min-width:90px">
        <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px">事业综合评分</div>
        <div style="position:relative;display:inline-block">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${score!=null?clamp(score,0,100)*2.136:0} 213.6"
              stroke-dashoffset="53.4" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <div style="font-size:22px;font-weight:900;color:${scoreColor};line-height:1">${score!=null?Math.round(score):'—'}</div>
            <div style="font-size:9px;color:var(--muted)">/ 100</div>
          </div>
        </div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <span style="font-size:18px;font-weight:800">⚡ 事业运势</span>
          ${c.leadership_potential?`<span style="padding:3px 10px;background:rgba(34,197,94,0.1);border-radius:20px;font-size:11px;font-weight:700;color:var(--ok)">⭐ 具备领导力</span>`:''}
        </div>
        ${score!=null?`<div style="margin-bottom:8px"><div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;overflow:hidden"><div style="height:100%;width:${clamp(score,0,100)}%;background:linear-gradient(90deg,${scoreColor},${scoreColor}aa);border-radius:3px"></div></div></div>`:''}
        ${c.inference_tags?.length?`<div style="display:flex;flex-wrap:wrap;gap:4px">${c.inference_tags.slice(0,5).map(t=>`<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;background:rgba(59,130,246,0.1);color:#3b82f6">${esc(t)}</span>`).join('')}</div>`:''}
      </div>
    </div>
    ${curDY8?`
    <div style="margin-top:12px;padding:10px 12px;background:rgba(59,130,246,0.07);border-radius:8px;border-left:3px solid #3b82f6">
      <div style="font-size:10px;font-weight:700;color:#3b82f6;margin-bottom:6px">▶ 当前大运 · ${esc(curDYGz8)}${curDY8.start_age!=null?` <span style="font-weight:400;color:var(--muted)">${curDY8.start_age}–${(curDY8.start_age||0)+10}岁</span>`:''}</div>
      ${curDY8.wealth_hint?`<div style="font-size:12px;line-height:1.65;margin-bottom:4px"><span style="color:var(--ok);font-weight:700">💰 财运：</span>${esc(curDY8.wealth_hint)}</div>`:''}
      ${curDY8.love_hint?`<div style="font-size:12px;line-height:1.65"><span style="color:#f43f5e;font-weight:700">❤️ 姻缘：</span>${esc(curDY8.love_hint)}</div>`:''}
    </div>`:''}
  </div>`;

  const dirHtml = c.career_directions?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>职业方向</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:${c.interpretation_text?'12':'0'}px">
      ${c.career_directions.map(d=>`<div style="display:flex;flex-direction:column;align-items:center;gap:5px;padding:10px 6px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:10px;font-size:12px;text-align:center;border:1px solid var(--line)"><span style="font-size:24px">${getCareerIcon(d)}</span><span>${esc(d)}</span></div>`).join('')}
    </div>
    ${c.interpretation_text?`<div style="font-size:13px;line-height:1.7;border-top:1px solid var(--line);padding-top:10px">${renderPara(c.interpretation_text)}</div>`:''}
  </div>` : (c.interpretation_text?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>事业解读</p><div style="font-size:13px;line-height:1.7">${renderPara(c.interpretation_text)}</div></div>`:'');

  el.innerHTML = heroCard + dirHtml + `
  ${c.optimal_move_timing?`<div style="margin-bottom:12px;padding:10px 14px;background:rgba(184,122,10,0.07);border:1px solid rgba(184,122,10,0.2);border-radius:8px"><span style="font-size:11px;font-weight:700;color:var(--accent-gold,#b87a0a)">⏰ 最佳行动时机：</span><span style="font-size:13px">${txt(c.optimal_move_timing)}</span></div>`:''}
  ${(c.development_advice||c.entrepreneurship_assessment)?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>发展建议 &amp; 创业分析</p>${c.development_advice?`<div style="font-size:13px;line-height:1.7;margin-bottom:${c.entrepreneurship_assessment?'10':'0'}px">${renderPara(c.development_advice)}</div>`:''}${c.entrepreneurship_assessment?`<details><summary style="cursor:pointer;font-size:12px;color:var(--accent)"><div style="display:inline">创业 vs 职场评估 ▾</div></summary><div style="font-size:13px;line-height:1.7;padding:8px 0">${renderPara(c.entrepreneurship_assessment)}</div></details>`:''}</div>`:''}
  ${c.five_year_roadmap?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>五年职业路线图</p>${c.five_year_roadmap.length>120?`<details><summary style="cursor:pointer;font-size:12px;color:var(--accent)"><div style="display:inline">展开路线图 ▾</div></summary><div style="font-size:13px;line-height:1.7;padding-top:8px">${renderPara(c.five_year_roadmap)}</div></details>`:`<div style="font-size:13px;line-height:1.7">${renderPara(c.five_year_roadmap)}</div>`}</div>`:''}
  ${c.collaboration_style?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>最佳协作风格</p><div style="font-size:13px;line-height:1.7">${renderPara(c.collaboration_style)}</div></div>`:''}
  ${c.suitable_industries?.length?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>适合行业</p><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:6px">${c.suitable_industries.map(i=>`<div style="padding:7px 6px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:8px;font-size:11px;text-align:center;border:1px solid var(--line)">🏢 ${esc(i)}</div>`).join('')}</div></div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 9: 姻缘 (MarriageAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab9(json, el) {
  const ma = json.marriage_analysis||{};
  const so = json.social||{};
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);
  const score = ma.marriage_score;
  const scoreColor = score>=70?'#f43f5e':score>=50?'#f97316':'var(--muted)';

  // 桃花状态
  const pb = ma.peach_blossom||'';
  const pbColor = pb==='旺'?'#f43f5e':pb==='中'?'var(--warn)':'var(--muted)';
  const pbLabel = pb==='旺'?'🌸 桃花旺':pb==='中'?'🌸 桃花中':pb==='弱'?'🌸 桃花弱':so.taohua_hit?'🌸 桃花星':'';

  // 当前大运感情 cross-ref
  const thisYear9 = new Date().getFullYear();
  const curDY9 = (json.dayun?.items||[]).find(d=>d.start_year<=thisYear9&&(d.start_year||0)+10>thisYear9)||null;
  const curDYGz9 = curDY9 ? (curDY9.stem||'')+(curDY9.branch||'') : '';

  /* ── 英雄区：SVG 评分圆环 ── */
  const heroCard = `
  <div class="card" style="margin-bottom:14px;padding:16px">
    <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
      <div style="text-align:center;min-width:90px">
        <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px">婚恋综合评分</div>
        <div style="position:relative;display:inline-block">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${score!=null?clamp(score,0,100)*2.136:0} 213.6"
              stroke-dashoffset="53.4" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <div style="font-size:22px;font-weight:900;color:${scoreColor};line-height:1">${score!=null?Math.round(score):'—'}</div>
            <div style="font-size:9px;color:var(--muted)">/ 100</div>
          </div>
        </div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
          <span style="font-size:18px;font-weight:800">❤️ 婚恋运势</span>
          ${pbLabel?`<span style="padding:3px 10px;background:rgba(244,63,94,0.12);border-radius:20px;font-size:11px;font-weight:700;color:#f43f5e">${esc(pbLabel)}</span>`:''}
        </div>
        ${ma.optimal_marriage_age?`<div style="font-size:13px;font-weight:600;margin-bottom:6px">💍 最佳婚龄：${esc(ma.optimal_marriage_age)}</div>`:''}
        ${score!=null?`<div style="margin-bottom:6px"><div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;overflow:hidden"><div style="height:100%;width:${clamp(score,0,100)}%;background:linear-gradient(90deg,#f43f5e,#fb7185);border-radius:3px"></div></div></div>`:''}
        ${ma.inference_tags?.length?`<div style="display:flex;flex-wrap:wrap;gap:4px">${ma.inference_tags.slice(0,4).map(t=>`<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;background:rgba(244,63,94,0.1);color:#f43f5e">${esc(t)}</span>`).join('')}</div>`:''}
      </div>
    </div>
    ${curDY9?`
    <div style="margin-top:12px;padding:10px 12px;background:rgba(244,63,94,0.07);border-radius:8px;border-left:3px solid #f43f5e">
      <div style="font-size:10px;font-weight:700;color:#f43f5e;margin-bottom:6px">▶ 当前大运 · ${esc(curDYGz9)}${curDY9.start_age!=null?` <span style="font-weight:400;color:var(--muted)">${curDY9.start_age}–${(curDY9.start_age||0)+10}岁</span>`:''}</div>
      ${curDY9.love_hint?`<div style="font-size:13px;line-height:1.7;margin-bottom:4px">${esc(curDY9.love_hint)}</div>`:''}
      ${curDY9.child_hint?`<div style="font-size:12px;color:var(--muted);padding-top:6px;border-top:1px solid var(--line)"><span style="font-weight:700;color:#6366f1">👶 子女：</span>${esc(curDY9.child_hint)}</div>`:''}
    </div>`:''}
    ${ma.marriage_windows?.length?`
    <div style="margin-top:12px">
      <div style="font-size:10px;color:var(--muted);font-weight:700;margin-bottom:6px">💑 婚恋时间窗口</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px">
        ${ma.marriage_windows.map(w=>`<span style="padding:4px 12px;background:rgba(244,63,94,0.1);border-radius:6px;color:#f43f5e;font-size:12px;font-weight:600">${esc(w)}</span>`).join('')}
      </div>
    </div>`:''}
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

  const taohuaYearsHtml = so.taohua_year_hit?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:#f43f5e"></span>🌸 桃花流年</p>
    <div class="row" style="flex-wrap:wrap">${so.taohua_year_hit.map(y=>`<span class="chip ok" style="font-size:14px;padding:4px 10px">${y}年</span>`).join('')}</div>
  </div>` : '';

  const socialHintHtml9 = so.social_hint ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>感情社交提示</p>
    <div style="font-size:13px;line-height:1.7">${txt(so.social_hint)}</div>
    ${so.relation_conflict!==undefined?`<div style="margin-top:6px;font-size:12px;color:${so.relation_conflict?'var(--bad)':'var(--ok)'}">${so.relation_conflict?'⚠ 命局有人际冲突倾向':'✓ 人际关系基础较顺'}</div>`:''}
  </div>` : '';

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

  el.innerHTML = heroCard + profileHtml + loveWindowHtml + taohuaYearsHtml + childHtml + mfHtml + socialHintHtml9 + `
  ${ma.emotional_pitfalls?`<div class="card" style="margin-bottom:12px;border-left:3px solid var(--bad)"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>情感禁区</p><div style="font-size:13px;line-height:1.7">${renderPara(ma.emotional_pitfalls)}</div></div>`:''}
  ${ma.second_marriage_indicator?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>再婚 / 感情波折指标</p><div style="font-size:13px;line-height:1.7">${renderPara(ma.second_marriage_indicator)}</div></div>`:''}

  <!-- ══ 合婚分析面板 ══ -->
  <div class="card" id="compat_panel_9" style="margin-top:16px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px">
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:22px">💑</span>
        <div>
          <div style="font-size:14px;font-weight:800;color:var(--text)">合婚 · 八字相配分析</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px">选择两个已保存的命盘，从五行用神、地支冲合角度综合判断匹配度</div>
        </div>
      </div>
      <span id="compat_status_9" style="font-size:11px;color:var(--muted);padding:3px 8px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:20px"></span>
    </div>

    <!-- 案例选择双列 -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
      <div>
        <div style="font-size:10px;color:var(--muted);font-weight:700;letter-spacing:.06em;margin-bottom:5px">👨 甲方 / 男方命盘</div>
        <select id="compat_case_a_9" style="width:100%;padding:6px 8px;border-radius:6px;border:1px solid var(--line);background:var(--bg);font-size:12px">
          <option value="">── 选择案例 ──</option>
        </select>
      </div>
      <div>
        <div style="font-size:10px;color:var(--muted);font-weight:700;letter-spacing:.06em;margin-bottom:5px">👩 乙方 / 女方命盘</div>
        <select id="compat_case_b_9" style="width:100%;padding:6px 8px;border-radius:6px;border:1px solid var(--line);background:var(--bg);font-size:12px">
          <option value="">── 选择案例 ──</option>
        </select>
      </div>
    </div>

    <!-- 操作按钮行 -->
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:14px;flex-wrap:wrap">
      <button id="compat_btn_load_9" style="font-size:12px;padding:6px 14px;background:var(--bg2,rgba(0,0,0,0.05));border:1px solid var(--line);border-radius:6px;cursor:pointer">🔄 加载案例列表</button>
      <button id="compat_btn_run_9" style="font-size:12px;padding:7px 18px;background:#f43f5e;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:700;letter-spacing:.04em">💑 开始合婚分析</button>
      <div style="font-size:11px;color:var(--muted);flex:1;min-width:100px" id="compat_hint_9">需登录并选择两个命盘案例（可在「案例」面板中保存命盘）</div>
    </div>

    <!-- 结果区 -->
    <div id="compat_result_9"></div>
  </div>
  `;

  /* ── 合婚面板交互逻辑 ───────────────────────────────────────── */
  (function _setupCompatPanel() {
    var _getTok = function() {
      return localStorage.getItem('access_token')
        || localStorage.getItem('token')
        || sessionStorage.getItem('access_token')
        || '';
    };
    var _setStatus = function(msg, ok) {
      var s = document.getElementById('compat_status_9');
      if (s) { s.textContent = msg; s.style.color = ok===false ? 'var(--bad)' : ok===true ? 'var(--ok)' : 'var(--muted)'; }
    };
    var _setHint = function(msg) {
      var h = document.getElementById('compat_hint_9');
      if (h) h.textContent = msg;
    };
    var WX_MAP = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};
    var WX_CLS = {wood:'wx-wood',fire:'wx-fire',earth:'wx-earth',metal:'wx-metal',water:'wx-water'};

    var _loadCases = async function() {
      var tok = _getTok();
      if (!tok) { _setStatus('未检测到 Token，请先登录', false); _setHint('在「案例」面板输入 Token 并保存后，点击"加载案例列表"'); return; }
      _setStatus('加载中…');
      try {
        var r = await fetch('/api/v1/cases?page_size=80', { headers: { Authorization: 'Bearer ' + tok } });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        var data = await r.json();
        var cases = data.items || data || [];
        var opts = cases.map(function(c) {
          var label = (c.name || c.id.slice(0,8)) + ' · ' + ((c.birth_dt_local||'').slice(0,10)) + (c.sex ? ' · ' + c.sex : '');
          return '<option value="' + c.id + '">' + label + '</option>';
        }).join('');
        var emptyA = '<option value="">── 选择甲方 ──</option>';
        var emptyB = '<option value="">── 选择乙方 ──</option>';
        var sa = document.getElementById('compat_case_a_9');
        var sb = document.getElementById('compat_case_b_9');
        if (sa) sa.innerHTML = emptyA + opts;
        if (sb) sb.innerHTML = emptyB + opts;
        _setStatus('已加载 ' + cases.length + ' 个案例', true);
        _setHint('选择甲方和乙方命盘后，点击"开始合婚分析"');
      } catch(e) { _setStatus('加载失败: ' + e.message, false); }
    };

    var _renderResult = function(data) {
      var box = document.getElementById('compat_result_9');
      if (!box || !data) return;
      var ca = data.case_a, cb = data.case_b, result = data.result;
      var score = result.compatibility_score;
      var scoreColor = score >= 75 ? 'var(--ok)' : score >= 55 ? '#f59e0b' : 'var(--bad)';
      var scoreLabel = score >= 80 ? '❤️ 高度匹配' : score >= 65 ? '💕 较为匹配' : score >= 50 ? '🤝 基本相容' : '⚠️ 需要调和';
      var supports = result.support_points || [];
      var conflicts = result.conflict_points || [];

      function wxBadge(el) {
        if (!el) return '—';
        return '<span class="' + (WX_CLS[el]||'') + '" style="font-weight:800">' + (WX_MAP[el]||el) + '</span>';
      }
      function favorChips(arr) {
        return (arr||[]).map(function(e){ return '<span class="' + (WX_CLS[e]||'') + '" style="font-size:11px;padding:2px 6px;border-radius:10px;background:rgba(0,0,0,0.04)">' + (WX_MAP[e]||e) + '</span>'; }).join('');
      }

      var supportRows = supports.map(function(p) {
        return '<div style="font-size:11px;line-height:1.6;padding:4px 0;border-bottom:1px solid rgba(0,0,0,0.04);display:flex;align-items:flex-start;gap:5px"><span style="color:var(--ok);flex-shrink:0">✓</span><span>' + p.detail + '</span></div>';
      }).join('');
      var conflictRows = conflicts.map(function(p) {
        return '<div style="font-size:11px;line-height:1.6;padding:4px 0;border-bottom:1px solid rgba(0,0,0,0.04);display:flex;align-items:flex-start;gap:5px"><span style="color:var(--bad);flex-shrink:0">⚡</span><span>' + p.detail + '</span></div>';
      }).join('');

      box.innerHTML =
        '<div style="border-top:2px dashed rgba(244,63,94,0.25);padding-top:16px">' +
          '<div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:start;margin-bottom:14px">' +
            '<div style="text-align:center">' +
              '<div style="position:relative;display:inline-block">' +
                '<svg width="90" height="90" viewBox="0 0 80 80">' +
                  '<circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>' +
                  '<circle cx="40" cy="40" r="34" fill="none" stroke="' + scoreColor + '" stroke-width="7" stroke-dasharray="' + (Math.min(Math.max(score,0),100)*2.136) + ' 213.6" stroke-dashoffset="53.4" stroke-linecap="round"/>' +
                '</svg>' +
                '<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">' +
                  '<div style="font-size:22px;font-weight:900;color:' + scoreColor + ';line-height:1">' + Math.round(score) + '</div>' +
                  '<div style="font-size:9px;color:var(--muted)">/ 100</div>' +
                '</div>' +
              '</div>' +
              '<div style="font-size:11px;font-weight:700;color:' + scoreColor + ';margin-top:4px">' + scoreLabel + '</div>' +
            '</div>' +
            '<div>' +
              '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px">' +
                '<div style="font-size:13px;font-weight:800">' + (ca.name||'甲方') + '</div>' +
                '<div style="font-size:11px;color:var(--muted)">主元：' + wxBadge(ca.dominant_element) + '</div>' +
                '<span style="color:#f43f5e;font-size:18px;margin:0 4px">♥</span>' +
                '<div style="font-size:13px;font-weight:800">' + (cb.name||'乙方') + '</div>' +
                '<div style="font-size:11px;color:var(--muted)">主元：' + wxBadge(cb.dominant_element) + '</div>' +
              '</div>' +
              '<div style="font-size:12px;color:var(--muted);margin-bottom:8px">' + (result.summary||'') + '</div>' +
              (result.advice ? '<div style="font-size:12px;line-height:1.7;padding:8px 12px;background:rgba(244,63,94,0.06);border-radius:8px;border-left:3px solid #f43f5e">' + result.advice + '</div>' : '') +
              (ca.yongshen_favor?.length||cb.yongshen_favor?.length ? '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;align-items:center"><span style="font-size:10px;color:var(--muted);font-weight:700">甲喜用：</span>' + favorChips(ca.yongshen_favor) + '<span style="font-size:10px;color:var(--muted);font-weight:700;margin-left:6px">乙喜用：</span>' + favorChips(cb.yongshen_favor) + '</div>' : '') +
            '</div>' +
          '</div>' +
          ((supports.length || conflicts.length) ?
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
              (supports.length ? '<div style="padding:10px 12px;background:rgba(34,197,94,0.05);border-radius:8px;border:1px solid rgba(34,197,94,0.15)"><div style="font-size:10px;font-weight:700;color:var(--ok);margin-bottom:6px;letter-spacing:.04em">相助 ' + supports.length + ' 项</div>' + supportRows + '</div>' : '') +
              (conflicts.length ? '<div style="padding:10px 12px;background:rgba(239,68,68,0.05);border-radius:8px;border:1px solid rgba(239,68,68,0.15)"><div style="font-size:10px;font-weight:700;color:var(--bad);margin-bottom:6px;letter-spacing:.04em">相冲 ' + conflicts.length + ' 项</div>' + conflictRows + '</div>' : '') +
            '</div>'
          : '') +
        '</div>';
    };

    var _runCompat = async function() {
      var a = (document.getElementById('compat_case_a_9')||{}).value;
      var b = (document.getElementById('compat_case_b_9')||{}).value;
      if (!a || !b) { _setStatus('请先选择两个案例', false); return; }
      if (a === b) { _setStatus('两个案例不能相同', false); return; }
      var tok = _getTok();
      if (!tok) { _setStatus('需要 Token 才能分析', false); return; }
      var btn = document.getElementById('compat_btn_run_9');
      var resultEl = document.getElementById('compat_result_9');
      if (btn) { btn.disabled = true; btn.textContent = '分析中…'; }
      _setStatus('八字对照计算中…'); if(resultEl) resultEl.innerHTML = '';
      try {
        var r = await fetch('/api/v1/relations/compat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tok },
          body: JSON.stringify({ case_a_id: a, case_b_id: b, relation_type: 'couple' })
        });
        if (!r.ok) { var e = await r.json().catch(function(){return {};}); throw new Error(e.message || e.detail || r.status); }
        var data = await r.json();
        _renderResult(data);
        _setStatus('分析完成 · ' + Math.round(data.result.compatibility_score) + '分', true);
        if (window.RelationShared) window.RelationShared.setResult(data);
      } catch(e) { _setStatus('计算失败: ' + e.message, false); }
      finally { if (btn) { btn.disabled = false; btn.textContent = '💑 开始合婚分析'; } }
    };

    var btnLoad = document.getElementById('compat_btn_load_9');
    var btnRun = document.getElementById('compat_btn_run_9');
    if (btnLoad) btnLoad.addEventListener('click', _loadCases);
    if (btnRun) btnRun.addEventListener('click', _runCompat);

    // 如果 RelationShared 有上次结果，直接回显
    var _shared = window.RelationShared && window.RelationShared.getState ? window.RelationShared.getState() : null;
    if (_shared && _shared.lastResult) {
      _renderResult(_shared.lastResult);
      _setStatus('上次结果：' + Math.round(_shared.lastResult.result.compatibility_score) + '分', true);
    }
    // Token 存在时自动加载案例
    if (_getTok()) { setTimeout(_loadCases, 100); }
  })();
}

/* ══════════════════════════════════════════════════
   Tab 10: 健康 (HealthAnalysisModel)
═══════════════════════════════════════════════════ */
function renderTab10(json, el) {
  const h = json.health||{};
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);
  const score = h.health_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'#f59e0b':'var(--bad)';

  // 当前大运健康 cross-ref
  const thisYear10 = new Date().getFullYear();
  const curDY10 = (json.dayun?.items||[]).find(d=>d.start_year<=thisYear10&&(d.start_year||0)+10>thisYear10)||null;
  const curDYGz10 = curDY10 ? (curDY10.stem||'')+(curDY10.branch||'') : '';

  /* ── 英雄区：SVG 评分圆环 ── */
  const heroCard = `
  <div class="card" style="margin-bottom:14px;padding:16px">
    <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
      <div style="text-align:center;min-width:90px">
        <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px">健康综合评分</div>
        <div style="position:relative;display:inline-block">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${score!=null?clamp(score,0,100)*2.136:0} 213.6"
              stroke-dashoffset="53.4" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <div style="font-size:22px;font-weight:900;color:${scoreColor};line-height:1">${score!=null?Math.round(score):'—'}</div>
            <div style="font-size:9px;color:var(--muted)">/ 100</div>
          </div>
        </div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
          <span style="font-size:18px;font-weight:800">♡ 健康运势</span>
          ${h.risk_level?`<span style="padding:3px 10px;background:${h.risk_level.includes('高')||h.risk_level.includes('重')?'rgba(239,68,68,0.1)':'rgba(245,158,11,0.1)'};border-radius:20px;font-size:11px;font-weight:700;color:${h.risk_level.includes('高')||h.risk_level.includes('重')?'var(--bad)':'#f59e0b'}">⚠ ${esc(h.risk_level)}</span>`:''}
        </div>
        ${h.risk_organs?.length
          ?`<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px">${h.risk_organs.map(r=>`<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;background:rgba(239,68,68,0.1);color:var(--bad)">⚠ ${esc(r)}</span>`).join('')}</div>`
          :`<div style="font-size:12px;color:var(--ok);font-weight:600;margin-bottom:6px">✓ 无明显高风险脏腑</div>`}
        ${score!=null?`<div><div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;overflow:hidden"><div style="height:100%;width:${clamp(score,0,100)}%;background:linear-gradient(90deg,#22c55e,#86efac);border-radius:3px"></div></div></div>`:''}
      </div>
    </div>
    ${curDY10?.health_hint?`
    <div style="margin-top:12px;padding:10px 12px;background:rgba(34,197,94,0.07);border-radius:8px;border-left:3px solid var(--ok)">
      <div style="font-size:10px;font-weight:700;color:var(--ok);margin-bottom:6px">▶ 当前大运健康提示 · ${esc(curDYGz10)}${curDY10.start_age!=null?` <span style="font-weight:400;color:var(--muted)">${curDY10.start_age}–${(curDY10.start_age||0)+10}岁</span>`:''}</div>
      <div style="font-size:13px;line-height:1.7">${esc(curDY10.health_hint)}</div>
    </div>`:''}
  </div>`;

  // 五行器官风险图
  const WX_DEFAULT_ORGANS = {'木':'肝·胆','火':'心·小肠','土':'脾·胃','金':'肺·大肠','水':'肾·膀胱'};
  const WX_EN = {'木':'wood','火':'fire','土':'earth','金':'metal','水':'water'};
  const WX_DISEASE = {'木':'肝炎/脂肪肝/眼疾','火':'心血管/高血压','土':'脾胃/妇科问题','金':'呼吸/肺炎','水':'肾虚/泌尿系统'};
  const organMapHtml = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>五行器官风险图</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
      ${Object.entries(WX_DEFAULT_ORGANS).map(([cn, organs]) => {
        const isRisk = h.risk_organs?.some(r=>organs.includes(r)||r.includes(cn));
        const enKey = WX_EN[cn];
        return `<div style="padding:8px 10px;border-radius:8px;border:1px solid var(--line);${isRisk?'border-left:3px solid var(--bad);background:rgba(192,57,43,0.05);':''}">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
            <span class="wx-${enKey}" style="font-size:14px;font-weight:800">${cn}</span>
            ${isRisk?'<span style="font-size:10px;color:var(--bad);font-weight:700">⚠ 注意</span>':''}
          </div>
          <div style="font-size:12px;margin-bottom:2px">${esc(organs)}</div>
          <div style="font-size:10px;color:var(--muted)">${esc(WX_DISEASE[cn]||'')}</div>
        </div>`;
      }).join('')}
    </div>
  </div>`;

  const hInferTagHtml = h.inference_tags?.length ? `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>健康标签</p>
    <div class="row" style="flex-wrap:wrap">${h.inference_tags.map(t=>`<span class="chip${/风险|高|注意|警/.test(t)?' warn':''}">${/风险|高|注意|警/.test(t)?'⚠ ':''}${esc(t)}</span>`).join('')}</div>
  </div>` : '';

  el.innerHTML = heroCard + hInferTagHtml + organMapHtml + `
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
  const clamp = (v,a,b) => Math.min(Math.max(v,a),b);
  const score = r.relationship_score;
  const scoreColor = score>=70?'var(--ok)':score>=50?'#f59e0b':'var(--bad)';

  // 当前大运人际 cross-ref（child_hint 不截断）
  const _thisYear11 = new Date().getFullYear();
  const _curDY11 = (json.dayun?.items||[]).find(d=>d.start_year<=_thisYear11&&(d.start_year||0)+10>_thisYear11)||null;
  const _curDYGz11 = _curDY11 ? (_curDY11.stem||'')+(_curDY11.branch||'') : '';

  /* ── 英雄区：SVG 评分圆环 ── */
  const heroCard = score != null ? `
  <div class="card" style="margin-bottom:14px;padding:16px">
    <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
      <div style="text-align:center;min-width:90px">
        <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:4px">人际综合评分</div>
        <div style="position:relative;display:inline-block">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(0,0,0,0.06)" stroke-width="7"/>
            <circle cx="40" cy="40" r="34" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${clamp(score,0,100)*2.136} 213.6"
              stroke-dashoffset="53.4" stroke-linecap="round"/>
          </svg>
          <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
            <div style="font-size:22px;font-weight:900;color:${scoreColor};line-height:1">${Math.round(score)}</div>
            <div style="font-size:9px;color:var(--muted)">/ 100</div>
          </div>
        </div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
          <span style="font-size:18px;font-weight:800">🤝 人际关系</span>
        </div>
        ${r.inference_tags?.length?`<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px">${r.inference_tags.slice(0,5).map(t=>`<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600;background:rgba(167,139,250,0.1);color:#a78bfa">${esc(t)}</span>`).join('')}</div>`:''}
        <div style="height:6px;background:rgba(0,0,0,0.06);border-radius:3px;overflow:hidden"><div style="height:100%;width:${clamp(score,0,100)}%;background:linear-gradient(90deg,var(--accent),#a78bfa);border-radius:3px"></div></div>
      </div>
    </div>
    ${_curDY11?`
    <div style="margin-top:12px;padding:10px 12px;background:rgba(167,139,250,0.07);border-radius:8px;border-left:3px solid #a78bfa">
      <div style="font-size:10px;font-weight:700;color:#a78bfa;margin-bottom:6px">▶ 当前大运人际 · ${esc(_curDYGz11)}${_curDY11.start_age!=null?` <span style="font-weight:400;color:var(--muted)">${_curDY11.start_age}–${(_curDY11.start_age||0)+10}岁</span>`:''}</div>
      ${_curDY11.love_hint?`<div style="font-size:13px;line-height:1.7;margin-bottom:4px">${esc(_curDY11.love_hint)}</div>`:''}
      ${_curDY11.child_hint?`<div style="font-size:12px;color:var(--muted);padding-top:6px;border-top:1px solid var(--line)">👶 ${esc(_curDY11.child_hint)}</div>`:''}
    </div>`:''}
  </div>` : '';

  /* 六亲解读 */
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

  const peopleHtml = (nobles.length||pettys.length) ? `
  <div class="g2" style="margin-bottom:12px">
    ${nobles.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--ok)"></span>贵人方向</p><div class="people-grid">${nobles.map(p=>`<span class="ppl-chip ok">★ ${esc(p)}</span>`).join('')}</div></div>`:''}
    ${pettys.length?`<div class="card"><p class="card-title"><span class="dot" style="background:var(--bad)"></span>小人方向</p><div class="people-grid">${pettys.map(p=>`<span class="ppl-chip bad">✕ ${esc(p)}</span>`).join('')}</div></div>`:''}
  </div>` : '';

  el.innerHTML = heroCard + `
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

  // 优势/劣势 → icon 卡片化
  const advCards = p.advantages?.length
    ? `<div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:var(--ok)"></span>优势特质</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px;margin-top:6px">
      ${p.advantages.map(s=>`<div style="padding:7px 10px;background:rgba(45,138,78,0.06);border-radius:8px;border-left:3px solid var(--ok);font-size:12px;line-height:1.5">✓ ${esc(s)}</div>`).join('')}
    </div></div>` : '';
  const disCards = p.disadvantages?.length
    ? `<div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot" style="background:var(--bad)"></span>需注意之处</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px;margin-top:6px">
      ${p.disadvantages.map(s=>`<div style="padding:7px 10px;background:rgba(192,57,43,0.06);border-radius:8px;border-left:3px solid var(--bad);font-size:12px;line-height:1.5">✕ ${esc(s)}</div>`).join('')}
    </div></div>` : '';

  el.innerHTML = stemHeroHtml + `
  ${p.interpretation_text||p.day_stem_trait?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>性格综述</p><div style="font-size:13px;line-height:1.7">${renderPara(p.interpretation_text||p.day_stem_trait)}</div>${p.strength_modifier?`<div style="font-size:11px;color:var(--muted);margin-top:6px">${txt('（'+p.strength_modifier+'）')}</div>`:''}</div>`:''}
  ${advCards}${disCards}
  ${p.growth_advice?`<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>成长建议</p><div style="font-size:13px;line-height:1.7">${renderPara(p.growth_advice)}</div></div>`:''}
  ${p.communication_style?`
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>💬 沟通风格</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(p.communication_style)}</div>
  </div>`:''}
  ${p.stress_coping_mode?`
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>⚙ 压力应对模式</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(p.stress_coping_mode)}</div>
  </div>`:''}
  ${p.potential_activation?`
  <div class="card">
    <p class="card-title"><span class="dot"></span>✨ 潜能激活时机</p>
    <div style="font-size:13px;line-height:1.7">${renderPara(p.potential_activation)}</div>
  </div>`:''}
  `;
}

/* ══════════════════════════════════════════════════
   Tab 13: 风水 (FengshuiModel, M4.05)
═══════════════════════════════════════════════════ */
function renderTab13(json, el) {
  const f = json.fengshui||{};
  // 方位罗盘可视化
  const DIR_POS = {
    '北': {top:'0',left:'50%',transform:'translate(-50%,0)'},
    '东北': {top:'8%',left:'85%',transform:'translate(-50%,0)'},
    '东': {top:'50%',left:'100%',transform:'translate(-100%,-50%)'},
    '东南': {top:'85%',left:'85%',transform:'translate(-50%,-100%)'},
    '南': {top:'100%',left:'50%',transform:'translate(-50%,-100%)'},
    '西南': {top:'85%',left:'8%',transform:'translate(0,-100%)'},
    '西': {top:'50%',left:'0',transform:'translate(0,-50%)'},
    '西北': {top:'8%',left:'8%',transform:'translate(0,0)'},
  };
  const auspDirs = f.auspicious_directions||[];
  const compassHtml = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>吉利方位</p>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">
      ${['北','东北','东','东南','南','西南','西','西北'].map(d=>{
        const isAusp = auspDirs.some(a=>a.includes(d)||d.includes(a));
        return `<div style="padding:6px 14px;border-radius:20px;border:2px solid ${isAusp?'var(--ok)':'var(--line)'};background:${isAusp?'rgba(45,138,78,0.08)':'transparent'};font-size:13px;font-weight:${isAusp?'700':'400'};color:${isAusp?'var(--ok)':'var(--muted)'}">${isAusp?'✓ ':''} ${esc(d)}</div>`;
      }).join('')}
    </div>
    ${f.lucky_colors?.length?`<div style="margin-top:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
      <span style="font-size:11px;color:var(--muted);font-weight:700">吉利颜色：</span>${f.lucky_colors.map(c=>{
        const HEX={'红':'#ef4444','橙':'#f97316','黄':'#eab308','绿':'#22c55e','青':'#06b6d4','蓝':'#3b82f6','紫':'#a855f7','白':'#94a3b8','黑':'#334155','金':'#f59e0b','粉':'#f43f5e','棕':'#92400e','灰':'#6b7280'};
        const hex=Object.entries(HEX).find(([k])=>c.includes(k))?.[1]||'var(--accent)';
        return `<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px"><span style="width:14px;height:14px;border-radius:50%;background:${hex};display:inline-block"></span>${esc(c)}</span>`;
      }).join('')}</div>`:''}
  </div>`;

  el.innerHTML = compassHtml + `
  <div class="card" style="margin-bottom:12px">
      <p class="card-title"><span class="dot"></span>布局建议</p>
      ${f.decor?.length?`<ul class="panel-list">${f.decor.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:'<div class="hint">暂无</div>'}
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

  // primary / secondary — 大卡片样式
  const WX_CLR={'木':'#4ade80','火':'#f87171','土':'#fbbf24','金':'#e2e8f0','水':'#93c5fd'};
  const renderJewelItem = (item, label) => {
    if (!item) return '';
    const title = [item.material, item.gemstone].filter(Boolean).join(' · ');
    const wxColor = WX_CLR[item.wuxing]||'var(--line)';
    return `<div class="card" style="border-top:3px solid ${wxColor};padding-top:12px">
      <div style="font-size:10px;text-transform:uppercase;font-weight:700;color:var(--muted);letter-spacing:.08em;margin-bottom:6px">${esc(label)}</div>
      ${title?`<div style="font-size:18px;font-weight:700;margin-bottom:6px">💎 ${esc(title)}</div>`:''}
      ${item.wuxing?`<span class="chip" style="background:${wxColor};color:#fff;font-size:11px;font-weight:700">${esc(item.wuxing)}</span>`:''}
      ${item.position?`<div style="font-size:12px;color:var(--muted);margin-top:8px">📍 佩戴位置：${esc(item.position)}</div>`:''}
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

  // ── 顶部汇总条 ──────────────────────────────
  const summaryHtml = `
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;padding:10px 14px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:10px;align-items:center">
    ${lk.lucky_numbers?.length?`<div style="text-align:center"><div style="font-size:9px;color:var(--muted);font-weight:700;margin-bottom:3px">幸运数</div><div style="font-size:14px;font-weight:800;color:var(--accent)">${lk.lucky_numbers.slice(0,3).join(' · ')}</div></div>`:''}      
    ${lk.lucky_direction?`<div style="text-align:center"><div style="font-size:9px;color:var(--muted);font-weight:700;margin-bottom:3px">吉方</div><div style="font-size:14px;font-weight:800;color:var(--ok)">${esc(lk.lucky_direction)}</div></div>`:''}
    ${lk.lucky_item?`<div style="text-align:center"><div style="font-size:9px;color:var(--muted);font-weight:700;margin-bottom:3px">开运物</div><div style="font-size:13px;font-weight:700">🔮 ${esc(lk.lucky_item)}</div></div>`:''}
    ${lk.lucky_colors?.length?`<div style="flex:1;min-width:120px"><div style="font-size:9px;color:var(--muted);font-weight:700;margin-bottom:3px">吉色</div><div style="display:flex;gap:5px;flex-wrap:wrap">${lk.lucky_colors.slice(0,4).map(c=>{const HEX={'红':'#ef4444','橙':'#f97316','黄':'#eab308','绿':'#22c55e','青':'#06b6d4','蓝':'#3b82f6','紫':'#a855f7','白':'#94a3b8','黑':'#334155','金':'#f59e0b','粉':'#f43f5e','棕':'#92400e','灰':'#6b7280'};const h=Object.entries(HEX).find(([k])=>c.includes(k))?.[1]||'var(--accent)';return `<span style="display:inline-flex;align-items:center;gap:3px;font-size:11px"><span style="width:12px;height:12px;border-radius:50%;background:${h};display:inline-block"></span>${esc(c)}</span>`;}).join('')}</div></div>`:''}
  </div>`;

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

  el.innerHTML = summaryHtml + numHtml + colorHtml + dirHtml + `
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

  const methodCard = `<div class="card" style="margin-bottom:12px"><p class="card-title"><span class="dot"></span>大运推算方法</p><div class="kv"><div class="k">方法</div><div>${esc(dy.method||'—')}</div><div class="k">边界</div><div>${esc(dy.boundary||'—')}</div>${preciseStartAge != null ? `<div class="k">起运岁数</div><div><strong>${preciseStartAge}岁</strong>${dy.start_age_months?` (${dy.start_age_months}月)`:''}</div>` : ''}${directionHtml}${dy.anchor_jieqi_name?`<div class="k">参考节气</div><div>${esc(dy.anchor_jieqi_name)}${dy.anchor_jieqi_dt?` <span style="color:var(--muted);font-size:11px">(${esc(dy.anchor_jieqi_dt.slice(0,10))})</span>`:''}</div>`:''}</div></div>`;

  // dim helper: 4维展示卡片
  const dim16 = (icon, label, text) => {
    if (!text) return '';
    return `<div style="background:var(--bg2,#f8f7f5);border-radius:6px;padding:10px"><div style="font-size:11px;color:var(--muted);margin-bottom:4px">${icon} ${label}</div><div style="font-size:12px;line-height:1.6">${esc(text)}</div></div>`;
  };

  const cardsHtml = items.map((d, di) => {
    const cur = isCurrent(d);
    const endAge = d.start_age != null ? d.start_age + 10 : '?';
    const wr = d.wealth_range;
    const wrTag = wr ? `<span style="font-size:11px;color:var(--ok,#2a7a3b);background:rgba(42,122,59,.08);border-radius:4px;padding:2px 6px">💰 ${wr.min}–${wr.max}万/年</span>` : '';
    const wSnip = d.wealth_hint ? d.wealth_hint.slice(0,55) + (d.wealth_hint.length>55?'…':'') : '';
    const tgBadge = d.ten_god ? `<span class="tengod-badge ${tenGodType(d.ten_god)}">${tenGodCN(d.ten_god)}</span>` : '';
    const fwBadge = d.flow_wuxing ? `<span class="chip wx-${d.flow_wuxing}" style="font-size:10px;padding:2px 6px">${typeof wxCN==='function'?wxCN(d.flow_wuxing):d.flow_wuxing}</span>` : '';
    const liunianGrid = (() => {
      const sy = d.start_year;
      if (!sy) return '';
      const liunianSrc = cur ? (json.liunian_detail||[]) : [];
      const years = Array.from({length:10},(_,i)=>sy+i);
      const cells = years.map(y=>{
        const ld = liunianSrc.find(l=>l.year===y);
        const gz = ld ? (ld.ganzhi||(ld.stem||'')+(ld.branch||'')) : _yearGanzhi(y);
        const score = ld?.annual_score;
        const isCurYear = y===thisYear;
        const df = ld?.domain_forecasts || {};
        const dfTooltip = ['财运','事业','婚恋','健康'].filter(k=>df[k]).map(k=>`${k}：${df[k]}`).join('\n');
        return `<div style="text-align:center;padding:4px 6px;border-radius:4px;background:var(--bg2,#f5f4f0)${isCurYear?';box-shadow:0 0 0 2px var(--accent)':''}${score!=null?`;border-bottom:3px solid ${score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)'}`:''}" title="${dfTooltip?`${y}年\n${dfTooltip}`:''}"><div style="font-size:11px${isCurYear?';font-weight:700;color:var(--accent)':''}">${y}</div><div style="font-size:12px">${gz}</div>${score!=null?`<div style="font-size:10px;color:${score>=70?'var(--ok)':score>=50?'var(--warn)':'var(--bad)'}">${score}</div>`:''}</div>`;
      }).join('');
      return `<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-top:8px">${cells}</div>`;
    })();
    const refsHtml = (d.refs&&d.refs.length) ? `<div style="margin-top:10px;font-size:11px;line-height:1.7;font-style:italic;color:var(--muted);font-family:var(--font-title)">📚 ${d.refs.map(r=>`<span style="color:var(--accent-gold)">《${esc(r.source||'')}》</span>${txt(r.text||'')}`).join(' ／ ')}</div>` : '';
    const narrativeHtml = d.narrative ? `<div style="margin-top:8px;font-size:12px;line-height:1.7;color:var(--muted)">${esc(d.narrative.slice(0,120))}${d.narrative.length>120?`…<details style="display:inline"><summary style="font-size:11px;color:var(--accent);cursor:pointer;margin-left:4px">展开全文 ▾</summary><div style="font-size:12px;line-height:1.7;padding:6px 0">${renderPara(d.narrative)}</div></details>`:''}</div>` : '';
    return `<div class="card${cur?' dayun-card-current':''}" style="${cur?'border-left:3px solid var(--accent);':''}margin-bottom:8px"><div style="cursor:pointer;display:flex;align-items:center;flex-wrap:wrap;gap:6px" data-toggle-body="dyb-${di}"><div class="dayun-gz ${GAN_CSS[d.stem]||''}" style="flex-shrink:0">${esc(d.stem||'')}${esc(d.branch||'')}</div><span style="font-size:12px;color:var(--muted)">${d.start_year||'?'}年起 · ${d.start_age!=null?d.start_age:'-'}–${endAge}岁</span>${tgBadge}${fwBadge}${wrTag}${cur?`<span style="font-size:10px;font-weight:700;color:var(--accent)">▶ 当前</span>`:''}<span style="font-size:11px;color:var(--muted);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(wSnip)}</span><span class="dyb-arrow" style="color:var(--muted);flex-shrink:0">${cur?'▲':'▼'}</span></div><div id="dyb-${di}" style="margin-top:10px${cur?'':';display:none'}"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${dim16('💰','财运',d.wealth_hint)}${dim16('🩺','健康',d.health_hint)}${dim16('❤️','感情',d.love_hint)}${dim16('👶','子女',d.child_hint)}</div>${refsHtml}${narrativeHtml}<div style="margin-top:8px"><div style="font-size:11px;color:var(--muted);margin-bottom:4px">流年速览</div>${liunianGrid}</div></div></div>`;
  }).join('') || `<div style="color:var(--muted);text-align:center;padding:20px">暂无大运数据</div>`;

  el.innerHTML = singleModeNotice + `<div id="dayunChartContainer" style="margin-bottom:16px"></div>` + methodCard + cardsHtml;

  el.querySelectorAll('[data-toggle-body]').forEach(hdr => {
    hdr.addEventListener('click', () => {
      const id = hdr.dataset.toggleBody;
      const body = document.getElementById(id);
      const arrow = hdr.querySelector('.dyb-arrow');
      if (!body) return;
      const hidden = body.style.display === 'none';
      body.style.display = hidden ? '' : 'none';
      if (arrow) arrow.textContent = hidden ? '▲' : '▼';
    });
  });

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
          ${item.interpretation_text?`<div style="margin-top:6px;font-size:11px;line-height:1.55;color:var(--muted)">${(item.annual_score!=null&&(item.annual_score>=70||item.annual_score<=40))?renderPara(item.interpretation_text):`${esc(item.interpretation_text.slice(0,60))}${item.interpretation_text.length>60?`…<details style="display:inline"><summary style="font-size:10px;color:var(--accent);cursor:pointer;margin-left:4px">全文</summary><div style="font-size:11px;line-height:1.65;padding:6px 8px;margin-top:4px;background:var(--bg2,rgba(0,0,0,0.03));border-radius:6px;max-width:300px">${renderPara(item.interpretation_text)}</div></details>`:''}`}</div>`:''}
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

  // ── 统计摘要行 ──────────────────────────────
  const jiCount = mf.filter(m=>m.luck_level==='吉').length;
  const xiongCount = mf.filter(m=>m.luck_level==='凶').length;
  const pingCount = mf.length - jiCount - xiongCount;
  // 最佳月/最差月：优先利用 luck_level（吉=高分 2，平=1，凶=0）
  const _lv = m => m.luck_level==='吉'?2:m.luck_level==='凶'?0:1;
  const bestMonth = mf.reduce((a,b)=>_lv(b)>_lv(a)?b:a, mf[0]);
  const worstMonth = mf.reduce((a,b)=>_lv(b)<_lv(a)?b:a, mf[0]);
  const monthSummaryHtml = `
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px">
    <div style="padding:8px 12px;background:rgba(45,138,78,0.08);border-radius:8px;border-left:3px solid var(--ok);text-align:center">
      <div style="font-size:10px;font-weight:700;color:var(--ok)">吉月</div>
      <div style="font-size:22px;font-weight:800;color:var(--ok)">${jiCount}</div>
    </div>
    <div style="padding:8px 12px;background:rgba(192,57,43,0.08);border-radius:8px;border-left:3px solid var(--bad);text-align:center">
      <div style="font-size:10px;font-weight:700;color:var(--bad)">凶月</div>
      <div style="font-size:22px;font-weight:800;color:var(--bad)">${xiongCount}</div>
    </div>
    <div style="padding:8px 12px;background:var(--bg2,rgba(0,0,0,0.04));border-radius:8px;border-left:3px solid var(--muted);text-align:center">
      <div style="font-size:10px;font-weight:700;color:var(--muted)">平月</div>
      <div style="font-size:22px;font-weight:800;color:var(--muted)">${pingCount}</div>
    </div>
  </div>
  ${(bestMonth||worstMonth)?`<div style="display:flex;gap:8px;margin-bottom:10px;font-size:12px">
    ${bestMonth&&bestMonth.luck_level==='吉'?`<div style="flex:1;padding:5px 10px;background:rgba(45,138,78,0.06);border-radius:6px">🌟 最佳：<strong>${(MONTHS[bestMonth.month-1]||bestMonth.month)+'月'}</strong> ${esc(bestMonth.month_ganzhi||bestMonth.month_dizhi||'')}</div>`:''}
    ${worstMonth&&worstMonth.luck_level==='凶'?`<div style="flex:1;padding:5px 10px;background:rgba(192,57,43,0.06);border-radius:6px">⚠ 注意：<strong>${(MONTHS[worstMonth.month-1]||worstMonth.month)+'月'}</strong> ${esc(worstMonth.month_ganzhi||worstMonth.month_dizhi||'')}</div>`:''}
  </div>`:''}`;
  // 月运五行色调映射（兼容旧文字键和新十六进制格式）
  const _colorMap = {'白/金':'#e2e8f0','绿/青':'#86efac','黑/蓝':'#93c5fd','红/紫':'#fca5a5','黄/棕':'#fde68a'};
  el.innerHTML = monthSummaryHtml + `
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

/* ══════════════════════════════════════════════════
   Tab 20: 紫微斗数（命盘展示面板）
═══════════════════════════════════════════════════ */
function renderTab20(json, el) {
  // 紫微盘由 verify.html 内联脚本独立渲染到 #zwBoard
  // 本函数负责在 panel-content 内显示导航卡和说明
  const zwData = window._zwLastAlone || null;
  if (!zwData) {
    el.innerHTML = `
    <div class="card" style="text-align:center;padding:32px 16px">
      <div style="font-size:36px;margin-bottom:12px">☆</div>
      <div style="font-size:15px;font-weight:700;margin-bottom:8px">紫微斗数命盘</div>
      <div style="font-size:13px;color:var(--muted);line-height:1.7;max-width:320px;margin:0 auto">
        紫微命盘将在排盘完成后自动计算。<br>
        请先在「请求 (Tab1)」输入出生信息并提交，随后切回此面板查看。
      </div>
    </div>`;
    return;
  }
  // 紫微盘已由内联脚本渲染，显示摘要链接
  const mingGong = zwData.ming_gong || zwData.palaces?.find?.(p=>p.name==='命宫') || null;
  const juType   = zwData.ju_type || '';
  const mainStars= zwData.main_stars || [];
  el.innerHTML = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>紫微命盘摘要</p>
    <div class="kv" style="margin-top:8px">
      ${juType?`<div class="k">局数</div><div><strong>${esc(juType)}</strong></div>`:''}
      ${mingGong?`<div class="k">命宫</div><div><strong>${esc(mingGong.dizhi||mingGong.branch||'')}</strong>${mingGong.main_star?` · ${esc(mingGong.main_star)}`:''}</div>`:''}
      ${mainStars.length?`<div class="k">主星</div><div>${mainStars.map(s=>`<span class="chip" style="font-size:11px">${esc(typeof s==='string'?s:s.name||'')}</span>`).join(' ')}</div>`:''}
    </div>
  </div>
  <div class="card">
    <p class="card-title"><span class="dot"></span>命盘图</p>
    <div style="font-size:12px;color:var(--muted);margin-bottom:8px">完整紫微盘请向下滚动或查看「紫微」独立区域。</div>
    <div id="zwBoardMirror" style="overflow-x:auto"></div>
  </div>`;
  // 如果内联盘已渲染，复制一份到 zwBoardMirror
  const src = document.getElementById('zwBoard');
  const dst = el.querySelector('#zwBoardMirror');
  if (src && dst) { dst.innerHTML = src.innerHTML; }
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
