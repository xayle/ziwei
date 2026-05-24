"""深度对比：辅星、小限、长生十二神、截空等"""
import requests, json

r = requests.post('http://localhost:8000/api/v1/ziwei/full', json={
    'year': 1990, 'month': 7, 'day': 17, 'hour': 10, 'minute': 25, 'gender': '女'
}, timeout=10)
d = r.json()

# ── 文墨天机参考辅星 ──
REF_AUX = {
    "命宫":   ["天才"],
    "兄弟宫": ["天魁", "寡宿"],
    "夫妻宫": [],
    "子女宫": ["天官", "截空"],
    "财帛宫": ["文曲", "截空"],
    "疾厄宫": ["左辅", "擎羊", "红鸾", "天使"],
    "迁移宫": ["禄存", "铃星", "天马", "天伤"],
    "交友宫": ["天钺", "陀罗"],
    "官禄宫": ["火星", "地空", "天福", "天寿"],
    "田宅宫": ["右弼", "孤辰"],
    "福德宫": ["地劫", "天空"],
    "父母宫": ["文昌", "天喜"],
}

# 参考：长生十二神 (土五局女命, 阳女逆行)
REF_CHANGSHENG = {
    "命宫":   "长生",   # 寅
    "兄弟宫": "养",     # 丑
    "夫妻宫": "胎",     # 子
    "子女宫": "绝",     # 亥
    "财帛宫": "墓",     # 戌
    "疾厄宫": "死",     # 酉
    "迁移宫": "病",     # 申
    "交友宫": "衰",     # 未
    "官禄宫": "帝旺",   # 午
    "田宅宫": "临官",   # 巳
    "福德宫": "冠带",   # 辰
    "父母宫": "沐浴",   # 卯
}

print("=" * 60)
print("1. 辅星对比")
print("=" * 60)
aux_errors = []
for p in d['palaces']:
    pname = p['name']
    our_aux = set(a['name'] if isinstance(a, dict) else a for a in p.get('aux_stars', []))
    ref_aux = set(REF_AUX.get(pname, []))

    # 截空特殊处理：我们拆成截空1/截空2，参考只显示截空
    our_jiekong = {a for a in our_aux if '截空' in a}
    ref_jiekong = {a for a in ref_aux if '截空' in a}
    our_aux_norm = our_aux - our_jiekong
    ref_aux_norm = ref_aux - ref_jiekong

    missing = ref_aux_norm - our_aux_norm
    extra = our_aux_norm - ref_aux_norm

    # 截空：参考有截空, 我们应有截空1或截空2
    jk_ok = True
    if ref_jiekong and not our_jiekong:
        missing.add("截空")
        jk_ok = False

    status = "✓" if (not missing and jk_ok) else "✗"
    aux_str = ', '.join(sorted(our_aux))
    print(f"  {pname:4s} {p['stem']}{p['branch']} {status}: {aux_str}")
    if missing:
        print(f"        缺少: {', '.join(missing)}")
        aux_errors.append(f"{pname}缺少{missing}")
    if extra:
        print(f"        多出: {', '.join(sorted(extra))}")

print(f"\n  辅星差异: {len(aux_errors)} 项")

print("\n" + "=" * 60)
print("2. 长生十二神对比")
print("=" * 60)
cs_errors = []
for p in d['palaces']:
    pname = p['name']
    our_cs = p.get('changsheng', '')
    ref_cs = REF_CHANGSHENG.get(pname, '')
    match = our_cs == ref_cs
    status = "✓" if match else "✗"
    print(f"  {pname:4s} {p['branch']}: {our_cs:4s} {status}  (参考: {ref_cs})")
    if not match:
        cs_errors.append(f"{pname}: 我们={our_cs}, 参考={ref_cs}")

print(f"\n  长生差异: {len(cs_errors)} 项")

print("\n" + "=" * 60)
print("3. 小限（第1~5岁对应宫位）")
print("=" * 60)
# 参考: 阳女(庚午年=阳), 年支午属火三合(寅午戌), 女起申, 逆行
# 1岁=申, 2岁=未, 3岁=午, 4岁=巳, 5岁=辰...
for p in d['palaces']:
    ages = p.get('xiaoxian_ages', [])[:6]
    if ages:
        print(f"  {p['name']:4s} {p['branch']}: {ages}")

print("\n" + "=" * 60)
print("4. 大限四化验证 (当前35~44, 乙亥)")
print("=" * 60)
dy = d['dayun']
for it in dy['items']:
    if it['start_age'] == 35:
        print(f"  干支: {it['ganzhi']}")
        sihua = it.get('sihua', {})
        print(f"  四化: {json.dumps(sihua, ensure_ascii=False)}")
        # 乙干四化: 天机化禄, 天梁化权, 紫微化科, 太阴化忌
        ref_sihua = {"天机": "化禄", "天梁": "化权", "紫微": "化科", "太阴": "化忌"}
        if sihua == ref_sihua:
            print("  ✓ 乙干四化正确")
        else:
            print(f"  ✗ 参考: {json.dumps(ref_sihua, ensure_ascii=False)}")
        break

print("\n" + "=" * 60)
print("5. 截空安星逻辑检查")
print("=" * 60)
# 截空: 根据日柱计算（甲子旬计算空亡）
# 打出截空1/截空2位置
for p in d['palaces']:
    aux = [a['name'] if isinstance(a, dict) else a for a in p.get('aux_stars', [])]
    jk = [a for a in aux if '截空' in a]
    if jk:
        print(f"  {p['name']:4s} {p['branch']}: {', '.join(jk)}")

print("\n" + "=" * 60)
print("6. 总结")
print("=" * 60)
total_issues = len(aux_errors) + len(cs_errors)
if total_issues == 0:
    print("  ✅ 深度对比全部通过")
else:
    print(f"  共 {total_issues} 个差异:")
    for e in aux_errors:
        print(f"    辅星: {e}")
    for e in cs_errors:
        print(f"    长生: {e}")
