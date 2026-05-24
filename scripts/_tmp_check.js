
/* ── 常量 ─────────────────────────────────────────────────── */
const BP={5:{r:1,c:1},6:{r:1,c:2},7:{r:1,c:3},8:{r:1,c:4},
  4:{r:2,c:1},9:{r:2,c:4},3:{r:3,c:1},10:{r:3,c:4},
  2:{r:4,c:1},1:{r:4,c:2},0:{r:4,c:3},11:{r:4,c:4}};
const CP={5:'东南',6:'正南',7:'南偏西',8:'西南',4:'正东',9:'正西',3:'东偏北',10:'西偏北',2:'东北',1:'正北偏东',0:'正北',11:'西北'};
const MS=new Set(['紫微','天机','太阳','武曲','天同','廉贞','天府','太阴','贪狼','巨门','天相','天梁','七杀','破军']);
const SS=new Set(['擎羊','陀罗','火星','铃星','地空','地劫']);
const JS=new Set(['文昌','文曲','天魁','天钺','左辅','右弼']);
const JC={'水二局':'jw','木三局':'jwo','金四局':'jme','土五局':'jea','火六局':'jfi'};
const BRANCHES='子丑寅卯辰巳午未申酉戌亥';
const DIMS={感情:'💕',财运:'💰',事业:'💼',健康:'🏥'};
const HUACSS={化禄:'flu',化权:'fqu',化科:'fke',化忌:'fji'};

/* ── 工具函数 ─────────────────────────────────────────────── */
function bi(b){return BRANCHES.indexOf(b)}
function sc(n){return MS.has(n)?'main':SS.has(n)?'sha':JS.has(n)?'ji':'aux'}

