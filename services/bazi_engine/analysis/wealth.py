"""
services/bazi_engine/analysis/wealth.py — 财运引擎 (M2 任务 2.01)

算法规格: §4.11-A
输入:
    yongshen: YongShenResult
    wuxing:   WuxingResult
    shishen:  dict[str, float]     # 十神得分分布
    dayun_list: list[dict]         # 大运列表
输出:
    WealthAnalysisModel
验证:
    wealth_score ≠ strength.score
    tier in {"上","中","下"}
    industries 非空列表
"""
from __future__ import annotations

from app.schemas.analysis import WealthAnalysisModel

# 五行→行业映射
_WUXING_TO_INDUSTRIES: dict[str, list[str]] = {
    "metal":  ["金融", "律政", "机械制造", "珠宝"],
    "wood":   ["教育", "医药", "农林", "食品", "出版"],
    "water":  ["贸易", "运输", "IT", "资讯", "旅游"],
    "fire":   ["传媒", "餐饮", "能源", "娱乐演艺"],
    "earth":  ["房地产", "保险", "建筑", "农业"],
}

# 地支六冲对照
_BRANCH_CHONG: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 天干五行（简化映射）
_STEM_ELEMENT: dict[str, str] = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支五行
_BRANCH_ELEMENT: dict[str, str] = {
    "子": "water", "亥": "water",
    "寅": "wood", "卯": "wood",
    "巳": "fire", "午": "fire",
    "申": "metal", "酉": "metal",
    "丑": "earth", "辰": "earth", "未": "earth", "戌": "earth",
}

# 相生关系（A生B）
_SHENG: dict[str, str] = {
    "wood": "fire", "fire": "earth", "earth": "metal",
    "metal": "water", "water": "wood",
}

# 五行对应中文
_ELEMENT_CN: dict[str, str] = {
    "metal": "金", "wood": "木", "water": "水", "fire": "火", "earth": "土",
}


