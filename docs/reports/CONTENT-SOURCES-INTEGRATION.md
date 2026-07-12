# Desktop 资料整合报告

> 生成时间：2026-07-12  
> 脚本：`scripts/import_desktop_content.py`  
> 清单：`data/imported/source_manifest.json`

## 一、三个文件夹盘点

| 文件夹 | 体量 | 结论 |
|--------|------|------|
| `Desktop/资料` | iztro、ziwei-main、bazi 库、DAO_DE_JING、玄学 repo 等 | **算法参考 + 设计文档已同步**；不全量拷贝 |
| `Desktop/文墨天机` | 4 套命例 xlsx/docx + 合盘 + App 二进制 | **3 套对照盘 + 叙事样例已入库** |
| `Desktop/紫薇` | 旧版 c2 快照（2026-07-08） | **跳过**；当前 `c2` 仓库为权威 |

## 二、已整合进项目的内容

### 1. 文墨天机 → 对照轨（`trust_level: advisory`）

| ID | 人物 | 命宫 | 用途 |
|----|------|------|------|
| WM01 | 华倩 | 壬戌 | 与引擎/iztro 三方对照 |
| WM02 | 黄振 | 乙卯 | 合盘样例（配 WM03） |
| WM03 | 路琳清 | 癸亥 | 合盘样例（配 WM02） |

输出：`data/imported/wenmo_reference_cases.json`（十二宫主辅星、大限范围）

**不当作产品主输出** —— 仅作「文墨天机对照轨」脚注，与 iztro 同级。

### 2. 设计文档 → Explain 星曜档案（`trust_level: reference`）

来源：`docs/design/ziwei/02-星曜体系/01-十四主星.md`（与 `资料/学习文件/ziwei-main` MD5 一致，早已同步）

输出：`data/ziwei/star_profiles.json`（14 主星：五行、化气、优缺点、关键特点）

供卷四 Explain `stars` section 引用；**不是典籍 verified 引文**。

### 3. 文墨天机 → 叙事风格样例（`ui_label: 经验推断`）

| ID | 来源 | 域 |
|----|------|-----|
| NARR-HEPAN-001 | 合盘.docx | 夫妻/子女/大限合盘结构 |
| NARR-ZW-001 | 华.docx 紫微段 | 宫位+格局叙事节奏 |

输出：`data/imported/narrative_style_samples.json`

用于 W8+ 六卷 prose 润色参考；**不得标为典籍依据**。

### 4. 术语表扩展

`data/glossary.json` 新增 12 条紫微术语（命宫、三方四正、四化、庙旺利陷等）。

## 三、已盘点但未入库（及原因）

| 来源 | 内容 | 处理 |
|------|------|------|
| `资料/iztro-main` | 排盘算法 | 已有 `scripts/iztro` 对照；不复制源码 |
| `资料/DAO_DE_JING-main` | 道德经、八字杂集 | 走 `import_github_classics.py` / ctext 管线 |
| `资料/FortuneTelling`、`xuanxue*` | 杂项玄学 | MVP 外；W17+ 再评估 |
| `资料/奇门遁甲` | 奇门 | 产品路线外 |
| `文墨天机/App.swf`、`.exe` | 运行时 | 非内容资产 |
| `文墨天机/刘.docx` | 空文件 | 跳过 |
| `Desktop/紫薇` | 旧 data | classics/GT 均落后于 c2 |

## 四、信任分层（与 FE-BE-DECISIONS 一致）

```
排盘推算  ← 引擎 + METHOD-REGISTRY（权威）
典籍依据  ← classics.json + ziwei_classic_refs（verified-only 进 UI）
参考解读  ← star_profiles.json（设计文档提炼）
经验推断  ← narrative_style_samples（文墨样例）
对照轨    ← wenmo_reference_cases + iztro_crosscheck（advisory 脚注）
```

## 五、后续接线（开发计划内）

> **执行权威：** [FUSHENG-INTEGRATED-DEV-PLAN §8.4](../plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md#84-desktop-资料整合已入库--待接线) · 附录 D 任务表

| 周次 | 动作 |
|------|------|
| W2 | P0-11 `WM01`–`WM03` 引擎 diff |
| W6 | P1-11 explain 读 `star_profiles` |
| W8 | P1-13 + F4-9 跋 wenmo advisory |
| W12 | P2-09 iztro horoscope 对照脚本 |
| W14 | P2-10 文墨 xlsx 运限表 diff |
| W16 | `GET /life/volumes` colophon `wenmo_advisory` |

## 六、复现

```bash
python scripts/import_desktop_content.py --desktop "D:/Users/Administrator/Desktop"
pytest tests/test_import_desktop_content.py -q
```

## 七、文件索引

| 路径 | 说明 |
|------|------|
| `data/imported/wenmo_reference_cases.json` | 文墨三盘对照 |
| `data/imported/narrative_style_samples.json` | 叙事样例 |
| `data/imported/source_manifest.json` | 机器可读清单 |
| `data/ziwei/star_profiles.json` | 十四主星 Explain 档案 |
| `data/glossary.json` | 八字+紫微术语 |
| `scripts/import_desktop_content.py` | 可重复导入脚本 |
