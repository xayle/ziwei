"""全面对比紫微斗数计算结果与文墨天机专业版参考数据
参考人: 刘*, 女, 1990-07-17 10:25, 庚午年闰五月廿五巳时
参考app: 文墨天机专业版 C5VUC pro 2.5.9
"""
import requests, json, sys

# ── 文墨天机参考数据（从截图提取）──────────────────────────────
REF = {
    "basic": {
        "gender": "女", "year_gz": "庚午", "month_gz": "癸未",
        "lunar": "闰五月廿五", "hour_branch": "巳",
        "life_palace_gz": "戊寅", "body_palace_gz": "戊子",
        "wuxing_ju": 5, "wuxing_ju_name": "土五局",
        "life_ruler": "禄存", "body_ruler": "火星",
    },
    # 宫名 → {stem+branch, [主星(亮度)], [辅星]}
    "palaces": {
        "命宫":   {"gz": "戊寅", "main": ["武曲(利)", "天相(庙)"],
                   "aux": ["天才"], "sihua": ["武曲化权"]},
        "兄弟宫": {"gz": "己丑", "main": ["天同(不)", "巨门(不)"],
                   "aux": ["天魁", "寡宿"], "sihua": ["天同化忌"]},
        "夫妻宫": {"gz": "戊子", "main": ["贪狼(旺)"],
                   "aux": [], "sihua": []},
        "子女宫": {"gz": "丁亥", "main": ["太阴(旺)"],
                   "aux": ["天官", "截空"], "sihua": ["太阴化科"]},
        "财帛宫": {"gz": "丙戌", "main": ["廉贞(利)", "天府(庙)"],
                   "aux": ["文曲", "截空"], "sihua": []},
        "疾厄宫": {"gz": "乙酉", "main": [],
                   "aux": ["左辅", "擎羊", "红鸾", "天使"], "sihua": []},
        "迁移宫": {"gz": "甲申", "main": ["破军(得)"],
                   "aux": ["禄存", "铃星", "天马", "天伤"], "sihua": []},
        "交友宫": {"gz": "癸未", "main": [],
                   "aux": ["天钺", "陀罗"], "sihua": []},
        "官禄宫": {"gz": "壬午", "main": ["紫微(旺)"],
                   "aux": ["火星", "地空", "天福", "天寿"], "sihua": []},
        "田宅宫": {"gz": "辛巳", "main": ["天机(利)"],
                   "aux": ["右弼", "孤辰"], "sihua": []},
        "福德宫": {"gz": "庚辰", "main": ["七杀(旺)"],
                   "aux": ["地劫", "天空"], "sihua": []},
        "父母宫": {"gz": "己卯", "main": ["太阳(庙)", "天梁(庙)"],
                   "aux": ["文昌", "天喜"], "sihua": ["太阳化禄"]},
    },
    # 大运（紫微大限法, 逆行, 土五局=5岁起运）
    "dayun": {
        "forward": False, "start_age": 5,
        "items": [
            {"gz": "戊寅", "ages": "5~14"},
            {"gz": "丁丑", "ages": "15~24"},
            {"gz": "丙子", "ages": "25~34"},
            {"gz": "乙亥", "ages": "35~44"},
            {"gz": "甲戌", "ages": "45~54"},
            {"gz": "癸酉", "ages": "55~64"},
            {"gz": "壬申", "ages": "65~74"},
            {"gz": "辛未", "ages": "75~84"},
            {"gz": "庚午", "ages": "85~94"},
            {"gz": "己巳", "ages": "95~104"},
        ],
    },
    "year_sihua": ["太阳化禄", "武曲化权", "太阴化科", "天同化忌"],
}

# ── 调用后端 ────────────────────────────────────────────────
try:
    r = requests.post('http://localhost:8000/api/v1/ziwei/full', json={
        'year': 1990, 'month': 7, 'day': 17, 'hour': 10, 'minute': 25,
        'gender': '女'
    }, timeout=10)
    r.raise_for_status()
    d = r.json()
