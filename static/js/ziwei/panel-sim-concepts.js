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

async function runSim(){
  if(!_lastData){alert('请先排盘。');return;}
  const statusEl = document.getElementById('sim-status');

  // 前端校验：必填字段不能为空或 0
  const simFy = +document.getElementById('sim-fy').value;
  const simFm = +document.getElementById('sim-fm').value;
  const simFd = +document.getElementById('sim-fd').value;
  const simFh = +document.getElementById('sim-fh').value;
  if (!simFy || simFy < 1900 || simFy > 2100) { statusEl.textContent = '⚠ 请填写合法年份（1900-2100）'; return; }
  if (!simFm || simFm < 1 || simFm > 12)       { statusEl.textContent = '⚠ 请填写月份（1-12）'; return; }
  if (!simFd || simFd < 1 || simFd > 31)        { statusEl.textContent = '⚠ 请填写日期（1-31）'; return; }
  if (isNaN(simFh) || simFh < 0 || simFh > 23)  { statusEl.textContent = '⚠ 请填写出生时（0-23）'; return; }

  statusEl.textContent = '计算中…';
  document.getElementById('sim-result-area').innerHTML =
    '<div class="sim-loading">⏳ 对比命盘生成中，请稍候…</div>';

  const simBody={
    year: simFy,
    month: simFm,
    day: simFd,
    hour: simFh,
    minute:+document.getElementById('sim-fmin').value||0,
    gender:document.getElementById('sim-fgender').value,
  };
  const ln=document.getElementById('sim-fln').value; if(ln)simBody.liunian_year=+ln;
  const lo=document.getElementById('sim-flo').value; if(lo)simBody.longitude=+lo;
  simBody.template_version='standard';  // 模拟对比固定用标准版以保证字段完整

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

/* ══════════════════ 概念文档面板（Sprint 5/6 C3）══════════════════════════════ */
function openConceptsPanel(){
  document.getElementById('concepts-panel').classList.add('open');
  document.getElementById('concepts-overlay').classList.add('show');
}
function closeConceptsPanel(){
  document.getElementById('concepts-panel').classList.remove('open');
  document.getElementById('concepts-overlay').classList.remove('show');
}

/* ══════════════ LLM 面板 Tab 切换 ══════════════════════════════════════════ */
function switchLlmTab(tab, btn){
  // 更新按钮样式
  document.querySelectorAll('.llm-tab').forEach(b=>b.classList.remove('act'));
  btn.classList.add('act');
  // 切换内容区
  document.getElementById('llm-tab-ziwei').style.display  = tab==='ziwei'  ? '' : 'none';
  document.getElementById('llm-tab-module').style.display = tab==='module' ? '' : 'none';
}
