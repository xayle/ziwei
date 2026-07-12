"""
交叉验证: 使用多组案例验证长生十二神、大限方向、brightness等
覆盖所有4种阴阳性别组合 + 不同五行局
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from services.ziwei_engine import ziwei_full
from services.ziwei_engine.decorative import place_changsheng12, _CHANGSHENG_START

BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# ── 案例1: 庚午年女 (阳女→逆行), 土五局, 命宫寅 ──────────
# 已经由 _compare_deep.py 验证通过

# ── 案例2: 壬午年女 (阳女→逆行), 水二局, 命宫未 ──────────
# Golden test case from test_ziwei_engine.py
# 2002-03-13 14:55 女

# ── 案例3: 虚构测试 - 各组合方向验证 ──────────────────────
def test_changsheng_directions():
    """验证 4 种阴阳性别组合的方向是否正确"""
    print("=" * 60)
    print("长生十二神方向验证")
    print("=" * 60)

    # 阳男 (男+阳年支=偶数): 顺行(地支递减, forward=False)
    r1 = place_changsheng12(6, "男", 0)  # 火六局, 男, 子年
    # 火六局start=寅(2), 顺行(递减): 长生=2, 沐浴=1, 冠带=0, 临官=11...
    assert r1[2] == "长生", f"阳男: 寅应为长生, 实得{r1[2]}"
    assert r1[1] == "沐浴", f"阳男: 丑应为沐浴, 实得{r1[1]}"
    assert r1[0] == "冠带", f"阳男: 子应为冠带, 实得{r1[0]}"
    print("  阳男(男+子年): 顺行(递减) ✓")

    # 阴女 (女+阴年支=奇数): 顺行(地支递减, forward=False)
    r2 = place_changsheng12(6, "女", 1)  # 火六局, 女, 丑年
    assert r2[2] == "长生", f"阴女: 寅应为长生, 实得{r2[2]}"
    assert r2[1] == "沐浴", f"阴女: 丑应为沐浴, 实得{r2[1]}"
    print("  阴女(女+丑年): 顺行(递减) ✓")

    # 阴男 (男+阴年支=奇数): 逆行(地支递增, forward=True)
    r3 = place_changsheng12(6, "男", 1)  # 火六局, 男, 丑年
    assert r3[2] == "长生", f"阴男: 寅应为长生, 实得{r3[2]}"
    assert r3[3] == "沐浴", f"阴男: 卯应为沐浴, 实得{r3[3]}"
    assert r3[4] == "冠带", f"阴男: 辰应为冠带, 实得{r3[4]}"
    print("  阴男(男+丑年): 逆行(递增) ✓")

    # 阳女 (女+阳年支=偶数): 逆行(地支递增, forward=True)
    r4 = place_changsheng12(6, "女", 0)  # 火六局, 女, 子年
    assert r4[2] == "长生", f"阳女: 寅应为长生, 实得{r4[2]}"
    assert r4[3] == "沐浴", f"阳女: 卯应为沐浴, 实得{r4[3]}"
    print("  阳女(女+子年): 逆行(递增) ✓")

    print()

def test_changsheng_all_wuxing():
    """验证 5 种五行局的起始位置"""
    print("=" * 60)
    print("长生十二神五行局起始验证")
    print("=" * 60)
    expected = {2: 8, 3: 11, 4: 5, 5: 2, 6: 2}  # 土五局=寅(2) 火土共长生
    for ju, start_branch in expected.items():
        r = place_changsheng12(ju, "男", 0)  # 阳男→顺行(递减)
        assert r[start_branch] == "长生", \
            f"  {ju}局: {BRANCHES[start_branch]}应为长生, 实得{r[start_branch]}"
        print(f"  {'水木金土火'[ju-2]}{ju}局: 长生在{BRANCHES[start_branch]} ✓")
    print()

def test_golden_case_changsheng():
    """验证黄金测试案例(水二局 阳女)的长生十二神"""
    print("=" * 60)
    print("黄金案例(2002壬午年女, 水二局, 命宫未) 长生验证")
    print("=" * 60)

    # 水二局, 女, 午年(6=阳) → 阳女→逆行(递增)
    r = place_changsheng12(2, "女", 6)  # 水二局start=申(8)
    # 逆行(递增): 长生=8(申), 沐浴=9(酉), ...
    print("  水二局阳女, 逆行(递增):")
    for b in range(12):
        print(f"    {BRANCHES[b]}: {r[b]}")
    assert r[8] == "长生", f"申应为长生, 实得{r[8]}"
    assert r[9] == "沐浴", f"酉应为沐浴, 实得{r[9]}"
    print("  ✓ 正确")
    print()

def test_golden_case_dayun():
    """验证黄金案例的大运"""
    print("=" * 60)
    print("黄金案例(2002壬午年女) 大运验证")
    print("=" * 60)

    chart = ziwei_full(2002, 3, 13, 14, 55, "女")
    d = chart.dayun

    # 壬(8)=阳年, 女 → 逆行
    assert not d.forward, f"壬午年女应逆行, 实得 forward={d.forward}"
    print(f"  方向: {'顺行' if d.forward else '逆行'} ✓")

    # 水二局 → 起运2岁
    assert d.start_age == 2, f"水二局起运应2岁, 实得{d.start_age}"
    print(f"  起运: {d.start_age}岁 ✓")

    # 命宫丁未 → 逆行: 丁未→丙午→乙巳→甲辰→癸卯...
    expected_gz = ["丁未","丙午","乙巳","甲辰","癸卯","壬寅","辛丑","庚子","己亥","戊戌","丁酉","丙申"]
    for i, item in enumerate(d.items):
        exp = expected_gz[i]
        status = "✓" if item.ganzhi == exp else "✗"
        print(f"  [{i+1:2d}] {item.ganzhi} {item.start_age}~{item.end_age} {status} (期望: {exp})")
        assert item.ganzhi == exp, f"第{i+1}大限应为{exp}, 实得{item.ganzhi}"

    print()

def test_brightness_range():
    """验证亮度值范围在 0-6"""
    print("=" * 60)
    print("亮度值范围验证")
    print("=" * 60)

    chart = ziwei_full(1990, 7, 17, 10, 25, "女")
    for p in chart.palaces:
        for s in p.main_stars:
            bv = s.get("brightness_val", -1)
            assert 0 <= bv <= 6, f"{p.name} {s['name']} brightness_val={bv} 超出 0-6 范围"
    print("  案例1(1990女): 所有主星亮度值在 0-6 范围 ✓")

    chart2 = ziwei_full(2002, 3, 13, 14, 55, "女")
    for p in chart2.palaces:
        for s in p.main_stars:
            bv = s.get("brightness_val", -1)
            assert 0 <= bv <= 6, f"{p.name} {s['name']} brightness_val={bv} 超出 0-6 范围"
    print("  案例2(2002女): 所有主星亮度值在 0-6 范围 ✓")

    # 测试男性案例
    chart3 = ziwei_full(1985, 5, 20, 8, 30, "男")
    for p in chart3.palaces:
        for s in p.main_stars:
            bv = s.get("brightness_val", -1)
            assert 0 <= bv <= 6, f"{p.name} {s['name']} brightness_val={bv} 超出 0-6 范围"
    print("  案例3(1985男): 所有主星亮度值在 0-6 范围 ✓")
    print()

def test_twelve_changsheng_coverage():
    """确保每个案例的12宫都恰好覆盖12种长生"""
    print("=" * 60)
    print("长生十二神完整覆盖验证")
    print("=" * 60)

    EXPECTED_NAMES = {"长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"}

    test_cases = [
        (1990, 7, 17, 10, 25, "女", "1990阳女土五局"),
        (2002, 3, 13, 14, 55, "女", "2002阳女水二局"),
        (1985, 5, 20, 8, 30, "男", "1985阴男木三局"),
        (1988, 1, 15, 6, 0,  "男", "1988阳男火六局"),
    ]

    for y, m, d, h, mi, g, desc in test_cases:
        chart = ziwei_full(y, m, d, h, mi, g)
        cs_set = set()
        for p in chart.palaces:
            if p.changsheng:
                cs_set.add(p.changsheng)
        assert cs_set == EXPECTED_NAMES, f"{desc}: 长生覆盖不完整, 缺少: {EXPECTED_NAMES - cs_set}"
        print(f"  {desc}: 12种长生全覆盖 ✓")
    print()


if __name__ == "__main__":
    test_changsheng_directions()
    test_changsheng_all_wuxing()
    test_golden_case_changsheng()
    test_golden_case_dayun()
    test_brightness_range()
    test_twelve_changsheng_coverage()
    print("=" * 60)
    print("✅ 全部交叉验证通过！")
    print("=" * 60)
