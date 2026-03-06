"""
services/bazi_engine/analysis/personality.py — 性格引擎 (M2 任务 2.06)

算法规格: §4.11-F
"""
from __future__ import annotations

from app.schemas.analysis import PersonalityModel

# 10 天干性格模板（各含优劣）
_STEM_TRAITS: dict[str, dict] = {
    "甲": {
        "trait":      "甲木→进取、担当、直率",
        "advantages": ["志向远大，有领导力", "正直坦率，言行一致", "抗压能力强，不轻言放弃"],
        "disadvantages": [
            "过于刚直，遇阻时难以变通",
            "自我中心，不易接受他人批评",
            "好胜心强，争强好胜容易树敌",
            "固执己见，决策后难以调整方向",
        ],
        "growth":     "学习弹性思维与换位思考，遇到阻力时善用迂回化解而非正面硬碰；将直率转化为真诚沟通，赢得更广泛的支持与共鸣。",
    },
    "乙": {
        "trait":      "乙木→柔韧、适应、审美",
        "advantages": ["适应力强，善于迂回达目标", "审美情趣高，具亲和力", "耐心细腻，善于维系关系"],
        "disadvantages": [
            "优柔寡断，关键时刻缺乏决断力",
            "依赖心较重，独立处事能力欠缺",
            "情绪易受外界影响，抗压稳定性弱",
            "过于顾虑他人感受，容易委屈自己",
        ],
        "growth":     "每天给自己设定一个小决策并立即执行，逐步培养主动决策习惯；建立清晰个人边界，让亲密关系既有温度又保有独立自主的空间。",
    },
    "丙": {
        "trait":      "丙火→热情、开朗、正直",
        "advantages": ["热情洋溢，感染力强", "乐观积极，给人温暖", "执行力强，敢于突破"],
        "disadvantages": [
            "冲动急躁，行事前缺乏深思熟虑",
            "缺乏耐性，不善处理繁琐细节",
            "喜欢表现，有时流于表面热闹",
            "情绪起伏大，高峰与低谷落差明显",
        ],
        "growth":     "在重要决策前刻意增加「停顿3分钟」的习惯，让热情转化为稳健行动；同时加强对细节的关注，用清单记录弥补冲劲有余、精细不足的短板。",
    },
    "丁": {
        "trait":      "丁火→细腻、聪敏、洞察",
        "advantages": ["观察力敏锐，思维细腻", "创意丰富，有艺术天赋", "心思深远，善于布局"],
        "disadvantages": [
            "多愁善感，情绪波动容易影响判断",
            "疑心较重，难以完全信任他人",
            "心思过细，容易钻牛角尖",
            "内向敏感，在陌生环境中社交消耗大",
        ],
        "growth":     "建立情绪日记习惯，将内心波动转化为创作素材；通过积累小信任证据清单，逐步放下过度防御，让人际关系更加轻盈顺畅。",
    },
    "戊": {
        "trait":      "戊土→稳重、厚道、包容",
        "advantages": ["诚信踏实，值得信赖", "包容大度，凝聚力强", "抗压稳定，遇事沉着"],
        "disadvantages": [
            "行动迟缓，做事节奏偏慢",
            "过于保守，容易错失快速变化的机遇",
            "思维固化，不擅长接受新思路",
            "情绪表达不足，内心有事难以倾诉",
        ],
        "growth":     "设定每月「新尝试」任务，强迫自己走出舒适圈；评估机会时给自己设定截止时间，将稳重优势与果断行动力相结合，把握时机。",
    },
    "己": {
        "trait":      "己土→谨慎、务实、细心",
        "advantages": ["务实周全，做事认真", "分析能力强，重视细节", "善于积累，财富稳健"],
        "disadvantages": [
            "过度谨小慎微，对自身能力长期低估",
            "表达欲较弱，优秀之处难以被外界发现",
            "过于自我要求，承担过多心理压力",
            "眼光有时局限，难以把握大格局机会",
        ],
        "growth":     "每周主动在团队或公开场合分享一个观点或成果，锻炼表达自信；记录「已实现清单」来对抗自我贬低，认识到严谨细致是难以复制的核心竞争力。",
    },
    "庚": {
        "trait":      "庚金→果断、刚强、正义",
        "advantages": ["决断力强，雷厉风行", "正义感强，嫉恶如仇", "执行力出色，成事效率高"],
        "disadvantages": [
            "过于强硬，容易招致人际关系紧张",
            "固执己见，不擅接受他人建议",
            "言辞直接，易在无意中伤害他人感情",
            "情绪管理不足，急躁时容易失控",
        ],
        "growth":     "在表达强烈立场前先主动倾听对方1-2分钟，寻找共识后再提建议；将果断转化为「攻心」而非「攻势」，以认同感代替对抗感，建立更强大的人际影响力。",
    },
    "辛": {
        "trait":      "辛金→精巧、清高、敏感",
        "advantages": ["精益求精，品位高雅", "善于语言沟通，言辞精准", "洞察秋毫，艺术敏感度强"],
        "disadvantages": [
            "心思细腻易计较得失，有时过于斤斤计较",
            "情绪敏感，遭遇挫折后恢复力偏弱",
            "自尊心强，难以坦然接受失误",
            "清高傲骨，有时难以融入普通社交圈",
        ],
        "growth":     "练习「放大镜转换」：每当发现小失误，拉远视角看整体成就；建立挫折复盘清单，把每次情绪消耗变成技能升级的证据，令敏感成为精准洞察的优势。",
    },
    "壬": {
        "trait":      "壬水→聪明、灵活、开阔",
        "advantages": ["思维活跃，学习能力强", "超然大度，视野开阔", "应变迅速，善于随机应变"],
        "disadvantages": [
            "三心二意，难以在单一方向持续深耕",
            "情感疏离，理性有余温度不足",
            "见异思迁，容易被新事物带偏原定计划",
            "思路发散，落地执行力相对偏弱",
        ],
        "growth":     "选定一个领域坚持90天深耕，用成果记录本追踪进展，聚焦聪明才智成专业深度；每天花5分钟真诚表达情感或感谢，让开阔心胸也能创造温暖的深度连接。",
    },
    "癸": {
        "trait":      "癸水→内敛、感性、洞悉",
        "advantages": ["直觉敏锐，内心世界丰富", "善解人意，同理心强", "思维深刻，善于研究"],
        "disadvantages": [
            "过于内敛，内心想法难以主动表达",
            "悲观倾向明显，情绪低落时难以自我调整",
            "敏感多虑，容易将小事放大引发焦虑",
            "依赖感强，面对重大选择时缺乏安全感",
        ],
        "growth":     "每天用100字记录一个内心洞察并分享给信任的朋友，把丰富内心世界转化为有价值的表达；培养「积极归因」习惯，遇到挫折先找可学点，再允许自己感受情绪。",
    },
}


