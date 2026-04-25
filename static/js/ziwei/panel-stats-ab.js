/* ════════════════════════════════════════════════════════════
   §17  全局统计面板  Admin Stats Dashboard
   ════════════════════════════════════════════════════════════ */

function openStatsPanel() {
  document.getElementById('stats-panel').classList.add('vis');
}

function closeStatsPanel() {
  document.getElementById('stats-panel').classList.remove('vis');
}

async function statsLoad() {
  const el = document.getElementById('stats-content');
  const ts = document.getElementById('stats-ts');
  el.innerHTML = '<div class="zeri-loading">加载中…</div>';
  ts.textContent = '加载中…';
  try {
    const token = localStorage.getItem('ziwei_token') || '';
    const r = await fetch('/api/v1/admin/stats', {
      headers: token ? { Authorization: 'Bearer ' + token } : {}
    });
    if (r.status === 401 || r.status === 403) {
      el.innerHTML = '<div style="color:#dc2626;padding:20px;font-size:.85rem">⚠ 权限不足：请先登录管理员账户后查看统计数据</div>';
      ts.textContent = '需要管理员权限';
      return;
    }
    if (!r.ok) {
      el.innerHTML = `<div style="color:#dc2626;padding:20px">加载失败：${r.status}</div>`;
      ts.textContent = '加载失败';
      return;
    }
    const d = await r.json();
    el.innerHTML = _statsRender(d);
    ts.textContent = d.generated_at ? ('更新时间：' + new Date(d.generated_at).toLocaleString('zh')) : '';
  } catch(e) {
    el.innerHTML = `<div style="color:#dc2626;padding:20px">网络错误：${e.message}</div>`;
    ts.textContent = '加载失败';
  }
}

function _statsRender(d) {
  const u = d.users || {};
  const rv = d.reviews || {};
  const exp = d.experiments || {};

  // 指标卡
  const cards = [
    { val: u.total || 0,             lbl: '总用户', sub: `活跃 ${u.active||0} · 非活跃 ${u.inactive||0}` },
    { val: d.cases?.total || 0,      lbl: '命盘档案', sub: '' },
    { val: d.snapshots?.total || 0,  lbl: '快照', sub: '' },
    { val: d.chart_cases?.total || 0,lbl: '索引命盘', sub: '' },
    { val: rv.total || 0,            lbl: '人工审核总数', sub: `待审 ${rv.pending||0}` },
    { val: d.api_keys?.total || 0,   lbl: 'API Keys', sub: '' },
    { val: exp.total || 0,           lbl: 'A/B 实验', sub: `运行中 ${exp.running||0}` },
    { val: d.audit_logs?.total || 0, lbl: '审计日志', sub: '' },
  ];
  let cardsHtml = '<div class="stats-grid">' + cards.map(c =>
    `<div class="stats-card"><div class="sc-val">${c.val}</div><div class="sc-lbl">${c.lbl}</div><div class="sc-sub">${c.sub}</div></div>`
  ).join('') + '</div>';

  // 审核状态
  const rvCards = [
    { cls:'srv-pending',  num: rv.pending  || 0, lbl:'待审核' },
    { cls:'srv-approved', num: rv.approved || 0, lbl:'已通过' },
    { cls:'srv-rejected', num: rv.rejected || 0, lbl:'已拒绝' },
    { cls:'srv-revised',  num: rv.revised  || 0, lbl:'待修改' },
  ];
  let rvHtml = `<div><div class="stats-sec-title">审核状态分布</div><div style="height:8px"></div>
    <div class="stats-review-grid">` + rvCards.map(c =>
    `<div class="stats-rv-card ${c.cls}"><div class="srv-num">${c.num}</div><div class="srv-lbl">${c.lbl}</div></div>`
  ).join('') + '</div></div>';

  // 柱状图辅助
  function barChart(title, items) {
    if (!items || items.length === 0) return '';
    const max = Math.max(...items.map(x => x.count), 1);
    return `<div><div class="stats-sec-title">${title}</div><div style="height:8px"></div>
      <div class="stats-bar-wrap">` + items.map(item => {
        const pct = Math.round((item.count / max) * 100);
        return `<div class="stats-bar-row">
          <div class="stats-bar-name" title="${item.name}">${item.name}</div>
          <div class="stats-bar-bg"><div class="stats-bar-fill" style="width:${pct}%"></div></div>
          <div class="stats-bar-cnt">${item.count}</div>
        </div>`;
      }).join('') + '</div></div>';
  }

  const patChart  = barChart('热门命格（Top 局型）', d.top_patterns);
  const wxChart   = barChart('五行局分布', d.top_wuxing);

  return `<div style="display:flex;flex-direction:column;gap:16px">
    ${cardsHtml}
    ${rvHtml}
    <div class="stats-two-col">
      ${patChart}
      ${wxChart}
    </div>
  </div>`;
}

