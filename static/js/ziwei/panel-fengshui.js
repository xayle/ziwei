/* ════════════════════════════════════════════════════════════
   §15  风水方位助手  Fengshui Panel
   ════════════════════════════════════════════════════════════ */

function openFsPanel() {
  document.getElementById('fs-panel').classList.add('vis');
  // 若已有命盘，自动填入出生年
  if (window._lastResult && window._lastResult.birth_year) {
    document.getElementById('fs-year').value = window._lastResult.birth_year;
  }
  if (window._lastResult && window._lastResult.gender) {
    const gSel = document.getElementById('fs-gender');
    gSel.value = window._lastResult.gender.includes('女') ? '女' : '男';
  }
}

function closeFsPanel() {
  document.getElementById('fs-panel').classList.remove('vis');
}

async function fsLoad() {
  const year   = document.getElementById('fs-year').value;
  const gender = document.getElementById('fs-gender').value;
  const facing = document.getElementById('fs-facing').value;
  const el = document.getElementById('fs-result');

  el.innerHTML = '<div class="zeri-loading">计算中…</div>';
  try {
    const params = new URLSearchParams({ birth_year: year, gender });
    if (facing) params.set('house_facing', facing);
    const r = await fetch(`/api/v1/fengshui/bagua?${params}`);
    if (!r.ok) {
      const err = await r.json().catch(()=>({}));
      el.innerHTML = `<div style="color:#dc2626;padding:16px">错误：${err.detail || r.status}</div>`;
      return;
    }
    const d = await r.json();
    el.innerHTML = _fsRender(d);
  } catch(e) {
    el.innerHTML = `<div style="color:#dc2626;padding:16px">请求失败：${e.message}</div>`;
  }
}

function _fsRender(d) {
  // 方向到指南针坐标的映射（3×3网格）
  const DIR_POS = { NW:0, N:1, NE:2, W:3, C:4, E:5, SW:6, S:7, SE:8 };
  const DIR_ARROW = { N:'↑', NE:'↗', E:'→', SE:'↘', S:'↓', SW:'↙', W:'←', NW:'↖', C:'●' };
  const cells = Array(9).fill(null);
  cells[4] = { direction:'C', direction_zh:'中', label:'命卦', level:'center', level_css:'center', desc:`${d.gua_name}（${d.gua_element}）` };

  // 吉凶色阶
  const jiCls = ['ji1','ji2','ji3','ji4'];
  const xiongCls = ['xiong1','xiong2','xiong3','xiong4'];
  d.auspicious.forEach((item, i) => {
    const pos = DIR_POS[item.direction];
    if (pos !== undefined) cells[pos] = { ...item, css: jiCls[i] || 'ji1' };
  });
  d.inauspicious.forEach((item, i) => {
    const pos = DIR_POS[item.direction];
    if (pos !== undefined) cells[pos] = { ...item, css: xiongCls[i] || 'xiong1' };
  });

  let compass = '<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start"><div class="fs-compass">';
  cells.forEach((c, i) => {
    if (!c) { compass += `<div class="fs-dir"></div>`; return; }
    const arrow = DIR_ARROW[c.direction] || '';
    compass += `<div class="fs-dir ${c.css || c.level_css || ''}">
      <div class="fsd-arrow">${arrow}</div>
      <div class="fsd-label">${c.direction_zh || c.direction}</div>
      <div class="fsd-name">${c.label || ''}</div>
    </div>`;
  });
  compass += '</div>';

  // 吉凶列表
  compass += '<div style="flex:1;min-width:180px"><div style="font-size:.8rem;font-weight:600;margin-bottom:6px">四吉方</div>';
  d.auspicious.forEach(item => {
    compass += `<div style="font-size:.76rem;margin-bottom:4px;color:var(--text)"><strong>${item.direction_zh}（${item.direction}）</strong> ${item.label} — ${item.desc}</div>`;
  });
  compass += '<div style="font-size:.8rem;font-weight:600;margin:10px 0 6px">四凶方</div>';
  d.inauspicious.forEach(item => {
    compass += `<div style="font-size:.76rem;margin-bottom:4px;color:var(--muted)"><strong>${item.direction_zh}（${item.direction}）</strong> ${item.label} — ${item.desc}</div>`;
  });
  compass += '</div></div>';

  // 家具建议
  const tips = [d.bed_tip, d.desk_tip, d.door_tip].filter(Boolean);
  let tipHtml = tips.length ? '<div class="fs-tip-cards">' + tips.map(t =>
    `<div class="fs-tip-card"><h4>${t.item}</h4><div class="ftc-dir">${t.direction_zh}（${t.direction}）</div><div style="font-size:.68rem;color:var(--muted)">${t.label}</div><div class="ftc-reason">${t.reason}</div></div>`
  ).join('') + '</div>' : '';

  // 人宅相合
  let compatHtml = '';
  if (d.compatibility) {
    const good = d.compatibility === '相合';
    compatHtml = `<div class="fs-compat ${good?'good':'bad'}">
      <div class="fsc-mark">${good?'✅':'⚠'}</div>
      <div><div class="fsc-text">人宅${d.compatibility}</div>
      <div class="fsc-note">${d.compatibility_note || ''}</div></div>
    </div>`;
  }

  // ── 九宫格房间布局评估区 ──────────────────────────────────
  // 构建 dir → { label, level_css } 映射（供 JS 使用）
  const _fsDirMap = {};
  [...(d.auspicious||[]), ...(d.inauspicious||[])].forEach(it => {
    _fsDirMap[it.direction] = { label: it.label, css: it.level_css, zh: it.direction_zh };
  });

  // 方位在 3×3 格中的位置（行×列，center=中间）
  const _FS_GRID_ORDER = ['NW','N','NE','W','C','E','SW','S','SE'];
  const _ROOM_OPTS = [
    ['empty','不设置'],['master_bedroom','主卧'],['bedroom','次卧'],
    ['study','书房'],['child_room','儿童房'],['living_room','客厅'],
    ['entrance','玄关/入口'],['dining_room','餐厅'],
    ['kitchen','厨房'],['bathroom','卫生间'],['storage','储藏室'],
  ];
  const optHtml = _ROOM_OPTS.map(([v,t]) => `<option value="${v}">${t}</option>`).join('');

  let roomGrid = '<div class="fs-room-section"><div class="fs-room-title">🏠 九宫格房间布局评估 <span style="font-size:.7rem;font-weight:400;color:var(--muted)">为每个方位指定房间类型，评估与命卦的相合程度</span></div>';
  roomGrid += '<div class="fs-room-grid">';
  _FS_GRID_ORDER.forEach(dir => {
    if (dir === 'C') {
      roomGrid += `<div class="fs-room-cell center"><div class="fs-room-cell-dir">中</div><div class="fs-room-cell-label">${d.gua_name}命</div></div>`;
    } else {
      const info = _fsDirMap[dir] || { label:'—', css:'', zh: dir };
      roomGrid += `<div class="fs-room-cell ${info.css}" id="frc-${dir}">
        <div class="fs-room-cell-dir">${info.zh}（${dir}）</div>
        <div class="fs-room-cell-label">${info.label}</div>
        <select class="fs-room-sel" id="frs-${dir}" onchange="fsUpdateCell('${dir}',this.value)">${optHtml}</select>
      </div>`;
    }
  });
  roomGrid += `</div><button class="fs-eval-btn" onclick="fsEvalRooms(${d.life_gua})">🔍 评估布局</button>`;
  roomGrid += '<div id="fs-assess-out"></div></div>';

  return `<div style="display:flex;flex-direction:column;gap:14px">
    <div style="font-size:.82rem"><strong>命卦：${d.gua_name}（第${d.life_gua}卦）</strong> · 五行：${d.gua_element} · 组别：${d.group}</div>
    ${compass}
    ${compatHtml}
    ${tipHtml}
    ${roomGrid}
    <p style="font-size:.65rem;color:var(--muted)">${d.disclaimer || '仅供参考，不构成专业建议。'}</p>
  </div>`;
}