/* ── 地支合冲关系 ──────────────────────────────────────────── */
const SAN_HE=[new Set([2,6,10]),new Set([3,7,11]),new Set([4,8,0]),new Set([5,9,1])]; // 寅午戌/卯未亥/辰申子/巳酉丑
const LIU_HE=[[0,1],[2,11],[3,10],[4,9],[5,8],[6,7]]; // 子丑/寅亥/卯戌/辰酉/巳申/午未
function branchRel(a,b){
  if(a==null||b==null||a<0||b<0)return '';
  if(a===b)return '<span class="br-same">同支</span>';
  if((a+6)%12===b||(b+6)%12===a)return '<span class="br-chong">冲</span>';
  for(const g of SAN_HE)if(g.has(a)&&g.has(b))return '<span class="br-sanhe">三合</span>';
  for(const p of LIU_HE)if((p[0]===a&&p[1]===b)||(p[0]===b&&p[1]===a))return '<span class="br-liuhe">六合</span>';
  return '';
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function scoreClass(s){return s>=75?'hi':s>=55?'md':'lo'}

/* ── 报告模板 ────────────────────────────────────────────────── */
let currentTpl='standard';
let _lastData=null;
function setTpl(tpl){
  currentTpl=tpl;
  document.querySelectorAll('.tpl-btn').forEach(b=>b.classList.toggle('act',b.dataset.tpl===tpl));
  if(_lastData)renderAna(_lastData);
}

/* ── 深色模式 ──────────────────────────────────────────────── */
function initTheme(){
  const saved=localStorage.getItem('zw_dark');
  const prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
  const useDark=saved!=null?saved==='1':prefersDark;
  if(useDark){document.documentElement.classList.add('dark');document.documentElement.classList.remove('light');}
  else{document.documentElement.classList.add('light');}
  const btn=document.getElementById('dark-toggle');
  if(btn)btn.textContent=useDark?'☀️':'🌙';
}
function toggleDark(){
  const isDark=document.documentElement.classList.toggle('dark');
  document.documentElement.classList.toggle('light',!isDark);
  localStorage.setItem('zw_dark',isDark?'1':'0');
  const btn=document.getElementById('dark-toggle');
  if(btn)btn.textContent=isDark?'☀️':'🌙';
}

/* 状态提示（含加载动画）*/
function st(msg,e=false){
  const txt=document.getElementById('st-txt');
  const el=document.getElementById('st');
  txt.textContent=msg;
  el.className='status'+(e?' err':'');
}
function stLoad(msg){
  const txt=document.getElementById('st-txt');
  document.getElementById('st').className='status loading';
  txt.textContent=msg;
}
function stClear(){st('');}

/* ── 城市选择器初始化 ────────────────────────────────────── */
async function initCities(){
  try{
    const r=await fetch('/api/v1/cities');
    if(!r.ok)return;
    const cities=await r.json();
    const sel=document.getElementById('fcity');
    cities.forEach(c=>{
      const opt=document.createElement('option');
      opt.value=c.lng;
      opt.textContent=c.name+' ('+c.province+')';
      sel.appendChild(opt);
    });
  }catch(e){
    // 静默失败，城市选择器非必须功能
  }
}

function onCityChange(){
  const sel=document.getElementById('fcity');
  const lng=sel.value;
  if(lng) document.getElementById('flo').value=parseFloat(lng).toFixed(2);
}

/* ── 排盘 ─────────────────────────────────────────────────── */
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
  stLoad('排盘计算中…');
  try{
    const r=await fetch('/api/v1/ziwei/full',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    if(!r.ok){const e=await r.json();throw new Error(e.detail||r.statusText)}
    const data=await r.json();
    _lastData=data;render(data);stClear();
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

  /* 宫位格盘 */
  const g=document.getElementById('pg');g.innerHTML='';
  const bodyB=body_palace_gz.slice(-1);
  const lnLifeB=liunian?liunian.life_palace_branch:-1;
  for(const p of data.palaces){
    const bid=bi(p.branch);const pos=BP[bid];if(!pos)continue;
    const c=document.createElement('div');c.className='pal';
    c.style.gridColumn=pos.c;c.style.gridRow=pos.r;
    const hasJi=p.main_stars.some(s=>s.transforms&&s.transforms.includes('化忌'));
    if(hasJi)c.classList.add('pal-ji-warn');
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
    /* 笔记区域 */
    const savedNote=getPalNote(p.name);
    h+=`<button class="pal-note-btn${savedNote?' has-note':''}" onclick="openNoteModal('${p.name}',event)" title="编辑宫位笔记">📝</button>`;
    h+=`<div class="pal-note-txt${savedNote?' vis':''}" id="pnt-${bid}">${esc(savedNote||'')}</div>`;
    c.innerHTML=h;
    if(p.tooltip)c.title=p.tooltip;
    g.appendChild(c);
  }

  /* 中宫 */
  const ctr=document.createElement('div');ctr.className='pcenter';
  ctr.style.gridColumn='2/4';ctr.style.gridRow='2/4';
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
  ctr.innerHTML=`<div class="ct">命盘中宫</div>
    <div class="cs"><h3>命盘信息</h3>
      <div style="font-size:.82rem;line-height:1.9">命宫：<b>${life_palace_gz}</b>　身宫：<b>${body_palace_gz}</b>　<span class="wbadge ${jc}">${wuxing_ju_name}</span>${rulerLine}</div>
    </div>${dyh}${lnh}${lyh}`;
  g.appendChild(ctr);
  document.getElementById('cr').classList.remove('hid');
  renderAna(data);
  injectGlossTooltips(); // §4 术语 Tooltip
}

/* ── 渲染解读区 ──────────────────────────────────────────── */
function renderAna(data){
  const aw=document.getElementById('aw');aw.classList.remove('hid');
  const isSimple=(currentTpl==='simple'),isPro=(currentTpl==='pro');
  const allTds=[{id:'sum',l:'命盘摘要'},{id:'pal',l:'逐宫解读'},{id:'dy',l:'大运流月'},{id:'fly',l:'飞星分析'},{id:'fc',l:'运势预测'}];
  const tds=isSimple?[{id:'sum',l:'命盘摘要'}]:allTds;
  document.getElementById('at').innerHTML=tds.map((t,i)=>
    `<button class="tbtn${i===0?' act':''}" data-tid="${t.id}" onclick="swt('${t.id}')">${t.l}</button>`).join('');

  /* ── Tab1：命盘摘要 ──────────────────────────────── */
  const PLVL={'大吉':'pat-daji','吉':'pat-ji','凶':'pat-xiong','大凶':'pat-daxiong'};
  let h=`<div id="tc-sum" class="tc act">`;
  /* 模板标注 */
  if(isSimple)h+=`<div style="font-size:.72rem;color:var(--muted);background:var(--bg);padding:4px 10px;border-radius:4px;margin-bottom:10px;text-align:center">📄 简版 · 仅显示核心摘要与格局</div>`;
  if(isPro)h+=`<div style="font-size:.72rem;color:#1e3a5f;background:#eff6ff;border-left:3px solid #3b82f6;border-radius:0 4px 4px 0;padding:4px 10px;margin-bottom:10px">🔬 专业版 · 完整数据展示，含详批注释与引用出处</div>`;
  h+=`<div class="sumcard">${esc(data.summary||'')}</div>`;
  /* 分析字段：简版不显示；专业版展开为手风琴 */
  if(!isSimple&&data.analysis&&Object.keys(data.analysis).length){
    if(isPro){
      h+=`<details class="pca-d" open style="margin-top:12px"><summary>命盘综合分析（展开/折叠）</summary>`;
      for(const[k,v]of Object.entries(data.analysis))if(v)h+=`<div class="pana" style="margin-top:6px"><h4>${esc(k)}</h4><p>${esc(v)}</p></div>`;
      h+=`</details>`;
    }else{
      h+=`<div style="margin-top:12px">`;
      for(const[k,v]of Object.entries(data.analysis))if(v)h+=`<div class="pana"><h4>${esc(k)}</h4><p>${esc(v)}</p></div>`;
      h+=`</div>`;
    }
  }
  /* 五行分布图 */
  if(data.palaces&&data.palaces.length){
    h+=`<div class="sec-title" style="margin-top:16px">五行分布·星曜统计</div>`;
    h+=`<div style="background:var(--bg);border-radius:8px;padding:10px 6px 6px;margin-top:8px">`;
    h+=buildWuxSVG(data.palaces);
    h+=`</div>`;
  }
  /* 格局检测展示 */
  if(data.patterns&&data.patterns.length){
    h+=`<div class="sec-title" style="margin-top:16px">格局检测·吉凶总览</div><div class="pat-list">`;
    for(const pt of data.patterns){
      const cls=PLVL[pt.level]||'pat-ji';
      const starsStr=pt.stars&&pt.stars.length?`<span class="pat-stars">${esc(pt.stars.join('·'))}</span>`:'';
      const palStr=pt.palaces&&pt.palaces.length?`<span class="pat-pals">${esc(pt.palaces.join('·'))}</span>`:'';
      h+=`<div class="pat-item ${cls}">`;
      h+=`<div class="pat-header"><span class="pat-badge">${esc(pt.level)}</span><span class="pat-name">${esc(pt.name)}</span>${starsStr}${palStr}</div>`;
      h+=`<div class="pat-desc">${esc(pt.description)}`;
      if(isPro && pt.source) h+=` <span style="font-size:.68rem;color:var(--muted);margin-left:6px">— 出处：${esc(pt.source)}</span>`;
      h+=`</div></div>`;
    }
    h+=`</div>`;
  }
  /* 破局建议区块 */
  if(data.remedies&&data.remedies.length){
    const prioLabel=['','紧要','关注','参考'];
    h+=`<div class="remedy-wrap">`;
    h+=`<div class="remedy-title">🔮 化劫建议<span style="font-size:.7rem;font-weight:400;color:var(--muted);margin-left:4px">（${data.remedies.length} 条 · 仅供参考，请理性评估）</span><button class="remedy-toggle" onclick="this.closest('.remedy-wrap').querySelector('.remedy-list').classList.toggle('hidden')">折叠 / 展开</button></div>`;
    h+=`<div class="remedy-list">`;
    for(const rd of data.remedies){
      const prioC=rd.priority===1?'':'p'+(rd.priority||3);
      h+=`<div class="remedy-item">`;
      h+=`<div class="remedy-header"><span class="remedy-prio ${prioC}">${prioLabel[rd.priority]||'参考'}</span><span class="remedy-name">${esc(rd.name)}</span><span class="remedy-meta">成本：${esc(rd.cost_level)} · ${esc(rd.valid_scope)}</span></div>`;
      if(rd.evidence) h+=`<div class="remedy-evidence">📌 触发依据：${esc(rd.evidence)}</div>`;
      if(rd.actions&&rd.actions.length){
        h+=`<ul class="remedy-actions">`;
        for(const act of rd.actions) h+=`<li>${esc(act)}</li>`;
        h+=`</ul>`;
      }
      h+=`<div class="remedy-disclaimer">⚠️ ${esc(rd.disclaimer)}</div>`;
      h+=`</div>`;
    }
    h+=`</div></div>`;
  }
  /* 生活化建议区块 */
  if(data.life_suggestions&&data.life_suggestions.length){
    const CAT_ICON={jewelry:'💍',plants:'🌿',objects:'🏮',bed:'🛏',timing:'📅'};
    const PRIO_LABEL=['','立即','次要','可选'];
    const PRIO_COLOR=['','#991b1b','#92400e','#1e40af'];
    // 按类别分组
    const catGroups={};
    for(const s of data.life_suggestions){
      if(!catGroups[s.category])catGroups[s.category]=[];
      catGroups[s.category].push(s);
    }
    h+=`<div class="lsug-wrap">`;
    h+=`<div class="lsug-title">🌟 生活化建议<span style="font-size:.7rem;font-weight:400;color:var(--muted);margin-left:4px">（${data.life_suggestions.length}条 · 传统命理参考，请理性评估）</span><button class="remedy-toggle" onclick="this.closest('.lsug-wrap').querySelector('.lsug-body').classList.toggle('hidden')">折叠 / 展开</button></div>`;
    // 类别 Tab 切换
    const catKeys=Object.keys(catGroups);
    h+=`<div class="lsug-cattabs" id="lsug-cattabs">`;
    catKeys.forEach((ck,ci)=>{
      const lbl=catGroups[ck][0].category_label;
      const icon=CAT_ICON[ck]||'📌';
      h+=`<button class="lsug-ctab${ci===0?' act':''}" onclick="switchLsugCat('${ck}')">${icon} ${lbl}</button>`;
    });
    h+=`</div>`;
    h+=`<div class="lsug-body">`;
    catKeys.forEach((ck,ci)=>{
      h+=`<div class="lsug-cat-panel${ci===0?' act':''}" data-cat="${ck}">`;
      for(const s of catGroups[ck]){
        const prioC=s.priority===1?'lsp-1':s.priority===2?'lsp-2':'lsp-3';
        const prioCol=PRIO_COLOR[s.priority]||'#374151';
        h+=`<div class="lsug-item">`;
        h+=`<div class="lsug-header"><span class="lsug-prio ${prioC}" style="border-color:${prioCol};color:${prioCol}">${PRIO_LABEL[s.priority]||'可选'}</span><span class="lsug-name">${esc(s.name)}</span><span class="lsug-meta">${esc(s.cost_level)} · ${esc(s.valid_scope)}</span></div>`;
        if(s.short_desc)h+=`<div class="lsug-desc">${esc(s.short_desc)}</div>`;
        if(s.evidence)h+=`<div class="lsug-evidence">📌 ${esc(s.evidence)}</div>`;
        if(s.actions&&s.actions.length){
          h+=`<details class="lsug-actions"><summary>实施步骤</summary><ul>`;
          for(const a of s.actions)h+=`<li>${esc(a)}</li>`;
          h+=`</ul></details>`;
        }
        if(s.notes)h+=`<div class="lsug-notes">📝 ${esc(s.notes)}</div>`;
        h+=`<div class="lsug-disclaimer">⚠️ ${esc(s.disclaimer)}</div>`;
        h+=`</div>`;
      }
      h+=`</div>`;
    });
    h+=`</div></div>`;
  }
  /* 十二宫综合评分排行 */
  if(data.palaces&&data.palaces.length){
    const sorted=[...data.palaces].map(p=>({n:p.name,s:palScore(p)})).sort((a,b)=>b.s-a.s);
    h+=`<div class="sec-title" style="margin-top:16px">十二宫·综合宫力排行<span style="font-size:.68rem;color:var(--muted);margin-left:8px">分值越高代表该宫星曜越旺、吉气越足</span></div>`;
    h+=`<div class="prank-wrap">`;
    sorted.forEach((pd,i)=>{
      const clr=pd.s>=75?'#16a34a':pd.s>=55?'#b8862a':'#dc2626';
      h+=`<div class="prank-row${i<3?' prank-top3':''}"><span class="prank-idx">${i+1}</span><span class="prank-name">${pd.n}</span><div class="prank-bar-bg"><div class="prank-fill" style="width:${pd.s}%;background:${clr}"></div></div><span class="prank-score" style="color:${clr}">${pd.s}</span></div>`;
    });
    h+=`</div>`;
  }
  h+=`</div>`;

  /* ── 简版只生成 Tab1，退出 ─────────────────────── */
  if(isSimple){document.getElementById('ab').innerHTML=h;return;}

  /* ── Tab2：逐宫解读 ──────────────────────────── */
  h+=`<div id="tc-pal" class="tc">`;
  if(isPro)h+=`<div class="pro-note" style="margin-bottom:10px">📌 专业版：含悬浮提示文字（Tooltip）完整展示，详批不折叠</div>`;
  /* 命盘五维雷达图 */
  if(data.palaces&&data.palaces.length){
    const radarSVG=buildRadarSVG(data.palaces);
    const palMap={};
    for(const p of data.palaces)palMap[p.name]=p;
    const scores=RADAR_DIMS.map(d=>{
      const ps=d.pals.map(n=>palScore(palMap[n])).filter(v=>v>0);
      return ps.length?Math.round(ps.reduce((a,b)=>a+b,0)/ps.length):50;
    });
    let legH='<div class="radar-legend">';
    RADAR_DIMS.forEach((d,i)=>{
      const s=scores[i],clr=s>=75?'#16a34a':s>=50?'#b8862a':'#dc2626';
      legH+=`<div class="rld"><span class="rld-dot" style="background:${clr}"></span><b>${d.icon}${d.label}</b>&ensp;${s}分`;
      legH+=`</div>`;
    });
    legH+='</div>';
    h+=`<div class="sec-title" style="margin-bottom:8px">命盘五维强度—雷达图<span style="font-size:.68rem;color:var(--muted);margin-left:8px">基于宫内主星、天干四化评估</span></div>`;
    h+=`<div class="radar-wrap">${radarSVG}${legH}</div>`;
  }
  for(const p of data.palaces){
    if(!p.conclusion&&!p.analysis)continue;
    h+=`<div class="pana"><h4>${p.name}·${p.stem}${p.branch}`;
    if(p.opposition_name)h+=` <span style="font-size:.72rem;color:var(--muted);font-weight:400">│ 对宫：${p.opposition_name}</span>`;
    h+=`</h4>`;
    /* 宫力速览：评分进度条 + 星曜徽章 */
    {const ps=palScore(p);const psC=ps>=75?'#16a34a':ps>=55?'#b8862a':'#dc2626';
    const psL=ps>=75?'强':ps>=55?'中':'弱';
    const psBg=ps>=75?'#dcfce7':ps>=55?'#fef9c3':'#fee2e2';
    const mN=(p.main_stars||[]).length,xN=(p.aux_stars||[]).length;
    h+=`<div class="psc-wrap"><div class="psc-bar-bg"><div class="psc-fill" style="width:${ps}%;background:${psC}"></div></div><span class="psc-score" style="color:${psC}">${ps}</span><span class="psc-lbl" style="background:${psBg};color:${psC}">${psL}</span></div>`;
    if(mN||xN){h+=`<div class="psc-badges">`;if(mN)h+=`<span class="psc-badge psc-main">主星×${mN}</span>`;if(xN)h+=`<span class="psc-badge psc-aux">辅星×${xN}</span>`;h+=`</div>`;}}
    if(p.analysis_tags&&p.analysis_tags.length){
      h+=`<div style="margin-bottom:5px">`;
      for(const t of p.analysis_tags)h+=`<span class="atag">${esc(t)}</span>`;
      h+=`</div>`;
    }
    if(p.conclusion){
      h+=`<div class="pca-c"><span class="lbl">结论</span>${esc(p.conclusion)}</div>`;
    }
    if(p.explanation){
      /* 专业版：详解不折叠；标准版默认展开 */
      if(isPro){
        h+=`<div class="pca-d"><div class="pca-exp">${esc(p.explanation)}</div>`;
        if(p.suggestion)h+=`<div class="pca-sug"><span class="lbl">💡 建议</span>${esc(p.suggestion)}</div>`;
        h+=`</div>`;
      }else{
        h+=`<details class="pca-d" open><summary>详细解释 ▸</summary>`;
        h+=`<div class="pca-exp">${esc(p.explanation)}</div>`;
        if(p.suggestion)h+=`<div class="pca-sug"><span class="lbl">💡 建议</span>${esc(p.suggestion)}</div>`;
        h+=`</details>`;
      }
    }else if(p.analysis){
      h+=`<p style="font-size:.83rem;line-height:1.7">${esc(p.analysis)}</p>`;
    }
    /* 专业版：显示 tooltip 注释 */
    if(isPro&&p.tooltip)h+=`<div class="pro-note">📎 命盘注释：${esc(p.tooltip)}</div>`;
    h+=`</div>`;
  }
  h+=`</div>`;

  /* Tab3：大运流月 */
  const curY2=data.liunian?data.liunian.year:new Date().getFullYear();
  const lifeBIdx=data.life_palace_branch_idx??-1;
  h+=`<div id="tc-dy" class="tc">`;
  /* 快速跳转按钮 */
  h+=`<div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap">`;
  h+=`<button class="btn-sm" onclick="scrollToDayunCur()" title="滚动到当前大运">⟳ 跳至当前大运</button>`;
  h+=`<button class="btn-sm" onclick="scrollToLiuyueCur()" title="滚动到当前流月">⟳ 跳至当前流月</button>`;
  h+=`</div>`;
  /* 大运时间轴 */
  if(data.dayun&&data.dayun.items)h+=buildDayunSVG(data.dayun,curY2);
  /* 专业版：当前大运速查卡片 */
  if(isPro){
    let curD2=null;
    if(data.dayun&&data.dayun.items)for(const d of data.dayun.items)if(curY2>=d.start_year&&curY2<d.start_year+10){curD2=d;break}
    if(curD2){
      const dyBIdx2=bi(curD2.ganzhi.slice(-1));
      const dyRelStr=branchRel(dyBIdx2,lifeBIdx)||'无特殊';
      const siaFull=Object.entries(curD2.sihua||{}).map(([s,v])=>`<span class="${HUACSS[v]||''}">${s}${v}</span>`).join(' ');
      h+=`<div class="pro-dayun-card"><h4>🔭 当前大运速查（${esc(curD2.ganzhi)} · ${curD2.start_age}–${curD2.end_age}岁）</h4>`;
      h+=`起运年 ${curD2.start_year} · 与命宫关系 ${dyRelStr}<br>`;
      h+=`大运四化：${siaFull||'—'}<br>`;
      if(curD2.boshi_stars&&Object.keys(curD2.boshi_stars).length)
        h+=`博士流曜：<span style="font-size:.75rem;color:var(--muted)">${Object.entries(curD2.boshi_stars).map(([sn,bz])=>`${sn}(${bz})`).join(' ')}</span>`;
      h+=`</div>`;
    }
  }
  // 流年命宫关系提示
  if(data.liunian){
    const lnBr=BRANCHES[data.liunian.life_palace_branch]||'';
    const lnRel=branchRel(data.liunian.life_palace_branch, lifeBIdx);
    h+=`<div style="font-size:.78rem;color:var(--muted);margin:0 0 8px;padding:5px 10px;background:var(--bg);border-radius:5px">流年（${esc(data.liunian.year_gz)}）· 流年命宫地支 <b>${lnBr}</b> 与命宫关系：${lnRel||'无（各自为政）'}</div>`;
  }
  h+=`<div class="fc-divider">大运列表</div>`;
  h+=`<table class="ftable"><tr><th>#</th><th>干支</th><th>年龄</th><th>起运年</th><th>大运四化</th><th>博士十二流曜</th><th>命宫关系</th></tr>`;
  if(data.dayun&&data.dayun.items)for(const d of data.dayun.items){
    const ic=curY2>=d.start_year&&curY2<d.start_year+10;
    const siaStr=Object.entries(d.sihua||{}).map(([s,v])=>`<span class="${HUACSS[v]||''}">${s}${v}</span>`).join(' ');
    const boshiStr=Object.entries(d.boshi_stars||{}).map(([sn,bz])=>`${sn}(${bz})`).join(' ');
    const dyBIdx=bi(d.ganzhi.slice(-1)); // 大运地支索引
    const dyRel=branchRel(dyBIdx, lifeBIdx);
    h+=`<tr${ic?' class="tr-cur"':''}><td>${d.index}</td><td><b>${d.ganzhi}</b></td><td>${d.start_age}–${d.end_age}岁</td><td>${d.start_year}</td><td style="font-size:.75rem">${siaStr||'—'}</td><td style="font-size:.7rem;color:var(--muted)">${boshiStr||'—'}</td><td style="text-align:center">${dyRel||'—'}</td></tr>`;
  }
  h+=`</table>`;
  if(data.liuyue&&data.liuyue.length){
    const today2=new Date(),todayM2=today2.getMonth()+1,lnY2=data.liunian?data.liunian.year:today2.getFullYear();
    h+=`<div class="sec-title" style="margin-top:14px">流月吉凶·热力方格（${lnY2}年）<span style="font-size:.66rem;color:var(--muted);margin-left:8px">吁年=吉　平偀=平　凶=危注意</span></div>`;
    h+=buildLiuyueGrid(data.liuyue,lnY2);
    h+=`<div class="fc-divider" style="margin-top:14px">流月一览（${lnY2}年）</div>`;
    h+=`<table class="ftable"><tr><th>月</th><th>月名</th><th>干支</th><th>流月命宫</th><th>四化</th><th>命宫关系</th></tr>`;
    for(const lm of data.liuyue){
      const isCM=(lnY2===today2.getFullYear()&&lm.month===todayM2);
      const msiaStr=Object.entries(lm.sihua||{}).map(([s,v])=>`<span class="${HUACSS[v]||''}">${s}${v}</span>`).join(' ');
      const lmRel=branchRel(lm.life_palace_branch, lifeBIdx);
      h+=`<tr${isCM?' class="tr-cur"':''}><td>${lm.month}</td><td>${lm.month_name}</td><td>${lm.month_gz}</td><td>${lm.palace_name}</td><td style="font-size:.75rem">${msiaStr||'—'}</td><td style="text-align:center">${lmRel||'—'}</td></tr>`;
    }
    h+=`</table>`;
  }
  h+=`</div>`;

  /* Tab4：飞星分析 */
  h+=`<div id="tc-fly" class="tc">`;
  if(data.flying&&data.flying.palaces){
    h+=buildFlyingHeatmap(data.flying);
    h+=`<div class="fc-divider">各宫飞出四化</div>`;
    h+=`<table class="ftable"><tr><th>宫位</th><th>宫干</th><th class="flu">化禄</th><th class="fqu">化权</th><th class="fke">化科</th><th class="fji">化忌</th><th>自化</th></tr>`;
    for(const fp of data.flying.palaces){
      const fo=fp.flying_out||{};
      const stArr=fp.self_transforms&&fp.self_transforms.length?fp.self_transforms.join(' · '):'—';
      h+=`<tr><td>${fp.palace_name}${fp.opposition_palace?`<br><span style="font-size:.7rem;color:var(--muted)">↔ ${fp.opposition_palace}</span>`:''}</td>`;
      h+=`<td>${fp.stem_name}</td><td class="flu">${fo['化禄']||'—'}</td><td class="fqu">${fo['化权']||'—'}</td><td class="fke">${fo['化科']||'—'}</td><td class="fji">${fo['化忌']||'—'}</td>`;
      h+=`<td style="font-size:.72rem;color:var(--muted)">${stArr}</td></tr>`;
    }
    h+=`</table>`;
    if(data.flying.received&&Object.keys(data.flying.received).length){
      h+=`<div class="fc-divider" style="margin-top:14px">各宫接收四化汇总</div>`;
      h+=`<table class="ftable"><tr><th>宫位</th><th>接收的四化</th></tr>`;
      for(const[pal,list]of Object.entries(data.flying.received)){
        if(!list||!list.length)continue;
        h+=`<tr><td>${pal}</td><td style="font-size:.75rem;line-height:1.8">${list.map(esc).join('　')}</td></tr>`;
      }
      h+=`</table>`;
    }
    if(data.flying.self_transforms&&data.flying.self_transforms.length){
      h+=`<div class="fc-divider" style="margin-top:14px">全局自化列表</div>`;
      h+=`<div style="font-size:.82rem;line-height:2;padding:6px 0">${data.flying.self_transforms.map(esc).join('　')}</div>`;
    }
    if(data.flying.chonged&&Object.keys(data.flying.chonged).length){
      h+=`<div class="fc-divider" style="margin-top:14px">被对冲汇总</div>`;
      h+=`<table class="ftable"><tr><th>宫位</th><th>被冲的四化来源</th></tr>`;
      for(const[pal,list]of Object.entries(data.flying.chonged)){
        if(!list||!list.length)continue;
        h+=`<tr><td>${pal}</td><td style="font-size:.75rem;line-height:1.8">${list.map(esc).join('　')}</td></tr>`;
      }
      h+=`</table>`;
    }
  }else{h+=`<p class="fc-empty">暂无飞星数据</p>`;}
  h+=`</div>`;

  /* Tab5：运势预测 */
  h+=`<div id="tc-fc" class="tc">${renderForecastTab(data.forecast)}</div>`;

  document.getElementById('ab').innerHTML=h;
}

/* ── Tab 切换 ────────────────────────────────────────────── */
function swt(id){
  document.querySelectorAll('.tbtn').forEach(b=>b.classList.toggle('act',b.dataset.tid===id));
  ['sum','pal','dy','fly','fc'].forEach(t=>{const el=document.getElementById('tc-'+t);if(el)el.classList.toggle('act',t===id)});
}

/* ── 流月折叠 ────────────────────────────────────────────── */
function togMonth(i){
  const el=document.getElementById('fc-mb-'+i),arr=document.getElementById('fc-arr-'+i);
  if(el){el.classList.toggle('open');if(arr)arr.textContent=el.classList.contains('open')?'▼':'▶';}
}

/* ── 运势卡片渲染 ────────────────────────────────────────── */
function fmtPeriod(pf,isCur){
  let h=`<div class="fc-section${isCur?' fc-cur':''}">`;
  h+=`<h3>${esc(pf.period)}（${esc(pf.ganzhi)}）<span class="fc-palace-tag">${esc(pf.palace_name)}</span> <span class="fc-score ${scoreClass(pf.score)}">${pf.score}分</span></h3>`;
  h+=`<div class="fc-overall">${esc(pf.overall)}</div>`;
  if(pf.events&&pf.events.length){
    h+=`<div class="fc-tags">`;
    for(const ev of pf.events)h+=`<span class="fc-tag lv-${esc(ev.level)}" title="${esc(ev.description)}（${esc(ev.source)}）">${esc(ev.category)}【${esc(ev.level)}】</span>`;
    h+=`</div>`;
  }
  h+=`<div class="fc-grid">`;
  for(const[k,v]of Object.entries(pf.details||{}))h+=`<div class="fc-dim"><b>${DIMS[k]||''} ${esc(k)}</b>${esc(v)}</div>`;
  h+=`</div>`;
  h+=`<div class="fc-advice">${esc(pf.advice)}</div>`;
  h+=`</div>`;
  return h;
}

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
function exportJSON(){
  if(!_lastData){alert('请先排盘后再导出。');return;}
  const payload={
    exported_at: new Date().toISOString(),
    engine_version: _lastData.engine_version||'2.1.0',
    input_snapshot: {
      year: document.getElementById('fy').value,
      month: document.getElementById('fm').value,
      day: document.getElementById('fd').value,
      hour: document.getElementById('fh').value,
      minute: document.getElementById('fmin').value,
      gender: document.getElementById('fgender').value,
      longitude: document.getElementById('flo').value||null,
      liunian_year: document.getElementById('fln').value||null,
    },
    data: _lastData,
  };
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  const dt=new Date().toISOString().slice(0,10).replace(/-/g,'');
  const name=`ziwei_${_lastData.birth_solar||'chart'}_${dt}.json`.replace(/[^a-z0-9_.\-]/gi,'_');
  a.href=URL.createObjectURL(blob);a.download=name;
  document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);document.body.removeChild(a);},1000);
}