except Exception as e:
    # fallback to vite proxy
    try:
        r = requests.post('http://localhost:5173/api/v1/ziwei/full', json={
            'year': 1990, 'month': 7, 'day': 17, 'hour': 10, 'minute': 25,
            'gender': '女'
        }, timeout=10)
        r.raise_for_status()
        d = r.json()
    except Exception as e2:
        print(f"无法连接后端: {e2}")
        sys.exit(1)

errors = []
warnings = []

def check(label, ours, ref, severity="ERROR"):
    if str(ours) != str(ref):
        msg = f"[{severity}] {label}: 我们={ours} | 参考={ref}"
        if severity == "ERROR":
            errors.append(msg)
        else:
            warnings.append(msg)
        return False
    return True

# ══════════════ 1. 基本信息 ══════════════
print("=" * 60)
print("1. 基本信息对比")
print("=" * 60)
rb = REF["basic"]
check("命宫干支", d.get("life_palace_gz"), rb["life_palace_gz"])
check("身宫干支", d.get("body_palace_gz"), rb["body_palace_gz"])
check("五行局数", d.get("wuxing_ju"), rb["wuxing_ju"])
check("五行局名", d.get("wuxing_ju_name"), rb["wuxing_ju_name"])
check("命主", d.get("life_ruler_star"), rb["life_ruler"])
check("身主", d.get("body_ruler_star"), rb["body_ruler"])
lu = d.get("lunar", {})
check("年柱", lu.get("year_gz"), rb["year_gz"])
check("月柱", lu.get("month_gz"), rb["month_gz"])
check("时支", lu.get("hour_branch"), rb["hour_branch"])
print(f"  命宫: {d.get('life_palace_gz')} {'✓' if d.get('life_palace_gz') == rb['life_palace_gz'] else '✗'}")
print(f"  身宫: {d.get('body_palace_gz')} {'✓' if d.get('body_palace_gz') == rb['body_palace_gz'] else '✗'}")
print(f"  五行局: {d.get('wuxing_ju_name')} {'✓' if d.get('wuxing_ju_name') == rb['wuxing_ju_name'] else '✗'}")
print(f"  命主/身主: {d.get('life_ruler_star')}/{d.get('body_ruler_star')} {'✓' if d.get('life_ruler_star') == rb['life_ruler'] and d.get('body_ruler_star') == rb['body_ruler'] else '✗'}")

# ══════════════ 2. 十二宫对比 ══════════════
print("\n" + "=" * 60)
print("2. 十二宫详细对比")
print("=" * 60)

for p in d.get("palaces", []):
    pname = p["name"]
    ref_p = REF["palaces"].get(pname)
    if not ref_p:
        continue

    our_gz = p["stem"] + p["branch"]
    gz_ok = check(f"{pname}干支", our_gz, ref_p["gz"])

    # 主星
    our_main = sorted([s["name"] + "(" + s["brightness"] + ")" for s in p.get("main_stars", [])])
    ref_main = sorted(ref_p["main"])
    # 仅比较星名（不含亮度）
    our_main_names = sorted([s["name"] for s in p.get("main_stars", [])])
    ref_main_names = sorted([m.split("(")[0] for m in ref_p["main"]])
    main_name_ok = our_main_names == ref_main_names
    if not main_name_ok:
        check(f"{pname}主星", ",".join(our_main_names), ",".join(ref_main_names))

    # 主星亮度
    for s in p.get("main_stars", []):
        sname = s["name"]
        for rm in ref_p["main"]:
            rname = rm.split("(")[0]
            rbright = rm.split("(")[1].rstrip(")")
            if sname == rname:
                if s["brightness"] != rbright:
                    check(f"{pname} {sname}亮度", s["brightness"], rbright, "WARN")

    # 四化
    our_sihua = []
    for s in p.get("main_stars", []):
        for t in s.get("transforms", []):
            our_sihua.append(s["name"] + t)
    ref_sihua = ref_p.get("sihua", [])
    if sorted(our_sihua) != sorted(ref_sihua):
        check(f"{pname}四化", ",".join(our_sihua) or "无", ",".join(ref_sihua) or "无", "WARN")

    # 辅星: 只检查缺失关键辅星
    our_aux = set(a["name"] if isinstance(a, dict) else a for a in p.get("aux_stars", []))
    ref_aux = set(ref_p.get("aux", []))
    missing = ref_aux - our_aux
    extra = our_aux - ref_aux
    
    status = "✓" if gz_ok and main_name_ok else "✗"
    bright_str = ", ".join(our_main)
    print(f"  {pname:4s} {our_gz} {status}  主星: {bright_str or '(空)'}")
    if missing:
        print(f"         辅星缺少: {', '.join(missing)}")
    if extra:
        # 只显示关键差异, 过滤掉不重要的
        important_extra = {e for e in extra if e not in ("截空1", "截空2")}
        # 参考里截空只显示一个, 我们可能拆成截空1/截空2
        if important_extra:
            print(f"         辅星多出: {', '.join(important_extra)}")

