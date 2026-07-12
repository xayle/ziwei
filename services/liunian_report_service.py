"""DB-backed liunian annual report async tasks (BE-P2-01)."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import uuid

from sqlmodel import Session

from app.models.async_task import LiunianReportTask
from services.normalize_input import normalize_birth_datetime

logger = logging.getLogger(__name__)


def create_liunian_task(
    session: Session,
    *,
    case_id: str,
    user_id: int,
    year: int,
    include_months: bool,
) -> LiunianReportTask:
    task = LiunianReportTask(
        id=str(uuid.uuid4()),
        case_id=case_id,
        user_id=user_id,
        year=year,
        include_months=include_months,
        status="queued",
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_liunian_task(session: Session, task_id: str) -> LiunianReportTask | None:
    return session.get(LiunianReportTask, task_id)


def _set_status(session: Session, task: LiunianReportTask, **fields) -> None:
    for key, value in fields.items():
        setattr(task, key, value)
    session.add(task)
    session.commit()


def task_to_response_dict(task: LiunianReportTask) -> dict:
    result = None
    if task.result_json:
        try:
            result = json.loads(task.result_json)
        except json.JSONDecodeError:
            result = None
    return {
        "task_id": task.id,
        "status": task.status,
        "year": task.year,
        "case_id": task.case_id,
        "submitted_at": task.submitted_at.isoformat() if task.submitted_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "result": result,
        "error": task.error,
    }


async def compute_liunian_report_result(case_id: str, year: int, include_months: bool) -> dict:
    """核心计算逻辑（供 worker 与测试复用）。"""
    from datetime import datetime as dt_cls
    from zoneinfo import ZoneInfo

    from app.models import Case
    from db import get_engine
    from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts
    from services.bazi_engine_service import calculate
    from services.bazi_full_service import ganzhi_for_year, ten_god

    with Session(get_engine()) as sess:
        case = sess.get(Case, case_id)
        if case is None or case.deleted_at is not None:
            raise ValueError(f"案例 {case_id!r} 不存在或已删除")
        birth_dt_local = case.birth_dt_local
        lon = float(case.lon)
        tz_name = case.tz or "Asia/Shanghai"
        gender = case.gender or "male"

    try:
        ZoneInfo(tz_name)
    except Exception:
        tz_name = "Asia/Shanghai"

    raw_dt = dt_cls.fromisoformat(birth_dt_local)
    if raw_dt.tzinfo is None or raw_dt.utcoffset() is None:
        raw_dt = raw_dt.replace(tzinfo=ZoneInfo(tz_name))
    dt_effective = normalize_birth_datetime(raw_dt, tz_name).local_dt
    calc = calculate(dt_effective, lon, tz_name, gender=gender)
    vr = calc.verify_response

    day_stem = vr.pillars_primary.day.stem
    day_branch = vr.pillars_primary.day.branch
    yongshen_favor = list(getattr(vr.yongshen, "favor", []) or [])
    wx = vr.wuxing_score
    wuxing_scores: dict[str, float] = (
        {
            "wood": float(wx.wood),
            "fire": float(wx.fire),
            "earth": float(wx.earth),
            "metal": float(wx.metal),
            "water": float(wx.water),
        }
        if wx
        else {}
    )

    shishen_scores: dict[str, float] = {}
    for stem in [vr.pillars_primary.year.stem, vr.pillars_primary.month.stem, vr.pillars_primary.hour.stem]:
        tg = ten_god(day_stem, stem)
        if tg:
            shishen_scores[tg] = shishen_scores.get(tg, 0) + 1.0

    year_stem, year_branch = ganzhi_for_year(year)
    year_ten_god = ten_god(day_stem, year_stem) or ""

    forecasts = compute_liunian_domain_forecasts(
        year=year,
        year_stem=year_stem,
        year_branch=year_branch,
        day_stem=day_stem,
        day_branch=day_branch,
        shishen_scores=shishen_scores,
        yongshen_favor=yongshen_favor,
        wuxing_scores=wuxing_scores,
        gender=gender,
        year_ten_god=year_ten_god,
    )

    months_data = []
    if include_months:
        branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        yr_stem_idx = stems.index(year_stem) if year_stem in stems else 0
        for i in range(12):
            m_stem = stems[(yr_stem_idx * 2 + i) % 10]
            m_branch = branches[(2 + i) % 12]
            m_tg = ten_god(day_stem, m_stem) or ""
            months_data.append(
                {
                    "month": i + 1,
                    "gz": f"{m_stem}{m_branch}",
                    "ten_god": m_tg,
                    "advice": f"{year}年{i + 1}月，{m_tg}月，宜顺势而为。" if m_tg else f"{year}年{i + 1}月稳步前行",
                }
            )

    return {
        "year": year,
        "year_gz": f"{year_stem}{year_branch}",
        "case_id": case_id,
        "day_stem": day_stem,
        "year_ten_god": year_ten_god,
        "overall_advice": f"{year}年（{year_stem}{year_branch}年）流年运势综合研判。",
        "career": forecasts.get("事业", ""),
        "wealth": forecasts.get("财运", ""),
        "relationship": forecasts.get("婚恋", ""),
        "health": forecasts.get("健康", ""),
        "months": months_data,
    }


async def build_liunian_report(task_id: str, case_id: str, year: int, include_months: bool) -> None:
    """Background worker: compute report and persist to DB."""
    from db import get_engine

    engine = get_engine()
    with Session(engine) as session:
        task = session.get(LiunianReportTask, task_id)
        if task is None:
            logger.warning("liunian task %s not found", task_id)
            return
        _set_status(session, task, status="running")

    try:
        result = await compute_liunian_report_result(case_id, year, include_months)
        with Session(engine) as session:
            task = session.get(LiunianReportTask, task_id)
            if task is None:
                return
            _set_status(
                session,
                task,
                status="done",
                result_json=json.dumps(result, ensure_ascii=False),
                finished_at=datetime.now(UTC),
                error=None,
            )
    except Exception as exc:
        logger.exception("liunian report failed task=%s", task_id)
        with Session(engine) as session:
            task = session.get(LiunianReportTask, task_id)
            if task is None:
                return
            _set_status(
                session,
                task,
                status="failed",
                error=str(exc),
                finished_at=datetime.now(UTC),
            )
