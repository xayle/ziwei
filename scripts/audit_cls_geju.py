"""One-off CLS geju audit helper."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from services.bazi_engine.geju import _check_huaqi, compute_geju
from services.bazi_engine_service import calculate

data = json.loads(Path("data/ground_truth_cases.json").read_text(encoding="utf-8"))
for c in data["cases"]:
    if not c.get("pre_1900"):
        continue
    p = c["computed_pillars"]
    ys, ms, ds, hs = p["year"][0], p["month"][0], p["day"][0], p["hour"][0]
    yb, mb, db, hb = p["year"][1], p["month"][1], p["day"][1], p["hour"][1]
    dt = datetime.fromisoformat(c["birth_dt_solar"]).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    wx = calculate(dt, c["longitude"], "Asia/Shanghai", False, "single", c.get("gender")).verify_response.wuxing_score.model_dump()
    r = compute_geju(ys, ms, mb, ds, hs, wx, yb, db, hb)
    hq = _check_huaqi([ys, ms, ds, hs], mb, day_stem=ds, day_branch=db)
    print(
        f"{c['id']} rec={c['recorded_geju']} eng={r['name']} type={r['type']} "
        f"tg={r['ten_god']} toukan={r['toukan_stem']} qi={r['month_qi']} huaqi={hq['is_huaqi']} day={ds}{db}"
    )
