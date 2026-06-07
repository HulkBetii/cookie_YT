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
from .selenium_utils import _cho_trang_load, safe_window_handles, selenium_call, safe_get
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


# ════════════════════════════════════════════════════════════════
#  YOUTUBE — TÍNH NĂNG PLAYER & CHANNEL
# ════════════════════════════════════════════════════════════════

def doi_chat_luong_video(driver):
    """Đổi chất lượng video sang 360p/480p qua settings menu."""
    try:
        # Mở settings menu
        settings_btn = driver.find_element(By.CSS_SELECTOR, ".ytp-settings-button")
        hover_element(driver, settings_btn)
        driver.execute_script("arguments[0].click();", settings_btn)
        time.sleep(random.uniform(0.8, 1.5))

        # Click Quality
        quality_items = driver.find_elements(
            By.CSS_SELECTOR, ".ytp-menuitem, .ytp-panel-menu .ytp-menuitem"
        )
        for item in quality_items:
            txt = (item.text or "").lower()
            if "quality" in txt or "chất lượng" in txt or "画質" in txt:
                driver.execute_script("arguments[0].click();", item)
                time.sleep(random.uniform(0.5, 1.0))
                break

        # Chọn quality thấp hơn (360p hoặc 480p)
        options = driver.find_elements(By.CSS_SELECTOR, ".ytp-menuitem, .ytp-quality-menu .ytp-menuitem")
        targets = ["480", "360", "240"]
        for target in targets:
            for opt in options:
                if target in (opt.text or ""):
                    driver.execute_script("arguments[0].click();", opt)
                    log(f"    🎥 Đổi chất lượng → {target}p")
                    time.sleep(random.uniform(1, 3))
                    return
    except Exception:
        pass
    # Close menu nếu vẫn mở
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass


def thay_toc_do_phat(driver):
    """Đổi tốc độ phát video 1.25× hoặc 1.5×, sau đó đặt lại Normal."""
    try:
        settings_btn = driver.find_element(By.CSS_SELECTOR, ".ytp-settings-button")
        hover_element(driver, settings_btn)
        driver.execute_script("arguments[0].click();", settings_btn)
        time.sleep(random.uniform(0.8, 1.5))

        # Click "Playback speed"
        items = driver.find_elements(By.CSS_SELECTOR, ".ytp-menuitem")
        for item in items:
            txt = (item.text or "").lower()
            if "speed" in txt or "tốc độ" in txt or "再生速度" in txt:
                driver.execute_script("arguments[0].click();", item)
                time.sleep(random.uniform(0.5, 1.0))
                break

        # Chọn tốc độ ngẫu nhiên
        target_speed = random.choice(["1.25", "1.5", "0.75"])
        options = driver.find_elements(By.CSS_SELECTOR, ".ytp-menuitem")
        _speed_was_set = False
        for opt in options:
            if target_speed in (opt.text or ""):
                driver.execute_script("arguments[0].click();", opt)
                log(f"    ⚡ Tốc độ {target_speed}×")
                time.sleep(random.uniform(10, 30))
                _speed_was_set = True
                break

        # Đặt lại Normal — chỉ khi đã đổi tốc độ thành công
        if _speed_was_set:
            settings_btn = driver.find_element(By.CSS_SELECTOR, ".ytp-settings-button")
            driver.execute_script("arguments[0].click();", settings_btn)
            time.sleep(0.8)
            items = driver.find_elements(By.CSS_SELECTOR, ".ytp-menuitem")
            for item in items:
                txt = (item.text or "").lower()
                if "speed" in txt or "tốc độ" in txt or "再生速度" in txt:
                    driver.execute_script("arguments[0].click();", item)
                    time.sleep(0.5)
                    break
            for opt in driver.find_elements(By.CSS_SELECTOR, ".ytp-menuitem"):
                if "Normal" in (opt.text or "") or "1×" in (opt.text or "") or "普通" in (opt.text or ""):
                    driver.execute_script("arguments[0].click();", opt)
                    break
    except Exception:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass


def bat_tat_phu_de(driver):
    """Bật/tắt CC/Subtitles bằng phím 'c'."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys("c")
        log("    📝 Bật CC/Subtitles")
        time.sleep(random.uniform(3, 8))
        # 50% xác suất tắt lại, 50% để bật
        if random.random() < 0.50:
            body.send_keys("c")
            log("    📝 Tắt CC/Subtitles")
    except Exception:
        pass


def fullscreen_va_thoat(driver):
    """Vào fullscreen xem một lúc rồi thoát."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys("f")
        giay = random.randint(5, 30)
        log(f"    📺 Fullscreen {giay}s")
        time.sleep(giay)
        body.send_keys("f")  # hoặc Escape
    except Exception:
        pass


def doc_mo_ta_video(driver):
    """Mở rộng description, đọc, đôi khi click hashtag."""
    try:
        # Tìm nút expand description
        expand_sels = [
            "#expand",
            "ytd-text-inline-expander button",
            "#description-inline-expander button",
            "tp-yt-paper-button#expand",
        ]
        expanded = False
        for sel in expand_sels:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    hover_element(driver, btn)
                    driver.execute_script("arguments[0].click();", btn)
                    log("    📄 Mở rộng description")
                    expanded = True
                    break
            except Exception:
                pass

        if not expanded:
            return

        # Đọc description
        time.sleep(random.uniform(5, 20))
        cuon_tu_nhien(driver, "xuong", random.randint(1, 3))

        # 40% xác suất click hashtag
        if random.random() < 0.40:
            try:
                hashtags = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#description a[href*='hashtag'], #description a[href*='/search']"
                )
                if hashtags:
                    tag = random.choice(hashtags[:5])
                    hover_element(driver, tag)
                    delay(0.5, 1.5)
                    # Không click thật — chỉ hover (tránh navigate)
            except Exception:
                pass

        # Collapse lại
        try:
            collapse_sels = ["#collapse", "tp-yt-paper-button#collapse"]
            for sel in collapse_sels:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        break
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass


def luu_xem_sau(driver):
    """Lưu video vào Watch Later."""
    try:
        # Click nút "..." menu dưới video
        more_btns = driver.find_elements(
            By.CSS_SELECTOR,
            "ytd-menu-renderer .yt-icon-button, #top-level-buttons-computed ytd-button-renderer"
        )
        menu_btn = None
        for btn in more_btns:
            aria = btn.get_attribute("aria-label") or ""
            if "more" in aria.lower() or "..." in (btn.text or ""):
                menu_btn = btn
                break

        if not menu_btn:
            # Fallback: tìm button có icon dấu "..."
            menu_btn = driver.find_element(
                By.CSS_SELECTOR,
                "ytd-video-primary-info-renderer ytd-menu-renderer button"
            )

        hover_element(driver, menu_btn)
        driver.execute_script("arguments[0].click();", menu_btn)
        time.sleep(random.uniform(0.8, 1.5))

        # Tìm "Save" / "Watch later"
        items = driver.find_elements(By.CSS_SELECTOR, "ytd-menu-service-item-renderer, yt-formatted-string")
        for item in items:
            txt = (item.text or "").lower()
            if "save" in txt or "後で" in txt or "lưu" in txt or "watch later" in txt:
                driver.execute_script("arguments[0].click();", item)
                log("    🕐 Lưu vào Watch Later")
                time.sleep(random.uniform(0.5, 1.0))
                # Đóng dialog nếu xuất hiện
                try:
                    close = driver.find_element(By.CSS_SELECTOR, "ytd-add-to-playlist-renderer button[aria-label*='Close'], paper-dialog button[aria-label*='Close']")
                    driver.execute_script("arguments[0].click();", close)
                except Exception:
                    try:
                        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    except Exception:
                        pass
                return
    except Exception:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass


