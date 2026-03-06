"""
services/bazi_engine/analysis/liunian_domain.py — 流年四维预测 (M3 §4.11-H)

四维: 财运 / 事业 / 婚恋 / 健康

规则（优先流年十神作主分支，兼顾命局五行特征）：
  财运（流年十神主导）:
    正财               → 本职收入稳定增长，宜稳健拓展
    偏财               → 横财与副业机遇活跃，把握流动性
    比肩               → 竞争加剧，防市场份额被抢
    劫财               → 财运起伏，防破财与合伙纠纷
    偏印               → 印星压财，守成减负
    正印               → 财运平稳，中长期规划
    食神               → 以才华换报酬，持续性收入可期
    伤官               → 变数并存，创新与守正并举
    正官               → 职位带动收入，薪资谈判有利
    七杀               → 财运波动大，防冲动决策
    （无十神）         → 按命局比劫/财星/印星率作分支
  事业（流年十神主导）:
    正官               → 升迁机遇明显，宜主动请缨
    七杀               → 压力化动力，合规行事
    食神               → 创造力爆发，展才华
    伤官               → 转型/创业窗口
    正印/偏印          → 进修考证，技能积累
    比肩               → 合作大于竞争
    劫财               → 职场竞争激烈，守本分
    正财/偏财          → 薪资增长，财务岗位利好
    （无十神）         → 按驿马/用神/默认逻辑
  婚恋:
    优先流年十神匹配 → 年特有感情场景
    其次命局官杀兼顾 → 女命官缘/七杀扰动
    再次流年用神    → 感情顺畅
    通用            → 感情平稳
  健康:
    克日主五行占优   → 对应脏腑承压
    某五行>50%       → 关注对应脏腑保养
    与用神合         → 身体状态佳
    通用             → 健康平稳
"""
from __future__ import annotations

from typing import Literal

# 五行与脏腑对应
_ORGAN_MAP = {
    "wood":  "肝胆",
    "fire":  "心血管",
    "earth": "脾胃",
    "metal": "肺肠",
    "water": "肾脏",
}

# 五行克关系：A克B
_OVERCOME: dict[str, str] = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}

# 干支对应五行（天干）
_STEM_WUXING = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支桃花规则：年/日支三合局首支 → 桃花地支
_TAOHUAL_MAP = {
    "寅": "卯", "午": "卯", "戌": "卯",   # 寅午戌 → 桃花在卯
    "亥": "子", "卯": "子", "未": "子",   # 亥卯未 → 桃花在子
    "申": "酉", "子": "酉", "辰": "酉",   # 申子辰 → 桃花在酉
    "巳": "午", "酉": "午", "丑": "午",   # 巳酉丑 → 桃花在午
}

# 地支驿马规则：年支三合局→驿马地支
_YIMA_MAP = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "亥": "巳", "卯": "巳", "未": "巳",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

def _is_taohua(day_branch: str, year_branch: str) -> bool:
    taohua = _TAOHUAL_MAP.get(day_branch)
    return taohua == year_branch


def _is_yima(day_branch: str, year_branch: str) -> bool:
    yima = _YIMA_MAP.get(day_branch)
    return yima == year_branch


