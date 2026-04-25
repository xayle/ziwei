async function openLlmPanel() {
  document.getElementById('llm-panel').classList.add('vis');
  await llmCheckConfig();
  llmUpdateMeta();
  llmLoadDrafts();
}

function closeLlmPanel() {
  document.getElementById('llm-panel').classList.remove('vis');
}

async function llmCheckConfig() {
  try {
    const r = await fetch('/api/v1/llm/config');
    if (!r.ok) return;
    const cfg = await r.json();
    const badge = document.getElementById('llm-provider-badge');
    badge.textContent = cfg.provider + (cfg.model ? ' / ' + cfg.model : '');
    badge.className = 'llm-provider-badge' + (cfg.provider === 'mock' ? ' mock' : '');
  } catch {}
}

function llmUpdateMeta() {
  const meta = document.getElementById('llm-meta-box');
  if (!_lastData || !_lastData.life_palace_gz) {
    meta.textContent = '请先在主界面排盘，再打开此面板生成 AI 解读草稿。';
    return;
  }
  const d = _lastData;
  const hash = _llmChartHash();
  meta.innerHTML = `<b>当前命盘：</b>${d.birth_info_summary||''}　<b>命宫：</b>${d.life_palace_gz||''}　<b>五行局：</b>${d.wuxing_ju_name||''}　<span style="color:var(--muted);font-size:.72rem">hash: ${hash.slice(0,12)}…</span>`;
}

function _llmChartHash() {
  // 简单 hash，基于命宫干支 + 五行局 + 出生信息摘要
  if (!_lastData) return 'no-data';
  const raw = [_lastData.life_palace_gz || '', _lastData.wuxing_ju_name || '', _lastData.birth_info_summary || ''].join('|');
  let h = 0;
  for (let i = 0; i < raw.length; i++) { h = Math.imul(31, h) + raw.charCodeAt(i) | 0; }
  return (h >>> 0).toString(16).padStart(8, '0') + '-' + raw.length.toString(16) + '-ziwei';
}

function _llmBuildRequest() {
  if (!_lastData || !_lastData.life_palace_gz) return null;
  return {
    chart_hash: _llmChartHash(),
    life_palace_gz:      _lastData.life_palace_gz      || '',
    wuxing_ju_name:      _lastData.wuxing_ju_name      || '',
    pattern_summary:     _lastData.pattern_summary      || (_lastData.patterns ? _lastData.patterns.join('、') : ''),
    birth_info_summary:  _lastData.birth_info_summary   || ''
  };
}

async function llmGenerateDraft() {
  const req = _llmBuildRequest();
  if (!req) { showToast('请先在主界面排盘', 'warn'); return; }
  const genBtn    = document.getElementById('llm-gen-btn');
  const statusEl  = document.getElementById('llm-gen-status');
  const streamBox = document.getElementById('llm-stream-box');
  const actionsEl = document.getElementById('llm-current-actions');
  const discEl    = document.getElementById('llm-disclaimer');

  genBtn.disabled = true;
  statusEl.textContent = '生成中…';
  streamBox.classList.remove('vis');
  actionsEl.classList.add('hid');
  discEl.style.display = 'none';

  try {
    const tok = localStorage.getItem('ziwei_token');
    const r = await fetch('/api/v1/llm/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(tok ? { Authorization: 'Bearer ' + tok } : {}) },
      body: JSON.stringify(req)
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      if (r.status === 401) {
        statusEl.innerHTML = '⚠ 需要登录后才能使用 AI 草稿功能。<br><small style="color:var(--muted)">请在右上角登录后重试。</small>';
      } else {
        statusEl.textContent = '错误：' + (e.detail || r.status);
      }
      return;
    }
    const draft = await r.json();
    _llmCurrentDraftId = draft.id;
    _llmCurrentText    = draft.draft_text || '';
    streamBox.textContent = draft.draft_text || '';
    streamBox.classList.add('vis');
    _llmShowActions(draft.status);
    discEl.style.display = '';
    statusEl.textContent = '✔ 已生成（来自缓存或新建）';
    llmLoadDrafts();
  } catch (err) {
    statusEl.textContent = '请求失败：' + err.message;
  } finally {
    genBtn.disabled = false;
  }
}

