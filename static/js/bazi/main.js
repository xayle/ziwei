/**
 * 八字排盘 — main.js
 * API base: /api/v1
 * 依赖：/static/js/auth.js（全局 getToken / setToken / clearToken）
 * P3.2: 所有内部实现封装在 IIFE 中；
 *       HTML onclick 依赖的函数通过 window.X = X 显式暴露
 */

"use strict";

(function () {

/* ══════════════════════════════════════════════
   全局状态
══════════════════════════════════════════════ */
let _lastResult = null;   // 最新 /bazi/full 响应
let _lastCaseId = null;   // 保存成功后的 case_id
const BASE = "/api/v1";

/* ══════════════════════════════════════════════
   工具函数
══════════════════════════════════════════════ */
let _toastTimer = null;
function showToast(msg, duration = 2600) {
  const el = document.getElementById("bazi-toast");
  if (!el) return;
  el.textContent = msg;
  clearTimeout(_toastTimer);
  el.classList.add("show");
  _toastTimer = setTimeout(() => el.classList.remove("show"), duration);
}

function setBusy(busy) {
  const btn  = document.getElementById("calc-btn");
  const txt  = document.getElementById("calc-btn-text");
  const ldg  = document.getElementById("calc-loading");
  if (!btn) return;
  btn.disabled = busy;
  txt.style.display = busy ? "none" : "";
  ldg.style.display = busy ? "" : "none";
}

function setErr(msg) {
  const el = document.getElementById("calc-err");
  if (el) el.textContent = msg || "";
}

function authHeaders() {
  const t = getToken();
  return t ? { "Authorization": `Bearer ${t}`, "Content-Type": "application/json" }
           : { "Content-Type": "application/json" };
}

/* ══════════════════════════════════════════════
   表单值读取
══════════════════════════════════════════════ */
function getFormValues() {
  const dtRaw = document.getElementById("birth-dt").value;
  if (!dtRaw) return null;
  const lon   = parseFloat(document.getElementById("lon").value);
  const tz    = document.getElementById("tz").value;
  const mode  = document.querySelector('input[name="mode"]:checked')?.value || "dual";
  const genderEl = document.querySelector('input[name="gender"]:checked');
  const gender = genderEl ? genderEl.value : "";
  const solar = document.getElementById("solar-time").checked;

  // datetime-local → ISO 8601（补 :00 保证秒字段完整）
  const dt = dtRaw.length === 16 ? dtRaw + ":00" : dtRaw;

  return { dt, lon, tz, mode, gender: gender || undefined, solar_time_enabled: solar };
}

/* ══════════════════════════════════════════════
   主计算函数
══════════════════════════════════════════════ */
async function doCalculate() {
  setErr("");
  const vals = getFormValues();
  if (!vals) { setErr("请填写出生日期时间"); return; }
  if (isNaN(vals.lon) || vals.lon < 73 || vals.lon > 135.1) {
    setErr("经度范围 73.0 ~ 135.1"); return;
  }

  setBusy(true);
  // 骨架屏：API 核心请求期间展示㘊  const resultArea = document.getElementById('result-area');
  if (resultArea) {
    resultArea.innerHTML = '<div style="padding:24px"><div class="skel-line" style="width:60%"></div><div class="skel-line" style="width:80%"></div><div class="skel-line" style="width:45%"></div><div class="skel-box" style="height:80px;margin-top:16px"></div></div>';
    resultArea.style.display = '';
  }
  try {
    const body = {
      dt:                  vals.dt,
      lon:                 vals.lon,
      tz:                  vals.tz,
      mode:                vals.mode,
      solar_time_enabled:  vals.solar_time_enabled,
    };
    if (vals.gender) body.gender = vals.gender;

    const resp = await fetch(`${BASE}/bazi/full`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    _lastResult = data;
    _lastCaseId = null;
    renderResult(data);
    document.getElementById("result-area").style.display = "";
  } catch (e) {
    setErr(`计算失败: ${e.message}`);
    showToast(`❌ ${e.message}`, 3500);
  } finally {
    setBusy(false);
  }
}

/* ══════════════════════════════════════════════
   渲染结果
══════════════════════════════════════════════ */
function renderResult(d) {
  renderPillars(d);
  renderOverview(d);
  renderDayun(d);
  renderLiunian(d);
  renderWuxing(d);
  renderRuleMatches(d);
  document.getElementById("raw-json").textContent = JSON.stringify(d, null, 2);
  switchTab("overview", document.querySelector('.res-tab[data-tab="overview"]'));
}

/* ── 四柱宫格 ─────────────────────────────── */
function renderPillars(d) {
  const pp = d.pillars_primary;
  if (!pp) return;
  const cols = [
    { lbl: "年柱", data: pp.year },
    { lbl: "月柱", data: pp.month },
    { lbl: "日柱", data: pp.day, isDay: true },
    { lbl: "时柱", data: pp.hour },
  ];
  const tg = d.ten_gods || {};

  const html = `<div class="pillars-table">` +
    cols.map(({ lbl, data, isDay }) => {
      if (!data) return `<div class="pillar-col"><div class="pillar-lbl">${lbl}</div><div class="pillar-stem pillar-empty">？</div><div class="pillar-branch pillar-empty">？</div></div>`;
      const shishen = isDay ? "日元" : (tg[lbl.replace("柱","").toLowerCase()] || "");
      return `<div class="pillar-col${isDay ? " day" : ""}">
        <div class="pillar-lbl">${lbl}</div>
        <div class="pillar-stem">${data.stem || "?"}</div>
        <div class="pillar-branch">${data.branch || "?"}</div>
        <div class="pillar-shishen">${shishen}</div>
      </div>`;
    }).join("") + `</div>`;

  document.getElementById("pillars-block").innerHTML = html;

  // 元数据行
  const m = d.methods || {};
  const meta = [
    m.solar_date   ? `阳历 <span>${m.solar_date}</span>` : "",
    m.lunar_date   ? `农历 <span>${m.lunar_date}</span>` : "",
    m.solar_time_rule ? `太阳时 <span>${m.solar_time_rule}</span>` : "",
    d.start_dayun_age != null ? `起运年龄 <span>${d.start_dayun_age} 岁</span>` : "",
  ].filter(Boolean).map(s => `<span class="meta-item">${s}</span>`).join("");
  document.getElementById("pillars-meta").innerHTML = meta;
}

/* ── 综合概览 ─────────────────────────────── */
function renderOverview(d) {
  // 用神/忌神
  const ys = d.yongshen;
  if (ys) {
    const favor  = (ys.favor  || []).map(t => `<span class="tag tag-favor">${t}</span>`).join(" ");
    const neutral= (ys.neutral|| []).map(t => `<span class="tag tag-neutral">${t}</span>`).join(" ");
    const avoid  = (ys.avoid  || []).map(t => `<span class="tag tag-avoid">${t}</span>`).join(" ");
    document.getElementById("ov-yongshen-body").innerHTML =
      `<div>${favor}${avoid}${neutral}</div>` +
      (ys.summary ? `<div style="font-size:.76rem;color:var(--muted);margin-top:4px">${ys.summary}</div>` : "");
  }

  // 日元强弱
  const dms = d.day_master_strength;
  if (dms) {
    document.getElementById("ov-strength-body").innerHTML =
      `<div><b>${dms.label || dms.strength || ""}</b></div>` +
      `<div style="font-size:.76rem;color:var(--muted)">${dms.score != null ? `分值: ${dms.score}` : ""}</div>`;
  }

  // 格局
  const gj = d.geju;
  if (gj) {
    document.getElementById("ov-geju-body").innerHTML =
      `<div><b>${gj.name || "—"}</b></div>` +
      `<div style="font-size:.76rem;color:var(--muted)">${gj.description || ""}</div>`;
  }

  // 命宫/胎元
  const palace = d.palace;
  if (palace) {
    document.getElementById("ov-palace-body").innerHTML =
      `<div>命宫：<b>${palace.ming_gong || "—"}</b></div>` +
      `<div>胎元：<b>${palace.tai_yuan || "—"}</b></div>`;
  }

  // 神煞
  const ss = d.shensha;
  if (ss && ss.length) {
    const tags = ss.map(s => `<span class="tag tag-gold">${s.name}</span>`).join(" ");
    document.getElementById("ov-shensha").innerHTML =
      `<div class="shensha-block"><div class="shensha-title">神煞</div><div class="shensha-list">${tags}</div></div>`;
  }

  // 人生弧线/命运说明
  const la = d.life_arc;
  if (la) {
    document.getElementById("ov-life-arc").innerHTML =
      `<div class="life-arc-block"><div class="life-arc-title">命运概说</div><div class="life-arc-body">${la.summary || ""}</div></div>`;
  }
}

/* ── 大运 ─────────────────────────────────── */
function renderDayun(d) {
  const dy = d.dayun;
  if (!dy) { document.getElementById("dayun-block").innerHTML = "<p>暂无大运数据</p>"; return; }

  const startAge = d.start_dayun_age != null
    ? `<div class="dayun-start-age">起运年龄：${d.start_dayun_age} 岁</div>` : "";

  const now = new Date().getFullYear();
  const cycles = dy.cycles || [];
  const items = cycles.map(c => {
    const isCur = c.start_year <= now && (c.end_year == null || c.end_year >= now);
    return `<div class="dayun-item${isCur ? " cur" : ""}">
      <div class="dayun-gz">${c.ganzhi || "?"}</div>
      <div class="dayun-age">${c.start_age || ""}岁</div>
      <div class="dayun-meta">${c.start_year || ""}年</div>
    </div>`;
  }).join("");

  document.getElementById("dayun-block").innerHTML =
    startAge + `<div class="dayun-list">${items || "<p>暂无大运数据</p>"}</div>`;
}

/* ── 流年 ─────────────────────────────────── */
function renderLiunian(d) {
  const ly = d.liunian;
  if (!ly) { document.getElementById("liunian-block").innerHTML = ""; return; }

  const rows = (ly.years || []).map(y =>
    `<tr>
      <td>${y.year || ""}</td>
      <td>${y.ganzhi || ""}</td>
      <td>${y.overall_score != null ? y.overall_score : "—"}</td>
      <td>${y.summary || "—"}</td>
    </tr>`
  ).join("");

  document.getElementById("liunian-block").innerHTML = rows
    ? `<table class="liunian-table">
        <thead><tr><th>年份</th><th>干支</th><th>综合分</th><th>概述</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`
    : `<p style="color:var(--muted);font-size:.84rem">暂无流年详情（可在综合概览查看）</p>`;
}

/* ── 五行图表 ─────────────────────────────── */
function renderWuxing(d) {
  const wx = d.wuxing_score;
  if (!wx) { document.getElementById("wuxing-block").innerHTML = "<p>暂无五行数据</p>"; return; }

  const ELEMENTS = [
    { key: "wood",  lbl: "木", cls: "wx-wood" },
    { key: "fire",  lbl: "火", cls: "wx-fire" },
    { key: "earth", lbl: "土", cls: "wx-earth" },
    { key: "metal", lbl: "金", cls: "wx-metal" },
    { key: "water", lbl: "水", cls: "wx-water" },
  ];
  const total = ELEMENTS.reduce((s, e) => s + (parseFloat(wx[e.key]) || 0), 0) || 1;

  const rows = ELEMENTS.map(({ key, lbl, cls }) => {
    const val = parseFloat(wx[key]) || 0;
    const pct = Math.round(val / total * 100);
    return `<div class="wx-row ${cls}">
      <div class="wx-lbl">${lbl}</div>
      <div class="wx-bar-wrap"><div class="wx-bar" style="width:${pct}%"></div></div>
      <div class="wx-val">${val.toFixed(1)}（${pct}%）</div>
    </div>`;
  }).join("");

  // 五行细分（wuxing_breakdown）
  const brk = d.wuxing_breakdown;
  let brkHtml = "";
  if (brk) {
    brkHtml = `<div style="margin-top:16px;font-size:.78rem;color:var(--muted)">
      <div style="font-weight:600;margin-bottom:8px">五行细分占比</div>
      ${Object.entries(brk).map(([k, v]) =>
        `<span class="tag tag-neutral">${k}: ${typeof v === "number" ? v.toFixed(2) : v}</span>`
      ).join("")}
    </div>`;
  }

  document.getElementById("wuxing-block").innerHTML =
    `<div class="wuxing-grid">${rows}</div>${brkHtml}`;
}

/* ══════════════════════════════════════════════
   流年分域查询（/bazi/liunian-domain）
══════════════════════════════════════════════ */
async function fetchLiunianDomain() {
  if (!_lastCaseId) {
    showToast("请先保存案例，再查询流年分域", 3000);
    return;
  }
  const year = parseInt(document.getElementById("liunian-year").value);
  if (isNaN(year)) { showToast("请填写有效年份"); return; }

  const block = document.getElementById("liunian-domain-block");
  block.innerHTML = `<div style="color:var(--muted);font-size:.84rem;padding:10px 0">查询中…</div>`;

  try {
    const resp = await fetch(`${BASE}/bazi/liunian-domain`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ case_id: _lastCaseId, year }),
    });
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    renderLiunianDomain(data);
  } catch (e) {
    block.innerHTML = `<div class="err-msg">查询失败: ${e.message}</div>`;
  }
}

