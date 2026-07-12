"""
深度对比脚本v2: 检查辅星/将前/岁前/大运四化/博士/流年等
刘*, 阳女, 1990-07-17 10:25, 庚午年闰五月廿五巳时, 土五局
参考: 文墨天机专业版 截图
"""
import requests, json, sys

API = "http://localhost:8000/api/v1/ziwei/full"
resp = requests.post(API, json={
    "year": 1990, "month": 7, "day": 17, "hour": 10, "minute": 25,
    "gender": "女", "liunian_year": 2026,
})
if resp.status_code != 200:
    print(f"API错误: {resp.status_code} {resp.text[:300]}")
    sys.exit(1)

data = resp.json()
palaces = data["palaces"]
BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
diffs = []

# ============================================================
# 1. 完整辅星分布 (含六吉六煞、杂曜)
# ============================================================
print("=" * 70)
print("1. 各宫完整信息 (主星+辅星+将前+岁前+长生)")
print("=" * 70)

# 截图参考辅星 (从截图3/5提取的关键辅星位置)
REF_AUX = {
    "命宫":   {"expected": {"天刑"}, "branch": "寅"},
    "兄弟宫": {"expected": {"天魁"}, "branch": "丑"},
    "夫妻宫": {"expected": set(), "branch": "子"},
    "子女宫": {"expected": {"天官"}, "branch": "亥"},
    "财帛宫": {"expected": {"文曲"}, "branch": "戌"},
    "疾厄宫": {"expected": {"左辅", "擎羊", "红鸾"}, "branch": "酉"},
    "迁移宫": {"expected": {"禄存", "铃星", "天马"}, "branch": "申"},
    "交友宫": {"expected": {"天钺", "陀罗"}, "branch": "丑"},  # 未(7)
    "官禄宫": {"expected": {"火星", "地空"}, "branch": "午"},
    "田宅宫": {"expected": {"右弼"}, "branch": "巳"},
    "福德宫": {"expected": {"地劫", "天空"}, "branch": "辰"},
    "父母宫": {"expected": {"文昌", "天喜"}, "branch": "卯"},
}

for p in palaces:
    pname = p["name"]
    ms_names = [s["name"] + "(" + s.get("brightness", "") + ")" for s in p.get("main_stars", [])]
    aux = set(p.get("aux_stars", []))
    jq = p.get("jiangqian_star", "")
    sq = p.get("suiqian_star", "")
    cs = p.get("changsheng", "")

    print(f"  {pname:5s} {p['stem']}{p['branch']}  主星:{', '.join(ms_names) or '(无)'}  长生:{cs}")
    print(f"         辅星: {', '.join(sorted(aux)) or '(空)'}")
    print(f"         将前:{jq:4s}  岁前:{sq}")

    # 检查关键辅星是否在位
    ref = REF_AUX.get(pname)
    if ref:
        missing = ref["expected"] - aux
        if missing:
            msg = f"辅星缺失: {pname}: 缺少 {missing}"
            diffs.append(msg)
            print(f"         ⚠ {msg}")

# ============================================================
# 2. 六吉六煞位置汇总检查
# ============================================================
print()
print("=" * 70)
print("2. 六吉六煞位置汇总")
print("=" * 70)

KEY_AUX_STARS = ["文昌", "文曲", "左辅", "右弼", "天魁", "天钺",
                 "擎羊", "陀罗", "火星", "铃星", "地空", "地劫",
                 "禄存", "天马", "红鸾", "天喜"]

# 截图参考位置 (星名 → 地支)
REF_KEY_AUX = {
    "文昌": "卯", "文曲": "戌", "左辅": "酉", "右弼": "巳",
    "天魁": "丑", "天钺": "未", "擎羊": "酉", "陀罗": "未",
    "火星": "午", "铃星": "申", "地空": "午", "地劫": "辰",
    "禄存": "申", "天马": "申", "红鸾": "酉", "天喜": "卯",
}

