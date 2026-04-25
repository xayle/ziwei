function exportJSON(){
  if(!_lastData){alert('请先排盘后再导出。');return;}
  const payload={
    exported_at: new Date().toISOString(),
    engine_version: _lastData.engine_version||'2.1.0',
    algorithm_version: _lastData.algorithm_version||'2.1.0',
    template_version: _lastData.template_version||'standard',
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

/* ── PNG 截图导出 ─────────────────────────────────────── */
async function exportPNG(){
  const el = document.getElementById('cr');
  if(!el || el.classList.contains('hid')){
    showToast('请先排盘后再导出图片','warn'); return;
  }
  if(typeof html2canvas === 'undefined'){
    showToast('截图库未加载（需联网），可用"🖨 打印"另存 PDF 替代','error'); return;
  }
  showToast('正在生成高清命盘图片…','ok');
  try{
    const canvas = await html2canvas(el,{
      backgroundColor:'#fdf9f3',
      scale:2,
      useCORS:true,
      logging:false,
      removeContainer:true,
    });
    const link = document.createElement('a');
    const hdr  = document.getElementById('ih');
    const tag  = (hdr ? hdr.textContent.trim().slice(0,12) : 'chart').replace(/[\/:*?"<>|]/g,'_');
    const dt   = new Date().toISOString().slice(0,10).replace(/-/g,'');
    link.download = `命盘_${tag}_${dt}.png`;
    link.href = canvas.toDataURL('image/png');
    document.body.appendChild(link);
    link.click();
    setTimeout(()=>document.body.removeChild(link),1000);
    showToast('命盘图片已导出 ✓','ok');
  }catch(e){
    showToast('截图失败：'+e.message,'error');
  }
}

/* ── 保存命盘到案例库 ─────────────────────────────────────── */

/**
 * saveChart(silent)
 * 将当前排盘保存为 Case + Snapshot，并自动索引相似盘。
 * silent=true 时不弹 Toast（供其他操作静默触发）。
 * 需要登录（Bearer token）。
 */
async function saveChart(silent = false) {
  if (!_lastData) { if (!silent) showToast('请先排盘后再保存', 'warn'); return; }
  const tok = localStorage.getItem('ziwei_token') || localStorage.getItem('token') || '';
  if (!tok) { if (!silent) showToast('请先登录后再保存命盘', 'warn'); return; }
  const headers = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok };

  const d = _lastData;
  const yr  = +document.getElementById('fy').value   || d.birth_year || 1990;
  const mo  = +document.getElementById('fm').value   || 1;
  const dy  = +document.getElementById('fd').value   || 1;
  const hr  = +document.getElementById('fh').value;
  const mn  = +(document.getElementById('fmin').value || 0);
  const gRaw= document.getElementById('fgender').value || '女';
  const lo  = +(document.getElementById('flo').value  || 120.0);
  // gRaw → 'male'/'female' for CaseCreate
  const genderApi = gRaw === '女' || gRaw === 'female' ? 'female' : 'male';
  const birth_dt_local = `${yr}-${String(mo).padStart(2,'0')}-${String(dy).padStart(2,'0')}T${String(hr).padStart(2,'0')}:${String(mn).padStart(2,'0')}`;
  const caseName = `${yr}年${mo}月${dy}日 ${hr}时 ${gRaw} | ${d.wuxing_ju_name || ''}`;

  try {
    // Step 1: 尝试复用已保存的 Case（同一次排盘会话内）
    let caseId = window._lastCaseId;

    if (!caseId) {
      // 创建 Case
      const caseResp = await fetch('/api/v1/cases', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          name: caseName,
          gender: genderApi,
          birth_dt_local,
          tz: 'Asia/Shanghai',
          lon: lo,
          solar_time_enabled: !!(document.getElementById('fsolar')?.checked),
        })
      });
      if (!caseResp.ok) {
        const err = await caseResp.json().catch(() => ({}));
        throw new Error(err.detail || `创建案例失败 (${caseResp.status})`);
      }
      const caseData = await caseResp.json();
      caseId = caseData.id;
      window._lastCaseId = caseId;   // 导出面板使用
    }

    // Step 2: 创建 Snapshot
    const snapBody = {
      kind: 'ziwei',
      input_json: {
        year: yr, month: mo, day: dy, hour: hr, minute: mn,
        gender: gRaw, longitude: lo,
        liunian_year: +(document.getElementById('fln').value || 0) || null,
        template_version: currentTpl,
      },
      output_json: d,
      api_version: d.algorithm_version || null,
    };
    const snapResp = await fetch(`/api/v1/cases/${caseId}/snapshots`, {
      method: 'POST',
      headers,
      body: JSON.stringify(snapBody),
    });
    if (!snapResp.ok) {
      const err = await snapResp.json().catch(() => ({}));
      throw new Error(err.detail || `保存快照失败 (${snapResp.status})`);
    }

    // Step 3: 自动索引到相似盘（静默，失败不影响主流程）
    try {
      const pats = (d.patterns || []).map(p => ({ name: p.name, level: p.level }));
      await fetch('/api/v1/similarity/index', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          chart_hash: d.report_hash || (yr+'+'+mo+'+'+dy+'+'+hr+'+'+gRaw),
          birth_solar: d.birth_solar || `${yr}-${String(mo).padStart(2,'0')}-${String(dy).padStart(2,'0')}`,
          birth_year: yr, birth_month: mo, birth_day: dy, birth_hour: hr,
          gender: gRaw,
          wuxing_ju_name: d.wuxing_ju_name || '',
          life_palace_gz: d.life_palace_gz || '',
          patterns: pats,
          source_label: 'user',
        })
      });
    } catch (_) {}

    // Step 4: 更新 UI 状态
    const btn = document.getElementById('save-chart-btn');
    if (btn) { btn.textContent = '✅ 已保存'; btn.style.color = '#16a34a'; }
    if (!silent) showToast(`已保存到案例库 ✓（ID: ${caseId.slice(0,8)}…）`, 'ok');
  } catch (e) {
    if (!silent) showToast('保存失败：' + e.message, 'error');
  }
}

