# 浮生 · 界面与功能问题汇总

| 字段 | 内容 |
|------|------|
| **版本** | inv-1.25 |
| **日期** | 2026-07-15 |
| **定位** | 全路由界面 / 主功能错误清单 · 根因 · 解决方案 · 修复优先级 |
| **依据** | 路由通读 · FE 代码核对 · 实机 API 探针 · 二次深挖（auth/经度/权益/入口） |
| **关联** | [`DEV-AUDIT-2026-07-13.md`](../DEV-AUDIT-2026-07-13.md) · [`FE-BE-DECISIONS.md`](../plan/FE-BE-DECISIONS.md) · [`R102-product-rebuild-plan-2026-07-13.md`](R102-product-rebuild-plan-2026-07-13.md) · [`HUMAN-SIGNOFF-PACKET-2026-07-15.md`](HUMAN-SIGNOFF-PACKET-2026-07-15.md) |
| **机读对照** | autopilot 常绿 ≠ 无产品 bug；本清单补「静默降级 / 经度 / 入口 / 权益」层 |

> **一句话**：维护态；Trust 双轨标题与卷六/问书配置去 recorded·LLM 机读词。

### 本轮修复进度（inv-1.25）

| 批次 | 状态 | 已勾 ID |
|------|------|---------|
| inv-1.24 及前 | ✅ | 见上 |
| 维护 | ✅ 本批 | QA-01 Trust 双轨「古籍 vs 引擎」· 卷六/问书去 LLM |
| 仍开 | — | AUTH-01 · NAV-03 · **GTM 未开（R109 A）** |

---

## 一、界面矩阵（18 路由）

| 路由 | 界面 | 状态 | 关联问题 ID |
|------|------|------|-------------|
| `/` `/home` `/new` | 品牌首页 | 可用 | ✅ NAV-02 · ✅ NAV-03 |
| `/profile` | 档案 | 可用 | ✅ NAV-01 · ✅ TIME-01 · ✅ CITY-01 · ✅ STORAGE-01 · ✅ PROF-01 · ✅ ZW03-eng |
| `/new/bazi` | 八字 | 可用 | ✅ BZ-Month · ✅ MOBILE-01 · ✅ OPS-01 |
| `/new/ziwei` | 紫微 | 可用↑ | ✅ ZW-Adv · ✅ ZW-01 · ✅ ZW03-eng |
| `/new/ziwei/timeline` | 紫微运限 | 可用↑ | ✅ ZW-02 |
| `/report` | 六卷报告 | 可用↑ | ✅ REP-* · ✅ ENT-01 · ✅ NAME-01 · ✅ SHARE-01 · ✅ PDF-01 · ✅ RACE-01 · ✅ CASE-01 · ✅ REP-05 · ✅ VOL6 · ✅ BZ-Month · ✅ CNT（Adapter+远端） · ✅ ENT-demo · ✅ A11Y-01 |
| `/relation/new` | 关系合盘 | 可用↑ | ✅ EXT-02 · ✅ EXT-03 · ✅ REL-01 · ✅ NAV-04 |
| `/extensions` | 工具箱 | 可用↑ | ✅ EXT-05 · ✅ NAV-04 |
| `/extensions/compat` | 八字合婚（旧） | 可用↑ | ✅ EXT-01 |
| `/extensions/ziwei-compat` | 紫微合盘 | 可用↑ | ✅ ZW-03 · ✅ GENDER-01 |
| `/extensions/similarity` | 相似盘 | 可用↑ | ✅ EXT-04 |
| `/extensions/zeri` | 择日 | 可用 | — |
| `/login` | 登录 | 可用↑ | AUTH-01 · ✅ AUTH-05 · ✅ SHARE-03 |
| `/landing` | 抖音落地 | 可用↑ | ✅ CLIP-01 · ✅ SHARE-02 |
| `/payment/callback` | 支付回调 | 可用↑ | ✅ AUTH-02 |
| `*` | 404 | 可用 | ✅ ROUTE-01（入口已改 `/static/app/` + 旧路径 redirect） |

**后端静态入口**

| URL | 预期 | 实际 | ID |
|-----|------|------|-----|
| `/static/app/`（`spa_entry_url`） | SPA 主页 | ✅ 已改 | ~~ROUTE-01~~ |
| `/static/app/new/bazi` · `new/ziwei` | 旧别名落地 | ✅ `resolve_page_url` 映射 | ROUTE-01 |
| Vue `/cases` `/bazi` `/ziwei` `/admin` | 兼容书签 | ✅ router redirect | ROUTE-01 |

---

## 二、优先级总表