/* ── @media print 时间戳注入 ─────────────────────────────── */
window.addEventListener('beforeprint',()=>{
  const now=new Date().toLocaleString('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
  document.body.setAttribute('data-print-time',now);
});

/* ── Tab3 快速跳转 ──────────────────────────────────────── */
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
function readUrlParams(){
  const p=new URLSearchParams(location.search);
  if(!p.has('y'))return false;
  document.getElementById('fy').value=p.get('y')||2002;
  document.getElementById('fm').value=p.get('m')||3;
  document.getElementById('fd').value=p.get('d')||13;
  document.getElementById('fh').value=p.get('h')||14;
  document.getElementById('fmin').value=p.get('min')||55;
  const g=p.get('g');if(g)document.getElementById('fgender').value=g;
  const lo=p.get('lo');if(lo)document.getElementById('flo').value=lo;
  const ln=p.get('ln');if(ln)document.getElementById('fln').value=ln;
  return true;
}

/* ── 历史记录（localStorage） ──────────────────────────────── */
const LS_KEY='ziwei_hist';
function _lsGet(){try{return JSON.parse(localStorage.getItem(LS_KEY)||'[]');}catch(_){return[];}}
function _lsSet(v){try{localStorage.setItem(LS_KEY,JSON.stringify(v));}catch(_){}}

function saveHistory(body,chart){
  const hist=_lsGet();
  const label=`${body.year}-${String(body.month).padStart(2,'0')}-${String(body.day).padStart(2,'0')} ${body.gender}`;
  const item={...body,ts:Date.now(),label,wuxing:chart.wuxing_ju_name||'',life_gz:chart.life_palace_gz||''};
  const deduped=hist.filter(h=>!(h.year===item.year&&h.month===item.month&&h.day===item.day&&h.hour===item.hour&&h.gender===item.gender));
  deduped.unshift(item);
  if(deduped.length>5)deduped.splice(5);
  _lsSet(deduped);renderHistory();
}

function renderHistory(){
  const hist=_lsGet(),hlist=document.getElementById('hlist'),hbtn=document.getElementById('hbtn');
  if(!hlist||!hbtn)return;
  const badge=hist.length?`<span style="font-size:.6rem;background:var(--accent);color:#fff;border-radius:8px;padding:0 4px;margin-left:3px">${hist.length}</span>`:'';
  hbtn.innerHTML='历史'+badge;
  if(!hist.length){hlist.innerHTML='<span style="font-size:.8rem;color:var(--muted);padding:4px 0;display:block">暂无记录</span>';return;}
  hlist.innerHTML=hist.map((item,i)=>
    `<div class="hist-item" onclick="applyHist(${i})">
      <span>${esc(item.label)}</span>
      <span class="hi-gz">${esc(item.life_gz)} ${esc(item.wuxing)}</span>
      <span class="hi-del" onclick="delHist(${i},event)" title="删除">×</span>
    </div>`).join('');
}

function toggleHist(){document.getElementById('hbar').classList.toggle('show');}

function applyHist(idx){
  const item=_lsGet()[idx];if(!item)return;
  document.getElementById('fy').value=item.year;
  document.getElementById('fm').value=item.month;
  document.getElementById('fd').value=item.day;
  document.getElementById('fh').value=item.hour;
  document.getElementById('fmin').value=item.minute;
  document.getElementById('fgender').value=item.gender;
  document.getElementById('flo').value=item.longitude!=null?item.longitude:'';
  document.getElementById('fln').value=item.liunian_year!=null?item.liunian_year:'';
  document.getElementById('hbar').classList.remove('show');
  go();
}

function delHist(idx,e){
  e.stopPropagation();
  const hist=_lsGet();hist.splice(idx,1);_lsSet(hist);renderHistory();
}

function clearAllHist(){
  _lsSet([]);renderHistory();
  document.getElementById('hbar').classList.remove('show');
}

/* ── 页面初始化 ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded',async()=>{
  initTheme();
  initCities();
  initCompatCities();
  renderHistory();
  if(readUrlParams())await go();
});

/* ── 合盘功能 ────────────────────────────────────────────── */
function toggleCompat(){
  const wrap=document.getElementById('compat-wrap');
  const btn=document.getElementById('compat-btn');
  const vis=wrap.style.display!=='none';
  wrap.style.display=vis?'none':'block';
  btn.textContent=vis?'⊕ 合盘':'⊖ 隐藏合盘';
  if(!vis)wrap.scrollIntoView({behavior:'smooth',block:'nearest'});
}

async function initCompatCities(){
  try{
    const r=await fetch('/api/v1/cities');
    if(!r.ok)return;
    const cities=await r.json();
    const sel=document.getElementById('bcity');
    cities.forEach(c=>{
      const opt=document.createElement('option');
      opt.value=c.lng;
      opt.textContent=c.name+' ('+c.province+')';
      sel.appendChild(opt);
    });
  }catch(_){}
}

function onBCityChange(){
  const sel=document.getElementById('bcity');
  if(sel.value)document.getElementById('blo').value=parseFloat(sel.value).toFixed(2);
}

function onBCityChange(){
  const sel=document.getElementById('bcity');
  if(sel.value)document.getElementById('blo').value=parseFloat(sel.value).toFixed(2);
}

/* ── 多人合盘功能 ─────────────────────────────────────────── */
const MCOMPAT_LABELS=['甲方','乙方','丙方','丁方'];
const MCOMPAT_COLORS=['#b8862a','#7c3aed','#0891b2','#059669'];
let _mcPersons=[]; // [{year,month,day,hour,minute,gender,longitude?},...]

/* ── 生活建议类别切换 ─────────────────────────────────────── */
function switchLsugCat(cat){
  document.querySelectorAll('.lsug-ctab').forEach(b=>{
    b.classList.toggle('act', b.textContent.trim().includes(cat) ||
      (b.onclick && b.getAttribute('onclick') && b.getAttribute('onclick').includes(`'${cat}'`)));
  });
  // 用 onclick 属性中的 cat 参数匹配更可靠
  document.querySelectorAll('.lsug-ctab').forEach(b=>{
    const oc=b.getAttribute('onclick')||'';
    b.classList.toggle('act', oc.includes(`'${cat}'`));
  });
  document.querySelectorAll('.lsug-cat-panel').forEach(p=>{
    p.classList.toggle('act', p.dataset.cat===cat);
  });
}

function toggleMultiCompat(){
  const wrap=document.getElementById('mcompat-wrap');
  const btn=document.getElementById('mcompat-btn');
  const vis=wrap.style.display!=='none';
  wrap.style.display=vis?'none':'block';
  btn.textContent=vis?'⊕ 多人合盘':'⊖ 隐藏多人合盘';
  if(!vis){
    if(_mcPersons.length===0)_mcPersons=[{year:1990,month:1,day:1,hour:10,minute:0,gender:'男'},{year:1992,month:6,day:15,hour:8,minute:0,gender:'女'}];
    renderMCompatForms();
    wrap.scrollIntoView({behavior:'smooth',block:'nearest'});
  }
}

function renderMCompatForms(){
  const cont=document.getElementById('mcompat-persons');
  let h='';
  _mcPersons.forEach((p,i)=>{
    const col=MCOMPAT_COLORS[i]||'#666';
    h+=`<div class="mcp-person-card" id="mcp-card-${i}">`;
    h+=`<div class="mcp-person-title" style="color:${col}">${MCOMPAT_LABELS[i]} · 第${i+1}人${i>=2?`<button class="mcp-del-btn" onclick="delMCompatPerson(${i})">删除</button>`:'<span></span>'}</div>`;
    h+=`<div class="form-row" style="flex-wrap:wrap;gap:6px 14px">`;
    h+=`<div class="fg"><label>出生年</label><input class="w-yr" type="number" id="mcp-y-${i}" value="${p.year}" min="1900" max="2100"></div>`;
    h+=`<div class="fg"><label>月</label><input class="w-mo" type="number" id="mcp-m-${i}" value="${p.month}" min="1" max="12"></div>`;
    h+=`<div class="fg"><label>日</label><input class="w-dy" type="number" id="mcp-d-${i}" value="${p.day}" min="1" max="31"></div>`;
    h+=`<div class="fg"><label>时(24h)</label><input class="w-hr" type="number" id="mcp-h-${i}" value="${p.hour}" min="0" max="23"></div>`;
    h+=`<div class="fg"><label>分</label><input class="w-mn" type="number" id="mcp-min-${i}" value="${p.minute}" min="0" max="59"></div>`;
    h+=`<div class="fg"><label>性别</label><select class="w-gen" id="mcp-g-${i}"><option value="男"${p.gender==='男'?' selected':''}>男</option><option value="女"${p.gender==='女'?' selected':''}>女</option></select></div>`;
    h+=`<div class="fg"><label>经度(可选)</label><input class="w-lo" type="number" id="mcp-lo-${i}" value="${p.longitude||''}" placeholder="如 121.5" step="0.1"></div>`;
    h+=`</div></div>`;
  });
  cont.innerHTML=h;
  const addBtn=document.getElementById('mcompat-add-btn');
  if(addBtn)addBtn.style.display=_mcPersons.length>=4?'none':'inline-flex';
}

function addMCompatPerson(){
  if(_mcPersons.length>=4)return;
  _mcPersons.push({year:1995,month:3,day:20,hour:12,minute:0,gender:'男'});
  renderMCompatForms();
  const addBtn=document.getElementById('mcompat-add-btn');
  if(addBtn)addBtn.textContent=_mcPersons.length<4?`＋ 添加第${_mcPersons.length+1}人`:'（最多4人）';
}

function delMCompatPerson(i){
  _mcPersons.splice(i,1);
  renderMCompatForms();
  const addBtn=document.getElementById('mcompat-add-btn');
  if(addBtn){addBtn.style.display='inline-flex';addBtn.textContent=`＋ 添加第${_mcPersons.length+1}人`;}
}

function _collectMCompatPersons(){
  return _mcPersons.map((_,i)=>{
    const obj={
      year:+document.getElementById(`mcp-y-${i}`).value,
      month:+document.getElementById(`mcp-m-${i}`).value,
      day:+document.getElementById(`mcp-d-${i}`).value,
      hour:+document.getElementById(`mcp-h-${i}`).value,
      minute:+document.getElementById(`mcp-min-${i}`).value||0,
      gender:document.getElementById(`mcp-g-${i}`).value,
    };
    const lo=document.getElementById(`mcp-lo-${i}`).value;
    if(lo)obj.longitude=+lo;
    return obj;
  });
}

async function goMultiCompat(){
  const errEl=document.getElementById('mcompat-err');
  errEl.style.display='none';
  const persons=_collectMCompatPersons();
  if(persons.length<2){errEl.textContent='至少需要2人';errEl.style.display='block';return;}
  const btnEl=document.querySelector('#mcompat-wrap .btn');
  btnEl.textContent='计算中…';btnEl.disabled=true;
  try{
    const r=await fetch('/api/v1/ziwei/multi_compat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({person_list:persons})
    });
    if(!r.ok){const e=await r.json();throw new Error(e.detail||r.statusText);}
    const data=await r.json();
    renderMultiCompat(data,persons);
    document.getElementById('mcompat-result').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(e){
    errEl.textContent='错误: '+e.message;errEl.style.display='block';
  }finally{
    btnEl.textContent='计算缘分矩阵';btnEl.disabled=false;
  }
}

function renderMultiCompat(d, persons){
  const res=document.getElementById('mcompat-result');
  const con=document.getElementById('mcompat-content');
  res.style.display='block';
  const n=d.person_count;
  const lbls=MCOMPAT_LABELS.slice(0,n);
  const cols=MCOMPAT_COLORS.slice(0,n);
  let h=`<div class="sec-title">☯ 多人合盘 · 缘分矩阵</div>`;
  /* 团队和谐指数 */
  const hs=d.team_harmony_score;
  const hLevel=hs>=85?'极佳':hs>=70?'良好':hs>=55?'一般':'较弱';
  h+=`<div class="mcompat-harmony">`;
  h+=`<div class="mcompat-harmony-score">${hs}</div>`;
  h+=`<div class="mcompat-harmony-label"><div style="font-weight:700;font-size:1rem">${hLevel}</div><div>团队和谐指数（满分 100）</div></div>`;
  h+=`</div>`;
  /* N×N 矩阵 */
  h+=`<div style="overflow-x:auto;margin:12px 0"><table class="mcompat-matrix"><tr><th></th>`;
  lbls.forEach((l,i)=>h+=`<th style="color:${cols[i]}">${l}</th>`);
  h+=`</tr>`;
  for(let i=0;i<n;i++){
    h+=`<tr><th style="color:${cols[i]}">${lbls[i]}</th>`;
    for(let j=0;j<n;j++){
      const s=d.matrix[i][j];
      if(i===j){h+=`<td class="mcs-self">—</td>`;continue;}
      const cls=s>=85?'mcs-hi':s>=70?'mcs-good':s>=55?'mcs-mid':'mcs-lo';
      h+=`<td class="${cls}">${s}</td>`;
    }
    h+=`</tr>`;
  }
  h+=`</table></div>`;
  /* 图例 */
  h+=`<div style="display:flex;gap:10px;flex-wrap:wrap;font-size:.72rem;margin-bottom:12px">`;
  [['mcs-hi','≥85 极佳'],['mcs-good','≥70 良好'],['mcs-mid','≥55 一般'],['mcs-lo','＜55 较弱']].forEach(([cls,lbl])=>{
    h+=`<span class="${cls}" style="padding:2px 8px;border-radius:4px">${lbl}</span>`;
  });
  h+=`</div>`;
  /* 两两对列表 */
  h+=`<div class="fc-divider">两两合盘详情</div>`;
  h+=`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:10px">`;
  for(const pair of d.pairs){
    const ia=pair.person_a_idx,ib=pair.person_b_idx;
    const pct=Math.round(pair.total_score/pair.max_score*100);
    const bg=pct>=85?'#fef9c3':pct>=70?'#dcfce7':pct>=55?'#fef3c7':'#fee2e2';
    const tc=pct>=85?'#713f12':pct>=70?'#14532d':pct>=55?'#92400e':'#7f1d1d';
    h+=`<div style="background:${bg};border-radius:8px;padding:10px 14px;border:1px solid rgba(0,0,0,.08)">`;
    h+=`<div style="font-size:.8rem;font-weight:700;margin-bottom:4px"><span style="color:${cols[ia]}">${lbls[ia]}</span> × <span style="color:${cols[ib]}">${lbls[ib]}</span></div>`;
    h+=`<div style="font-size:1.6rem;font-weight:700;color:${tc};line-height:1">${pair.total_score}<span style="font-size:.7rem;color:${tc};font-weight:400"> / ${pair.max_score}</span></div>`;
    h+=`<div style="font-size:.78rem;color:${tc};margin-top:2px">${esc(pair.level)}</div>`;
    h+=`</div>`;
  }
  h+=`</div>`;
  con.innerHTML=h;
}

async function goCompat(){
  const errEl=document.getElementById('compat-err');
  errEl.style.display='none';
  const a={
    year:+document.getElementById('fy').value,
    month:+document.getElementById('fm').value,
    day:+document.getElementById('fd').value,
    hour:+document.getElementById('fh').value,
    minute:+document.getElementById('fmin').value||0,
    gender:document.getElementById('fgender').value
  };
  const alo=document.getElementById('flo').value;if(alo)a.longitude=+alo;
  const b={
    year:+document.getElementById('by').value,
    month:+document.getElementById('bm').value,
    day:+document.getElementById('bd').value,
    hour:+document.getElementById('bh').value,
    minute:+document.getElementById('bmin').value||0,
    gender:document.getElementById('bgender').value
  };
  const blo=document.getElementById('blo').value;if(blo)b.longitude=+blo;

  const btnEl=document.querySelector('#compat-wrap .btn');
  btnEl.textContent='计算中…';btnEl.disabled=true;
  try{
    const r=await fetch('/api/v1/ziwei/compatibility',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({person_a:a,person_b:b})
    });
    if(!r.ok){const e=await r.json();throw new Error(e.detail||r.statusText);}
    const data=await r.json();
    renderCompat(data);
    document.getElementById('compat-result').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(e){
    errEl.textContent='错误: '+e.message;errEl.style.display='block';
  }finally{
    btnEl.textContent='计算六合度';btnEl.disabled=false;
  }
}

function renderCompat(d){
  const res=document.getElementById('compat-result');
  const con=document.getElementById('compat-content');
  res.style.display='block';
  const PCT=Math.round(d.total_score/d.max_score*100);
  const scoreColor=PCT>=75?'#14532d':PCT>=55?'#713f12':'#7f1d1d';
  let h=`<div class="sec-title">☯ 合盘结果 · 六合度分析</div>`;
  h+=`<div class="compat-header">`;
  h+=`<div style="text-align:center"><div class="compat-score" style="color:${scoreColor}">${d.total_score}</div><div style="font-size:.7rem;color:var(--muted)">满分 ${d.max_score}</div></div>`;
  h+=`<div style="text-align:center"><div class="compat-level">${esc(d.level)}</div></div>`;
  h+=`<div class="compat-summary">${esc(d.summary)}</div>`;
  h+=`</div>`;
  /* 双方信息 */
  const pa=d.person_a_info,pb=d.person_b_info;
  h+=`<div class="compat-persons">`;
  h+=`<div class="compat-person" style="border-left:3px solid #b8862a"><h4>甲方</h4><p>${esc(pa.birth_solar)} ${esc(pa.gender)}<br>命宫 ${esc(pa.life_gz)} &nbsp; ${esc(pa.wuxing_ju)}</p></div>`;
  h+=`<div class="compat-person" style="border-left:3px solid #7c3aed"><h4>乙方</h4><p>${esc(pb.birth_solar)} ${esc(pb.gender)}<br>命宫 ${esc(pb.life_gz)} &nbsp; ${esc(pb.wuxing_ju)}</p></div>`;
  h+=`</div>`;
  /* 双色叠加雷达图 */
  h+=buildCompatRadar(d);
  /* 冲合点 / 合和点 / 互补点 */
  const ptSecs=[
    {key:'harmony_points',cls:'cpt-harm',icon:'💚',title:'合和点'},
    {key:'conflict_points',cls:'cpt-conf',icon:'⚡',title:'冲克点'},
    {key:'complement_points',cls:'cpt-comp',icon:'🔵',title:'互补点'},
  ];
  let hasPts=false;
  for(const sec of ptSecs){
    const pts=d[sec.key]||[];
    if(!pts.length)continue;
    if(!hasPts){h+=`<div class="fc-divider" style="margin-top:14px">吸引与矛盾 · 冲合分析</div>`;hasPts=true;}
    h+=`<div class="cpt-section"><div class="cpt-title">${sec.icon} ${sec.title}</div><div class="cpt-chips">`;
    for(const pt of pts)h+=`<span class="cpt-chip ${sec.cls}">${esc(pt)}</span>`;
    h+=`</div></div>`;
  }
  /* 各维度进度条 */
  h+=`<div class="fc-divider" style="margin-top:14px">各维度分析</div><div class="compat-dims">`;
  for(const dim of d.dimensions){
    const pct=Math.round(dim.score/dim.max_score*100);
    const fillColor=pct>=75?'#16a34a':pct>=55?'#ca8a04':'#e11d48';
    h+=`<div><div class="compat-dim">`;
    h+=`<div class="cdim-name">${esc(dim.name)}</div>`;
    h+=`<div class="cdim-bar"><div class="cdim-fill" style="width:${pct}%;background:${fillColor}"></div></div>`;
    h+=`<div class="cdim-score">${dim.score}/${dim.max_score}</div>`;
    h+=`</div><div class="cdim-desc">${esc(dim.description)}</div></div>`;
  }
  h+=`</div>`;
  /* 宫位对比表 */
  if(d.palace_compare&&d.palace_compare.length){
    h+=`<div class="fc-divider" style="margin-top:14px">六大宫位 · 双方对比</div>`;
    h+=`<table class="cpal-table"><tr><th>宫位</th><th style="color:#b8862a">甲方（干支·主星）</th><th>宫位地支关系</th><th style="color:#7c3aed">乙方（干支·主星）</th></tr>`;
    for(const row of d.palace_compare){
      const rmap={'六合':'cpal-rel-he','三合':'cpal-rel-san','相冲':'cpal-rel-chong','同支':'cpal-rel-same'};
      const relBadge=row.relation?`<span class="cpal-rel ${rmap[row.relation]||''}">${row.relation}</span>`:'—';
      h+=`<tr><td style="font-weight:700">${row.palace}</td>`;
      h+=`<td>${esc(row.a_gz)} <span style="color:var(--muted)">${esc(row.a_stars)}</span>`;
      if(row.a_tags&&row.a_tags.length)h+=`<br><span style="font-size:.65rem;color:var(--muted)">${row.a_tags.map(esc).join(' ')}</span>`;
      h+=`</td><td style="text-align:center">${relBadge}</td>`;
      h+=`<td>${esc(row.b_gz)} <span style="color:var(--muted)">${esc(row.b_stars)}</span>`;
      if(row.b_tags&&row.b_tags.length)h+=`<br><span style="font-size:.65rem;color:var(--muted)">${row.b_tags.map(esc).join(' ')}</span>`;
      h+=`</td></tr>`;
    }
    h+=`</table>`;
  }
  con.innerHTML=h;
}

/* 双色叠加雷达图（甲方金色 / 乙方紫色虚线） */
function buildCompatRadar(d){
  const DIMS=['命宫相合','五行相生','年支缘分','夫妻宫缘','阴阳互补'];
  const n=DIMS.length;
  const dimMap={};
  for(const dm of d.dimensions)dimMap[dm.name]=dm;
  const scoresA=DIMS.map(k=>dimMap[k]?Math.round(dimMap[k].score/dimMap[k].max_score*100):50);
  /* 乙方视角：用 (max_score - score) 的镜像，体现互补/对立 */
  const scoresB=DIMS.map(k=>dimMap[k]?Math.round((dimMap[k].max_score-dimMap[k].score)/dimMap[k].max_score*100+30):50).map(v=>Math.max(20,Math.min(98,v)));
  const cx=90,cy=88,R=62;
  const pt=(i,r)=>{const a=-Math.PI/2+i*Math.PI*2/n;return{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)};};
  let svg='';
  [0.25,0.5,0.75,1].forEach(f=>{
    const pp=Array.from({length:n},(_,i)=>pt(i,R*f));
    svg+=`<polygon points="${pp.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}" fill="none" stroke="var(--border-lt)" stroke-width="${f===1?1.2:0.7}"/>`;
  });
  Array.from({length:n},(_,i)=>{const p=pt(i,R);svg+=`<line x1="${cx}" y1="${cy}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" stroke="var(--border-lt)" stroke-width="0.8"/>`;});
  const pA=scoresA.map((s,i)=>pt(i,R*s/100));
  svg+=`<polygon points="${pA.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}" fill="#b8862a" fill-opacity=".22" stroke="#b8862a" stroke-width="1.8" stroke-linejoin="round"/>`;
  pA.forEach(p=>svg+=`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3" fill="#b8862a" stroke="var(--paper)" stroke-width="1"/>`);
  const pB=scoresB.map((s,i)=>pt(i,R*s/100));
  svg+=`<polygon points="${pB.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}" fill="#7c3aed" fill-opacity=".14" stroke="#7c3aed" stroke-width="1.6" stroke-linejoin="round" stroke-dasharray="5,3"/>`;
  pB.forEach(p=>svg+=`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3" fill="#7c3aed" stroke="var(--paper)" stroke-width="1"/>`);
  DIMS.forEach((lbl,i)=>{
    const lp=pt(i,R+15);
    svg+=`<text x="${lp.x.toFixed(1)}" y="${lp.y.toFixed(1)}" text-anchor="middle" dominant-baseline="central" font-size="9.5" font-weight="600" fill="var(--text)">${lbl}</text>`;
  });
  svg+=`<text x="${cx}" y="${cy-5}" text-anchor="middle" font-size="13" font-weight="700" fill="var(--gold)">${d.total_score}</text>`;
  svg+=`<text x="${cx}" y="${cy+8}" text-anchor="middle" font-size="7.5" fill="var(--muted)">六合度</text>`;
  const leg=`<div style="font-size:.72rem;line-height:2.2">`+
    `<div style="display:flex;align-items:center;gap:6px"><span style="width:16px;height:3px;background:#b8862a;display:inline-block;border-radius:2px"></span>甲方</div>`+
    `<div style="display:flex;align-items:center;gap:6px"><span style="width:16px;height:3px;background:#7c3aed;display:inline-block;border-radius:2px"></span>乙方（镜像）</div>`+
    DIMS.map((k,i)=>`<div style="color:var(--muted)">${k}：${scoresA[i]}%</div>`).join('')+
    `</div>`;
  return `<div style="display:flex;gap:14px;align-items:flex-start;background:var(--bg);border-radius:8px;padding:10px 12px 8px;margin-bottom:12px;flex-wrap:wrap"><svg viewBox="0 0 180 175" style="width:180px;flex-shrink:0;display:block;overflow:visible">${svg}</svg>${leg}</div>`;
}

