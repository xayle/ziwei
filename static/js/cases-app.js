/**
 * cases-app.js
 * cases.html 主逻辑脚本——案例列表加载/筛选/新建/关系计算/Token鉴权
 * 提取自原 cases.html 内联脚本以符合 CSP script-src 'self'
 * 依赖：relation-shared.js（可选，window.RelationShared）
 */
const state = { order:'updated_at', dir:'desc', q:'', tag:'', loading:false, offset:0, limit:20, end:false, selected:new Set() };
const relationShared = window.RelationShared;
const sharedInit = relationShared?.getState?.() || {};
if (Array.isArray(sharedInit.selected)) {
  state.selected = new Set(sharedInit.selected.slice(0, 2));
}
let initialRelationType = sharedInit.relationType || 'couple';
const $ = id => document.getElementById(id);
const queryParams = new URLSearchParams(window.location.search);
const queryToken = queryParams.get('token');
const banner = id => document.getElementById(id);

function getToken(){
  return queryToken
    || localStorage.getItem('access_token')
    || localStorage.getItem('token')
    || sessionStorage.getItem('access_token');
}

function withAuthHeaders(headers={}){
  const token=getToken();
  return token ? { ...headers, Authorization:`Bearer ${token}` } : headers;
}

function authFetch(url, options={}){
  const opts={...options};
  const baseHeaders=options && options.headers ? { ...options.headers } : {};
  opts.headers=withAuthHeaders(baseHeaders);
  return fetch(url, opts).then(async res=>{
    if(res.status===401){
      // token 无效或已过期——清除本地缓存，显示重新输入提示，不继续解析响应
      localStorage.removeItem('access_token');
      sessionStorage.removeItem('access_token');
      const ti=$('tokenInput'); if(ti) ti.value='';
      refreshTokenStatus();
      const box=$('casesBox');
      if(box) box.innerHTML='<div class="empty"><div class="empty-icon">🔒</div><div><div style="font-weight:700;color:var(--text);">Token 无效或已过期</div><div class="muted">请在上方重新粘贴有效 Token 并点击「保存」。</div></div></div>';
      showAuthBanner('Token 已失效，请重新粘贴并保存。', false);
      // 返回一个假 Response 避免调用方 JSON.parse 报错
      return new Response('[]', {status:200, headers:{'Content-Type':'application/json'}});
    }
    return res;
  });
}

function fmtDate(str){ if(!str) return '—'; const d=new Date(str); if(Number.isNaN(d.getTime())) return str; return d.toLocaleString(); }
function levelTag(level){ if(!level) return '<span class="tag">无快照</span>'; const cls=level==='L0'?'ok':level==='L1'?'warn':'bad'; return `<span class="tag ${cls}">${level}</span>`; }
function warnTag(n){ if(n==null) return ''; const cls=n===0?'ok':'warn'; return `<span class="tag ${cls}">告警 ${n}</span>`; }
function diffTag(n){ if(n==null) return ''; const cls=n===0?'ok':'warn'; return `<span class="tag ${cls}">差异 ${n}</span>`; }
function genderLabel(g){ if(g==='female') return '女'; if(g==='male') return '男'; return '未填'; }