| 优先级 | 含义 | ID |
|--------|------|-----|
| **P0** | 错误结果 / 登录态假阳 / 主入口不可用 / 解锁可绕 | ✅ ROUTE-01 · ✅ AUTH-03 · ✅ TIME-01 · ✅ ENT-01 |
| **P1** | 结果偏、失败不可见、导航断链、合盘经度 | ✅ NAV-01 · ✅ ZW-03 · ✅ EXT-01 · ✅ EXT-02 · ✅ REP-01~03 · ✅ NAME-01 · ✅ SHARE-01 · ✅ PDF-01 · ✅ REL-01 · ✅ CASE-01 · ✅ RACE-01 · ✅ AUTH-04 · ✅ AUTH-05 |
| **P2** | 体验/文案/无障碍/内容厚度/环境债 | 见 §四；MR-E～H 与 BE CNT 已 ✅ |

建议 MR 切分（历史）：

1. ~~**MR-A 入口与时辰诚实**：ROUTE-01 · TIME-01~~ ✅  
2. ~~**MR-B Auth 真源**：AUTH-03 · AUTH-04 · AUTH-05~~ ✅  
3. ~~**MR-C 导航与合盘经度**：NAV-01 · ZW-03 · EXT-01 · REL-01~~ ✅  
4. ~~**MR-D 报告可信**：REP-01~03 · ENT-01 · PDF-01 · RACE-01~~ ✅  
5. ~~**MR-E 内容与打磨（代码）**：NAME-01 · CASE-01 · CITY/MOBILE/ZW/REP-05…~~ ✅  
6. ~~**MR-F 产品接线**：NAV-02 · BZ-Month · SHARE-02 · EXT-05~~ ✅  
7. ~~**MR-G 收尾**：REP-04 · CNT Adapter · ZW03 UI · A11Y · ENT-demo~~ ✅  
8. ~~**契约债**：X-01 · X-03 · TEST-01 · ROUTE-02 · R060 · R103~~ ✅ |

---

## 三、P0 明细（必先修）

| ID | 界面 | 现象 | 根因 | 解决方案 | 状态 |
|----|------|------|------|----------|------|
| **ROUTE-01** | 后端默认入口 | `spa_entry_url` 原指向 `/cases` → 404 | `static_entrypoints.py` | 改为 `/static/app/`；别名映射 + Vue redirect | ✅ |
| **AUTH-03** | 全局 | 401 清 LS 不清 Pinia | `client.ts` / `App.vue` | `clearToken` + `entitlement.reset`；refresh 同步 Pinia | ✅ |
| **TIME-01** | 档案未知时辰 | noon/midday 都成 12:30 | `buildChartRequests.ts` | noon→12:00，midday→12:30；单测锁定 | ✅ |
| **ENT-01** | 报告锁卷 | sandbox 失败仍 mockUnlock | `VolumePaywall.vue` | 已登录仅 purchase 成功才 emit | ✅ |

---

## 四、P1 / P2 明细（按域）

### 4.1 导航 / IA

| ID | Sev | 现象 | 解决方案 | 状态 |
|----|-----|------|----------|------|
| **NAV-01** | P1 | Shell 锁链无 redirect | `navTarget` 带 `reason/redirect` | ✅ |
| **NAV-02** | P2 | 首页六卷 ≠ 报告六卷 | 文案区分「排盘台/成书」+ lane 标记 | ✅ |
| **NAV-03** | P2 | 三入口同页 | canonical 标明为 `/`（`/home` `/new` 同页） | ☑ 文档 |
| **NAV-04** | P2 | 主壳无合盘入口 | Q18：合盘走「工具」→ 关系合盘；`/relation` 高亮工具 | ✅ |

### 4.2 Auth / 支付 / 存储

| ID | Sev | 现象 | 解决方案 | 状态 |
|----|-----|------|----------|------|
| **AUTH-01** | P2 | DEV 预填账号 | 保持 DEV only | ☑ 保持 |
| **AUTH-02** | P2 | 支付成功硬跳报告被踢 | 未齐档案 → profile+redirect | ✅ |
| **AUTH-04** | P1 | 并发 401 无单飞 | `refreshInFlight` Promise | ✅ |
| **AUTH-05** | P1 | 422 → `[object Object]` | `formatApiDetail` | ✅ |
| **SHARE-03** | P2 | login redirect 未校验 | 仅 `/` 且非 `//` | ✅ |
| **STORAGE-01** | P2 | 档案 JSON 损坏吞错 | 重置 + banner（`profile-storage-reset`） | ✅ |

### 4.3 八字 / 紫微 / 运限

