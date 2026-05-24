"""对比紫微斗数计算结果与文墨天机参考数据"""
import requests, json

r = requests.post('http://localhost:5173/api/v1/ziwei/full', json={
    'year': 1990, 'month': 7, 'day': 17, 'hour': 10, 'minute': 25,
    'gender': '女'
})
d = r.json()

print("=== 基本信息 ===")
print(f"birth_solar: {d.get('birth_solar')}")
print(f"gender: {d.get('gender')}")
print(f"life_palace_gz: {d.get('life_palace_gz')}")
print(f"body_palace_gz: {d.get('body_palace_gz')}")
print(f"wuxing_ju: {d.get('wuxing_ju')} {d.get('wuxing_ju_name')}")
print(f"life_palace_branch_idx: {d.get('life_palace_branch_idx')}")
print(f"body_palace_branch_idx: {d.get('body_palace_branch_idx')}")
print(f"true_solar_time: {d.get('true_solar_time')}")
print(f"life_ruler_star: {d.get('life_ruler_star')}")
print(f"body_ruler_star: {d.get('body_ruler_star')}")

print("\n=== 农历 ===")
lu = d.get('lunar', {})
print(f"lunar_year: {lu.get('lunar_year')}")
print(f"lunar_month: {lu.get('lunar_month')}")
print(f"lunar_day: {lu.get('lunar_day')}")
print(f"is_leap_month: {lu.get('is_leap_month')}")
print(f"year_gz: {lu.get('year_gz')}")
print(f"month_gz: {lu.get('month_gz')}")
print(f"hour_branch: {lu.get('hour_branch')}")
print(f"jieqi_month_gz: {lu.get('jieqi_month_gz')}")

print("\n=== 十二宫 ===")
BRANCHES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
for p in d.get('palaces', []):
    main_stars = ', '.join(s['name'] + '(' + s['brightness'] + ')' for s in p.get('main_stars', []))
    transforms = []
    for s in p.get('main_stars', []):
        for t in s.get('transforms', []):
            transforms.append(s['name'] + t)
    tr_str = '  四化: ' + ' '.join(transforms) if transforms else ''
    aux_list = [a['name'] if isinstance(a, dict) else a for a in p.get('aux_stars', [])]
    aux_str = ', '.join(aux_list[:8])
    print(f"  [{p['index']:2d}] {p['name']:4s} {p['stem']}{p['branch']}  主星: {main_stars}{tr_str}")
    if aux_str:
        print(f"       辅星: {aux_str}")

print("\n=== 大运 ===")
dy = d.get('dayun', {})
print(f"forward: {dy.get('forward')}")
print(f"start_age: {dy.get('start_age')}")
print(f"start_age_exact: {dy.get('start_age_exact')}")
print(f"start_age_text: {dy.get('start_age_text')}")
for item in dy.get('items', [])[:10]:
    sihua = item.get('sihua', {})
    sihua_str = ' '.join(f"{k}:{v}" for k, v in sihua.items()) if sihua else ''
    print(f"  {item['ganzhi']}  {item['start_age']}~{item['end_age']}  起始年:{item.get('start_year', '?')}  {sihua_str}")

print("\n=== 流年 ===")
ln = d.get('liunian')
if ln:
    print(f"year: {ln.get('year')}")
    print(f"year_gz: {ln.get('year_gz')}")
    print(f"life_palace_branch: {ln.get('life_palace_branch')}")
    sihua = ln.get('sihua', {})
    print(f"sihua: {json.dumps(sihua, ensure_ascii=False)}")

print("\n=== 格局 ===")
for pt in d.get('patterns', [])[:15]:
    print(f"  {pt['name']} ({pt['level']}): {pt.get('description', '')[:60]}")

print("\n=== summary ===")
print(d.get('summary', ''))