function renderLiunianDomain(data) {
  const domains = data.domains || {};
  const gz = data.year_ganzhi || "";
  const cards = Object.entries(domains).map(([k, v]) =>
    `<div class="domain-card">
      <div class="domain-name">${k}</div>
      <div class="domain-val">${v}</div>
    </div>`
  ).join("");

  document.getElementById("liunian-domain-block").innerHTML =
    `<div style="font-size:.84rem;color:var(--muted);margin-bottom:6px">
       ${data.year || ""} 年（${gz}年）流年分域预测
     </div>
     <div class="liunian-domain-grid">${cards}</div>`;
}

/* ══════════════════════════════════════════════
   规则匹配渲染（rule_matches bazi_full@5.1）
══════════════════════════════════════════════ */
function renderRuleMatches(d) {
  const matches = d.rule_matches || [];

  // overview 规则摘要栏
  const summaryEl = document.getElementById("ov-rule-summary");
  if (summaryEl) {
    if (matches.length) {
      summaryEl.innerHTML =
        `<div class="rule-summary-bar">
          <strong>规则引擎：</strong>命中 ${matches.length} 条规则（${matches.slice(0,3).map(r => r.name).join("、")}${matches.length > 3 ? "等" : ""}）
          <button class="rule-summary-toggle" onclick="switchTab('ai', document.querySelector('.res-tab[data-tab=ai]'))">查看详情 →</button>
        </div>`;
    } else {
      summaryEl.innerHTML = "";
    }
  }

  // AI Tab 内详细列表
  const listEl = document.getElementById("ai-rule-matches");
  if (!listEl) return;
  if (!matches.length) {
    listEl.innerHTML = `<div class="rule-match-empty">未命中任何规则（该命盘格局/用神信息待计算）</div>`;
    return;
  }

  listEl.innerHTML = `<div class="rule-match-list">` +
    matches.map(rm => `
      <div class="rule-match-item">
        <div class="rule-match-header">
          <span class="rule-match-name">${rm.name || ""}</span>
          <span class="rule-match-id">${rm.rule_id || ""}</span>
          ${rm.classic_hint ? `<span class="rule-match-classic">《${rm.classic_hint}》</span>` : ""}
        </div>
        <div class="rule-match-text">${rm.evidence_text || ""}</div>
        ${(rm.flags || []).length ? `<div class="rule-match-flags">${(rm.flags).map(f => `<span class="rule-match-flag">${f}</span>`).join("")}</div>` : ""}
        ${rm.disclaimer ? `<div class="rule-match-disclaimer">${rm.disclaimer}</div>` : ""}
      </div>`
    ).join("") + `</div>`;
}

