#!/usr/bin/env python3
"""Generate formal PDF compatibility report for 黄振 / 路琳清 / 华倩."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
DATA_COMPAT = ROOT / "_tmp_wenmo" / "compat_results.json"
DATA_ENRICH = ROOT / "_tmp_wenmo" / "enriched_data.json"

REPORT_DATE = date.today().isoformat()
OUTPUT_NAME = f"合盘分析报告-黄振-路琳清-华倩-{REPORT_DATE}.pdf"


def _css() -> str:
    return """
    @page { size: A4; margin: 12mm 10mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      font-size: 10.5pt;
      line-height: 1.65;
      color: #1a1410;
      background: #fffdf8;
    }
    .cover {
      page-break-after: always;
      min-height: 260mm;
      padding: 18mm 14mm;
      background: linear-gradient(165deg, #fffdf8 0%, #f7f1e8 55%, #f0e0c7 100%);
      border: 1px solid #e5dcc8;
    }
    .cover-tag {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 999px;
      background: rgba(184,137,77,.15);
      color: #8b5e34;
      font-size: 9pt;
      font-weight: 700;
      letter-spacing: .12em;
    }
    .cover h1 {
      margin: 16px 0 8px;
      font-size: 28pt;
      letter-spacing: -.02em;
      color: #1a1410;
    }
    .cover .subtitle { color: #6b5d4f; font-size: 12pt; margin-bottom: 24px; }
    .cover-meta {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 28px;
    }
    .meta-card {
      padding: 12px 14px;
      border: 1px solid #e5dcc8;
      border-radius: 10px;
      background: rgba(255,250,245,.85);
    }
    .meta-card strong { display: block; color: #8b5e34; font-size: 9pt; margin-bottom: 4px; }
    .disclaimer {
      margin-top: 36px;
      padding: 12px 14px;
      border-left: 3px solid #8b3a2a;
      background: #fffaf5;
      font-size: 9pt;
      color: #6b5d4f;
    }
    h2 {
      margin: 22px 0 10px;
      padding-bottom: 6px;
      border-bottom: 2px solid #b8894d;
      font-size: 14pt;
      color: #1a1410;
      page-break-after: avoid;
    }
    h3 {
      margin: 16px 0 8px;
      font-size: 11.5pt;
      color: #8b5e34;
      page-break-after: avoid;
    }
    p { margin: 0 0 8px; }
    .section { padding: 0 2mm; }
    .page-break { page-break-before: always; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 14px;
      font-size: 9.5pt;
    }
    th, td {
      border: 1px solid #e5dcc8;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }
    th { background: #f7f1e8; color: #8b5e34; font-weight: 700; }
    tr:nth-child(even) td { background: #fffaf5; }
    .score-high { color: #14532d; font-weight: 700; }
    .score-mid { color: #854d0e; font-weight: 700; }
    .score-low { color: #8b3a2a; font-weight: 700; }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 8.5pt;
      font-weight: 700;
    }
    .badge-ok { background: #f0e0c7; color: #8b5e34; }
    .badge-warn { background: #fef3c7; color: #854d0e; }
    .badge-heur { background: #f7f1e8; color: #6b5d4f; border: 1px solid #d4c4a8; }
    ul { margin: 6px 0 10px; padding-left: 18px; }
    li { margin-bottom: 4px; }
    .footer-note {
      margin-top: 24px;
      padding-top: 10px;
      border-top: 1px solid #e5dcc8;
      font-size: 8.5pt;
      color: #9a8b7a;
      text-align: center;
    }
    .matrix { text-align: center; }
    .matrix td:first-child { font-weight: 700; background: #f7f1e8; }
    .quote {
      margin: 10px 0;
      padding: 10px 12px;
      border-left: 3px solid #b8894d;
      background: #fffaf5;
      font-style: italic;
      color: #6b5d4f;
    }
    """


def _score_class(score: float) -> str:
    if score >= 70:
        return "score-high"
    if score >= 50:
        return "score-mid"
    return "score-low"


def _level_badge(level: str) -> str:
    cls = "badge-ok" if level in {"佳", "上上", "上签", "上上签"} else "badge-warn"
    return f'<span class="badge {cls}">{level}</span>'


def _build_html(compat: dict, enrich: dict) -> str:
    hl = compat["黄振 x 路琳清"]
    lh = compat["路琳清 x 华倩"]
    hh = compat["黄振 x 华倩"]

    def bazi_rows(details: list) -> str:
        rows = ""
        for d in details:
            rows += (
                f"<tr><td>{d['dimension']}</td>"
                f"<td>{d['score']}/{d['max']}</td>"
                f"<td>{_level_badge(d['level'])}</td>"
                f"<td>{d['description']}</td></tr>"
            )
        return rows

    def ziwei_rows(dims: list) -> str:
        rows = ""
        for d in dims:
            rows += (
                f"<tr><td>{d['name']}</td>"
                f"<td>{d['score']}/{d['max']}</td>"
                f"<td>{d['desc']}</td></tr>"
            )
        return rows

    def palace_rows(items: list) -> str:
        rows = ""
        for p in items:
            rel = p.get("relation") or "-"
            rows += (
                f"<tr><td>{p['palace']}</td>"
                f"<td>{p['a_gz']}<br/>{p['a_stars']}</td>"
                f"<td>{p['b_gz']}<br/>{p['b_stars']}</td>"
                f"<td>{rel}</td></tr>"
            )
        return rows

    huang = enrich["ziwei_summary"]["黄振"]
    lu = enrich["ziwei_summary"]["路琳清"]
    hua = enrich["ziwei_summary"]["华倩"]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>合盘分析报告</title>
<style>{_css()}</style>
</head>
<body>

<div class="cover">
  <span class="cover-tag">FUSHENG · 双引擎合盘</span>
  <h1>合盘深度分析报告</h1>
  <p class="subtitle">黄振 × 路琳清 · 路琳清 × 华倩 · 三角关系全览</p>
  <p>报告日期：{REPORT_DATE}<br/>
  引擎：八字合婚 §5.1 + 紫微六合度 heuristic<br/>
  数据来源：文墨天机导出 · 项目实算校验</p>

  <div class="cover-meta">
    <div class="meta-card"><strong>黄振 · 男</strong>1988-06-25 06:10<br/>戊辰 戊午 辛亥 辛卯<br/>命宫 {huang['life_gz']} · {huang['wuxing_ju']}</div>
    <div class="meta-card"><strong>路琳清 · 女</strong>1993-03-06 08:35<br/>癸酉 乙卯 丙戌 壬辰<br/>命宫 {lu['life_gz']} · {lu['wuxing_ju']}</div>
    <div class="meta-card"><strong>华倩 · 女</strong>1993-06-29 15:15<br/>癸酉 戊午 辛巳 丙申<br/>命宫 {hua['life_gz']} · {hua['wuxing_ju']}</div>
    <div class="meta-card"><strong>综合评分</strong>
      黄×路 <span class="{_score_class(hl['combined_score'])}">{hl['combined_score']}</span> ·
      路×华 <span class="{_score_class(lh['combined_score'])}">{lh['combined_score']}</span> ·
      黄×华 <span class="{_score_class(hh['combined_score'])}">{hh['combined_score']}</span>
    </div>
  </div>

  <div class="disclaimer">
    <strong>免责声明</strong><br/>
    本报告基于规则化启发式模型与文墨天机资料整合，反映命盘结构模式，非宿命论。
    重大决策请结合现实、法律、医学与心理咨询，勿单凭命理。
    <span class="badge badge-heur">layer: heuristic</span>
  </div>
</div>

<div class="section">
<h2>一、执行摘要</h2>
<p class="quote">这不是一对平静的夫妻，而是动荡中不断磨合、重塑彼此的伴侣。两个内心都极度缺乏安全感的人，用近乎残酷的方式，成为彼此的依靠与功课。</p>

<table class="matrix">
<tr><th></th><th>黄振</th><th>路琳清</th><th>华倩</th></tr>
<tr><td>黄振</td><td>-</td><td class="{_score_class(hl['combined_score'])}">{hl['combined_score']}</td><td class="{_score_class(hh['combined_score'])}">{hh['combined_score']}</td></tr>
<tr><td>路琳清</td><td>{hl['combined_score']}</td><td>-</td><td class="{_score_class(lh['combined_score'])}">{lh['combined_score']}</td></tr>
<tr><td>华倩</td><td>{hh['combined_score']}</td><td>{lh['combined_score']}</td><td>-</td></tr>
</table>

<h3>关系定性</h3>
<ul>
<li><strong>黄 × 路（{hl['combined_score']}）</strong>：相杀相爱、因家成事的业力型婚姻。八字 {hl['bazi_score']}（{hl['bazi_grade']}），紫微 {hl['ziwei_score']}/{hl['ziwei_max']}（{hl['ziwei_level']}）。</li>
<li><strong>路 × 华（{lh['combined_score']}）</strong>：共生依附型闺蜜/合伙关系。宜情绪支持，忌边界模糊。</li>
<li><strong>黄 × 华（{hh['combined_score']}）</strong>：三对中合拍最高，宜共事理解，需管理三角感受。</li>
</ul>
</div>

<div class="section page-break">
<h2>二、主合盘：黄振 × 路琳清</h2>

<h3>2.1 八字合婚（{hl['bazi_score']} 分 · {hl['bazi_grade']}）</h3>
<p>{hl['bazi_summary']}</p>
<table>
<tr><th>维度</th><th>得分</th><th>等级</th><th>说明</th></tr>
{bazi_rows(hl['bazi_details'])}
</table>

<h3>十神与地支互动</h3>
<ul>
<li><strong>丙辛合</strong>：路（丙）× 黄（辛），天干五合中最具情感色彩，迷恋与灵魂吸引。</li>
<li><strong>路看黄为正财</strong>：稳定归宿；<strong>黄看路为正官</strong>：责任、约束、心甘情愿被管。</li>
<li><strong>辰酉六合</strong>：年支满分，生肖天作之合，子女宫动 — 因孩子绑定。</li>
<li><strong>卯戌合、卯酉冲</strong>：两种家庭观念碰撞，争吵不断但难以拆散。</li>
<li><strong>五行互补</strong>：黄为路的「厚土」吸纳过剩火；路为黄的「劲木」唤醒被土压抑的生机。</li>
</ul>

<h3>2.2 紫微合盘（{hl['ziwei_score']}/{hl['ziwei_max']} · {hl['ziwei_level']}）</h3>
<p>{hl['ziwei_summary']}</p>
<table>
<tr><th>维度</th><th>得分</th><th>解读</th></tr>
{ziwei_rows(hl['ziwei_dims'])}
</table>

<h3>合和点</h3>
<ul>{''.join(f'<li>{x}</li>' for x in hl['harmony'])}</ul>

<h3>冲克点（飞星）</h3>
<ul>{''.join(f'<li>{x}</li>' for x in hl['conflict'])}</ul>

<h3>2.3 六大关键宫位对照（全部三合）</h3>
<table>
<tr><th>宫位</th><th>黄振</th><th>路琳清</th><th>地支关系</th></tr>
{palace_rows(hl['palace_compare'])}
</table>
</div>

<div class="section page-break">
<h2>三、子女 · 田宅 · 业力交叉</h2>

<h3>3.1 子女专题</h3>
<table>
<tr><th>层面</th><th>路琳清</th><th>黄振</th><th>合盘结论</th></tr>
<tr><td>八字</td><td>枭神夺食，辰戌冲</td><td>食神藏亥被克泄</td><td>求子极难，需格外呵护</td></tr>
<tr><td>紫微</td><td>子女宫 紫微/天府 + 文曲</td><td>子女宫 巨门</td><td>孩子优秀、自我、口才强</td></tr>
<tr><td>婚姻功能</td><td colspan="3">粘合剂 — 多次争吵后仍选择继续；注意消化与呼吸系统</td></tr>
</table>

<h3>3.2 田宅与来因宫</h3>
<ul>
<li><strong>黄田宅（来因宫）</strong>：戊午 天机化忌 + 擎羊 — 一生不安之源，婚姻核心战场。</li>
<li><strong>路子嗣宫</strong>：庚申 紫微/天府 — 骄傲与执念所在。</li>
<li>婚姻自始与<strong>房子、家庭、孩子</strong>深度绑定，争吵大半源于家事。</li>
</ul>

<h3>3.3 交叉业力</h3>
<table>
<tr><th>方向</th><th>机制</th><th>表现</th></tr>
<tr><td>路 → 黄</td><td>贪狼忌入父母、巨门忌冲疾厄</td><td>牵动黄与原生家庭；言语伤身心</td></tr>
<tr><td>黄 → 路</td><td>天机忌入福德</td><td>闷葫芦式焦虑，放大路的多想与烦躁</td></tr>
</table>
</div>

<div class="section page-break">
<h2>四、2026-2030 时间轴与破局</h2>

<h3>4.1 流年对照</h3>
<table>
<tr><th>年份</th><th>黄振</th><th>路琳清</th><th>婚姻气象</th></tr>
<tr><td>2026</td><td>大限叠田宅天机忌；劫财夺财</td><td>大限甲寅安家；流年破军化禄</td><td>经济焦虑 × 巨门指责，战争高发</td></tr>
<tr><td>2027</td><td>六合填实</td><td>关系空位被填</td><td>必须谈清钱、分工、边界</td></tr>
<tr><td>2028</td><td>十年中少数喘息年</td><td>财运机会点</td><td>若合力可短暂缓和</td></tr>
</table>

<h3>4.2 破局清单</h3>
<p><strong>给黄振：</strong></p>
<ul>
<li>开口 — 计划、焦虑、失败都要说；沉默是路的猜忌温床</li>
<li>甲寅运禁忌：不合伙、不担保、不信「兄弟」项目</li>
<li>与原生家庭划界；2026 顾好代谢、水液、心脑血管</li>
</ul>
<p><strong>给路琳清：</strong></p>
<ul>
<li>管住嘴 — 依赖别用刀子表达；巨门改策谋</li>
<li>焦虑时先停三秒；华倩是支持但不能替代婚姻修复</li>
<li>夫妻宫右弼陷 — 宜减少边界模糊的闺蜜互动</li>
</ul>
<p><strong>给双方：</strong></p>
<ul>
<li>共同目标：孩子 education / 未来 — 紫破 + 紫府可创条件</li>
<li>定期家事会议：钱、房、子、老人分开吵、合并谈</li>
</ul>
</div>

<div class="section page-break">
<h2>五、路琳清 × 华倩（闺蜜/合伙轴）</h2>
<p>综合 <span class="{_score_class(lh['combined_score'])}">{lh['combined_score']}</span> · 八字 {lh['bazi_score']} · 紫微 {lh['ziwei_score']}/{lh['ziwei_max']}</p>

<h3>5.1 八字：为何华「一直帮着」路？</h3>
<ul>
<li>五行循环：路（丙）→ 木生火 → 戌土 → 生华（辛）；华（戊印）→ 生路 — 生理层舒适</li>
<li>华看路为<strong>正官</strong>：被需要、想管、释放责任感</li>
<li>路看华为<strong>正财</strong>：饭碗、安全感、妻子式依赖</li>
</ul>

<h3>5.2 紫微与风险</h3>
<ul>
<li>阴阳互补满分（15/15）；财帛宫六合；年支酉酉三合</li>
<li>风险：情感勒索、利益分配（2027 关键节点）、感情与钱未分开</li>
<li>对黄路婚姻：华廉府 + 福德贪狼忌 — 催化路的情感觉醒，宜边界清晰</li>
</ul>

<h3>5.3 合伙提示（若涉服装等）</h3>
<table>
<tr><th>项</th><th>判断</th></tr>
<tr><td>核心</td><td>华：品味/人脉/判断；路：运营/执行</td></tr>
<tr><td>规模</td><td>圈子生意，稳定难规模化</td></tr>
<tr><td>维系</td><td>合同化、流程化，感情与钱分开</td></tr>
</table>
</div>

<div class="section page-break">
<h2>六、三人命盘摘要</h2>

<h3>6.1 黄振</h3>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>格局</td><td>杀印相生，印旺土埋金；克妻信息重，宜晚婚</td></tr>
<tr><td>大运</td><td>当下甲寅（32-41）劫财夺财 — 忌合伙、忌担保</td></tr>
<tr><td>紫微</td><td>武杀命，身宫天府；田宅天机忌为来因</td></tr>
<tr><td>2026</td><td>疾厄太阴化权 — 身体优先；官禄有冲动、财帛难落地</td></tr>
</table>

<h3>6.2 路琳清</h3>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>格局</td><td>正印格 + 官杀混杂；夫妻宫枭神夺食</td></tr>
<tr><td>大运</td><td>入辛亥（32-41）财合身，经济好转</td></tr>
<tr><td>紫微</td><td>巨门化权命；子女紫府；兄弟贪狼化忌</td></tr>
<tr><td>2026</td><td>疾厄破军化禄 — 体态变化；夫妻天同 — 矛盾暂缓</td></tr>
</table>

<h3>6.3 华倩</h3>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>格局</td><td>官杀混杂，丙辛合 + 伤官克官</td></tr>
<tr><td>大运</td><td>乙卯（22-31）感情动荡；甲寅（32-41）事业黄金</td></tr>
<tr><td>紫微</td><td>廉府命，福德贪狼化忌；夫妻破军化禄</td></tr>
<tr><td>2026</td><td>财帛雄心；官禄武曲化忌 — 忌冒进投资</td></tr>
</table>
</div>

<div class="section">
<h2>七、最终结论</h2>
<ol>
<li><strong>黄路婚姻 65.5</strong> — 中高绑定型：散不易，好亦不易；丙辛合 + 辰酉合 + 卯亥三合 vs 火克金 + 巨门 + 天机忌之家。</li>
<li><strong>路华关系 59.0</strong> — 功能性亲密：贵在有，险在越界；2027 谈清利益。</li>
<li><strong>黄华关系 80.0</strong> — 高理解：宜共事，需主动管理三角感受。</li>
<li><strong>2026 优先序</strong>：黄开口+断兄弟财；路停嘴三秒；共同孩子目标；华帮路要有边界。</li>
</ol>

<div class="footer-note">
浮生命理 · 双引擎合盘正式版 · {REPORT_DATE}<br/>
Generated by Fusheng compute_compatibility + calc_compatibility · heuristic layer
</div>
</div>

</body>
</html>"""


async def main() -> Path:
    compat = json.loads(DATA_COMPAT.read_text(encoding="utf-8"))
    enrich = json.loads(DATA_ENRICH.read_text(encoding="utf-8"))
    html = _build_html(compat, enrich)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    html_path = TMP_DIR / "wenmo_compat_report.html"
    html_path.write_text(html, encoding="utf-8")

    from services.pdf_exporter import render_html_to_pdf

    pdf_bytes = await render_html_to_pdf(html)
    out_path = OUT_DIR / OUTPUT_NAME
    out_path.write_bytes(pdf_bytes)
    print(str(out_path))
    print(f"bytes={len(pdf_bytes)}")
    return out_path


if __name__ == "__main__":
    asyncio.run(main())
