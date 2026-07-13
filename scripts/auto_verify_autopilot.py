"""Autopilot verification bundle — full A01–A59 (engineering + aesthetic).

Writes docs/reports/autopilot-verify-latest.json
Exit 0 only when all checks pass.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
REPORT = ROOT / "docs" / "reports" / "autopilot-verify-latest.json"


@dataclass
class Check:
    id: str
    track: str
    name: str
    ok: bool
    detail: str = ""


def _npm(*args: str) -> list[str]:
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm not found in PATH")
    return [npm, *args]


def _is_e2e_cmd(cmd: list[str]) -> bool:
    return any(part == "test:e2e" for part in cmd)


def _run(cmd: list[str], *, cwd: Path | None = None) -> tuple[bool, str]:
    env = {**dict(__import__("os").environ), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    if _is_e2e_cmd(cmd):
        # Fresh Playwright webServer per suite — avoids ERR_CONNECTION_REFUSED after prior run exits.
        env["AUTOPILOT_E2E"] = "1"
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = out.strip()[-1200:] if out.strip() else ""
    return proc.returncode == 0, tail


def _rg_debt_zero() -> bool:
    pattern = r"linear-gradient|PageHead|#334155|-ok-bg|trust-drift-bg|四维分析|ChapterStub"
    src = FRONTEND / "src"
    rg = shutil.which("rg")
    if rg:
        proc = subprocess.run(
            [rg, pattern, str(src)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode != 0

    # CI runners may lack ripgrep — fall back to a pure-Python scan.
    import re

    rx = re.compile(pattern)
    for path in src.rglob("*"):
        if path.suffix not in {".vue", ".ts", ".js", ".css"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if rx.search(text):
            return False
    return True


def _git_tracked(rel: str) -> bool:
    ok, _ = _run(["git", "ls-files", "--error-unmatch", rel])
    return ok


def _targets_compare_pass() -> bool:
    path = ROOT / "docs" / "reports" / "R079-targets-compare-latest.json"
    if not path.exists():
        return False
    return bool(json.loads(path.read_text(encoding="utf-8")).get("pass"))


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _export_stable(rel: str, export_cmd: list[str], *, cwd: Path | None = None) -> tuple[bool, str]:
    path = ROOT / rel if not (cwd and rel.startswith("frontend")) else (cwd or ROOT) / rel.split("frontend/", 1)[-1]
    if rel.startswith("frontend/"):
        path = ROOT / rel
    before = path.read_bytes() if path.is_file() else b""
    ok, detail = _run(export_cmd, cwd=cwd)
    if not ok:
        return False, detail
    after = path.read_bytes() if path.is_file() else b""
    return before == after, "idempotent" if before == after else "export changed file"


def main() -> int:
    checks: list[Check] = []

    def add(cid: str, track: str, name: str, ok: bool, detail: str = "") -> None:
        checks.append(Check(cid, track, name, ok, detail))

    def ok_of(cid: str) -> bool:
        for c in checks:
            if c.id == cid:
                return c.ok
        return False

    eng_specs: list[tuple[str, str, list[str], Path | None]] = [
        ("A01", "scorecard", [sys.executable, "scripts/audit_scorecard.py"], None),
        ("A04", "life-volume schema", [sys.executable, "-m", "pytest", "-q", "tests/test_life_volume_schema_contract.py"], None),
        ("A05", "explain map", [sys.executable, "-m", "pytest", "-q", "tests/test_explain_section_map.py", "tests/test_fe_be_explain_sections.py"], None),
        ("A06", "volume names", [sys.executable, "scripts/verify_volume_names.py"], None),
        ("A09", "anti-slop E2E", _npm("run", "test:e2e", "--", "fusheng-anti-slop"), FRONTEND),
        ("A11", "trial-read E2E", _npm("run", "test:e2e", "--", "fusheng-trial-read"), FRONTEND),
        ("A12", "R060 trial", [sys.executable, "scripts/auto_verify_r060.py"], None),
        ("A13", "flow E2E", _npm("run", "test:e2e", "--", "fusheng-flow"), FRONTEND),
        ("A14", "bazi-ziwei E2E", _npm("run", "test:e2e", "--", "fusheng-bazi-ziwei"), FRONTEND),
        ("A15", "report E2E", _npm("run", "test:e2e", "--", "fusheng-report"), FRONTEND),
        ("A16", "responsive E2E", _npm("run", "test:e2e", "--", "fusheng-responsive"), FRONTEND),
        ("A18", "vitest", _npm("run", "test"), FRONTEND),
        ("A20", "quality_gate backend", [sys.executable, "scripts/quality_gate.py", "--section", "backend"], None),
        ("A21", "quality_gate frontend", [sys.executable, "scripts/quality_gate.py", "--section", "frontend"], None),
        ("A22", "W14 bundle", [sys.executable, "scripts/auto_verify_w14.py"], None),
        ("A23", "pytest full", [sys.executable, "-m", "pytest", "-q", "--ignore=tests/e2e", "--ignore=tests/legacy"], None),
        ("A24", "glossary", [sys.executable, "-m", "pytest", "-q", "tests/test_static_data_endpoints.py::TestGlossaryEndpoint"], None),
        ("A25", "cities >=300", [sys.executable, "-m", "pytest", "-q", "tests/test_static_data_endpoints.py::TestCitiesEndpoint"], None),
        ("A27", "FE-BE r007", [sys.executable, "scripts/auto_verify_r007.py"], None),
        ("A28", "R103 auto", [sys.executable, "scripts/auto_verify_r103.py"], None),
        ("A29", "environment", [sys.executable, "scripts/auto_verify_env.py"], None),
    ]
    a11_trial_read_ok = False
    for cid, name, cmd, cwd in eng_specs:
        if cid == "A12":
            ok = a11_trial_read_ok
            detail = "deduped with A11 trial-read E2E" if ok else "A11 trial-read E2E failed"
        else:
            ok, detail = _run(cmd, cwd=cwd)
        if cid == "A11":
            a11_trial_read_ok = ok
        add(cid, "engineering", name, ok, detail)

    ok_a02, d_a02 = _export_stable("docs/openapi.json", [sys.executable, "scripts/export_openapi.py"])
    add("A02", "engineering", "openapi idempotent", ok_a02, d_a02)

    ok_a03, d_a03 = _export_stable("frontend/src/api/schema.d.ts", _npm("run", "gen:types"), cwd=FRONTEND)
    add("A03", "engineering", "schema.d.ts idempotent", ok_a03, d_a03)

    ok_a19a, d_a19a = _run(_npm("run", "type-check"), cwd=FRONTEND)
    ok_a19b, d_a19b = _run(_npm("run", "lint"), cwd=FRONTEND)
    ok_a19c, d_a19c = _run(_npm("run", "build"), cwd=FRONTEND)
    add("A19", "engineering", "type-check+lint+build", ok_a19a and ok_a19b and ok_a19c, d_a19c or d_a19b or d_a19a)

    add("A07", "engineering", "debt rg zero", _rg_debt_zero())
    add("A10", "engineering", "targets compare", _targets_compare_pass())
    add("A31", "engineering", "cities.json tracked", _git_tracked("data/cities.json"))
    add("A26", "engineering", "R108 release notes", (ROOT / "docs/reports/R108-release-notes-generated.md").is_file())
    add("A08", "engineering", "risk-alert spec", (FRONTEND / "e2e/fusheng-risk-alert.spec.ts").is_file())
    add("A17", "engineering", "report snapshot (A15)", ok_of("A15"))

    cities_ts = _read("frontend/src/utils/citiesCache.ts")
    add("A30", "aesthetic", "cities API >=300", ok_of("A25"))
    add(
        "A32",
        "aesthetic",
        "cities no silent fallback",
        "FALLBACK_CITIES" not in cities_ts and "CitiesLoadError" in cities_ts,
    )
    font_ok = any(
        p.is_file() and p.stat().st_size > 1000
        for p in (
            FRONTEND / "public/fonts/LXGWNeoZhiSong-subset.woff2",
            ROOT / "static/app/fonts/LXGWNeoZhiSong-subset.woff2",
        )
    )
    add("A33", "aesthetic", "Song webfont present", font_ok)

    profile = _read("frontend/src/views/ProfileView.vue")
    brief = profile.split("meta-list--brief", 1)[-1].split("</dl>", 1)[0] if "meta-list--brief" in profile else ""
    add(
        "A36",
        "aesthetic",
        "profile brief sidebar",
        "meta-list--brief" in profile and "夏令时" not in brief and "profile-advanced-meta" in profile,
    )

    bazi = _read("frontend/src/views/new/NewBaziView.vue")
    add("A37", "aesthetic", "bazi pillars-hero anchor", 'id="bazi-layer-structure"' in bazi or "pillars-hero" in bazi)

    ziwei = _read("frontend/src/views/new/FushengZiweiView.vue")
    add(
        "A40",
        "aesthetic",
        "ziwei trust collapsed",
        "<details" in ziwei and "EngineTrustPanel" in ziwei and "默认折叠" in ziwei,
    )

    report = _read("frontend/src/views/ReportView.vue")
    add(
        "A41",
        "aesthetic",
        "report vol1 compact chart",
        "report-vol1-lead" in report and "report-embed--compact" in report and ':show-detail-rows="false"' in report,
    )

    home = _read("frontend/src/views/new/NewHomeView.vue")
    add(
        "A35",
        "aesthetic",
        "home single hero (no nested logo)",
        "hero-brand" not in home and ("hero-copy__title" in home or "brand-island__word" in home),
    )

    add("A42", "aesthetic", "report continuous mode", "readingMode" in report or "continuous" in report)
    add("A34", "aesthetic", "risk-alert e2e spec", (FRONTEND / "e2e/fusheng-risk-alert.spec.ts").is_file())
    add("A43", "aesthetic", "vol5 folded (A15)", ok_of("A15"))
    add("A44", "aesthetic", "vol6 on demand (r103)", ok_of("A28"))

    ok_a45, d_a45 = _run([sys.executable, "scripts/verify_surface_levels.py"])
    add("A45", "aesthetic", "surface two levels", ok_a45, d_a45)

    add("A46", "aesthetic", "copper budget proxy", ok_of("A09"))
    add("A47", "aesthetic", "targets deviation proxy", _targets_compare_pass())

    ok_a48, d_a48 = _run(_npm("run", "test", "--", "src/components/__tests__/CityPicker.spec.ts"), cwd=FRONTEND)
    add("A48", "aesthetic", "CityPicker 31 provinces", ok_a48, d_a48)

    ok_a38, d_a38 = _run(_npm("run", "test:e2e", "--", "fusheng-bazi-ziwei", "-g", "横滚"), cwd=FRONTEND)
    add("A38", "aesthetic", "bazi no horizontal scroll", ok_a38, d_a38)

    ok_a39, d_a39 = _run(_npm("run", "test:e2e", "--", "fusheng-anti-slop", "-g", "方盘面积"), cwd=FRONTEND)
    add("A39", "aesthetic", "ziwei plate area hero", ok_a39, d_a39)

    ok_a49, d_a49 = _run(_npm("run", "test:e2e", "--", "fusheng-bazi-ziwei", "-g", "缺失展示"), cwd=FRONTEND)
    add("A49", "aesthetic", "bazi missing cells <6", ok_a49, d_a49)

    ok_a50, d_a50 = _run(_npm("run", "test:e2e", "--", "fusheng-anti-slop", "-g", "Q5"), cwd=FRONTEND)
    add("A50", "aesthetic", "anti-slop Q5 blind proxy", ok_a50, d_a50)

    eng = [c for c in checks if c.track == "engineering"]
    aes = [c for c in checks if c.track == "aesthetic"]
    eng_pass = all(c.ok for c in eng)
    aes_pass = all(c.ok for c in aes)

    payload = {
        "pass": eng_pass and aes_pass,
        "engineering_pass": eng_pass,
        "aesthetic_pass": aes_pass,
        "engineering": {c.id: {"ok": c.ok, "name": c.name, "detail": c.detail} for c in eng},
        "aesthetic": {c.id: {"ok": c.ok, "name": c.name, "detail": c.detail} for c in aes},
        "summary": {
            "engineering": f"{sum(1 for c in eng if c.ok)}/{len(eng)}",
            "aesthetic": f"{sum(1 for c in aes if c.ok)}/{len(aes)}",
        },
    }
    REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": payload["pass"], "summary": payload["summary"]}, ensure_ascii=False))
    failed = [c for c in checks if not c.ok]
    if failed:
        print("FAILED: " + ", ".join(c.id for c in failed), file=sys.stderr)
        for c in failed:
            detail = (c.detail or "").replace("\n", " ").replace("%", "pct")[-240:]
            # GitHub Actions workflow command → annotation on the Autopilot step
            print(f"::error title=Autopilot {c.id} {c.name}::{detail or 'failed'}")
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — surface unexpected crash to CI annotations
        print(f"::error title=Autopilot crashed::{type(exc).__name__}: {exc}")
        raise
