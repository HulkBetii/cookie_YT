# -*- coding: utf-8 -*-
"""YouTube — tìm kiếm, xem video, tương tác người thật."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException,
    StaleElementReferenceException, TimeoutException,
)

from .config import TU_KHOA_LIEN_QUAN
from .logger import log
from .selenium_utils import _cho_trang_load
from .human_behavior import (
    delay, nghi_ngau_nhien, kiem_tra_ket_noi,
    cuon_tu_nhien, hover_element, go_co_loi_chinh_ta,
    SessionMood,
)
from .cdp import cdp_click
from .tab_guard import don_dep_tab_la, watchdog_tabs

# ── Skip ad selectors ─────────────────────────────────────────────
_YT_SKIP_BTNS = [
    ".ytp-skip-ad-button", ".ytp-ad-skip-button",
    "button.ytp-ad-skip-button-modern", ".ytp-skip-ad-button-modern",
    ".ytp-ad-skip-button-slot button", "[class*='skip-ad'] button",
    "[class*='skipAd']", "[class*='SkipAd']", "button[id*='skip']",
]
_YT_SKIP_TEXTS = [
    "skip", "bỏ qua", "スキップ", "건너뛰기",
    "跳过", "跳過", "überspringen", "passer", "saltar",
]
_YT_BANNER_CLOSE = [
    ".ytp-ad-overlay-close-button", ".ytp-ad-overlay-close",
    ".ytp-ad-text-overlay .ytp-ad-overlay-close-button",
]


def xu_ly_quang_cao_youtube(driver) -> bool:
    """Skip/close YouTube ads. Hỗ trợ UI cũ và UI 2024+."""
    co_xu_ly = False

    for sel in _YT_SKIP_BTNS:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn.is_displayed():
                time.sleep(random.uniform(0.5, 1.5))
                driver.execute_script("arguments[0].click();", btn)
                log("    ⏭  Skip quảng cáo (selector)")
                time.sleep(random.uniform(0.5, 1.0))
                co_xu_ly = True
                break
        except Exception:
            pass

    if not co_xu_ly:
        try:
            btns = driver.find_elements(
                By.CSS_SELECTOR,
                ".html5-video-player button, #movie_player button, .ytp-chrome-bottom button"
            )
            for btn in btns:
                try:
                    txt = (btn.text or btn.get_attribute("aria-label") or "").lower().strip()
                    if any(t in txt for t in _YT_SKIP_TEXTS):
                        rect = btn.rect
                        if rect.get("width", 0) > 0:
                            time.sleep(random.uniform(0.3, 0.8))
                            driver.execute_script("arguments[0].click();", btn)
                            log(f"    ⏭  Skip quảng cáo (text: '{btn.text[:20]}')")
                            time.sleep(0.5)
                            co_xu_ly = True
                            break
                except Exception:
                    pass
        except Exception:
            pass

    if not co_xu_ly:
        for sel in _YT_BANNER_CLOSE:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    log("    ✖  Đóng banner quảng cáo")
                    time.sleep(0.5)
                    co_xu_ly = True
                    break
            except Exception:
                pass

    if not co_xu_ly:
        try:
            player = driver.find_element(By.CSS_SELECTOR, ".ad-showing")
            if player.is_displayed():
                try:
                    cd = driver.find_element(By.CSS_SELECTOR, ".ytp-ad-duration-remaining")
                    log(f"    ⏳ QC không skip, còn: {cd.text.strip()}")
                except Exception:
                    log("    ⏳ Quảng cáo không thể skip, đang chờ...")
                co_xu_ly = True
        except Exception:
            pass

    return co_xu_ly


def _cho_ket_qua_tim_kiem(driver, timeout=25) -> list:
    """Chờ kết quả search YouTube, lọc bỏ Shorts."""
    SELECTORS = [
        "ytd-video-renderer a#video-title-link",
        "a#video-title-link[href*='/watch']",
        "ytd-video-renderer h3 a",
        "ytd-rich-item-renderer a#video-title-link",
        "ytd-rich-item-renderer h3 a",
        "a.ytd-video-renderer",
    ]
    try:
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.5)
    except Exception:
        pass

    deadline = time.time() + timeout
    while time.time() < deadline:
        for sel in SELECTORS:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                valids = [
                    e for e in els
                    if e.is_displayed()
                    and "/shorts/" not in (e.get_attribute("href") or "")
                    and (e.get_attribute("title") or e.text or "").strip()
                ]
                if valids:
                    return valids[:15]
            except Exception:
                pass
        time.sleep(1.5)
    return []


def cold_start(driver, mood: SessionMood):
    """
    Warm-up trước khi bắt đầu task — giả lập hành vi ngay khi mở browser.
    Người thật không đi thẳng vào việc: họ kiểm tra notification,
    lướt lịch sử, hoặc gõ thử rồi xóa.
    """
    # Delay ngẫu nhiên ban đầu (nhìn vào màn hình trước khi làm gì)
    time.sleep(random.uniform(4, 18))

    roll = random.random()
    if roll < 0.28:
        # Hover notification bell như đang kiểm tra thông báo
        try:
            bell = driver.find_element(By.CSS_SELECTOR,
                "#notification-button, button[aria-label*='otification']")
            hover_element(driver, bell)
            delay(1.5, 4)
        except Exception:
            pass

    elif roll < 0.50:
        # Lướt lịch sử xem trước
        try:
            driver.get("https://www.youtube.com/feed/history")
            delay(3, 8)
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            driver.get("https://www.youtube.com")
            delay(2, 4)
        except Exception:
            pass

    elif roll < 0.65:
        # Gõ vài ký tự vào ô tìm kiếm rồi xóa (đang suy nghĩ)
        try:
            box = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )
            hover_element(driver, box)
            delay(0.8, 2)
            partial = random.choice(TU_KHOA_LIEN_QUAN)
            n = random.randint(2, max(2, len(partial) // 2 + 1))
            for ch in partial[:n]:
                box.send_keys(ch)
                time.sleep(random.uniform(0.08, 0.25))
            delay(1.5, 4)
            box.clear()
        except Exception:
            pass

    else:
        # Chỉ ngồi idle rồi cuộn nhẹ
        delay(2, 7)
        cuon_tu_nhien(driver, "xuong", random.randint(1, 3))


def luot_trang_chu_youtube(driver):
    """Lướt trang chủ YouTube trước khi tìm kiếm."""
    log("  🏠 Lướt trang chủ YouTube...")
    try:
        cuon_tu_nhien(driver, "xuong", random.randint(3, 6))
        delay(1, 3)
        thumbs = driver.find_elements(
            By.CSS_SELECTOR, "ytd-rich-item-renderer, ytd-compact-video-renderer"
        )
        for thumb in random.sample(thumbs, min(3, len(thumbs))):
            hover_element(driver, thumb)
            delay(0.3, 1.2)
        nghi_ngau_nhien(ty_le=0.3)
    except Exception:
        pass


def tuong_tac_video_youtube(driver, giay_xem: int,
                             handles_cho_phep: set, mood: SessionMood) -> bool:
    """
    Xem video với tương tác người thật + watchdog.
    mood quyết định xác suất mỗi hành động — không còn hardcode.
    Trả về True nếu crash.
    """
    tab_video = driver.current_window_handle
    chunk     = max(8, giay_xem // 7)
    dem       = 0
    crash     = False
    MAX_GIAY  = giay_xem * 3 + 90
    t_bat_dau = time.time()

    # Cumulative thresholds từ mood (thay hardcode)
    t_pause    = mood.pause_prob
    t_seek_fwd = t_pause    + mood.seek_fwd_prob
    t_seek_bwd = t_seek_fwd + mood.seek_bwd_prob
    t_comment  = t_seek_bwd + mood.comment_prob
    t_like     = t_comment  + mood.like_prob
    t_vol      = t_like     + mood.vol_prob
    t_related  = t_vol      + mood.related_prob
    # hd >= t_related → cuộn random

    try:
        player = driver.find_element(By.CSS_SELECTOR, "#movie_player, .html5-video-player")
        hover_element(driver, player)
    except Exception:
        pass

    while dem < giay_xem:
        da_qua = time.time() - t_bat_dau
        if da_qua > MAX_GIAY:
            log(f"    ⚠️ Đã qua {int(da_qua)}s (tối đa {MAX_GIAY}s) — thoát vòng xem")
            crash = True
            break

        c = min(chunk, giay_xem - dem)
        time.sleep(c)
        dem += c

        if not watchdog_tabs(driver, handles_cho_phep, tab_video):
            crash = True
            break

        xu_ly_quang_cao_youtube(driver)

        try:
            if driver.current_window_handle != tab_video:
                if tab_video in driver.window_handles:
                    driver.switch_to.window(tab_video)
                else:
                    crash = True
                    break
        except Exception:
            crash = True
            break

        # Mood passive: hay bỏ qua cả chunk — xem im lặng
        if random.random() < mood.chunk_skip_prob:
            nghi_ngau_nhien(ty_le=0.05)
            continue

        hd = random.random()
        try:
            body = driver.find_element(By.TAG_NAME, "body")

            if hd < t_pause:
                body.send_keys("k")
                time.sleep(random.uniform(1.5, 4.0))
                body.send_keys("k")
                log("    ⏸ Tạm dừng rồi tiếp tục")

            elif hd < t_seek_fwd:
                lan = random.randint(1, 3)
                for _ in range(lan):
                    body.send_keys(Keys.ARROW_RIGHT)
                    time.sleep(0.3)
                log(f"    ⏩ Tua +{lan*5}s")

            elif hd < t_seek_bwd:
                body.send_keys(Keys.ARROW_LEFT)
                time.sleep(0.3)
                log("    ⏪ Tua -5s")

            elif hd < t_comment:
                cuon_tu_nhien(driver, "xuong", random.randint(2, 5))
                delay(2, 6)
                try:
                    cmts = driver.find_elements(By.CSS_SELECTOR, "#content-text")
                    for c_el in random.sample(cmts, min(2, len(cmts))):
                        hover_element(driver, c_el)
                        delay(0.5, 1.5)
                except Exception:
                    pass
                cuon_tu_nhien(driver, "len", random.randint(2, 4))

            elif hd < t_like:
                try:
                    like_btn = driver.find_element(
                        By.CSS_SELECTOR,
                        "ytd-toggle-button-renderer button[aria-label*='like'], #top-level-buttons button"
                    )
                    hover_element(driver, like_btn)
                    delay(0.5, 1.5)
                    if random.random() < mood.like_click_prob:
                        driver.execute_script("arguments[0].click();", like_btn)
                        log("    👍 Đã Like video")
                except Exception:
                    pass

            elif hd < t_vol:
                try:
                    vol = driver.find_element(By.CSS_SELECTOR, ".ytp-volume-panel, .volume-slider")
                    hover_element(driver, vol)
                    delay(0.5, 1.0)
                except Exception:
                    pass

            elif hd < t_related:
                try:
                    related = driver.find_elements(By.CSS_SELECTOR, "ytd-compact-video-renderer")
                    if related:
                        hover_element(driver, random.choice(related[:5]))
                        delay(1, 2)
                except Exception:
                    pass

            else:
                driver.execute_script(f"window.scrollBy(0, {random.randint(-100, 200)});")

        except Exception:
            pass

        nghi_ngau_nhien(ty_le=0.1)
        watchdog_tabs(driver, handles_cho_phep, tab_video)

    return crash


def xem_video_lien_quan(driver, search_url) -> bool:
    """25% xác suất xem video liên quan."""
    try:
        related = driver.find_elements(
            By.CSS_SELECTOR,
            "ytd-compact-video-renderer h3 a, ytd-watch-next-secondary-results-renderer h3 a"
        )
        if related and random.random() < 0.25:
            chon    = random.choice(related[:5])
            tieu_de = (chon.text or "")[:40]
            hover_element(driver, chon)
            delay(0.5, 1.0)
            driver.execute_script("arguments[0].click();", chon)
            delay(3, 6)
            giay = random.randint(20, 60)
            log(f"  🎯 Xem video liên quan: '{tieu_de}...' {giay}s")
            time.sleep(giay)
            return True
    except Exception:
        pass
    return False


def tim_kiem_youtube(driver, tu_khoa: str) -> bool:
    """Tìm kiếm trên YouTube, có thể tìm từ khóa phụ trước."""
    if random.random() < 0.35 and TU_KHOA_LIEN_QUAN:
        tk_phu = random.choice(TU_KHOA_LIEN_QUAN)
        log(f"  🔍 Tìm phụ trước: '{tk_phu}'")
        try:
            o_tim = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )
            o_tim.clear()
            delay(0.3, 0.8)
            go_co_loi_chinh_ta(o_tim, tk_phu)
            delay(0.5, 1.5)
            o_tim.send_keys(Keys.RETURN)
            delay(2, 4)
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            delay(1, 3)
        except Exception:
            pass

    try:
        o_tim = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "search_query"))
        )
        hover_element(driver, o_tim)
        o_tim.click()
        delay(0.3, 0.8)
        o_tim.clear()
        delay(0.2, 0.5)
        go_co_loi_chinh_ta(o_tim, tu_khoa)
        delay(0.5, 1.5)
        o_tim.send_keys(Keys.RETURN)
        delay(2, 5)
        return True
    except TimeoutException:
        log("  ⚠️ YouTube không load được (proxy chậm/chết)")
        return False
    except Exception as e:
        log(f"  ⚠️ Không tìm kiếm được: {str(e)[:60]}")
        return False


def xem_youtube(driver, tu_khoa: str, so_video: int,
                min_giay: int, max_giay: int, mood: SessionMood) -> int:
    """Main YouTube flow: cold start → browse → search → watch videos."""
    log(f"  🎬 YouTube | '{tu_khoa}' | {so_video} video | {min_giay}-{max_giay}s/video | mood={mood.name}")

    if not kiem_tra_ket_noi(driver):
        log("  ❌ Browser đã đóng, bỏ qua YouTube")
        return 0

    try:
        driver.get("https://www.youtube.com")
        delay(3, 6)
    except Exception as e:
        log(f"  ❌ Không vào YouTube được: {str(e)[:60]}")
        return 0

    try:
        cur = driver.current_url
        if "youtube.com" not in cur and "about:" not in cur:
            log(f"  ⚠️ Proxy có thể chết, URL: {cur[:60]}")
    except Exception:
        log("  ❌ Browser crash ngay sau khi vào YouTube")
        return 0

    # Cold start — warm-up behavior trước khi bắt đầu task
    cold_start(driver, mood)

    handles_yt = set(driver.window_handles)
    luot_trang_chu_youtube(driver)

    if not tim_kiem_youtube(driver, tu_khoa):
        return 0

    cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
    nghi_ngau_nhien(ty_le=0.3)

    da_xem     = 0
    thu        = 0
    search_url = driver.current_url

    while da_xem < so_video and thu < so_video * 4:
        thu += 1

        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash, dừng xem video")
            break

        try:
            try:
                cur_url = driver.current_url
                if "results" not in cur_url and "search" not in cur_url:
                    log("  🔙 Quay lại trang tìm kiếm...")
                    driver.get(search_url)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 4)
            except Exception:
                break

            videos = _cho_ket_qua_tim_kiem(driver, timeout=25)
            if not videos:
                log(f"  ⚠️ Không tìm thấy video lần #{thu}, thử reload...")
                driver.get(search_url)
                _cho_trang_load(driver, timeout=15)
                delay(3, 6)
                videos = _cho_ket_qua_tim_kiem(driver, timeout=15)
                if not videos:
                    break

            video   = random.choice(videos[:min(12, len(videos))])
            tieu_de = (video.get_attribute("title") or video.text or "")[:50]

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", video)
            delay(0.5, 1.2)
            hover_element(driver, video)
            delay(0.3, 0.8)

            handles_yt = set(driver.window_handles)
            cdp_click(driver, video)
            time.sleep(0.8)
            don_dep_tab_la(driver, handles_yt)

            _cho_trang_load(driver, timeout=15)
            delay(2, 4)

            if not kiem_tra_ket_noi(driver):
                break

            handles_yt = set(driver.window_handles)
            don_dep_tab_la(driver, handles_yt)

            for _ in range(3):
                if xu_ly_quang_cao_youtube(driver):
                    time.sleep(2)
                else:
                    break

            giay = random.randint(min_giay, max_giay)
            # Early exit: mood quyết định thoát sớm hay xem đủ
            if random.random() < mood.early_exit_prob:
                lo, hi = mood.early_exit_ratio
                giay = max(15, int(giay * random.uniform(lo, hi)))
                log(f"  ▶  [{da_xem+1}/{so_video}] '{tieu_de}' — {giay}s ⏩early")
            else:
                log(f"  ▶  [{da_xem+1}/{so_video}] '{tieu_de}' — {giay}s")

            crash = tuong_tac_video_youtube(driver, giay, handles_yt, mood)
            if crash:
                break

            da_xem += 1

            if da_xem < so_video:
                xem_video_lien_quan(driver, search_url)

            handles_yt = set(driver.window_handles)
            don_dep_tab_la(driver, handles_yt)
            try:
                driver.get(search_url)
                _cho_trang_load(driver, timeout=15)
                delay(2, 5)
                cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
            except Exception:
                break

        except StaleElementReferenceException:
            log(f"  ⚠️ Stale element #{thu}, thử lại...")
            delay(1, 2)
        except TimeoutException:
            log(f"  ⚠️ Timeout tải trang tìm kiếm #{thu}, thử lại...")
            delay(3, 6)
        except (NoSuchWindowException, WebDriverException) as e:
            msg = str(e)[:80]
            if "connection" in msg.lower() or "window" in msg.lower():
                log(f"  ❌ Browser crash: {msg}")
                break
            log(f"  ⚠️ Lỗi video #{thu}: {msg[:60]}")
            delay(2, 4)
        except Exception as e:
            log(f"  ⚠️ Lỗi video #{thu}: {str(e)[:80]}")
            delay(2, 4)

    log(f"  ✅ Đã xem {da_xem}/{so_video} video")
    return da_xem