# ══════════════ 3. 年干四化对比 ══════════════
print("\n" + "=" * 60)
print("3. 年干四化 (庚干)")
print("=" * 60)
our_year_sihua = []
for p in d.get("palaces", []):
    for s in p.get("main_stars", []):
        for t in s.get("transforms", []):
            our_year_sihua.append(s["name"] + t)
ref_year_sihua = REF["year_sihua"]
print(f"  我们: {', '.join(sorted(our_year_sihua))}")
print(f"  参考: {', '.join(sorted(ref_year_sihua))}")
if sorted(our_year_sihua) == sorted(ref_year_sihua):
    print("  结果: ✓ 完全一致")
else:
    print("  结果: ✗ 有差异")
    our_set = set(our_year_sihua)
    ref_set = set(ref_year_sihua)
    if our_set - ref_set:
        print(f"  我们多出: {our_set - ref_set}")
    if ref_set - our_set:
        print(f"  我们缺少: {ref_set - our_set}")

# ══════════════ 4. 大运对比 ══════════════
print("\n" + "=" * 60)
print("4. 大运 (紫微大限)")
print("=" * 60)
dy = d.get("dayun", {})
ref_dy = REF["dayun"]
check("大运方向", dy.get("forward"), ref_dy["forward"])
check("起运岁数", dy.get("start_age"), ref_dy["start_age"])
print(f"  方向: {'顺行' if dy.get('forward') else '逆行'} {'✓' if dy.get('forward') == ref_dy['forward'] else '✗'}")
print(f"  起运: {dy.get('start_age')}岁 {'✓' if dy.get('start_age') == ref_dy['start_age'] else '✗'}")

our_items = dy.get("items", [])
ref_items = ref_dy["items"]
all_match = True
for i, ref_it in enumerate(ref_items):
    if i < len(our_items):
        our_gz = our_items[i]["ganzhi"]
        our_ages = f"{our_items[i]['start_age']}~{our_items[i]['end_age']}"
        gz_match = our_gz == ref_it["gz"]
        age_match = our_ages == ref_it["ages"]
        status = "✓" if gz_match and age_match else "✗"
        if not (gz_match and age_match):
            all_match = False
        print(f"  [{i+1:2d}] {our_gz} {our_ages} {status}  (参考: {ref_it['gz']} {ref_it['ages']})")
    else:
        print(f"  [{i+1:2d}] 缺少  (参考: {ref_it['gz']} {ref_it['ages']})")
        all_match = False

# ══════════════ 5. 总结 ══════════════
print("\n" + "=" * 60)
print("5. 总结")
print("=" * 60)
if errors:
    print(f"\n  ❌ 发现 {len(errors)} 个错误:")
    for e in errors:
        print(f"    {e}")
if warnings:
    print(f"\n  ⚠️  发现 {len(warnings)} 个警告:")
    for w in warnings:
        print(f"    {w}")
if not errors and not warnings:
    print("\n  ✅ 全部对比通过！")
elif not errors:
    print(f"\n  ✅ 无严重错误, {len(warnings)} 个细节差异(亮度/辅星)")
