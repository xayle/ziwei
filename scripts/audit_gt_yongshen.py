"""GT post-1900 yongshen: recorded vs live engine."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from services.bazi_engine_service import calculate

data = json.loads(Path("data/ground_truth_cases.json").read_text(encoding="utf-8"))
print("=== GT yongshen: recorded vs live ===")
for c in data["cases"]:
    if c.get("pre_1900") or not c.get("verified_pillars"):
        continue
    dt = datetime.fromisoformat(c["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    r = calculate(dt, c["longitude"], "Asia/Shanghai", False, "single", c.get("gender"))
    live = sorted(r.verify_response.yongshen.favor or [])
    rec = sorted(c.get("recorded_yongshen") or [])
    eng = sorted(c.get("engine_yongshen_favor") or [])
    print(
        f"{c['id']} geju={c.get('engine_geju')} "
        f"baseline_ok={live == eng} vs_rec={live == rec if rec else 'n/a'} "
        f"rec={rec} live={live}"
    )