/* ════════════════════════════════════════════════════════════
   §18  风水九宫格房间布局评估  Fengshui Room Layout
   ════════════════════════════════════════════════════════════ */

function fsUpdateCell(dir, roomType) {
  /* 实时更新格子背景色（可扩展） */
}

async function fsEvalRooms(lifeGua) {
  const tok = localStorage.getItem('ziwei_token') || localStorage.getItem('token') || '';
  const year   = document.getElementById('fs-year').value;
  const gender = document.getElementById('fs-gender').value;
  const facing = document.getElementById('fs-facing').value || null;
  const DIRS   = ['N','NE','E','SE','S','SW','W','NW'];
  const rooms  = {};
  DIRS.forEach(d => {
    const sel = document.getElementById(`frs-${d}`);
    if (sel && sel.value && sel.value !== 'empty') rooms[d] = sel.value;
  });
  if (!Object.keys(rooms).length) {
    showToast('请先设置至少一个方位的房间类型', 'warn');
    return;
  }
  const out = document.getElementById('fs-assess-out');
  out.innerHTML = '<div class="zeri-loading" style="padding:12px">评估中…</div>';
  try {
    const body = { birth_year: +year, gender, rooms };
    if (facing) body.house_facing = facing;
    const r = await fetch('/api/v1/fengshui/room-layout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(tok ? { Authorization: 'Bearer '+tok } : {}) },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(()=>({}));
      out.innerHTML = `<div style="color:#dc2626;font-size:.78rem;padding:8px">${err.detail || '评估失败 '+r.status}</div>`;
      return;
    }
    const d = await r.json();
    const lvlLabel = { excellent:'优秀✨', good:'不错👍', ok:'可接受', caution:'注意⚠', warning:'不佳❌', skip:'' };
    // 评分卡
    let html = `<div class="fs-assess-result">
      <div class="fs-assess-score ${d.grade_css}">
        <div class="fs-score-num">${d.score}</div>
        <div><div class="fs-score-grade">${d.grade}</div>
        <div style="font-size:.72rem;color:var(--muted)">命卦：${d.gua_name} · 加权布局评分</div></div>
      </div>`;
    // 逐区徽章
    const validCells = d.cells.filter(c => c.assess_level !== 'skip');
    if (validCells.length) {
      html += '<div class="fs-cell-badges">';
      validCells.forEach(c => {
        html += `<div class="fs-cb ${c.assess_level}" title="${c.assess_note}">${c.room_zh}@${c.direction_zh} ${lvlLabel[c.assess_level] || ''}</div>`;
      });
      html += '</div>';
    }
    // 建议列表
    if (d.suggestions && d.suggestions.length) {
      html += '<ul class="fs-suggestions">' + d.suggestions.map(s => `<li>${s}</li>`).join('') + '</ul>';
    }
    html += `<p style="font-size:.63rem;color:var(--muted);margin:0">${d.disclaimer}</p></div>`;
    out.innerHTML = html;
  } catch(e) {
    out.innerHTML = `<div style="color:#dc2626;font-size:.78rem;padding:8px">请求失败：${e.message}</div>`;
  }
}

/* ════════════════════════════════════════════════════════════
