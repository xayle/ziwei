/* ════════════════════════════════════════════════════════════
   §13  择日推荐  Zeri Recommendation
   ════════════════════════════════════════════════════════════ */

function openZeriPanel() {
  document.getElementById('zeri-panel').classList.add('vis');
}

function closeZeriPanel() {
  document.getElementById('zeri-panel').classList.remove('vis');
}

async function zeriLoad() {
  const year  = document.getElementById('zeri-year').value;
  const month = document.getElementById('zeri-month').value;
  const purpose = document.getElementById('zeri-purpose').value;
  const el = document.getElementById('zeri-result');

  // 从上次命盘结果取参数（使用全局 _lastData）
  const res = _lastData;
  if (!res || !res.wuxing_ju_name || res.life_palace_branch_idx == null) {
    el.innerHTML = '<div style="color:#dc2626;padding:16px">请先排盘后再使用择日功能（需要命宫地支和五行局信息）</div>';
    return;
  }
  // life_palace_branch_idx 是地支索引（子=0…亥=11），转为地支字符
  const branch = BRANCHES[res.life_palace_branch_idx] || '';
  const wxju   = res.wuxing_ju_name || '';
  // 从出生年干支（lunar.year_gz，如「戊申」）提取地支（第2字）
  const natal  = (res.lunar && res.lunar.year_gz) ? res.lunar.year_gz.slice(1, 2) : '';

  el.innerHTML = '<div class="zeri-loading">计算中…</div>';
  try {
    const params = new URLSearchParams({
      year, month, life_palace_branch: branch,
      wuxing_ju_name: wxju, natal_year_branch: natal, purpose
    });
    const r = await fetch(`/api/v1/zeri/recommend?${params}`);
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      el.innerHTML = `<div style="color:#dc2626;padding:16px">错误：${err.detail || r.status}</div>`;
      return;
    }
    const d = await r.json();
    el.innerHTML = _zeriRender(d, parseInt(year), parseInt(month));
  } catch(e) {
    el.innerHTML = `<div style="color:#dc2626;padding:16px">请求失败：${e.message}</div>`;
  }
}

function _zeriRender(d, year, month) {
  const days = d.days || [];
  const recs = d.recommendations || [];
  const maxScore = Math.max(...days.map(x => x.score), 1);

  // 日历头
  const WDAYS = ['日','一','二','三','四','五','六'];
  let firstDay = new Date(year, month - 1, 1).getDay();
  let cal = '<div class="zeri-cal">';
  WDAYS.forEach(w => { cal += `<div class="zeri-cal-hd">${w}</div>`; });
  for (let i = 0; i < firstDay; i++) cal += `<div class="zeri-day empty"></div>`;
  days.forEach(day => {
    let cls = 'zeri-day';
    if (day.score >= 9)      cls += ' ji2';
    else if (day.score >= 7) cls += ' ji3';
    else if (day.score >= 5) cls += ' ji1';
    else                     cls += ' xiong';
    const stars = day.auspicious_stars && day.auspicious_stars.length ? day.auspicious_stars.slice(0,2).join(' ') : '';
    cal += `<div class="${cls}"><div class="zd-score">${day.score}</div><div class="zd-num">${day.date ? day.date.slice(-2) + '日' : ''}</div><div class="zd-star">${stars}</div></div>`;
  });
  cal += '</div>';

  // 推荐列表
  let recHtml = '<div class="zeri-recs">';
  if (recs.length === 0) {
    recHtml += '<div style="color:var(--muted);font-size:.8rem;padding:8px">本月暂无高分吉日（评分≥7），建议调整月份或用途</div>';
  } else {
    recs.forEach(rec => {
      const goodTags = (rec.auspicious_stars || []).map(s => `<span class="zrc-tag">${s}</span>`).join('');
      const badTags  = (rec.inauspicious_stars || []).map(s => `<span class="zrc-tag bad">${s}</span>`).join('');
      recHtml += `<div class="zeri-rec-card">
        <div class="zrc-score">${rec.score}</div>
        <div><div class="zrc-date">${rec.date} ${rec.weekday || ''} ${rec.jieqi ? '（'+rec.jieqi+'）':''}</div>
        <div class="zrc-tags">${goodTags}${badTags}</div>
        <div class="zrc-reason">${rec.summary || ''}</div></div>
      </div>`;
    });
  }
  recHtml += '</div>';

  return `<div>
    <div style="font-size:.78rem;color:var(--muted);margin-bottom:8px">
      ${year}年${month}月 · 命宫: <strong>${window._lastResult?.life_palace?.branch || ''}</strong> · 
      五行局: <strong>${window._lastResult?.wuxing_ju_name || ''}</strong>
    </div>
    ${cal}
    <div style="font-size:.78rem;font-weight:600;color:var(--text);margin:14px 0 6px">推荐吉日（共 ${recs.length} 天）</div>
    ${recHtml}
  </div>`;
}

