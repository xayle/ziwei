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
let _rvSelected = new Set(); // 当前选中的 ID 集合
let _rvSearchQ  = '';    // 当前搜索关键词