function renderCases(list, append=false){
  const box=$('casesBox');
  if(!box) return;
  if(!append) box.innerHTML='';
  if(!list.length && !append){ box.innerHTML=`<div class="empty"><div class="empty-icon">◎</div><div><div style="font-weight:700;color:var(--text);">暂无案例</div><div class="muted">先在左侧填写信息并提交，最新验证摘要会出现在这里。</div></div></div>`; return; }
  const html=list.map(c=>{
    const s=c.latest_verify_summary||null;
    const tags=c.tags?c.tags.split(',').map(t=>t.trim()).filter(Boolean):[];
    const checked = state.selected.has(c.id) ? 'checked' : '';
    const selClass = state.selected.has(c.id) ? ' selected' : '';
    return `<div class="card case-card${selClass}" data-case-id="${c.id}">
      <div class="sel-badge">已选</div>
      <div class="badge">${genderLabel(c.gender)}</div>
      <div class="row" style="justify-content:space-between;gap:10px;align-items:flex-start;">
        <div>
          <div style="font-weight:800;font-size:17px;">${c.name}</div>
          <div class="meta">
            <span>创建 ${fmtDate(c.created_at)}</span>
            <span>更新 ${fmtDate(c.updated_at)}</span>
            ${c.city?`<span>${c.city}</span>`:''}
          </div>
        </div>
        <div class="row" style="gap:6px;">
          ${levelTag(s?.summary_level)}
          ${warnTag(s?.summary_warning_count)}
          ${diffTag(s?.summary_diff_count)}
        </div>
      </div>
      <div class="muted" style="margin:8px 0 6px;">TZ ${c.tz} · 经度 ${c.lon} · 真太阳时 ${c.solar_time_enabled?"开启":"关闭"}</div>
      ${tags.length?`<div class="row">${tags.map(t=>`<span class="pill">${t}</span>`).join('')}</div>`:''}
      <div class="row" style="margin-top:10px;">
        <a class="pill accent" href="/static/case.html?id=${encodeURIComponent(c.id)}">查看快照</a>
        <span class="pill" title="schema">${c.schema_version||'schema?'}</span>
        <span class="pill" title="api">api ${c.api_version_last||'-'}</span>
        <span class="pill" title="rule">rule ${c.rule_version_last||'-'}</span>
        <span class="pill gray" title="case id">${c.id}</span>
        <label class="select-chip"><input type="checkbox" data-case-id="${c.id}" ${checked}/> 选中关系计算</label>
      </div>
    </div>`;
  }).join('');
  box.insertAdjacentHTML('beforeend', html);
  updateCardSelectionUI();
}

function updateMore(){
  const more=$('casesMore'); if(!more) return;
  more.innerHTML='';
  if(state.end) return;
  const btn=document.createElement('button');
  btn.textContent=state.loading?'加载中…':'加载更多案例';
  btn.disabled=state.loading;
  btn.addEventListener('click', ()=>loadCases(false));
  more.appendChild(btn);
}

async function loadCases(reset=false){
  if(state.loading || (state.end && !reset)) return;
  if(reset){ state.offset=0; state.end=false; $('casesBox').innerHTML=''; $('loadedCount').textContent='已加载 0 条'; }
  state.loading=true; $('loadStatus').textContent='加载中…'; updateMore();
  const params=new URLSearchParams({limit:String(state.limit), offset:String(state.offset), order:state.order, dir:state.dir});
  if(state.q) params.set('q', state.q);
  if(state.tag) params.set('tag', state.tag);
  try{
    const res=await authFetch(`/api/v1/cases?${params.toString()}`);
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    const data=await res.json();
    const list=Array.isArray(data)?data:[];
    renderCases(list, true);
    state.offset += list.length;
    if(list.length < state.limit) state.end=true;
    $('loadStatus').textContent=`✓ 已加载 ${state.offset} 条${state.end?'（已到底）':''}`;
    $('loadedCount').textContent=`已加载 ${state.offset} 条${state.end?' · 完成':''}`;
    updateMore();
  }catch(e){
    $('casesBox').innerHTML=`<div class="empty"><div class="empty-icon">!</div><div><div style="font-weight:700;color:#991b1b;">加载失败</div><div class="muted">${e}</div></div></div>`;
    $('loadStatus').textContent='加载失败';
  }finally{ state.loading=false; updateMore(); }
}

function getInput(id){ return ($(id)?.value||'').trim(); }
function fillDemo(){
  $('name').value='示例用户';
  $('gender').value='female';
  $('birth_dt_local').value='2002-03-13T14:36:00';
  $('tz').value='Asia/Shanghai';
  $('lon').value='121.4737';
  $('city').value='上海';
  $('tags').value='演示,回归';
  $('notes').value='示例记录，用于演示接口';
  $('solar').checked=false;
}

