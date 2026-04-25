function openReviewPanel(){
  document.getElementById('review-panel').classList.add('vis');
  rvLoad();
  rvLoadStats();
}
function closeReviewPanel(){
  document.getElementById('review-panel').classList.remove('vis');
}

async function rvLoad(){
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
    _rvSelected = new Set();
    rvUpdateBulkBar();
    _rvSearchQ = document.getElementById('rv-search')?.value?.trim()||'';
    rvApplyFilter();
  }catch(e){
    document.getElementById('rv-tbody').innerHTML =
      `<tr><td colspan="11" style="color:#ef4444;padding:16px">${e.message}</td></tr>`;
  }
}

function rvRenderUnauth(){
  document.getElementById('rv-tbody').innerHTML =
    `<tr><td colspan="11" style="color:var(--muted);padding:20px;text-align:center">
      请先登录后查看审核列表。当前仍可使用「提交当前命盘」功能。
    </td></tr>`;
  document.getElementById('rv-total').textContent='';
}

function rvRenderTable(rows){
  const empty = document.getElementById('rv-empty');
  const tbody = document.getElementById('rv-tbody');
  _rvExpandedId = null;   // 重置展开状态
  if(!rows.length){empty.style.display='block';tbody.innerHTML='';return;}
  empty.style.display='none';
  const statusLabel={pending:'待审',approved:'已通过',rejected:'已拒绝',revised:'修订中'};
  const badgeCls  ={pending:'rv-pending',approved:'rv-approved',rejected:'rv-rejected',revised:'rv-revised'};
  tbody.innerHTML = rows.map(r=>{
    const dt = r.created_at ? r.created_at.replace('T',' ').slice(0,16) : '—';
    const hash = r.report_hash.slice(0,8)+'…';
    const sl   = (r.pattern_summary||'').split(',').slice(0,2).join(', ')||'—';
    const chk  = _rvSelected.has(r.id) ? 'checked' : '';
    const nt   = (r.notes||r.reject_reason||'').trim();
    const ntShort = nt.length > 16 ? nt.slice(0,16)+'…' : (nt||'—');
    const revBadge = (r.revision||1) > 1
      ? ` <span title="已修订${r.revision}次" style="font-size:.6rem;background:#e0e7ff;color:#3730a3;border-radius:8px;padding:1px 5px">v${r.revision}</span>` : '';
    return `<tr style="cursor:pointer" onclick="if(!event.target.closest('input,button'))rvToggleDetail(this,${r.id})">
      <td onclick="event.stopPropagation()"><input type="checkbox" class="rv-sel-cb rv-row-chk" data-id="${r.id}" ${chk} onchange="rvRowCheck(this)"></td>
      <td>${r.id}</td>
      <td title="${r.report_hash}">${hash}</td>
      <td>${r.life_palace_gz||'—'}</td>
      <td>${r.wuxing_ju_name||'—'}</td>
      <td title="${r.pattern_summary||''}">${sl}</td>
      <td><span class="rv-badge ${badgeCls[r.status]||''}">${statusLabel[r.status]||r.status}</span>${revBadge}</td>
      <td>${r.reviewer||'—'}</td>
      <td title="${nt}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.74rem;color:var(--muted)">${ntShort}</td>
      <td>${dt}</td>
      <td class="rv-actions" onclick="event.stopPropagation()">
        ${r.status==='pending'?`
          <button class="rv-btn rv-approve" onclick="rvAct(${r.id},'approved')">通过</button>
          <button class="rv-btn rv-reject"  onclick="rvAct(${r.id},'rejected')">拒绝</button>
          <button class="rv-btn rv-revise"  onclick="rvAct(${r.id},'revised')">修订</button>
        `:'<span style="color:var(--muted);font-size:.72rem">已处理</span>'}
      </td>
    </tr>`;
  }).join('');
}

/* ── 审核详情展开行 ─────────────────────────────────────────── */
let _rvExpandedId = null;