def tham_kenh_youtube(driver, mood: SessionMood, search_url: str = "") -> bool:
    """
    Visit channel page sau khi xem video.
    Lướt, hover thumbnails, đôi khi subscribe.
    Trả về True nếu thành công.
    """
    try:
        # Click vào tên/avatar channel
        channel_sels = [
            "#channel-name a", "#owner a", "ytd-channel-name a",
            ".ytd-channel-name a", "#top-row ytd-channel-name a",
        ]
        channel_link = None
        for sel in channel_sels:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed() and el.get_attribute("href"):
                    channel_link = el
                    break
            except Exception:
                pass

        if not channel_link:
            return False

        hover_element(driver, channel_link)
        delay(0.5, 1.2)
        driver.execute_script("arguments[0].click();", channel_link)
        _cho_trang_load(driver, timeout=15)
        delay(2, 4)

        channel_url = driver.current_url
        # Chấp nhận cả 3 format: /@handle, /channel/ID, /user/name (legacy)
        if not any(p in channel_url for p in ("youtube.com/@", "/channel/", "/user/")):
            return False

        log(f"  🔗 Tham kênh YouTube: {channel_url[:60]}")

        # Lướt trang channel
        cuon_tu_nhien(driver, "xuong", random.randint(3, 6))
        delay(2, 5)

        # Hover qua 2-3 video thumbnails
        try:
            thumbs = driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer, ytd-grid-video-renderer")
            for thumb in random.sample(thumbs, min(3, len(thumbs))):
                hover_element(driver, thumb)
                delay(0.5, 1.5)
        except Exception:
            pass

        # 20% xem thêm 1 video ngắn từ channel
        if random.random() < 0.20:
            try:
                vids = driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer h3 a, ytd-grid-video-renderer h3 a")
                if vids:
                    v = random.choice(vids[:6])
                    hover_element(driver, v)
                    delay(0.3, 0.8)
                    driver.execute_script("arguments[0].click();", v)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 4)
                    giay = random.randint(20, 40)
                    log(f"    📺 Xem thêm video channel {giay}s")
                    time.sleep(giay)
                    driver.back()
                    _cho_trang_load(driver, timeout=10)
                    delay(1, 3)
            except Exception:
                pass

        # Hover Subscribe (engaged: 30% click thật) — chỉ khi vẫn đang ở channel page
        cur = driver.current_url
        if not any(p in cur for p in ("youtube.com/@", "/channel/", "/user/")):
            return True
        try:
            sub_btn = driver.find_element(By.CSS_SELECTOR,
                "#subscribe-button button, ytd-subscribe-button-renderer button")
            if sub_btn.is_displayed():
                hover_element(driver, sub_btn)
                delay(1, 3)
                if mood.name == "engaged" and random.random() < 0.30:
                    driver.execute_script("arguments[0].click();", sub_btn)
                    log("    🔔 Đã Subscribe kênh")
                    time.sleep(random.uniform(1, 2))
        except Exception:
            pass

        # Quay về
        if search_url:
            safe_get(driver, search_url, timeout=20)
        else:
            driver.back()
        _cho_trang_load(driver, timeout=12)
        delay(1, 3)
        return True

    except Exception as e:
        try:
            if search_url:
                safe_get(driver, search_url, timeout=20)
            else:
                driver.back()
        except Exception:
            pass
        return False


def mo_thong_bao(driver):
    """
    Mở notification panel thật (không chỉ hover).
    Hover qua 1-2 notification, đôi khi click vào 1 cái.
    """
    try:
        bell = driver.find_element(By.CSS_SELECTOR,
            "#notification-button button, button[aria-label*='otification']")
        if not bell.is_displayed():
            return

        hover_element(driver, bell)
        delay(0.5, 1.0)
        driver.execute_script("arguments[0].click();", bell)
        delay(1.5, 3)
        log("  🔔 Mở notification panel")

        # Hover qua notifications
        try:
            notifs = driver.find_elements(By.CSS_SELECTOR,
                "ytd-notification-renderer, .notification-item")
            for notif in random.sample(notifs, min(2, len(notifs))):
                hover_element(driver, notif)
                delay(0.8, 2)

            # 20% click vào 1 notification
            if notifs and random.random() < 0.20:
                n = random.choice(notifs[:5])
                driver.execute_script("arguments[0].click();", n)
                _cho_trang_load(driver, timeout=15)
                delay(2, 5)
                log("    📌 Click notification, xem nhanh")
                time.sleep(random.randint(15, 45))
                driver.back()
                _cho_trang_load(driver, timeout=10)
                delay(1, 3)
                # Đảm bảo trở về YouTube sau back() — tránh SPA navigation không đúng
                if "youtube.com" not in driver.current_url:
                    safe_get(driver, "https://www.youtube.com", timeout=20)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 3)
                return
        except Exception:
            pass

        # Đóng panel
        try:
            driver.execute_script("arguments[0].click();", bell)
        except Exception:
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass

    except Exception:
        pass