async function llmStreamDraft() {
  const req = _llmBuildRequest();
  if (!req) { showToast('请先在主界面排盘', 'warn'); return; }
  const streamBtn = document.getElementById('llm-stream-btn');
  const statusEl  = document.getElementById('llm-gen-status');
  const streamBox = document.getElementById('llm-stream-box');
  const actionsEl = document.getElementById('llm-current-actions');
  const discEl    = document.getElementById('llm-disclaimer');

  streamBtn.disabled = true;
  statusEl.textContent = '流式生成中…';
  streamBox.classList.add('vis');
  streamBox.innerHTML = '<span class="llm-stream-cursor"></span>';
  actionsEl.classList.add('hid');
  discEl.style.display = 'none';
  _llmCurrentText = '';
  _llmCurrentDraftId = null;

  try {
    const tok = localStorage.getItem('ziwei_token');
    const qs = new URLSearchParams({
      chart_hash:         req.chart_hash,
      life_palace_gz:     req.life_palace_gz,
      wuxing_ju_name:     req.wuxing_ju_name,
      pattern_summary:    req.pattern_summary,
      birth_info_summary: req.birth_info_summary
    }).toString();
    const url = '/api/v1/llm/stream?' + qs;
    const resp = await fetch(url, { headers: tok ? { Authorization: 'Bearer ' + tok } : {} });
    if (!resp.ok) {
      if (resp.status === 401) {
        statusEl.innerHTML = '⚠ 需要登录后才能使用流式生成。<br><small style="color:var(--muted)">请在右上角登录后重试。</small>';
      } else {
        statusEl.textContent = '流式请求失败：' + resp.status;
      }
      return;
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    let text = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') continue;
        try {
          const evt = JSON.parse(payload);
          if (evt.type === 'chunk') {
            text += evt.text;
            streamBox.textContent = text;
          } else if (evt.type === 'done') {
            _llmCurrentDraftId = evt.draft_id || null;
            statusEl.textContent = '✔ 流式生成完成';
            discEl.style.display = '';
            _llmShowActions('pending_review');
            llmLoadDrafts();
          } else if (evt.type === 'error') {
            statusEl.textContent = '生成失败：' + (evt.message || '未知错误');
          }
        } catch {}
      }
      _llmCurrentText = text;
    }
  } catch (err) {
    statusEl.textContent = '连接失败：' + err.message;
  } finally {
    streamBtn.disabled = false;
    // 移除闪烁游标
    if (streamBox.querySelector('.llm-stream-cursor')) {
      streamBox.innerHTML = streamBox.textContent.replace('<span class="llm-stream-cursor"></span>', '');
    }
  }
}

function _llmShowActions(status) {
  const actionsEl  = document.getElementById('llm-current-actions');
  const statusTag  = document.getElementById('llm-current-status-tag');
  const labelMap   = { pending_review: '待审核', approved: '已通过', rejected: '已驳回' };
  actionsEl.classList.remove('hid');
  statusTag.textContent = labelMap[status] || status;
  statusTag.className   = 'llm-status-tag ' + (status || 'pending_review');
  // 审核按钮只对待审核状态可用
  actionsEl.querySelectorAll('.llm-approve-btn,.llm-reject-btn').forEach(b => {
    b.style.display = status === 'pending_review' ? '' : 'none';
  });
}

async function llmReviewCurrentDraft(action) {
  if (!_llmCurrentDraftId) return;
  const reviewer = localStorage.getItem('ziwei_username') || 'reviewer';
  await llmReviewDraft(_llmCurrentDraftId, action, reviewer);
  _llmShowActions(action === 'approved' ? 'approved' : 'rejected');
  llmLoadDrafts();
}

function llmCopyCurrentDraft() {
  if (!_llmCurrentText) return;
  navigator.clipboard.writeText(_llmCurrentText).then(() => showToast('已复制到剪贴板', 'ok')).catch(() => {});
}