/* ── 词汇表悬浮面板 ───────────────────────────────────────── */
let _glossData=null, _glossCat='全部';
let _glossMap = {};   // §4 term → short definition map

function _buildGlossMap(){
  if(!_glossData)return;
  _glossMap = {};
  for(const g of _glossData){
    if(g.term){
      const def = (g.definition||'').slice(0,60) + ((g.definition||'').length>60?'…':'');
      _glossMap[g.term] = def;
    }
  }
}

function injectGlossTooltips(){
  if(!_glossData){
    // 懒加载：首次调用时拉取词汇表再注入
    fetch('/api/v1/glossary').then(r=>r.ok?r.json():null).then(d=>{
      if(!d)return;
      _glossData=d;
      _buildGlossMap();
      injectGlossTooltips();
    }).catch(()=>{});
    return;
  }
  document.querySelectorAll('.sn').forEach(el=>{
    const name=el.textContent.trim();
    if(_glossMap[name]){
      el.setAttribute('data-gt', _glossMap[name]);
    }
  });
}

async function toggleGloss(){
  const panel=document.getElementById('gloss-panel');
  const overlay=document.getElementById('gloss-overlay');
  if(panel.classList.contains('open')){closeGloss();return;}
  panel.classList.add('open');overlay.classList.add('show');
  if(!_glossData){
    try{
      const r=await fetch('/api/v1/glossary');
      if(r.ok){_glossData=await r.json();}else{_glossData=[];}
    }catch(e){_glossData=[];}
    _buildGlossMap();
    _buildGlossCats();filterGloss();
  }
}

