"""八字流日流时推演 — 基于日柱干支计算指定日期的流日/流时。"""

from __future__ import annotations

import datetime

from services.bazi_engine.tables import get_ten_god

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

_TG_CN = {
    "bi_jian": "比肩",
    "jie_cai": "劫财",
    "shi_shen": "食神",
    "shang_guan": "伤官",
    "zheng_cai": "正财",
    "pian_cai": "偏财",
    "zheng_guan": "正官",
    "qi_sha": "七杀",
    "zheng_yin": "正印",
    "pian_yin": "偏印",
}

_FAVORABLE_TG = {"正印", "偏印", "比肩", "劫财", "食神", "正财", "正官"}
_UNFAVORABLE_TG = {"伤官", "偏财", "七杀"}

# 1900-01-01 = 甲戌日（60甲子 index 10）
_BASE_DATE = datetime.date(1900, 1, 1)
_BASE_DAY_GZ_INDEX = 10

_ZI_DAY_RULE_LABELS = {
    "sxtwl": "sxtwl（后端默认，23–01 时换日提示）",
    "early_zi_prev_day": "early_zi_prev_day（23 时算前一日）",
    "early_zi_same_day": "early_zi_same_day（23 时仍算当日）",
}


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _day_gz_index(d: datetime.date) -> int:
    """计算某日的 60 甲子日柱索引。"""
    delta = (d - _BASE_DATE).days
    return (_BASE_DAY_GZ_INDEX + delta) % 60


