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
  if (!json) { alert('请先排盘'); return; }
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
   CSV 导出  M5.02 (单表，关键字段)
═══════════════════════════════════════════════════ */
function exportCSV(json) {
  const rows = [];
  const add  = (label, value) => rows.push([label, value]);

  add('请求ID',  json.request_id||'');
  add('API版本', json.api_version||'');
  add('规则版本', json.rule_version||'');
  add('模式',    json.mode_effective||'');
  add('输入时间', json.dt_input||'');

  const p = json.pillars_primary||{};
  const CN = {year:'年',month:'月',day:'日',hour:'时'};
  ['year','month','day','hour'].forEach(k => {
    add(`${CN[k]}柱天干`, p[k]?.stem||'');
    add(`${CN[k]}柱地支`, p[k]?.branch||'');
    add(`${CN[k]}柱干支`, p[k]?.ganzhi||'');
  });

  const tg = json.ten_gods||{};
  ['year','month','day','hour'].forEach(k => add(`${CN[k]}柱十神`, k==='day'?'日主':(tg[k]||'')));

  const wx = json.wuxing_score||{};
  const WX_CN = {wood:'木',fire:'火',earth:'土',metal:'金',water:'水'};
  ['wood','fire','earth','metal','water'].forEach(k=>{
    add(`五行_${WX_CN[k]}`, (wx[k]||0).toFixed(2));
  });

  add('日主强弱',   json.day_master_strength?.tier||'');
  add('日主强弱分', (json.day_master_strength?.score||0).toFixed(2));

  const g = json.geju||{};
  add('格局名称',   g.geju_name||'');    // geju_name field per schema
  add('格局评级',   g.geju_level||'');   // geju_level field per schema
  add('月干十神',   g.month_stem_shishen||'');

  add('校验级别',   json.validation?.level||'');

  add('财运分',     (json.wealth_analysis?.wealth_score??''));
  add('财运层级',   json.wealth_analysis?.wealth_tier||'');
  add('推荐行业',   (json.wealth_analysis?.industries||[]).join('/'));
  add('事业分',     (json.career?.career_score??''));
  add('职业方向',   (json.career?.career_directions||[]).join('/'));
  add('婚姻分',     (json.marriage_analysis?.marriage_score??''));
  add('桃花旺衰',   json.marriage_analysis?.peach_blossom||'');
  add('健康分',     (json.health?.health_score??''));
  add('健康风险',   json.health?.risk_level||'');
  add('人际分',     (json.relationship?.relationship_score??''));
  add('人生格局',   json.life_arc?.overall_tier||'');

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

})();
