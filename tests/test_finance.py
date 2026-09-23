# -*- coding: utf-8 -*-
"""Unit tests for Google Finance US module."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from unittest.mock import MagicMock, patch
from nuoi_kenh.google_finance import luot_google_finance, _tuong_tac_bieu_do, _chuyen_timeframe
from nuoi_kenh.human_behavior import draw_session_mood


def test_google_finance_dry_run():
    mock_driver = MagicMock()
    mock_driver.current_url = "https://www.google.com/finance"
    mock_driver.window_handles = ["handle1"]
    mock_driver.current_window_handle = "handle1"
    mock_driver.execute_script.return_value = {"x": 100, "y": 100, "w": 400, "h": 200, "ok": True}
    mock_driver.find_elements.return_value = []

    mood = draw_session_mood()

    with patch("nuoi_kenh.google_finance.safe_get", return_value=True), \
         patch("nuoi_kenh.google_finance.time.sleep", return_value=None), \
         patch("nuoi_kenh.google_finance.cdp_click", return_value=True), \
         patch("nuoi_kenh.google_finance.bezier_mouse_move", return_value=None), \
         patch("nuoi_kenh.google_finance.cuon_tu_nhien", return_value=None), \
         patch("nuoi_kenh.google_finance.don_dep_tab_la", return_value=None), \
         patch("nuoi_kenh.google_finance.kiem_tra_ket_noi", return_value=True):
        
        result = luot_google_finance(mock_driver, so_ticker=1, mood=mood)
        assert result == 1, f"Expected 1 ticker visited, got {result}"
        print("✅ Google Finance dry run simulation PASS")


def test_google_finance_disconnected():
    mock_driver = MagicMock()
    with patch("nuoi_kenh.google_finance.kiem_tra_ket_noi", return_value=False):
        result = luot_google_finance(mock_driver, so_ticker=1)
        assert result == 0
        print("✅ Google Finance disconnected check PASS")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("🧪  TEST GOOGLE FINANCE US MODULE")
    print("=" * 55)
    test_google_finance_dry_run()
    test_google_finance_disconnected()
    print("=" * 55)
    print("🎉 ALL GOOGLE FINANCE TESTS PASSED!")
    print("=" * 55)
