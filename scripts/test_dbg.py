import asyncio
from fastapi.testclient import TestClient
from run import app

client = TestClient(app)

payload = {
    "dt": "2026-02-24T12:34:56+08:00",
    "lon": 120.0,
    "mode": "dual",
    "solar_time_enabled": False,
    "tz": "Asia/Shanghai",
}
long_id = "a" * 130
resp = client.post("/api/v1/verify", json=payload, headers={"X-Request-Id": long_id})
print(resp.status_code)
import json
print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