async function createCase(){
  const payload={
    name:getInput('name'),
    gender:getInput('gender')||null,
    birth_dt_local:getInput('birth_dt_local'),
    tz:getInput('tz')||'Asia/Shanghai',
    birth_dt:getInput('birth_dt')||null,
    city:getInput('city')||null,
    lon:Number(getInput('lon')),
    solar_time_enabled:$('solar').checked,
    notes:getInput('notes')||null,
    tags:getInput('tags')||null,
  };
  if(!payload.name||!payload.birth_dt_local||!payload.tz||!Number.isFinite(payload.lon)){
    showCreateMsg('必填字段缺失或经度非法'); return;
  }
  try{
    const res=await authFetch('/api/v1/cases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const text=await res.text();
    if(!res.ok) throw new Error(text||res.status);
    showCreateMsg('✓ 创建成功', true);
    loadCases(true);
  }catch(e){ showCreateMsg('创建失败: '+e); }
}

$('btn-create').addEventListener('click', createCase);
$('btn-refresh').addEventListener('click', ()=>loadCases(true));
$('btn-apply').addEventListener('click', ()=>{state.q=getInput('q');state.tag=getInput('tag');state.order=$('order').value;state.dir=$('dir').value;loadCases(true);});
$('btn-clear').addEventListener('click', ()=>{ $('q').value=''; $('tag').value=''; state.q=''; state.tag=''; loadCases(true); });
$('btn-fill-demo').addEventListener('click', fillDemo);
$('btn-save-token').addEventListener('click', ()=>saveTokenFromInput());
$('btn-clear-token').addEventListener('click', ()=>{ localStorage.removeItem('access_token'); $('tokenInput').value=''; showAuthBanner('已清除本地 token，当前依赖本地免登录。', true); refreshTokenStatus(); });

// 关系选择：限制 2 个
function syncSelectedChips(){
  const list=$('selectedList'); if(!list) return;
  if(!state.selected.size){ list.textContent='未选择'; return; }
  list.innerHTML='';
  state.selected.forEach(id=>{
    const chip=document.createElement('span');
    chip.className='pill accent';
    chip.textContent=id;
    list.appendChild(chip);
  });
  list.appendChild(document.createTextNode(`（${state.selected.size}/2）`));
}

function handleSelect(caseId, checked){
  if(checked){
    if(state.selected.size >=2 && !state.selected.has(caseId)) return false;
    state.selected.add(caseId);
  } else {
    state.selected.delete(caseId);
  }
  syncSelectedChips();
  updateCardSelectionUI();
  updateRelationStatus();
  if (relationShared?.setSelection) {
    relationShared.setSelection(Array.from(state.selected), $('relationType')?.value || 'couple');
  }
  return true;
}

function updateCardSelectionUI(){
  document.querySelectorAll('[data-case-id]').forEach(node=>{
    const id=node.getAttribute('data-case-id');
    if(state.selected.has(id)) node.classList.add('selected'); else node.classList.remove('selected');
    const cb=node.querySelector('input[type="checkbox"][data-case-id]');
    if(cb) cb.checked=state.selected.has(id);
  });
}

document.addEventListener('change', (e)=>{
  const target=e.target;
  if(target && target.matches('input[type="checkbox"][data-case-id]')){
    const cid=target.getAttribute('data-case-id');
    const ok=handleSelect(cid, target.checked);
    if(!ok){
      target.checked=false;
      showAuthBanner('最多选择 2 个案例进行关系计算。', false);
    }
  }
});

function updateRelationStatus(){
  const el=$('relationStatus'); if(!el) return;
  if(state.selected.size===2){
    el.textContent='已选 2 个，准备计算';
    el.className='pill ok';
  } else {
    el.textContent='等待选择案例';
    el.className='pill gray';
  }
}

function applyRelationStateFromShared(payload){
  if(!payload) return;
  if(Array.isArray(payload.selected)){
    state.selected = new Set(payload.selected.slice(0, 2));
    syncSelectedChips();
    updateCardSelectionUI();
    updateRelationStatus();
  }
  if(payload.relationType && $('relationType')){
    $('relationType').value = payload.relationType;
  }
  if(payload.lastResult){
    renderRelationResult(payload.lastResult);
  }
}

if (relationShared?.subscribe) {
  relationShared.subscribe((payload) => applyRelationStateFromShared(payload));
}

function renderRelationResult(payload){
  const box=$('relationResult'); if(!box) return;
  if(!payload){ box.innerHTML=''; return; }
  const { case_a, case_b, result } = payload;
  const support = (result.support_points||[]).map(p=>`<span class="pill ok">+ ${p.detail}</span>`).join('');
  const conflict = (result.conflict_points||[]).map(p=>`<span class="pill red">- ${p.detail}</span>`).join('');
  box.innerHTML = `
    <div class="result-box" style="border-color:rgba(34,197,94,.35);">
      <div class="row" style="justify-content:space-between;align-items:center;">
        <div><strong>匹配度</strong> ${result.compatibility_score.toFixed(1)} / 100 · ${result.summary}</div>
        <span class="pill">关系类型: ${result.relation_type}</span>
      </div>
      <div class="muted" style="margin-top:6px;">${result.advice||''}</div>
      <div class="row" style="margin-top:8px; gap:8px; align-items:flex-start;">
        <div style="flex:1;">
          <div class="lbl" style="margin-bottom:4px;">助力</div>
          <div class="chips">${support || '<span class="muted">暂无</span>'}</div>
        </div>
        <div style="flex:1;">
          <div class="lbl" style="margin-bottom:4px;">冲突</div>
          <div class="chips">${conflict || '<span class="muted">暂无</span>'}</div>
        </div>
      </div>
    </div>`;
}

async function computeRelation(){
  if(state.selected.size!==2){ showAuthBanner('请选择 2 个案例再计算。', false); return; }
  const [a,b]=Array.from(state.selected);
  const relationType=$('relationType')?.value||'couple';
  const status=$('relationStatus');
  const btn=$('btn-compute-relation');
  try{
    if(status){ status.textContent='计算中…'; status.className='pill amber'; }
    if(btn){ btn.disabled=true; btn.textContent='计算中…'; }
    renderRelationResult(null);
    const res=await authFetch('/api/v1/relations/compat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ case_a_id:a, case_b_id:b, relation_type:relationType })
    });
    const data=await res.json();
    if(!res.ok) throw new Error(data?.message||res.status);
    renderRelationResult(data);
    relationShared?.setResult(data);
    if(status){ status.textContent='计算完成'; status.className='pill ok'; }
  }catch(e){
    showAuthBanner('计算失败: '+e, false);
    if(status){ status.textContent='计算失败'; status.className='pill red'; }
  }finally{
    if(btn){ btn.disabled=false; btn.textContent='计算关系'; }
  }
}