function rvToggleDetail(row, id) {
  const next = row.nextElementSibling;
  if (_rvExpandedId === id && next && next.classList.contains('rv-detail-row')) {
    next.remove();
    row.style.background = '';
    _rvExpandedId = null;
    return;
  }
  // 关闭已展开的其他行
  const existing = document.querySelector('.rv-detail-row');
  if (existing) {
    const prevRow = existing.previousElementSibling;
    if (prevRow) prevRow.style.background = '';
    existing.remove();
  }
  const rec = _rvData.find(r => r.id === id);
  if (!rec) return;
  _rvExpandedId = id;
  row.style.background = 'var(--bg)';

  let birthStr = '—';
  try {
    const bi = JSON.parse(rec.birth_info || '{}');
    const parts = [];
    if (bi.year) {
      const min = bi.minute && bi.minute !== '0' ? `${bi.minute}分` : '';
      parts.push(`${bi.year}年${bi.month||''}月${bi.day||''}日 ${bi.hour||'0'}时${min}`);
    }
    if (bi.gender) parts.push(`性别：${bi.gender}`);
    if (bi.longitude) parts.push(`经度：${Number(bi.longitude).toFixed(2)}`);
    if (bi.liunian_year) parts.push(`流年：${bi.liunian_year}`);
    birthStr = parts.join(' · ') || JSON.stringify(bi);
  } catch(e) { birthStr = rec.birth_info || '—'; }

  const pats = (rec.pattern_summary||'').split(',').filter(Boolean);
  const patHtml = pats.length
    ? pats.map(p=>`<span style="display:inline-block;background:#eff6ff;color:#1e3a5f;border-radius:10px;padding:1px 8px;font-size:.72rem;margin:1px 2px">${p}</span>`).join('')
    : '<span style="color:var(--muted)">—</span>';

  const det = document.createElement('tr');
  det.className = 'rv-detail-row';
  det.innerHTML = `<td colspan="11"><div class="rv-detail-box">
    <div class="rv-detail-grid">
      <div>
        <span class="rv-detail-label">出生信息</span>
        <div style="font-size:.82rem">${birthStr}</div>
        <div style="margin-top:8px;display:flex;gap:14px;flex-wrap:wrap;font-size:.77rem">
          <span><span class="rv-detail-label">算法版本 </span>${rec.algorithm_version||'—'}</span>
          <span><span class="rv-detail-label">模板 </span>${rec.template_version||'—'}</span>
          <span><span class="rv-detail-label">修订次数 </span>${rec.revision||1}</span>
        </div>
        ${rec.reviewed_at?`<div style="margin-top:4px;font-size:.75rem;color:var(--muted)">审核时间：${rec.reviewed_at.replace('T',' ').slice(0,16)}</div>`:''}
      </div>
      <div>
        <span class="rv-detail-label">格局列表</span>
        <div style="margin-top:2px">${patHtml}</div>
        ${rec.reject_reason?`<div style="margin-top:10px"><span class="rv-detail-label">拒绝原因</span><div style="color:#dc2626;font-size:.78rem;margin-top:2px">${rec.reject_reason}</div></div>`:''}
      </div>
    </div>
    <div>
      <span class="rv-detail-label">📝 批注 / 审核说明</span>
      <textarea class="rv-det-edit" id="rv-det-notes-${id}" placeholder="输入批注内容，保存后不改变当前审核状态…">${rec.notes||''}</textarea>
    </div>
    <div style="display:flex;gap:8px;align-items:center">
      <button class="rv-detail-save" onclick="rvSaveDetail(${id})">💾 保存批注</button>
      <button class="rv-detail-cancel" onclick="rvToggleDetail(this.closest('tr').previousElementSibling,${id})">收起</button>
      <span style="font-size:.7rem;color:var(--muted)">仅更新批注，不改变审核状态</span>
    </div>
    <div>
      <span class="rv-detail-label">🕐 变更历史</span>
      <div id="rv-hist-${id}" style="margin-top:6px;font-size:.75rem;color:var(--muted)">加载中…</div>
    </div>
  </div></td>`;
  row.insertAdjacentElement('afterend', det);

  // 异步加载变更历史时间轴
  (async () => {
    const histBox = document.getElementById(`rv-hist-${id}`);
    if (!histBox) return;
    try {
      const resp = await fetch(`/api/v1/reviews/${id}/history`, {
        headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('token') || '') }
      });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      if (!data.items || !data.items.length) {
        histBox.innerHTML = '<span style="color:var(--muted)">暂无历史记录</span>';
        return;
      }
      const statusLabel = { pending:'待审', approved:'已通过', rejected:'已拒绝', revised:'修订中', deleted:'已删除' };
      const badgeCls    = { pending:'rv-pending', approved:'rv-approved', rejected:'rv-rejected', revised:'rv-revised' };
      const typeMap     = { status_change:'状态变更', notes_update:'批注更新', bulk_action:'批量操作' };
      histBox.innerHTML = `<div class="rv-history-list">${data.items.map(h => {
        const dt    = (h.changed_at || '').replace('T', ' ').slice(0, 16);
        const badge = `<span class="rv-badge rv-hist-badge ${badgeCls[h.status] || ''}">${statusLabel[h.status] || h.status}</span>`;
        const type  = `<span style="font-size:.68rem;color:var(--muted)">[${typeMap[h.change_type] || h.change_type}]</span>`;
        return `<div class="rv-hist-item">
          <div class="rv-hist-meta">${badge}<span class="rv-hist-who">${h.reviewer || '系统'}</span><span class="rv-hist-time">${dt}</span>${type}</div>
          ${h.notes ? `<div style="color:var(--muted);font-size:.74rem;margin-top:2px">批注：${h.notes}</div>` : ''}
          ${h.reject_reason ? `<div style="color:#dc2626;font-size:.74rem;margin-top:2px">原因：${h.reject_reason}</div>` : ''}
        </div>`;
      }).join('')}</div>`;
    } catch (e) {
      if (document.getElementById(`rv-hist-${id}`))
        document.getElementById(`rv-hist-${id}`).innerHTML = '<span style="color:var(--muted)">历史记录加载失败</span>';
    }
  })();
}

