/**
 * verify-export.js  v4.0.20260301
 * M5.01 JSON导出 | M5.02 CSV导出 | M5.03 Excel导出(6张表) | M4.13 打印
 */
;(function(){
'use strict';

const $ = id => document.getElementById(id);

/* ── 获取当前命盘结果 ─────────────────────────── */
function getResult() {
  return window.__BAZI_STATE?.result;
}
function getPayload() {
  return window.__BAZI_STATE?.payload || {};
}
function getFileName(ext) {
  const p = getPayload();
  const dt = (p.dt||new Date().toISOString()).slice(0,10).replace(/-/g,'');
  const sex = p.sex==='M'?'男':'女';
  return `bazi_${dt}_${sex}.${ext}`;
}

/* ══════════════════════════════════════════════════
   导出分发  M5.01-03
═══════════════════════════════════════════════════ */
window.exportResult = function(format) {
  const json = getResult();
  if (!json) { showToast('请先排盘','warn'); return; }
  switch(format||'json') {
    case 'json':  return exportJSON(json);
    case 'csv':   return exportCSV(json);
    case 'excel': return exportExcel(json);
    case 'print': return exportPDF();
    default: exportJSON(json);
  }
};

/* ══════════════════════════════════════════════════
   JSON 导出  M5.01
═══════════════════════════════════════════════════ */
function exportJSON(json) {
  const blob = new Blob([JSON.stringify(json, null, 2)], { type:'application/json;charset=utf-8' });
  downloadBlob(blob, getFileName('json'));
}
window.exportJSON = exportJSON;

/* ══════════════════════════════════════════════════
   CSV 导出  M5.02 (单表，字段名与 VerifyResponseModel 一致)
   格式: 两列 [field_path, value]，UTF-8 BOM
   spec §5.03: 所有字段名与 API 响应 schema 零不匹配
═══════════════════════════════════════════════════ */
function exportCSV(json) {
  const rows = [];
  // 行以 [api_field_path, value] 格式 → 与 VerifyResponseModel 字段名零不匹配
  const add  = (field, value) => rows.push([field, value]);

  // 顶层字段
  add('request_id',                json.request_id||'');
  add('api_version',               json.api_version||'');
  add('rule_version',              json.rule_version||'');
  add('mode_effective',            json.mode_effective||'');
  add('dt_input',                  json.dt_input||'');
  add('solar_time_offset_minutes', json.solar_time_offset_minutes??'');

  // 四柱
  const p = json.pillars_primary||{};
  ['year','month','day','hour'].forEach(k => {
    add(`pillars_primary.${k}.stem`,    p[k]?.stem||'');
    add(`pillars_primary.${k}.branch`,  p[k]?.branch||'');
    add(`pillars_primary.${k}.ganzhi`,  p[k]?.ganzhi||'');
  });

  // 十神
  const tg = json.ten_gods||{};
  ['year','month','day','hour'].forEach(k => add(`ten_gods.${k}`, k==='day'?'ri_zhu':(tg[k]||'')));

  // 五行
  const wx = json.wuxing_score||{};
  ['wood','fire','earth','metal','water'].forEach(k => add(`wuxing_score.${k}`, (wx[k]||0).toFixed(2)));

  // 日主
  add('day_master_strength.tier',  json.day_master_strength?.tier||'');
  add('day_master_strength.score', (json.day_master_strength?.score||0).toFixed(2));

  // 格局
  const g = json.geju||{};
  add('geju.geju_name',            g.geju_name||'');
  add('geju.geju_level',           g.geju_level||'');
  add('geju.month_stem_shishen',   g.month_stem_shishen||'');
  add('geju.classic_ref',          g.classic_ref||'');

  // 用神
  add('yongshen.favor',            (json.yongshen?.favor||[]).join('/'));
  add('yongshen.avoid',            (json.yongshen?.avoid||[]).join('/'));

  // 校验
  add('validation.level',          json.validation?.level||'');
  add('validation.mode_effective', json.validation?.mode_effective||'');

  // 财运
  const wa = json.wealth_analysis||{};
  add('wealth_analysis.wealth_score',  wa.wealth_score??'');
  add('wealth_analysis.wealth_tier',   wa.wealth_tier||'');
  add('wealth_analysis.annual_range',  wa.annual_range||'');
  add('wealth_analysis.industries',    (wa.industries||[]).join('/'));

  // 事业
  const ca = json.career||{};
  add('career.career_score',        ca.career_score??'');
  add('career.career_directions',   (ca.career_directions||[]).join('/'));
  add('career.leadership_potential',ca.leadership_potential?'true':'false');
  add('career.optimal_move_timing', ca.optimal_move_timing||'');

  // 婚姻
  const ma = json.marriage_analysis||{};
  add('marriage_analysis.marriage_score',      ma.marriage_score??'');
  add('marriage_analysis.peach_blossom',       ma.peach_blossom||'');
  add('marriage_analysis.partner_wuxing',      ma.partner_wuxing||'');
  add('marriage_analysis.optimal_marriage_age',ma.optimal_marriage_age||'');

  // 健康
  const ha = json.health||{};
  add('health.health_score',   ha.health_score??'');
  add('health.risk_organs',    (ha.risk_organs||[]).join('/'));
  add('health.risk_level',     ha.risk_level||'');

  // 人际
  const ra = json.relationship||{};
  add('relationship.relationship_score', ra.relationship_score??'');
  add('relationship.social_strategy',    ra.social_strategy||'');

  // 性格
  const pe = json.personality||{};
  add('personality.day_stem',      pe.day_stem||'');
  add('personality.day_stem_trait',pe.day_stem_trait||'');
  add('personality.advantages',    (pe.advantages||[]).join('；'));
  add('personality.disadvantages', (pe.disadvantages||[]).join('；'));

  // 人生弧线
  const la = json.life_arc||{};
  add('life_arc.overall_tier',  la.overall_tier||'');
  add('life_arc.early_fortune', la.early_fortune||'');
  add('life_arc.mid_fortune',   la.mid_fortune||'');
  add('life_arc.late_fortune',  la.late_fortune||'');
  add('life_arc.peak_periods',  (la.peak_periods||[]).join('；'));

  // 大运概要
  const dy = json.dayun||{};
  add('dayun.method',         dy.method||'');
  add('dayun.start_age',      dy.start_age??'');
  add('dayun.items_count',    (dy.items||[]).length);

  // 神煞数量
  add('shensha_count',        (json.shensha||[]).length);

  // header 行
  rows.unshift(['field_path', 'value']);

  const csvContent = '\uFEFF' + rows.map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(',')).join('\r\n');
  const blob = new Blob([csvContent], { type:'text/csv;charset=utf-8' });
  downloadBlob(blob, getFileName('csv'));
}
window.exportCSV = exportCSV;

/* ══════════════════════════════════════════════════
   Excel 导出  M5.03  (6 工作表，无第三方库)
   格式: TSV 文件 + 扩展名 .xls (Excel 能直接打开)
   若要真正的 xlsx 请按需引入 SheetJS
═══════════════════════════════════════════════════ */
function exportExcel(json) {
  // 尝试使用 SheetJS（如已全局加载）
  if (typeof XLSX !== 'undefined') {
    exportWithSheetJS(json); return;
  }
  // 回退：HTML Table → .xls
  exportHTMLtoXLS(json);
}
window.exportExcel = exportExcel;

function exportWithSheetJS(json) {
  const wb = XLSX.utils.book_new();

  // 表1: 四柱基础
  const p  = json.pillars_primary||{};
  const tg = json.ten_gods||{};
  const CN = {year:'年',month:'月',day:'日',hour:'时'};
  const pillarsData = [
    ['柱','天干','地支','干支','十神','日主'],
    ...['year','month','day','hour'].map(k=>[CN[k], p[k]?.stem||'', p[k]?.branch||'', p[k]?.ganzhi||'', tg[k]||'', k==='day'?'日主':'']),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(pillarsData), '四柱');

  // 表2: 五行
  const wx = json.wuxing_score||{};
  const wxTotal = ['wood','fire','earth','metal','water'].reduce((s,k)=>s+(wx[k]||0),0)||1;
  const WX_CN = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};
  const wxData = [
    ['五行','得分','占比'],
    ...['wood','fire','earth','metal','water'].map(k=>[WX_CN[k], (wx[k]||0).toFixed(2), (wx[k]/wxTotal*100).toFixed(1)+'%']),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(wxData), '五行');

  // 表3: 大运  (Sheet3 per spec §5.02)
  const dayunItems = json.dayun?.items||[];
  const dayunData = [
    ['干支','起年','起岁','十神','财运提示','健康提示','感情提示','古籍'],
    ...dayunItems.map(d=>[
      (d.stem||'')+(d.branch||''), d.start_year||'',
      d.start_age!==undefined?d.start_age+'岁':'', d.ten_god||'',
      d.wealth_hint||'', d.health_hint||'', d.love_hint||'',
      (d.refs||[]).map(r=>r.source||r.text||'').join('；'),
    ]),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(dayunData), '大运');

  // 表4: 分析维度汇总  (Sheet4 per spec §5.02)
  const g = json.geju||{};
  const str = json.day_master_strength||{};
  const wa = json.wealth_analysis||{};
  const ca = json.career||{};
  const ma = json.marriage_analysis||{};
  const ha = json.health||{};
  const ra = json.relationship||{};
  const pe = json.personality||{};
  const la = json.life_arc||{};
  const analysisData = [
    ['维度','字段','值'],
    ['格局','格局名称', g.geju_name||''],
    ['格局','格局等级', g.geju_level||''],
    ['格局','月干十神', g.month_stem_shishen||''],
    ['格局','古籍引用', g.classic_ref||''],
    ['日主','强弱层级', str.tier||''],
    ['日主','强弱分数', (str.score||0).toFixed(2)],
    ['校验','级别', json.validation?.level||''],
    ['财运','分数', wa.wealth_score!==undefined?(wa.wealth_score+''):'-'],
    ['财运','层级', wa.wealth_tier||''],
    ['财运','年收入区间', wa.annual_range||''],
    ['财运','推荐行业', (wa.industries||[]).join('/')],
    ['事业','分数', ca.career_score!==undefined?(ca.career_score+''):'-'],
    ['事业','职业方向', (ca.career_directions||[]).join('/')],
    ['事业','领导潜力', ca.leadership_potential?'是':'否'],
    ['事业','最佳换工时机', ca.optimal_move_timing||''],
    ['婚姻','分数', ma.marriage_score!==undefined?(ma.marriage_score+''):'-'],
    ['婚姻','桃花旺衰', ma.peach_blossom||''],
    ['婚姻','配偶五行特质', ma.partner_wuxing||''],
    ['婚姻','最佳婚龄', ma.optimal_marriage_age||''],
    ['健康','分数', ha.health_score!==undefined?(ha.health_score+''):'-'],
    ['健康','风险脏腑', (ha.risk_organs||[]).join('/')],
    ['健康','风险等级', ha.risk_level||''],
    ['人际','分数', ra.relationship_score!==undefined?(ra.relationship_score+''):'-'],
    ['人际','社交策略', ra.social_strategy||''],
    ['性格','日干', pe.day_stem||''],
    ['性格','特质', pe.day_stem_trait||''],
    ['性格','优势', (pe.advantages||[]).join('；')],
    ['性格','劣势', (pe.disadvantages||[]).join('；')],
    ['总览','人生格局', la.overall_tier||''],
    ['总览','幼年运势', la.early_fortune||''],
    ['总览','中年运势', la.mid_fortune||''],
    ['总览','晚年运势', la.late_fortune||''],
    ['总览','旺运区间', (la.peak_periods||[]).join('；')],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(analysisData), '分析维度汇总');

  // 表5: 神煞  (Sheet5 per spec §5.02)
  const shenshaData = [
    ['名称','所在地支','所在柱','吉/凶','★多关系','含义','古籍来源'],
    ...(json.shensha||[]).map(s=>[
      s.name||'', s.dizhi||'', s.pillar||'',
      s.is_beneficial?'吉':'凶', s.is_star?'★':'',
      s.meaning||'', s.classic_source||'',
    ]),
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(shenshaData), '神煞');

  // 表6: 原始JSON  (Sheet6 per spec §5.02)
  const rawData = [
    ['字段路径','值'],
    ['request_id', json.request_id||''],
    ['api_version', json.api_version||''],
    ['rule_version', json.rule_version||''],
    ['mode_effective', json.mode_effective||''],
    ['dt_input', json.dt_input||''],
    ['solar_time_offset_minutes', json.solar_time_offset_minutes!==undefined?json.solar_time_offset_minutes:''],
    ['raw_json', JSON.stringify(json)],
  ];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rawData), '原始JSON');

  XLSX.writeFile(wb, getFileName('xlsx'));
}

