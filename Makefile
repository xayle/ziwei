.PHONY: dev-install lint format security test test-fast quality-gate quality-gate-backend quality-gate-frontend export-openapi sync-frontend-types import-classics verify-ctext verify-classics-ctext scorecard verify-iztro-install verify-iztro verify-iztro-hour verify-iztro-calibrate verify-horoscope-iztro verify-wenmo-horoscope verify-wenmo-bazi capture-live-targets verify-volume-names

dev-install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

lint:
	ruff check .
	ruff format --check .
	pyright --project pyrightconfig.json

format:
	ruff format .
	ruff check --fix .

security:
	bandit -r app services routers run.py db.py constants.py boundary.py backends.py -ll

test:
	python -m pytest -q --ignore=tests/e2e --ignore=tests/legacy

test-fast:
	python -m pytest -q -n auto --ignore=tests/e2e --ignore=tests/legacy

scorecard:
	python scripts/audit_scorecard.py

verify-iztro-install:
	cd scripts/iztro && npm install

verify-iztro: verify-iztro-install
	node scripts/verify_ziwei_iztro.mjs

verify-iztro-hour: verify-iztro-install
	node scripts/verify_ziwei_iztro.mjs --youbi=hour

verify-iztro-calibrate: verify-iztro-install
	node scripts/verify_ziwei_iztro.mjs --calibrate

verify-horoscope-iztro: verify-iztro-install
	node scripts/verify_ziwei_horoscope_iztro.mjs --case WM01

verify-wenmo-horoscope:
	python scripts/wenmo_engine_diff.py --horoscope --write

capture-live-targets:
	node scripts/capture-live-targets.mjs

compare-live-targets:
	node scripts/compare-live-targets.mjs

auto-verify-w14:
	python scripts/auto_verify_w14.py

auto-verify-r007:
	python scripts/auto_verify_r007.py

auto-verify-r103:
	python scripts/auto_verify_r103.py

auto-verify-env:
	python scripts/auto_verify_env.py

auto-verify-r060:
	python scripts/auto_verify_r060.py

generate-r108:
	python scripts/generate_r108_release.py

verify-wenmo-bazi:
	python scripts/wenmo_engine_diff.py --bazi --write

verify-volume-names:
	python scripts/verify_volume_names.py

quality-gate:
	python scripts/quality_gate.py

quality-gate-backend:
	python scripts/quality_gate.py --section backend

quality-gate-full:
	python scripts/quality_gate.py --section backend --with-scorecard

quality-gate-frontend:
	python scripts/quality_gate.py --section frontend

export-openapi:
	python scripts/export_openapi.py

sync-frontend-types: export-openapi
	cd frontend && npm run gen:types

import-classics:
	python scripts/import_github_classics.py --skip-download --merge-gt

verify-ctext:
	python scripts/import_github_classics.py --verify-ctext

verify-classics-ctext:
	python scripts/verify_classics_ctext.py

spotcheck-ctext:
	python scripts/spotcheck_ctext_pages.py
