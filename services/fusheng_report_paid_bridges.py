"""付费 PDF 人话桥 / 议题卡 / 读盘图例（v2.7）。"""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any


def _esc(value: Any) -> str:
    return escape(str(value if value is not None else ""))


def _clip(text: str, n: int = 120) -> str:
    t = " ".join(str(text or "").split())
    if len(t) <= n:
        return t
    return t[: n - 1].rstrip("，。；、 ") + "…"


def _to_cn_elements(values: list[str] | None) -> list[str]:
    m = {"metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土"}
    out: list[str] = []
    for value in values or []:
        key = str(value).strip().lower()
        out.append(m.get(key, value))
    return out


def chart_row_legend_html() -> str:
    return (
        "<div class='legend-box'>"
        "<p class='legend-title'>读盘图例</p>"
        "<p>主星＝十神角色 · 天干/地支＝柱面显隐 · 藏干＝支中藏力 · "
        "星运/自坐＝旺衰阶段 · 空亡＝虚落旁证 · 纳音＝古典意象 · "
        "神煞＝吉慎旁证（勿单凭断吉凶）。</p>"
        "<p>先看<strong>日柱</strong>，再看<strong>当前大运 / 流年</strong>，最后对照用神。</p>"
        "</div>"
    )


def find_current_dayun(bazi: dict[str, Any], year: int) -> dict[str, Any]:
    items = (bazi.get("dayun") or {}).get("items") or (bazi.get("dayun") or {}).get("cycles") or []
    for item in items:
        if not isinstance(item, dict):
            continue
        start = item.get("start_year")
        if isinstance(start, int) and start <= year <= start + 9:
            return item
    return items[0] if items and isinstance(items[0], dict) else {}


def find_current_liunian(bazi: dict[str, Any], year: int) -> dict[str, Any]:
    for item in (bazi.get("liunian") or {}).get("items") or []:
        if isinstance(item, dict) and int(item.get("year") or 0) == year:
            return item
    return {}


def yongshen_lifestyle_line(bazi: dict[str, Any]) -> str:
    ys = bazi.get("yongshen") or {}
    favor = _to_cn_elements(ys.get("favor"))
    if not favor:
        return "用神未明时，宜以守成与核对大运节点为先。"
    tip = {
        "金": "宜清爽秩序、金属质感与规则明确的事务",
        "木": "宜生长规划、文书学习与向东向的舒展环境",
        "水": "宜流动变通、智库咨询与向北向的安静角落",
        "火": "宜公开表达、热场协作与向南向的明亮空间",
        "土": "宜稳扎稳打、仓储置产与中央安定的节奏",
    }
    bits = [tip.get(el, f"宜顺「{el}」属性安排节奏") for el in favor[:2]]
    return "用神落地：" + "；".join(bits) + "。"


def geju_tension_block(bazi: dict[str, Any], explain_bazi: dict[str, Any] | None) -> str:
    geju = bazi.get("geju") or {}
    name = str(geju.get("geju_name") or "—")
    tier = str((bazi.get("day_master_strength") or {}).get("tier") or "—")
    path = ""
    for section in (explain_bazi or {}).get("sections") or []:
        if section.get("section_id") != "geju":
            continue
        for block in section.get("blocks") or []:
            text = str(block.get("text") or "")
            if "取格" in text or "→" in text or "定格" in text:
                path = _clip(text, 140)
                break
    if not path:
        path = f"本盘取格为「{name}」，以月令与透干关系定格；细节以排盘事实为准。"
    tension = ""
    if tier in {"极弱", "偏弱"} and any(k in name for k in ("杀", "官")):
        tension = f"日主{tier}与「{name}」并存时，取用重在制化与顺势，勿以身强杀战硬拼；重大抉择回扣用神与大运。"
    elif tier in {"极旺", "偏旺"} and "财" in name:
        tension = f"日主{tier}逢财格，宜防透支与过贪，节奏上宜有收有放。"
    body = f"<p><strong>定格说明</strong>：{_esc(path)}</p>"
    if tension:
        body += f"<p><strong>口径张力</strong>：{_esc(tension)}</p>"
    return f"<div class='bridge-card'>{body}</div>"


