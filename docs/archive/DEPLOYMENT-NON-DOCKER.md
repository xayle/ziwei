# Deployment Guide (Non-Docker)

A concise, environment-agnostic guide to run the service without containers.

## 1) Prerequisites
- OS: Windows or Linux
- Python: 3.10+
- Database: PostgreSQL (or the DB used in your env)
- Redis: optional (only if enabling RedisCache)
- Tools: `git`, `pip`, `virtualenv`

## 2) Prepare Environment
1. Clone code and enter repo directory.
2. Create & activate venv:
   - Windows (PowerShell): `python -m venv .venv; .\.venv\Scripts\Activate.ps1`
   - Linux: `python -m venv .venv && source .venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Create `.env` (or reuse existing). Minimal variables:
   - `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`
   - `APP_ENV=prod`
   - `APP_HOST=0.0.0.0`
   - `APP_PORT=8000`
   - `REDIS_URL=redis://localhost:6379` (optional; omit to disable Redis cache)

## 3) Database Setup
- Ensure target DB is reachable and schema exists.
- If migrations exist, run them (e.g., `alembic upgrade head`).
- If relying on ORM auto-create, run once with correct credentials and confirm tables.

## 4) Run the Service
- Dev/foreground: `uvicorn run:app --host 0.0.0.0 --port 8000 --reload`
- Prod example: `uvicorn run:app --host 0.0.0.0 --port 8000 --workers 4`

## 5) Background/Service Mode
- Linux (systemd) sketch:
  - ExecStart=`/path/to/repo/.venv/bin/uvicorn run:app --host 0.0.0.0 --port 8000 --workers 4`
  - WorkingDirectory=`/path/to/repo`
  - User=service user; Restart=on-failure
- Windows: use NSSM/Task Scheduler to wrap the same uvicorn command.

## 6) Reverse Proxy (optional)
- Terminate TLS and forward to `127.0.0.1:8000` via Nginx/Apache.
- Configure timeouts and request size as needed; enable gzip if appropriate.

## 7) Health & Observability
- Health/metrics: `GET /metrics` should return HTTP 200 with Prometheus-format data.
- Logs: capture stdout/stderr; configure rotation (logrotate on Linux, or built-in tools on Windows).

## 8) Smoke Tests Before Go-Live
- Import check: `python -c "from routers import cases, members, events; print('import ok')"`
- Minimal pytest: `python -m pytest tests/test_auth_complete.py tests/test_bazi_full.py tests/test_cascade_validation.py -q`
- Full suite (optional): `python -m pytest -q`

## 9) Common Issues
- Missing Redis: remove/leave `REDIS_URL` empty to disable cache.
- DB auth/connectivity: verify `DATABASE_URL`, network, and credentials.
- Port in use: change `APP_PORT` or stop the conflicting service.

## 10) Rollback Tip
- Keep previous venv and code snapshot. If deploy fails, switch back to prior commit/venv and restart the service command.