def compute_personality(
    day_stem: str,
    strength_tier: str,    # "极旺" | "偏旺" | "中和" | "偏弱" | "极弱"
    strength_score: float,
    geju_name: str = "",
) -> PersonalityModel:
    """
    §4.11-F 性格引擎

    Parameters:
        day_stem:       日干
        strength_tier:  旺弱档次
        strength_score: 旺弱分数
        geju_name:      格局名称
    """
    template = _STEM_TRAITS.get(day_stem, {
        "trait":         "命主五行均衡，性格综合",
        "advantages":    ["适应力强", "性格平和", "包容力好"],
        "disadvantages": ["缺乏突出特质，个人风格不鲜明", "难以在人群中留下深刻印象", "缺乏核心竞争力，容易被替代"],
        "growth":        "发掘自身优势，打造个人核心价值。",
    })

    # ─── 旺衰修正 ─────────────────────────────────────────────────────
    advantages    = list(template["advantages"])
    disadvantages = list(template["disadvantages"])

    if strength_tier in ("极旺", "偏旺"):
        # 极旺：放大特征（优势更强，缺点也更明显）
        advantages    = [f"（旺势加持）{a}" for a in advantages]
        disadvantages = [f"（旺势放大）{d}" for d in disadvantages]
        modifier = "日主偏旺，性格特质更为鲜明突出，需留意过刚则折。"
    elif strength_tier in ("极弱", "偏弱"):
        advantages    = [a for a in advantages]  # 保留优点
        disadvantages = [f"（身弱谨慎）{d}" for d in disadvantages]
        modifier = "日主偏弱，性格趋向谨慎内敛，宜提升自信心。"
    else:
        modifier = "日主中和，性格均衡稳重，适应力强。"

    # ─── 格局叠加修正 ─────────────────────────────────────────────────
    if "官" in geju_name:
        advantages.append(f"（{geju_name}加持）责任感强，受人尊重")
    elif "财" in geju_name:
        advantages.append(f"（{geju_name}加持）理财意识强，务实进取")
    elif "印" in geju_name:
        advantages.append(f"（{geju_name}加持）学习力强，思维深邃")
    elif "食" in geju_name or "伤" in geju_name:
        advantages.append(f"（{geju_name}加持）创造力与表达力出众")

    # 限制长度
    advantages    = advantages[:5]
    disadvantages = disadvantages[:5]

    # ─── inference_tags ─────────────────────────────────────────────
    _TIER_CN_P = {
        "extremely_strong": "极旺", "strong": "偏旺", "balanced": "中和",
        "neutral": "中和", "weak": "偏弱", "extremely_weak": "极弱",
    }
    _tier_display = _TIER_CN_P.get(strength_tier, strength_tier)
    tags = [day_stem + "日主", _tier_display]
    if geju_name:
        tags.append(geju_name)

    interp = (
        f"日主为【{day_stem}】，{template['trait']}。"
        f"{modifier}"
        f"在【{geju_name or '气中格'}】加持下，性格特质进一步得到塑造和强化。"
        f"核心优势：{'、'.join(advantages[:3])}；要注意的局限：{'、'.join(disadvantages)}。"
        f"成长建议：{template['growth']}"
        f"（仅供学术研究参考）"
    )

    return PersonalityModel(
        day_stem=day_stem,
        day_stem_trait=template["trait"],
        strength_modifier=modifier,
        advantages=advantages,
        disadvantages=disadvantages,
        growth_advice=template["growth"],
        inference_tags=tags,
        interpretation_text=interp,
    )
