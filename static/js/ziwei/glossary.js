
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

/* 词汇表防抖服务端搜索（Sprint 5/6 D6: TF-IDF 全文检索）*/
let _glossDebounceTimer=null;
function filterGlossDebounced(){
  if(_glossDebounceTimer)clearTimeout(_glossDebounceTimer);
  _glossDebounceTimer=setTimeout(async()=>{
    const q=(document.getElementById('gloss-search').value||'').trim();
    if(!q){filterGloss();return;}
    document.getElementById('gloss-cnt').textContent='搜索中…';
    try{
      const r=await fetch('/api/v1/glossary?q='+encodeURIComponent(q));
      if(r.ok){
        const items=await r.json();
        document.getElementById('gloss-cnt').textContent=`共 ${items.length} 条（智能搜索）`;
        document.getElementById('gloss-list').innerHTML=items.map((g,i)=>
          `<div class="gloss-item" id="gi-${i}" onclick="toggleGlossItem(${i})">
            <div><span class="gloss-term">${esc(g.term||'')}</span><span class="gloss-pin">${esc(g.pinyin||'')}</span><span class="gloss-cat-badge">${esc(g.category||'')}</span></div>
            <div class="gloss-detail" id="gd-${i}" style="display:none">
              <div class="gloss-def">${esc(g.definition||'')}</div>
              ${g.classic_source?`<div class="gloss-src">📚 ${esc(g.classic_source)}</div>`:''}
            </div>
          </div>`
        ).join('');
        return;
      }
    }catch(e){}
    filterGloss();
  },300);
}
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
