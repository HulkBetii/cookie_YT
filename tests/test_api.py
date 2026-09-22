# -*- coding: utf-8 -*-
"""Test API endpoints of FastAPI Control Server."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "healthy"
    print("✅ Health check PASS:", data)


def test_api_system_stats():
    resp = client.get("/api/system/stats")
    assert resp.status_code == 200, f"Stats check failed: {resp.text}"
    data = resp.json()
    assert "us_time_est" in data
    assert "circadian_mode" in data
    print("✅ System stats PASS:", data)


def test_api_profiles():
    resp = client.get("/api/profiles")
    assert resp.status_code == 200, f"Profiles check failed: {resp.text}"
    data = resp.json()
    assert isinstance(data, list)
    print(f"✅ Profiles list PASS: {len(data)} profiles found")


def test_api_config():
    resp = client.get("/api/config")
    assert resp.status_code == 200, f"Config check failed: {resp.text}"
    data = resp.json()
    assert "GPM_API_URL" in data
    assert len(data["DANH_SACH_TU_KHOA"]) > 0
    print("✅ Config GET PASS")


def test_static_spa():
    resp = client.get("/")
    assert resp.status_code == 200, f"Static SPA failed: {resp.status_code}"
    assert "YouTube Farm Pro" in resp.text
    print("✅ Static SPA index.html served PASS")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("🧪 TESTING FASTAPI DASHBOARD SERVER")
    print("=" * 55)
    test_api_health()
    test_api_system_stats()
    test_api_profiles()
    test_api_config()
    test_static_spa()
    print("=" * 55)
    print("🎉 ALL API ENDPOINTS PASSED 100%!")
    print("=" * 55)