def liunian_bridge_html(bazi: dict[str, Any], year: int | None = None) -> str:
    y = year or datetime.now().year
    ln = find_current_liunian(bazi, y)
    stem = str(ln.get("stem") or "").strip()
    branch = str(ln.get("branch") or "").strip()
    tg = str(ln.get("ten_god") or "—").strip()
    gz = f"{stem}{branch}" if stem and branch else "—"
    dayun = find_current_dayun(bazi, y)
    dgz = f"{dayun.get('stem') or ''}{dayun.get('branch') or ''}" or "—"
    if gz == "—":
        text = f"{y} 年流年柱暂缺，请以满盘流年列与大运页互参。"
    else:
        text = (
            f"{y} 年为{_esc(gz)}年；对日主而言流年主星偏「{_esc(tg)}」。"
            f"宜对照当前大运「{_esc(dgz)}」看进退，勿单凭生肖年运断事。"
            f"（文化研究参考，非必然断语。）"
        )
    return f"<div class='bridge-card'><p class='bridge-k'>本年对我</p><p>{text}</p></div>"


def dayun_bridge_html(bazi: dict[str, Any], year: int | None = None) -> str:
    y = year or datetime.now().year
    dayun = find_current_dayun(bazi, y)
    gz = f"{dayun.get('stem') or ''}{dayun.get('branch') or ''}" or "—"
    tg = str(dayun.get("ten_god") or "—")
    start = dayun.get("start_year")
    ns = dayun.get("narrative_sections") if isinstance(dayun.get("narrative_sections"), dict) else {}
    core = _clip(str(ns.get("core") or ""), 150)
    if not core:
        core = (
            f"当前大运「{gz}」·十神「{tg}」"
            + (f"（约自 {start} 年起）" if start else "")
            + "。宜以扶抑/制化顺势决策，并回扣用神。"
        )
    career = _clip(str(ns.get("career") or ""), 80)
    wealth = _clip(str(ns.get("wealth") or ""), 80)
    extras = ""
    if career:
        extras += f"<p><strong>事业侧</strong>：{_esc(career)}</p>"
    if wealth:
        extras += f"<p><strong>财侧</strong>：{_esc(wealth)}</p>"
    return (
        f"<div class='bridge-card'><p class='bridge-k'>当前大运 · {_esc(gz)}</p>"
        f"<p>{_esc(core)}</p>{extras}"
        f"<p class='meta'>属经验推断；重大抉择请回扣命局与流年。</p></div>"
    )


def _palace_blob(ziwei: dict[str, Any], name: str) -> dict[str, Any]:
    for p in ziwei.get("palaces") or []:
        if isinstance(p, dict) and str(p.get("name") or "") == name:
            return p
    return {}


def _stars_line(palace: dict[str, Any]) -> str:
    mains = [str(s.get("name") or "") for s in (palace.get("main_stars") or []) if isinstance(s, dict)]
    mains = [m for m in mains if m]
    if mains:
        return "、".join(mains)
    return "无主星（或借对宫）"