/* ════════════════════════════════════════════════════════════
   §17  案例库浏览面板  Cases Browser
   ════════════════════════════════════════════════════════════ */

let _casesOffset = 0;
const _casesLimit = 15;
let _casesTotal   = 0;
let _casesSearchQ = '';
let _casesSTimer  = null;

function openCasesPanel() {
  document.getElementById('cases-panel').classList.add('vis');
  casesLoad(0);
}

function closeCasesPanel() {
  document.getElementById('cases-panel').classList.remove('vis');
}

function _casesSearchTimer() {
  if (_casesSTimer) clearTimeout(_casesSTimer);
  _casesSTimer = setTimeout(() => {
    _casesSearchQ = (document.getElementById('cases-search').value || '').trim();
    casesLoad(0);
  }, 300);
}

function casesPage(dir) {
  const newOff = _casesOffset + dir * _casesLimit;
  if (newOff < 0 || newOff >= _casesTotal) return;
  casesLoad(newOff);
}

async function casesLoad(offset = 0) {
  _casesOffset = offset;
  const tok = localStorage.getItem('ziwei_token') || localStorage.getItem('token') || '';
  const body = document.getElementById('cases-body');
  if (!body) return;
  body.innerHTML = '<div class="cases-empty">加载中…</div>';

  try {
    const sortEl = document.getElementById('cases-sort');
    const orderBy = sortEl ? sortEl.value : 'updated_at';
    const params = new URLSearchParams({ limit: _casesLimit, offset, order: orderBy, dir: 'desc' });
    if (_casesSearchQ) params.set('q', _casesSearchQ);
    const r = await fetch('/api/v1/cases?' + params, {
      headers: tok ? { Authorization: 'Bearer ' + tok } : {}
    });
    if (!r.ok) {
      if (r.status === 401 || r.status === 403) {
        body.innerHTML = '<div class="cases-empty">请先登录后查看案例库</div>';
        return;
      }
      throw new Error('HTTP ' + r.status);
    }
    const data = await r.json();
    _casesTotal = data.total || 0;

    const countEl = document.getElementById('cases-count');
    if (countEl) countEl.textContent = `共 ${_casesTotal} 条`;
    const totalEl = document.getElementById('cases-total-info');
    if (totalEl) {
      const from = _casesTotal ? offset + 1 : 0;
      const to   = Math.min(offset + _casesLimit, _casesTotal);
      totalEl.textContent = _casesTotal ? `第 ${from}–${to} 条` : '';
    }
    const prevBtn = document.getElementById('cases-prev-btn');
    const nextBtn = document.getElementById('cases-next-btn');
    const pgInfo  = document.getElementById('cases-page-info');
    if (prevBtn) prevBtn.disabled = offset <= 0;
    if (nextBtn) nextBtn.disabled = offset + _casesLimit >= _casesTotal;
    if (pgInfo)  pgInfo.textContent = _casesTotal ? `第 ${Math.floor(offset / _casesLimit) + 1} 页` : '—';

    if (!data.items || !data.items.length) {
      body.innerHTML = '<div class="cases-empty">暂无案例' + (_casesSearchQ ? '（搜索无结果）' : '') + '</div>';
      return;
    }

    const gMap = { male: '男', female: '女' };
    let h = `<table class="cases-table"><thead><tr>
      <th>姓名 / 标识</th><th>性别</th><th>出生时间</th><th>最近更新</th><th>标签</th><th>操作</th>
    </tr></thead><tbody>`;
    for (const c of data.items) {
      const bdt  = (c.birth_dt_local || '').slice(0, 16).replace('T', ' ');
      const upd  = (c.last_snapshot_at || c.updated_at || '').slice(0, 16).replace('T', ' ');
      const tags = Array.isArray(c.tags) && c.tags.length
        ? c.tags.map(t => `<span class="cases-tag">${t}</span>`).join('')
        : '<span style="color:var(--muted);font-size:.7rem">—</span>';
      const safeName = (c.name || '').replace(/'/g, '\\\'');
      h += `<tr class="cases-row" onclick="casesLoadChart('${c.id}','${safeName}')" title="点击载入此命盘">
        <td style="font-weight:500;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.name}</td>
        <td>${gMap[c.gender] || c.gender || '—'}</td>
        <td style="white-space:nowrap;font-size:.76rem">${bdt}</td>
        <td style="white-space:nowrap;font-size:.72rem;color:var(--muted)">${upd || '—'}</td>
        <td>${tags}</td>
        <td style="white-space:nowrap">
          <button class="cases-load-btn" onclick="event.stopPropagation();casesLoadChart('${c.id}','${safeName}')">载入</button>
          <button class="cases-del-btn"  onclick="event.stopPropagation();casesDelete('${c.id}','${safeName}')" title="删除此案例">🗑</button>
        </td>
      </tr>`;
    }
    h += '</tbody></table>';
    body.innerHTML = h;
  } catch (e) {
    body.innerHTML = `<div class="cases-empty" style="color:#dc2626">加载失败：${e.message}</div>`;
  }
}