async function llmLoadDrafts() {
  const listEl  = document.getElementById('llm-drafts-list');
  const emptyEl = document.getElementById('llm-drafts-empty');
  const status  = document.getElementById('llm-list-status').value;
  listEl.innerHTML = '<div style="text-align:center;color:var(--muted);font-size:.8rem;padding:16px">加载中…</div>';
  emptyEl.style.display = 'none';

  try {
    const tok = localStorage.getItem('ziwei_token');
    const qs = 'skip=0&limit=20' + (status ? '&status=' + encodeURIComponent(status) : '');
    const r = await fetch('/api/v1/llm/drafts?' + qs, {
      headers: tok ? { Authorization: 'Bearer ' + tok } : {}
    });
    if (!r.ok) { 
      if (r.status === 401) {
        listEl.innerHTML = '<div style="color:#ca8a04;padding:12px;font-size:.78rem">⚠ 需要登录后才能查看历史草稿。</div>';
      } else {
        listEl.innerHTML = '<div style="color:#ef4444;padding:12px;font-size:.78rem">加载失败 ' + r.status + '</div>';
      }
      return; }
    const data = await r.json();
    if (!data.items || data.items.length === 0) {
      listEl.innerHTML = '';
      emptyEl.style.display = '';
      return;
    }
    listEl.innerHTML = data.items.map(d => _llmDraftCard(d)).join('');
  } catch (err) {
    listEl.innerHTML = '<div style="color:#ef4444;padding:12px;font-size:.78rem">请求失败：' + err.message + '</div>';
  }
}

function _llmDraftCard(d) {
  const labelMap = { pending_review: '待审核', approved: '已通过', rejected: '已驳回' };
  const preview  = (d.draft_text || '').slice(0, 100).replace(/\n/g, ' ');
  const approveBtn = d.status === 'pending_review' ?
    `<button class="llm-draft-card-btn llm-dcb-approve" onclick="llmReviewDraft(${d.id},'approved')">通过</button>
     <button class="llm-draft-card-btn llm-dcb-reject"  onclick="llmReviewDraft(${d.id},'rejected')">驳回</button>` : '';
  return `<div class="llm-draft-card">
    <div class="llm-draft-card-top">
      <span class="llm-status-tag ${d.status}">${labelMap[d.status]||d.status}</span>
      <span style="color:var(--muted);font-size:.72rem">${d.provider}/${d.model||''}</span>
      <span style="color:var(--muted);font-size:.72rem;margin-left:auto">${(d.created_at||'').slice(0,16)}</span>
    </div>
    <div class="llm-draft-preview">${preview}…</div>
    <div class="llm-draft-card-btns">
      <button class="llm-draft-card-btn llm-dcb-view" onclick="llmViewDraft(${d.id})">查看全文</button>
      ${approveBtn}
    </div>
  </div>`;
}

async function llmViewDraft(id) {
  const tok = localStorage.getItem('ziwei_token');
  const r = await fetch('/api/v1/llm/drafts/' + id, {
    headers: tok ? { Authorization: 'Bearer ' + tok } : {}
  });
  if (!r.ok) { showToast('加载失败', 'error'); return; }
  const d = await r.json();
  _llmCurrentDraftId = d.id;
  _llmCurrentText    = d.draft_text || '';
  const streamBox = document.getElementById('llm-stream-box');
  const discEl    = document.getElementById('llm-disclaimer');
  streamBox.textContent = d.draft_text || '';
  streamBox.classList.add('vis');
  discEl.style.display = '';
  _llmShowActions(d.status);
}

async function llmReviewDraft(id, action, reviewer) {
  const tok = localStorage.getItem('ziwei_token');
  reviewer = reviewer || localStorage.getItem('ziwei_username') || 'reviewer';
  const r = await fetch('/api/v1/llm/drafts/' + id, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...(tok ? { Authorization: 'Bearer ' + tok } : {}) },
    body: JSON.stringify({ status: action, reviewer, reviewer_notes: '' })
  });
  if (r.ok) {
    showToast(action === 'approved' ? '已通过草稿' : '已驳回草稿', 'ok');
    llmLoadDrafts();
  } else {
    showToast('操作失败 ' + r.status, 'error');
  }
}