/* ════════════════════════════════════════════════════════════
   §14  命盘数据导出  Chart Data Export
   ════════════════════════════════════════════════════════════ */

function openExportPanel() {
  document.getElementById('export-panel').classList.add('vis');
  document.getElementById('export-status').textContent = '';
  // 若尚未保存，则自动静默保存以获取 case_id
  if (!window._lastCaseId && _lastData) {
    saveChart(true);
  }
}

function closeExportPanel() {
  document.getElementById('export-panel').classList.remove('vis');
}

async function exportFull(e) {
  e.preventDefault();
  const caseId = window._lastCaseId;
  if (!caseId) {
    document.getElementById('export-status').textContent = '⚠ 未找到 Case ID，请先保存命盘';
    return;
  }
  document.getElementById('export-status').textContent = '下载中…';
  try {
    const token = localStorage.getItem('ziwei_token') || '';
    const r = await fetch(`/api/v1/cases/${caseId}/export`, {
      headers: token ? { Authorization: 'Bearer ' + token } : {}
    });
    if (!r.ok) {
      document.getElementById('export-status').textContent = '下载失败：' + r.status;
      return;
    }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `ziwei_case_${caseId}.json`;
    document.body.appendChild(a); a.click();
    URL.revokeObjectURL(url); a.remove();
    document.getElementById('export-status').textContent = '✓ 下载完成';
  } catch(err) {
    document.getElementById('export-status').textContent = '网络错误：' + err.message;
  }
}

async function exportMeta(e) {
  e.preventDefault();
  const caseId = window._lastCaseId;
  if (!caseId) {
    document.getElementById('export-status').textContent = '⚠ 未找到 Case ID，请先保存命盘';
    return;
  }

  async function exportPDF(e) {
    e.preventDefault();
    const caseId = window._lastCaseId;
    if (!caseId) {
      document.getElementById('export-status').textContent = '⚠ 未找到 Case ID，请先保存命盘';
      return;
    }
    const btn = document.getElementById('export-pdf-link');
    const originalText = btn.textContent;
    btn.textContent = '⏳ 正在云端渲染，请耐心等待 (约3-5秒)...';
    btn.style.pointerEvents = 'none';
    btn.style.opacity = '0.7';
    document.getElementById('export-status').textContent = '正生成PDF文件…';
    try {
      const token = localStorage.getItem('ziwei_token') || '';
      const r = await fetch(`/api/v1/cases/${caseId}/export/pdf`, {
        headers: token ? { Authorization: 'Bearer ' + token } : {}
      });
      if (!r.ok) {
        let msg = r.status;
        try { const errData = await r.json(); msg += ' ' + (errData.detail || errData.message); } catch(ex){}
        document.getElementById('export-status').textContent = '下载失败：' + msg;
        return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ziwei_${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      document.getElementById('export-status').textContent = 'PDF 下载成功';
    } catch(err) {
      document.getElementById('export-status').textContent = '网络错误：' + err.message;
    } finally {
      btn.textContent = originalText;
      btn.style.pointerEvents = 'auto';
      btn.style.opacity = '1';
    }
  }

  document.getElementById('export-status').textContent = '下载中…';
  try {
    const token = localStorage.getItem('ziwei_token') || '';
    const r = await fetch(`/api/v1/cases/${caseId}/export/meta`, {
      headers: token ? { Authorization: 'Bearer ' + token } : {}
    });
    if (!r.ok) {
      document.getElementById('export-status').textContent = '下载失败：' + r.status;
      return;
    }
    const data = await r.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `ziwei_meta_${caseId}.json`;
    document.body.appendChild(a); a.click();
    URL.revokeObjectURL(url); a.remove();
    document.getElementById('export-status').textContent = '✓ 元数据下载完成';
  } catch(err) {
    document.getElementById('export-status').textContent = '网络错误：' + err.message;
  }
}