function closeGloss(){
  document.getElementById('gloss-panel').classList.remove('open');
  document.getElementById('gloss-overlay').classList.remove('show');
}

function _buildGlossCats(){
  if(!_glossData)return;
  const cats=['全部',...new Set(_glossData.map(g=>g.category).filter(Boolean))];
  document.getElementById('gloss-cats').innerHTML=cats.map(c=>
    `<button class="gloss-cat${c==='全部'?' act':''}" onclick="setGlossCat('${c}')">${esc(c)}</button>`
  ).join('');
}

function setGlossCat(c){
  _glossCat=c;
  document.querySelectorAll('.gloss-cat').forEach(b=>b.classList.toggle('act',b.textContent===c));
  filterGloss();
}

function filterGloss(){
  if(!_glossData){document.getElementById('gloss-list').innerHTML='<div style="padding:20px;text-align:center;color:var(--muted)">加载中…</div>';return;}
  const q=(document.getElementById('gloss-search').value||'').trim().toLowerCase();
  const items=_glossData.filter(g=>{
    if(_glossCat!=='全部'&&g.category!==_glossCat)return false;
    if(q&&!(g.term||'').toLowerCase().includes(q)&&!(g.definition||'').toLowerCase().includes(q))return false;
    return true;
  });
  document.getElementById('gloss-cnt').textContent=`共 ${items.length} 条`;
  document.getElementById('gloss-list').innerHTML=items.map((g,i)=>
    `<div class="gloss-item" id="gi-${i}" onclick="toggleGlossItem(${i})">
      <div><span class="gloss-term">${esc(g.term||'')}</span><span class="gloss-pin">${esc(g.pinyin||'')}</span><span class="gloss-cat-badge">${esc(g.category||'')}</span></div>
      <div class="gloss-detail" id="gd-${i}" style="display:none">
        <div class="gloss-def">${esc(g.definition||'')}</div>
        ${g.classic_source?`<div class="gloss-src">📚 ${esc(g.classic_source)}</div>`:''}
      </div>
    </div>`
  ).join('');
}

function toggleGlossItem(i){
  const d=document.getElementById('gd-'+i);
  const it=document.getElementById('gi-'+i);
  if(!d)return;
  const open=d.style.display==='block';
  d.style.display=open?'none':'block';
  it.classList.toggle('open',!open);
}

/* ══════════════════ 星曜详情弹窗 ══════════════════════════════ */
const STAR_INFO={
  '紫微':{cat:'北斗主星',wux:'土',yin:'阴',desc:'十四主星之首，化气为「尊贵」。主多翰、尊贵、开创力、领导力，对与辅弼、天相、天梁同宫或三方有力。单守无辅则弱。',adv:'宜公别事务，贵人提挈，势力圣地'},
  '天机':{cat:'南斗主星',wux:'木',yin:'阴',desc:'化气为「机智」。主沉喜、思维敏捷、机心重、善谋划，精于分析与谋略。最怕居陷地与化忌同宫。如遇居陷地与化忌同宫则谋事多费。',adv:'宜技术、策划、资讯工作，忌独断'},
  '太阳':{cat:'南斗主星',wux:'火',yin:'阳',desc:'化气为「富贵」。主刚、光明、外向、仗贸，是心期之星。在日边（富路) 客宫最为贵。女命和父角缘分指标。',adv:'宜公共事务、明星、发表展示'},
  '武曲':{cat:'北斗主星',wux:'金',yin:'阳',desc:'化气为「富足」。主勇敢、执行力强、金融财富，崇尚实际行动而非空谈。孤寡奇偶力不小。煞如居陷刚、金轮明之陷则强异之眉。',adv:'宜金融、管理、财务工作'},
  '天同':{cat:'北斗主星',wux:'水',yin:'阳',desc:'化气为「福寿」。主健康、悠闲、重感情、之落。嗤人无连续居安就干办。孩子星，主活泼可爱不感少年心情。',adv:'平和处事，适宜艺术、服务行业'},
  '廉贞':{cat:'北斗主星',wux:'火',yin:'陈',desc:'化气为「囚围」。主决断、基础、干练。内心严谨、外表和善。自化气为囚毙，难展其基。心志高远但知进退。',adv:'宜内勤、行政、算法技术工作'},
  '天府':{cat:'南斗主星',wux:'土',yin:'阳',desc:'化气为「令主」。南斗第一富贵庙星。属阴中之阳。主财富、物质、安居良。最喜有主星提挈，单茎些弱。',adv:'宜财务、基础、公务将氅'},
  '太阴':{cat:'南斗主星',wux:'水',yin:'阴',desc:'化气为「富贵」（女对旺）。主梅花、旖丽、感情丰富。日月同宫是特能型格。女性在旺宫克应。夜生人更得其力。',adv:'宜艺术、美容、教育行业'},
  '贪狼':{cat:'北斗主星',wux:'水木',yin:'阴',desc:'化气为「欲望」。蜃蜴之星，多色、欲望强、艺术才华。大层、成器晚成型，融谋奈何。桓北金一刘鼢替。',adv:'宜战略、谈判、娱乐演艺行业'},
  '巨门':{cat:'北斗主星',wux:'水',yin:'阴',desc:'化气为「暗」。主口色、滔辩、是非「口液」。若遇化权则言创奇功，化忌则口舰大起。居陷地寄宫则晦岙。',adv:'宜法律、媒体、教育、胡辩贯诉行业'},
  '天相':{cat:'南斗主星',wux:'水',yin:'阳',desc:'化气为「印绶」。服务、辅佐之星，善于协调、审审批准，心地善良。小人之星，需官辅佐。如居陷地则赏罚不分。',adv:'宜助理、协调、行政办公工作'},
  '天梁':{cat:'南斗主星',wux:'木',yin:'阳',desc:'化气为「清洁」。明烺对性，喜指导他人。最为长辈明工之星。咖啡超运，若非四化公傧则渐耐性强。老年得子刑家剿。',adv:'宜宗教、学术研究、财务顾问'},
  '七杀':{cat:'北斗主星',wux:'金',yin:'阴',desc:'化气为「将林」。刘宁成亿脚，所过之处斧山乎可。主警训、孤处、最土干。社会运动山包。右弼左辅典则成尊贵局。',adv:'宜军事、运动、高考备考期途动'},
  '破军':{cat:'北斗主星',wux:'水',yin:'阴',desc:'化气为「耗散」。对旧事物有破坏力，主改革、创新、成填。强势移居、迁动非常。相冲来后方谋。',adv:'宜创业、平台转型、自由职业'},
  /* 煞星 */
  '擎羊':{cat:'北斗煞星',wux:'金',yin:'阳',desc:'属金，主刑伤、壁刀、事故。命宫逢之奉献边，难免小灵。与北斗干删点展则伏杀为用兵。',adv:'宜军事法律外科工作'},
  '陀罗':{cat:'北斗煞星',wux:'土',yin:'阴',desc:'属土、主拖延、小人、暴房、刘伤。罗屯在阳完全公公赞。底返动不利，成事需花费山力。',adv:'宜耐心丛中工作，忌冲动'},
  '火星':{cat:'北斗火元煞',wux:'火',yin:'阳',desc:'主壁燃、冲动、杀伤。奇狂姿旖。在宫的正陈自然主急冲动。居陷地时加重伤害。',adv:'宜技术研发、消防、急病展示'},
  '铃星':{cat:'北斗火元煞',wux:'火',yin:'阴',desc:'主孤离、冲动、处事忘子。厉害时进却慢于火星。与大加四化主运山前三年害。',adv:'宜履个世界题才艺技工作'},
  '地空':{cat:'垣府煞星',wux:'水',yin:'附',desc:'属阴圣。主空愿、想象力强、孤矸内废。如居守宫九则共泉。版宫所入成务广泛。',adv:'宜精神层面工作，迟起工作'},
  '地劫':{cat:'垣府煞星',wux:'火',yin:'阴',desc:'属阴火。主山垂、意外、劫善。害于迎年年蛤法。大局和地空同宫小志汇集评判。',adv:'宜学习弅证、其他想象装备'},
  /* 吉星 */
  '文昌':{cat:'文星',wux:'金',yin:'阳',desc:'主考试、属旧官、割功名。入命宫/第三宫/官绸/迁移宫最吉。子年生居陷地，年少时没法考。化忌圣学就读不安定。',adv:'宜文化、媒体、出版、学术工作'},
  '文曲':{cat:'文星',wux:'水',yin:'阴',desc:'主艺术、表演、文学。入命宫最得多华。化忌列宦极为不利。与文昌不同，文曲主知行当落。运期遇之最为侪气。',adv:'宜艺术表演、设计创意行业'},
  '天魁':{cat:'天使',wux:'水',yin:'阳',desc:'魁主贵人提挈、吉人帮助。与天钺同宫为左右周全色。游帅刺备于鸟、天使在自年存也有最丰。贵人提挈，在途这渐平进。',adv:'宜公事务、广路人脉、政务工作'},
  '天钺':{cat:'天使',wux:'火',yin:'阴',desc:'钺主女为贵人提挈、正雅和尚。充满变很有情诩谅。天魁天钺同宫为最特定遍\\u7375山贵。偏墙向女性缘分。',adv:'宜公共事务、女性工作环境'},
  '左辅':{cat:'左强',wux:'土',yin:'阳',desc:'左辅外展结业。左巡审芝达心。主得下属辅佐、「衣食足」。天府、天相入命宫最为吉庆。',adv:'宜领导管理、团队协作工作'},
  '右弼':{cat:'右弼',wux:'水',yin:'阴',desc:'右弼内卫唐迫魂。主得广泛范围的支撑和审核。左强架外露、右弼居内宫。与左辅共塑则壁埠异彰。',adv:'宜广益人脉工作，广存自缴'}
};
const STAR_CAT_COLOR={'北斗主星':'main','南斗主星':'main','北斗煞星':'sha','南斗煞星':'sha',
  '北斗火元煞':'sha','垣府煞星':'sha','文星':'ji','天使':'ji','左强':'ji','右弼':'ji'};