function exportHTMLtoXLS(json) {
  const p   = json.pillars_primary||{};
  const tg  = json.ten_gods||{};
  const wx  = json.wuxing_score||{};
  const g   = json.geju||{};
  const str = json.day_master_strength||{};
  const dy  = json.dayun?.items||[];
  const wa  = json.wealth_analysis||{};
  const ca  = json.career||{};
  const ma  = json.marriage_analysis||{};
  const ha  = json.health||{};
  const la  = json.life_arc||{};
  const CN  = {year:'年',month:'月',day:'日',hour:'时'};
  const WX_CN = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};

  const esc  = s => String(s||'').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const table = str => `<table border="1">${str}</table>`;
  const row   = cells => `<tr>${cells.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`;
  const hrow  = cells => `<tr>${cells.map(c=>`<th>${esc(c)}</th>`).join('')}</tr>`;

  let html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="utf-8"/></head><body>`;

  // Sheet1: 四柱
  html += `<h3>Sheet1: 四柱</h3>${table(hrow(['柱','天干','地支','干支','十神','日主'])+['year','month','day','hour'].map(k=>row([CN[k],p[k]?.stem||'',p[k]?.branch||'',p[k]?.ganzhi||'',tg[k]||'',k==='day'?'日主':''])).join(''))}`;

  // Sheet2: 五行
  const wxTotal = ['wood','fire','earth','metal','water'].reduce((s,k)=>s+(wx[k]||0),0)||1;
  html += `<h3>Sheet2: 五行</h3>${table(hrow(['五行','得分','占比'])+['wood','fire','earth','metal','water'].map(k=>row([WX_CN[k],(wx[k]||0).toFixed(2),(wx[k]/wxTotal*100).toFixed(1)+'%'])).join(''))}`;

  // Sheet3: 大运
  html += `<h3>Sheet3: 大运</h3>${table(hrow(['干支','起年','起岁','十神','财运提示','健康提示','感情提示'])+dy.map(d=>row([(d.stem||'')+(d.branch||''),d.start_year||'',d.start_age!==undefined?d.start_age+'岁':'',d.ten_god||'',d.wealth_hint||'',d.health_hint||'',d.love_hint||''])).join(''))}`;

  // Sheet4: 分析维度汇总
  const dimRows = [
    ['格局','格局名称',g.geju_name||''],['格局','格局等级',g.geju_level||''],
    ['格局','月干十神',g.month_stem_shishen||''],['格局','古籍引用',g.classic_ref||''],
    ['日主','强弱层级',str.tier||''],['日主','强弱分数',(str.score||0).toFixed(2)],
    ['校验','级别',json.validation?.level||''],
    ['财运','分数',wa.wealth_score!==undefined?wa.wealth_score:'-'],['财运','层级',wa.wealth_tier||''],
    ['财运','年收入区间',wa.annual_range||''],['财运','推荐行业',(wa.industries||[]).join('/')],
    ['事业','分数',ca.career_score!==undefined?ca.career_score:'-'],
    ['事业','职业方向',(ca.career_directions||[]).join('/')],
    ['婚姻','分数',ma.marriage_score!==undefined?ma.marriage_score:'-'],
    ['婚姻','桃花旺衰',ma.peach_blossom||''],['婚姻','最佳婚龄',ma.optimal_marriage_age||''],
    ['健康','分数',ha.health_score!==undefined?ha.health_score:'-'],
    ['健康','风险脏腑',(ha.risk_organs||[]).join('/')],['健康','风险等级',ha.risk_level||''],
    ['总览','人生格局',la.overall_tier||''],['总览','旺运区间',(la.peak_periods||[]).join('；')],
  ];
  html += `<h3>Sheet4: 分析维度汇总</h3>${table(hrow(['维度','字段','值'])+dimRows.map(row).join(''))}`;

  // Sheet5: 神煞
  html += `<h3>Sheet5: 神煞</h3>${table(hrow(['名称','地支','柱','吉凶','★','含义','古籍'])+
    (json.shensha||[]).map(s=>row([s.name||'',s.dizhi||'',s.pillar||'',s.is_beneficial?'吉':'凶',s.is_star?'★':'',s.meaning||'',s.classic_source||''])).join(''))}`;

  // Sheet6: 原始JSON
  html += `<h3>Sheet6: 原始JSON</h3>${table(hrow(['字段路径','值'])+
    [['request_id',json.request_id||''],['api_version',json.api_version||''],
     ['rule_version',json.rule_version||''],['mode_effective',json.mode_effective||''],
     ['dt_input',json.dt_input||''],['solar_time_offset_minutes',json.solar_time_offset_minutes||0],
     ['raw_json',JSON.stringify(json).slice(0,32767)]].map(row).join(''))}`;

  html += `</body></html>`;
  const blob = new Blob(['\uFEFF'+html], { type:'application/vnd.ms-excel;charset=utf-8' });
  downloadBlob(blob, getFileName('xls'));
}

/* ══════════════════════════════════════════════════
   打印 / PDF  M4.13
═══════════════════════════════════════════════════ */
window.exportPDF = function() {
  // 隐藏非打印区域在 print CSS 中已处理
  window.print();
};

/* ══════════════════════════════════════════════════
   通用下载
═══════════════════════════════════════════════════ */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href    = url;
  a.download= filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(()=>{ document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
}

/* ══════════════════════════════════════════════════
   导出菜单 打开/关闭
═══════════════════════════════════════════════════ */
window.toggleExportMenu = function() {
  const menu = document.getElementById('exportDropdown');
  if (!menu) return;
  menu.classList.toggle('open');
};

// 点击外部关闭
document.addEventListener('click', e => {
  if (!e.target.closest('#exportMenuWrapper')) {
    document.getElementById('exportDropdown')?.classList.remove('open');
  }
});

/* ══════════════════════════════════════════════════
   N5.02 分享卡片 – html2canvas PNG 导出
   依赖: verify.html 中通过 CDN 加载 html2canvas
═══════════════════════════════════════════════════ */
window.exportShareCard = function() {
  const json = window.ST?.result;
  if (!json) { alert('请先完成排盘再生成分享卡片。'); return; }

  // 1. 构建或更新 #share-card div
  let card = document.getElementById('share-card');
  if (!card) {
    card = document.createElement('div');
    card.id = 'share-card';
    document.body.appendChild(card);
  }

  const thisYear = new Date().getFullYear();
  const liunianNow = (json.liunian_detail||[]).find(l=>l.year===thisYear);
  const annualScore = liunianNow?.annual_score != null ? liunianNow.annual_score + '分' : '—';
  const dayStem     = json.pillars_primary?.day?.stem || '—';
  const gejuName    = json.geju?.geju_name || json.geju?.name || '—';
  const gejuLevel   = json.geju?.geju_level || '';
  const yongshen    = (json.yongshen?.favor||[]).join(' / ') || '—';
  const dtInput     = json.dt_input ? json.dt_input.slice(0,16).replace('T',' ') : '—';
  const requestId   = json.request_id || '';

  card.innerHTML = `
  <div class="share-card-inner">
    <div class="share-card-header">
      <div class="share-card-title">八字命理分析结果</div>
      <div class="share-card-sub">${dtInput}</div>
    </div>
    <div class="share-card-body">
      <div class="share-item"><span class="share-label">日主</span><span class="share-value">${dayStem}</span></div>
      <div class="share-item"><span class="share-label">格局</span><span class="share-value">${gejuName}${gejuLevel?' · '+gejuLevel:''}</span></div>
      <div class="share-item"><span class="share-label">用神</span><span class="share-value">${yongshen}</span></div>
      <div class="share-item"><span class="share-label">本年运势（${thisYear}）</span><span class="share-value share-score">${annualScore}</span></div>
    </div>
    <div class="share-card-footer">
      <div class="share-watermark">本结果仅供娱乐参考，不构成任何建议</div>
      <div class="share-rid" style="font-size:9px;opacity:0.5;margin-top:4px">ID: ${requestId.slice(0,12)}</div>
    </div>
  </div>`;

  // Card styling (injected once)
  if (!document.getElementById('share-card-style')) {
    const style = document.createElement('style');
    style.id = 'share-card-style';
    style.textContent = `
    #share-card {
      position: fixed; left: -9999px; top: 0;
      width: 360px; background: #1a1128; color: #f5f0ff;
      font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
      border-radius: 16px; overflow: hidden; padding: 0;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    #share-card .share-card-inner { padding: 24px 20px 16px; }
    #share-card .share-card-header { margin-bottom: 16px; text-align: center; }
    #share-card .share-card-title { font-size: 18px; font-weight: 700; color: #d4af37; }
    #share-card .share-card-sub { font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 4px; }
    #share-card .share-card-body { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
    #share-card .share-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(255,255,255,0.07); border-radius: 8px; }
    #share-card .share-label { font-size: 12px; color: rgba(255,255,255,0.6); }
    #share-card .share-value { font-size: 14px; font-weight: 600; }
    #share-card .share-score { color: #4ade80; font-size: 18px; font-weight: 800; }
    #share-card .share-card-footer { text-align: center; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); }
    #share-card .share-watermark { font-size: 10px; color: rgba(255,255,255,0.35); letter-spacing: 0.04em; position: relative; }
    `;
    document.head.appendChild(style);
  }

  // 2. 使用 html2canvas 截图并下载
  if (typeof html2canvas !== 'function') {
    alert('分享卡片功能需要网络连接加载 html2canvas 库，请检查网络后重试。');
    return;
  }

  card.style.left = '-9999px';
  card.style.display = 'block';

  html2canvas(card, {
    backgroundColor: '#1a1128',
    scale: 2,
    useCORS: true,
    logging: false,
  }).then(canvas => {
    card.style.left = '-9999px';
    canvas.toBlob(blob => {
      if (!blob) { alert('生成图片失败，请重试。'); return; }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bazi-share-${Date.now()}.png`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 500);
    }, 'image/png');
  }).catch(err => {
    console.error('html2canvas error:', err);
    alert('生成分享卡片失败，请稍后重试。');
  });
};

})();
