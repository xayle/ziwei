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
      h+=`<div class="pat-item ${cls}">`;
      h+=`<div class="pat-header"><span class="pat-badge">${esc(pt.level)}</span><span class="pat-name">${esc(pt.name)}</span>${starsStr}</div>`;
      h+=`<div class="pat-desc">${esc(pt.description)}`;
      if(isPro && pt.source) h+=` <span style="font-size:.68rem;color:var(--muted);margin-left:6px">— 出处：${esc(pt.source)}</span>`;
      h+=`</div>`;
      // §20 涉及宫位跳转按钮
      if(pt.palaces&&pt.palaces.length){
        h+=`<div class="pat-jump-pals">`;
        for(const pn of pt.palaces){
          h+=`<button class="pat-jump-btn" onclick="patJumpToPalace('${esc(pn)}')">📍 ${esc(pn)}</button>`;
        }
        h+=`</div>`;
      }
      h+=`</div>`;
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
      if(rd.evidence){
        const _rPal=lsugExtractPalace(rd.evidence);
        const _rJbtn=_rPal?` <button class="lsug-jump-btn" onclick="event.stopPropagation();patJumpToPalace('${_rPal}')">→ 定位${_rPal}</button>`:'';
        h+=`<div class="remedy-evidence">📌 触发依据：${esc(rd.evidence)}${_rJbtn}</div>`;
      }
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
    // §19 偏好设置栏
    const _prefs=lsugGetPrefs();
    h+=`<div class="lsug-prefs-bar">
      <span class="lsug-pref-label">偏好：</span>
      <label class="lsug-pref-check"><input type="checkbox" id="lsug-pref-pets" ${_prefs.has_pets?'checked':''} onchange="lsugSavePrefs()"> 🐾 家中有宠物</label>
      <label class="lsug-pref-check"><input type="checkbox" id="lsug-pref-allergy" ${_prefs.allergy?'checked':''} onchange="lsugSavePrefs()"> 🌸 植物过敏</label>
      <label class="lsug-pref-check"><input type="checkbox" id="lsug-pref-noheavy" ${_prefs.no_heavy?'checked':''} onchange="lsugSavePrefs()"> 🚫 不宜移动大件</label>
      <label class="lsug-pref-check">💰 预算：<select class="lsug-pref-sel" id="lsug-pref-budget" onchange="lsugSavePrefs()">
        <option value="">全部</option>
        <option value="low" ${_prefs.budget==='low'?'selected':''}>仅低花费</option>
        <option value="medium" ${_prefs.budget==='medium'?'selected':''}>低+中</option>
      </select></label>
    </div>`;
    const _lsTotal = data.life_suggestions.length;
    const _lsDone  = Object.values(_lsugState).filter(v=>v==='done').length;
    const _lsWatch = Object.values(_lsugState).filter(v=>v==='watching').length;
    h+=`<div class="lsug-title">🌟 生活化建议<span class="lsug-summary-badge">（${_lsTotal}条 · 已实施${_lsDone} · 关注${_lsWatch} · 传统命理参考）</span><button class="remedy-toggle" onclick="this.closest('.lsug-wrap').querySelector('.lsug-body').classList.toggle('hidden')">折叠 / 展开</button></div>`;
    h+=`<div class="lsug-filter-row">
      <label>花费：</label>
      <select id="lsug-filter-cost" onchange="lsugApplyFilter()">
        <option value="">全部</option>
        <option value="低">低</option><option value="中">中</option><option value="高">高</option>
      </select>
      <label>状态：</label>
      <select id="lsug-filter-state" onchange="lsugApplyFilter()">
        <option value="">全部</option>
        <option value="none">未设置</option>
        <option value="done">已实施</option>
        <option value="watching">关注中</option>
        <option value="ignored">已忽略</option>
      </select>
      <button class="lsug-export-btn" onclick="lsugExport()">📋 导出清单</button>
    </div>`;
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
        const lsid = s.id || (s.category+'_'+s.name.slice(0,8));
        const curState = _lsugState[lsid] || '';
        const stateClass = curState ? 'lsug-' + curState : '';
        h+=`<div class="lsug-item ${stateClass}" data-lsug-id="${lsid}" data-cost="${esc(s.cost_level||'')}" data-cat="${esc(s.category||'')}">`;
        // §19 偏好警告标签
        const _wp=lsugGetPrefs();
        const _pwarns=[];
        if(_wp.has_pets&&s.category==='plants'&&s.notes&&/宠/.test(s.notes))_pwarns.push('🐾 家中有宠物：请确认此植物对宠物安全');
        if(_wp.allergy&&s.category==='plants')_pwarns.push('🌸 植物过敏：请谨慎考虑此建议');
        if(_wp.no_heavy&&s.category==='bed')_pwarns.push('🚫 不宜移动大件：请量力而为');
        if(_wp.budget==='low'&&s.cost_level==='高')_pwarns.push('💰 花费较高，与低预算偏好不符');
        else if(_wp.budget==='medium'&&s.cost_level==='高')_pwarns.push('💰 花费较高，请酌情考虑');
        if(_pwarns.length)h+=_pwarns.map(w=>`<span class="lsug-pref-warn">${w}</span>`).join('');
        h+=`<div class="lsug-header"><span class="lsug-prio ${prioC}" style="border-color:${prioCol};color:${prioCol}">${PRIO_LABEL[s.priority]||'可选'}</span><span class="lsug-name lsug-title-text">${esc(s.name)}</span><span class="lsug-meta">${esc(s.cost_level)} · ${esc(s.valid_scope)}</span></div>`;
        if(s.short_desc)h+=`<div class="lsug-desc">${esc(s.short_desc)}</div>`;
        if(s.evidence){
          const _evPal=lsugExtractPalace(s.evidence);
          const _jbtn=_evPal?` <button class="lsug-jump-btn" onclick="event.stopPropagation();lsugJumpToPalace('${_evPal}')">→ 定位${_evPal}</button>`:'';
          h+=`<div class="lsug-evidence">📌 ${esc(s.evidence)}${_jbtn}</div>`;
        }
        if(s.actions&&s.actions.length){
          h+=`<details class="lsug-actions"><summary>实施步骤</summary><ul>`;
          for(const a of s.actions)h+=`<li>${esc(a)}</li>`;
          h+=`</ul></details>`;
        }
        if(s.notes)h+=`<div class="lsug-notes">📝 ${esc(s.notes)}</div>`;
        h+=`<div class="lsug-disclaimer">⚠️ ${esc(s.disclaimer)}</div>`;
        h+=`<div class="lsug-action-bar">
          <button class="lsug-act-btn done ${curState==='done'?'active':''}" data-action="done" onclick="lsugSetAction('${lsid}','${curState==='done'?'':'done'}')">✅ 已实施</button>
          <button class="lsug-act-btn watching ${curState==='watching'?'active':''}" data-action="watching" onclick="lsugSetAction('${lsid}','${curState==='watching'?'':'watching'}')">👀 关注</button>
          <button class="lsug-act-btn ignored ${curState==='ignored'?'active':''}" data-action="ignored" onclick="lsugSetAction('${lsid}','${curState==='ignored'?'':'ignored'}')">🚫 忽略</button>
        </div>`;
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

