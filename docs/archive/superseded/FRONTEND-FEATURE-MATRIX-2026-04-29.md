# 前端能力对照清单（2026-04-29）

## 目的

回答两个问题：

1. 前端主入口是否已经做到职责唯一、避免重复承载。
2. 后端现有能力是否都已经被前端页面完整承接。

结论：

- 前端主入口的唯一性已经基本建立。
- 核心功能大多已前端化。
- 仍有一批能力处于“规划页 / 轻量页 / 仅 API 存在、尚无完整前端工作区”的状态。

---

## A. 主入口唯一性检查

| 领域 | 主入口 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| 首页总览 | `/home` | 已建立 | 作为模块分发与总览入口 |
| 案件枢纽 | `/cases` | 已建立 | 不再承载八字/紫微超级页 |
| 八字分析 | `/bazi` | 已建立 | 八字阅读与分析主入口 |
| 紫微分析 | `/ziwei` | 已建立 | 紫微主盘与阅读主入口 |
| 紫微批量 | `/ziwei/batch` | 已建立 | 独立入口 |
| 紫微案例工作区 | `/ziwei/cases` | 已建立 | 快照、相似盘、案例流程独立 |
| AI 草稿 | `/llm/drafts` | 已建立 | 草稿与 AI 输出独立 |
| 报告 | `/report` | 已建立 | 章节化报告独立 |
| 个人档案 | `/profile` | 已建立 | 出生信息与同步独立 |
| 管理后台 | `/admin` | 已建立 | 运营治理类能力独立 |
| 术语词库 | `/glossary` | 已建立 | 知识检索独立 |
| 人类设计 | `/human-design` | 仅规划入口 | 有入口，但仍是预留页 |

判断：主入口已基本符合“一功能一主入口”。

---

## B. 已由前端完整承接的核心模块

### B1. 已形成页面或工作区的主能力

| 模块 | 前端承接状态 | 主要页面 / 路由 | 后端/API 证据 |
| --- | --- | --- | --- |
| 八字 | 完整承接 | `/bazi` | `computeBazi`、案例保存、AI 解读 |
| 紫微 | 完整承接 | `/ziwei` | `computeZiwei`、demo、建案例、建快照、入相似盘索引 |
| 紫微批量 | 完整承接 | `/ziwei/batch` | `ziweiBatch` |
| 紫微案例流程 | 完整承接 | `/ziwei/cases` | `createSnapshot`、`listSnapshots`、`diffSnapshots`、`searchSimilar` |
| 案例中心 / Workbench | 完整承接 | `/cases` | 案例 CRUD、八字/紫微装配、导出、分享、快照 |
| 姓名学 | 完整承接 | `/name` | `analyzeName`、`suggestNames` |
| 合婚/合盘 | 基本承接 | `/compat`、`/compat/team` | `getBaziCompat`、`ziweiMultiCompat` |
| 择日 | 完整承接 | `/zeri` | `recommendZeri`、`getZeriPurposes` |
| 风水 | 完整承接 | `/fengshui` | `fetchFengshuiBagua`、`getFengshuiOptions`、`analyzeRoomLayout` |
| 西方占星 | 完整承接 | `/western` | `getWesternChart` 等 |
| 报告书 | 完整承接 | `/report` | 导出 PDF / JSON、章节展示 |
| AI 草稿 | 完整承接 | `/llm/drafts` | 草稿列表、详情、更新、删除 |
| 登录 | 完整承接 | `/login` | `login` |
| 术语词库 | 完整承接 | `/glossary` | `getGlossary` |
| 管理后台 | 已承接主要运营治理 | `/admin` | dashboard、审查、实验、API Key、规则、事件、黄金案例、术语编辑 |

---

## C. 已接入前端，但不是完整上线态

| 模块 | 状态 | 当前前端形态 | 说明 |
| --- | --- | --- | --- |
| 人类设计 | planned | 规划页 | 只有预留说明，不是实际工作区 |
| 数字学 | integrated | 独立页已接入 | 更接近轻量模块，非完整后端驱动主能力 |
| 塔罗 | integrated | 独立页已接入 | 更接近轻量模块，非完整后端驱动主能力 |