def compute_liunian_domain_forecasts(
    year:            int,
    year_stem:       str,
    year_branch:     str,
    day_stem:        str,
    day_branch:      str,
    shishen_scores:  dict[str, float],
    yongshen_favor:  list[str],
    wuxing_scores:   dict[str, float],
    gender:          str = "male",
    year_ten_god:    str = "",          # 流年天干对日主的十神（优先分支）
) -> dict[str, str]:
    """
    M3 §4.11-H — 流年四维预测

    参数:
        year:           流年年份（如 2025）
        year_stem:      流年天干（甲/乙/...）
        year_branch:    流年地支（子/丑/...）
        day_stem:       日主天干
        day_branch:     日柱地支（用于桃花/驿马计算）
        shishen_scores: 十神占比 {十神名: float}（命局固定值）
        yongshen_favor: 用神五行列表（英文）
        wuxing_scores:  五行分布 {english: float}（命局固定值）
        gender:         "male" / "female"
        year_ten_god:   流年天干对日主的十神（优先用于分支判断，空串回退到命局逻辑）

    返回:
        {"财运": str, "事业": str, "婚恋": str, "健康": str}
    """
    year_wuxing = _STEM_WUXING.get(year_stem, "")
    day_wuxing  = _STEM_WUXING.get(day_stem, "")
    total_wx    = sum(wuxing_scores.values()) or 1.0

    # ── 财运 ──────────────────────────────────────────────────────────────────
    # 优先用流年十神作主分支，命局分布作备用
    if year_ten_god == "正财":
        caiyun = (
            f"{year}年正财当令，本职收入稳定，薪资调整或绩效奖金落袋机会较大。"
            f"可主动申请加薪或对接稳健投资渠道，把握财运高峰期。"
            f"注意合同与票据管理，签约前核查条款，防止细节失财。"
        )
    elif year_ten_god == "偏财":
        caiyun = (
            f"{year}年偏财临年，横财与意外收益活跃，适合拓展副业与投资理财机遇。"
            f"建议分散风险、小步试水，把握流动性强的短期机会，不宜孤注一掷。"
            f"偏财性质流动，及时落袋为安，防财来财去白忙一场。"
        )
    elif year_ten_god == "劫财":
        caiyun = (
            f"{year}年劫财临年，财运起伏明显，合伙与口头承诺易引发财务纠纷。"
            f"重要协议须书面落实，避免为他人担保，独立掌控资金是本年底线。"
            f"理财以守为主，减少投机风险敞口，稳住本金优先于追逐收益。"
        )
    elif year_ten_god == "比肩":
        caiyun = (
            f"{year}年比肩临年，同行竞争加剧，市场份额面临压制，财务竞争风险偏高。"
            f"差异化定位是破局关键，深耕专业领域增强不可替代性。"
            f"合伙生意须谨慎，共识需书面确认，防因利益分歧引发纠纷。"
        )
    elif year_ten_god == "偏印":
        caiyun = (
            f"{year}年偏印临年，财星受制，正财进账偏缓，不宜激进投资。"
            f"适合学习财务规划知识、梳理资产结构，为下一财运高峰积累基础。"
            f"精简开支，控制冲动消费，守成减负方为上策。"
        )
    elif year_ten_god == "正印":
        caiyun = (
            f"{year}年正印当令，财运平稳，收支基本平衡，无大的意外横财。"
            f"适合复盘资产配置，规划中长期理财，以稳健原则守住已有积累。"
            f"不宜追涨杀跌，合法合规经营理财，守稳本金即为财。"
        )
    elif year_ten_god == "食神":
        caiyun = (
            f"{year}年食神生财，以专业技能与创造力换取报酬，持续性收入可期。"
            f"技术服务、内容创作、教学咨询等领域尤为有利，展才即得财。"
            f"投入与产出成正比，认真打磨作品与口碑，财运随之水涨船高。"
        )
    elif year_ten_god == "伤官":
        caiyun = (
            f"{year}年伤官当令，财运有变数，创业与副业机会与风险并存。"
            f"创新项目可带来额外收入，但须控制成本、防止过度扩张。"
            f"正职收入稳固后再布局副业，守正方能破奇。"
        )
    elif year_ten_god == "正官":
        caiyun = (
            f"{year}年正官入局，职务晋升有望带动收入增长，本职为最稳收入来源。"
            f"宜做好薪资谈判准备，职场人脉积累将带来额外商业机遇。"
            f"同步启动理财规划，为未来资产增值打好基础。"
        )
    elif year_ten_god == "七杀":
        caiyun = (
            f"{year}年七杀临年，财运波动偏大，防冲动投资酿成损失。"
            f"审慎评估高收益项目，遇有超额回报承诺须格外警惕。"
            f"守住本职稳定收入，财务安全线优先于追逐暴利机会。"
        )
    else:
        # 无流年十神时，回退到命局分布逻辑
        zhengcai_score = shishen_scores.get("正财", 0.0)
        piancai_score  = shishen_scores.get("偏财", 0.0)
        bijie_score    = (shishen_scores.get("比肩", 0.0) +
                          shishen_scores.get("劫财", 0.0))
        has_cai_yongshen = bool(yongshen_favor)  # 用神存在即有财运支撑
        yin_score = (shishen_scores.get("正印", 0.0) + shishen_scores.get("偏印", 0.0))

        if (zhengcai_score > 0.1 or piancai_score > 0.1) and has_cai_yongshen:
            caiyun = (
                f"{year}年正财当令，用神顺势得力，财运进入活跃期。"
                f"宜积极拓展新收入渠道，副业兼职或投资理财均有斩获，把握上半年财运高峰。"
                f"注意合同与票据管理，签约前仔细核查条款，防止漏洞失财。"
            )
        elif bijie_score > 0.35:
            caiyun = (
                f"{year}年比劫争财局面显现，竞争者环绕，财务竞争风险偏高。"
                f"合伙生意需谨慎，建议书面确认权责，防止口头承诺引发纠纷。"
                f"守成为上，减少不必要投资，稳住本职收入为先。"
            )
        elif yin_score > 0.3 and year_wuxing not in yongshen_favor:
            caiyun = (
                f"{year}年印星压财，财星受制，正财进账偏缓。"
                f"适合复盘已有资产配置，学习财务知识规划未来，精简开支填补缺口。"
                f"勿轻易投机，以稳健理财方式积累资本。"
            )
        elif (zhengcai_score + piancai_score) < 0.05:
            caiyun = (
                f"{year}年财气偏弱，主动创收阻力较大，守成减负为宜。"
                f"谨防支出超支，勿轻易借贷或为他人担保，控制消费冲动。"
                f"可将精力转向技能提升，为下一个财运高峰期蓄力。"
            )
        elif year_wuxing in yongshen_favor:
            caiyun = (
                f"{year}年流年五行顺用神，财运有明显小幅提升。"
                f"适合把握短期机遇小试牛刀，谨慎中不失进取，财务决策宜快不宜拖。"
                f"建议在上半年确定主要收入方向，下半年稳固成果。"
            )
        else:
            caiyun = (
                f"{year}年财运整体平稳，无大起大落，宜按既定计划执行理财规划。"
                f"定期收支记账，优化消费结构，尽早清理高息负债。"
                f"不宜贸然冒进，守住当前收入基础即为上策。"
            )

    # ── 事业 ──────────────────────────────────────────────────────────────────
    # 优先用流年十神作主分支，命局分布/驿马作备用
    is_yima = _is_yima(day_branch, year_branch)
    guansha_score  = (shishen_scores.get("正官", 0.0) +
                      shishen_scores.get("七杀", 0.0))
    shishang_score = (shishen_scores.get("食神", 0.0) +
                      shishen_scores.get("伤官", 0.0))

    if year_ten_god == "正官":
        shiye = (
            f"{year}年正官护身，职场规则清晰，是争取晋升与调薪的有利时机。"
            f"上司对你表现格外关注，宜主动请缨承担核心项目，充分展现执行力与专业素养。"
            f"遵守制度规范，合规行事将为长期发展积累良好口碑。"
        )
    elif year_ten_god == "七杀":
        shiye = (
            f"{year}年七杀临年，职场压力明显增大，外部挑战与内部摩擦同步升级。"
            f"化压力为动力，以实力说话；减少情绪化反应，冷静处置职场矛盾。"
            f"遵守边界、谨防越权，低调求稳方能规避风险。"
        )
    elif year_ten_god == "食神":
        shiye = (
            f"{year}年食神显能，创造力与表达力进入高峰期，专业形象大幅提升。"
            f"主动展示成果与作品，技术型人才本年尤有突破空间。"
            f"申请专利、发表成果或公开演讲均可有效推动职业能见度。"
        )
    elif year_ten_god == "伤官":
        shiye = (
            f"{year}年伤官当令，宜跳出固有框架，探索自主创业或职业转型机遇。"
            f"创新风格与个人特质是突破职场天花板的核心竞争力。"
            f"注意维护上下级关系，伤官年易生顶撞，沟通方式以柔克刚为宜。"
        )
    elif year_ten_god == "正印":
        shiye = (
            f"{year}年正印护身，考证、进修与学历提升均有利好，学习转化率高。"
            f"深耕专业技能，稳步提升行业知名度，领导认可度同步提升。"
            f"本年以积累为主，厚积薄发，成果将在后续顺运年份集中展现。"
        )
    elif year_ten_god == "偏印":
        shiye = (
            f"{year}年偏印临年，宜低调深耕，独立完成核心任务，展现专业可靠性。"
            f"研究型、幕后型岗位本年效率高，避免高调发言以防招致批评。"
            f"稳扎稳打，等待时机是本年职场最优策略。"
        )
    elif year_ten_god == "比肩":
        shiye = (
            f"{year}年比肩助力，团队协作机遇增多，合伙推进项目比单打独斗更有成效。"
            f"主动参与跨部门合作，借助同频人的资源拓展边界。"
            f"善用集体力量，注意分清职责，避免责任模糊地带引发摩擦。"
        )
    elif year_ten_god == "劫财":
        shiye = (
            f"{year}年劫财临年，职场竞争加剧，防同事或竞争者抢占机会。"
            f"坚守岗位本分，以厚实业绩说话，而非靠关系与投机取巧。"
            f"收紧个人信息，防止核心资源或方案被他人借用。"
        )
    elif year_ten_god in ("正财", "偏财"):
        shiye = (
            f"{year}年财星入职场，薪资谈判与职务晋升机遇同步开启。"
            f"积极把握年底绩效评定窗口，整理业绩材料争取加薪或晋升。"
            f"财运与职场联动，稳住核心业务的同时可探索跨界合作。"
        )
    elif is_yima:
        shiye = (
            f"{year}年驿马临命，宜出差调动、探索新市场，外出奔波反而有利于开运。"
            f"异地合作、跨城市项目或海外业务均有发展机遇，不必拘泥于本地圈子。"
            f"保持灵活机动，随机应变是本年职场制胜关键。"
        )
    elif guansha_score > 0.2:
        shiye = (
            f"{year}年官杀当旺，职场升迁信号明显，上司或贵人对你表现格外关注。"
            f"宜主动请缨承担重要项目，展现领导力与执行力，争取晋升或调薪机会。"
            f"注意规章制度，官杀之年行事须合规，切勿逾越职场边界。"
        )
    elif shishang_score > 0.2 and year_wuxing in yongshen_favor:
        shiye = (
            f"{year}年食伤生财，创造力与表达力进入高峰，适合开拓新业务或副业。"
            f"以专业才华换取成果，技术型独立工作者本年尤其有突破空间。"
            f"可考虑展示个人作品集或申请专利，将创意变现。"
        )
    elif year_wuxing in yongshen_favor:
        shiye = (
            f"{year}年流年顺应用神，事业稳中有进，专注本职岗位可有所突破。"
            f"适合深耕专业技能，完善个人知识体系，积累行业资源与口碑。"
            f"稳扎稳打，以量变推动质变，本年奠基为主，成果将在下一个大运期显现。"
        )
    else:
        shiye = (
            f"{year}年职场气场偏平，宜避免轻易跳槽或创业，维持现有格局为先。"
            f"利用空档期主动学习、考证、建立行业人脉，为下一个顺运年份蓄势。"
            f"减少无谓内耗，聚焦最核心的工作交付，保持职业信誉。"
        )

    # ── 婚恋 ──────────────────────────────────────────────────────────────────
    # 优先：桃花/流年十神特殊场景；其次：命局官杀女命；再次：用神/通用
    guanxing_score = shishen_scores.get("正官", 0.0)
    qisha_score    = shishen_scores.get("七杀", 0.0)
    is_taohua      = _is_taohua(day_branch, year_branch)

    if is_taohua:
        hunlian = (
            f"{year}年桃花临年支，感情缘分进入旺盛周期。"
            f"单身者宜主动扩大社交圈，参加聚会、兴趣社群，正缘可能出现于日常偶遇。"
            f"已婚者注重感情保鲜，策划小惊喜与旅行，防止第三者介入。"
        )
    elif year_ten_god == "正官" and gender == "female":
        hunlian = (
            f"{year}年官星透出，女命夫星得令，感情正缘机遇显现。"
            f"宜主动扩大社交范围，借助亲友介绍或正式社交场合接触稳重异性。"
            f"已婚者夫妻感情稳固，共同规划未来，感情质量持续升温。"
        )
    elif year_ten_god == "七杀" and gender == "female":
        hunlian = (
            f"{year}年七杀透出，女命感情关系有摩擦波折，情绪张力偏大。"
            f"冷静面对感情变化，不宜冲动做出分手或缔结婚约等重大决定。"
            f"给予彼此独立空间，理性沟通化解争执，勿以情绪主导感情走向。"
        )
    elif year_ten_god == "伤官" and gender == "female":
        hunlian = (
            f"{year}年伤官临年，女命感情易生波折，与伴侣观点分歧增多。"
            f"以包容替代对抗，减少要求改变对方的执念，给感情更多成长空间。"
            f"单身者此年不宜匆促确立关系，多了解对方再做决定。"
        )
    elif year_ten_god == "偏财" and gender == "male":
        hunlian = (
            f"{year}年偏财当令，男命桃花缘分活跃，社交场合异性互动明显增多。"
            f"单身者可开放心态，把握正缘机遇；已婚者防异性纠纷，清晰划定界限。"
            f"感情中以真诚为上，切勿因一时冲动影响长期感情稳定性。"
        )
    elif year_ten_god in ("比肩", "劫财"):
        hunlian = (
            f"{year}年比劫临年，感情中第三方干扰风险有所提升，需警惕外部诱惑。"
            f"主动投入感情经营，增加与伴侣高质量互动，提升感情黏性。"
            f"单身者注意辨别追求者诚意，防止因利益驱动的虚假感情介入。"
        )
    elif year_ten_god == "正印":
        hunlian = (
            f"{year}年正印护身，感情关系理性稳健，注重精神层面的契合与共鸣。"
            f"深度交流与共同成长是本年增进感情的最佳方式。"
            f"单身者不急于求结果，遇到有共同价值观的人再认真发展。"
        )
    elif year_ten_god == "偏印":
        hunlian = (
            f"{year}年偏印临年，感情关系偏内敛，情绪不易表达，易产生误解。"
            f"主动打开心扉，适当增加与伴侣的情感表达，减少因沉默引发的隔阂。"
            f"单身者可广泛社交，等待与志同道合者自然相遇。"
        )
    elif year_ten_god == "食神":
        hunlian = (
            f"{year}年食神临年，感情温和滋养，互动轻松愉快，关系有增温迹象。"
            f"以共同活动与兴趣爱好为纽带，加深彼此了解，双方都舒适自在。"
            f"单身者从友谊出发自然发展，感情萌芽于日常相处之中。"
        )
    elif year_ten_god == "正官" and gender == "male":
        hunlian = (
            f"{year}年正官护身，男命感情务实稳重，注重长期承诺与责任感。"
            f"宜在稳定情感基础上推进关系，对独立生活与家庭规划有积极意义。"
            f"已婚者以可靠与包容经营感情，夫妻关系稳中向好。"
        )
    elif year_ten_god == "七杀" and gender == "male":
        hunlian = (
            f"{year}年七杀临年，男命感情易受外部压力波及，情绪波动需关注。"
            f"主动舒缓职场与生活压力，避免将负能量带入亲密关系。"
            f"坦诚沟通是化解感情危机的最佳方式，勿让沉默扩大裂缝。"
        )
    elif gender == "female" and guanxing_score > 0.15:
        hunlian = (
            f"{year}年官星透出，女命有正式感情机遇，有缘遇见气场稳重的异性。"
            f"单身者宜减少自我封闭，借助朋友介绍或正式社交场合拓展圈子。"
            f"已婚者感情基础稳固，宜共同规划未来，感情升温有利家庭和谐。"
        )
    elif gender == "female" and qisha_score > 0.2:
        hunlian = (
            f"{year}年七杀透出，感情关系有摩擦与变数，情绪波动较大。"
            f"宜冷静面对感情挫折，不轻率做分手或结婚等重大决策，理性沟通优先。"
            f"给自己和伴侣足够的独立空间，避免控制欲或争执升级。"
        )
    elif year_wuxing in yongshen_favor:
        hunlian = (
            f"{year}年流年气场和谐，感情整体顺畅，互动增多、关系升温。"
            f"单身者有望遇到真诚相配之人；伴侣感情可考虑进一步确立关系。"
            f"已婚者夫妻默契提升，共同出行或参与活动有助于拉近距离。"
        )
    else:
        hunlian = (
            f"{year}年感情运势平稳，无明显大起大落，重在经营现有亲密关系。"
            f"主动倾听伴侣需求，减少因小事引发的争执，以耐心换取信任。"
            f"单身者不必急于求成，内修自我才是吸引良缘的根本。"
        )

    # ── 健康 ──────────────────────────────────────────────────────────────────
    克day = _OVERCOME.get(year_wuxing, "")
    is_克day = (克day == day_wuxing) if 克day else False

    dominant_el = max(wuxing_scores, key=lambda k: wuxing_scores.get(k, 0.0)) if wuxing_scores else ""
    dominant_ratio = wuxing_scores.get(dominant_el, 0) / total_wx if dominant_el else 0

    is_yongshen_favorable_year = year_wuxing in yongshen_favor

    if is_克day:
        organ = _ORGAN_MAP.get(day_wuxing, "脏腑")
        jiankang = (
            f"{year}年流年五行克制日主，{organ}系统承压，注意定期检查。"
            f"防止精力透支，保证充足睡眠（7-8小时），减少不必要的熬夜与应酬。"
            f"情志保持平和，避免忧思过重，调节压力是本年养生重点。"
        )
    elif dominant_ratio > 0.5:
        organ = _ORGAN_MAP.get(dominant_el, "相关脏腑")
        jiankang = (
            f"{year}年命局五行偏旺，{organ}可能因过度运作而出现问题，需关注相关保养。"
            f"饮食均衡，避免过度偏食某类食物，保持五行饮食调和。"
            f"建议每半年进行一次全面体检，将潜在问题消灭于萌芽状态。"
        )
    elif is_yongshen_favorable_year:
        jiankang = (
            f"{year}年流年与用神相合，整体气血较为充盈，精力状态良好。"
            f"适合在本年强化运动习惯，建立锻炼规律，为健康打好基础。"
            f"保持情绪稳定与规律作息，疫病防护不可松懈，偶发小疾及时就诊即可。"
        )
    else:
        jiankang = (
            f"{year}年健康运势整体平稳，无明显大病征兆，以预防为主。"
            f"定期进行常规体检，关注睡眠质量与消化系统。"
            f"注意情绪起伏对身体的影响，保持良好心态是本年养生管理的核心要素。"
        )

    return {
        "财运": caiyun,
        "事业": shiye,
        "婚恋": hunlian,
        "健康": jiankang,
    }
