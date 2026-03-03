/**
 * docs/samples/js_v2_example.js
 * ───────────────────────────────
 * API v2 JavaScript 调用示例（Node.js >= 18 或现代浏览器）
 *
 * Node.js 运行：
 *   BASE_URL=http://localhost:8000 node docs/samples/js_v2_example.js
 *
 * 浏览器使用：将 BASE_URL 和 TOKEN 替换为实际值后直接调用各函数。
 */

const BASE_URL = (typeof process !== "undefined" && process.env.BASE_URL)
  || "http://localhost:8000";

const TOKEN = (typeof process !== "undefined" && process.env.API_TOKEN) || "";

const commonHeaders = {
  "Content-Type": "application/json",
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

// ─── 示例 1：v2 完整排盘（output_format=full）──────────────────────────────
async function exampleFullVerify() {
  console.log("\n[示例 1] POST /api/v2/verify  (output_format=full)");

  const payload = {
    dt: "1990-03-15T08:30:00",
    lon: 116.41,
    mode: "dual",
    solar_time_enabled: false,
    tz: "Asia/Shanghai",
    gender: "male",
    city_tier: "一线",
    industry: "金融IT",
    output_format: "full",
  };

  const res = await fetch(`${BASE_URL}/api/v2/verify`, {
    method: "POST",
    headers: commonHeaders,
    body: JSON.stringify(payload),
  });

  if (res.status === 501) {
    console.log("  ⚠️  v2 引擎未启用（ENGINE_V2=false）");
    return;
  }
  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After") || "60";
    console.log(`  ⚠️  频率超限，请 ${retryAfter} 秒后重试`);
    return;
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);

  const json = await res.json();
  const { meta, data } = json;

  console.log(`  api_version   : ${meta.api_version}`);
  console.log(`  engine_version: ${meta.engine_version}`);
  console.log(`  calc_ms       : ${meta.calc_ms} ms`);
  console.log(`  response_type : ${data.response_type}`);

  if (data.geju) {
    console.log(`  格局名称      : ${data.geju.geju_name}`);
    console.log(`  格局 confidence: ${data.geju.confidence}`);
  }
  if (data.yongshen) {
    console.log(`  用神          : ${JSON.stringify(data.yongshen.favor)}`);
  }
  if (data.pillars_primary?.day) {
    const d = data.pillars_primary.day;
    console.log(`  日柱          : ${d.stem}${d.branch}`);
  }
}

// ─── 示例 2：v2 精简排盘（output_format=minimal）──────────────────────────
async function exampleMinimalVerify() {
  console.log("\n[示例 2] POST /api/v2/verify  (output_format=minimal)");

  const payload = {
    dt: "1985-07-20T10:00:00",
    lon: 121.47,
    mode: "dual",
    solar_time_enabled: false,
    tz: "Asia/Shanghai",
    gender: "female",
    output_format: "minimal",
  };

  const res = await fetch(`${BASE_URL}/api/v2/verify`, {
    method: "POST",
    headers: commonHeaders,
    body: JSON.stringify(payload),
  });

  if (res.status === 501) { console.log("  ⚠️  v2 引擎未启用"); return; }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const json = await res.json();
  const { meta, data } = json;

  console.log(`  calc_ms       : ${meta.calc_ms} ms`);
  console.log(`  response_type : ${data.response_type}`);
  console.log(`  精简字段      : ${Object.keys(data).join(", ")}`);

  if (data.yongshen) console.log(`  用神: ${JSON.stringify(data.yongshen.favor)}`);
  if (data.dayun_current) {
    const dc = data.dayun_current;
    console.log(`  当前大运: ${dc.stem || ""}${dc.branch || ""} (起运${dc.start_age}岁)`);
  }
}