$('btn-compute-relation').addEventListener('click', computeRelation);

const relationTypeSelect = $('relationType');
if (relationTypeSelect) {
  relationTypeSelect.addEventListener('change', () => {
    relationShared?.setSelection(Array.from(state.selected), relationTypeSelect.value || 'couple');
  });
}

window.addEventListener('DOMContentLoaded', ()=>{
  fillDemo();
  const saved=localStorage.getItem('access_token')||'';
  const ti=$('tokenInput'); if(ti) ti.value=saved;
  if ($('relationType')) $('relationType').value = initialRelationType;
  applyRelationStateFromShared(sharedInit);
  syncSelectedChips();
  updateCardSelectionUI();
  updateRelationStatus();
  refreshTokenStatus();
  // 有 token 才发请求，避免无 token 时产生 401
  if (getToken()) {
    loadCases(true);
  } else {
    const box=$('casesBox');
    if(box) box.innerHTML='<div class="empty"><div class="empty-icon">🔒</div><div><div style="font-weight:700;color:var(--text);">请先填写 Token</div><div class="muted">在上方粘贴 Token 并点击「保存」后即可加载案例列表。</div></div></div>';
  }
});

// 处理来自 verify.html 的 postMessage
window.addEventListener('message', (event) => {
  if (event.type === 'message' && event.data?.type === 'search') {
    const searchInput = $('q');
    if (searchInput) {
      searchInput.value = event.data.keyword || '';
      state.q = event.data.keyword || '';
      loadCases(true);
    }
  }
});

function showAuthBanner(msg, ok=false){
  const el=banner('authBanner'); if(!el) return;
  el.style.display='flex';
  el.className = ok ? 'banner ok' : 'banner';
  el.textContent=msg;
}

function refreshTokenStatus(){
  const t=getToken();
  const el=$('tokenStatus'); if(!el) return;
  const ti=$('tokenInput'); if(ti && t) ti.value=t;
  if(t){ el.textContent='鉴权: 已就绪'; el.className='pill ok'; }
  else { el.textContent='鉴权: 未检测'; el.className='pill amber'; }
}

function saveTokenFromInput(){
  const ti=$('tokenInput'); if(!ti) return;
  const val=(ti.value||'').trim();
  if(!val){ showAuthBanner('未填写 token，如需鉴权请粘贴后再点保存。', false); return; }
  localStorage.setItem('access_token', val);
  showAuthBanner('已保存 token，本页请求将自动携带。', true);
  refreshTokenStatus();
  loadCases(true); // token 保存后立即加载
}

function showCreateMsg(msg, ok=false){
  const el=$('createMsg'); if(!el) return;
  el.textContent=msg;
  el.style.color= ok ? '#166534' : '#991b1b';
}