async function casesLoadChart(caseId, caseName) {
  const tok = localStorage.getItem('ziwei_token') || localStorage.getItem('token') || '';
  const headers = tok ? { Authorization: 'Bearer ' + tok } : {};
  showToast(`正在载入「${caseName}」…`, 'ok');
  try {
    // 获取该案例最新快照（按创建时间降序取第一条）
    const snapsResp = await fetch(`/api/v1/cases/${caseId}/snapshots?limit=1&offset=0`, { headers });
    if (!snapsResp.ok) throw new Error('获取快照失败 ' + snapsResp.status);
    const snaps = await snapsResp.json();
    if (!snaps || !snaps.length) {
      showToast('该案例尚无快照数据，请先重新排盘并保存', 'warn'); return;
    }
    const snap = snaps[0];
    if (!snap.output_json) { showToast('快照数据为空', 'warn'); return; }

    const outData = snap.output_json;
    const inp     = snap.input_json  || {};

    // 填充表单输入字段
    const setVal = (id, v) => { const el = document.getElementById(id); if (el && v !== undefined && v !== null) el.value = v; };
    setVal('fy',     inp.year);
    setVal('fm',     inp.month);
    setVal('fd',     inp.day);
    setVal('fh',     inp.hour);
    setVal('fmin',   inp.minute !== undefined ? inp.minute : 0);
    if (inp.gender)    { const gel = document.getElementById('fgender'); if (gel) gel.value = inp.gender === 'female' ? '女' : inp.gender === 'male' ? '男' : inp.gender; }
    setVal('flo',    inp.longitude);
    if (inp.liunian_year) setVal('fln', inp.liunian_year);
    if (inp.template_version && typeof setTpl === 'function') {
      currentTpl = inp.template_version;
      setTpl(inp.template_version);
    }

    // 渲染命盘
    _lastData = outData;
    window._lastCaseId = caseId;
    if (typeof render === 'function') render(outData);
    if (typeof stClear === 'function') stClear();
    const tbar = document.getElementById('tbar');
    if (tbar) tbar.classList.add('vis');
    const tplGrp = document.getElementById('tpl-grp');
    if (tplGrp) tplGrp.style.display = 'flex';
    const saveBtn = document.getElementById('save-chart-btn');
    if (saveBtn) { saveBtn.textContent = '✅ 已保存'; saveBtn.style.color = '#16a34a'; }

    closeCasesPanel();
    showToast(`已载入「${caseName}」✓`, 'ok');
  } catch (e) {
    showToast('载入失败：' + e.message, 'error');
  }
}

async function casesDelete(caseId, caseName) {
  if (!confirm(`确定删除案例「${caseName}」？此操作不可恢复。`)) return;
  const tok = localStorage.getItem('ziwei_token') || localStorage.getItem('token') || '';
  if (!tok) { showToast('请先登录', 'warn'); return; }
  try {
    const r = await fetch(`/api/v1/cases/${caseId}`, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + tok },
    });
    if (!r.ok && r.status !== 204) throw new Error('HTTP ' + r.status);
    showToast(`已删除「${caseName}」`, 'ok');
    casesLoad(_casesOffset);  // 刷新列表
  } catch (e) {
    showToast('删除失败：' + e.message, 'error');
  }
}

/* ── @media print 时间戳注入 ─────────────────────────────── */
window.addEventListener('beforeprint',()=>{
  const now=new Date().toLocaleString('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
  document.body.setAttribute('data-print-time',now);
  const av=(_lastData&&_lastData.algorithm_version)||'—';
  const tv=(_lastData&&_lastData.template_version)||'standard';
  document.body.setAttribute('data-algo-ver',av);
  document.body.setAttribute('data-tpl-ver',tv);
});

/* ── Tab3 快速跳转 ──────────────────────────────────────── */
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

