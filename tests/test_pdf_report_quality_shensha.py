"""PDF 质量方案：神煞极性 / 强弱叙事回归。"""

from __future__ import annotations

from services.bazi_engine.interpret import InterpretInput, interpret_bazi


def test_tianyi_not_in_xiongsha_bucket_and_deduped():
    inp = InterpretInput(
        day_stem="庚",
        wuxing_scores={"metal": 2, "wood": 1, "water": 1, "fire": 3, "earth": 1},
        yongshen_favor=["wood", "water"],
        yongshen_avoid=["metal"],
        strength_tier="极弱",
        geju_name="七杀格",
        shensha_items=[
            {"name": "天乙贵人", "polarity": "+"},
            {"name": "天乙贵人", "polarity": "+"},
            {"name": "羊刃", "polarity": "-"},
        ],
        dizhi_relations=[],
    )
    result = interpret_bazi(inp)
    text = result.full_summary or ""
    assert "天乙贵人" in text
    assert "凶煞有" not in text
    assert text.count("天乙贵人") == 1
    assert "命中吉神有天乙贵人" in text
    assert "慎神有羊刃" in text
    assert "日主极弱" in text or "日主为极弱" in text
    # 全文不得用「偏弱」顶替已给出的「极弱」
    assert "偏弱" not in text
    assert "综合收束" not in text
    assert text.count("用神为金、水") <= 1


def test_weak_day_master_template_uses_tier_not_hardcoded_pianruo():
    inp = InterpretInput(
        day_stem="甲",
        wuxing_scores={"wood": 1, "water": 1, "fire": 1, "earth": 1, "metal": 1},
        yongshen_favor=["wood"],
        yongshen_avoid=["metal"],
        strength_tier="极弱",
        geju_name="正官格",
        shensha_items=[],
        dizhi_relations=[],
    )
    result = interpret_bazi(inp)
    general = result.general_text or ""
    assert "日主极弱" in general
    assert "日主偏弱" not in general