/* ════════════════════════════════════════════════════════════
   §9  A/B 测试平台  A/B Testing Platform
   ════════════════════════════════════════════════════════════ */

let _abFilter   = 'all';    // 当前筛选状态
let _abPage     = 0;        // 当前分页 (0-based)
const _AB_PAGE  = 10;       // 每页条数
let _abTotal    = 0;        // 总条数
let _abData     = [];       // 当前页数据

function openAbPanel() {
  document.getElementById('ab-panel').classList.add('vis');
  abLoadList();
}

function closeAbPanel() {
  document.getElementById('ab-panel').classList.remove('vis');
}

function abShowCreateForm() {
  document.getElementById('ab-create-form').style.display = '';
}

function abHideCreateForm() {
  document.getElementById('ab-create-form').style.display = 'none';
}

function abHideResults() {
  document.getElementById('ab-results').classList.remove('show');
}

function abFilter(btn, status) {
  document.querySelectorAll('.ab-status-btn').forEach(b => b.classList.remove('act'));
  btn.classList.add('act');
  _abFilter = status;
  _abPage   = 0;
  abLoadList();
}

async function abLoadList() {
  const listEl  = document.getElementById('ab-list');
  const pageEl  = document.getElementById('ab-pagination');
  listEl.innerHTML = '<div class="ab-empty">加载中…</div>';
  pageEl.innerHTML = '';

  const params = new URLSearchParams({ skip: _abPage * _AB_PAGE, limit: _AB_PAGE });
  if (_abFilter !== 'all') params.set('status', _abFilter);

  try {
    const token = localStorage.getItem('jwt_token') || '';
    const r = await fetch('/api/v1/experiments?' + params, {
      headers: { Authorization: 'Bearer ' + token }
    });
    if (r.status === 401) { listEl.innerHTML = '<div class="ab-empty">需要登录才能管理实验</div>'; return; }
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    _abData  = d.items || [];
    _abTotal = d.total || 0;
    abRenderList(_abData);
    abRenderPagination();
  } catch (e) {
    listEl.innerHTML = '<div class="ab-empty" style="color:#dc2626">加载失败: ' + e.message + '</div>';
  }
}

function abRenderList(items) {
  const el = document.getElementById('ab-list');
  if (!items.length) { el.innerHTML = '<div class="ab-empty">暂无实验记录</div>'; return; }
  el.innerHTML = items.map(exp => {
    const statusLabel = { draft:'草稿', running:'运行中', paused:'暂停', completed:'已完成' }[exp.status] || exp.status;
    const variantChips = (exp.variants || []).map(v =>
      `<span class="ab-variant-chip">${v.name} (${exp.traffic_split[v.name]||0}%)</span>`
    ).join('');
    const btnStart    = exp.status === 'draft'    ? `<button class="ab-btn start"    onclick="abChangeStatus(${exp.id},'running')">▶ 启动</button>` : '';
    const btnPause    = exp.status === 'running'  ? `<button class="ab-btn pause"    onclick="abChangeStatus(${exp.id},'paused')">⏸ 暂停</button>` : '';
    const btnResume   = exp.status === 'paused'   ? `<button class="ab-btn start"    onclick="abChangeStatus(${exp.id},'running')">▶ 继续</button>` : '';
    const btnComplete = (exp.status === 'running' || exp.status === 'paused') ? `<button class="ab-btn complete" onclick="abChangeStatus(${exp.id},'completed')">✔ 完成</button>` : '';
    const btnResults  = `<button class="ab-btn results" onclick="abViewResults(${exp.id})">📊 结果</button>`;
    const btnDelete   = exp.status !== 'running' ? `<button class="ab-btn delete"   onclick="abDelete(${exp.id})">🗑 删除</button>` : '';
    const startedInfo = exp.started_at ? `· 启动：${exp.started_at.slice(0,10)}` : '';
    return `
    <div class="ab-card" id="ab-card-${exp.id}">
      <div class="ab-card-top">
        <span class="ab-card-name">${exp.name}</span>
        <span class="ab-badge ${exp.status}">${statusLabel}</span>
      </div>
      <div class="ab-card-desc">${exp.description || '<em>无描述</em>'}</div>
      <div class="ab-variants">${variantChips}</div>
      <div class="ab-card-meta">目标指标: ${exp.target_metric} · 最小样本: ${exp.min_sample_size}${startedInfo}</div>
      <div class="ab-card-btns">${btnStart}${btnResume}${btnPause}${btnComplete}${btnResults}${btnDelete}</div>
    </div>`;
  }).join('');
}

