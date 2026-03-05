/**
 * verify-chart.js  v4.0.20260305M
 * M4.30 五行环形图 | M4.08 大运走势图 | M4 6D评分条
 * 纯 CSS/Canvas 实现，无第三方依赖
 */
;(function(){
'use strict';

/* ── 工具函数 ──────────────────────────────────── */
const esc = s => String(s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');

/* ── 颜色常量 ──────────────────────────────────── */
const WX_COLORS = { wood:'#4ade80', fire:'#f87171', earth:'#fbbf24', metal:'#94a3b8', water:'#60a5fa' };
const WX_NAMES  = { wood:'木', fire:'火', earth:'土', metal:'金', water:'水' };
const SCORE_COLORS = ['#b22222','#b8860b','#4a7c59','#2563eb','#7c3aed','#c2410c'];
const SCORE_LABELS = ['财运','事业','婚姻','健康','发展','整体'];

/* ══════════════════════════════════════════════════
   五行环形图  M4.30
   用 CSS conic-gradient 绘制甜甜圈
═══════════════════════════════════════════════════ */
window.renderWuxingRingChart = function(wx, container, json) {
  if (!container) return;
  const keys  = ['wood','fire','earth','metal','water'];
  const vals  = keys.map(k => Math.max(0, wx[k]||0));
  const total = vals.reduce((a,b)=>a+b, 0) || 1;

  // 构建 conic-gradient 分段
  let deg = 0;
  const segments = keys.map((k,i) => {
    const pct  = vals[i] / total * 100;
    const from = deg;
    deg += pct * 3.6;
    return { key: k, from, to: deg, pct };
  });
  const grad = segments.map(s => `${WX_COLORS[s.key]} ${s.from.toFixed(1)}deg ${s.to.toFixed(1)}deg`).join(',');

  // 图例
  const legend = keys.map((k,i) => `
    <div class="wuxing-legend-item">
      <span style="background:${WX_COLORS[k]}" class="wuxing-legend-dot"></span>
      <span>${WX_NAMES[k]}</span>
      <span style="font-weight:700">${(vals[i]/total*100).toFixed(0)}%</span>
    </div>`).join('');

  // N5.06: 五行均衡分、偏缺/偏旺
  const balanceScore = json?.wuxing_balance_score;
  const wxWeak   = json?.wuxing_weak   || [];
  const wxStrong = json?.wuxing_strong || [];
  // 清洗 "> 分隔符，避免后端富文本格式污染 HTML
  const _clean = s => String(s||'').split('">').map(p=>p.trim()).filter(Boolean).join(' · ');
  const balanceAdvice = _clean(json?.balance_advice || '');
  const yongshenList = json?.yongshen?.favor || [];

  // 五行建议映射 (N5.06)
  const WX_ADVICE = {
    water: '水：宜北方、黑蓝色系、金融/理财行业',
    wood:  '木：宜东方、绿色系、教育/文化行业',
    fire:  '火：宜南方、红色系、文娱/传媒行业',
    earth: '土：宜中央/中部、黄色系、房产/建筑行业',
    metal: '金：宜西方、白色系、法律/金融/机械行业',
  };
  const adviceLines = yongshenList.map(f => WX_ADVICE[f]).filter(Boolean);

  const balanceHtml = balanceScore != null ? `<div style="margin-top:8px;font-size:12px;color:var(--muted)">均衡分 <strong style="color:${balanceScore>=70?'var(--ok)':balanceScore>=50?'var(--warn)':'var(--bad)'}">${balanceScore.toFixed(1)}</strong></div>` : '';
  const _wxcn = w => (typeof wxCN === 'function' ? wxCN(w) : w);
  const weakHtml  = wxWeak.length  ? `<div style="margin-top:4px;font-size:11px;color:var(--bad)">偏缺：${wxWeak.map(_wxcn).join('、')}</div>` : '';
  const strongHtml= wxStrong.length? `<div style="font-size:11px;color:var(--warn)">偏旺：${wxStrong.map(_wxcn).join('、')}</div>` : '';
  const balAdviceHtml = balanceAdvice ? `<div style="margin-top:6px;font-size:11px;color:var(--text);line-height:1.6;border-top:1px dashed var(--line);padding-top:6px">▸ ${esc(balanceAdvice)}</div>` : '';
  const adviceHtml= adviceLines.length ? `<div style="margin-top:8px;font-size:11px;line-height:1.7;border-top:1px solid var(--line);padding-top:6px">${adviceLines.map(a=>`<div>▸ ${a}</div>`).join('')}</div>` : '';

  container.innerHTML = `
  <div class="wuxing-ring">
    <div class="wuxing-ring-outer" style="background: conic-gradient(${grad})">
      <div class="wuxing-ring-inner">
        <div style="font-size:10px;color:var(--muted)">五行</div>
        <div style="font-size:11px;font-weight:700;color:var(--text)">${WX_NAMES[keys[vals.indexOf(Math.max(...vals))]]}</div>
        <div style="font-size:9px;color:var(--muted)">最旺</div>
      </div>
    </div>
    <div class="wuxing-legend">${legend}</div>
  </div>
  ${balanceHtml}${weakHtml}${strongHtml}${balAdviceHtml}${adviceHtml}`;
};

/* ══════════════════════════════════════════════════
   大运走势图  M4.08  (多因子 Canvas 折线)
   若无真实分数则退化为颜色条
═══════════════════════════════════════════════════ */
window.renderDayunTrendChart = function(items, container) {
  if (!container || !items?.length) return;

  // 检查是否有真实 overall_score
  const hasRealScores = items.some(d => d.overall_score !== undefined);

  if (!hasRealScores) {
    // 退化条形图
    container.innerHTML = `
    <div style="overflow-x:auto">
      <div style="display:flex;gap:4px;align-items:flex-end;min-width:400px;height:60px;padding:4px 0">
        ${items.map(d=>{
          const greenish = '甲乙木'.includes(d.stem||'') ? 80 : 50;
          return `<div title="${d.stem||''}${d.branch||''} ${d.start_year||''}年" style="flex:1;min-width:24px;background:linear-gradient(180deg,var(--ok),var(--accent-gold));border-radius:4px 4px 0 0;height:${greenish}%"></div>`;
        }).join('')}
      </div>
      <div style="display:flex;gap:4px;font-size:10px;color:var(--muted);min-width:400px">
        ${items.map(d=>`<div style="flex:1;min-width:24px;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d.stem||''}${d.branch||''}</div>`).join('')}
      </div>
    </div>`;
    return;
  }

  // Canvas 多因子折线图
  const canvas = document.createElement('canvas');
  const W = container.clientWidth || 560;
  const H = 140;
  canvas.width  = W;
  canvas.height = H;
  canvas.style.cssText = 'width:100%;height:auto;display:block;border-radius:8px;background:var(--input)';
  container.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const PAD = { top:16, right:20, bottom:32, left:36 };
  const cw  = W - PAD.left - PAD.right;
  const ch  = H - PAD.top  - PAD.bottom;

  const factors = ['overall_score','wealth_score','health_score','love_score'];
  const fColors = ['#b22222','#b8860b','#22c55e','#ec4899'];
  const fLabels = ['综合','财','健','情'];

  const maxV = 100, minV = 0;
  const xScale = i => PAD.left + (i / (items.length-1||1)) * cw;
  const yScale = v => PAD.top + ch - ((v-minV)/(maxV-minV)) * ch;

  // 背景网格
  ctx.strokeStyle = '#e5e7eb';
  ctx.lineWidth = 0.5;
  [25,50,75].forEach(y=>{
    ctx.beginPath();
    ctx.moveTo(PAD.left, yScale(y));
    ctx.lineTo(PAD.left+cw, yScale(y));
    ctx.stroke();
    ctx.fillStyle='#9ca3af';
    ctx.font='9px sans-serif';
    ctx.fillText(y, 4, yScale(y)+3);
  });

  // X 轴标签
  ctx.font = '9px sans-serif';
  ctx.fillStyle = '#9ca3af';
  items.forEach((d,i) => {
    if (items.length <= 10 || i%Math.ceil(items.length/8)===0) {
      ctx.fillText((d.stem||'')+(d.branch||''), xScale(i)-8, H-8);
    }
  });

  // 折线
  factors.forEach((factor, fi) => {
    const pts = items.map((d,i) => [xScale(i), yScale(d[factor]??50)]);
    ctx.beginPath();
    ctx.strokeStyle = fColors[fi];
    ctx.lineWidth = fi===0 ? 2.5 : 1.5;
    ctx.globalAlpha = fi===0 ? 1 : 0.7;
    pts.forEach(([x,y],i) => i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y));
    ctx.stroke();
    ctx.globalAlpha = 1;

    // 当前大运标记
    const thisYear = new Date().getFullYear();
    const curIdx = items.findIndex(d=>d.start_year<=thisYear&&(d.start_year||0)+10>thisYear);
    if (curIdx>=0) {
      const [cx,cy] = pts[curIdx];
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, Math.PI*2);
      ctx.fillStyle = fColors[fi];
      ctx.fill();
    }
  });

  // 图例
  const legendDiv = document.createElement('div');
  legendDiv.style.cssText = 'display:flex;gap:12px;font-size:11px;margin-top:4px;flex-wrap:wrap';
  legendDiv.innerHTML = factors.map((f,i)=>`<span style="display:flex;align-items:center;gap:4px"><span style="width:20px;height:3px;background:${fColors[i]};display:inline-block;border-radius:2px"></span>${fLabels[i]}</span>`).join('');
  container.appendChild(legendDiv);
};

/* ══════════════════════════════════════════════════
   6D 评分条  (M4 scoring bars, Tab 5)
═══════════════════════════════════════════════════ */
window.renderScoringBars = function(json, container) {
  if (!container) return;
  const sc = json.score_v2 || json.scoring_detail || {};
  // 当前大运评分（取大运列表中当前大运的财运/得分）
  const _thisYear = new Date().getFullYear();
  const _curDayun = (json.dayun?.items||[]).find(d => d.start_year<=_thisYear && (d.start_year||0)+10>_thisYear);
  const _dayunScore = _curDayun?.score ?? _curDayun?.wealth_score ?? sc.dayun ?? null;

  const scores6D = [
    ['wealth',   '财运评分', json.wealth_analysis?.wealth_score    ?? sc.wealth   ?? null],
    ['career',   '事业评分', json.career?.career_score             ?? sc.career   ?? null],
    ['marriage', '婚姻评分', json.marriage_analysis?.marriage_score?? sc.marriage ?? null],
    ['health',   '健康评分', json.health?.health_score             ?? sc.health   ?? null],
    ['dayun',    '当前大运', _dayunScore],
    ['overall',  '综合评分', json.overall_score ?? sc.overall ?? null],
  ].filter(([,,val]) => val !== null && val > 0);  // 隐藏无数据的维度

  const barHtml = scores6D.map(([k,label,val],i) => {
    const v = Math.min(100, Math.max(0, val));
    const cl = v>=75?'ok':v>=50?'warn':'bad';
    return `
    <div class="score-bar-row" style="display:flex;align-items:center;gap:8px;margin:5px 0">
      <div style="width:60px;font-size:12px;color:var(--muted)">${label}</div>
      <div style="flex:1;height:10px;background:#f1f5f9;border-radius:5px;overflow:hidden">
        <div style="width:${v}%;height:100%;background:${SCORE_COLORS[i]};border-radius:5px;transition:width .6s"></div>
      </div>
      <div style="width:36px;font-size:12px;font-weight:700;text-align:right;color:var(--${cl})">${v.toFixed(0)}</div>
    </div>`;
  }).join('');

  container.innerHTML = `
  <div class="card" style="margin-bottom:12px">
    <p class="card-title"><span class="dot"></span>六维评分</p>
    ${barHtml}
  </div>`;
};

/* ══════════════════════════════════════════════════
   公共: 枚举翻译（供 verify-render.js 使用）
   挂到 window 上
═══════════════════════════════════════════════════ */
const TEN_GOD_CN = {
  zheng_guan:'正官', pian_guan:'偏官(七杀)', qi_sha:'七杀',
  zheng_yin:'正印',  pian_yin:'偏印(枭神)',
  bi_jian:'比肩',   jie_cai:'劫财',
  shang_guan:'伤官', shi_shen:'食神',
  zheng_cai:'正财',  pian_cai:'偏财',
  ri_zhu:'日主',
  zheng_guan_he:'正官合', bi_jian_he:'比肩合', jie_cai_he:'劫财合',
};
const TEN_GOD_TYPE = {
  zheng_guan:'auth', pian_guan:'kill', qi_sha:'kill',
  zheng_yin:'seal',  pian_yin:'seal',
  bi_jian:'peer',    jie_cai:'peer',
  shang_guan:'output', shi_shen:'output',
  zheng_cai:'wealth',  pian_cai:'wealth',
  ri_zhu:'self',
};

window.tenGodCN = code => TEN_GOD_CN[code] || code || '—';
window.tenGodType = code => TEN_GOD_TYPE[code] || 'other';
window.wxCN = wx => ({ wood:'木',fire:'火',earth:'土',metal:'金',water:'水' }[wx] || wx || '—');

window.GAN_WUXING = {
  '甲':'wood','乙':'wood','丙':'fire','丁':'fire','戊':'earth',
  '己':'earth','庚':'metal','辛':'metal','壬':'water','癸':'water',
};
window.GAN_CSS = {
  '甲':'wx-wood','乙':'wx-wood','丙':'wx-fire','丁':'wx-fire','戊':'wx-earth',
  '己':'wx-earth','庚':'wx-metal','辛':'wx-metal','壬':'wx-water','癸':'wx-water',
};
window.GAN_DESC = {
  '甲':'甲木，阳木，栋梁之材，性正直','乙':'乙木，阴木，花草之灵',
  '丙':'丙火，阳火，太阳之象','丁':'丁火，阴火，烛灯之光',
  '戊':'戊土，阳土，厚重城墙','己':'己土，阴土，沃土田园',
  '庚':'庚金，阳金，铸剑之器','辛':'辛金，阴金，珠宝饰品',
  '壬':'壬水，阳水，江海奔腾','癸':'癸水，阴水，雨露甘霖',
};

window.translateRationale = tier => ({
  extremely_strong:'极强', strong:'强', balanced:'中和', neutral:'中和',
  weak:'弱', extremely_weak:'极弱',
}[tier]||tier||'—');

window.translateFactorName = name => ({
  gan_root:'天干根',         zhi_root:'地支自根',       same_opp_gang:'刑冲克合',
  month_stem:'月令天干',     month_branch:'月令地支',   dayun_stem:'大运天干',
  dayun_branch:'大运地支',   seasonal_bonus:'季节加成', transparency:'透干',
  same_element_support:'同类加成', parent_element_support:'生我加成',
}[name]||name||'—');

/* ── 地支五行 CSS 映射 & 藏干（供 Tab2 命盘使用） ── */
window.ZHI_CSS = {
  '子':'wx-water','丑':'wx-earth','寅':'wx-wood','卯':'wx-wood',
  '辰':'wx-earth','巳':'wx-fire','午':'wx-fire','未':'wx-earth',
  '申':'wx-metal','酉':'wx-metal','戌':'wx-earth','亥':'wx-water',
};
/* 藏干 – 子平通行版（本气/中气/余气次序） */
window.ZHI_HIDDEN = {
  '子':['癸'],         '丑':['己','癸','辛'],  '寅':['甲','丙','戊'], '卯':['乙'],
  '辰':['戊','乙','癸'],'巳':['丙','庚','戊'], '午':['丁','己'],      '未':['己','乙','丁'],
  '申':['庚','壬','戊'],'酉':['辛'],            '戌':['戊','辛','丁'], '亥':['壬','甲'],
};
/* 十神提示文字（鼠标悬停 title） */
window.tenGodDesc = code => ({
  zheng_guan:'【正官】克我（异性），代表规则、职权、贵人，身强逢官则贵',
  pian_guan: '【偏官·七杀】克我（同性），霸道冲劲，逢印化煞则贵，无制则凶',
  qi_sha:    '【七杀】偏官别名，主攻克竞争，逢制化可化杀为权',
  zheng_yin: '【正印】生我（异性），庇护、学业、文书，印制煞护主为吉',
  pian_yin:  '【偏印·枭神】生我（同性），偏才艺、异路功名，过多则孤僻',
  bi_jian:   '【比肩】同我（同性），代表兄弟、竞争，旺命多比则分财，弱命得比则有助',
  jie_cai:   '【劫财】同我（异性），夺财之星，主竞争、破财',
  shang_guan:'【伤官】我生（异性），才华、口才、创新，克正官，宜有印制衡',
  shi_shen:  '【食神】我生（同性），衣食、才艺、福禄，食神制煞则贵',
  zheng_cai: '【正财】我克（异性），正当收入、妻财（男命），日主有力方能驭财',
  pian_cai:  '【偏财】我克（同性），横财、父（男命）、流动资金',
  ri_zhu:    '【日主】命局核心，代表命主本人，一切分析以此为基准',
}[code]||'');

window.copyText = function(text, btn) {
  navigator.clipboard?.writeText(text).then(()=>{
    if(btn){ const old=btn.textContent; btn.textContent='✓ 已复制'; setTimeout(()=>btn.textContent=old,1500); }
  });
};

/* ── 六十甲子纳音五行（命理大师专业查询） ── */
window.NAYIN = {
  '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火','戊辰':'大林木','己巳':'大林木',
  '庚午':'路旁土','辛未':'路旁土','壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
  '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土','庚辰':'白蜡金','辛巳':'白蜡金',
  '壬午':'杨柳木','癸未':'杨柳木','甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
  '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木','壬辰':'长流水','癸巳':'长流水',
  '甲午':'沙中金','乙未':'沙中金','丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
  '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金','甲辰':'覆灯火','乙巳':'覆灯火',
  '丙午':'天河水','丁未':'天河水','戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
  '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水','丙辰':'沙中土','丁巳':'沙中土',
  '戊午':'天上火','己未':'天上火','庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
};

})();
