/* ── P3.4 增量渲染：宫格签名缓存 & HTML 构建函数 ──────────── */
/** bid → 上次渲染时宫格的内容签名字符串 */
const _palSigs = new Map();

/**
 * 计算宫格内容签名（轻量字符串，仅含影响渲染的关键字段）
 * 额外包含 bodyB / lnLifeB 以响应流年命宫、身宫位置变化
 */
function _palSig(p, bodyB, lnLifeB) {
  const stars = p.main_stars.map(s => s.name + (s.brightness||'') + (s.transforms||[]).join('')).join('|');
  const aux   = (p.aux_stars||[]).join('|');
  const ages  = (p.xiaoxian_ages||[]).join('·');
  const isB   = (p.branch === bodyB) ? '1' : '0';
  const isLN  = (bi(p.branch) === lnLifeB) ? '1' : '0';
  return `${p.name}|${p.stem}${p.branch}|${stars}|${aux}|${ages}|${isB}|${isLN}`;
}

/** 构建单个宫格的 innerHTML 字符串 */
function _buildPalHTML(p, bodyB, lnLifeB, bid) {
  const hasJi=p.main_stars.some(s=>s.transforms&&s.transforms.includes('化忌'));
  const isL=(p.name==='命宫'),isB=(p.branch===bodyB),isLN=(lnLifeB>=0&&bid===lnLifeB);
  let h=`<div class="pname">${p.name}`;
  if(isL)h+=` <span class="blife">命</span>`;
  if(isB)h+=` <span class="bbody">身</span>`;
  if(isLN)h+=` <span class="bln">年</span>`;
  h+=`</div><div class="db">${p.stem}${p.branch}</div><div class="stars">`;
  for(const s of p.main_stars){
    const sia=s.transforms&&s.transforms.length?s.transforms.map(t=>`<span class="shan">${t}</span>`).join(''):'';
    const _bv=(typeof s.brightness_val==='number'&&MS.has(s.name))?s.brightness_val:0;
    const _bs=_bv>0?`<span style="font-size:.5rem;color:#c9963a;letter-spacing:-1px;vertical-align:middle;margin-right:1px" title="${s.brightness}">${'★'.repeat(_bv)}</span>`:'';
    h+=`<div class="sl">${_bs}<span class="sn ${sc(s.name)}" onclick="showStarInfo('${s.name}',event)">${s.name}</span><span class="sbr">${s.brightness}</span>${sia}</div>`;
  }
  for(const ax of p.aux_stars){
    h+=`<div class="sl"><span class="sn ${sc(ax)}" onclick="showStarInfo('${ax}',event)" style="font-size:.7rem">${ax}</span></div>`;
  }
  h+=`</div>`;
  if(p.xiaoxian_ages&&p.xiaoxian_ages.length)h+=`<div class="xage">${p.xiaoxian_ages.join('·')}岁</div>`;
  h+=`<div class="compass">${CP[bid]||''}</div>`;
  const savedNote=getPalNote(p.name);
  h+=`<button class="pal-note-btn${savedNote?' has-note':''}" onclick="openNoteModal('${p.name}',event)" title="编辑宫位笔记">📝</button>`;
  h+=`<div class="pal-note-txt${savedNote?' vis':''}" id="pnt-${bid}">${esc(savedNote||'')}</div>`;
  const _ps=palScore(p);const _pc=_ps>=75?'#16a34a':_ps>=55?'#b8862a':'#dc2626';
  h+=`<div class="pal-score-bar"><div class="pal-score-fill" style="width:${_ps}%;background:${_pc}" title="宫力评分：${_ps}"></div></div>`;
  return h;
}

