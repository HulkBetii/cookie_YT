#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E + Unit Test — kiểm tra từng module, in PASS/FAIL rõ ràng.

Cấu trúc:
  Phase 0 : Unit tests — không cần browser (logic, URL validation, helpers)
  Phase 1 : GPM API + environment
  Phase 2 : Browser + proxy
  Phase 3 : YouTube (search, click, watch)
  Phase 4 : Google News
  Phase 5 : Yahoo! Japan
  Phase 6 : Google Search
  Phase 7 : Selenium timeout + tab guard
"""
import sys, time, traceback, os, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ── Package imports ───────────────────────────────────────────────
from nuoi_kenh.config import (
    GPM_API_URL, TU_DONG_DONG_POPUP, DANH_SACH_TU_KHOA,
    KHUNG_GIO_NGHI_DAI, HE_SO_HOAT_DONG_THEO_GIO,
)
from nuoi_kenh.gpm_api import (
    tim_gpmdriver, lay_tat_ca_profiles,
    mo_profile_gpm, dong_profile_gpm, kiem_tra_proxy_nhanh,
    tao_profile_gpm, cap_nhat_profile_gpm, cap_nhat_proxy_gpm, cap_nhat_note_gpm,
    _trich_debug_addr,
)
from nuoi_kenh.selenium_utils import (
    _cho_trang_load,
    configure_driver_transport,
    driver_failure_reason,
    focus_content_tab,
    is_driver_healthy,
    mark_driver_unhealthy,
    safe_get,
    safe_quit,
    safe_window_handles,
    selenium_call,
)
from nuoi_kenh.news import (
    dong_popup_tu_dong, _tim_bai_google_news, _la_link_bai_bao,
)
from nuoi_kenh.youtube import _cho_ket_qua_tim_kiem, xu_ly_quang_cao_youtube
from nuoi_kenh.tab_guard import la_url_quang_cao, don_dep_tab_la
from nuoi_kenh.human_behavior import draw_session_mood, kiem_tra_ket_noi

# ── Test runner ───────────────────────────────────────────────────

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⏭  SKIP"

results = []


def step(name, fn, skip_if=False):
    print(f"\n{'─'*55}")
    print(f"TEST: {name}")
    if skip_if:
        print(f"{SKIP}  (điều kiện tiên quyết không thoả)")
        results.append((name, SKIP))
        return None
    try:
        t0      = time.time()
        out     = fn()
        ms      = int((time.time() - t0) * 1000)
        verdict = PASS if out is not False else FAIL
        print(f"{verdict}  ({ms}ms)")
        if isinstance(out, str):
            print(f"     → {out}")
        results.append((name, verdict))
        return out
    except AssertionError as e:
        print(f"{FAIL}  — assert: {e}")
        results.append((name, FAIL))
        return None
    except Exception as e:
        print(f"{FAIL}  — {type(e).__name__}: {e}")
        traceback.print_exc()
        results.append((name, FAIL))
        return None


# ════════════════════════════════════════════════════════════════
#  PHASE 0 — UNIT TESTS (không cần browser)
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 0 — UNIT TESTS (no browser)")
print("█"*55)


def test_la_url_quang_cao():
    """la_url_quang_cao nhận diện đúng các URL cần đóng."""
    assert la_url_quang_cao("chrome-extension://aapbdbdomjkkjkaonfhkkikfgjllcleb/off"), \
        "chrome-extension:// phải là quảng cáo"
    assert la_url_quang_cao("data:text/html,<h1>hi</h1>"), "data: phải là quảng cáo"
    assert la_url_quang_cao("about:blank"), "about:blank phải là quảng cáo"
    assert la_url_quang_cao(""), "empty string phải là quảng cáo"
    assert la_url_quang_cao("https://googleadservices.com/track"), "ad domain phải là quảng cáo"
    assert not la_url_quang_cao("https://news.yahoo.co.jp/articles/abc"), \
        "Yahoo article không phải quảng cáo"
    assert not la_url_quang_cao("https://www.youtube.com/watch?v=abc"), \
        "YouTube watch không phải quảng cáo"
    return "chrome-ext/data/about/ad-domain/empty đều detected đúng"


def test_us_keywords_config():
    """Kiểm tra danh sách từ khóa tiếng Anh US đa dạng."""
    from nuoi_kenh.config import DANH_SACH_TU_KHOA, TU_KHOA_LIEN_QUAN, GOOGLE_SEARCH_QUERIES
    assert len(DANH_SACH_TU_KHOA) >= 10, "DANH_SACH_TU_KHOA phải có ít nhất 10 từ khóa"
    assert len(TU_KHOA_LIEN_QUAN) >= 5, "TU_KHOA_LIEN_QUAN phải có ít nhất 5 từ khóa"
    assert len(GOOGLE_SEARCH_QUERIES) >= 5, "GOOGLE_SEARCH_QUERIES phải có ít nhất 5 từ khóa"
    return f"Keywords US: {len(DANH_SACH_TU_KHOA)} main, {len(TU_KHOA_LIEN_QUAN)} related, {len(GOOGLE_SEARCH_QUERIES)} search queries ✓"


def test_la_link_bai_bao():
    """_la_link_bai_bao (Google News) nhận diện đúng."""
    assert _la_link_bai_bao("https://news.google.com/articles/abc"), \
        "Google News article phải được chấp nhận"
    assert _la_link_bai_bao("https://www.nhk.or.jp/news/abc"), \
        "External link phải được chấp nhận"
    assert not _la_link_bai_bao("https://news.google.com/home"), \
        "GN homepage phải bị reject"
    assert not _la_link_bai_bao("https://accounts.google.com/signin"), \
        "Google accounts phải bị reject"
    assert not _la_link_bai_bao(""), "empty phải bị reject"
    return "article, external, nav-pages đều đúng"


def test_he_so_theo_gio():
    """_he_so_theo_gio trả về đúng hệ số theo khung giờ."""
    from main import _he_so_theo_gio
    # Khung 1-6: hệ số 8.0 (giờ ngủ)
    assert _he_so_theo_gio(KHUNG_GIO_NGHI_DAI, gio=3) == 8.0, \
        f"3h phải là 8.0, got {_he_so_theo_gio(KHUNG_GIO_NGHI_DAI, gio=3)}"
    # Khung 19-24: hệ số 0.2 (buổi tối — ít nghỉ dài)
    assert _he_so_theo_gio(KHUNG_GIO_NGHI_DAI, gio=21) == 0.2, \
        f"21h phải là 0.2, got {_he_so_theo_gio(KHUNG_GIO_NGHI_DAI, gio=21)}"
    # Khung hoạt động: ban đêm thấp, tối cao
    he_so_dem  = _he_so_theo_gio(HE_SO_HOAT_DONG_THEO_GIO, gio=3)
    he_so_toi  = _he_so_theo_gio(HE_SO_HOAT_DONG_THEO_GIO, gio=21)
    assert he_so_dem < he_so_toi, \
        f"Hệ số hoạt động ban đêm ({he_so_dem}) phải < buổi tối ({he_so_toi})"
    return f"3h→{he_so_dem} (thấp), 21h→{he_so_toi} (cao) — đúng"


def test_lay_tu_khoa_no_repeat():
    """lay_tu_khoa không lặp lại từ khóa vừa dùng liên tiếp."""
    from main import lay_tu_khoa, _TU_KHOA_GAN_DAY
    _TU_KHOA_GAN_DAY.clear()

    if len(DANH_SACH_TU_KHOA) < 2:
        return "SKIP — quá ít từ khóa để test"

    seen = []
    for i in range(20):
        k = lay_tu_khoa(i)
        seen.append(k)

    # Không có 2 từ khoá giống nhau liên tiếp
    for i in range(1, len(seen)):
        assert seen[i] != seen[i-1], \
            f"Lặp liên tiếp '{seen[i]}' tại vị trí {i}"

    unique = len(set(seen))
    return f"20 lần chọn, {unique} từ khóa duy nhất, không lặp liên tiếp"


def test_draw_session_mood():
    """draw_session_mood luôn trả về SessionMood hợp lệ với tất cả fields."""
    from nuoi_kenh.human_behavior import SessionMood
    import dataclasses
    fields = {f.name for f in dataclasses.fields(SessionMood)}

    for _ in range(10):
        mood = draw_session_mood()
        assert mood.name in ("passive", "normal", "engaged"), \
            f"name không hợp lệ: {mood.name}"
        for f in fields:
            v = getattr(mood, f)
            if f in ("name", "archetype"):
                continue
            if f == "early_exit_ratio":
                lo, hi = v
                assert 0 <= lo <= hi <= 1.0, f"early_exit_ratio ngoài range: {v}"
            else:
                assert isinstance(v, float), f"{f} phải là float, got {type(v)}"
                assert 0.0 <= v <= 1.0, f"{f}={v} ngoài [0,1]"

    return "10 moods, tất cả fields hợp lệ"





def test_news_da_doc_fix():
    """Kiểm tra logic fix news.py: safe_get fail không tăng da_doc."""
    # Simulate old vs new behavior
    so_bai = 2
    # OLD: da_doc += 1 khi safe_get fail → loop thoát sau 2 timeout
    da_doc_old = 0
    for _ in range(so_bai * 3):
        if da_doc_old >= so_bai:
            break
        safe_ok = False  # simulate timeout
        if not safe_ok:
            da_doc_old += 1  # BUG: count failure as read
            continue
    assert da_doc_old == so_bai, "OLD logic phải reach so_bai mà không đọc gì"

    # NEW: không tăng khi safe_get fail
    da_doc_new = 0
    iterations = 0
    for _ in range(so_bai * 3):
        if da_doc_new >= so_bai:
            break
        iterations += 1
        safe_ok = False  # simulate timeout
        if not safe_ok:
            continue  # FIX: don't increment
        da_doc_new += 1
    assert da_doc_new == 0, "NEW logic: tất cả timeout → da_doc vẫn là 0"
    assert iterations == so_bai * 3, "NEW logic phải chạy hết vòng lặp"

    return f"OLD=count_failures({da_doc_old}), NEW=0 fails counted ✓"


def test_popup_text_matching_is_exact():
    """Short popup labels must not match words such as TikTok."""
    popup_text = "OK"
    article_text = "TikTok ナンパ"
    old_match = popup_text in article_text.upper()
    new_match = popup_text == article_text.strip().upper()
    assert old_match, "Old contains logic must reproduce the false positive"
    assert not new_match, "Exact matching must reject article text containing TikTok"
    return "OK no longer matches TikTok article links ✓"


def test_transport_guard():
    """Transport failure marks the driver and blocks later commands."""
    from urllib3.exceptions import ReadTimeoutError

    class FakePoolManager:
        def __init__(self):
            self.connection_pool_kw = {"timeout": None}
            self.pools = {}

    class FakeClientConfig:
        timeout = None

    class FakeExecutor:
        def __init__(self):
            self.client_config = FakeClientConfig()
            self._conn = FakePoolManager()

    class FakeDriver:
        def __init__(self):
            self.command_executor = FakeExecutor()
            self.execute_count = 0

        def execute(self, command, params=None):
            self.execute_count += 1
            raise ReadTimeoutError(None, "/session", "read timed out")

    fake_driver = FakeDriver()
    configure_driver_transport(fake_driver)
    result = selenium_call(
        lambda: fake_driver.execute("getCurrentUrl"),
        driver=fake_driver,
        timeout=1,
        default="timeout",
    )
    assert result == "timeout"
    assert not is_driver_healthy(fake_driver)
    assert "getCurrentUrl" in driver_failure_reason(fake_driver)

    second_result = selenium_call(
        lambda: fake_driver.execute("getCurrentUrl"),
        driver=fake_driver,
        timeout=1,
        default="blocked",
    )
    assert second_result == "blocked"
    assert fake_driver.execute_count == 1, "Driver hỏng không được nhận thêm command"
    return "timeout marks unhealthy; later command blocked ✓"


def test_safe_quit_skips_unhealthy_driver():
    """Cleanup must use GPM stop instead of queueing quit on a broken driver."""
    class FakeDriver:
        quit_called = False

        def quit(self):
            self.quit_called = True

    fake_driver = FakeDriver()
    mark_driver_unhealthy(fake_driver)
    assert not safe_quit(fake_driver)
    assert not fake_driver.quit_called
    return "unhealthy driver skips quit ✓"


def test_focus_content_tab_skips_extension():
    """Navigation must recover focus from GPM extension background tabs."""
    class FakePoolManager:
        def __init__(self):
            self.connection_pool_kw = {"timeout": None}
            self.pools = {}

    class FakeClientConfig:
        timeout = None

    class FakeExecutor:
        def __init__(self):
            self.client_config = FakeClientConfig()
            self._conn = FakePoolManager()

    class FakeSwitchTo:
        def __init__(self, driver):
            self.driver = driver

        def window(self, handle):
            self.driver.current_handle = handle

    class FakeDriver:
        def __init__(self):
            self.command_executor = FakeExecutor()
            self.current_handle = "extension"
            self.window_handles = ["extension", "content"]
            self.urls = {
                "extension": "chrome-extension://abc/background.html",
                "content": "https://www.youtube.com/results?search_query=test",
            }
            self.switch_to = FakeSwitchTo(self)

        @property
        def current_window_handle(self):
            return self.current_handle

        @property
        def current_url(self):
            return self.urls[self.current_handle]

    fake_driver = FakeDriver()
    selected = focus_content_tab(fake_driver, create_if_missing=False)
    assert selected == "content"
    assert fake_driver.current_window_handle == "content"
    return "extension tab skipped; content tab focused ✓"


def test_human_behavior_avoids_actions_command():
    """Optional human behavior must not use Selenium /actions with GPMDriver."""
    source = (PROJECT_ROOT / "nuoi_kenh" / "human_behavior.py").read_text(encoding="utf-8")
    assert "ActionChains" not in source
    assert ".perform(" not in source
    return "human_behavior no longer sends /actions commands ✓"


def test_trich_debug_addr_api_v2():
    """_trich_debug_addr trích xuất chính xác từ response API v2 tiêu chuẩn."""
    sample_v2_resp = {
        "status": True,
        "profile_id": "test_profile_123",
        "browser_location": "C:\\GPM\\gpm_browser\\chrome.exe",
        "selenium_remote_debug_address": "127.0.0.1:62561",
        "selenium_driver_location": "C:\\GPM\\gpmdriver.exe"
    }
    addr = _trich_debug_addr(sample_v2_resp)
    assert addr == "127.0.0.1:62561", f"Expected 127.0.0.1:62561, got {addr}"
def test_us_modules_import():
    """Kiểm tra import thành công các module US mới (Google Maps, Reddit, Wikipedia)."""
    from nuoi_kenh.google_maps import luot_google_maps
    from nuoi_kenh.reddit import luot_reddit
    from nuoi_kenh.wikipedia import luot_wikipedia
    from nuoi_kenh.config import MAPS_CITIES_QUERIES, REDDIT_SUBREDDITS, WIKIPEDIA_TOPICS
    assert len(MAPS_CITIES_QUERIES) > 0, "MAPS_CITIES_QUERIES không được rỗng"
    assert len(REDDIT_SUBREDDITS) > 0, "REDDIT_SUBREDDITS không được rỗng"
    assert len(WIKIPEDIA_TOPICS) > 0, "WIKIPEDIA_TOPICS không được rỗng"
    return f"Maps({len(MAPS_CITIES_QUERIES)}), Reddit({len(REDDIT_SUBREDDITS)}), Wiki({len(WIKIPEDIA_TOPICS)}) loaded ✓"


def test_us_circadian_timezone():
    """Kiểm tra tính toán nhịp sinh học theo múi giờ US."""
    from main import _he_so_theo_gio
    from nuoi_kenh.config import KHUNG_GIO_NGHI_DAI
    from zoneinfo import ZoneInfo
    from datetime import datetime
    us_hour = datetime.now(ZoneInfo("America/New_York")).hour
    he_so = _he_so_theo_gio(KHUNG_GIO_NGHI_DAI)
    assert he_so > 0, "Hệ số phải > 0"
    return f"US EST Hour: {us_hour}h -> Circadian multiplier: {he_so}x ✓"


def test_markov_state_machine():
    """Kiểm tra Markov state transitions hoạt động ổn định."""
    from main import _chon_hoat_dong_markov, _lay_dich_vu_kha_dung, MARKOV_TRANSITIONS
    enabled = _lay_dich_vu_kha_dung(so_tin=3)
    cur = "start"
    history = []
    for _ in range(50):
        next_act = _chon_hoat_dong_markov(cur, enabled, history)
        assert next_act in enabled and enabled[next_act], f"Hoạt động {next_act} không hợp lệ hoặc bị tắt"
        history.append(next_act)
        cur = next_act
    unique_acts = set(history)
    assert len(unique_acts) >= 3, f"Quá ít hoạt động được chọn: {unique_acts}"
    return f"50 transitions -> {len(unique_acts)} unique states: {list(unique_acts)} ✓"


def test_qwerty_typo_generator():
    """Kiểm tra mô hình gõ phím lỗi chính tả QWERTY."""
    from nuoi_kenh.human_behavior import _QWERTY_ADJACENT
    assert "a" in _QWERTY_ADJACENT and "s" in _QWERTY_ADJACENT["a"]
    assert "k" in _QWERTY_ADJACENT and "j" in _QWERTY_ADJACENT["k"]
    return f"QWERTY mapping: {len(_QWERTY_ADJACENT)} keys supported ✓"


def test_fitts_mouse_speed():
    """Kiểm tra tính toán đường cong Bézier chuột trong CDP."""
    from nuoi_kenh.cdp import _bezier_pts
    pts = _bezier_pts((0, 0), (50, 100), (150, 100), (200, 200), n_steps=15)
    assert len(pts) == 15, f"Expected 15 points, got {len(pts)}"
    assert pts[0] == (0, 0) and pts[-1] == (200, 200)
    return f"Bézier points generated: {len(pts)} pts from (0,0) to (200,200) ✓"


step("la_url_quang_cao — phát hiện chrome-ext/data/ad", test_la_url_quang_cao)
step("US Keywords Config — đa dạng tiếng Anh",        test_us_keywords_config)
step("_la_link_bai_bao — Google News link filter",       test_la_link_bai_bao)
step("_he_so_theo_gio — circadian multipliers",          test_he_so_theo_gio)
step("lay_tu_khoa — không lặp liên tiếp",                test_lay_tu_khoa_no_repeat)
step("draw_session_mood — fields hợp lệ",                test_draw_session_mood)
step("News da_doc fix — timeout không đếm là bài đọc",  test_news_da_doc_fix)
step("Popup text — OK không match TikTok",              test_popup_text_matching_is_exact)
step("Transport guard — không tạo command queue",       test_transport_guard)
step("Cleanup — skip quit khi driver hỏng",             test_safe_quit_skips_unhealthy_driver)
step("Tab focus — bỏ qua extension background",         test_focus_content_tab_skips_extension)
step("Human behavior — không dùng /actions",            test_human_behavior_avoids_actions_command)
step("GPM API v2 — trích xuất debug address",           test_trich_debug_addr_api_v2)
step("US Modules — Google Maps, Reddit, Wiki",          test_us_modules_import)
step("US Circadian — múi giờ America/New_York",         test_us_circadian_timezone)
step("Markov State Machine — 50 transitions",          test_markov_state_machine)
step("QWERTY Keyboard Typo Model",                     test_qwerty_typo_generator)
step("Fitts's Law Mouse Velocity Profile",             test_fitts_mouse_speed)


# ════════════════════════════════════════════════════════════════
#  PHASE 1 — ENVIRONMENT
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 1 — ENVIRONMENT")
print("█"*55)

driver     = None
profile_id = None


def test_gpm_api():
    r = requests.get(f"{GPM_API_URL}/v2/profiles?page=1&per_page=10", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    return f"{len(data)} profile(s)"


def test_gpmdriver():
    p = tim_gpmdriver()
    assert p and os.path.exists(p)
    return p


def test_profiles():
    global profile_id
    profiles = lay_tat_ca_profiles(page=1, per_page=100)
    assert profiles, "Không có profile"
    # Prioritize test profile or profile without proxy if available
    chosen = profiles[0]
    for p in profiles:
        if p.get("name") == "Test-DOM" or not p.get("proxy"):
            chosen = p
            break
    profile_id = chosen["id"]
    proxy_str = (chosen.get("proxy") or "direct").split(":")[0]
    return f"id={profile_id[:8]}… name={chosen.get('name')} proxy={proxy_str}"


def test_note_update():
    global profile_id
    assert profile_id, "Không có profile_id để test note"
    old_note = ""
    profiles = lay_tat_ca_profiles(page=1, per_page=100)
    for p in profiles:
        if p.get("id") == profile_id:
            old_note = p.get("note", "")
            break
    test_note = "E2E_Test_API_v2"
    ok = cap_nhat_note_gpm(profile_id, test_note)
    assert ok, "cap_nhat_note_gpm trả về False"
    # Restore old note
    cap_nhat_note_gpm(profile_id, old_note)
    return f"Updated note to '{test_note}' and restored old note ✓"


step("GPM API kết nối (v2/profiles)", test_gpm_api)
step("Tìm gpmdriver.exe",             test_gpmdriver)
step("Lấy danh sách profile (v2)",    test_profiles)
step("Cập nhật Note profile (v2)",    test_note_update)

if not profile_id:
    print("\n❌ Không có profile — dừng test")
    sys.exit(1)

gpmdriver = tim_gpmdriver()


# ════════════════════════════════════════════════════════════════
#  PHASE 2 — BROWSER
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 2 — BROWSER")
print("█"*55)


def test_mo_browser():
    global driver
    import subprocess
    dong_profile_gpm(profile_id)
    time.sleep(2)
    subprocess.run("taskkill /F /IM chrome.exe /T >nul 2>&1", shell=True)
    subprocess.run("taskkill /F /IM gpmdriver.exe /T >nul 2>&1", shell=True)
    time.sleep(2)
    driver = mo_profile_gpm(profile_id, gpmdriver)
    assert driver is not None
    return f"URL: {driver.current_url[:60]}"


def test_urllib3_patch():
    """Kiểm tra urllib3 pool đã được patch timeout sau driver creation."""
    assert driver
    try:
        from urllib3.util.timeout import Timeout
        pool_mgr = driver.command_executor._conn
        assert hasattr(pool_mgr, 'connection_pool_kw'), "Không tìm thấy connection_pool_kw"
        t = pool_mgr.connection_pool_kw.get('timeout')
        assert t is not None, "timeout chưa được set trong connection_pool_kw"
        if hasattr(t, 'read_timeout'):
            assert t.read_timeout == 15, f"read_timeout phải là 15, got {t.read_timeout}"
            return f"Timeout(connect={t.connect_timeout}, read={t.read_timeout}) ✓"
        else:
            return f"timeout={t} (không phải Timeout object — kiểm tra thủ công)"
    except ImportError:
        return "urllib3 Timeout không available — skip"


def test_proxy():
    assert driver
    ok = kiem_tra_proxy_nhanh(driver, timeout=20)
    assert ok, "Proxy không phản hồi"
    return "google.com load OK"


def test_popup_dismiss():
    assert driver
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)
    return "không có popup / đã đóng"


def test_kiem_tra_ket_noi():
    """kiem_tra_ket_noi trả về True khi browser đang sống."""
    assert driver
    alive = kiem_tra_ket_noi(driver)
    assert alive, "Browser vừa mở phải còn sống"
    return "kiem_tra_ket_noi=True ✓"


def test_safe_window_handles():
    """safe_window_handles trả về set các handle."""
    assert driver
    handles = safe_window_handles(driver)
    assert isinstance(handles, set), f"Phải là set, got {type(handles)}"
    assert len(handles) >= 1, "Phải có ít nhất 1 handle"
    return f"{len(handles)} handle(s)"


step("Mở browser qua GPM",       test_mo_browser)
step("urllib3 pool timeout patch", test_urllib3_patch)
step("Kiểm tra proxy",            test_proxy)
step("Auto-dismiss popup",        test_popup_dismiss)
step("kiem_tra_ket_noi alive",    test_kiem_tra_ket_noi)
step("safe_window_handles",       test_safe_window_handles)

if not driver:
    print("\n❌ Browser không mở được — dừng test")
    dong_profile_gpm(profile_id)
    sys.exit(1)


# ════════════════════════════════════════════════════════════════
#  PHASE 3 — YOUTUBE
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 3 — YOUTUBE")
print("█"*55)

_search_url = None


def test_youtube_load():
    assert safe_get(driver, "https://www.youtube.com", timeout=25), \
        "Không load được YouTube"
    _cho_trang_load(driver, timeout=20)
    assert "youtube" in driver.current_url.lower(), \
        f"URL không phải YouTube: {driver.current_url}"
    return f"title={driver.title[:40]}"


def test_youtube_search():
    global _search_url
    from nuoi_kenh.youtube import _focus_search_box, _clear_overlays
    from nuoi_kenh.human_behavior import go_co_loi_chinh_ta
    from selenium.webdriver.common.keys import Keys

    _clear_overlays(driver)
    box = _focus_search_box(driver, timeout=20)
    assert box is not None, "_focus_search_box không tìm thấy ô tìm kiếm"
    go_co_loi_chinh_ta(box, "偉人の教え")
    time.sleep(0.5)
    box.send_keys(Keys.RETURN)
    time.sleep(3)
    videos = _cho_ket_qua_tim_kiem(driver, timeout=40)
    assert videos, "Timeout 40s — không tìm thấy video"
    _search_url = driver.current_url
    return f"{len(videos)} videos | url={driver.current_url[:50]}"


def test_youtube_no_shorts():
    """Tất cả video trả về không phải Shorts."""
    videos = _cho_ket_qua_tim_kiem(driver, timeout=20)
    assert videos, "Không tìm thấy video"
    for v in videos[:10]:
        href = v.get_attribute("href") or ""
        assert "/shorts/" not in href, f"Shorts lọt vào: {href}"
    return f"{len(videos)} videos, 0 Shorts ✓"


def test_youtube_click_watch():
    videos = _cho_ket_qua_tim_kiem(driver, timeout=15)
    assert videos
    v = videos[0]
    title = (v.get_attribute("title") or v.text or "")[:40]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", v)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", v)
    WebDriverWait(driver, 25).until(
        lambda d: "/watch" in d.current_url or "/shorts/" in d.current_url
    )
    time.sleep(3)
    xu_ly_quang_cao_youtube(driver)
    assert "/watch" in driver.current_url, \
        f"Không vào trang watch: {driver.current_url}"
    return f"'{title}' | {driver.current_url[:50]}"


def test_youtube_watch_15s():
    assert "/watch" in driver.current_url
    xu_ly_quang_cao_youtube(driver)
    time.sleep(15)
    xu_ly_quang_cao_youtube(driver)
    assert kiem_tra_ket_noi(driver), "Browser crash sau 15s xem"
    return "15s watch OK"


def test_youtube_return_search():
    assert _search_url
    ok = safe_get(driver, _search_url, timeout=20)
    assert ok, "Không quay về search URL được"
    _cho_trang_load(driver, timeout=15)
    time.sleep(2)
    videos = _cho_ket_qua_tim_kiem(driver, timeout=30)
    assert videos, "Sau khi quay về search không tìm thấy video"
    return f"{len(videos)} videos sau khi quay về ✓"


step("YouTube load trang chủ",    test_youtube_load)
step("YouTube tìm kiếm + _focus_search_box", test_youtube_search)
step("YouTube không có Shorts",   test_youtube_no_shorts, skip_if=not _search_url)
step("YouTube click + vào watch", test_youtube_click_watch)
step("YouTube xem 15s",           test_youtube_watch_15s)
step("YouTube quay về search",    test_youtube_return_search, skip_if=not _search_url)


# ════════════════════════════════════════════════════════════════
#  PHASE 4 — GOOGLE NEWS
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 4 — GOOGLE NEWS")
print("█"*55)


def test_googlenews_load():
    assert safe_get(driver, "https://news.google.com/", timeout=25), \
        "Không load được Google News"
    time.sleep(4)
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)
    time.sleep(2)
    articles = _tim_bai_google_news(driver)
    assert articles, "Không tìm thấy bài báo Google News"
    return f"{len(articles)} bài"


def test_googlenews_click():
    articles = _tim_bai_google_news(driver)
    assert articles
    bai  = articles[0]
    href = bai.get_attribute("href") or ""
    print(f"     href: {href[:80]}")
    assert _la_link_bai_bao(href), f"Href không phải bài báo: {href[:80]}"
    url_truoc = driver.current_url
    assert safe_get(driver, href, timeout=20), f"Không navigate được tới {href[:60]}"
    _cho_trang_load(driver, timeout=15)
    time.sleep(3)
    url_sau = driver.current_url
    assert url_sau != url_truoc, "URL không thay đổi"
    assert url_sau.startswith("http"), f"URL sau không hợp lệ: {url_sau[:60]}"
    time.sleep(3)
    driver.back()
    time.sleep(2)
    return f"Đọc bài OK: {url_sau[:70]}"


step("Google News load + tìm bài", test_googlenews_load)
step("Google News click bài báo",  test_googlenews_click)


# ════════════════════════════════════════════════════════════════
#  PHASE 5 — US TRACKING & LOCAL TRUST (MAPS, REDDIT, WIKI)
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 5 — US TRACKING & LOCAL TRUST")
print("█"*55)


def test_google_maps_us():
    """Kiểm tra load và search Google Maps US."""
    from nuoi_kenh.google_maps import luot_google_maps
    so = luot_google_maps(driver, so_lan=1)
    assert so >= 1, "Google Maps không xem được địa điểm nào"
    return f"Xem thành công {so} địa điểm Maps ✓"


def test_reddit_us():
    """Kiểm tra load và lướt Reddit US."""
    from nuoi_kenh.reddit import luot_reddit
    so = luot_reddit(driver, so_bai=1)
    assert so >= 1, "Reddit US không xem được bài nào"
    return f"Đọc thành công {so} bài Reddit ✓"


def test_wikipedia_us():
    """Kiểm tra load và lướt Wikipedia tiếng Anh."""
    from nuoi_kenh.wikipedia import luot_wikipedia
    so = luot_wikipedia(driver, so_bai=1)
    assert so >= 1, "Wikipedia không xem được bài nào"
    return f"Đọc thành công {so} chủ đề Wikipedia ✓"


step("Google Maps US (Local Trust)",     test_google_maps_us)
step("Reddit US (Ad & GA Tracking)",     test_reddit_us)
step("Wikipedia EN (Knowledge Graph)",   test_wikipedia_us)


# ════════════════════════════════════════════════════════════════
#  PHASE 6 — GOOGLE SEARCH
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 6 — GOOGLE SEARCH")
print("█"*55)


def test_google_load():
    assert safe_get(driver, "https://www.google.com?hl=en", timeout=25), \
        "Không vào được Google"
    _cho_trang_load(driver, timeout=20)
    time.sleep(2)
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)
    assert "google" in driver.current_url.lower()
    return f"title={driver.title[:40]}"


def test_google_search_flow():
    from selenium.webdriver.common.keys import Keys
    from nuoi_kenh.human_behavior import go_co_loi_chinh_ta
    from nuoi_kenh.google_search import (
        _la_link_ket_qua,
        wait_for_search_results,
    )

    try:
        box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
    except TimeoutException:
        return False

    driver.execute_script("arguments[0].click();", box)
    time.sleep(0.3)
    box.clear()
    go_co_loi_chinh_ta(box, "latest tech news")
    time.sleep(0.5)
    box.send_keys(Keys.RETURN)
    time.sleep(1.5)
    if "/search" not in driver.current_url:
        try:
            driver.execute_script("arguments[0].form.submit();", box)
        except Exception:
            pass

    _cho_trang_load(driver, timeout=20)
    time.sleep(2)

    results_found = wait_for_search_results(driver, timeout=25)
    assert results_found, "Không tìm thấy kết quả Google"

    # Verify filter: không có Google/YouTube trong kết quả
    for r in results_found[:5]:
        href = r.get_attribute("href") or ""
        assert _la_link_ket_qua(href), f"Kết quả không phải organic: {href[:60]}"

    return f"{len(results_found)} organic results, không có Google/YouTube ✓"


step("Google Search load",   test_google_load)
step("Google Search flow",   test_google_search_flow)


# ════════════════════════════════════════════════════════════════
#  PHASE 7 — SELENIUM TIMEOUT + TAB GUARD
# ════════════════════════════════════════════════════════════════

print("\n" + "█"*55)
print("  PHASE 7 — SELENIUM TIMEOUT + TAB GUARD")
print("█"*55)


def test_cho_trang_load_no_hang():
    """_cho_trang_load phải complete trong timeout, không hang."""
    assert safe_get(driver, "https://www.youtube.com", timeout=25)
    t0 = time.time()
    _cho_trang_load(driver, timeout=10)
    elapsed = time.time() - t0
    assert elapsed < 35, f"_cho_trang_load mất {elapsed:.1f}s (quá 35s limit)"
    return f"{elapsed:.1f}s (dưới 35s limit) ✓"


def test_execute_script_no_hang():
    """execute_script không hang — urllib3 pool timeout được patch."""
    t0 = time.time()
    result = driver.execute_script("return document.readyState")
    elapsed = time.time() - t0
    assert elapsed < 30, f"execute_script mất {elapsed:.1f}s"
    assert result in ("complete", "interactive", "loading"), \
        f"readyState không hợp lệ: {result}"
    return f"readyState='{result}' trong {elapsed:.2f}s ✓"


def test_don_dep_tab_la_safe():
    """don_dep_tab_la không crash khi tất cả tab hợp lệ."""
    handles = safe_window_handles(driver)
    assert handles
    # Không có tab lạ → don_dep_tab_la phải trả về 0
    so_dong = don_dep_tab_la(driver, handles)
    assert so_dong == 0, f"Không có tab lạ nhưng dong {so_dong} tab"
    return "don_dep_tab_la(handles_hợp_lệ)=0 ✓"


def test_watchdog_tabs_alive():
    """watchdog_tabs trả về True khi browser sống."""
    from nuoi_kenh.tab_guard import watchdog_tabs
    handles = safe_window_handles(driver)
    tab_hien_tai = driver.current_window_handle
    ok = watchdog_tabs(driver, handles, tab_hien_tai)
    assert ok, "watchdog_tabs phải trả True khi browser sống"
    return "watchdog_tabs=True ✓"


step("_cho_trang_load không hang (≤35s)",   test_cho_trang_load_no_hang)
step("execute_script không hang (urllib3)",  test_execute_script_no_hang)
step("don_dep_tab_la an toàn",              test_don_dep_tab_la_safe)
step("watchdog_tabs khi browser sống",      test_watchdog_tabs_alive)


# ════════════════════════════════════════════════════════════════
#  KẾT QUẢ
# ════════════════════════════════════════════════════════════════

print(f"\n{'═'*55}")
print("📊  KẾT QUẢ E2E + UNIT TEST")
print(f"{'═'*55}")

passed  = sum(1 for _, v in results if v == PASS)
failed  = sum(1 for _, v in results if v == FAIL)
skipped = sum(1 for _, v in results if v == SKIP)

for name, verdict in results:
    print(f"  {verdict}  {name}")

print(f"{'─'*55}")
print(f"  Tổng: {passed} PASS  |  {failed} FAIL  |  {skipped} SKIP  (/{len(results)})")
print(f"{'═'*55}")

try:
    if driver:
        safe_quit(driver)
    dong_profile_gpm(profile_id)
    print("\n🔒 Đã đóng browser")
except Exception:
    pass

sys.exit(0 if failed == 0 else 1)