说明：这些模块已经“出现在前端”，但不能等同于“全部功能已完成加载”。

---

## D. 后端已有 API，但前端尚未形成一等页面/完整流程的能力

以下能力在 API 层可见，但当前未发现对应的独立主页面或完整工作区承接。

| API / 能力 | 当前状态 | 备注 |
| --- | --- | --- |
| `/api/v1/quickstart` | 仅 API 存在 | 未发现对应前端入口 |
| `members.ts` | 仅 API 存在 | 未发现成员管理页 |
| `scenarios.ts` | 仅 API 存在 | 未发现情景模拟页 |
| `relations.ts` | 仅 API 存在 | 未发现关系工作区页 |
| `ziweiFlying()` | 仅 API 存在 | 未发现独立飞星盘页面 |
| `calendarCompare()` | 仅 API 存在 | 未发现历法对照工作区 |
| `batchCompare()` | 仅 API 存在 | 未发现批量对比页 |
| `analyzeBazi()` | API 可用但非一等入口 | 未见独立模块化分析工作区 |
| `liunian-report` 任务接口 | API 可用但前端未见完整任务面板 | 暂未形成任务管理页 |

---

## E. 已被局部消费，但还不是独立产品模块的能力

| 能力 | 当前承接方式 | 说明 |
| --- | --- | --- |
| 黄金案例 | 只在管理后台可见 | 已用于运营治理，不是独立终端模块 |
| 事件统计 | 只在管理后台可见 | 已接入，但不是独立业务工作区 |
| 相似盘 | 已用于紫微流程页 | 已承接，但依附于案例工作流 |
| 快照系统 | 已用于案例中心/紫微案例页 | 已承接，但更多是支撑层 |
| 导出能力 | 已在报告/Workbench 中承接 | 属于输出能力，不是独立模块 |

---

## F. 对“是否全部加载到前端”的最终判断

### 可以认为已经完成的

- 主入口唯一性基本建立
- 核心命理链路已前端化
- Workbench / Bazi / Ziwei / Report / AI / Admin 的主干已经打通

### 不能认为已经完成的

- 不是所有后端 API 都有前端页面
- 不是所有模块都处于 `ready`
- `human-design` 仍是规划页
- `numerology`、`tarot` 更偏已接入但非完整主能力
- `quickstart`、`members`、`scenarios`、`relations` 等仍缺前端工作区

---

## G. 产品化结论

当前前端状态可归纳为：

- 核心主链路：已加载
- 扩展工具：部分加载
- 预留模块：已占位但未完成
- 若干后端能力：只有 API，未产品化到前端

所以答案不是“全部已加载”，而是：

> 前端已经完成主干产品化，但还没有达到“后端能力全量前端化”的程度。

---

## H. 下一步建议

1. 建立一份正式的“模块状态表”
   - `ready`
   - `integrated`
   - `planned`
   - `api-only`

2. 对 API-only 能力做去留决策
   - 补页面
   - 并入已有工作区
   - 明确降级为后台/内部接口

3. 对轻量模块补状态提示
   - 在首页、模块卡、规划页中明确说明“已上线 / 已集成 / 规划中”

4. 优先补齐最影响产品闭环的缺口
   - `quickstart`
   - `members`
   - `scenarios`
   - `relations`
   - `ziweiFlying`

---

## I. 本次核对依据

主要依据以下前端结构进行核对：

- 路由入口：`frontend/src/router/index.ts`
- 模块定义：`frontend/src/data/appModules.ts`
- 导航树：`frontend/src/data/navTree.ts`
- 页面清单：`frontend/src/views/*.vue`
- Workbench 组件清单：`frontend/src/components/workbench/*.vue`
- API 使用情况：`frontend/src/api/*.ts` 与 `views / stores / composables / components / utils` 的导入关系
