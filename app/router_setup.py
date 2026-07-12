from __future__ import annotations

from fastapi import FastAPI

from routers import analytics as analytics_router
from routers import api_keys as api_keys_router
from routers import audit as audit_router
from routers import auth as auth_router
from routers import bazi as bazi_router
from routers import cases as cases_router
from routers import compat as compat_router
from routers import compute as compute_router
from routers import delegation as delegation_router
from routers import event_prediction as event_prediction_router
from routers import events as events_router
from routers import experiments as experiments_router
from routers import export as export_router
from routers import fengshui as fengshui_router
from routers import fusheng_report as fusheng_report_router
from routers import life as life_router
from routers import liuyao as liuyao_router
from routers import llm as llm_router
from routers import members as members_router
from routers import fusheng_archive as fusheng_archive_router
from routers import notifications as notifications_router
from routers import payment as payment_router
from routers import name as name_router
from routers import privacy as privacy_router
from routers import quickstart as quickstart_router
from routers import relations as relations_router
from routers import reviews as reviews_router
from routers import rules_admin as rules_admin_router
from routers import scenarios as scenarios_router
from routers import similarity as similarity_router
from routers import snapshots as snapshots_router
from routers import static_data as static_data_router
from routers import tarot as tarot_router
from routers import v2 as v2_router_module
from routers import verify as verify_router
from routers import western as western_router
from routers import zeri as zeri_router
from routers import ziwei as ziwei_router_module


def _include_core_routers(app: FastAPI) -> None:
    app.include_router(cases_router.router)
    app.include_router(cases_router._share_router)
    app.include_router(relations_router.router)
    app.include_router(bazi_router.router)
    app.include_router(compute_router.router)
    app.include_router(snapshots_router.router)
    app.include_router(auth_router.router)
    app.include_router(members_router.router)
    app.include_router(delegation_router.router)
    app.include_router(audit_router.router)
    app.include_router(events_router.router)
    app.include_router(scenarios_router.router)
    app.include_router(static_data_router.router)
    app.include_router(quickstart_router.router)
    app.include_router(v2_router_module.router, prefix="/api/v2")
    app.include_router(ziwei_router_module.router)


def _include_workflow_routers(app: FastAPI) -> None:
    app.include_router(reviews_router.router)
    app.include_router(experiments_router.router)
    app.include_router(llm_router.router)
    app.include_router(similarity_router.router)
    app.include_router(api_keys_router.router)
    app.include_router(zeri_router.router)
    app.include_router(export_router.router)
    app.include_router(fusheng_report_router.router)
    app.include_router(fusheng_archive_router.router)
    app.include_router(life_router.router)
    app.include_router(notifications_router.router)
    app.include_router(payment_router.router)
    app.include_router(fengshui_router.router)
    app.include_router(rules_admin_router.router)
    app.include_router(analytics_router.router)
    app.include_router(privacy_router.router)


def _include_page_routers(app: FastAPI) -> None:
    app.include_router(name_router.router)
    app.include_router(western_router.router)
    app.include_router(compat_router.router)
    app.include_router(event_prediction_router.router)
    app.include_router(liuyao_router.router)
    app.include_router(tarot_router.router)
    app.include_router(verify_router.router)


def include_all_routers(app: FastAPI) -> None:
    _include_core_routers(app)
    _include_workflow_routers(app)
    _include_page_routers(app)
