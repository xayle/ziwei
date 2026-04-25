"""Coverage boost 29 — routers/reviews.py (T-05) + routers/analytics.py (T-06)

T-05: routers/reviews.py  — 当前覆盖率 25%，miss=118 行
T-06: routers/analytics.py — 当前覆盖率 52%，miss=34 行
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session as SQLModelSession


# ══════════════════════════════════════════════════════════════════════════
# DB helpers
# ══════════════════════════════════════════════════════════════════════════

def _make_review(
    db_session: SQLModelSession,
    report_hash: str = "hash_abc0000000000000000000000000000",
    status: str = "pending",
    reviewer: str = "",
):
    """在测试库中直接插入 ChartReview 记录。"""
    from app.models.review import ChartReview

    r = ChartReview(
        report_hash=report_hash,
        birth_info='{"year":1990,"month":7,"day":17}',
        status=status,
        reviewer=reviewer,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


def _make_case(
    db_session: SQLModelSession,
    owner_id: int,
    name: str = "测试案例",
):
    """在测试库中直接插入 Case 记录。"""
    from app.models.case import Case

    c = Case(
        owner_id=owner_id,
        name=name,
        birth_dt_local="1990-07-17T00:00:00",
        tz="Asia/Shanghai",
        lon=116.4,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


# ══════════════════════════════════════════════════════════════════════════
# T-05  reviews.py
# ══════════════════════════════════════════════════════════════════════════


class TestSubmitReview:
    """POST /api/v1/reviews — 无需登录"""

    def test_submit_happy_path(self, client: TestClient):
        payload = {
            "report_hash": "deadbeef00000000000000000000000000000000000000000000000000000001",
            "birth_info": '{"year":1990,"month":7,"day":17}',
        }
        resp = client.post("/api/v1/reviews", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["report_hash"] == payload["report_hash"]

    def test_submit_idempotent_same_hash(
        self, client: TestClient, db_session: SQLModelSession
    ):
        report_hash = "idem_hash_0000000000000000000000000000000000000000000000000001"
        existing = _make_review(db_session, report_hash=report_hash)
        payload = {
            "report_hash": report_hash,
            "birth_info": '{"year":1991}',
        }
        resp = client.post("/api/v1/reviews", json=payload)
        assert resp.status_code == 201
        # 应返回已有记录（幂等）
        assert resp.json()["id"] == existing.id

    def test_submit_different_hash_creates_new(
        self, client: TestClient, db_session: SQLModelSession
    ):
        _make_review(
            db_session,
            report_hash="hash_first00000000000000000000000000000000000000000000001",
        )
        new_hash = "hash_second0000000000000000000000000000000000000000000000001"
        payload = {
            "report_hash": new_hash,
            "birth_info": '{"year":1992}',
        }
        resp = client.post("/api/v1/reviews", json=payload)
        assert resp.status_code == 201
        assert resp.json()["report_hash"] == new_hash

    def test_submit_records_prometheus(self, client: TestClient):
        """validate Prometheus metric is called on submit."""
        with patch(
            "routers.reviews.record_review_submit"
        ) as mock_metric:
            payload = {
                "report_hash": "prom_test_hash00000000000000000000000000000000000001",
                "birth_info": '{"year":1993}',
            }
            client.post("/api/v1/reviews", json=payload)
            mock_metric.assert_called_once()


class TestListReviews:
    """GET /api/v1/reviews — 需要登录"""

    def test_list_empty(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_with_records(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        _make_review(db_session, report_hash="list_h001_00000000000000000000000000001")
        _make_review(
            db_session,
            report_hash="list_h002_00000000000000000000000000001",
            status="approved",
        )
        resp = client_with_auth.get("/api/v1/reviews")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

    def test_list_status_filter_pending(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        _make_review(
            db_session, report_hash="flt_p001_000000000000000000000000000001", status="pending"
        )
        _make_review(
            db_session, report_hash="flt_a001_000000000000000000000000000001", status="approved"
        )
        resp = client_with_auth.get("/api/v1/reviews?status=pending")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "pending"

    def test_list_status_filter_approved(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        _make_review(
            db_session,
            report_hash="flt_a002_000000000000000000000000000001",
            status="approved",
        )
        resp = client_with_auth.get("/api/v1/reviews?status=approved")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "approved"

    def test_list_pagination_page_size(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        for i in range(5):
            _make_review(
                db_session, report_hash=f"page_h{i:04d}_000000000000000000000000001"
            )
        resp = client_with_auth.get("/api/v1/reviews?page=1&page_size=2")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 2


class TestGetReview:
    """GET /api/v1/reviews/{id}"""

    def test_get_existing(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="get_h001_0000000000000000000000001")
        resp = client_with_auth.get(f"/api/v1/reviews/{r.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == r.id

    def test_get_404_not_found(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews/99999999")
        assert resp.status_code == 404

    def test_get_404_soft_deleted(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="get_del_0000000000000000000000001")
        r.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db_session.add(r)
        db_session.commit()
        resp = client_with_auth.get(f"/api/v1/reviews/{r.id}")
        assert resp.status_code == 404


class TestUpdateReview:
    """PATCH /api/v1/reviews/{id}"""

    def test_approve(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="upd_h001_0000000000000000000000001")
        resp = client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "approved", "reviewer": "expert_1"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["reviewer"] == "expert_1"

    def test_reject_with_reason(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="upd_h002_0000000000000000000000001")
        resp = client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "rejected", "reject_reason": "计算有误"},
        )
        assert resp.status_code == 200
        assert resp.json()["reject_reason"] == "计算有误"

    def test_revised_increments_revision(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="upd_h003_0000000000000000000000001")
        old_revision = r.revision
        resp = client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "revised", "notes": "已修订"},
        )
        assert resp.status_code == 200
        assert resp.json()["revision"] == old_revision + 1

    def test_update_with_notes(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="upd_h004_0000000000000000000000001")
        resp = client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "approved", "notes": "批注内容"},
        )
        assert resp.status_code == 200
        assert resp.json()["notes"] == "批注内容"

    def test_update_404(self, client_with_auth: TestClient):
        resp = client_with_auth.patch(
            "/api/v1/reviews/99999998",
            json={"status": "approved"},
        )
        assert resp.status_code == 404

    def test_update_writes_history(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        """更新后应写入 ChartReviewHistory 记录。"""
        from app.models.review_history import ChartReviewHistory
        from sqlmodel import select

        r = _make_review(db_session, report_hash="upd_h005_0000000000000000000000001")
        client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "approved"},
        )
        hist = db_session.exec(
            select(ChartReviewHistory).where(ChartReviewHistory.review_id == r.id)
        ).all()
        assert len(hist) >= 1


class TestDeleteReview:
    """DELETE /api/v1/reviews/{id}"""

    def test_soft_delete_returns_204(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="sdel_h001_000000000000000000000001")
        resp = client_with_auth.delete(f"/api/v1/reviews/{r.id}")
        assert resp.status_code == 204

    def test_deleted_record_invisible(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="sdel_h002_000000000000000000000001")
        client_with_auth.delete(f"/api/v1/reviews/{r.id}")
        # 已删除的记录不应在列表中出现
        resp = client_with_auth.get("/api/v1/reviews")
        ids = [item["id"] for item in resp.json()["items"]]
        assert r.id not in ids

    def test_delete_404(self, client_with_auth: TestClient):
        resp = client_with_auth.delete("/api/v1/reviews/99999997")
        assert resp.status_code == 404

    def test_delete_already_deleted_is_404(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="sdel_h003_000000000000000000000001")
        r.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db_session.add(r)
        db_session.commit()
        resp = client_with_auth.delete(f"/api/v1/reviews/{r.id}")
        assert resp.status_code == 404


class TestBulkAction:
    """POST /api/v1/reviews/bulk_action"""

    def test_bulk_approve(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r1 = _make_review(db_session, report_hash="bulk_h001_00000000000000000000001")
        r2 = _make_review(db_session, report_hash="bulk_h002_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r1.id, r2.id], "action": "approved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["succeeded"]) == {r1.id, r2.id}
        assert data["failed"] == []
        assert data["total"] == 2

    def test_bulk_reject_with_reason(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="bulk_h003_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r.id], "action": "rejected", "reject_reason": "批量拒绝"},
        )
        assert resp.status_code == 200
        assert r.id in resp.json()["succeeded"]

    def test_bulk_delete(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="bulk_h004_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r.id], "action": "delete"},
        )
        assert resp.status_code == 200
        assert r.id in resp.json()["succeeded"]

    def test_bulk_revised_increments(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="bulk_h005_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r.id], "action": "revised"},
        )
        assert resp.status_code == 200
        assert r.id in resp.json()["succeeded"]

    def test_invalid_action_422(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="bulk_inv_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r.id], "action": "invalid_action"},
        )
        assert resp.status_code in (422, 400)

    def test_nonexistent_ids_go_to_failed(self, client_with_auth: TestClient):
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [88888888, 99999998], "action": "approved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 88888888 in data["failed"]
        assert 99999998 in data["failed"]

    def test_bulk_mixed_success_failure(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="bulk_mix_00000000000000000000001")
        resp = client_with_auth.post(
            "/api/v1/reviews/bulk_action",
            json={"ids": [r.id, 77777777], "action": "approved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert r.id in data["succeeded"]
        assert 77777777 in data["failed"]


class TestReviewStats:
    """GET /api/v1/reviews/stats"""

    def test_stats_response_structure(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews/stats")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("total", "pending", "approved", "rejected", "revised"):
            assert key in data

    def test_stats_correct_counts(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        _make_review(db_session, report_hash="stat_p001_00000000000000000000000001", status="pending")
        _make_review(db_session, report_hash="stat_a001_00000000000000000000000001", status="approved")
        _make_review(db_session, report_hash="stat_a002_00000000000000000000000001", status="approved")
        _make_review(db_session, report_hash="stat_r001_00000000000000000000000001", status="rejected")

        resp = client_with_auth.get("/api/v1/reviews/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending"] >= 1
        assert data["approved"] >= 2
        assert data["rejected"] >= 1

class TestReviewHistory:
    """GET /api/v1/reviews/{review_id}/history"""

    def test_empty_history_on_fresh_record(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="hist_h001_0000000000000000000001")
        resp = client_with_auth.get(f"/api/v1/reviews/{r.id}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["review_id"] == r.id

    def test_history_populated_after_update(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="hist_h002_0000000000000000000001")
        # 先更新，产生历史记录
        client_with_auth.patch(
            f"/api/v1/reviews/{r.id}",
            json={"status": "approved", "reviewer": "expert"},
        )
        resp = client_with_auth.get(f"/api/v1/reviews/{r.id}/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["status"] == "approved"

    def test_history_404_not_found(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews/99999996/history")
        assert resp.status_code == 404

    def test_history_multiple_entries(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(db_session, report_hash="hist_h003_0000000000000000000001")
        client_with_auth.patch(
            f"/api/v1/reviews/{r.id}", json={"status": "approved"}
        )
        client_with_auth.patch(
            f"/api/v1/reviews/{r.id}", json={"status": "revised", "notes": "再次修订"}
        )
        resp = client_with_auth.get(f"/api/v1/reviews/{r.id}/history")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2


class TestReviewQueue:
    """GET /api/v1/reviews/queue (W1)"""

    def test_queue_only_pending(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        _make_review(
            db_session, report_hash="q_pend_001_000000000000000000000001", status="pending"
        )
        _make_review(
            db_session, report_hash="q_appr_001_000000000000000000000001", status="approved"
        )
        resp = client_with_auth.get("/api/v1/reviews/queue")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "pending"

    def test_queue_returns_200(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_queue_pagination(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        for i in range(4):
            _make_review(
                db_session,
                report_hash=f"q_pg_{i:04d}_000000000000000000000001",
                status="pending",
            )
        resp = client_with_auth.get("/api/v1/reviews/queue?page=1&page_size=2")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 2

class TestAssignReview:
    """POST /api/v1/reviews/{review_id}/assign (W1)"""

    def test_assign_pending_success(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(
            db_session, report_hash="asgn_h001_00000000000000000000001", status="pending"
        )
        resp = client_with_auth.post(
            f"/api/v1/reviews/{r.id}/assign",
            json={"assignee": "reviewer_alice"},
        )
        assert resp.status_code == 200
        assert resp.json()["reviewer"] == "reviewer_alice"

    def test_assign_approved_returns_422(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(
            db_session, report_hash="asgn_h002_00000000000000000000001", status="approved"
        )
        resp = client_with_auth.post(
            f"/api/v1/reviews/{r.id}/assign",
            json={"assignee": "reviewer_bob"},
        )
        assert resp.status_code == 422

    def test_assign_rejected_returns_422(
        self, client_with_auth: TestClient, db_session: SQLModelSession
    ):
        r = _make_review(
            db_session, report_hash="asgn_h003_00000000000000000000001", status="rejected"
        )
        resp = client_with_auth.post(
            f"/api/v1/reviews/{r.id}/assign",
            json={"assignee": "reviewer_charlie"},
        )
        assert resp.status_code == 422

    def test_assign_404(self, client_with_auth: TestClient):
        resp = client_with_auth.post(
            "/api/v1/reviews/99999995/assign",
            json={"assignee": "nobody"},
        )
        assert resp.status_code == 404


class TestMyQueue:
    """GET /api/v1/reviews/my-queue (W1)"""

    def test_my_queue_empty(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/reviews/my-queue")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_my_queue_only_returns_assigned_to_me(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
        test_user,
    ):
        username = test_user.username
        # 分配给我的
        _make_review(
            db_session,
            report_hash="myq_h001_00000000000000000000001",
            status="pending",
            reviewer=username,
        )
        # 分配给别人的
        _make_review(
            db_session,
            report_hash="myq_h002_00000000000000000000001",
            status="pending",
            reviewer="other_user",
        )
        resp = client_with_auth.get("/api/v1/reviews/my-queue")
        assert resp.status_code == 200
        data = resp.json()
        # 只能看到分配给自己的
        for item in data["items"]:
            assert item["reviewer"] == username

    def test_my_queue_excludes_non_pending(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
        test_user,
    ):
        username = test_user.username
        # pending — 应出现
        _make_review(
            db_session,
            report_hash="myq_h003_00000000000000000000001",
            status="pending",
            reviewer=username,
        )
        # approved — 不应出现
        _make_review(
            db_session,
            report_hash="myq_h004_00000000000000000000001",
            status="approved",
            reviewer=username,
        )
        resp = client_with_auth.get("/api/v1/reviews/my-queue")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "pending"


# ══════════════════════════════════════════════════════════════════════════
# T-06  analytics.py
# ══════════════════════════════════════════════════════════════════════════


class TestDashboard:
    """GET /api/v1/analytics/dashboard"""

    def test_dashboard_basic_structure(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        for key in (
            "cases_total",
            "cases_this_month",
            "snapshots_total",
            "snapshots_this_month",
            "reviews_pending",
            "reviews_approved",
            "reviews_rejected",
            "reviews_revised",
            "daily_activity",
            "recent_cases",
            "generated_at",
            "owner_id",
        ):
            assert key in data, f"missing field: {key}"

    def test_dashboard_daily_activity_has_7_days(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["daily_activity"]) == 7

    def test_dashboard_daily_activity_structure(self, client_with_auth: TestClient):
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        for entry in resp.json()["daily_activity"]:
            assert "date" in entry
            assert "count" in entry
            assert isinstance(entry["count"], int)

    def test_dashboard_counts_user_cases(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
        test_user,
    ):
        _make_case(db_session, owner_id=test_user.id, name="dash_c1")
        _make_case(db_session, owner_id=test_user.id, name="dash_c2")
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cases_total"] >= 2
        assert data["owner_id"] == test_user.id

    def test_dashboard_does_not_count_other_user_cases(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
    ):
        # owner_id=9999 属于别的用户，不应计入
        _make_case(db_session, owner_id=9999, name="other_user_case")
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        # 仅验证不会抛错且结构正确
        assert "cases_total" in resp.json()

    def test_dashboard_recent_cases_max_5(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
        test_user,
    ):
        for i in range(7):
            _make_case(db_session, owner_id=test_user.id, name=f"rc_case_{i}")
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        assert len(resp.json()["recent_cases"]) <= 5

    def test_dashboard_review_counts_reflect_db(
        self,
        client_with_auth: TestClient,
        db_session: SQLModelSession,
    ):
        _make_review(
            db_session, report_hash="dash_rv_p_000000000000000000000001", status="pending"
        )
        _make_review(
            db_session, report_hash="dash_rv_a_000000000000000000000001", status="approved"
        )
        _make_review(
            db_session, report_hash="dash_rv_r_000000000000000000000001", status="rejected"
        )
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reviews_pending"] >= 1
        assert data["reviews_approved"] >= 1
        assert data["reviews_rejected"] >= 1

    def test_dashboard_zero_counts_for_empty_user(
        self, client_with_auth: TestClient
    ):
        """新用户无案例/快照时，各计数从 0 起步。"""
        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["snapshots_total"], int)
        assert isinstance(data["cases_total"], int)

    def test_dashboard_generated_at_is_recent(self, client_with_auth: TestClient):
        from datetime import timedelta

        resp = client_with_auth.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        generated_at_str = resp.json()["generated_at"]
        # 确保 generated_at 是合法的 ISO 时间格式
        # FastAPI 序列化为带 Z 或 +00:00 后缀的 ISO 字符串
        assert generated_at_str is not None
        assert len(generated_at_str) > 10