/* ══════════════════════════════════════════════
   AI解读（POST /api/v1/llm/interpret-bazi）
══════════════════════════════════════════════ */
async function doInterpretBazi() {
  if (!_lastCaseId) {
    showToast("请先保存案例，再生成 AI 解读", 3000);
    return;
  }

  const btnEl    = document.getElementById("ai-gen-btn");
  const statusEl = document.getElementById("ai-status");
  const resultEl = document.getElementById("ai-result");
  const metaEl   = document.getElementById("ai-result-meta");
  const moduleVal = document.getElementById("ai-module-sel")?.value || "";

  btnEl.disabled = true;
  statusEl.textContent = "⏷ 生成中，请稍候…";
  resultEl.style.display = "none";
  metaEl.style.display = "none";

  try {
    const body = { case_id: _lastCaseId };
    if (moduleVal) body.module = moduleVal;

    const resp = await fetch(`${BASE}/llm/interpret-bazi`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(body),
    });

    if (resp.status === 401) {
      statusEl.textContent = "";
      showToast("请先登录账号", 3000);
      return;
    }
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.detail || `HTTP ${resp.status}`);
    }

    const draft = await resp.json();

    // 渲染解读文本（段落分隔）
    const text = draft.draft_text || "";
    resultEl.innerHTML = text
      .split(/\n{2,}/)
      .map(p => p.trim())
      .filter(Boolean)
      .map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`)
      .join("");
    resultEl.style.display = "";

    // 元信息栏
    metaEl.innerHTML = [
      draft.provider       ? `<span>🤖 ${draft.provider}</span>` : "",
      draft.model          ? `<span>📌 ${draft.model}</span>` : "",
      draft.prompt_version ? `<span><span class="ai-schema-badge">${draft.prompt_version}</span></span>` : "",
      draft.status         ? `<span>状态: ${draft.status}</span>` : "",
      (draft.input_tokens || draft.output_tokens)
        ? `<span>开销: ${draft.input_tokens || 0}in / ${draft.output_tokens || 0}out tokens</span>` : "",
    ].filter(Boolean).join("");
    metaEl.style.display = "";

    statusEl.textContent = "✔ 生成完成";
    setTimeout(() => { statusEl.textContent = ""; }, 3000);

  } catch (e) {
    statusEl.textContent = `❌ 失败: ${e.message}`;
    showToast(`AI解读失败: ${e.message}`, 4000);
  } finally {
    btnEl.disabled = false;
  }
}

/* ══════════════════════════════════════════════
   Tab 切换
══════════════════════════════════════════════ */
function switchTab(name, btn) {
  const tabs = ["overview", "dayun", "liunian", "wuxing", "ai", "raw"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    if (el) el.style.display = t === name ? "" : "none";
  });
  document.querySelectorAll(".res-tab").forEach(b => b.classList.remove("act"));
  if (btn) btn.classList.add("act");
  // Tab 滑动指示器
  const tabsEl = document.querySelector('.res-tabs');
  if (tabsEl && btn) {
    tabsEl.style.setProperty('--tab-x', btn.offsetLeft + 'px');
    tabsEl.style.setProperty('--tab-w', btn.offsetWidth + 'px');
  }
}

/* ══════════════════════════════════════════════
   案例保存（POST /cases）
══════════════════════════════════════════════ */
function openSaveModal() {
  if (!_lastResult) { showToast("请先完成排盘计算"); return; }
  document.getElementById("save-modal").style.display = "flex";
  document.getElementById("save-overlay").style.display = "block";
}

function closeSaveModal() {
  document.getElementById("save-modal").style.display = "none";
  document.getElementById("save-overlay").style.display = "none";
  document.getElementById("save-err").textContent = "";
}

/** 关闭所有面板 / 模态框（Escape 快捷键调用） */
function closePanels() {
  closeSaveModal();
}

async function doSaveCase() {
  const vals = getFormValues();
  if (!vals) return;
  const note = document.getElementById("save-note").value.trim();
  const errEl = document.getElementById("save-err");
  errEl.textContent = "";

  try {
    const resp = await fetch(`${BASE}/cases`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        birth_dt_local: vals.dt,
        lon: vals.lon,
        tz: vals.tz,
        gender: vals.gender || null,
        note: note || null,
      }),
    });
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({}));
      throw new Error(e.detail || `HTTP ${resp.status}`);
    }
    const saved = await resp.json();
    _lastCaseId = saved.id || saved.case_id || null;
    closeSaveModal();
    showToast("✅ 案例已保存！case_id: " + _lastCaseId, 3000);
    // 保存成功后启用 AI 解读按钮
    const aiBtn = document.getElementById("ai-gen-btn");
    if (aiBtn) aiBtn.disabled = false;
    const aiQuickBtn = document.getElementById("ai-quick-btn");
    if (aiQuickBtn) aiQuickBtn.style.display = "";
  } catch (e) {
    errEl.textContent = `保存失败: ${e.message}`;
  }
}

/* ══════════════════════════════════════════════
   表单重置
══════════════════════════════════════════════ */
function resetForm() {
  document.getElementById("birth-dt").value = "1990-01-15T08:30";
  document.getElementById("lon").value = "116.4";
  document.getElementById("tz").value = "Asia/Shanghai";
  document.querySelector('input[name="mode"][value="dual"]').checked = true;
  document.querySelector('input[name="gender"][value="male"]').checked = true;
  document.getElementById("solar-time").checked = false;
  document.getElementById("result-area").style.display = "none";
  setErr("");
  _lastResult = null;
  _lastCaseId = null;
  // 重置 AI 解读区
  const aiBtn = document.getElementById("ai-gen-btn");
  if (aiBtn) aiBtn.disabled = true;
  const aiQuickBtn = document.getElementById("ai-quick-btn");
  if (aiQuickBtn) aiQuickBtn.style.display = "none";
  const aiResultEl = document.getElementById("ai-result");
  if (aiResultEl) { aiResultEl.style.display = "none"; aiResultEl.innerHTML = ""; }
  const aiStatusEl = document.getElementById("ai-status");
  if (aiStatusEl) aiStatusEl.textContent = "";
}

/* ══════════════════════════════════════════════
   键盘快捷键
══════════════════════════════════════════════ */
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    doCalculate();
  }
  if (e.key === "Escape") {
    closePanels();
  }
});

/* —— P3.2: 向 window 显式显露 HTML onclick 依赖的函数 —— */
window.doCalculate       = doCalculate;
window.switchTab         = switchTab;
window.openSaveModal     = openSaveModal;
window.closeSaveModal    = closeSaveModal;
window.closePanels       = closePanels;
window.doSaveCase        = doSaveCase;
window.doInterpretBazi   = doInterpretBazi;
window.fetchLiunianDomain = fetchLiunianDomain;
window.resetForm         = resetForm;

}()); // end IIFE