star_locations = {}
for p in palaces:
    for star in p.get("aux_stars", []):
        star_locations[star] = p["branch"]

for star in KEY_AUX_STARS:
    our_branch = star_locations.get(star, "?")
    ref_branch = REF_KEY_AUX.get(star, "?")
    ok = our_branch == ref_branch
    status = "✓" if ok else "✗"
    print(f"  {star:4s}: {our_branch} {status} (参考: {ref_branch})")
    if not ok:
        diffs.append(f"辅星位置: {star} 我们={our_branch}, 参考={ref_branch}")

# ============================================================
# 3. 将前十二神对比
# ============================================================
print()
print("=" * 70)
print("3. 将前十二神 (2026丙午年)")
print("=" * 70)

# 截图5参考: 2026丙午年流年将前十二神
# 午年属 寅午戌三合, 将前起将星于午
# 将星→午, 攀鞍→未, 岁驿→申, 息神→酉, 华盖→戌, 劫煞→亥
# 灾煞→子, 天煞→丑, 指背→寅, 咸池→卯, 月煞→辰, 亡神→巳
REF_JIANGQIAN = {
    "午": "将星", "未": "攀鞍", "申": "岁驿", "酉": "息神",
    "戌": "华盖", "亥": "劫煞", "子": "灾煞", "丑": "天煞",
    "寅": "指背", "卯": "咸池", "辰": "月煞", "巳": "亡神",
}

for p in palaces:
    jq = p.get("jiangqian_star", "")
    ref = REF_JIANGQIAN.get(p["branch"], "?")
    ok = jq == ref
    status = "✓" if ok else "✗"
    print(f"  {p['branch']}: {jq:4s} {status} (参考: {ref})")
    if not ok:
        diffs.append(f"将前: {p['branch']} 我们={jq}, 参考={ref}")

# ============================================================
# 4. 岁前十二神对比
# ============================================================
print()
print("=" * 70)
print("4. 岁前十二神 (2026丙午年)")
print("=" * 70)

# 午年: 岁建起于午, 顺行
# 岁建→午, 晦气→未, 丧门→申, 贯索→酉, 官符→戌, 小耗→亥
# 大耗→子, 龙德→丑, 白虎→寅, 天德→卯, 吊客→辰, 病符→巳
REF_SUIQIAN = {
    "午": "岁建", "未": "晦气", "申": "丧门", "酉": "贯索",
    "戌": "官符", "亥": "小耗", "子": "大耗", "丑": "龙德",
    "寅": "白虎", "卯": "天德", "辰": "吊客", "巳": "病符",
}

for p in palaces:
    sq = p.get("suiqian_star", "")
    ref = REF_SUIQIAN.get(p["branch"], "?")
    ok = sq == ref
    status = "✓" if ok else "✗"
    print(f"  {p['branch']}: {sq:4s} {status} (参考: {ref})")
    if not ok:
        diffs.append(f"岁前: {p['branch']} 我们={sq}, 参考={ref}")

# ============================================================
# 5. 年干四化对比
# ============================================================
print()
print("=" * 70)
print("5. 年干四化 (庚干: 太阳化禄, 武曲化权, 太阴化科, 天同化忌)")
print("=" * 70)

REF_SIHUA = {
    "太阳": "化禄", "武曲": "化权", "太阴": "化科", "天同": "化忌",
}

found_sihua = {}
for p in palaces:
    for s in p.get("main_stars", []):
        if s.get("transforms"):
            for t in s["transforms"]:
                found_sihua[s["name"]] = t
                print(f"  {p['name']:5s} {s['name']}: {t}")

for star, expected in REF_SIHUA.items():
    actual = found_sihua.get(star, "无")
    if actual != expected:
        diffs.append(f"四化: {star} 我们={actual}, 参考={expected}")
        print(f"  ⚠ {star}: {actual} ≠ {expected}")
    else:
        print(f"  ✓ {star}: {actual}")