function showStarInfo(name,evt){
  if(evt){evt.stopPropagation();}
  const info=STAR_INFO[name];
  const ov=document.getElementById('star-overlay');
  const mo=document.getElementById('star-modal');
  if(!info){
    mo.innerHTML=`<div class="smi-hdr"><span class="smi-name">${esc(name)}</span><button class="smi-close" onclick="closeStarInfo()">✕</button></div><p style="font-size:.82rem;color:var(--muted);padding:8px 0">暂无该星曜的详细资料。</p>`;
  }else{
    const catCls=STAR_CAT_COLOR[info.cat]||'aux';
    mo.innerHTML=
      `<div class="smi-hdr">`+
      `<div><span class="smi-name sn ${catCls}">${esc(name)}</span><span class="smi-cat">${esc(info.cat)}</span></div>`+
      `<button class="smi-close" onclick="closeStarInfo()">✕</button></div>`+
      `<div class="smi-row"><span class="smi-badge smi-wux">五行: ${esc(info.wux)}</span>`+
      `<span class="smi-badge ${info.yin==='阴'?'smi-yin':'smi-yang'}">${esc(info.yin)}</span></div>`+
      `<div class="smi-section">化气 / 明征</div>`+
      `<div class="smi-desc">${esc(info.desc)}</div>`+
      `<div class="smi-adv">💼 适西方向：${esc(info.adv)}</div>`;
  }
  ov.classList.add('show');
  mo.style.display='block';
}
/* ══════════════════ 宫位笔记 ═══════════════════════════════ */
let _notePalace=null;
let _noteMode=false;
function NOTE_KEY(birth){
  const bd=_lastData&&_lastData.birth_solar?_lastData.birth_solar:'default';
  return 'zw_notes_'+bd;
}
function getPalNote(name){
  try{
    const k=NOTE_KEY();
    const all=JSON.parse(localStorage.getItem(k)||'{}');
    return all[name]||'';
  }catch(e){return '';}
}
function setPalNote(name,txt){
  try{
    const k=NOTE_KEY();
    const all=JSON.parse(localStorage.getItem(k)||'{}');
    if(txt.trim())all[name]=txt.trim();else delete all[name];
    localStorage.setItem(k,JSON.stringify(all));
  }catch(e){}
}
function toggleNoteMode(){
  _noteMode=!_noteMode;
  document.querySelectorAll('.pal-note-btn').forEach(b=>{
    b.style.opacity=_noteMode?'0.9':'';
  });
  const btn=document.getElementById('note-toggle-btn');
  if(btn)btn.classList.toggle('act',_noteMode);
}
function openNoteModal(palName,evt){
  if(evt)evt.stopPropagation();
  _notePalace=palName;
  const txt=getPalNote(palName);
  document.getElementById('note-ta').value=txt;
  document.getElementById('note-modal-title').textContent=palName+'·笔记';
  document.getElementById('note-overlay').classList.add('show');
  document.getElementById('note-modal').style.display='block';
  setTimeout(()=>document.getElementById('note-ta').focus(),50);
}
function closeNoteModal(){
  document.getElementById('note-overlay').classList.remove('show');
  document.getElementById('note-modal').style.display='none';
  _notePalace=null;
}
function saveNote(){
  if(!_notePalace)return;
  const txt=document.getElementById('note-ta').value;
  setPalNote(_notePalace,txt);
  /* 刷新宫格内显示 */
  const bid=bi(_lastData&&_lastData.palaces&&_lastData.palaces.find(p=>p.name===_notePalace)?.branch||'');
  const noteEl=document.getElementById('pnt-'+bid);
  if(noteEl){noteEl.textContent=txt.trim();noteEl.classList.toggle('vis',!!txt.trim());}
  document.querySelectorAll('.pal-note-btn').forEach(b=>{
    if(b.getAttribute('onclick')&&b.getAttribute('onclick').includes(`'${_notePalace}'`)){
      b.classList.toggle('has-note',!!txt.trim());
    }
  });
  closeNoteModal();
}
function delNote(){
  if(!_notePalace)return;
  document.getElementById('note-ta').value='';
  saveNote();
}

function closeStarInfo(){
  document.getElementById('star-overlay').classList.remove('show');
  document.getElementById('star-modal').style.display='none';
}

/* ══════════════════ 五行分布环图 ═══════════════════════════════ */
const WUX_CLR={金:'#d4af37',木:'#4ade80',水:'#60a5fa',火:'#f87171',土:'#fb923c'};
const WUX_ORD=['金','木','水','火','土'];
function buildWuxSVG(palaces){
  const cnt={金:0,木:0,水:0,火:0,土:0};
  for(const p of palaces){
    for(const s of (p.main_stars||[])){
      const info=STAR_INFO[s.name];
      if(info)info.wux.replace(/[\/、·]/g,',').split(',').forEach(w=>{w=w.trim();if(cnt[w]!==undefined)cnt[w]++;});
    }
    for(const ax of (p.aux_stars||[])){
      const info=STAR_INFO[ax];
      if(info)info.wux.replace(/[\/、·]/g,',').split(',').forEach(w=>{w=w.trim();if(cnt[w]!==undefined)cnt[w]++;});
    }
  }
  const total=WUX_ORD.reduce((s,k)=>s+cnt[k],0)||1;
  const cx=68,cy=64,Ro=50,Ri=28;
  let svg='';
  let a=-Math.PI/2;
  for(const k of WUX_ORD){
    const ratio=cnt[k]/total;
    const sw=ratio*Math.PI*2;
    if(ratio<0.001){a+=sw;continue;}
    const la=sw>Math.PI?1:0;
    const x1=cx+Ro*Math.cos(a),      y1=cy+Ro*Math.sin(a);
    const x2=cx+Ro*Math.cos(a+sw),   y2=cy+Ro*Math.sin(a+sw);
    const x3=cx+Ri*Math.cos(a+sw),   y3=cy+Ri*Math.sin(a+sw);
    const x4=cx+Ri*Math.cos(a),       y4=cy+Ri*Math.sin(a);
    const d=`M${x1.toFixed(1)},${y1.toFixed(1)} A${Ro},${Ro} 0 ${la},1 ${x2.toFixed(1)},${y2.toFixed(1)} L${x3.toFixed(1)},${y3.toFixed(1)} A${Ri},${Ri} 0 ${la},0 ${x4.toFixed(1)},${y4.toFixed(1)} Z`;
    svg+=`<path d="${d}" fill="${WUX_CLR[k]}" opacity=".88" stroke="var(--paper)" stroke-width="1.5"/>`;
    if(ratio>0.055){
      const ma=a+sw/2,mr=(Ro+Ri)/2;
      svg+=`<text x="${(cx+mr*Math.cos(ma)).toFixed(1)}" y="${(cy+mr*Math.sin(ma)+3.5).toFixed(1)}" text-anchor="middle" font-size="9.5" fill="#fff" font-weight="bold">${k}</text>`;
    }
    a+=sw;
  }
  /* 图例 */
  let legH='';
  WUX_ORD.forEach((k,i)=>{
    const pct=Math.round(cnt[k]/total*100);
    const lx=130,ly=10+i*20;
    legH+=`<rect x="${lx}" y="${ly}" width="10" height="10" rx="2" fill="${WUX_CLR[k]}"/>`;
    legH+=`<text x="${lx+14}" y="${ly+9}" font-size="10" fill="currentColor">${k}  ${pct}%  (${cnt[k]})</text>`;
  });
  /* 中心文字 */
  svg+=`<text x="${cx}" y="${cy-5}" text-anchor="middle" font-size="9" fill="var(--muted)">五行</text>`;
  svg+=`<text x="${cx}" y="${cy+9}" text-anchor="middle" font-size="8.5" fill="var(--muted)">分布</text>`;
  return `<svg viewBox="0 0 175 130" style="width:100%;max-width:300px;display:block;margin:0 auto;overflow:visible">${svg}${legH}</svg>`;
}

/* ══════════════════ 大运时间轴图 ════════════════════════════ */
function buildDayunSVG(dayun,curY){
  if(!dayun||!dayun.items||!dayun.items.length)return '';
  const items=dayun.items;
  const n=items.length;
  const birthY=items[0].start_year-items[0].start_age;
  const bw=62,bh=44,by=18,gap=3,pw=6;
  const W=pw*2+n*(bw+gap)-gap,H=72;
  let svg='';
  for(let i=0;i<n;i++){
    const d=items[i];
    const isCur=curY>=d.start_year&&curY<d.start_year+10;
    const past=curY>=d.start_year+10;
    const x=pw+i*(bw+gap);
    const fill=isCur?'var(--gold)':past?'var(--border-lt)':'var(--bg)';
    const tf=isCur?'#fff':past?'var(--muted)':'var(--text)';
    const sm=isCur?'var(--accent)':'var(--border)';
    const sw=isCur?2:1;
    svg+=`<rect x="${x}" y="${by}" width="${bw}" height="${bh}" rx="5" fill="${fill}" stroke="${sm}" stroke-width="${sw}"/>`;
    svg+=`<text x="${x+4}" y="${by+11}" font-size="7.5" fill="${isCur?'#fff9':past?'#bbb':'var(--muted)'}">第${d.index}运</text>`;
    svg+=`<text x="${x+bw/2}" y="${by+29}" text-anchor="middle" font-size="13.5" font-weight="${isCur?700:500}" fill="${tf}" letter-spacing="1">${d.ganzhi}</text>`;
    svg+=`<text x="${x+bw/2}" y="${by+41}" text-anchor="middle" font-size="8" fill="${isCur?'#fffd':past?'#bbb':'var(--muted)'}">${d.start_age}–${d.end_age}</text>`;
    if(isCur){
      const prog=Math.min(1,Math.max(0,(curY-d.start_year)/10));
      const mx=(x+prog*bw).toFixed(1);
      svg+=`<line x1="${mx}" y1="${by-8}" x2="${mx}" y2="${by+bh+4}" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="3,2"/>`;
      svg+=`<polygon points="${mx},${by-8} ${(parseFloat(mx)-4).toFixed(1)},${by-15} ${(parseFloat(mx)+4).toFixed(1)},${by-15}" fill="#ef4444"/>`;
      svg+=`<text x="${mx}" y="${by-17}" text-anchor="middle" font-size="8.5" fill="#ef4444" font-weight="700">今</text>`;
    }
  }
  const dir=dayun.forward?'顺':'逆';
  svg+=`<text x="${W-pw}" y="${H}" text-anchor="end" font-size="8" fill="var(--muted)">${dir}行·起运${dayun.start_age}岁</text>`;
  return `<div style="overflow-x:auto;margin-bottom:10px"><svg viewBox="0 0 ${W} ${H}" style="min-width:${Math.min(W,300)}px;width:100%;max-width:${W}px;display:block">${svg}</svg></div>`;
}