def rabbit_hole(driver, search_url: str, mood: SessionMood):
    """
    Depth-2 rabbit hole: sau related video 1, xem thêm 1 related nữa.
    Depth tối đa = 2. Sau xong quay về search_url.
    """
    try:
        related = driver.find_elements(By.CSS_SELECTOR,
            "ytd-compact-video-renderer h3 a, ytd-watch-next-secondary-results-renderer h3 a")
        if not related:
            return

        chon = random.choice(related[:5])
        tieu_de = (chon.text or "")[:35]
        hover_element(driver, chon)
        delay(0.5, 1.0)
        driver.execute_script("arguments[0].click();", chon)
        _cho_trang_load(driver, timeout=15)
        delay(2, 4)

        giay = random.randint(20, 60)
        log(f"  🐇 Rabbit hole depth-2: '{tieu_de}...' {giay}s")
        time.sleep(giay)

    except Exception:
        pass
    finally:
        try:
            safe_get(driver, search_url, timeout=20)
            _cho_trang_load(driver, timeout=12)
            delay(2, 4)
        except Exception:
            pass


def vao_youtube_qua_google(driver, tu_khoa: str) -> bool:
    """
    Vào YouTube bằng cách search Google thay vì trực tiếp.
    Trả về True nếu thành công, False để fallback về direct URL.
    Giới hạn page_load_timeout ngắn hơn để không hang trên proxy chậm.
    """
    t_bat_dau = time.time()
    try:
        # Timeout ngắn hơn cho Google (proxy Nhật đôi khi rất chậm)
        driver.set_page_load_timeout(15)
        try:
            driver.get("https://www.google.com")
        except Exception:
            return False
        finally:
            driver.set_page_load_timeout(30)

        delay(1.5, 3)

        # Tìm ô search Google (clickable, không chỉ present)
        try:
            search_box = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
        except Exception:
            return False

        hover_element(driver, search_box)
        delay(0.4, 1.0)

        # Gõ từ khóa + "youtube" với typo correction
        query = tu_khoa + " youtube"
        go_co_loi_chinh_ta(search_box, query)
        delay(0.5, 1.2)
        search_box.send_keys(Keys.RETURN)
        delay(2, 3)

        # Kiểm tra tổng thời gian — bail out nếu quá 40s
        if time.time() - t_bat_dau > 40:
            return False

        # Tìm và click kết quả YouTube đầu tiên
        results = driver.find_elements(By.CSS_SELECTOR, "a[href*='youtube.com']")
        for r in results[:5]:
            href = r.get_attribute("href") or ""
            if "youtube.com/results" in href or "youtube.com/watch" in href:
                hover_element(driver, r)
                delay(0.3, 0.8)
                driver.execute_script("arguments[0].click();", r)
                _cho_trang_load(driver, timeout=15)
                delay(1, 3)
                if "youtube.com" in driver.current_url:
                    log("  🌐 Vào YouTube qua Google Search")
                    return True

        return False

    except Exception:
        return False
    finally:
        # Đảm bảo timeout được reset
        try:
            driver.set_page_load_timeout(30)
        except Exception:
            pass


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
        # Mở notification panel thật (60%) hoặc chỉ hover (40%)
        if random.random() < 0.60:
            mo_thong_bao(driver)
        else:
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
            safe_get(driver, "https://www.youtube.com/feed/history", timeout=20)
            delay(3, 8)
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            safe_get(driver, "https://www.youtube.com", timeout=20)
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
    Trả về tuple (crash, da_xem_du):
      - crash: True nếu browser/connection chết giữa chừng
      - da_xem_du: True nếu đã xem đủ thời lượng dự kiến (dem >= giay_xem),
        kể cả khi crash xảy ra NGAY SAU đó (vd. watchdog hậu-kiểm chết) —
        người dùng đã thực sự xem xong video, không nên tính là "chưa xem"
    """
    tab_video = driver.current_window_handle
    chunk     = max(8, giay_xem // 7)
    dem       = 0
    crash     = False
    MAX_GIAY  = giay_xem * 3 + 90
    t_bat_dau = time.time()

    # Local flags — mỗi hành vi chỉ xảy ra 1 lần/video (giống người thật)
    _quality_changed  = False
    _subtitle_toggled = False
    _speed_changed    = False
    _fullscreened     = False
    _theater          = False
    _desc_expanded    = False

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
                if tab_video in safe_window_handles(driver):
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

        # ── Hành vi một lần/video (check ĐỘC LẬP — dùng if, KHÔNG elif) ──
        # Mỗi hành vi có xác suất riêng, có thể xảy ra cùng lúc trong 1 video.
        if not _quality_changed and random.random() < mood.quality_change_prob:
            try:
                doi_chat_luong_video(driver)
                _quality_changed = True
            except Exception:
                pass

        if not _subtitle_toggled and random.random() < mood.subtitle_prob:
            try:
                bat_tat_phu_de(driver)
                _subtitle_toggled = True
            except Exception:
                pass

        if not _speed_changed and random.random() < mood.speed_change_prob:
            try:
                thay_toc_do_phat(driver)
                _speed_changed = True
            except Exception:
                pass

        if not _fullscreened and random.random() < mood.fullscreen_prob:
            try:
                fullscreen_va_thoat(driver)
                _fullscreened = True
            except Exception:
                pass

        if not _theater and random.random() < mood.theater_prob:
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys("t")  # theater mode
                _theater = True  # entered theater — mark even if exit fails
                time.sleep(random.uniform(8, 25))
                driver.find_element(By.TAG_NAME, "body").send_keys("t")  # exit theater
            except Exception:
                pass

        if not _desc_expanded and random.random() < mood.desc_expand_prob:
            try:
                doc_mo_ta_video(driver)
                _desc_expanded = True
            except Exception:
                pass

        watchdog_tabs(driver, handles_cho_phep, tab_video)

    da_xem_du = dem >= giay_xem
    return crash, da_xem_du


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


def _focus_search_box(driver, timeout=30):
    """
    Chờ search box INTERACTABLE rồi JS-click focus. Poll nhiều selector để
    chịu được DOM thay đổi sau popup dismiss hoặc SPA navigation.
    """
    _SELECTORS = [
        (By.NAME, "search_query"),          # YouTube homepage + results page
        (By.ID, "search"),                   # <input id="search"> bên trong ytd-searchbox
        (By.CSS_SELECTOR, "input.ytSearchboxComponentSearchbox"),  # YouTube 2024+ class
        (By.CSS_SELECTOR, "input[aria-label*='earch']"),           # aria fallback
    ]
    deadline = time.time() + timeout
    while time.time() < deadline:
        for by, sel in _SELECTORS:
            # find_element gọi qua HTTP tới GPMDriver — global read-timeout là 30s,
            # nên 1 lần proxy chậm có thể khiến lệnh này "treo" tới 30s. Với 4
            # selector, một vòng quét có thể mất tới 120s, vượt xa `timeout` danh
            # nghĩa và khiến deadline-check phía trên gần như vô nghĩa. Bọc qua
            # selenium_call với timeout ngắn để mỗi lần thử bị chặn tối đa vài giây.
            try:
                el = selenium_call(lambda by=by, sel=sel: driver.find_element(by, sel),
                                   timeout=6, default=None)
            except Exception:
                el = None
            if el is None:
                continue
            try:
                if el.is_displayed() and el.is_enabled():
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(random.uniform(0.3, 0.7))
                    el.clear()
                    return el
            except Exception:
                pass
        if time.time() >= deadline:
            break
        time.sleep(1)
    return None


def _clear_overlays(driver):
    """
    Xóa mọi popup/overlay đang block search box trước khi tìm kiếm.
    Gọi ngay trước _focus_search_box để đảm bảo không bị chặn.
    """
    # Nhập Escape để đóng notification panel, menu, autocomplete
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass
    # Dismiss popup cookie/consent nếu còn
    try:
        from .news import dong_popup_tu_dong
        dong_popup_tu_dong(driver, lan_thu=1)
    except Exception:
        pass


def tim_kiem_youtube(driver, tu_khoa: str) -> bool:
    """Tìm kiếm trên YouTube, có thể tìm từ khóa phụ trước."""
    # Xóa overlay trước khi tìm kiếm (notification panel, consent popup, menu)
    _clear_overlays(driver)

    if random.random() < 0.35 and TU_KHOA_LIEN_QUAN:
        tk_phu = random.choice(TU_KHOA_LIEN_QUAN)
        log(f"  🔍 Tìm phụ trước: '{tk_phu}'")
        try:
            o_tim = _focus_search_box(driver, timeout=20)
            if o_tim:
                go_co_loi_chinh_ta(o_tim, tk_phu)
                delay(0.5, 1.5)
                o_tim.send_keys(Keys.RETURN)
                delay(2, 4)
                cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                delay(1, 3)
        except Exception:
            pass

    # Tìm kiếm từ khóa chính — clear overlay lần 2 (preliminary search / popup có thể để lại state)
    _clear_overlays(driver)
    delay(1, 2)
    o_tim = _focus_search_box(driver, timeout=35)
    if o_tim is None:
        log("  ⚠️ YouTube search box không interactable (proxy chậm/chết)")
        return False
    try:
        hover_element(driver, o_tim)
        delay(0.2, 0.5)
        go_co_loi_chinh_ta(o_tim, tu_khoa)
        delay(0.5, 1.5)
        o_tim.send_keys(Keys.RETURN)
        delay(2, 5)
        return True
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

    # Entry point: 25% vào qua Google Search thay vì direct URL
    entry_ok = False
    if random.random() < 0.25:
        entry_ok = vao_youtube_qua_google(driver, tu_khoa)

    # Luôn về homepage — cold_start và luot_trang_chu_youtube giả định homepage layout.
    # Google entry có thể land ở /results hoặc /watch nên vẫn cần navigate về homepage.
    try:
        if not safe_get(driver, "https://www.youtube.com", timeout=25):
            log("  ❌ Không vào YouTube được: load timeout (proxy chậm/chết)")
            return 0
        delay(3, 5) if not entry_ok else delay(2, 4)
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

    handles_yt = safe_window_handles(driver)
    luot_trang_chu_youtube(driver)

    # Session-level watch_later flag (chỉ lưu 1 lần/session)
    _saved_watch_later = False

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
                    safe_get(driver, search_url, timeout=20)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 4)
            except Exception:
                break

            videos = _cho_ket_qua_tim_kiem(driver, timeout=25)
            if not videos:
                log(f"  ⚠️ Không tìm thấy video lần #{thu}, thử reload...")
                safe_get(driver, search_url, timeout=20)
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

            handles_yt = safe_window_handles(driver)
            cdp_click(driver, video)
            time.sleep(0.8)
            don_dep_tab_la(driver, handles_yt)

            _cho_trang_load(driver, timeout=15)
            delay(2, 4)

            if not kiem_tra_ket_noi(driver):
                break

            handles_yt = safe_window_handles(driver)
            don_dep_tab_la(driver, handles_yt)

            for _ in range(3):
                if xu_ly_quang_cao_youtube(driver):
                    time.sleep(2)
                else:
                    break

            # Watch Later — lưu video 1 lần/session
            if not _saved_watch_later and random.random() < mood.watch_later_prob:
                luu_xem_sau(driver)
                _saved_watch_later = True

            giay = random.randint(min_giay, max_giay)
            # Early exit: mood quyết định thoát sớm hay xem đủ
            if random.random() < mood.early_exit_prob:
                lo, hi = mood.early_exit_ratio
                giay = max(15, int(giay * random.uniform(lo, hi)))
                log(f"  ▶  [{da_xem+1}/{so_video}] '{tieu_de}' — {giay}s ⏩early")
            else:
                log(f"  ▶  [{da_xem+1}/{so_video}] '{tieu_de}' — {giay}s")

            crash, da_xem_du = tuong_tac_video_youtube(driver, giay, handles_yt, mood)
            if da_xem_du:
                # Đã xem đủ thời lượng dự kiến — tính là đã xem dù crash xảy ra
                # ngay sau đó (vd. watchdog hậu-kiểm phát hiện browser chết)
                da_xem += 1
            if crash:
                break

            if da_xem < so_video:
                # Channel visit (mood-based, mutually exclusive với related)
                if random.random() < mood.channel_visit_prob:
                    tham_kenh_youtube(driver, mood, search_url)
                    # tham_kenh đã navigate về search_url
                elif random.random() < 0.25:
                    # Rabbit hole thay vì single related
                    if random.random() < mood.rabbit_hole_prob:
                        rabbit_hole(driver, search_url, mood)
                    else:
                        xem_video_lien_quan(driver, search_url)

            handles_yt = safe_window_handles(driver)
            don_dep_tab_la(driver, handles_yt)
            try:
                if not safe_get(driver, search_url, timeout=20):
                    log("  ⚠️ Quay lại trang tìm kiếm timeout — dừng vòng xem")
                    break
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