| ID | Sev | 现象 | 解决方案 | 状态 |
|----|-----|------|----------|------|
| **BZ-Month** | P2 | monthly_fortune 未展示 | vol3 Adapter + 报告月运表 | ✅ |
| **REL-Combine** | P2 | 有拱合仍 missing `combine_summary` | `干支互动`+合类 summary → type=合 & 写入摘要 | ✅ |
| **ZW-03** | P1 | 对方经度=本人 | 对方经度输入 | ✅ |
| **ZW-Adv** | P2 | advisory 无横幅 | banner warn | ✅ |
| **ZW-01** | P2 | 双标题 | VolumeHead `titleTag=p`；节标题 h3 | ✅ |
| **ZW-02** | P2 | 大限高亮年可能错 | `dayunEndYear` + 年区间 | ✅ |
| **ZW03-eng** | P2 | 晚子时 vs iztro | 紫微页双轨表 + 档案口径提示 | ✅ |
| **GENDER-01** | P2 | UI 显示 male | 显示 男/女；缺性别拒跑 | ✅ |
| **OPS-01** | P2 | 后端未 reload | Shell banner 提示 `--reload` | ✅ |
| **Z-09-SC** | P2 | scorecard「太阳时未统一」 | `buildChartRequests` 恢复 `solarTime↔longitude` 耦合注释 | ✅ |
| **MOBILE-01** | P2 | 参考表窄屏难用 | DualTrack 横向滚动 + &lt;640 hint | ✅ |

### 4.4 报告 / 六卷 / 分享 / PDF

| ID | Sev | 现象 | 解决方案 | 状态 |
|----|-----|------|----------|------|
| **REP-01** | P1 | bundle 失败不回退 | compute fallback | ✅ |
| **REP-02** | P1 | explain 静默失败 | WithMeta + notice | ✅ |
| **REP-03** | P1 | volumes 静默 Adapter | degraded notice | ✅ |
| **REP-04** | P2 | 默认 Adapter | volumes API 默认开（可 LS/env 关） | ✅ |
| **REP-05** | P2 | readingFailed 语义 | 默认读法 note ≠ 加载失败 fallback | ✅ |
| **REP-Cite** | P2 | cite→inference | 去掉重映射 | ✅ |
| **NAME-01** | P1 | 姓名分析不渲染 | ReportView 五格面板 | ✅ |
| **SHARE-01** | P1 | 本地 UUID 当 caseId | 仅 remoteCaseId | ✅ |
| **SHARE-02** | P2 | H5 preview 未接线 | mint + landing 读 `?case_id&token` | ✅ |
| **CLIP-01** | P2 | 复制失败无提示 | `aria-live` + 失败文案 | ✅ |
| **PDF-01** | P1 | PDF 静默降级 | 可见 notice | ✅ |
| **RACE-01** | P1 | 换档不重生 | watch reload | ✅ |
| **CASE-01** | P1 | 快照签名错用 | `input_json.profile_signature` + 不一致清缓存 | ✅ |
| **CNT-01~03** | P2 | vol1/3/4 内容薄 | Adapter + 远端 `life_volume_service` 加厚；审计同源 API | ✅ FE+BE |
| **VOL6** | P2 | 问书空壳 | on-demand 说明文案 | ✅ |
| **ENT-demo** | P2 | Adapter 常全开 | demo lock → `volume.locked` | ✅ |

### 4.5 扩展 / 合盘

| ID | Sev | 现象 | 解决方案 | 状态 |
|----|-----|------|----------|------|
| **EXT-01** | P1 | 旧合婚无 lon/tz | 对方经度/时区字段 | ✅ |
| **EXT-02** | P1 | explain catch null | ResultStateCard | ✅ |
| **EXT-03** | P2 | lon 回落无提示 | fallback 提示 | ✅ |
| **EXT-04** | P2 | index 失败静默 | `similarity-index-notice` | ✅ |
| **REL-01** | P1 | multi lon 不对称 | ziwei 始终传 longitude | ✅ |
| **EXT-05** | P2 | Hub 标注清楚 | 权威/兼容/专项 badge | ✅ |

### 4.6 档案 / 城市 / A11y / 契约债

| ID | Sev | 现象 | 状态 |
|----|-----|------|------|
| **CITY-01** | P2 | 城市选择器 a11y / 经度精度 | ✅ |
| **PROF-01** | P2 | demo seed 工具函数闲置 | ✅ 档案页提示 |
| **A11Y-01** | P2 | 弹层焦点陷阱 | ✅ |
| **X-01** | P2 | 典籍 `source_page` FE 未展示 | ✅ 报告引用表 + cite meta |
| **X-03** | P2 | OpenAPI 测试只增不减 | ✅ `make sync-frontend-types` 注释约定 |
| **TEST-01** | P2 | 单测固化 volumes 联调假设 | ✅ `@debt` 标注 |
| **ROUTE-02** | P2 | vite `historyApiFallback` 无效键 | ✅ 已删；文档写 SPA fallback |
| **R060-env** | P2 | E2E 与本地 Vite 抢 5173 | ✅ `reuseExistingServer`（CI 除外） |
| **R103-report** | P2 | 磁盘 R103 与源码漂移 | ✅ 重跑 7/7 绿 |

---

## 五、二次深挖结论