# ============================================================
# 6. 大运四化对比 (第1限 戊寅)
# ============================================================
print()
print("=" * 70)
print("6. 大运四化 (当前大限)")
print("=" * 70)

dayun_items = data.get("dayun", {}).get("items", [])
# 当前年龄37岁(2026-1990+1), 在35~44大限(第4限, 丁亥)
# 丁干四化: 太阴化禄, 天同化权, 天机化科, 巨门化忌
REF_DAYUN_SIHUA_4 = {
    "太阴": "化禄", "天同": "化权", "天机": "化科", "巨门": "化忌",
}

if len(dayun_items) >= 4:
    d4 = dayun_items[3]  # 第4限(index 3)
    print(f"  第4限 {d4['ganzhi']} ({d4['start_age']}~{d4['end_age']})")
    d4_sihua = d4.get("sihua", {})
    print(f"  大运四化: {d4_sihua}")
    for star, expected in REF_DAYUN_SIHUA_4.items():
        actual = d4_sihua.get(star, "无")
        ok = actual == expected
        status = "✓" if ok else "✗"
        print(f"    {star}: {actual} {status} (参考: {expected})")
        if not ok:
            diffs.append(f"大运四化(丁亥): {star} 我们={actual}, 参考={expected}")

# ============================================================
# 7. 小限岁数抽查 (2026年=37虚岁)
# ============================================================
print()
print("=" * 70)
print("7. 小限岁数抽查 (2026年37虚岁)")
print("=" * 70)

# 1990年生, 命宫寅, 庚午年阳女
# 小限起法: 从命宫寅起1岁, 阳女逆行(申→未→午→巳...)
# 1岁在申(迁移), 2岁在未(交友), ...12岁回酉(疾厄), 13岁又在申
# 37虚岁: (37-1) % 12 = 0 → 迁移宫申
# 截图4确认: 2026年37岁小限在申(迁移宫)

for p in palaces:
    ages = p.get("xiaoxian_ages", [])
    if 37 in ages:
        print(f"  37岁小限在: {p['name']} {p['branch']}")
        if p["branch"] == "申":
            print(f"  ✓ 匹配参考(迁移宫申)")
        else:
            msg = f"小限: 37岁应在申(迁移宫), 实际在{p['branch']}({p['name']})"
            diffs.append(msg)
            print(f"  ✗ {msg}")
        break

# ============================================================
# 8. 命宫/身宫检查
# ============================================================
print()
print("=" * 70)
print("8. 命宫/身宫位置")
print("=" * 70)

life_gz = data.get("life_palace_gz", "")
# 优先用汉字字段
body_b = data.get("body_palace_branch_name") or data.get("body_palace_branch", "")
print(f"  命宫干支: {life_gz} (参考: 戊寅)")
print(f"  身宫地支: {body_b}")

if life_gz != "戊寅":
    diffs.append(f"命宫干支: 我们={life_gz}, 参考=戊寅")

# 截图显示身宫在午(官禄宫)
REF_BODY_BRANCH = "午"
if body_b != REF_BODY_BRANCH:
    diffs.append(f"身宫地支: 我们={body_b}, 参考={REF_BODY_BRANCH}")
    print(f"  ⚠ 身宫地支不匹配: 我们={body_b}, 参考={REF_BODY_BRANCH}")
else:
    print(f"  ✓ 身宫在午(官禄宫)")

# ============================================================
# 9. 五行局
# ============================================================
print()
print("=" * 70)
print("9. 五行局")
print("=" * 70)

wuxing = data.get("wuxing_ju_name", "")
print(f"  五行局: {wuxing} (参考: 土五局)")
if "五" not in wuxing:
    diffs.append(f"五行局: 我们={wuxing}, 参考=土五局")

# ============================================================
# 10. 流年信息
# ============================================================
print()
print("=" * 70)
print("10. 流年信息 (2026)")
print("=" * 70)