def _hour_zhi(hour: int) -> str:
    """小时 → 地支（23–0=子, 1–2=丑, …）。"""
    if hour == 23 or hour == 0:
        return "子"
    return ZHI[((hour + 1) // 2) % 12]


def _hour_stem(day_stem: str, hour_zhi: str) -> str:
    """日干 + 时支 → 时干（五鼠遁）。"""
    start_idx = {
        "甲": 0,
        "己": 0,
        "乙": 2,
        "庚": 2,
        "丙": 4,
        "辛": 4,
        "丁": 6,
        "壬": 6,
        "戊": 8,
        "癸": 8,
    }
    zi_idx = ZHI.index(hour_zhi)
    return GAN[(start_idx.get(day_stem, 0) + zi_idx) % 10]


def _tg_cn(day_stem: str, flow_stem: str) -> str | None:
    tg = get_ten_god(day_stem, flow_stem)
    return _TG_CN.get(tg, tg) if tg else None


def _score_dayun_dimension(
    *,
    day_ten_god: str | None,
    hour_ten_god: str | None,
    dayun_ten_god: str | None,
) -> tuple[int, str | None]:
    score = 50
    link = ""
    if day_ten_god and dayun_ten_god:
        if day_ten_god == dayun_ten_god:
            score += 18
            link = f"流日十神「{day_ten_god}」与当前大运同气"
        elif day_ten_god in _FAVORABLE_TG and dayun_ten_god in _FAVORABLE_TG:
            score += 8
            link = f"流日十神「{day_ten_god}」与大运「{dayun_ten_god}」同为顺气"
        elif day_ten_god in _UNFAVORABLE_TG and dayun_ten_god in _UNFAVORABLE_TG:
            score -= 10
            link = f"流日十神「{day_ten_god}」与大运「{dayun_ten_god}」同逆"
    if hour_ten_god in _FAVORABLE_TG:
        score += 2
    elif hour_ten_god in _UNFAVORABLE_TG:
        score -= 2
    return _clamp_score(score), link or None


def _score_liunian_dimension(
    *,
    day_ten_god: str | None,
    liunian_ten_god: str | None,
) -> tuple[int, str | None]:
    score = 50
    link = ""
    if day_ten_god and liunian_ten_god:
        if day_ten_god == liunian_ten_god:
            score += 15
            link = f"流日十神「{day_ten_god}」与流年同气"
        elif day_ten_god in _FAVORABLE_TG and liunian_ten_god in _FAVORABLE_TG:
            score += 6
            link = f"流日十神「{day_ten_god}」与流年「{liunian_ten_god}」同为顺气"
        elif day_ten_god in _UNFAVORABLE_TG and liunian_ten_god in _UNFAVORABLE_TG:
            score -= 8
            link = f"流日十神「{day_ten_god}」与流年「{liunian_ten_god}」同逆"
    return _clamp_score(score), link or None


def _score_geju_dimension(
    *,
    day_ten_god: str | None,
    hour_ten_god: str | None,
    yongshen_favor: list[str] | None,
    yongshen_avoid: list[str] | None,
    geju_broken: bool = False,
) -> int:
    score = 50
    if geju_broken:
        score -= 15
    if day_ten_god in _FAVORABLE_TG:
        score += 8
    elif day_ten_god in _UNFAVORABLE_TG:
        score -= 10
    if hour_ten_god in _FAVORABLE_TG:
        score += 4
    elif hour_ten_god in _UNFAVORABLE_TG:
        score -= 4
    if yongshen_favor or yongshen_avoid:
        score += 3
    return _clamp_score(score)


def _build_transition_hint(
    *,
    days_to_next_transition: int | None,
    next_transition_ganzhi: str | None,
    next_transition_age: int | None,
    next_transition_hint: str | None,
) -> str | None:
    if next_transition_hint:
        return next_transition_hint
    if days_to_next_transition is None:
        return None
    if days_to_next_transition <= 7:
        gz = next_transition_ganzhi or "下一运"
        age = next_transition_age
        age_part = f"虚岁{age}岁" if age is not None else ""
        return f"换运窗口：距{gz}（{age_part}）约 {days_to_next_transition} 天，宜稳守过渡、忌重大决断。"
    if days_to_next_transition <= 30:
        gz = next_transition_ganzhi or "下一运"
        return f"近运提醒：距{gz}约 {days_to_next_transition} 天，可提前规划节奏。"
    return None


def _zi_boundary_warnings(zi_day_rule: str, target_hour: int) -> list[str]:
    from services.bazi_provenance import day_boundary_crossed

    if not day_boundary_crossed(zi_day_rule, target_hour):
        return []
    label = _ZI_DAY_RULE_LABELS.get(zi_day_rule, zi_day_rule)
    return [
        f"流日目标处于子时换日窗口（{label}）；"
        "日柱/流日干支可能因 zi_day_rule 与真太阳时修正而异，请以档案换日规则为准。"
    ]


def _annotate_flow_missing_fields(
    result: dict,
    *,
    day_stem: str | None,
    dayun_ten_god: str | None,
    liunian_ten_god: str | None,
) -> None:
    """流日联动缺上下文时显式登记 missing_fields，禁止静默 50 分占位。"""
    missing = result.setdefault("missing_fields", [])
    if not day_stem:
        for key in (
            "flow_score",
            "flow_score_dayun",
            "flow_score_liunian",
            "flow_score_geju",
            "flow_tone",
            "flow_summary",
        ):
            if key not in missing:
                missing.append(key)
    if day_stem and not dayun_ten_god and "dayun_context" not in missing:
        missing.append("dayun_context")
        result.pop("flow_score_dayun", None)
    if day_stem and not liunian_ten_god and "liunian_context" not in missing:
        missing.append("liunian_context")
        result.pop("flow_score_liunian", None)
    if day_stem and result.get("flow_score_geju") is None and "flow_score_geju" not in missing:
        missing.append("flow_score_geju")


def _composite_flow_score(
    *,
    dayun: int | None,
    liunian: int | None,
    geju: int | None,
) -> int | None:
    parts = [v for v in (dayun, liunian, geju) if v is not None]
    if not parts:
        return None
    return _clamp_score(round(sum(parts) / len(parts)))


def _link_flow_context(
    *,
    day_stem: str | None,
    day_ten_god: str | None,
    hour_ten_god: str | None,
    dayun_ten_god: str | None = None,
    dayun_ganzhi: str | None = None,
    liunian_ten_god: str | None = None,
    liunian_ganzhi: str | None = None,
    yongshen_favor: list[str] | None = None,
    yongshen_avoid: list[str] | None = None,
    geju_broken: bool = False,
    days_to_next_transition: int | None = None,
    next_transition_ganzhi: str | None = None,
    next_transition_age: int | None = None,
    next_transition_hint: str | None = None,
) -> dict:
    """流日/流时与大运、流年、格局联动评分（B-P2 三维 + transition_hint）。"""
    flow_score_dayun: int | None = None
    flow_score_liunian: int | None = None
    dayun_link: str | None = None
    liunian_link: str | None = None

    if dayun_ten_god:
        flow_score_dayun, dayun_link = _score_dayun_dimension(
            day_ten_god=day_ten_god,
            hour_ten_god=hour_ten_god,
            dayun_ten_god=dayun_ten_god,
        )
    if liunian_ten_god:
        flow_score_liunian, liunian_link = _score_liunian_dimension(
            day_ten_god=day_ten_god,
            liunian_ten_god=liunian_ten_god,
        )

    flow_score_geju: int | None = None
    if day_ten_god:
        flow_score_geju = _score_geju_dimension(
            day_ten_god=day_ten_god,
            hour_ten_god=hour_ten_god,
            yongshen_favor=yongshen_favor,
            yongshen_avoid=yongshen_avoid,
            geju_broken=geju_broken,
        )

    flow_score = _composite_flow_score(
        dayun=flow_score_dayun,
        liunian=flow_score_liunian,
        geju=flow_score_geju,
    )
    tone = (
        "顺"
        if flow_score is not None and flow_score >= 60
        else ("逆" if flow_score is not None and flow_score < 40 else "平")
    )
    transition_hint = _build_transition_hint(
        days_to_next_transition=days_to_next_transition,
        next_transition_ganzhi=next_transition_ganzhi,
        next_transition_age=next_transition_age,
        next_transition_hint=next_transition_hint,
    )

    notes: list[str] = []
    if dayun_link:
        notes.append(dayun_link)
    if liunian_link:
        notes.append(liunian_link)
    if geju_broken:
        notes.append("格局破格，流日格局维度降分")
    if yongshen_favor or yongshen_avoid:
        notes.append("用神喜忌已纳入流日格局评分")

    summary_parts = notes.copy()
    if dayun_ganzhi:
        summary_parts.insert(0, f"当前大运 {dayun_ganzhi}")
    if liunian_ganzhi:
        summary_parts.insert(1 if dayun_ganzhi else 0, f"流年 {liunian_ganzhi}")
    summary_parts = notes.copy()
    if dayun_ganzhi:
        summary_parts.insert(0, f"当前大运 {dayun_ganzhi}")
    if liunian_ganzhi:
        summary_parts.insert(1 if dayun_ganzhi else 0, f"流年 {liunian_ganzhi}")
    dim_bits = []
    if flow_score_dayun is not None:
        dim_bits.append(f"大运{flow_score_dayun}")
    if flow_score_liunian is not None:
        dim_bits.append(f"流年{flow_score_liunian}")
    if flow_score_geju is not None:
        dim_bits.append(f"格局{flow_score_geju}")
    if dim_bits:
        score_text = f"{'/'.join(dim_bits)}"
        if flow_score is not None:
            score_text += f"；综合 {flow_score}（{tone}）"
        summary_parts.append(score_text)
    if transition_hint:
        summary_parts.append(transition_hint)

    _ = day_stem
    payload: dict = {
        "flow_tone": tone if flow_score is not None else None,
        "transition_hint": transition_hint,
        "dayun_link": dayun_link,
        "liunian_link": liunian_link,
        "current_dayun_ganzhi": dayun_ganzhi,
        "current_liunian_ganzhi": liunian_ganzhi,
        "flow_summary": "；".join(summary_parts) if summary_parts else None,
    }
    if flow_score is not None:
        payload["flow_score"] = flow_score
    if flow_score_dayun is not None:
        payload["flow_score_dayun"] = flow_score_dayun
    if flow_score_liunian is not None:
        payload["flow_score_liunian"] = flow_score_liunian
    if flow_score_geju is not None:
        payload["flow_score_geju"] = flow_score_geju
    return payload


def get_liuri_liushi(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    *,
    day_stem: str | None = None,
    target_date: datetime.date | None = None,
    target_hour: int | None = None,
    dayun_ten_god: str | None = None,
    dayun_ganzhi: str | None = None,
    liunian_ten_god: str | None = None,
    liunian_ganzhi: str | None = None,
    yongshen_favor: list[str] | None = None,
    yongshen_avoid: list[str] | None = None,
    geju_broken: bool = False,
    days_to_next_transition: int | None = None,
    next_transition_ganzhi: str | None = None,
    next_transition_age: int | None = None,
    next_transition_hint: str | None = None,
    zi_day_rule: str = "sxtwl",
) -> dict:
    """获取指定日期的流日流时信息。

    day_stem: 本命日干，用于计算流日/流时十神；缺省则仅返回干支。
    target_hour: 0–23；缺省则用 target_date 当天 12 时（或 today 的当前钟点）。
    dayun_* / liunian_*: 可选，用于 B-P2 运限联动评分。
    zi_day_rule: 子时换日规则，用于边界 warnings。
    """
    _ = (birth_year, birth_month, birth_day, birth_hour)

    d = target_date or datetime.date.today()
    day_idx = _day_gz_index(d)
    day_stem_flow = GAN[day_idx % 10]
    day_branch = ZHI[day_idx % 12]

    if target_hour is not None:
        current_hour = target_hour
    elif target_date is not None:
        current_hour = 12
    else:
        current_hour = datetime.datetime.now().hour

    hz = _hour_zhi(current_hour)
    hs = _hour_stem(day_stem_flow, hz)
    hour_branch_idx = ZHI.index(hz)

    result: dict = {
        "date": d.isoformat(),
        "day_ganzhi": f"{day_stem_flow}{day_branch}",
        "day_stem": day_stem_flow,
        "day_branch": day_branch,
        "hour_ganzhi": f"{hs}{hz}",
        "hour_stem": hs,
        "hour_branch": hz,
        "hour_branch_idx": hour_branch_idx,
        "hour_label": f"{hz}时",
        "method": "ganzhi_day_pillar",
        "missing_fields": [],
        "warnings": _zi_boundary_warnings(zi_day_rule, current_hour),
    }

    day_tg_cn: str | None = None
    hour_tg_cn: str | None = None
    if day_stem:
        day_tg_cn = _tg_cn(day_stem, day_stem_flow)
        hour_tg_cn = _tg_cn(day_stem, hs)
        result["day_ten_god"] = day_tg_cn
        result["hour_ten_god"] = hour_tg_cn
    else:
        result["missing_fields"].append("natal_day_stem")

    if day_stem:
        result.update(
            _link_flow_context(
                day_stem=day_stem,
                day_ten_god=day_tg_cn,
                hour_ten_god=hour_tg_cn,
                dayun_ten_god=dayun_ten_god,
                dayun_ganzhi=dayun_ganzhi,
                liunian_ten_god=liunian_ten_god,
                liunian_ganzhi=liunian_ganzhi,
                yongshen_favor=yongshen_favor,
                yongshen_avoid=yongshen_avoid,
                geju_broken=geju_broken,
                days_to_next_transition=days_to_next_transition,
                next_transition_ganzhi=next_transition_ganzhi,
                next_transition_age=next_transition_age,
                next_transition_hint=next_transition_hint,
            )
        )
        _annotate_flow_missing_fields(
            result,
            day_stem=day_stem,
            dayun_ten_god=dayun_ten_god,
            liunian_ten_god=liunian_ten_god,
        )
    else:
        _annotate_flow_missing_fields(
            result,
            day_stem=None,
            dayun_ten_god=dayun_ten_god,
            liunian_ten_god=liunian_ten_god,
        )
        if not dayun_ten_god and not liunian_ten_god and "dayun_liunian_context" not in result["missing_fields"]:
            result["missing_fields"].append("dayun_liunian_context")

    return result