async function go(){
  const body={
    year:+document.getElementById('fy').value,
    month:+document.getElementById('fm').value,
    day:+document.getElementById('fd').value,
    hour:+document.getElementById('fh').value,
    minute:+document.getElementById('fmin').value,
    gender:document.getElementById('fgender').value
  };
  const ln=document.getElementById('fln').value; if(ln)body.liunian_year=+ln;
  const lo=document.getElementById('flo').value; if(lo)body.longitude=+lo;
  body.template_version=currentTpl;
  stLoad('排盘计算中…');
  // 骨架屏：命盘宫格区域
  const pg = document.getElementById('pg');
  if (pg && !pg.querySelector('.pgrid-skel')) {
    const skels = Array.from({length: 4}, () =>
      '<div class="skel-box" style="height:var(--ph,136px);border-radius:4px"></div>'
    ).join('');
    pg.insertAdjacentHTML('beforebegin', `<div class="pgrid-skel" style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:8px">${skels}</div>`);
  }
  try{
    const r=await fetch('/api/v1/ziwei/full',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    if(!r.ok){const e=await r.json();throw new Error(e.detail||r.statusText)}
    const data=await r.json();
    _lastData=data;render(data);stClear();
    // 移除骨架屏
    document.querySelectorAll('.pgrid-skel').forEach(el => el.remove());
    /* 排盘成功后重置保存状态 */
    window._lastCaseId = null;
    const _saveBtn = document.getElementById('save-chart-btn');
    if (_saveBtn) { _saveBtn.textContent = '💾 保存'; _saveBtn.style.color = ''; }
    /* 更新 URL 参数 */
    const _ps=new URLSearchParams({y:body.year,m:body.month,d:body.day,h:body.hour,min:body.minute,g:body.gender});
    if(body.longitude!=null)_ps.set('lo',body.longitude);
    if(body.liunian_year!=null)_ps.set('ln',body.liunian_year);
    history.replaceState(null,'','?'+_ps.toString());
    document.getElementById('tbar').classList.add('vis');
    document.getElementById('tpl-grp').style.display='flex';
    saveHistory(body,data);
  }catch(e){st('错误: '+e.message,true)}
}

/* ── 演示盘 ──────────────────────────────────────────────── */
async function demo(){
  stLoad('加载演示盘…');
  try{
    const r=await fetch('/api/v1/ziwei/demo');
    if(!r.ok)throw new Error('演示请求失败');
    const d=await r.json();
    document.getElementById('fy').value=2002;
    document.getElementById('fm').value=3;
    document.getElementById('fd').value=13;
    document.getElementById('fh').value=14;
    document.getElementById('fmin').value=55;
    document.getElementById('fgender').value='女';
    _lastData=d;render(d);stClear();
    document.getElementById('tbar').classList.add('vis');
    document.getElementById('tpl-grp').style.display='flex';
    saveHistory({year:2002,month:3,day:13,hour:14,minute:55,gender:'女'},d);
  }catch(e){st('演示错误: '+e.message,true)}
}

/* ── 渲染命盘 ────────────────────────────────────────────── */
function render(data){
  const{lunar,life_palace_gz,body_palace_gz,wuxing_ju_name,dayun,liunian,gender}=data;
  const life_ruler_star=data.life_ruler_star||'';
  const body_ruler_star=data.body_ruler_star||'';
  const true_solar_time=data.true_solar_time||'';
  const jc=JC[wuxing_ju_name]||'';
  const curY=liunian?liunian.year:new Date().getFullYear();
  let curD=null;
  if(dayun&&dayun.items)for(const d of dayun.items)if(curY>=d.start_year&&curY<d.start_year+10){curD=d;break}

  /* 信息头栏 */
  let ihh=`
    <div class="kv"><span class="k">公历</span><span class="v">${data.birth_solar.replace('T',' ')}</span></div>
    <div class="kv"><span class="k">性别</span><span class="v">${gender}</span></div>
    <div class="kv"><span class="k">农历</span><span class="v">${lunar.year_gz}年${lunar.is_leap_month?'<span class="blife" style="font-size:.52rem;padding:1px 3px;margin:0 2px">闰</span>':''}${lunar.lunar_month}月${lunar.lunar_day}日${lunar.hour_branch}时</span></div>
    <div class="kv"><span class="k">命宫</span><span class="v">${life_palace_gz}</span></div>
    <div class="kv"><span class="k">身宫</span><span class="v">${body_palace_gz}</span></div>
    <div class="kv"><span class="k">五行局</span><span class="wbadge ${jc}">${wuxing_ju_name}</span></div>`;
  if(life_ruler_star)ihh+=`<div class="kv"><span class="k">命主</span><span class="v">${life_ruler_star}</span></div>`;
  if(body_ruler_star)ihh+=`<div class="kv"><span class="k">身主</span><span class="v">${body_ruler_star}</span></div>`;
  if(curD)ihh+=`<div class="kv"><span class="k">当前大运</span><span class="v">${curD.ganzhi}（${curD.start_age}岁）</span></div>`;
  if(true_solar_time)ihh+=`<div class="kv"><span class="k">真太阳时</span><span class="v">${true_solar_time}</span></div>`;
  document.getElementById('ih').innerHTML=ihh;

  /* 宫位格盘 — P3.4 增量渲染 */
  const g=document.getElementById('pg');
  const bodyB=body_palace_gz.slice(-1);
  const lnLifeB=liunian?liunian.life_palace_branch:-1;

  // 标记现存宫格节点，便于后续清除已失效节点
  const _seen=new Set();
  for(const p of data.palaces){
    const bid=bi(p.branch);const pos=BP[bid];if(!pos)continue;
    _seen.add(bid);
    const h=_buildPalHTML(p,bodyB,lnLifeB,bid);
    const sig=_palSig(p,bodyB,lnLifeB);
    let c=g.querySelector(`[data-bid="${bid}"]`);
    if(!c){
      // 首次：新建节点
      c=document.createElement('div');c.className='pal';
      c.setAttribute('data-bid',bid);
      c.setAttribute('data-pname',p.name);
      c.style.gridColumn=pos.c;c.style.gridRow=pos.r;
      c.innerHTML=h;
      if(p.tooltip)c.title=p.tooltip;
      g.appendChild(c);
      _palSigs.set(bid,sig);
    } else if(_palSigs.get(bid)!==sig){
      // 内容变化：增量更新
      c.className='pal';
      const hasJi=p.main_stars.some(s=>s.transforms&&s.transforms.includes('化忌'));
      if(hasJi)c.classList.add('pal-ji-warn');
      c.innerHTML=h;
      if(p.tooltip)c.title=p.tooltip;else c.removeAttribute('title');
      _palSigs.set(bid,sig);
    }
    // 始终刷新 class（命宫/身宫/年命可能跨次改变）
    const hasJi2=p.main_stars.some(s=>s.transforms&&s.transforms.includes('化忌'));
    c.classList.toggle('pal-ji-warn',hasJi2);
  }
  // 移除上次渲染但本次不存在的宫格
  g.querySelectorAll('[data-bid]').forEach(el=>{
    if(!_seen.has(+el.getAttribute('data-bid')))el.remove();
  });

  /* 中宫 — P3.4 增量更新 */
  let dyh='';
  if(dayun&&dayun.items){
    const dir=dayun.forward?'顺行':'逆行';
    dyh=`<div class="cs"><h3>大运（${dir} · 起运${dayun.start_age}岁）</h3><div class="dylist">`;
    for(const d of dayun.items)dyh+=`<div class="dyi${curD&&d.index===curD.index?' cur':''}" title="${d.start_year}年起">${d.ganzhi}<br><small>${d.start_age}岁</small></div>`;
    dyh+=`</div></div>`;
  }
  let lnh='';
  if(liunian){
    const sia=Object.entries(liunian.sihua||{}).map(([s,v])=>`<span class="${HUACSS[v]||''}">${s}${v}</span>`).join(' · ');
    lnh=`<div class="cs"><h3>流年 ${liunian.year_gz}（${liunian.year}年）</h3><div class="lnrow">${sia||'—'}</div></div>`;
  }
  let lyh='';
  if(data.liuyue&&data.liuyue.length){
    const today=new Date(),todayM=today.getMonth()+1,lnY=liunian?liunian.year:today.getFullYear();
    lyh=`<div class="cs"><h3>流月一览</h3><div class="lylist">`;
    for(const lm of data.liuyue){
      const isCM=(lnY===today.getFullYear()&&lm.month===todayM);
      lyh+=`<div class="lyi${isCM?' cur':''}" title="${lm.palace_name}·${lm.month_gz}">${lm.month_name}</div>`;
    }
    lyh+=`</div></div>`;
  }
  const rulerLine=life_ruler_star?`<br>命主：<b>${life_ruler_star}</b>　身主：<b>${body_ruler_star}</b>`:'';
  const ctrHTML=`<div class="ct">命盘中宫</div>
    <div class="cs"><h3>命盘信息</h3>
      <div style="font-size:.82rem;line-height:1.9">命宫：<b>${life_palace_gz}</b>　身宫：<b>${body_palace_gz}</b>　<span class="wbadge ${jc}">${wuxing_ju_name}</span>${rulerLine}</div>
    </div>${dyh}${lnh}${lyh}`;
  let ctr=g.querySelector('.pcenter');
  if(!ctr){
    ctr=document.createElement('div');ctr.className='pcenter';
    ctr.style.gridColumn='2/4';ctr.style.gridRow='2/4';
    g.appendChild(ctr);
  }
  ctr.innerHTML=ctrHTML;
  // §20 格局宫位自动标注
  if(data.patterns&&data.patterns.length) annotatePatternPalaces(data.patterns);
  document.getElementById('cr').classList.remove('hid');
  renderAna(data);
  injectGlossTooltips(); // §4 术语 Tooltip
}

/* ── 渲染解读区 ──────────────────────────────────────────── */

function buildScoreChart(fc){
  if(!fc||!fc.monthly||!fc.monthly.length)return'';
  const scores=fc.monthly.map(m=>m.score);
  const labels=fc.monthly.map(m=>m.period||'');
  const curPeriod=fc.current_month?fc.current_month.period:null;
  const n=scores.length;
  const W=520,H=110,pl=28,pr=12,pt=12,pb=28;
  const iW=W-pl-pr,iH=H-pt-pb;
  const sx=i=>pl+i/(n-1)*iW;
  const sy=v=>pt+iH-(v/100)*iH;
  const avgScore=Math.round(scores.reduce((a,b)=>a+b,0)/n);
  let svg='';
  /* 背景网格 */
  [25,50,75].forEach(g=>{
    const gy=sy(g).toFixed(1);
    svg+=`<line x1="${pl}" y1="${gy}" x2="${W-pr}" y2="${gy}" stroke="var(--border-lt)" stroke-width="1"/>`;
    svg+=`<text x="${pl-4}" y="${parseFloat(gy)+3.5}" text-anchor="end" font-size="7" fill="var(--muted)">${g}</text>`;
  });
  /* 年均线 */
  const avy=sy(avgScore).toFixed(1);
  svg+=`<line x1="${pl}" y1="${avy}" x2="${W-pr}" y2="${avy}" stroke="#b8862a" stroke-width="1" stroke-dasharray="4,3" opacity=".6"/>`;
  svg+=`<text x="${W-pr+2}" y="${parseFloat(avy)+3}" font-size="7" fill="#b8862a">${avgScore}</text>`;
  /* 折线渐变填充 */
  let pts=scores.map((v,i)=>`${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(' ');
  const fillPts=`${pl.toFixed(1)},${sy(0).toFixed(1)} ${pts} ${(W-pr).toFixed(1)},${sy(0).toFixed(1)}`;
  svg+=`<polygon points="${fillPts}" fill="#b8862a" opacity=".08"/>`;
  /* 折线 */
  let path=`M${sx(0).toFixed(1)},${sy(scores[0]).toFixed(1)}`;
  for(let i=1;i<n;i++)path+=` L${sx(i).toFixed(1)},${sy(scores[i]).toFixed(1)}`;
  svg+=`<path d="${path}" fill="none" stroke="#b8862a" stroke-width="1.8" stroke-linejoin="round"/>`;
  /* 数据点 + 月份标签 */
  for(let i=0;i<n;i++){
    const v=scores[i],x=sx(i).toFixed(1),y=sy(v).toFixed(1);
    const isCur=curPeriod&&labels[i]&&labels[i].startsWith(curPeriod.slice(0,3));
    const dotClr=v>=75?'#16a34a':v>=55?'#ca8a04':'#dc2626';
    svg+=`<circle cx="${x}" cy="${y}" r="${isCur?5:3}" fill="${dotClr}" stroke="var(--paper)" stroke-width="${isCur?2:1.2}"/>`;
    if(isCur)svg+=`<line x1="${x}" y1="${pt}" x2="${x}" y2="${H-pb}" stroke="#dc2626" stroke-width="1.2" stroke-dasharray="3,2" opacity=".7"/>`;
    /* 分数标签（仅峰谷和当月） */
    const isPeak=(i===0||i===n-1||(i>0&&i<n-1&&scores[i]>scores[i-1]&&scores[i]>scores[i+1])||(i>0&&i<n-1&&scores[i]<scores[i-1]&&scores[i]<scores[i+1]));
    if(isCur||isPeak)svg+=`<text x="${x}" y="${parseFloat(y)-7}" text-anchor="middle" font-size="7.5" font-weight="${isCur?700:400}" fill="${isCur?dotClr:'var(--muted)'}">${v}</text>`;
    /* X轴月份 */
    svg+=`<text x="${x}" y="${H-1}" text-anchor="middle" font-size="7" fill="var(--muted)">${i+1}月</text>`;
  }
  return `<div style="background:var(--bg);border-radius:8px;padding:8px 4px 4px;margin-bottom:14px"><svg viewBox="0 0 ${W} ${H}" style="width:100%;display:block;overflow:visible">${svg}</svg></div>`;
}

function renderForecastTab(fc){
  if(!fc)return`<p class="fc-empty">暂无运势数据，请先排盘</p>`;
  const curPeriod=fc.current_month?fc.current_month.period:null;
  let h=buildScoreChart(fc);
  if(fc.monthly&&fc.monthly.length){
    h+=`<div class="sec-title" style="margin-bottom:7px">月度运势概览<span style="font-size:.66rem;color:var(--muted);margin-left:8px">展开列表登录详细读取各月</span></div>`;
    h+=buildMonthScoreGrid(fc.monthly,curPeriod);
  }
  h+=`<div style="background:#fef9f0;border:1px solid #e8d8b0;border-left:3px solid #b8862a;border-radius:0 6px 6px 0;padding:7px 11px;font-size:.74rem;color:#78350f;line-height:1.65;margin-bottom:12px">`+
     `⚠️ 运势评分基于天干四化、流年宫位等启发式诊断，为参考性斯文小结，不是统计概率。请理性参考，不作为任何决策依据。</div>`;
  h+=`<div class="fc-divider">🗓 ${fc.year}年 年运总览</div>`;
  h+=fmtPeriod(fc.yearly,false);
  if(fc.current_month){
    h+=`<div class="fc-divider">📅 本月运势（${esc(fc.current_month.period)}）</div>`;
    h+=fmtPeriod(fc.current_month,true);
  }
  h+=`<div class="fc-divider">📆 全年十二流月</div><div class="fc-months">`;
  for(let i=0;i<fc.monthly.length;i++){
    const m=fc.monthly[i];
    const isCur=(curPeriod&&m.period===curPeriod);
    const topEvs=m.events&&m.events.length?m.events.slice(0,3).map(e=>`<span class="fc-tag fc-tag-sm lv-${esc(e.level)}">${esc(e.category)}</span>`).join(''):'';
    h+=`<div class="fc-month${isCur?' fc-cur':''}">`;
    h+=`<div class="fc-mhdr" onclick="togMonth(${i})">`;
    h+=`<span class="fc-arr" id="fc-arr-${i}">${isCur?'▼':'▶'}</span>`;
    h+=`<span class="mn">${esc(m.period)}（${esc(m.ganzhi)}）<span class="fc-palace-tag">${esc(m.palace_name)}</span></span>`;
    h+=`<span class="fc-tag-inline">${topEvs}</span>`;
    h+=`<div class="fc-bar"><div class="fc-bar-fill" style="width:${m.score}%"></div></div>`;
    h+=`<span class="ms">${m.score}分</span></div>`;
    h+=`<div class="fc-mbody${isCur?' open':''}" id="fc-mb-${i}">`;
    if(m.events&&m.events.length){
      h+=`<div class="fc-tags" style="margin-bottom:7px">`;
      for(const ev of m.events)h+=`<span class="fc-tag lv-${esc(ev.level)}" title="${esc(ev.description)}">${esc(ev.category)}【${esc(ev.level)}】</span>`;
      h+=`</div>`;
    }
    h+=`<div class="fc-grid">`;
    for(const[k,v]of Object.entries(m.details||{}))h+=`<div class="fc-dim"><b>${DIMS[k]||''} ${esc(k)}</b>${esc(v)}</div>`;
    h+=`</div><div class="fc-advice">${esc(m.advice)}</div>`;
    h+=`</div></div>`;
  }
  h+=`</div>`;
  return h;
}

/* ── 分享链接 ────────────────────────────────────────────────── */
/* ── JSON 导出 ────────────────────────────────────────────── */

/* ── Tab 快速跳转 (moved from export-cases.js) ─ */
function scrollToDayunCur(){
  const el=document.querySelector('#tc-dy svg .dayun-cur-marker, #tc-dy svg');
  if(!el){const tc=document.getElementById('tc-dy');if(tc)tc.scrollIntoView({behavior:'smooth',block:'start'});return;}
  const wrap=el.closest('div[style*="overflow-x"]')||el.closest('#tc-dy');
  if(!wrap)return;
  // 找 SVG 内当前大运的 x 位置（红色竖线）
  const line=document.querySelector('#tc-dy svg line[stroke="#ef4444"]');
  if(line&&wrap.scrollWidth>wrap.clientWidth){
    const svgEl=line.closest('svg');
    const vbW=parseFloat(svgEl.getAttribute('viewBox')?.split(' ')[2]||svgEl.getAttribute('width')||300);
    const x=parseFloat(line.getAttribute('x1')||0);
    const ratio=x/vbW;
    wrap.scrollLeft=ratio*wrap.scrollWidth-wrap.clientWidth/2;
  } else if(wrap.scrollIntoView){
    wrap.scrollIntoView({behavior:'smooth',block:'nearest'});
  }
}
function scrollToLiuyueCur(){
  const lmCur=document.querySelector('#tc-dy .lmg-cur');
  if(lmCur){lmCur.scrollIntoView({behavior:'smooth',block:'center'});}
  else{
    const tbl=document.querySelector('#tc-dy .ftable tr.tr-cur');
    if(tbl)tbl.scrollIntoView({behavior:'smooth',block:'center'});
  }
}

function shareLink(){
  const ps=new URLSearchParams({y:document.getElementById('fy').value,m:document.getElementById('fm').value,
    d:document.getElementById('fd').value,h:document.getElementById('fh').value,
    min:document.getElementById('fmin').value,g:document.getElementById('fgender').value});
  const lo=document.getElementById('flo').value,ln=document.getElementById('fln').value;
  if(lo)ps.set('lo',lo);if(ln)ps.set('ln',ln);
  const url=location.origin+location.pathname+'?'+ps.toString();
  const btn=document.getElementById('sbtn');
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(url).then(()=>{
      btn.textContent='✓ 链接已复制';btn.classList.add('copied');
      setTimeout(()=>{btn.textContent='🔗 复制分享链接';btn.classList.remove('copied');},2200);
    }).catch(()=>prompt('复制此链接：',url));
  }else{prompt('复制此链接：',url);}
}

/* ── URL 参数自动填表 ────────────────────────────────────────── */
