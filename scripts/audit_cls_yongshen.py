"""CLS yongshen drift audit."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from services.bazi_engine_service import calculate

data = json.loads(Path("data/ground_truth_cases.json").read_text(encoding="utf-8"))
for c in data["cases"]:
    if not c.get("pre_1900"):
        continue
    rec = sorted(c.get("recorded_yongshen") or [])
    eng = sorted(c.get("engine_yongshen_favor") or [])
    dt = datetime.fromisoformat(c["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    r = calculate(dt, c["longitude"], "Asia/Shanghai", False, "single", c.get("gender"))
    live = sorted(r.verify_response.yongshen.favor or [])
    if rec == live:
        print(f"{c['id']} OK {rec}")
        continue
    if rec == eng:
        print(f"{c['id']} OK (json) {rec}")
        continue
    vr = r.verify_response
    ys = vr.yongshen
    print(f"{c['id']} geju={c.get('engine_geju')} strength={vr.day_master_strength}")
    print(f"  rec={rec}")
    print(f"  eng_json={eng}")
    print(f"  eng_live={live}")
    print(f"  avoid={sorted(ys.avoid or [])}")
    print(f"  comment={c.get('recorded_dayun_comment', '')[:80]}")
    print()