// ─── 示例 3：v2 批量排盘──────────────────────────────────────────────────
async function exampleBatchVerify() {
  console.log("\n[示例 3] POST /api/v2/batch/verify");

  const payload = {
    items: [
      { dt: "1990-01-01T08:00:00", lon: 116.41, tz: "Asia/Shanghai", gender: "male" },
      { dt: "1995-05-15T12:30:00", lon: 121.47, tz: "Asia/Shanghai", gender: "female" },
      { dt: "2000-12-31T23:30:00", lon: 104.06, tz: "Asia/Shanghai" },
    ],
  };

  const res = await fetch(`${BASE_URL}/api/v2/batch/verify`, {
    method: "POST",
    headers: commonHeaders,
    body: JSON.stringify(payload),
  });

  if (res.status === 422) {
    const body = await res.json();
    console.log(`  ⚠️  参数验证失败: ${JSON.stringify(body.detail)}`);
    return;
  }
  if (res.status === 429) {
    console.log(`  ⚠️  频率超限: Retry-After=${res.headers.get("Retry-After")}`);
    return;
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const { results, failed } = await res.json();
  console.log(`  成功 ${results.length} 条，失败 ${failed.length} 条`);

  results.forEach((r, i) => {
    const day = r.pillars_primary?.day || {};
    const geju = r.geju || {};
    console.log(`  [${i}] 日柱=${day.stem || "?"}${day.branch || "?"}  格局=${geju.geju_name || "?"}`);
  });
  failed.forEach((f) => console.log(`  [FAIL] index=${f.index}  error=${f.error}`));
}

// ─── 示例 4：CSV 行数超 50 时前端拦截（R39 验证）────────────────────────
async function exampleBatchOverLimit() {
  console.log("\n[示例 4] 超 50 条 → 期望 422 (R39)");

  const items = Array.from({ length: 51 }, (_, i) => ({
    dt: `2000-0${(i % 12) + 1}-01T08:00:00`.replace("-0", "-").replace(/-(\d)-/, "-0$1-"),
    lon: 116.41,
    tz: "Asia/Shanghai",
  }));
  // 简化 dt 构造
  const safeItems = items.map((_, i) => ({
    dt: "2000-01-01T08:00:00",
    lon: 116.41,
    tz: "Asia/Shanghai",
  }));

  const res = await fetch(`${BASE_URL}/api/v2/batch/verify`, {
    method: "POST",
    headers: commonHeaders,
    body: JSON.stringify({ items: safeItems }),
  });

  console.log(`  HTTP 状态: ${res.status} (期望 422)`);
  if (res.status === 422) {
    console.log("  ✅ 超限返回 422 验证通过（R39）");
  }
}

// ─── 示例 5：验证 v1 废弃响应头（R45）───────────────────────────────────
async function exampleCheckDeprecationHeader() {
  console.log("\n[示例 5] 验证 /api/v1/* 废弃响应头（R45）");

  const res = await fetch(`${BASE_URL}/api/v1/verify`, {
    method: "POST",
    headers: commonHeaders,
    body: JSON.stringify({ dt: "1990-01-01T08:00:00", lon: 116.41, tz: "Asia/Shanghai" }),
  });

  const deprecation = res.headers.get("Deprecation");
  const sunset = res.headers.get("Sunset");
  console.log(`  Deprecation: ${deprecation}`);
  console.log(`  Sunset     : ${sunset}`);

  if (deprecation === "true" && sunset === "2026-12-31") {
    console.log("  ✅ 废弃声明响应头验证通过");
  } else {
    console.log("  ❌ 响应头不符合预期");
  }
}

// ─── 主入口（Node.js）────────────────────────────────────────────────────
async function main() {
  console.log(`=== API v2 JS 示例（BASE_URL=${BASE_URL}) ===`);
  try {
    await exampleFullVerify();
    await exampleMinimalVerify();
    await exampleBatchVerify();
    await exampleBatchOverLimit();
    await exampleCheckDeprecationHeader();
    console.log("\n=== 全部示例执行完毕 ===");
  } catch (err) {
    console.error("运行出错:", err.message);
    process.exit(1);
  }
}

// Node.js 直接运行
if (typeof require !== "undefined" && require.main === module) {
  main();
}

// 浏览器 / 模块导出
if (typeof module !== "undefined") {
  module.exports = {
    exampleFullVerify,
    exampleMinimalVerify,
    exampleBatchVerify,
    exampleBatchOverLimit,
    exampleCheckDeprecationHeader,
  };
}
