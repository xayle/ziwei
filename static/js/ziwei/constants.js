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