async function rvSaveDetail(id) {
  const rec = _rvData.find(r => r.id === id);
  if (!rec) return;
  const notes = document.getElementById(`rv-det-notes-${id}`)?.value ?? '';
  try {
    const r = await fetch(`/api/v1/reviews/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('token') || '') },
      body: JSON.stringify({ status: rec.status, notes, reject_reason: rec.reject_reason || '', reviewer: rec.reviewer || '' })
    });
    if (!r.ok) throw new Error(await r.text());
    rec.notes = notes;
    // 更新表格中该行的批注预览
    const rows = document.querySelectorAll('#rv-tbody tr:not(.rv-detail-row)');
    rows.forEach(tr => {
      if (tr.onclick && tr.innerHTML.includes(`rvToggleDetail(this,${id})`)) {
        const ntCell = tr.cells[8];
        if (ntCell) { ntCell.textContent = notes.length > 16 ? notes.slice(0,16)+'…' : (notes||'—'); ntCell.title = notes; }
      }
    });
    showToast('批注已保存 ✓', 'ok');
  } catch(e) { showToast('保存失败：' + e.message, 'error'); }
}

/* ── 审核内联操作模态（替代 prompt()）─────────────────────── */
let _rvActPending = null;  // { type:'single'|'bulk', id?, status?, action? }

function rvAct(id, status) {
  _rvActPending = { type: 'single', id, status };
  _rvActOpenDialog(status, 1);
}

function rvBulkAct(action) {
  if (!_rvSelected.size) { showToast('请先勾选记录', 'warn'); return; }
  if (action === 'delete') {
    if (!confirm(`确定删除 ${_rvSelected.size} 条记录？此操作不可恢复。`)) return;
    _rvBulkSend({ ids: [..._rvSelected], action: 'delete', reviewer: '', reject_reason: '', notes: '' });
    return;
  }
  _rvActPending = { type: 'bulk', action };
  _rvActOpenDialog(action, _rvSelected.size);
}

function _rvActOpenDialog(status, count) {
  const labels = { approved: '✅ 通过', rejected: '❌ 拒绝', revised: '🔄 修订' };
  const dlgTitle = labels[status] || status;
  document.getElementById('rv-act-title').textContent =
    count > 1 ? `${dlgTitle}（批量 ${count} 条）` : dlgTitle;
  document.getElementById('rv-act-notes-lbl').textContent =
    status === 'rejected' ? '拒绝原因（可留空）' : '备注说明（可留空）';
  const savedReviewer = localStorage.getItem('rv_reviewer') || 'admin';
  document.getElementById('rv-act-reviewer').value = savedReviewer;
  document.getElementById('rv-act-notes').value = '';
  document.getElementById('rv-act-dialog').classList.add('vis');
  setTimeout(() => document.getElementById('rv-act-reviewer').focus(), 50);
}

function rvActCancel() {
  document.getElementById('rv-act-dialog').classList.remove('vis');
  _rvActPending = null;
}

async function rvActConfirm() {
  if (!_rvActPending) return;
  const reviewer = document.getElementById('rv-act-reviewer').value.trim();
  const notes    = document.getElementById('rv-act-notes').value.trim();
  if (reviewer) localStorage.setItem('rv_reviewer', reviewer);
  document.getElementById('rv-act-dialog').classList.remove('vis');
  const pending = _rvActPending;
  _rvActPending = null;
  if (pending.type === 'single') {
    const { id, status } = pending;
    try {
      const body = { status, reviewer, notes, reject_reason: status === 'rejected' ? notes : '' };
      const r = await fetch(`/api/v1/reviews/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('token') || '') },
        body: JSON.stringify(body)
      });
      if (!r.ok) throw new Error(await r.text());
      showToast('已保存 ✓', 'ok');
      rvLoad();
      rvLoadStats();
    } catch(e) { showToast('操作失败：' + e.message, 'error'); }
  } else {
    const { action } = pending;
    await _rvBulkSend({
      ids: [..._rvSelected], action, reviewer,
      reject_reason: action === 'rejected' ? notes : '',
      notes
    });
  }
}

async function _rvBulkSend(body) {
  try {
    const r = await fetch('/api/v1/reviews/bulk_action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (localStorage.getItem('token') || '') },
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    showToast(`成功 ${d.succeeded.length} 条${d.failed.length ? '，失败 ' + d.failed.length + ' 条' : ''} ✓`, 'ok');
    _rvSelected.clear();
    rvLoad();
    rvLoadStats();
  } catch(e) { showToast('操作失败：' + e.message, 'error'); }
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
    template_version: (_lastData&&_lastData.template_version)||'standard',
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