def compute_wealth(
    yongshen_favor: list[str],
    yongshen_avoid: list[str],
    wuxing_scores: dict[str, float],      # {"wood":..., "fire":..., ...}
    shishen_scores: dict[str, float],     # {"正财":..., "偏财":..., ...}
    strength_score: float,                # 日主强弱分（0-100）
    dayun_list: list[dict],               # 大运列表（每项含 stem/branch/ganzhi）
    day_branch: str = "",                 # 日支（用于地支冲断言）
) -> WealthAnalysisModel:
    """
    §4.11-A 财运引擎

    Parameters:
        yongshen_favor:  用神五行列表（英文，如 ["metal","water"]）
        yongshen_avoid:  忌神五行列表
        wuxing_scores:   五行原始得分字典
        shishen_scores:  十神得分分布
        strength_score:  日主强弱分
        dayun_list:      大运列表
        day_branch:      日支

    Returns:
        WealthAnalysisModel
    """
    # ─── 1. 财星力量 ────────────────────────────────────────────────────────
    zheng_cai = shishen_scores.get("正财", 0.0)
    pian_cai  = shishen_scores.get("偏财", 0.0)
    total_shishen = sum(shishen_scores.values()) or 1.0
    cai_power = (zheng_cai * 1.0 + pian_cai * 0.8) / total_shishen * 100  # 归一化

    # ─── 2. 用神匹配度 ─────────────────────────────────────────────────────
    # 财星五行属于哪些：正财/偏财对应的五行（需要从 wuxing 得分判断）
    total_wx = sum(wuxing_scores.values()) or 1.0
    yongshen_match = sum(
        wuxing_scores.get(e, 0.0) for e in yongshen_favor
    ) / total_wx * 100

    # ─── 3. 月令旺衰系数 ────────────────────────────────────────────────────
    # 简化：用最大五行占比作为旺衰指标（30-50为均衡=0.5；>50为旺）
    max_wx = max(wuxing_scores.values()) if wuxing_scores else 0
    if total_wx > 0:
        max_ratio = max_wx / total_wx
    else:  # pragma: no cover
        max_ratio = 0.0
    wangshuai_coeff = min(1.0, max(0.0, (max_ratio - 0.2) / 0.6))

    # ─── 合计分数 ─────────────────────────────────────────────────────────
    raw_score = cai_power * 0.5 + yongshen_match * 0.3 + wangshuai_coeff * 100 * 0.2

    # 身弱财旺反向修正
    if strength_score < 30:
        raw_score = raw_score * (strength_score / 50)

    wealth_score = int(min(100, max(0, round(raw_score))))

    # tier
    if wealth_score >= 70:
        tier = "上"
    elif wealth_score >= 40:
        tier = "中"
    else:
        tier = "下"

    # ─── 4. 年收入区间估算 ─────────────────────────────────────────────────
    if tier == "上":
        annual_range = "80-200万/年"
    elif tier == "中":
        annual_range = "20-80万/年"
    else:
        annual_range = "10-30万/年"

    # ─── 5. 行业推荐 ─────────────────────────────────────────────────────
    industries: list[str] = []
    for el in yongshen_favor:
        industries.extend(_WUXING_TO_INDUSTRIES.get(el, []))
    if not industries:
        industries = ["贸易", "实业"]
    industries = list(dict.fromkeys(industries))[:5]  # 去重，取前5

    # ─── 6. 大运趋势 ─────────────────────────────────────────────────────
    dayun_forecast: list[dict] = []
    for item in dayun_list:
        gz = item.get("ganzhi") or (
            (item.get("stem") or "") + (item.get("branch") or "")
        )
        stem  = item.get("stem", "")
        branch = item.get("branch", "")
        stem_el   = _STEM_ELEMENT.get(stem, "")
        branch_el = _BRANCH_ELEMENT.get(branch, "")

        # 天干与日主关系：先判断基础趋势
        if stem_el and yongshen_favor and stem_el in yongshen_favor:
            trend = "上升"
        elif stem_el and yongshen_avoid and stem_el in yongshen_avoid:
            trend = "下降"
        else:
            trend = "平稳"

        # 地支修正：冲日支 → 降级
        if day_branch and branch and _BRANCH_CHONG.get(branch) == day_branch:
            if trend == "上升":
                trend = "平稳"
            elif trend == "平稳":
                trend = "下降"
        # 地支与用神五行同气 → 升级
        elif branch_el and yongshen_favor and branch_el in yongshen_favor:
            if trend == "下降":
                trend = "平稳"
            elif trend == "平稳":
                trend = "上升"

        # 生成趋势说明语（依据天干/地支五行组合差异化描述）
        stem_cn   = _ELEMENT_CN.get(stem_el, "")
        branch_cn = _ELEMENT_CN.get(branch_el, "")
        branch_in_favor = bool(branch_el and yongshen_favor and branch_el in yongshen_favor)
        branch_in_avoid = bool(branch_el and yongshen_avoid and branch_el in yongshen_avoid)

        if trend == "上升":
            if branch_in_favor:
                trend_desc = (
                    f"{gz}大运：天干{stem_cn}、地支{branch_cn}双顺用神，财运进入强势上升通道。"
                    f"宜主动布局多元收益，稳健配置长线资产，把握大运红利。"
                )
            elif branch_in_avoid:
                trend_desc = (
                    f"{gz}大运：天干{stem_cn}顺用神，地支{branch_cn}稍有阻力，财运上升中需稳中求进。"
                    f"主动开拓收入渠道，同时注意防范地支带来的小挫折，不宜过度冒进。"
                )
            else:
                trend_desc = (
                    f"{gz}大运：天干{stem_cn}五行顺用神，财运进入上升通道。"
                    f"适合主动拓展主副业收益，顺势而为积累财富底仓。"
                )
        elif trend == "下降":
            trend_desc = (
                f"{gz}大运：天干{stem_cn}与用神相忌，财运进入收缩期，守成为主。"
                f"控制投资风险与负债规模，精简开支，等待下一顺运大运再谋进取。"
            )
        else:
            if branch_in_favor:
                trend_desc = (
                    f"{gz}大运：天干中和，地支{branch_cn}有用神之气托底，财运平稳中带稳。"
                    f"可小步稳健理财，守住本职收入，不必冒进。"
                )
            elif branch_in_avoid:
                trend_desc = (
                    f"{gz}大运：天干中和，地支{branch_cn}稍逆用神，财运偏平。"
                    f"守住既有资产，精简无效支出，为下一顺运期积累资本。"
                )
            else:
                trend_desc = (
                    f"{gz}大运：财运平稳，五行中和，收支基本均衡。"
                    f"轻装稳打，稳健发展为宜，不必冒进。"
                )

        dayun_forecast.append({"ganzhi": gz, "trend": trend, "description": trend_desc})

    # ─── 7. 策略建议 ─────────────────────────────────────────────────────
    if tier == "上":
        strategy = (
            "财运旺盛期，适当加大主动收入的投入力度，多路并进开拓增量渠道。"
            "投资方面可尝试中长期配置，但需避免过度分散或盲目追高风险行业。"
            "建议每季强制存入流动盈余的 20％，为个人资产建立安全垫。"
        )
    elif tier == "中":
        strategy = (
            "财运属中等层，稳中求进是最佳策略，守住主职收入并少量开拓副业。"
            "投资选择温和型品种（稳健基金、定期定投），避免购买高风险行业股或高杠杆衍生品。"
            "建议增强财务记账习惯，清楚每月收支结构再作决策。"
        )
    else:
        strategy = (
            "财运属弱势层，守成减负是首要任务，修复财务漏洞和高息负债。"
            "在此阶段重点积累专业技能和行业资源，为下一个财运高峰提前积蓄力量。"
            "尽量避免借贷或为他人担保，勿在劣势期购入投资性资产。"
        )

    # ─── inference_tags ─────────────────────────────────────────────────
    tags = []
    if zheng_cai > 0.5:
        tags.append("正财有根")
    if pian_cai > 0.5:
        tags.append("偏财有力")
    if yongshen_favor:
        tags.append(f"用神{''.join(_ELEMENT_CN.get(e, e) for e in yongshen_favor)}")
    if strength_score < 30:
        tags.append("财多身弱主贫困警示")

    # ─── interpretation_text ────────────────────────────────────────────
    _ys_cn = "、".join(_ELEMENT_CN.get(e, e) for e in yongshen_favor) or "未知"
    _ind_top3 = "、".join(industries[:3])
    interp = (
        f"此命财运综合评分为 {wealth_score} 分（{tier}等），"
        f"财星力量指数 {cai_power:.0f}/100，"
        f"用神五行属【{_ys_cn}】，命局对财运的支配程度属 {tier}级。"
        f"综合财星强弱与用神匹配度，预计年收入区间为 {annual_range}，"
        f"推荐最适宜进入的行业领域为：{_ind_top3}。"
        f"{strategy}"
        f"（仅供学术研究参考）"
    )

    # ─── 新增：投资偏好 ──────────────────────────────────────────────────
    zheng_cai_pct = zheng_cai / total_shishen
    pian_cai_pct  = pian_cai  / total_shishen
    if zheng_cai_pct > pian_cai_pct and zheng_cai_pct >= 0.12:
        investment_preference = (
            f"正财有根（正财占比{zheng_cai_pct:.0%}），天然倾向稳健收益型投资。"
            "建议采用「核心+卫星」资产配置：60-70%配置债券基金/稳健理财，"
            "20-30%配置指数基金进行长期定投，5-10%保留流动储备。"
            "投资决策应遵循最小12个月验证周期，避免追热点短炒；"
            "年复合回报预期维持在8-15%为合理区间，不轻易追求超额收益。"
        )
    elif pian_cai_pct > zheng_cai_pct and pian_cai_pct >= 0.12:
        investment_preference = (
            f"偏财有力（偏财占比{pian_cai_pct:.0%}），天然具备捕捉机会的商业敏锐性。"
            "建议配合「机会主义+纪律性」策略：设置严格止损线（亏损超15%强制离场），"
            "仅在用神顺运大运年才可增加高风险仓位（不超总资产35%）。"
            "任何单笔投资仓位不超10%，并强制建立「失控复盘清单」，记录失败投资优化决策。"
        )
    elif zheng_cai_pct >= 0.08 and pian_cai_pct >= 0.08:
        investment_preference = (
            "正财偏财并存，兼具稳健与机会捕捉能力，适合「均衡型」组合。"
            "建议50%配置稳健基金/REITs，30%配置精选个股/主题ETF，20%保留流动现金；"
            "每季度进行一次仓位再平衡，防止偏财旺性引发过度集中持仓风险。"
        )
    else:
        investment_preference = (
            "财星力量偏弱，财富积累应以「提升总体收入」为第一优先级，而非追求投资超额回报。"
            "建议将80%以上资产配置于货币基金或银行定存等防御性工具，"
            "以技能提升带来的主动收入增长为核心策略，待大运财运顺势后再逐步增加投资仓位。"
        )

    # ─── 新增：财务禁区 ──────────────────────────────────────────────────
    taboo_items: list[str] = []
    for el in yongshen_avoid[:2]:
        ind_list = _WUXING_TO_INDUSTRIES.get(el, [])
        el_cn_str = _ELEMENT_CN.get(el, el)
        if ind_list:
            taboo_items.append(
                f"忌神五行属{el_cn_str}，对应行业（{'、'.join(ind_list[:3])}）"
                "为财运高风险领域，投资或创业须谨慎进入，强烈建议不超总资产5%试仓。"
            )
    if strength_score < 30 and (zheng_cai_pct + pian_cai_pct) > 0.25:
        taboo_items.append(
            "身弱财多（日主力量不足以驾驭财星），切忌大规模举债投资或为他人担保，"
            "否则极易在财运高峰期遭遇反向财务危机，须先强主气（行用神旺运）再谈驾驭财富。"
        )
    if pian_cai_pct >= 0.3:
        taboo_items.append(
            "偏财过旺，对高风险高回报项目吸引力极强，须特别警惕「一夜暴富」型项目诱惑，"
            "以及涉及陌生人担保、传销性质投资、杠杆率超3倍的金融衍生品，防止倾家荡产式风险。"
        )
    if not taboo_items:
        taboo_items.append(
            "命局财星结构较为均衡，无明显财务禁区，维持稳健理财习惯、保持合理负债率（低于40%）即可；"
            "仍需在大运忌神当令年份警惕轻率投资与情绪性超支消费行为。"
        )
    financial_taboos = "；".join(taboo_items)

    # ─── 新增：财富积累三阶段规划 ────────────────────────────────────────
    _phases: list[str] = []
    for i, dy in enumerate(dayun_list[:3]):
        gz = dy.get("ganzhi") or (
            (dy.get("stem") or "") + (dy.get("branch") or "")
        )
        stem_el = _STEM_ELEMENT.get(dy.get("stem", ""), "")
        start_age = dy.get("start_age", "")
        end_age   = dy.get("end_age", "")
        age_str = f"{start_age}-{end_age}岁" if start_age or end_age else f"第{i + 1}大运"
        if stem_el and yongshen_favor and stem_el in yongshen_favor:
            phase_strategy = (
                f"【{gz}大运·{age_str}】财运上升期：主动布局多元收入，"
                "可适当提升权益类投资仓位至30-40%，此为财富跃升的关键窗口，宜大胆推进。"
            )
        elif stem_el and yongshen_avoid and stem_el in yongshen_avoid:
            phase_strategy = (
                f"【{gz}大运·{age_str}】财运收缩期：以保守守成为主，压缩投资风险仓位至10%以下，"
                "集中清偿高息债务，储备3-6个月生活支出的流动应急资金，蓄力待机。"
            )
        else:
            phase_strategy = (
                f"【{gz}大运·{age_str}】财运平稳期：维持均衡配置，"
                "坚持每月定投指数基金，将月收入10-15%转入专项储蓄积累复利基础。"
            )
        _phases.append(phase_strategy)
    if not _phases:
        _phases = [
            "【早期阶段】以「开源为主、节流为辅」为核心，重点投资技能与人脉提升主动收入。",
            "【中期阶段】在用神顺运大运中积极扩大投资仓位，形成收入多元化格局。",
            "【成熟阶段】以资产保值增值为主，布局稳健性现金流资产，形成坚实财富护城河。",
        ]
    wealth_accumulation_phases = "".join(_phases)

    return WealthAnalysisModel(
        wealth_score=wealth_score,
        wealth_tier=tier,
        annual_range=annual_range,
        industries=industries,
        strategy=strategy,
        dayun_forecast=dayun_forecast,
        inference_tags=tags,
        interpretation_text=(
            f"此命财运综合评分为 {wealth_score} 分（{tier}等），"
            f"财星力量指数 {cai_power:.0f}/100，"
            f"用神五行属【{_ys_cn}】。\n"
            f"预计年收入区间为 {annual_range}，推荐首选行业：{_ind_top3}。\n"
            f"【财务策略】{strategy}\n"
            f"【投资偏好】{investment_preference}\n"
            f"【财务禁区】{financial_taboos}\n"
            f"【财富积累三阶段】{wealth_accumulation_phases}"
            f"（仅供学术研究参考）"
        ),
        investment_preference=investment_preference,
        financial_taboos=financial_taboos,
        wealth_accumulation_phases=wealth_accumulation_phases,
    )
