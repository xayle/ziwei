function rvFilter(btn, status){
  _rvStatus=status;
  document.querySelectorAll('.rv-filter-btn').forEach(b=>b.classList.remove('act'));
  btn.classList.add('act');
  rvLoad();
}

function rvSearch(val){
  _rvSearchQ = (val||'').trim().toLowerCase();
  rvApplyFilter();
}

function rvApplyFilter(){
  const q = _rvSearchQ;
  const filtered = q
    ? _rvData.filter(r =>
        (r.life_palace_gz||'').includes(q) ||
        (r.wuxing_ju_name||'').includes(q) ||
        (r.reviewer||'').toLowerCase().includes(q) ||
        (r.report_hash||'').toLowerCase().includes(q) ||
        (r.pattern_summary||'').toLowerCase().includes(q) ||
        (r.notes||'').toLowerCase().includes(q)
      )
    : _rvData;
  document.getElementById('rv-total').textContent = q
    ? `共 ${_rvData.length} 条（已筛选 ${filtered.length} 条）`
    : `共 ${_rvData.length} 条`;
  rvRenderTable(filtered);
}

function rvExportCsv(){
  const rows = _rvSearchQ
    ? _rvData.filter(r =>
        (r.life_palace_gz||'').includes(_rvSearchQ) ||
        (r.wuxing_ju_name||'').includes(_rvSearchQ) ||
        (r.reviewer||'').toLowerCase().includes(_rvSearchQ) ||
        (r.report_hash||'').toLowerCase().includes(_rvSearchQ) ||
        (r.pattern_summary||'').toLowerCase().includes(_rvSearchQ) ||
        (r.notes||'').toLowerCase().includes(_rvSearchQ)
      )
    : _rvData;
  if(!rows.length){showToast('无数据可导出','warn');return;}
  const headers=['ID','哈希','命宫','五行局','格局','状态','审核员','批注','拒绝原因','算法版本','模板','修订次数','提交时间','审核时间'];
  const csvRows=[headers.join(',')];
  for(const r of rows){
    const esc=v=>`"${String(v||'').replace(/"/g,'""')}"`;
    csvRows.push([
      r.id, esc(r.report_hash), esc(r.life_palace_gz), esc(r.wuxing_ju_name),
      esc(r.pattern_summary), r.status, esc(r.reviewer), esc(r.notes),
      esc(r.reject_reason), esc(r.algorithm_version), esc(r.template_version),
      r.revision,
      esc((r.created_at||'').replace('T',' ').slice(0,16)),
      esc((r.reviewed_at||'').replace('T',' ').slice(0,16)),
    ].join(','));
  }
  const bom='\ufeff';
  const blob=new Blob([bom+csvRows.join('\n')],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`reviews_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);document.body.removeChild(a);},1000);
  showToast(`已导出 ${rows.length} 条记录 ✓`,'ok');
}

async function rvLoadStats(){
  try{
    const r = await fetch('/api/v1/reviews/stats',{
      headers:{'Authorization':'Bearer '+(localStorage.getItem('token')||'')}
    });
    if(!r.ok)return;
    const s = await r.json();
    document.getElementById('rvs-total').textContent    = s.total    ?? '—';
    document.getElementById('rvs-pending').textContent  = s.pending  ?? '—';
    document.getElementById('rvs-approved').textContent = s.approved ?? '—';
    document.getElementById('rvs-rejected').textContent = s.rejected ?? '—';
    document.getElementById('rvs-revised').textContent  = s.revised  ?? '—';
  }catch(e){}
}

function rvRowCheck(cb){
  const id = +cb.getAttribute('data-id');
  if(cb.checked) _rvSelected.add(id); else _rvSelected.delete(id);
  rvUpdateBulkBar();
}

function rvToggleAll(masterCb){
  document.querySelectorAll('.rv-row-chk').forEach(cb=>{
    cb.checked = masterCb.checked;
    const id = +cb.getAttribute('data-id');
    if(masterCb.checked) _rvSelected.add(id); else _rvSelected.delete(id);
  });
  rvUpdateBulkBar();
}

function rvUpdateBulkBar(){
  const bar = document.getElementById('rv-bulk-bar');
  const cnt = document.getElementById('rv-bulk-count');
  if(_rvSelected.size > 0){
    bar.classList.add('show');
    cnt.textContent = `已选 ${_rvSelected.size} 条`;
  } else {
    bar.classList.remove('show');
  }
  const chkAll = document.getElementById('rv-chk-all');
  if(chkAll){
    const totalVisible = document.querySelectorAll('.rv-row-chk').length;
    chkAll.indeterminate = _rvSelected.size > 0 && _rvSelected.size < totalVisible;
    chkAll.checked = totalVisible > 0 && _rvSelected.size === totalVisible;
  }
}

function rvClearSel(){
  _rvSelected.clear();
  document.querySelectorAll('.rv-row-chk').forEach(cb=>cb.checked=false);
  const chkAll = document.getElementById('rv-chk-all');
  if(chkAll){ chkAll.checked=false; chkAll.indeterminate=false; }
  rvUpdateBulkBar();
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
   §11  相似盘检索  Similar Chart Search
   ════════════════════════════════════════════════════════════ */

function _simChartHash() {
  // 与 LLM 的 _llmChartHash 逻辑一致
  if (!_lastData) return 'no-data';
  const raw = [_lastData.life_palace_gz || '', _lastData.wuxing_ju_name || '', _lastData.birth_info_summary || ''].join('|');
  let h = 0;
  for (let i = 0; i < raw.length; i++) { h = Math.imul(31, h) + raw.charCodeAt(i) | 0; }
  return (h >>> 0).toString(16).padStart(8, '0') + '-' + raw.length.toString(16) + '-ziwei';
}

function openSimSearchPanel() {
  document.getElementById('sim-search-panel').classList.add('vis');
  _simUpdateQuery();
}
function closeSimSearchPanel() {
  document.getElementById('sim-search-panel').classList.remove('vis');
}

function _simUpdateQuery() {
  const box = document.getElementById('sim-query-box');
  if (!_lastData || !_lastData.life_palace_gz) {
    box.textContent = '请先在主界面排盘，再使用相似盘检索。';
    return;
  }
  box.innerHTML = `<b>查询命盘：</b>${_lastData.birth_info_summary||''}　<b>命宫：</b>${_lastData.life_palace_gz||''}　<b>五行局：</b>${_lastData.wuxing_ju_name||''}　<b>格局数：</b>${(_lastData.patterns||[]).length}个`;
}

async function simDoSearch() {
  if (!_lastData || !_lastData.life_palace_gz) { showToast('请先在主界面排盘', 'warn'); return; }
  const statusEl = document.getElementById('sim-status');
  const listEl   = document.getElementById('sim-results-list');
  const badgeEl  = document.getElementById('sim-count-badge');
  statusEl.textContent = '检索中…';
  listEl.innerHTML = '<div class="sim-empty">检索中，请稍候…</div>';

  const hash     = _simChartHash();
  const patterns = JSON.stringify((_lastData.patterns || []).map(p => ({ name: p.name, level: p.level })));
  const qs = new URLSearchParams({
    chart_hash:     hash,
    life_palace_gz: _lastData.life_palace_gz  || '',
    wuxing_ju_name: _lastData.wuxing_ju_name  || '',
    gender:         _lastData.gender          || '',
    birth_year:     String(_lastData.birth_year || 0),
    patterns:       patterns,
    top_k:          '10',
  }).toString();

  try {
    const r = await fetch('/api/v1/similarity/search?' + qs);
    if (!r.ok) { const e = await r.json().catch(() => ({})); statusEl.textContent = '检索失败：' + (e.detail || r.status); return; }
    const data = await r.json();
    badgeEl.textContent = `已索引 ${data.total_indexed} 张命盘`;
    statusEl.textContent = `找到 ${data.results.length} 条相似盘`;
    if (!data.results.length) {
      listEl.innerHTML = '<div class="sim-empty">暂无相似命盘，库中命盘数量不足或当前命盘特征较特殊。<br>点击「将当前命盘入库」可增加索引。</div>';
      return;
    }
    listEl.innerHTML = data.results.map((r, i) => _simCard(r, i)).join('');
  } catch (err) {
    statusEl.textContent = '请求失败：' + err.message;
    listEl.innerHTML = '<div class="sim-empty" style="color:#ef4444">' + err.message + '</div>';
  }
}

function _simCard(r, idx) {
  const sim   = r.similarity;
  const pct   = Math.round(sim * 100);
  const ringCls = pct >= 80 ? 'hi' : pct >= 55 ? 'mid' : 'lo';
  const c = r.case;
  const dateStr = `${c.birth_year}-${String(c.birth_month).padStart(2,'0')}-${String(c.birth_day).padStart(2,'0')} ${String(c.birth_hour).padStart(2,'0')}:00`;
  const src = c.source_label === 'ground_truth' ? '📚 古籍样例' : c.source_label === 'imported' ? '📋 导入' : '👤 用户';
  const pats = c.pattern_summary ? c.pattern_summary.split(',').slice(0,3).join('、') : '无格局';
  return `<div class="sim-card">
    <div class="sim-score-ring ${ringCls}">${pct}%</div>
    <div class="sim-card-info">
      <div class="sim-card-title">${c.life_palace_gz} 命宫 · ${c.wuxing_ju_name} · ${c.gender}命  <span style="font-size:.69rem;color:var(--muted);margin-left:6px">${src}</span></div>
      <div class="sim-card-meta">出生：${dateStr}　hash: <span style="font-family:monospace">${c.chart_hash.slice(0,14)}…</span></div>
      <div class="sim-card-pats">格局：${pats}</div>
    </div>
  </div>`;
}

async function simIndexCurrent() {
  if (!_lastData || !_lastData.life_palace_gz) { showToast('请先在主界面排盘', 'warn'); return; }
  const statusEl = document.getElementById('sim-status');
  statusEl.textContent = '入库中…';
  const hash = _simChartHash();
  const yearStr = (_lastData.birth_solar || '').slice(0, 4);
  const body = {
    chart_hash:     hash,
    birth_solar:    _lastData.birth_solar || '',
    birth_year:     parseInt(yearStr) || 0,
    birth_month:    _lastData.birth_month  || 0,
    birth_day:      _lastData.birth_day    || 0,
    birth_hour:     _lastData.birth_hour   || 0,
    gender:         _lastData.gender       || '',
    wuxing_ju_name: _lastData.wuxing_ju_name || '',
    life_palace_gz: _lastData.life_palace_gz || '',
    patterns:       (_lastData.patterns || []).map(p => ({ name: p.name, level: p.level })),
    source_label:   'user',
  };
  try {
    const tok = localStorage.getItem('ziwei_token');
    const r = await fetch('/api/v1/similarity/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(tok ? { Authorization: 'Bearer ' + tok } : {}) },
      body: JSON.stringify(body),
    });
    if (r.ok) {
      showToast('命盘已成功入库', 'ok');
      statusEl.textContent = '✔ 已入库';
    } else {
      const e = await r.json().catch(() => ({}));
      statusEl.textContent = '入库失败：' + (e.detail || r.status);
    }
  } catch (err) {
    statusEl.textContent = '请求失败：' + err.message;
  }
}

/* ════════════════════════════════════════════════════════════
   §10  LLM AI 辅助解读  LLM-Assisted Interpretation
   ════════════════════════════════════════════════════════════ */

let _llmCurrentDraftId = null;   // 当前生成的草稿 ID（审核用）
let _llmCurrentText    = '';     // 当前草稿文本（复制用）

