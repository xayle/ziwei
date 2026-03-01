import json
import urllib.request

payload = json.dumps({
    'dt': '2002-03-13T14:36:00',
    'tz': 'Asia/Shanghai',
    'lon': 121.4737,
    'mode': 'dual',
    'solar_time_enabled': False
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/verify',
    data=payload,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        content = resp.read().decode('utf-8')
        rj = json.loads(content)
        print('✓ API 请求成功！')
        print('===== 四柱数据 =====')
        print(f'  year stem: {rj["pillars_primary"]["year"]["stem"]}')
        print(f'  year branch: {rj["pillars_primary"]["year"]["branch"]}')
        print(f'  day stem: {rj["pillars_primary"]["day"]["stem"]}')
        print(f'  day branch: {rj["pillars_primary"]["day"]["branch"]}')
        print()
        print('===== 新增数据字段 =====')
        new_fields = ['wuxing_score', 'day_master_strength', 'yongshen', 'ten_gods']
        for field in new_fields:
            if field in rj:
                print(f'  ✓ {field} 已返回')
            else:
                print(f'  ✕ {field} 缺失')
        print()
        print('===== 十神数据 =====')
        ten_gods = rj.get('ten_gods', {})
        for col in ['year', 'month', 'day', 'hour']:
            code = ten_gods.get(col)
            print(f'  {col}: {code}')
except Exception as e:
    print(f'✕ 错误: {e}')
    import traceback
    traceback.print_exc()
