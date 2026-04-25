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