/* ══════════════════ 命盘五维雷达图 ══════════════════════════ */
/* 五维评分映射：宫位名 → [0-100]; 利用主星个数 + sihua 化禅/化忌评估 */
const RADAR_DIMS=[
  {label:'命运',pals:['命宫','身宫'],icon:'☆'},
  {label:'财富',pals:['财帛宫','田宅宫'],icon:'元'},
  {label:'事业',pals:['官禄宫','迁移宫'],icon:'印'},
  {label:'感情',pals:['夫妻宫','子女宫'],icon:'♥'},
  {label:'健康',pals:['疾厄宫','福德宫'],icon:'♥︎'},
];
function palScore(p){
  if(!p)return 50;
  let s=50;
  const n=((p.main_stars||[]).length)*8+((p.aux_stars||[]).length)*3;
  s+=Math.min(n,25);
  const tags=p.analysis_tags||[];
  if(tags.some(t=>t.includes('大吉')||t.includes('吉气')))s+=15;
  if(tags.some(t=>t.includes('凶')||t.includes('危')||t.includes('化忌')))s-=15;
  /* 主星化忌 在该宫 重罚 */
  const hasJi=(p.main_stars||[]).some(st=>st.transforms&&st.transforms.includes('化忌'));
  if(hasJi)s-=18;
  return Math.max(10,Math.min(98,Math.round(s)));
}
function buildRadarSVG(palaces){
  if(!palaces||!palaces.length)return'';
  const palMap={};
  for(const p of palaces)palMap[p.name]=p;
  const scores=RADAR_DIMS.map(d=>{
    const ps=d.pals.map(n=>palScore(palMap[n])).filter(v=>v>0);
    return ps.length?Math.round(ps.reduce((a,b)=>a+b,0)/ps.length):50;
  });
  const cx=90,cy=88,R=64,n=5;
  const pts=i=>{const a=-Math.PI/2+i*Math.PI*2/n;return{x:cx+R*Math.cos(a),y:cy+R*Math.sin(a)};};
  const ptsS=(i,r)=>{const a=-Math.PI/2+i*Math.PI*2/n;return{x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)};};
  let svg='';
  /* 背景网格 */
  [0.25,0.5,0.75,1].forEach(f=>{
    const pp=RADAR_DIMS.map((_,i)=>ptsS(i,R*f));
    svg+=`<polygon points="${pp.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}" fill="none" stroke="var(--border-lt)" stroke-width="${f===1?1.2:0.7}"/>`;
  });
  /* 轴线 */
  RADAR_DIMS.forEach((_,i)=>{const p=pts(i);svg+=`<line x1="${cx}" y1="${cy}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" stroke="var(--border-lt)" stroke-width="0.8"/>`; });
  /* 数据多边形 */
  const spts=scores.map((s,i)=>ptsS(i,R*s/100));
  svg+=`<polygon points="${spts.map(p=>`${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}" fill="#b8862a" fill-opacity=".18" stroke="#b8862a" stroke-width="1.8" stroke-linejoin="round"/>`;
  /* 数据点 */
  spts.forEach((p,i)=>{
    const clr=scores[i]>=75?'#16a34a':scores[i]>=50?'#b8862a':'#dc2626';
    svg+=`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.5" fill="${clr}" stroke="var(--paper)" stroke-width="1.2"/>`;
  });
  /* 标签 */
  RADAR_DIMS.forEach((d,i)=>{
    const lp=ptsS(i,R+16);
    svg+=`<text x="${lp.x.toFixed(1)}" y="${lp.y.toFixed(1)}" text-anchor="middle" dominant-baseline="central" font-size="10" font-weight="600" fill="var(--text)">${d.label}</text>`;
    svg+=`<text x="${lp.x.toFixed(1)}" y="${(lp.y+12).toFixed(1)}" text-anchor="middle" font-size="8.5" fill="var(--muted)">${scores[i]}</text>`;
  });
  /* 平均分 */
  const avg=Math.round(scores.reduce((a,b)=>a+b,0)/n);
  svg+=`<text x="${cx}" y="${cy-6}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--gold)">${avg}</text>`;
  svg+=`<text x="${cx}" y="${cy+8}" text-anchor="middle" font-size="8" fill="var(--muted)">综合</text>`;
  const W=180,H=175;
  return `<svg viewBox="0 0 ${W} ${H}" style="width:180px;flex-shrink:0;display:block;overflow:visible">${svg}</svg>`;
}

/* ── 流月吉凶热力方格 (Tab3) ─────────────────────── */
function buildLiuyueGrid(liuyue, lnYear){
  if(!liuyue||!liuyue.length)return'';
  const today=new Date();
  const curM=(lnYear===today.getFullYear())?today.getMonth()+1:-1;
  let ji=0,ping=0,xiong=0;
  const cells=liuyue.map(lm=>{
    let sc=60;
    for(const v of Object.values(lm.sihua||{})){
      if(v==='\u5316\u7984')sc+=18;else if(v==='\u5316\u6743')sc+=10;
      else if(v==='\u5316\u79d1')sc+=5;else if(v==='\u5316\u5fcc')sc-=18;
    }
    sc=Math.max(20,Math.min(95,sc));
    const isCur=lm.month===curM;
    const clr=sc>=72?'#16a34a':sc>=54?'#ca8a04':'#dc2626';
    const lbl=sc>=72?'\u5409':sc>=54?'\u5e73':'\u51f6';
    if(sc>=72)ji++;else if(sc>=54)ping++;else xiong++;
    const siaH=Object.entries(lm.sihua||{}).map(([,v])=>{
      const cls=v==='\u5316\u7984'?'flu':v==='\u5316\u6743'?'fqu':v==='\u5316\u79d1'?'fke':v==='\u5316\u5fcc'?'fji':'';
      return cls?`<span class="fbg ${cls}" style="font-size:.55rem;padding:0 3px">${v.slice(1)}</span>`:''; 
    }).filter(Boolean).join('');
    return `<div class="lmg-cell${isCur?' lmg-cur':''}" style="border-color:${isCur?clr:'var(--border)'};background:${sc>=72?'rgba(22,163,74,.06)':sc>=54?'rgba(202,138,4,.06)':'rgba(220,38,38,.06)'}">`+
      `${isCur?'<span class="lmg-today">今月</span>':''}`+
      `<div><span class="lmg-mno" style="color:${clr}">${lm.month}月</span><span class="lmg-gz">${lm.month_gz}</span></div>`+
      `<div class="lmg-pal">${lm.palace_name}</div>`+
      `<div class="lmg-sia">${siaH||'<span style="color:var(--muted);font-size:.6rem">—</span>'}</div>`+
      `<div class="lmg-lbl" style="color:${clr}">${lbl}</div>`+
      `<div class="lmg-bar" style="width:${sc}%;background:${clr};opacity:.5"></div>`+
      `</div>`;
  });
  return `<div class="lmg-wrap"><div class="lmg-grid">${cells.join('')}</div>`+
    `<div class="lmg-summary"><span class="lmg-ji">吉 ${ji}月</span><span class="lmg-ping">平 ${ping}月</span><span class="lmg-xiong">凶 ${xiong}月</span></div></div>`;
}

/* ── 月度运势概览格 (Tab5) ──────────────────────── */
function buildMonthScoreGrid(monthly, curPeriod){
  if(!monthly||!monthly.length)return'';
  let ji=0,ping=0,xiong=0;
  const cells=monthly.map(m=>{
    const sc=m.score||60;
    const isCur=m.period===curPeriod;
    const clr=sc>=72?'#16a34a':sc>=54?'#ca8a04':'#dc2626';
    const lbl=sc>=72?'\u5409':sc>=54?'\u5e73':'\u51f6';
    if(sc>=72)ji++;else if(sc>=54)ping++;else xiong++;
    const shortP=(m.period||'').replace(/[年月]/g,m=>m==='年'?'/':'').slice(0,5);
    const topEvs=m.events&&m.events.length?m.events.slice(0,2).map(e=>{
      const ecls=e.level==='凶'||e.level==='大凶'?'fji':e.level==='吉'||e.level==='大吉'?'flu':'';
      return ecls?`<span class="fbg ${ecls}" style="font-size:.53rem;padding:0 2px">${e.category.slice(0,2)}</span>`:''
    }).filter(Boolean).join(''):'';
    return `<div class="lmg-cell${isCur?' lmg-cur':''}" style="border-color:${isCur?clr:'var(--border)'};background:${sc>=72?'rgba(22,163,74,.06)':sc>=54?'rgba(202,138,4,.06)':'rgba(220,38,38,.06)'}">`+
      `${isCur?'<span class="lmg-today">今月</span>':''}`+
      `<div><span class="lmg-mno" style="color:${clr}">${shortP}</span></div>`+
      `<div class="lmg-pal">${m.palace_name}</div>`+
      `<div class="lmg-sia">${topEvs||'<span style="color:var(--muted);font-size:.6rem">—</span>'}</div>`+
      `<div class="lmg-lbl" style="color:${clr}">${sc}分 ${lbl}</div>`+
      `<div class="lmg-bar" style="width:${sc}%;background:${clr};opacity:.5"></div>`+
      `</div>`;
  });
  return `<div class="lmg-wrap"><div class="lmg-grid">${cells.join('')}</div>`+
    `<div class="lmg-summary"><span class="lmg-ji">吉月 ${ji}</span><span class="lmg-ping">平月 ${ping}</span><span class="lmg-xiong">凶月 ${xiong}</span></div></div>`;
}

/* ── 飞星四化接收热力宫格图 ──────────────────────────────── */
function buildFlyingHeatmap(flying){
  if(!flying||!flying.palaces||!flying.palaces.length)return'';
  const HUA=['化禄','化权','化科','化忌'];
  const HCLS={化禄:'flu',化权:'fqu',化科:'fke',化忌:'fji'};
  /* 接收映射 */
  const rcvIn={};
  if(flying.received){
    for(const[pal,list]of Object.entries(flying.received))rcvIn[pal]=list||[];
  }
  let h='<div class="fly-hw">';
  h+='<div class="fly-hw-title">飞星四化 · 宫位接收热力图</div>';
  h+='<div class="fly-hw-grid">';
  for(const fp of flying.palaces){
    const pname=fp.palace_name;
    const inList=rcvIn[pname]||[];
    const fo=fp.flying_out||{};
    const hasSelf=fp.self_transforms&&fp.self_transforms.length>0;
    const totalIn=inList.length;
    h+=`<div class="fly-cell${totalIn>0?' fly-active':''}">`;
    h+=`<div class="fly-cn">${pname}</div>`;
    h+=`<div class="fly-cn-stem">${fp.stem_name||''}</div>`;
    /* 接收行 */
    h+='<div class="fly-in-row">';
    let anyIn=false;
    for(const hua of HUA){
      for(const s of inList){
        if(s.includes(hua)){
          anyIn=true;
          h+=`<span class="fbg ${HCLS[hua]}" title="${esc(s)}">${hua.slice(1)}</span>`;
        }
      }
    }
    if(!anyIn)h+='<span class="fbg-none">—</span>';
    h+='</div>';
    /* 飞出行 */
    h+='<div class="fly-out-row">';
    let anyOut=false;
    for(const hua of HUA){
      if(fo[hua]){
        anyOut=true;
        const dest=fo[hua].length>2?fo[hua].slice(0,3):fo[hua];
        h+=`<span class="fob ${HCLS[hua]}" title="飞出${hua}→${fo[hua]}">↗${dest}</span>`;
      }
    }
    if(hasSelf)h+=`<span class="fly-self-tag" title="${esc(fp.self_transforms.join(' '))}">自化</span>`;
    if(!anyOut&&!hasSelf)h+='<span class="fbg-none">—</span>';
    h+='</div>';
    h+='</div>';
  }
  h+='</div>';
  /* 图例 */
  h+='<div class="fly-hw-legend">';
  for(const hua of HUA)h+=`<span class="fbg ${HCLS[hua]}">${hua}</span>`;
  h+='<span style="font-size:.68rem;color:var(--muted);margin-left:4px">上=接收　下=飞出目标</span>';
  h+='</div>';
  h+='</div>';
  return h;
}

/* ════════════════════════════════════════════════════════════
   §3  审核面板  Review Panel
   ════════════════════════════════════════════════════════════ */
let _rvStatus = 'all';   // 当前筛选状态
let _rvData   = [];      // 缓存的列表数据

function openReviewPanel(){
  document.getElementById('review-panel').classList.add('vis');
  rvLoad();
}
function closeReviewPanel(){
  document.getElementById('review-panel').classList.remove('vis');
}
// 点击背景遮罩关闭
document.getElementById('review-panel').addEventListener('click',function(e){
  if(e.target===this)closeReviewPanel();
});

async function rvLoad(){
  const cnt = document.getElementById('review-list-cnt');
  const qp  = _rvStatus==='all' ? '' : `?status=${_rvStatus}`;
  try{
    const r = await fetch(`/api/v1/reviews${qp}`,{
      headers:{'Authorization':'Bearer '+(localStorage.getItem('token')||'')}
    });
    if(r.status===401){rvRenderUnauth();return;}
    if(!r.ok)throw new Error(await r.text());
    const d = await r.json();
    _rvData  = d.items||[];
    document.getElementById('rv-total').textContent = `共 ${d.total} 条`;
    rvRenderTable(_rvData);
  }catch(e){
    document.getElementById('rv-tbody').innerHTML =
      `<tr><td colspan="9" style="color:#ef4444;padding:16px">${e.message}</td></tr>`;
  }
}

function rvRenderUnauth(){
  document.getElementById('rv-tbody').innerHTML =
    `<tr><td colspan="9" style="color:var(--muted);padding:20px;text-align:center">
      请先登录后查看审核列表。当前仍可使用「提交当前命盘」功能。
    </td></tr>`;
  document.getElementById('rv-total').textContent='';
}

