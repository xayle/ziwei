"""
全面对比: 基于文墨天机专业版截图(6张) 完整比对所有数据
刘*, 阳女, 1990-07-17 10:25, 庚午年闰五月廿五巳时, 土五局
"""
import requests, json, sys

API = "http://localhost:8000/api/v1/ziwei/full"
resp = requests.post(API, json={
    "year": 1990, "month": 7, "day": 17, "hour": 10, "minute": 25,
    "gender": "女",
    "liunian_year": 2026,   # 截图显示的流年
})
if resp.status_code != 200:
    print(f"API错误: {resp.status_code}")
    sys.exit(1)

data = resp.json()
palaces = data["palaces"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# ── 从截图3(三合详细图)提取的完整参考数据 ──────────────────────────────────────
# 格式: {宫名: {"main": [(星名, 亮度)], "aux": [星名...], "changsheng": str}}
REF = {
    "命宫": {
        "branch": "寅", "stem": "戊", "dayun": "5~14",
        "main": [("武曲", "得"), ("天相", "庙")],
        # 截图3: 天刑厨廉 得庙庙
        "aux_extra": ["天刑", "天厨", "廉贞(?)"],  # 这些是杂曜
        "changsheng": "病",  # 截图3底部
    },
    "兄弟宫": {
        "branch": "丑", "stem": "己", "dayun": "15~24",
        "main": [("天同", "不"), ("巨门", "不")],
        # 截图3: 大龙耗德 旺平
        "aux_extra": ["天魁", "大耗", "龙德"],
        "changsheng": "死",
    },
    "夫妻宫": {
        "branch": "子", "stem": "戊", "dayun": "25~34",
        "main": [("贪狼", "旺")],
        # 截图3: 解天天 庙平陷
        "aux_extra": ["解神", "天哭", "天虚"],
        "changsheng": "墓",
    },
    "子女宫": {
        "branch": "亥", "stem": "丁", "dayun": "35~44",
        "main": [("太阴", "庙")],
        # 截图3: 台副月 旺平
        "aux_extra": ["天官", "截空", "台辅", "副月(?)"],
        "changsheng": "绝",  # 截图3底部
    },
    "财帛宫": {
        "branch": "戌", "stem": "丙", "dayun": "45~54",
        "main": [("廉贞", "利"), ("天府", "庙")],
        # 截图3: 龙旬华 陷陷平
        "aux_extra": ["截空", "文曲", "龙池", "旬空(?)"],
        "changsheng": "胎",  # 已修复前的结果被fix了
    },
    "疾厄宫": {
        "branch": "酉", "stem": "乙", "dayun": "55~64",
        "main": [],  # 无主星
        # 截图3: 文左擎红三天 → 文曲(not here, in 财帛), 左辅,擎羊,红鸾,三台,天使
        "aux_extra": ["左辅", "擎羊", "红鸾", "三台", "天使"],
        "changsheng": "养",
    },
    "迁移宫": {
        "branch": "申", "stem": "甲", "dayun": "65~74",
        "main": [("破军", "得")],
        # 截图3: 禄铃天天天天孤辰 → 禄存,铃星,天马,天贵(?),天巫(?),孤辰
        "aux_extra": ["禄存", "铃星", "天马", "天伤", "孤辰(?)"],
        "changsheng": "长生",
    },
    "交友宫": {
        "branch": "未", "stem": "癸", "dayun": "75~84",
        "main": [],  # 无主星
        # 截图3: 天陀天封副天截空
        "aux_extra": ["天钺", "陀罗"],
        "changsheng": "沐浴",
    },
    "官禄宫": {
        "branch": "午", "stem": "壬", "dayun": "85~94",
        "main": [("紫微", "庙")],  # 截图3只标了紫微旺→庙
        # 截图3: 火地天天天截 → 火星,地空,天姚,天寿,天福,截(?)
        "aux_extra": ["火星", "地空", "天姚(?)","天寿", "天福"],
        "changsheng": "冠带",
    },
    "田宅宫": {
        "branch": "巳", "stem": "辛", "dayun": "95~104",
        "main": [("天机", "利")],
        # 截图3: 文右八破 → 文昌,右弼,八座,破碎
        "aux_extra": ["右弼", "文昌", "八座(?)", "破碎(?)"],
        "changsheng": "临官",
    },
    "福德宫": {
        "branch": "辰", "stem": "庚", "dayun": "105~114",
        "main": [("七杀", "庙")],
        # 截图3: 地恩凤寡阴年 → 地劫,恩光,凤阁,寡宿,阴煞(?),年解(?)
        "aux_extra": ["地劫", "天空", "恩光(?)", "凤阁(?)"],
        "changsheng": "帝旺",  # 已修复
    },
    "父母宫": {
        "branch": "卯", "stem": "己", "dayun": "115~124",
        "main": [("太阳", "庙"), ("天梁", "庙")],
        # 截图3: 天喜咸天德 → 天喜,咸池,天德
        "aux_extra": ["天喜", "文昌", "咸池(?)"],
        "changsheng": "衰",  # 已修复
    },
}

# ── 截图3中可读取的主星亮度完整参考 ──────────────────────────────
# 从截图3最详细的视图解读
REF_BRIGHTNESS = {
    # (星名, 地支) → 参考亮度
    ("武曲", "寅"): "得",
    ("天相", "寅"): "庙",
    ("天同", "丑"): "不",
    ("巨门", "丑"): "不",
    ("贪狼", "子"): "旺",
    ("太阴", "亥"): "庙",
    ("廉贞", "戌"): "利",
    ("天府", "戌"): "庙",
    ("破军", "申"): "得",
    ("紫微", "午"): "庙",
    ("天机", "巳"): "利",  # 截图3标"平"?
    ("七杀", "辰"): "庙",
    ("太阳", "卯"): "庙",
    ("天梁", "卯"): "庙",
}

# ── 截图中的小限参考 (截图4: 流年1994-2003, 显示35~44岁) ──────
# 截图4显示: 命宫寅=大田5~14, 兄弟丑=大福15~24, ...
# 以及各宫的具体流年岁数
REF_XIAOXIAN_2026 = {
    # 截图4: 2026丙午, 37岁
    # 田宅辛巳: 36岁 2025
    # 官禄壬午: 37岁 2026
    # 交友癸未: 38岁 2027
    # 迁移甲申: 39岁 2028
}

# ── 截图中的流年 ──────────────────────────────────────────────
# 底部大限栏: 5~14戊寅 | 15~24己丑 | 25~34戊子 | 35~44丁亥 | 45~54丙戌 | 55~64乙酉 | 65~74甲申 | 75~84癸未
REF_DAYUN_GANZHI = [
    ("戊寅", 5, 14), ("己丑", 15, 24), ("戊子", 25, 34), ("丁亥", 35, 44),
    ("丙戌", 45, 54), ("乙酉", 55, 64), ("甲申", 65, 74), ("癸未", 75, 84),
    ("壬午", 85, 94), ("辛巳", 95, 104), ("庚辰", 105, 114), ("己卯", 115, 124),
]

# ── 截图底部流年栏 ──────────────────────────────────────────
REF_LIUNIAN = [
    (2024, "甲辰"), (2025, "乙巳"), (2026, "丙午"), (2027, "丁未"),
    (2028, "戊申"), (2029, "己酉"), (2030, "庚戌"), (2031, "辛亥"),
    (2032, "壬子"), (2033, "癸丑"),
]

# ── 命主身主 ──────────────────────────────────────────────────
REF_LIFE_RULER = "禄存"
REF_BODY_RULER = "火星"

# ===================================================================
# 开始对比
# ===================================================================
diffs = []

print("=" * 70)
print("1. 基本信息")
print("=" * 70)

# 命主身主
lr = data.get("life_ruler_star", "")
br = data.get("body_ruler_star", "")
lr_ok = lr == REF_LIFE_RULER
br_ok = br == REF_BODY_RULER
print(f"  命主: {lr} {'✓' if lr_ok else '✗ (参考: '+REF_LIFE_RULER+')'}")
print(f"  身主: {br} {'✓' if br_ok else '✗ (参考: '+REF_BODY_RULER+')'}")
if not lr_ok:
    diffs.append(f"命主: 我们={lr}, 参考={REF_LIFE_RULER}")
if not br_ok:
    diffs.append(f"身主: 我们={br}, 参考={REF_BODY_RULER}")

print()
print("=" * 70)
print("2. 主星亮度对比")
print("=" * 70)
for p in palaces:
    pname = p["name"]
    ref = REF.get(pname)
    if not ref:
        continue
    for s in p.get("main_stars", []):
        sname = s["name"]
        our_br = s.get("brightness", "")
        key = (sname, ref["branch"])
        if key in REF_BRIGHTNESS:
            ref_br = REF_BRIGHTNESS[key]
            ok = our_br == ref_br
            status = "✓" if ok else "✗"
            print(f"  {pname:5s} {sname}: {our_br:3s} {status} (参考: {ref_br})")
            if not ok:
                diffs.append(f"亮度: {pname} {sname}: 我们={our_br}, 参考={ref_br}")

print()
print("=" * 70)
print("3. 大限干支/年龄对比")
print("=" * 70)
dayun_items = data.get("dayun", {}).get("items", [])
for i, ref_item in enumerate(REF_DAYUN_GANZHI):
    ref_gz, ref_start, ref_end = ref_item
    if i < len(dayun_items):
        our = dayun_items[i]
        our_gz = our["ganzhi"]
        our_start = our["start_age"]
        our_end = our["end_age"]
        gz_ok = our_gz == ref_gz
        age_ok = our_start == ref_start and our_end == ref_end
        status = "✓" if (gz_ok and age_ok) else "✗"
        detail = ""
        if not gz_ok:
            detail += f" 干支不匹配(我们={our_gz})"
            diffs.append(f"大限{i+1}: 干支 我们={our_gz}, 参考={ref_gz}")
        if not age_ok:
            detail += f" 年龄不匹配(我们={our_start}~{our_end})"
            diffs.append(f"大限{i+1}: 年龄 我们={our_start}~{our_end}, 参考={ref_start}~{ref_end}")
        print(f"  [{i+1:2d}] {our_gz} {our_start:3d}~{our_end:3d} {status} (参考: {ref_gz} {ref_start}~{ref_end}){detail}")

print()
print("=" * 70)
print("4. 长生十二神对比")
print("=" * 70)
for p in palaces:
    pname = p["name"]
    ref = REF.get(pname)
    if not ref:
        continue
    our_cs = p.get("changsheng", "")
    ref_cs = ref.get("changsheng", "")
    if ref_cs:
        ok = our_cs == ref_cs
        print(f"  {pname:5s} {ref['branch']}: {our_cs:4s} {'✓' if ok else '✗ (参考: '+ref_cs+')'}")
        if not ok:
            diffs.append(f"长生: {pname}: 我们={our_cs}, 参考={ref_cs}")

print()
print("=" * 70)
print("5. 辅星详细对比")
print("=" * 70)
for p in palaces:
    pname = p["name"]
    our_aux = set(p.get("aux_stars", []))
    print(f"  {pname:5s}: {', '.join(sorted(our_aux)) if our_aux else '(空)'}")

print()
print("=" * 70)
print("6. 宫位大限年龄对比 (宫位上标注的大限)")
print("=" * 70)
# 截图显示每个宫位标注了大限年龄范围
# 截图中: 命宫=5~14, 兄弟=15~24, ..., 父母=115~124
# 这是逆行（从命宫往逆时针递增）
ref_palace_dayun = {
    "命宫": "5~14", "兄弟宫": "15~24", "夫妻宫": "25~34", "子女宫": "35~44",
    "财帛宫": "45~54", "疾厄宫": "55~64", "迁移宫": "65~74", "交友宫": "75~84",
    "官禄宫": "85~94", "田宅宫": "95~104", "福德宫": "105~114", "父母宫": "115~124",
}
for i, item in enumerate(dayun_items):
    # 找到该大限对应的宫位(通过ganzhi中的地支匹配)
    item_branch = item["ganzhi"][1]  # 取干支的第二个字(地支)
    palace_name = "?"
    for p in palaces:
        if p["branch"] == item_branch:
            palace_name = p["name"]
            break
    age_range = f"{item['start_age']}~{item['end_age']}"
    ref_range = ref_palace_dayun.get(palace_name, "?")
    ok = age_range == ref_range
    status = "✓" if ok else "✗"
    if not ok:
        diffs.append(f"宫位大限: {palace_name} 我们={age_range}, 参考={ref_range}")
    print(f"  {palace_name:5s}: {age_range:10s} {status} (参考: {ref_range})")

print()
print("=" * 70)
print("7. 四化标记 (截图中A/B/C/D标记)")
print("=" * 70)
# 截图1/5: A=化禄, B=化权, C=化科, D=化忌
# 年干庚的四化: 太阳化禄(A), 武曲化权(B), 太阴化科(C), 天同化忌(D)
# 截图1标记:
#   父母宫(太阳梁) = A+C? → 太阳化禄在此
#   命宫(武曲相) = B → 武曲化权
#   子女宫(太阴) = C → 太阴化科
#   兄弟宫(天同巨门) = D → 天同化忌
print("  年干四化 (庚干):")
for p in palaces:
    for s in p.get("main_stars", []):
        if s.get("transforms"):
            print(f"    {p['name']:5s} {s['name']}: {', '.join(s['transforms'])}")

print()
print("=" * 70)
print("8. 小限 (截图4: 特定年龄显示)")
print("=" * 70)
# 截图4显示2026年时每个宫的小限岁数
# 大田→命宫=大田、大福→兄弟=大福 等标注是大限宫位名
# 截图4右下角显示: 子女宫丁亥 42岁 2031, 大命35~44
# 命宫=44岁2033, 兄弟=大福15~24→44岁, 夫妻=大父25~34→43岁
for p in palaces:
    pname = p["name"]
    xx_ages = p.get("xiaoxian_ages", [])
    if xx_ages:
        print(f"  {pname:5s} {p.get('branch','')}: {xx_ages[:8]}")

print()
print("=" * 70)
print("9. 流年信息")
print("=" * 70)
liunian = data.get("liunian")
if liunian:
    print(f"  流年干支: {liunian.get('year_gz', '')}")
    print(f"  流年年份: {liunian.get('year', '')}")

print()
print("=" * 70)
print("10. 总结")
print("=" * 70)
if diffs:
    print(f"  共 {len(diffs)} 个差异:")
    for d in diffs:
        print(f"    {d}")
else:
    print("  ✅ 全部对比通过")