liunian = data.get("liunian", {})
ln_gz = liunian.get("year_gz", "")
ln_year = liunian.get("year", 0)
ln_branch = liunian.get("life_palace_branch", "")
ln_sihua = liunian.get("sihua", {})

print(f"  流年干支: {ln_gz} (参考: 丙午)")
if ln_gz != "丙午":
    diffs.append(f"流年干支: 我们={ln_gz}, 参考=丙午")

print(f"  流年年份: {ln_year}")
print(f"  流年命宫: {ln_branch}")

# 丙干四化: 天同化禄, 天机化权, 文昌化科, 廉贞化忌
REF_LN_SIHUA = {"天同": "化禄", "天机": "化权", "文昌": "化科", "廉贞": "化忌"}
print(f"  流年四化: {ln_sihua}")
for star, expected in REF_LN_SIHUA.items():
    actual = ln_sihua.get(star, "无")
    ok = actual == expected
    status = "✓" if ok else "✗"
    print(f"    {star}: {actual} {status} (参考: {expected})")
    if not ok:
        diffs.append(f"流年四化: {star} 我们={actual}, 参考={expected}")

# ============================================================
# 11. 不同案例交叉验证: 男命/阳年 (阳男顺行)
# ============================================================
print()
print("=" * 70)
print("11. 交叉验证: 男命 1990-07-17 10:25 (庚午年 阳男)")
print("=" * 70)

r2 = requests.post(API, json={
    "year": 1990, "month": 7, "day": 17, "hour": 10, "minute": 25,
    "gender": "男", "liunian_year": 2026,
})
if r2.status_code == 200:
    d2 = r2.json()
    dayun2 = d2.get("dayun", {})
    print(f"  大运方向: {'顺行' if dayun2.get('forward') else '逆行'} (参考: 阳男应顺行)")
    if not dayun2.get("forward"):
        diffs.append("交叉验证: 阳男大运应顺行但引擎返回逆行")

    # 阳男顺行: 从命宫寅开始, 寅→卯→辰→巳...
    items2 = dayun2.get("items", [])
    if items2:
        first_gz = items2[0]["ganzhi"]
        # 阳男命宫也是寅, 应该是戊寅
        print(f"  第1限干支: {first_gz}")
        # 长生: 阳男 + 阳年 → 顺行(forward=True代码), 土五局start=申(8)
        # forward=True: idx = (8+i)%12 → 申=长生, 酉=沐浴, 戌=冠带...
        cs2 = {}
        for p2 in d2["palaces"]:
            cs2[p2["branch"]] = p2.get("changsheng", "")
        print(f"  长生@申: {cs2.get('申','')} (参考: 长生)")
        print(f"  长生@酉: {cs2.get('酉','')} (参考: 沐浴)")
        print(f"  长生@寅: {cs2.get('寅','')} (参考: 衰)")

        # 阳男(forward=True): start=8, idx=(8+i)%12
        CS = ["长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]
        ref_cs = {}
        for i, star in enumerate(CS):
            idx = (8 + i) % 12
            ref_cs[BRANCHES[idx]] = star

        cs_ok = 0
        for br in BRANCHES:
            if cs2.get(br) == ref_cs.get(br):
                cs_ok += 1
            else:
                print(f"  ⚠ 长生@{br}: 我们={cs2.get(br,'')}, 应={ref_cs.get(br,'')}")
        print(f"  长生匹配: {cs_ok}/12")
        if cs_ok < 12:
            diffs.append(f"交叉验证男命: 长生匹配 {cs_ok}/12")
else:
    print(f"  API错误: {r2.status_code}")

# ============================================================
# 总结
# ============================================================
print()
print("=" * 70)
print("总结")
print("=" * 70)
if diffs:
    print(f"  共 {len(diffs)} 个差异:")
    for d in diffs:
        print(f"    ❌ {d}")
else:
    print("  ✅ 全部深度对比通过，无差异")