function rvRenderTable(rows){
  const empty = document.getElementById('rv-empty');
  const tbody = document.getElementById('rv-tbody');
  if(!rows.length){empty.style.display='block';tbody.innerHTML='';return;}
  empty.style.display='none';
  const statusLabel={pending:'待审',approved:'已通过',rejected:'已拒绝',revised:'修订中'};
  const badgeCls  ={pending:'rv-pending',approved:'rv-approved',rejected:'rv-rejected',revised:'rv-revised'};
  tbody.innerHTML = rows.map(r=>{
    const dt = r.created_at ? r.created_at.replace('T',' ').slice(0,16) : '—';
    const hash = r.report_hash.slice(0,8)+'…';
    const sl   = (r.pattern_summary||'').split(',').slice(0,2).join(', ')||'—';
    return `<tr>
      <td>${r.id}</td>
      <td title="${r.report_hash}">${hash}</td>
      <td>${r.life_palace_gz||'—'}</td>
      <td>${r.wuxing_ju_name||'—'}</td>
      <td title="${r.pattern_summary||''}">${sl}</td>
      <td><span class="rv-badge ${badgeCls[r.status]||''}">${statusLabel[r.status]||r.status}</span></td>
      <td>${r.reviewer||'—'}</td>
      <td>${dt}</td>
      <td class="rv-actions">
        ${r.status==='pending'?`
          <button class="rv-btn rv-approve" onclick="rvAct(${r.id},'approved')">通过</button>
          <button class="rv-btn rv-reject"  onclick="rvAct(${r.id},'rejected')">拒绝</button>
          <button class="rv-btn rv-revise"  onclick="rvAct(${r.id},'revised')">修订</button>
        `:'<span style="color:var(--muted);font-size:.72rem">已处理</span>'}
      </td>
    </tr>`;
  }).join('');
}

async function rvAct(id, status){
  const reviewer = prompt('审核员昵称（可留空）','admin')||'';
  const notes    = status==='rejected'
    ? (prompt('拒绝原因（可留空）','')||'')
    : '';
  try{
    const body={status, reviewer, notes, reject_reason: status==='rejected'?notes:''};
    const r = await fetch(`/api/v1/reviews/${id}`,{
      method:'PATCH',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+(localStorage.getItem('token')||'')},
      body:JSON.stringify(body)
    });
    if(!r.ok)throw new Error(await r.text());
    rvLoad();
  }catch(e){alert('操作失败：'+e.message);}
}

async function rvSubmitCurrent(){
  if(!_lastData){alert('请先排盘后再提交。');return;}
  /* 构建输入快照 */
  const snap={
    year:  document.getElementById('fy').value,
    month: document.getElementById('fm').value,
    day:   document.getElementById('fd').value,
    hour:  document.getElementById('fh').value,
    minute:document.getElementById('fmin')?.value||'0',
    gender:document.getElementById('fgender').value,
    longitude: document.getElementById('flo')?.value||null,
    liunian_year: document.getElementById('fln')?.value||null,
  };
  /* 生成 SHA-256 哈希（用 SubtleCrypto） */
  const enc  = new TextEncoder();
  const hash = await crypto.subtle.digest('SHA-256', enc.encode(JSON.stringify(snap)));
  const hex  = Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
  const body={
    report_hash: hex,
    birth_info:  JSON.stringify(snap),
    life_palace_gz:  _lastData.life_palace_gz||'',
    wuxing_ju_name:  _lastData.wuxing_ju_name||'',
    pattern_summary: (_lastData.patterns||[]).map(p=>p.name||p).slice(0,10).join(','),
    template_version:'standard',
  };
  try{
    const r = await fetch('/api/v1/reviews',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    if(!r.ok)throw new Error(await r.text());
    const d=await r.json();
    alert(`✅ 提交成功！审核 ID：${d.id}，状态：${d.status}`);
    rvLoad(); // 刷新列表
  }catch(e){alert('提交失败：'+e.message);}
}

function rvFilter(btn, status){
  _rvStatus=status;
  document.querySelectorAll('.rv-filter-btn').forEach(b=>b.classList.remove('act'));
  btn.classList.add('act');
  rvLoad();
}

/* ════════════════════════════════════════════════════════════
   §6  批量排盘  Batch Ziwei
   ════════════════════════════════════════════════════════════ */
let _batchFile = null;

function openBatchPanel(){
  document.getElementById('batch-panel').classList.add('vis');
}
function closeBatchPanel(){
  document.getElementById('batch-panel').classList.remove('vis');
}
document.getElementById('batch-panel').addEventListener('click',function(e){
  if(e.target===this)closeBatchPanel();
});

function batchFileSelected(input, file){
  const f = file || (input && input.files && input.files[0]);
  if(!f)return;
  _batchFile = f;
  document.getElementById('batch-drop-label').textContent = '✅ 已选择：'+f.name+' ('+Math.round(f.size/1024)+' KB)';
  document.getElementById('batch-run-btn').disabled = false;
  document.getElementById('batch-status').textContent = '准备就绪，点击「开始批量排盘」';
  document.getElementById('batch-result-area').innerHTML = '';
  document.getElementById('batch-progress-area').innerHTML = '';
}

function batchDownloadSample(){
  const csv = 'name,year,month,day,hour,minute,gender,liunian_year\n' +
    '张三,1990,5,20,8,30,男,2026\n' +
    '李四,1985,9,15,14,0,女,2026\n' +
    '王五,2000,1,1,0,0,男,\n';
  const blob = new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'ziwei_batch_sample.csv';
  document.body.appendChild(a); a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);document.body.removeChild(a);},1000);
}

async function runBatch(){
  if(!_batchFile){alert('请先选择 CSV 文件。');return;}
  const btn = document.getElementById('batch-run-btn');
  const statusEl = document.getElementById('batch-status');
  const progressArea = document.getElementById('batch-progress-area');
  const resultArea = document.getElementById('batch-result-area');

  btn.disabled = true;
  statusEl.textContent = '上传并计算中，请稍候…';
  progressArea.innerHTML = '<div style="font-size:.8rem;color:var(--muted);padding:6px 0">⏳ 服务器正在逐行排盘（视行数可能需要数十秒）…</div>';
  resultArea.innerHTML = '';

  const fd = new FormData();
  fd.append('file', _batchFile);

  try{
    const r = await fetch('/api/v1/ziwei/batch', {method:'POST', body: fd});
    if(!r.ok){
      const err = await r.json().catch(()=>({detail:r.statusText}));
      throw new Error(err.detail || r.statusText);
    }
    /* 下载 ZIP */
    const blob = await r.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const dt   = new Date().toISOString().slice(0,10).replace(/-/g,'');
    a.href = url; a.download = `ziwei_batch_${dt}.zip`;
    document.body.appendChild(a); a.click();
    setTimeout(()=>{URL.revokeObjectURL(url);document.body.removeChild(a);},1500);

    progressArea.innerHTML = '';
    statusEl.textContent = '✅ 批量排盘完成，ZIP 已下载';
    resultArea.innerHTML = `
      <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:6px;padding:10px 14px;font-size:.82rem;color:#15803d">
        🎉 ZIP 包已下载到本地！<br>
        包含：每人一个 JSON 命盘文件 + <code>_summary.csv</code>（汇总概览）。
      </div>`;
  }catch(e){
    progressArea.innerHTML = '';
    statusEl.textContent = '❌ 失败：'+e.message;
    resultArea.innerHTML = `<div style="color:#dc2626;font-size:.8rem;padding:6px">${e.message}</div>`;
  }finally{
    btn.disabled = false;
  }
}

/* ════════════════════════════════════════════════════════════
   §5  快速模拟对比  Quick Simulation Compare
   ════════════════════════════════════════════════════════════ */

function openSimPanel(){
  if(!_lastData){alert('请先排盘，再使用对比模拟。');return;}
  /* 用当前排盘参数预填 */
  document.getElementById('sim-fy').value   = document.getElementById('fy').value;
  document.getElementById('sim-fm').value   = document.getElementById('fm').value;
  document.getElementById('sim-fd').value   = document.getElementById('fd').value;
  document.getElementById('sim-fh').value   = document.getElementById('fh').value;
  document.getElementById('sim-fmin').value = document.getElementById('fmin').value||'0';
  document.getElementById('sim-fgender').value = document.getElementById('fgender').value;
  document.getElementById('sim-fln').value  = document.getElementById('fln').value||'';
  document.getElementById('sim-flo').value  = document.getElementById('flo').value||'';
  document.getElementById('sim-result-area').innerHTML = '';
  document.getElementById('sim-status').textContent = '调整任意参数后点击「开始对比」';
  document.getElementById('sim-panel').classList.add('vis');
}

function closeSimPanel(){
  document.getElementById('sim-panel').classList.remove('vis');
}
document.getElementById('sim-panel').addEventListener('click',function(e){
  if(e.target===this)closeSimPanel();
});

async function runSim(){
  if(!_lastData){alert('请先排盘。');return;}
  const statusEl = document.getElementById('sim-status');
  statusEl.textContent = '计算中…';
  document.getElementById('sim-result-area').innerHTML =
    '<div class="sim-loading">⏳ 对比命盘生成中，请稍候…</div>';

  const simBody={
    year:+document.getElementById('sim-fy').value,
    month:+document.getElementById('sim-fm').value,
    day:+document.getElementById('sim-fd').value,
    hour:+document.getElementById('sim-fh').value,
    minute:+document.getElementById('sim-fmin').value||0,
    gender:document.getElementById('sim-fgender').value,
  };
  const ln=document.getElementById('sim-fln').value; if(ln)simBody.liunian_year=+ln;
  const lo=document.getElementById('sim-flo').value; if(lo)simBody.longitude=+lo;

  try{
    const r = await fetch('/api/v1/ziwei/full',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(simBody)
    });
    if(!r.ok){const e=await r.json();throw new Error(e.detail||r.statusText);}
    const simData = await r.json();
    statusEl.textContent = '✅ 对比完成';
    document.getElementById('sim-result-area').innerHTML = buildSimDiff(_lastData, simData);
  }catch(e){
    statusEl.textContent = '❌ '+e.message;
    document.getElementById('sim-result-area').innerHTML = '';
  }
}

function buildSimDiff(orig, sim){
  const e=s=>String(s||'—').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const dc=(a,b)=>a===b?'diff-same':'diff-changed';

  /* 关键字段对比 */
  const fields=[
    ['命宫干支','life_palace_gz'],
    ['身宫干支','body_palace_gz'],
    ['五行局','wuxing_ju_name'],
    ['命主','life_ruler_star'],
    ['身主','body_ruler_star'],
  ];
  let rows=fields.map(([lbl,key])=>{
    const a=orig[key]||'—', b=sim[key]||'—';
    return `<tr>
      <td>${e(lbl)}</td>
      <td>${e(a)}</td>
      <td class="${dc(a,b)}">${e(b)}</td>
    </tr>`;
  }).join('');

  /* 格局差异 */
  const origPats = new Set((orig.patterns||[]).map(p=>p.name));
  const simPats  = new Set((sim.patterns||[]).map(p=>p.name));
  const added    = [...simPats].filter(n=>!origPats.has(n));
  const removed  = [...origPats].filter(n=>!simPats.has(n));
  const common   = [...origPats].filter(n=>simPats.has(n));

  let patDiff = '';
  if(added.length){
    patDiff += added.map(n=>`<span class="diff-add">+${e(n)}</span>`).join(' ');
  }
  if(removed.length){
    if(patDiff)patDiff+=' ';
    patDiff += removed.map(n=>`<span class="diff-remove">${e(n)}</span>`).join(' ');
  }
  if(common.length && !added.length && !removed.length){
    patDiff = `<span class="diff-same">无变化（${common.length} 个格局）</span>`;
  }
  if(!orig.patterns?.length && !sim.patterns?.length){
    patDiff = '<span class="diff-same">两版均无格局</span>';
  }
  rows += `<tr><td>格局变化</td><td>${[...origPats].slice(0,4).map(e).join('、')||'无'}</td><td>${patDiff||'<span class="diff-same">无变化</span>'}</td></tr>`;

  /* 摘要对比（前 60 字） */
  const os=(orig.summary||'').slice(0,60)+'…';
  const ss=(sim.summary||'').slice(0,60)+'…';
  rows += `<tr><td>摘要（前60字）</td><td style="font-size:.74rem">${e(os)}</td><td class="${dc(os,ss)}" style="font-size:.74rem">${e(ss)}</td></tr>`;

  /* 原版参数摘要 */
  const origParams=`${orig.birth_solar||''}·${orig.gender||''}`;
  const simParams =`${sim.birth_solar||''}·${sim.gender||''}`;

  return `
    <div class="sim-result">
      <div class="sim-result-title">📊 对比结果</div>
      <table class="diff-table">
        <thead><tr>
          <th>比较项</th>
          <th>原始命盘<br><small style="font-weight:400;color:var(--muted)">${e(origParams)}</small></th>
          <th>模拟命盘<br><small style="font-weight:400;color:var(--muted)">${e(simParams)}</small></th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="margin-top:10px;font-size:.72rem;color:var(--muted)">
        ⚠️ 本功能为参考性探索，请勿作为决策依据。
        <button class="btn-sm" style="margin-left:12px;font-size:.72rem" onclick="applySimResult()">📥 应用模拟参数（替换当前命盘）</button>
      </div>
    </div>`;
}

function applySimResult(){
  if(!confirm('确定将模拟参数替换当前命盘并重新排盘？'))return;
  document.getElementById('fy').value    = document.getElementById('sim-fy').value;
  document.getElementById('fm').value    = document.getElementById('sim-fm').value;
  document.getElementById('fd').value    = document.getElementById('sim-fd').value;
  document.getElementById('fh').value    = document.getElementById('sim-fh').value;
  document.getElementById('fmin').value  = document.getElementById('sim-fmin').value;
  document.getElementById('fgender').value = document.getElementById('sim-fgender').value;
  const ln=document.getElementById('sim-fln').value;
  if(ln)document.getElementById('fln').value=ln;
  const lo=document.getElementById('sim-flo').value;
  if(lo)document.getElementById('flo').value=lo;
  closeSimPanel();
  go();
}
