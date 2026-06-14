"""
services/bazi_engine/analysis/wealth_estimate.py — 财富数额估算 (M3 任务 3.03)

估算公式（M3规格）:
  base = 高格 80万 | 中格 40万 | 低格 15万
  × 大运系数(上升1.2 / 平稳1.0 / 下降0.8)
  × 地区系数(一线1.8 / 新一线1.2 / 其余1.0)
  × 行业系数(金融/IT 1.5 / 教育公务 0.8 / 其余 1.0)

单位: 万元 RMB（年收入峰值估算，非总财富）
"""

from __future__ import annotations

from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────────────────────
# 系数映射
# ──────────────────────────────────────────────────────────────────────────────

# 基础值（万元）
BASE_AMOUNT: dict[str, float] = {
    "高格": 80.0,
    "中格": 40.0,
    "低格": 15.0,
}

# 大运系数
DAYUN_COEFF: dict[str, float] = {
    "上升": 1.2,
    "平稳": 1.0,
    "下降": 0.8,
}

# 地区系数
CITY_TIER_COEFF: dict[str, float] = {
    "一线": 1.8,  # 北京/上海/广州/深圳
    "新一线": 1.2,  # 成都/杭州/南京/武汉/重庆/西安/苏州/天津/郑州/长沙/东莞/佛山/沈阳/宁波/青岛
    "其余": 1.0,
}

# 行业系数
INDUSTRY_COEFF: dict[str, float] = {
    "金融": 1.5,
    "IT": 1.5,
    "互联网": 1.5,
    "投资": 1.5,
    "教育": 0.8,
    "公务员": 0.8,
    "医疗": 0.9,
    "制造": 1.0,
    "商贸": 1.1,
    "文化": 0.9,
    "其余": 1.0,
}

# 一线城市列表（用于自动判断tier）
TIER1_CITIES = {"北京", "上海", "广州", "深圳"}
NEW_TIER1_CITIES = {
    "成都",
    "杭州",
    "南京",
    "武汉",
    "重庆",
    "西安",
    "苏州",
    "天津",
    "郑州",
    "长沙",
    "东莞",
    "佛山",
    "沈阳",
    "宁波",
    "青岛",
}


@dataclass
class WealthEstimate:
    """财富估算结果"""

    base_amount: float  # 基础值（万元）
    dayun_coeff: float  # 大运系数
    city_coeff: float  # 地区系数
    industry_coeff: float  # 行业系数
    estimated_amount: float  # 估算值（万元）
    low_bound: float  # 下限（万元，×0.7）
    high_bound: float  # 上限（万元，×1.5）
    wealth_tier: str  # 高格/中格/低格
    note: str  # 注解说明
    disclaimer: str = (
        "本估算为推演模型输出，仅供学术研究参考，"
        "不构成任何形式的财富预测或投资建议。"
        "实际收入受宏观经济、个人努力及机遇等多重因素影响。"
    )


def estimate_wealth(
    wealth_tier: str,
    dayun_trend: str = "平稳",
    city: str | None = None,
    city_tier: str | None = None,
    industry: str | None = None,
) -> WealthEstimate:
    """
    M3 任务3.03 — 财富数额估算

    参数:
        wealth_tier:  命局财富等级（高格/中格/低格）
        dayun_trend:  当前大运趋势（上升/平稳/下降）
        city:         城市名（选填，用于自动判断tier）
        city_tier:    城市等级（一线/新一线/其余，优先级高于city）
        industry:     行业名称（选填）

    返回:
        WealthEstimate 实例
    """
    base = BASE_AMOUNT.get(wealth_tier, BASE_AMOUNT["中格"])
    dc = DAYUN_COEFF.get(dayun_trend, 1.0)

    # 确定城市等级
    if city_tier and city_tier in CITY_TIER_COEFF:
        cc = CITY_TIER_COEFF[city_tier]
        tier_label = city_tier
    elif city:
        if city in TIER1_CITIES:
            cc = CITY_TIER_COEFF["一线"]
            tier_label = "一线"
        elif city in NEW_TIER1_CITIES:
            cc = CITY_TIER_COEFF["新一线"]
            tier_label = "新一线"
        else:
            cc = CITY_TIER_COEFF["其余"]
            tier_label = "其余"
    else:
        cc = 1.0
        tier_label = "其余"

    # 确定行业系数
    ic = 1.0
    ind_label = "其余"
    if industry:
        for key, coeff in INDUSTRY_COEFF.items():
            if key in industry:
                ic = coeff
                ind_label = key
                break

    estimated = round(base * dc * cc * ic, 2)
    low_bound = round(estimated * 0.7, 2)
    high_bound = round(estimated * 1.5, 2)

    note = (
        f"估算基础：{wealth_tier}命局基准{base}万元"
        f" × 大运系数{dc:.1f}（{dayun_trend}）"
        f" × 地区系数{cc:.1f}（{tier_label}城市）"
        f" × 行业系数{ic:.1f}（{ind_label}）"
        f" = 约{estimated}万元/年峰值收入"
        f"，合理区间：{low_bound}—{high_bound}万元。"
    )

    return WealthEstimate(
        base_amount=base,
        dayun_coeff=dc,
        city_coeff=cc,
        industry_coeff=ic,
        estimated_amount=estimated,
        low_bound=low_bound,
        high_bound=high_bound,
        wealth_tier=wealth_tier,
        note=note,
    )


def wealth_estimate_to_dict(est: WealthEstimate) -> dict:
    """转换为 JSON 可序列化的字典"""
    return {
        "estimated_amount_wan": est.estimated_amount,
        "range_wan": {"low": est.low_bound, "high": est.high_bound},
        "coefficients": {
            "base_amount": est.base_amount,
            "dayun": est.dayun_coeff,
            "city": est.city_coeff,
            "industry": est.industry_coeff,
        },
        "wealth_tier": est.wealth_tier,
        "note": est.note,
        "disclaimer": est.disclaimer,
    }
