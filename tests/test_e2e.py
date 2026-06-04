#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2E Test — chạy nhanh từng bước, in PASS/FAIL rõ ràng."""
import sys, time, traceback, os
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ── Imports từ package mới ───────────────────────────────────────
from nuoi_kenh.config import GPM_API_URL, GPM_BROWSER_DIR, TU_DONG_DONG_POPUP
from nuoi_kenh.gpm_api import (
    tim_gpmdriver, lay_tat_ca_profiles,
    mo_profile_gpm, dong_profile_gpm,
    _trich_debug_addr, kiem_tra_proxy_nhanh,
)
from nuoi_kenh.news import (
    dong_popup_tu_dong, _tim_bai_google_news, _la_link_bai_bao,
)
from nuoi_kenh.youtube import _cho_ket_qua_tim_kiem, xu_ly_quang_cao_youtube
from nuoi_kenh.selenium_utils import _cho_trang_load

# ════════════════════════════════════════════════════════════════

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = []


def step(name, fn):
    print(f"\n{'─'*50}")
    print(f"TEST: {name}")
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
    except Exception as e:
        print(f"{FAIL}  — {e}")
        traceback.print_exc()
        results.append((name, FAIL))
        return None


# ── Phase 1: Environment ─────────────────────────────────────────

driver     = None
profile_id = None


def test_gpm_api():
    r = requests.get(f"{GPM_API_URL}/v2/profiles?limit=1", timeout=5)
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
    profiles = lay_tat_ca_profiles()
    assert profiles, "Không có profile"
    profile_id = profiles[0]["id"]
    return f"id={profile_id[:8]}…  proxy={profiles[0].get('proxy','').split(':')[0]}"


step("GPM API kết nối",       test_gpm_api)
step("Tìm gpmdriver.exe",     test_gpmdriver)
step("Lấy danh sách profile", test_profiles)

if not profile_id:
    print("\n❌ Không có profile — dừng test")
    sys.exit(1)

gpmdriver = tim_gpmdriver()


# ── Phase 2: Browser ─────────────────────────────────────────────

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
    return f"URL hiện tại: {driver.current_url[:60]}"


def test_proxy():
    assert driver
    ok = kiem_tra_proxy_nhanh(driver, timeout=15)
    assert ok, "Proxy không phản hồi"
    return "google.com load OK"


def test_popup_dismiss():
    assert driver
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)
    return "không có popup / đã đóng"


step("Mở browser qua GPM", test_mo_browser)
step("Kiểm tra proxy",     test_proxy)
step("Auto-dismiss popup", test_popup_dismiss)

if not driver:
    print("\n❌ Browser không mở được — dừng test")
    dong_profile_gpm(profile_id)
    sys.exit(1)


# ── Phase 3: YouTube ─────────────────────────────────────────────

def test_youtube_load():
    driver.get("https://www.youtube.com")
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "search_query"))
    )
    return f"title={driver.title[:40]}"


def test_youtube_search():
    from selenium.webdriver.common.keys import Keys
    # Chờ box clickable (không chỉ present) trước khi send_keys
    box = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.NAME, "search_query"))
    )
    driver.execute_script("arguments[0].click();", box)
    time.sleep(0.4)
    box.clear()
    box.send_keys("偉人の教え")
    box.send_keys(Keys.RETURN)
    videos = _cho_ket_qua_tim_kiem(driver, timeout=40)
    assert videos, "Timeout 40s — không tìm thấy video"
    return f"{len(videos)} videos | url={driver.current_url[:50]}"


def test_youtube_find_videos():
    videos = _cho_ket_qua_tim_kiem(driver, timeout=20)
    assert videos, "Không tìm thấy video nào"
    for v in videos[:5]:
        href = v.get_attribute("href") or ""
        assert "/shorts/" not in href, f"Shorts lọt vào: {href}"
    titles = [v.get_attribute("title") or v.text for v in videos[:3]]
    return f"{len(videos)} videos | top3: {titles}"


_search_url = None


def test_youtube_click_video():
    global _search_url
    _search_url = driver.current_url
    videos = _cho_ket_qua_tim_kiem(driver, timeout=15)
    assert videos
    v     = videos[0]
    title = (v.get_attribute("title") or v.text or "")[:40]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", v)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", v)
    WebDriverWait(driver, 20).until(
        lambda d: "/watch" in d.current_url or "/shorts/" in d.current_url
    )
    time.sleep(3)
    xu_ly_quang_cao_youtube(driver)
    return f"Đang xem: {title}… | URL: {driver.current_url[:50]}"


def test_youtube_watch_short():
    assert "/watch" in driver.current_url
    xu_ly_quang_cao_youtube(driver)
    time.sleep(15)
    xu_ly_quang_cao_youtube(driver)
    assert "/watch" in driver.current_url
    return "15s xem OK, vẫn ở trang watch"


def test_youtube_return_search():
    driver.get(_search_url)
    _cho_trang_load(driver, timeout=15)
    time.sleep(2)
    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(1)
    videos = _cho_ket_qua_tim_kiem(driver, timeout=40)
    assert videos, "Sau khi quay về search không tìm thấy video"
    return f"Tìm thấy {len(videos)} video sau khi quay về"


step("YouTube load trang chủ",  test_youtube_load)
step("YouTube tìm kiếm",        test_youtube_search)
step("YouTube tìm thấy videos", test_youtube_find_videos)
step("YouTube click video",     test_youtube_click_video)
step("YouTube xem 15s",         test_youtube_watch_short)
step("YouTube quay về search",  test_youtube_return_search)


# ── Phase 4: Google News ─────────────────────────────────────────

def test_googlenews_load():
    driver.get("https://news.google.com/")
    time.sleep(4)
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)
    time.sleep(2)
    articles = _tim_bai_google_news(driver)
    assert articles, "Không tìm thấy bài báo"
    return f"Tìm thấy {len(articles)} bài"


def test_googlenews_click():
    articles = _tim_bai_google_news(driver)
    assert articles
    bai  = articles[0]
    href = bai.get_attribute("href") or ""
    print(f"     href: {href[:80]}")
    assert _la_link_bai_bao(href), f"Href không phải bài báo: {href[:80]}"
    url_truoc = driver.current_url
    driver.get(href)
    _cho_trang_load(driver, timeout=15)
    time.sleep(3)
    url_sau = driver.current_url
    assert "news.google.com/home" not in url_sau
    assert url_sau != url_truoc, "URL không thay đổi"
    time.sleep(3)
    driver.back()
    time.sleep(2)
    return f"Đọc bài OK: {url_sau[:70]}"


step("Google News load + tìm bài", test_googlenews_load)
step("Google News click bài báo",  test_googlenews_click)


# ── Kết quả ──────────────────────────────────────────────────────

print(f"\n{'═'*50}")
print("📊  KẾT QUẢ E2E TEST")
print(f"{'═'*50}")

passed = sum(1 for _, v in results if v == PASS)
failed = sum(1 for _, v in results if v == FAIL)

for name, verdict in results:
    print(f"  {verdict}  {name}")

print(f"{'─'*50}")
print(f"  Tổng: {passed}/{len(results)} PASS  |  {failed} FAIL")
print(f"{'═'*50}")

try:
    if driver:
        driver.quit()
    dong_profile_gpm(profile_id)
    print("\n🔒 Đã đóng browser")
except Exception:
    pass

sys.exit(0 if failed == 0 else 1)