高价值项状态：

| ID | 为何严重 | 状态 |
|----|----------|------|
| **ROUTE-01** | 默认 SPA 入口 404 | ✅ |
| **AUTH-03** | 登录态假阳 | ✅ |
| **TIME-01** | 12:00 打成 12:30 | ✅ |
| **ENT-01** | 解锁可绕 | ✅ |
| **NAME-01** | 姓名 API 白打 | ✅ |
| **RACE-01** | 换档错乱 | ✅ |
| **CASE-01** | 快照签名 | ✅ |
| **REL-01 / PDF-01** | 载荷不一致 | ✅ |
| **SHARE-01** | 假 caseId | ✅ |

---

## 六、已对齐 / 勿再当 Open 的项

| 项 | 说明 |
|----|------|
| OpenAPI · life-volume · explain map · R007 | 机读通过 |
| 八字 `dt`/`lon`、紫微 `gender: 男/女` | 对齐 |
| 大运 `dayun.items` | 实盘无 cycles |
| TD-01/03/04 等历史已关项 | 见 R102 / DEV-AUDIT |

---

## 七、验收建议（修完一项勾一项）

- [x] **入口** `spa_entry_url` → `/static/app/`；`resolve_page_url('bazi')` → `/static/app/new/bazi`
- [x] **时辰** unknown + noon → `T12:00:00`；midday → `T12:30:00`（vitest）
- [x] **Auth** 401 → Pinia 登出；refresh 单飞；登录 422 可读
- [x] **合盘** 紫微/八字合婚对方经度可改；关系合盘 lon 未填有提示
- [x] **报告** volumes/explain/PDF 失败有可见 notice；切换档案自动重生
- [x] **权益** sandbox 失败不 emit mockUnlock（vitest ENT-01）
- [x] **姓名** NAME-01 报告五格面板
- [x] **快照** CASE-01 `profile_signature` + 不一致提示
- [x] **分享** SHARE-02 H5 preview mint + landing 试读
- [x] **导航** NAV-02 排盘台 / 成书分流
- [x] **月运** BZ-Month 进 vol3 / 报告表
- [x] **volumes** REP-04 默认开权威六卷 API
- [x] **内容** CNT Adapter + 远端 life/volumes 加厚 vol1/3/4（空洞审计 thin 目标达标）
- [x] **契约债** X-01 / R060 / R103 / ROUTE-02 等

定向自测（本轮 BE CNT）：

```text
python -m pytest -q tests/test_life_volumes_api.py \
  tests/test_life_volume_locks_t087.py \
  tests/test_life_volume_schema_contract.py
python scripts/audit_content_hollowness.py   # source=build_life_volumes_from_charts
```

---

## 八、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| inv-1.0 | 2026-07-14 | 初版：18 路由矩阵 + P1/P2 |
| inv-1.1 | 2026-07-14 | 二次深挖：P0 四件套 + Auth/时辰/权益 |
| inv-1.2 | 2026-07-14 | **MR-A~D 代码落地**：勾选 P0 全项 + 多数 P1；剩 MR-E/CASE/NAME/内容 |
| inv-1.3 | 2026-07-15 | **MR-E 代码落地**：NAME/CASE/CLIP/EXT-04/STORAGE/REP-05/ZW-01·02/CITY/MOBILE/VOL6；剩 CNT/SHARE-02/产品与引擎债 |
| inv-1.4 | 2026-07-15 | **MR-F**：NAV-02 · BZ-Month · SHARE-02 · EXT-05；剩 CNT/A11Y/ZW03-eng/产品决策 |
| inv-1.5 | 2026-07-15 | **MR-G**：REP-04 · CNT Adapter · ZW03 UI · A11Y · ENT-demo · PROF/NAV-04/OPS；剩契约环境债 |
| inv-1.6 | 2026-07-15 | **MR-H 契约债收口**：X-01 · X-03 · TEST-01 · ROUTE-02 · R060-env · R103 7/7；清单闭环 |
| inv-1.7 | 2026-07-15 | **BE CNT**：远端六卷加厚 · 审计改测真源 · CNT-01~03 全链路 ✅ |
| inv-1.8 | 2026-07-15 | **FE/BE 对齐**：Adapter 强弱因子/短块/流年域对齐远端；加厚回归测 |
| inv-1.9 | 2026-07-15 | **REL-Combine**：拱合→`combine_summary`；消假 missing；后端已 reload 实机确认 |
| inv-1.10 | 2026-07-15 | **收官**：SPA→`/static/app/`；Z-09 scorecard；W14/R103/R108 刷新绿 |
| inv-1.11 | 2026-07-15 | **ADV-miss**：advisory missing 对照文案（Trust + 跋） |
| inv-1.12 | 2026-07-15 | **ADV-miss**：BE 跋字段注记 · Trust tone 徽章对齐 |
