# -*- coding: utf-8 -*-
"""Unit tests for Scheduler Engine and REST API."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from server.app import app
from server.scheduler import scheduler_engine

client = TestClient(app)


def test_scheduler_engine_crud():
    # Test Create
    job_data = {
        "name": "Test Schedule Morning",
        "schedule_type": "us_preset",
        "preset_name": "us_morning",
        "timezone_mode": "US_EST",
        "loop_count": 2,
        "profile_ids": ["profile_1"],
        "enabled": True,
    }
    job = scheduler_engine.create(job_data)
    assert job["id"] in scheduler_engine.jobs
    assert job["name"] == "Test Schedule Morning"
    assert "EST" in job["next_run"]

    jid = job["id"]

    # Test Toggle
    updated = scheduler_engine.toggle(jid)
    assert updated["enabled"] is False

    updated2 = scheduler_engine.toggle(jid)
    assert updated2["enabled"] is True

    # Test Run Now
    run_res = scheduler_engine.run_now(jid)
    assert run_res is True

    # Test Delete
    del_res = scheduler_engine.delete(jid)
    assert del_res is True
    assert jid not in scheduler_engine.jobs
    print("✅ Scheduler Engine CRUD PASS")


def test_scheduler_api_endpoints():
    # GET /api/schedules
    res = client.get("/api/schedules")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # POST /api/schedules
    payload = {
        "name": "API Test Job",
        "schedule_type": "interval",
        "interval_minutes": 30,
        "timezone_mode": "LOCAL",
        "loop_count": 1,
        "enabled": True,
    }
    create_res = client.post("/api/schedules", json=payload)
    assert create_res.status_code == 200
    created_job = create_res.json()
    jid = created_job["id"]
    assert created_job["name"] == "API Test Job"

    # PUT /api/schedules/{id}/toggle
    tog_res = client.put(f"/api/schedules/{jid}/toggle")
    assert tog_res.status_code == 200
    assert tog_res.json()["enabled"] is False

    # POST /api/schedules/{id}/run-now
    run_res = client.post(f"/api/schedules/{jid}/run-now")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "triggered"

    # DELETE /api/schedules/{id}
    del_res = client.delete(f"/api/schedules/{jid}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
    print("✅ Scheduler API Endpoints PASS")


def test_system_stats_endpoint():
    res = client.get("/api/system/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_finance_viewed" in data
    assert "total_shorts_watched" in data
    assert "active_schedules_count" in data
    print("✅ Enriched System Stats PASS")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("🧪  TEST SCHEDULER ENGINE & API")
    print("=" * 55)
    test_scheduler_engine_crud()
    test_scheduler_api_endpoints()
    test_system_stats_endpoint()
    print("=" * 55)
    print("🎉 ALL SCHEDULER TESTS PASSED!")
    print("=" * 55)