function abRenderPagination() {
  const el = document.getElementById('ab-pagination');
  const totalPages = Math.ceil(_abTotal / _AB_PAGE);
  if (totalPages <= 1) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <button class="ab-page-btn" onclick="abGoPage(${_abPage - 1})" ${_abPage === 0 ? 'disabled' : ''}>&laquo;</button>
    <span>${_abPage + 1} / ${totalPages}（共 ${_abTotal} 条）</span>
    <button class="ab-page-btn" onclick="abGoPage(${_abPage + 1})" ${_abPage >= totalPages - 1 ? 'disabled' : ''}>&raquo;</button>`;
}

function abGoPage(page) {
  _abPage = page;
  abLoadList();
}

async function abCreateExperiment() {
  const name = document.getElementById('abn-name').value.trim();
  if (!name) { alert('请填写实验名称'); return; }
  const wCtrl = parseInt(document.getElementById('abn-weight-ctrl').value) || 50;
  const wVA   = parseInt(document.getElementById('abn-weight-va').value)   || 50;
  const body = {
    name,
    description: document.getElementById('abn-desc').value.trim(),
    target_metric: document.getElementById('abn-metric').value,
    hypothesis: document.getElementById('abn-hypothesis').value.trim(),
    min_sample_size: parseInt(document.getElementById('abn-mss').value) || 100,
    variants: [
      { name: 'control',   description: '对照组', weight: wCtrl },
      { name: 'variant_a', description: '实验组 A', weight: wVA },
    ]
  };
  try {
    const token = localStorage.getItem('jwt_token') || '';
    const r = await fetch('/api/v1/experiments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify(body)
    });
    if (!r.ok) { const e = await r.json(); alert('创建失败: ' + (e.detail || JSON.stringify(e))); return; }
    abHideCreateForm();
    // 清空表单
    ['abn-name','abn-desc','abn-hypothesis'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('abn-mss').value = '100';
    abLoadList();
  } catch (e) {
    alert('请求失败: ' + e.message);
  }
}

async function abChangeStatus(id, newStatus) {
  const labels = { running: '启动', paused: '暂停', completed: '完成' };
  if (!confirm(`确定要将実验状态改为「${labels[newStatus] || newStatus}」吗？`)) return;
  try {
    const token = localStorage.getItem('jwt_token') || '';
    const r = await fetch('/api/v1/experiments/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ status: newStatus })
    });
    if (!r.ok) { const e = await r.json(); alert('操作失败: ' + (e.detail || JSON.stringify(e))); return; }
    abLoadList();
  } catch (e) {
    alert('请求失败: ' + e.message);
  }
}

async function abDelete(id) {
  if (!confirm('确定要删除这条实验吗？此操作不可撤销。')) return;
  try {
    const token = localStorage.getItem('jwt_token') || '';
    const r = await fetch('/api/v1/experiments/' + id, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + token }
    });
    if (r.status !== 204 && !r.ok) { const e = await r.json(); alert('删除失败: ' + (e.detail || JSON.stringify(e))); return; }
    abLoadList();
  } catch (e) {
    alert('请求失败: ' + e.message);
  }
}

async function abViewResults(id) {
  const resEl = document.getElementById('ab-results');
  const titleEl = document.getElementById('ab-results-title');
  const noteEl  = document.getElementById('ab-results-note');
  const barsEl  = document.getElementById('ab-results-bars');
  const winnerEl= document.getElementById('ab-results-winner');

  resEl.classList.add('show');
  titleEl.textContent = '加载结果中…';
  noteEl.textContent = '';
  barsEl.innerHTML = '';
  winnerEl.textContent = '';
  // scroll results into view
  resEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  try {
    const token = localStorage.getItem('jwt_token') || '';
    const r = await fetch('/api/v1/experiments/' + id + '/results', {
      headers: { Authorization: 'Bearer ' + token }
    });
    if (!r.ok) throw new Error((await r.json()).detail || '请求失败');
    const d = await r.json();
    titleEl.textContent = `📊 ${d.experiment_name} — 结果`;
    noteEl.textContent  = d.note;
    winnerEl.textContent = d.winner ? `🏆 优胜变体: ${d.winner}` : '';

    const maxRate = Math.max(...(d.variants || []).map(v => v.conversion_rate), 0.001);
    barsEl.innerHTML = (d.variants || []).map(v => `
      <div class="ab-vrow">
        <span>${v.variant}</span>
        <div class="ab-vbar-bg"><div class="ab-vbar-fill" style="width:${(v.conversion_rate/maxRate*100).toFixed(1)}%"></div></div>
        <span>${(v.conversion_rate * 100).toFixed(1)}%</span>
        <span style="color:var(--muted)">${v.assigned} 样本</span>
      </div>
    `).join('');
  } catch (e) {
    noteEl.textContent = '加载失败: ' + e.message;
    titleEl.textContent = '实验结果';
  }
}

/* ════════════════════════════════════════════════════════════
   §5  快速模拟对比  Quick Simulation Compare