def _collect_minor_names(palace: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key in ("minor_stars", "aux_stars", "stars", "all_stars"):
        for s in palace.get(key) or []:
            if isinstance(s, dict):
                n = str(s.get("name") or "").strip()
                if n:
                    names.append(n)
            elif isinstance(s, str) and s.strip():
                names.append(s.strip())
    # 有些响应把辅星摊在 text
    return list(dict.fromkeys(names))


def ziwei_topic_cards_html(ziwei: dict[str, Any], bazi: dict[str, Any] | None = None) -> str:
    """桃花 / 田宅 / 官财慎点 — 本命结构 + 窗口级提示。"""
    del bazi  # 预留交叉
    peach_stars = {"红鸾", "天喜", "天姚", "咸池", "沐浴"}
    found_peach: list[str] = []
    for p in ziwei.get("palaces") or []:
        if not isinstance(p, dict):
            continue
        pname = str(p.get("name") or "")
        bag = _collect_minor_names(p) + [
            str(s.get("name") or "") for s in (p.get("main_stars") or []) if isinstance(s, dict)
        ]
        hits = [n for n in bag if n in peach_stars]
        if hits:
            found_peach.append(f"{pname}见{'、'.join(hits)}")

    spouse = _palace_blob(ziwei, "夫妻宫")
    property_p = _palace_blob(ziwei, "田宅宫")
    career = _palace_blob(ziwei, "官禄宫")
    wealth = _palace_blob(ziwei, "财帛宫")
    health = _palace_blob(ziwei, "疾厄宫")

    peach_body = (
        f"本命依据：夫妻宫主星「{_esc(_stars_line(spouse))}」"
        + (
            "；" + "；".join(_esc(x) for x in found_peach[:4])
            if found_peach
            else "；未见常见桃花星高亮时，以夫妻/福德宫结构为主。"
        )
        + " 时机：大限走到夫妻、福德、财帛或流年引动上述宫时，感情主题更易活跃；只给宜推动/宜暂缓级线索，不作日期断言。"
    )
    house_body = (
        f"本命依据：田宅宫主星「{_esc(_stars_line(property_p))}」。"
        " 置业/家宅宜看田宅与财帛互参；大限或流年叠田宅、或化忌冲田宅时宜更谨慎核对合同与节奏，勿作必买/必涨断语。"
    )
    caution_bits = []
    for label, pal in (("官禄", career), ("财帛", wealth), ("疾厄", health)):
        # 粗检：主星名含化忌字样或空主星
        mains = _stars_line(pal)
        if "无主星" in mains:
            caution_bits.append(f"{label}宫空或借对宫，主题较隐，宜合三方看")
    if not caution_bits:
        caution_bits.append("以化忌落宫、空宫借对、煞曜会照为慎点线索，须叠大限/流年再定阶段主题")
    caution_body = (
        "本命慎点："
        + "；".join(caution_bits)
        + "。窗口：大限化忌或流年冲会相关宫时，宜放慢决策、先核对事实；禁止恐吓式必然凶断。"
    )

    cards = [
        ("桃花 / 感情", peach_body),
        ("田宅 / 置业", house_body),
        ("宜谨慎主题", caution_body),
    ]
    # 官财各一短卡
    cards.append(
        (
            "官禄 / 财帛结构",
            f"官禄「{_esc(_stars_line(career))}」· 财帛「{_esc(_stars_line(wealth))}」。"
            "事业与财气看三方四正与大限应宫，勿单宫贴标签。",
        )
    )
    inner = "".join(
        f"<div class='topic-card'><p class='bridge-k'>{_esc(t)}</p><p>{_esc(b)}</p></div>" for t, b in cards
    )
    foot = "<p class='meta'>读法：立太极 → 三方四正 → 四化 → 大限/流年。属文化研究与自我认知参考。</p>"
    return f"<div class='topic-grid'>{inner}</div>{foot}"


def flying_star_plain_html() -> str:
    return (
        "<div class='bridge-card'>"
        "<p class='bridge-k'>飞星三分钟读法</p>"
        "<p>化禄≈顺遂/财气线索 · 化权≈权柄/主导 · 化科≈名气文书 · 化忌≈纠结损耗线索（皆旁证）。</p>"
        "<p>三步：① 先选关心的宫（夫妻/田宅/财帛…）② 看谁飞入、谁被冲 ③ 再叠大限/流年问时机。"
        "详细矩阵见站内飞星盘「进阶对照」。</p>"
        "</div>"
    )


def relations_short_list_html(bazi: dict[str, Any]) -> str:
    rs = bazi.get("relations_summary") if isinstance(bazi.get("relations_summary"), dict) else {}
    lines: list[str] = []
    items = rs.get("items") or []
    if isinstance(items, list):
        for item in items[:6]:
            if not isinstance(item, dict):
                continue
            rel = str(item.get("type") or "互动")
            summary = str(item.get("summary") or item.get("detail") or "").strip()
            sub = str(item.get("subject") or "").strip()
            tgt = str(item.get("target") or "").strip()
            if sub and tgt:
                lines.append(f"{rel}：{sub}与{tgt}" + (f"（{summary}）" if summary else ""))
            elif summary:
                lines.append(f"{rel}：{summary}")
    if not lines:
        for key in ("clash_summary", "combine_summary", "harm_summary", "interaction_summary"):
            text = str(rs.get(key) or "").strip()
            if text:
                lines.append(text)
    if not lines:
        return ""
    lis = "".join(f"<li>{_esc(x)}</li>" for x in lines[:6])
    return (
        "<div class='bridge-card'><p class='bridge-k'>干支关系要点</p>"
        f"<ul class='tight'>{lis}</ul>"
        "<p class='meta'>合≠必吉、冲≠必灾；以排盘事实为准。</p></div>"
    )


def how_to_read_book_html() -> str:
    return (
        "<div class='bridge-card'>"
        "<p class='bridge-k'>本册怎么读</p>"
        "<ol class='tight'>"
        "<li>先看「八字满盘」日柱与当前大运/流年。</li>"
        "<li>再看大运叙事与紫微议题卡（桃花/田宅/慎点）。</li>"
        "<li>最后落到「综合总结」三条行动建议。</li>"
        "</ol></div>"
    )


def closing_rich_html(
    bazi: dict[str, Any],
    ziwei: dict[str, Any],
    meta: dict[str, Any] | None = None,
    *,
    year: int | None = None,
) -> str:
    del meta
    y = year or datetime.now().year
    ys = bazi.get("yongshen") or {}
    favor = "、".join(_to_cn_elements(ys.get("favor"))) or "中和"
    avoid = "、".join(_to_cn_elements(ys.get("avoid"))) or "过旺"
    tier = (bazi.get("day_master_strength") or {}).get("tier") or "中和"
    geju = ((bazi.get("geju") or {}).get("geju_name")) or "本局"
    life = ziwei.get("life_palace_gz") or "命宫"
    ln = find_current_liunian(bazi, y)
    gz = f"{ln.get('stem') or ''}{ln.get('branch') or ''}" or "—"
    tg = str(ln.get("ten_god") or "—")

    s1 = f"日常取用优先围绕喜用「{favor}」，忌避「{avoid}」过用；重大支出与换岗宜对照大运节点。"
    s2 = f"日主{tier}、格局「{geju}」并存时，决策以扶抑/制化顺势为主，勿单凭神煞名单断吉凶。"
    s3 = f"紫微命宫「{life}」可作事业/心性旁证；流年变动时回看满盘与议题卡。"
    items = "".join(f"<li>{_esc(t)}</li>" for t in (s1, s2, s3))
    focus = (
        f"<div class='bridge-card'><p class='bridge-k'>{y} 本年焦点</p>"
        f"<p>流年「{_esc(gz)}」· 主星「{_esc(tg)}」。宜与当前大运同看进退；"
        f"细节见「八字满盘 · 本年对我」。</p></div>"
    )
    index = (
        "<div class='bridge-card'><p class='bridge-k'>回看索引</p>"
        "<p>盘面与本年 → 八字满盘 · 大运叙事 → 运势时间轴 · "
        "桃花/田宅 → 紫微议题 · 行动建议 → 本页。</p></div>"
    )
    boundary = "本报告仅供文化研究与自我认知参考，不构成医疗、法律或投资建议。"
    return (
        "<section class='page sheet'>"
        "<h2>综合总结</h2>"
        "<p class='meta'>以下为行动建议，不复述命局总评全文。</p>"
        f"<ol class='closing'>{items}</ol>"
        f"{focus}{index}"
        f"<p class='page-foot-bar'><strong>边界</strong>：{_esc(boundary)}</p>"
        "</section>"
    )
