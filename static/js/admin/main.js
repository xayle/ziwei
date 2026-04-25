/**
 * 管理后台 — main.js
 * API base: /api/v1
 * P3.2: 常量和内部函数封装在 IIFE 中；
 *       HTML onclick 依赖函数通过 window.X = X 显式暴露
 */

"use strict";

(function () {

const BASE = "/api/v1";
let _token = "";
let _toastTimer = null;
let _glossaryData = [];
let _editingTerm = "";

/* ══════════════════════════════════════════════
   工具
══════════════════════════════════════════════ */
function showToast(msg, duration = 2600) {
  const el = document.getElementById("adm-toast");
  if (!el) return;
  el.textContent = msg;
  clearTimeout(_toastTimer);
  el.classList.add("show");
  _toastTimer = setTimeout(() => el.classList.remove("show"), duration);
}

function authHeaders(extra = {}) {
  return { "Content-Type": "application/json", "Authorization": `Bearer ${_token}`, ...extra };
}

function esc(s) {
  return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

/* ══════════════════════════════════════════════
   登录 / 登出
══════════════════════════════════════════════ */
async function doLogin() {
  const user = document.getElementById("login-user").value.trim();
  const pass = document.getElementById("login-pass").value;
  const errEl = document.getElementById("login-err");
  errEl.textContent = "";
  if (!user || !pass) { errEl.textContent = "请填写用户名和密码"; return; }

  try {
    const fd = new FormData();
    fd.append("username", user);
    fd.append("password", pass);
    const resp = await fetch(`${BASE}/auth/login`, { method:"POST", body:fd });
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    _token = data.access_token || "";
    if (!_token) throw new Error("未返回 token");

    // 持久化（localStorage+sessionStorage）
    setToken(_token);
    sessionStorage.setItem("access_token", _token);

    // 验证是否管理员
    const me = await fetch(`${BASE}/auth/me`, { headers: authHeaders() });
    if (!me.ok) throw new Error("获取用户信息失败");
    const meData = await me.json();
    if (!meData.is_admin) {
      _token = "";
      sessionStorage.removeItem("access_token");
      throw new Error("当前账号不是管理员，无法访问后台");
    }

    document.getElementById("hdr-username").textContent = meData.username || meData.email || "管理员";
    document.getElementById("logout-btn").style.display = "";
    document.getElementById("login-panel").style.display = "none";
    document.getElementById("admin-main").style.display = "";
    loadStats();
  } catch(e) {
    errEl.textContent = `登录失败: ${e.message}`;
  }
}

function doLogout() {
  _token = "";
  clearToken();
  sessionStorage.removeItem("access_token");
  document.getElementById("login-panel").style.display = "flex";
  document.getElementById("admin-main").style.display = "none";
  document.getElementById("hdr-username").textContent = "未登录";
  document.getElementById("logout-btn").style.display = "none";
}

// 页面加载时检查已有 token
(async function autoLogin() {
  const saved = sessionStorage.getItem("access_token") || localStorage.getItem("access_token");
  if (!saved) return;
  _token = saved;
  try {
    const me = await fetch(`${BASE}/auth/me`, { headers: authHeaders() });
    if (!me.ok) throw new Error("token 过期");
    const meData = await me.json();
    if (!meData.is_admin) throw new Error("非管理员");
    document.getElementById("hdr-username").textContent = meData.username || meData.email || "管理员";
    document.getElementById("logout-btn").style.display = "";
    document.getElementById("login-panel").style.display = "none";
    document.getElementById("admin-main").style.display = "";
    loadStats();
  } catch {
    _token = "";
    sessionStorage.removeItem("access_token");
  }
})();

// 回车登录
document.addEventListener("keydown", e => {
  if (e.key === "Enter" && document.getElementById("login-panel").style.display !== "none") {
    doLogin();
  }
  if (e.key === "Escape") closeGlossModal();
});

/* ══════════════════════════════════════════════
   Tab 切换
══════════════════════════════════════════════ */
function switchAdmTab(name, btn) {
  const tabs = ["stats", "events", "glossary", "audit", "cases"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    if (el) el.style.display = t === name ? "" : "none";
  });
  document.querySelectorAll(".adm-tab").forEach(b => b.classList.remove("act"));
  if (btn) btn.classList.add("act");
  // Tab 滑动指示器
  const tabsEl = document.querySelector('.adm-tabs');
  if (tabsEl && btn) {
    tabsEl.style.setProperty('--tab-x', btn.offsetLeft + 'px');
    tabsEl.style.setProperty('--tab-w', btn.offsetWidth + 'px');
  }

  // 懒加载
  switch (name) {
    case "events":    loadEventStats(); loadEvents();    break;
    case "glossary":  loadGlossary();                   break;
    case "audit":     loadAuditLogs();                  break;
    case "cases":     loadGoldenCases();                break;
  }
}

/* ══════════════════════════════════════════════
   系统统计  GET /api/v1/admin/stats
══════════════════════════════════════════════ */
async function loadStats() {
  const grid = document.getElementById("stats-grid");
  grid.innerHTML = `<div class="stat-loading">加载中…</div>`;
  try {
    const resp = await fetch(`${BASE}/admin/stats`, { headers: authHeaders() });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const d = await resp.json();
    renderStats(d);
  } catch(e) {
    grid.innerHTML = `<div class="stat-loading" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
  }
}

function renderStats(d) {
  const cards = [
    { lbl: "总用户",       val: d.total_users,            cls: "" },
    { lbl: "活跃用户",     val: d.active_users,           cls: "accent" },
    { lbl: "总案例",       val: d.total_cases,            cls: "accent2" },
    { lbl: "快照数",       val: d.total_snapshots,        cls: "" },
    { lbl: "审计日志",     val: d.total_audit_logs,       cls: "" },
    { lbl: "API Keys",     val: d.total_api_keys,         cls: "gold" },
    { lbl: "实验数",       val: d.total_experiments,      cls: "" },
    { lbl: "运行中实验",   val: d.running_experiments,    cls: "accent" },
  ];
  document.getElementById("stats-grid").innerHTML = cards.map(c =>
    `<div class="stat-card">
      <div class="stat-lbl">${esc(c.lbl)}</div>
      <div class="stat-val ${c.cls}">${c.val ?? "—"}</div>
    </div>`
  ).join("");

  // 审核状态
  const rv = d.review_stats || {};
  const extra = `
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:4px">
      ${[["待审核","pending","accent"],["通过","approved",""],["拒绝","rejected",""],["修改","revised","gold"]].map(([lbl,k,cls]) =>
        `<div class="stat-card">
           <div class="stat-lbl">图表审核·${lbl}</div>
           <div class="stat-val ${cls}">${d["review_"+k] ?? rv[k] ?? "—"}</div>
         </div>`
      ).join("")}
    </div>`;
  document.getElementById("stats-extra").innerHTML = extra;
}

/* ══════════════════════════════════════════════
   事件统计  GET /api/v1/events/stats
══════════════════════════════════════════════ */
async function loadEventStats() {
  const block = document.getElementById("events-stat-block");
  block.innerHTML = `<div class="empty-hint">加载中…</div>`;
  try {
    const resp = await fetch(`${BASE}/events/stats`, { headers: authHeaders() });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const d = await resp.json();
    renderEventStats(d);
  } catch(e) {
    block.innerHTML = `<div class="empty-hint" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
  }
}

function renderEventStats(d) {
  const stats = d.stats || d.distribution || d || {};
  const entries = Object.entries(stats).sort((a,b) => b[1] - a[1]);
  if (!entries.length) {
    document.getElementById("events-stat-block").innerHTML = `<div class="empty-hint">暂无事件统计</div>`;
    return;
  }
  const max = entries[0][1] || 1;
  const rows = entries.map(([type, cnt]) => {
    const pct = Math.round(cnt / max * 100);
    return `<tr>
      <td>${esc(type)}</td>
      <td>${cnt}</td>
      <td>
        <div class="ev-bar-wrap" style="width:${Math.max(40, Math.round(cnt/max*160))}px">
          <div class="ev-bar" style="width:${pct}%"></div>
        </div>
      </td>
    </tr>`;
  }).join("");
  document.getElementById("events-stat-block").innerHTML =
    `<table class="ev-stat-table">
       <thead><tr><th>事件类型</th><th>数量</th><th>分布</th></tr></thead>
       <tbody>${rows}</tbody>
     </table>`;
}

/* ══════════════════════════════════════════════
   事件列表  GET /api/v1/events
══════════════════════════════════════════════ */
async function loadEvents() {
  const q = document.getElementById("events-search")?.value?.trim() || "";
  const block = document.getElementById("events-list-block");
  block.innerHTML = `<div class="empty-hint">加载中…</div>`;
  try {
    const url = `${BASE}/events?limit=50${q ? "&event_type="+encodeURIComponent(q) : ""}`;
    const resp = await fetch(url, { headers: authHeaders() });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const d = await resp.json();
      const items = Array.isArray(d.items)  ? d.items
                  : Array.isArray(d.events) ? d.events
                  : Array.isArray(d)        ? d : [];
    if (!items.length) { block.innerHTML = `<div class="empty-hint">暂无事件记录</div>`; return; }
    const rows = items.map(ev =>
      `<tr>
        <td>${esc(ev.event_type || ev.type || "—")}</td>
        <td>${esc(ev.created_at?.slice(0,19) || "—")}</td>
        <td>${esc(ev.member_id || ev.user_id || "—")}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(JSON.stringify(ev.payload || ev.data || {}))}</td>
      </tr>`
    ).join("");
    block.innerHTML =
      `<table class="ev-stat-table">
         <thead><tr><th>类型</th><th>时间</th><th>用户</th><th>数据</th></tr></thead>
         <tbody>${rows}</tbody>
       </table>`;
  } catch(e) {
    block.innerHTML = `<div class="empty-hint" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
  }
}

/* ══════════════════════════════════════════════
   词汇管理  GET/PUT /api/v1/glossary
══════════════════════════════════════════════ */
let _glossOffset = 0;
const _GLOSS_PAGE = 50;

async function loadGlossary(append = false) {
  const q = document.getElementById("gloss-search")?.value?.trim() || "";
  const block = document.getElementById("glossary-block");
  const moreWrap = document.getElementById("gloss-more-wrap");
  const moreBtn  = document.getElementById("gloss-load-more");
  if (!append) {
    _glossOffset = 0;
    block.innerHTML = `<div class="empty-hint">加载中…</div>`;
    if (moreWrap) moreWrap.style.display = "none";
  } else {
    if (moreBtn) { moreBtn.disabled = true; moreBtn.textContent = "加载中…"; }
  }
  try {
    const url = `${BASE}/glossary?limit=${_GLOSS_PAGE}&offset=${_glossOffset}${q ? "&q="+encodeURIComponent(q) : ""}`;
    const resp = await fetch(url);  // 无需认证
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    // 兼容旧版返回数组 / 新版返回 {items,total}
    const items  = Array.isArray(data) ? data : (data.items || data);
    const total  = data.total != null ? data.total : null;

    if (!append) {
      _glossaryData = items;
      if (!items.length) {
        block.innerHTML = `<div class="empty-hint">暂无词汇</div>`;
        if (moreWrap) moreWrap.style.display = "none";
        return;
      }
      const hdrId = "gloss-hdr-label";
      const rows = buildGlossRows(items);
      block.innerHTML =
        `<div id="${hdrId}" style="font-size:.76rem;color:var(--muted);margin-bottom:8px">已加载 ${items.length}${total != null ? "/"+total : ""} 条词汇</div>
         <table class="gloss-table" id="gloss-table">
           <thead><tr><th>术语</th><th>分类</th><th>定义</th><th>操作</th></tr></thead>
           <tbody id="gloss-tbody">${rows}</tbody>
         </table>`;
    } else {
      _glossaryData = (_glossaryData || []).concat(items);
      const tbody = document.getElementById("gloss-tbody");
      if (tbody) tbody.insertAdjacentHTML("beforeend", buildGlossRows(items));
      const hdr = document.getElementById("gloss-hdr-label");
      if (hdr) hdr.textContent = `已加载 ${_glossaryData.length}${total != null ? "/"+total : ""} 条词汇`;
    }
    _glossOffset += items.length;
    const hasMore = items.length === _GLOSS_PAGE && (total == null || _glossOffset < total);
    if (moreWrap) {
      moreWrap.style.display = hasMore ? "block" : "none";
      if (moreBtn) { moreBtn.disabled = false; moreBtn.textContent = "⬇ 加载更多词汇"; }
    }
  } catch(e) {
    if (!append) block.innerHTML = `<div class="empty-hint" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
    else if (moreBtn) { moreBtn.disabled = false; moreBtn.textContent = "⬇ 加载更多词汇（重试）"; }
  }
}

function buildGlossRows(items) {
  return items.map(item =>
    `<tr>
      <td class="gloss-term">${esc(item.term)}</td>
      <td><span class="gloss-cat">${esc(item.category || "—")}</span></td>
      <td class="gloss-def-cell">${esc(item.definition || "—")}</td>
      <td><button class="btn-edit" onclick="openGlossEdit(${JSON.stringify(JSON.stringify(item))})">编辑</button></td>
    </tr>`
  ).join("");
}



function openGlossEdit(jsonStr) {
  const item = JSON.parse(jsonStr);
  _editingTerm = item.term;
  document.getElementById("edit-term").value = item.term || "";
  document.getElementById("edit-def").value  = item.definition || "";
  document.getElementById("edit-cat").value  = item.category || "";
  document.getElementById("gloss-edit-err").textContent = "";
  document.getElementById("gloss-modal").style.display = "flex";
  document.getElementById("gloss-overlay").style.display = "block";
  document.getElementById("edit-def").focus();
}

function closeGlossModal() {
  document.getElementById("gloss-modal").style.display = "none";
  document.getElementById("gloss-overlay").style.display = "none";
}

async function saveGlossaryEdit() {
  const def = document.getElementById("edit-def").value.trim();
  const cat = document.getElementById("edit-cat").value.trim();
  const errEl = document.getElementById("gloss-edit-err");
  errEl.textContent = "";
  if (!def) { errEl.textContent = "定义不能为空"; return; }

  try {
    const resp = await fetch(`${BASE}/glossary/${encodeURIComponent(_editingTerm)}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ definition: def, category: cat || undefined }),
    });
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.detail || `HTTP ${resp.status}`);
    }
    closeGlossModal();
    showToast(`✅ 词汇"${_editingTerm}"已更新`, 2500);
    loadGlossary();
  } catch(e) {
    errEl.textContent = `保存失败: ${e.message}`;
  }
}

/* ══════════════════════════════════════════════
   审计日志  GET /api/v1/audit-logs/admin
══════════════════════════════════════════════ */
let _auditOffset = 0;
const _AUDIT_PAGE = 50;

async function loadAuditLogs(append = false) {
  if (!append) {
    _auditOffset = 0;
    document.getElementById('audit-block').innerHTML = `<div class="empty-hint">加载中…</div>`;
    document.getElementById('audit-more-wrap').style.display = 'none';
  }
  const block = document.getElementById('audit-block');
  const moreBtn = document.getElementById('audit-load-more');
  if (moreBtn) moreBtn.disabled = true;
  try {
    const resp = await fetch(
      `${BASE}/audit-logs/admin?limit=${_AUDIT_PAGE}&offset=${_auditOffset}`,
      { headers: authHeaders() }
    );
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const d = await resp.json();
    const items = d.items || d.logs || (Array.isArray(d) ? d : []);
    const total = d.total ?? items.length;

    if (!append && !items.length) {
      block.innerHTML = `<div class="empty-hint">暂无审计日志</div>`;
      return;
    }

    const rows = items.map(log =>
      `<tr>
        <td>${esc(log.created_at?.slice(0,19) || '—')}</td>
        <td><span class="audit-action">${esc(log.action || '—')}</span></td>
        <td>${esc(log.actor_id || log.user_id || '—')}</td>
        <td>${esc(log.resource_type || '—')}</td>
        <td>${esc(log.resource_id || '—')}</td>
        <td title="${esc(JSON.stringify(log.detail || {}))}">${esc(log.ip || '—')}</td>
      </tr>`
    ).join('');

    if (!append) {
      block.innerHTML =
        `<table class="audit-table" id="audit-table">
           <thead><tr><th>时间</th><th>操作</th><th>用户</th><th>资源类型</th><th>资源ID</th><th>IP</th></tr></thead>
           <tbody id="audit-tbody">${rows}</tbody>
         </table>`;
    } else {
      const tbody = document.getElementById('audit-tbody');
      if (tbody) tbody.insertAdjacentHTML('beforeend', rows);
    }

    _auditOffset += items.length;
    const loaded = _auditOffset;
    const label = document.getElementById('audit-hdr-label');
    if (label) label.textContent = total > loaded
      ? `审计日志（已加载 ${loaded} / ${total} 条）`
      : `审计日志（共 ${loaded} 条）`;

    const moreWrap = document.getElementById('audit-more-wrap');
    if (moreWrap) moreWrap.style.display = (items.length === _AUDIT_PAGE && _auditOffset < total) ? '' : 'none';
  } catch(e) {
    if (!append) block.innerHTML = `<div class="empty-hint" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
  } finally {
    if (moreBtn) moreBtn.disabled = false;
  }
}

/* ══════════════════════════════════════════════
   黄金案例  GET /api/v1/bazi/golden-cases
══════════════════════════════════════════════ */
async function loadGoldenCases() {
  const block = document.getElementById("golden-cases-block");
  block.innerHTML = `<div class="empty-hint">加载中…</div>`;
  try {
    // 尝试 /bazi/golden-cases 端点，若不存在则降级为 /cases
    let resp = await fetch(`${BASE}/bazi/golden-cases?limit=50`, { headers: authHeaders() });
    if (resp.status === 404 || resp.status === 405) {
      resp = await fetch(`${BASE}/cases?limit=50`, { headers: authHeaders() });
    }
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const d = await resp.json();
    const items = d.items || d.cases || d || [];
    if (!items.length) { block.innerHTML = `<div class="empty-hint">暂无案例</div>`; return; }
    const rows = items.map(c =>
      `<tr>
        <td style="font-size:.72rem;font-family:monospace">${esc((c.id || c.case_id || "").slice(0,12))}…</td>
        <td>${esc(c.birth_dt_local || "—")}</td>
        <td>${esc(c.gender === "male" ? "男" : c.gender === "female" ? "女" : "—")}</td>
        <td>${esc(c.lon ?? "—")}</td>
        <td>${esc(c.note || c.label || "—")}</td>
        <td>${esc(c.created_at?.slice(0,10) || "—")}</td>
      </tr>`
    ).join("");
    block.innerHTML =
      `<div style="font-size:.76rem;color:var(--muted);margin-bottom:8px">共 ${items.length} 条案例</div>
       <table class="gc-table">
         <thead><tr><th>ID</th><th>出生时间</th><th>性别</th><th>经度</th><th>备注</th><th>创建日</th></tr></thead>
         <tbody>${rows}</tbody>
       </table>`;
  } catch(e) {
    block.innerHTML = `<div class="empty-hint" style="color:#b91c1c">加载失败: ${esc(e.message)}</div>`;
  }
}

/* —— P3.2: 向 window 显式暴露 HTML onclick 依赖的函数 —— */
window.switchAdmTab      = switchAdmTab;
window.doLogin           = doLogin;
window.doLogout          = doLogout;
window.loadStats         = loadStats;
window.loadEvents        = loadEvents;
window.loadEventStats    = loadEventStats;
window.loadGlossary      = loadGlossary;
window.loadGoldenCases   = loadGoldenCases;
window.loadAuditLogs     = loadAuditLogs;
window.openGlossEdit     = openGlossEdit;
window.closeGlossModal   = closeGlossModal;
window.saveGlossaryEdit  = saveGlossaryEdit;

}()); // end IIFE
