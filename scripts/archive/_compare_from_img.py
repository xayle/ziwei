import requests
import json

params = {
    'year': 1990,
    'month': 7,
    'day': 17,
    'hour': 10,
    'minute': 25,
    'gender': '女',
    'liunian_year': 2026
}
headers = {'Authorization': 'Bearer test'}

r = requests.post('http://127.0.0.1:8000/api/v1/ziwei/full', json=params, headers=headers, timeout=10)
data = r.json()

print('=== 完整辅星分布 ===')
for p in data['palaces']:
    aux = p.get('aux_stars', [])
    jq = p.get('jiangqian_star','')
    sq = p.get('suiqian_star','')
    cs = p.get('changsheng','')
    ms = [s['name']+'('+s.get('brightness','')+')' for s in p.get('main_stars',[])]
    print(f"{p['name']:5s} {p['branch']}{p['stem']}  主:{ms}  辅:{aux}  将前:{jq}  岁前:{sq}  长生:{cs}")

print('\n=== 大运四化+博士 ===')
for item in data['dayun']['items'][:4]:
    print(f"  {item['ganzhi']} {item['start_age']}~{item['end_age']}  四化:{item.get('sihua',{})}  博士:{item.get('boshi_stars',{})}")

print('\n=== 流年四化 ===')
ln = data.get('liunian',{})
print(f"  {ln.get('year_gz','')} 流年命宫:{ln.get('life_palace_branch','')}  四化:{ln.get('sihua',{})}")

print('\n=== 飞星盘 ===')
fly = data.get('flying')
if fly:
    print(f"  palaces count: {len(fly.get('palaces',[]))}")
    fp0 = fly['palaces'][0] if fly.get('palaces') else {}
    print(f"  first palace keys: {list(fp0.keys())[:10]}")
