# -*- coding: utf-8 -*-
"""X (Twitter) — timeline, trending, đọc bài báo từ link tweet. Mô phỏng hành vi người Nhật."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException, StaleElementReferenceException,
)

from .config import TU_DONG_DONG_POPUP, TWITTER_KEYWORDS, TU_KHOA_LIEN_QUAN
from .logger import log
from .selenium_utils import _cho_trang_load
from .human_behavior import (
    delay, nghi_ngau_nhien, kiem_tra_ket_noi,
    cuon_tu_nhien, hover_element,
    chon_van_ban_ngau_nhien, phim_tat_ngau_nhien,
    go_co_loi_chinh_ta, SessionMood,
)
from .tab_guard import don_dep_tab_la
from .news import dong_popup_tu_dong

# ── URLs ──────────────────────────────────────────────────────────
_TWITTER_HOME    = "https://x.com/home"
_TWITTER_EXPLORE = "https://x.com/explore/tabs/trending"

# ── Selectors ─────────────────────────────────────────────────────

# Timeline tweets — data-testid ổn định nhất trên X
_TWEET_SELECTORS = [
    "article[data-testid='tweet']",
    "div[data-testid='cellInnerDiv'] article",
    "section[aria-label] article",
]

# External links trong tweet (bài báo, blog được share)
# Loại trừ internal x.com/twitter.com; giữ lại t.co (browser tự redirect)
_TWEET_LINK_SEL = [
    "article[data-testid='tweet'] a[data-testid='card.wrapper']",
    "article[data-testid='tweet'] a[href*='://']:not([href*='x.com']):not([href*='twitter.com'])",
]

# Trending / Explore
_TRENDING_SELECTORS = [
    "div[data-testid='trend']",
    "a[href*='/hashtag/']",
    "div[aria-label*='trending'] a",
    "div[aria-label*='Trending'] a",
]

# Search box
_SEARCH_BOX_SEL = [
    "input[data-testid='SearchBox_Search_Input']",  # most stable — X test id
    "input[placeholder*='Search']",
    "input[aria-label*='Search']",
]

# Login wall patterns (X-specific)
_X_LOGIN_PATTERNS = ("x.com/i/flow/login", "twitter.com/i/flow/login")


# ── Helpers ───────────────────────────────────────────────────────

def _safe_get(driver, url: str, timeout: int = 25) -> bool:
    """
    driver.get với page_load_timeout giới hạn ngắn.
    X.com tải RẤT chậm/hay treo trên proxy Nhật — driver.get() không giới hạn
    có thể block hàng phút, khiến HTTP connection giữa Selenium↔GPMDriver
    time out và crash CẢ browser session (không chỉ Twitter).
    Giới hạn timeout biến lỗi không bắt được (connection timeout) thành
    TimeoutException có thể catch — bảo vệ session.
    Trả về True nếu load xong, False nếu timeout/lỗi (browser vẫn sống).
    """
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return True
    except Exception:
        return False
    finally:
        try:
            driver.set_page_load_timeout(60)
        except Exception:
            pass


def _co_login_wall(driver) -> bool:
    """Phát hiện login wall của X — URL pattern hoặc nút Login hiển thị."""
    try:
        url = driver.current_url.lower()
        if any(p in url for p in _X_LOGIN_PATTERNS):
            return True
        # Fallback: tìm nút login trên trang (guest mode)
        for sel in ["a[data-testid='loginButton']",
                    "a[href='/login']",
                    "div[data-testid='signupSection']"]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def _la_link_bai_ngoai(href: str) -> bool:
    """Chỉ chấp nhận external link từ tweet — loại trừ X internal URLs."""
    if not href or href.startswith("javascript") or href == "#":
        return False
    if not href.startswith("http"):
        return False
    for domain in ("x.com", "twitter.com", "pic.twitter.com"):
        if domain in href:
            return False
    return True


def _tim_link_trong_tweet(driver) -> list:
    """Tìm external links trong các tweet trên timeline hiện tại."""
    for sel in _TWEET_LINK_SEL:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            valids = []
            for e in els:
                try:
                    href = e.get_attribute("href") or ""
                    if _la_link_bai_ngoai(href) and e.is_displayed():
                        valids.append(e)
                except Exception:
                    pass
            if valids:
                return valids
        except Exception:
            pass
    return []


def _doc_bai_tu_tweet(driver):
    """Đọc bài báo mở từ tweet link: scroll tự nhiên, bôi đen, đọc 15-45s."""
    giay = random.randint(15, 45)
    log(f"    📖 Đọc bài từ tweet ~{giay}s...")
    for _ in range(random.randint(4, 10)):
        if not kiem_tra_ket_noi(driver):
            return
        cuon_tu_nhien(driver, "xuong", 1)
        nghi_ngau_nhien(ty_le=0.2)
        if random.random() < 0.35:
            chon_van_ban_ngau_nhien(driver)
    if random.random() < 0.20:
        phim_tat_ngau_nhien(driver)
    time.sleep(random.uniform(2, 8))
    nghi_ngau_nhien(ty_le=0.2)
    if random.random() < 0.40:
        cuon_tu_nhien(driver, "len", random.randint(2, 4))
        delay(2, 5)
        cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
    remaining = max(0, giay - 25)
    if remaining > 0:
        time.sleep(remaining)


def _tuong_tac_tweet(driver, tweet_el, mood: SessionMood):
    """Hover + tương tác nhẹ với 1 tweet: like hover, đôi khi like thật."""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", tweet_el)
        delay(0.3, 0.8)
        hover_element(driver, tweet_el)
        delay(0.5, 1.5)

        # Hover Like button (không click)
        if random.random() < mood.like_prob * 0.5:
            try:
                like_btn = tweet_el.find_element(
                    By.CSS_SELECTOR, "[data-testid='like'], [aria-label*='Like']")
                if like_btn.is_displayed():
                    hover_element(driver, like_btn)
                    delay(0.3, 0.8)
            except Exception:
                pass

        # Click Like thật — tỷ lệ thấp để tự nhiên
        if random.random() < mood.like_click_prob * 0.25:
            try:
                like_btn = tweet_el.find_element(
                    By.CSS_SELECTOR, "[data-testid='like']")
                if like_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", like_btn)
                    delay(0.5, 1.0)
                    log("    ❤️  Like tweet")
            except Exception:
                pass
    except Exception:
        pass


def _luot_trending_twitter(driver, handles_goc: set) -> bool:
    """Xem trang Trending/Explore — hover hashtag, đôi khi click xem."""
    try:
        if not _safe_get(driver, _TWITTER_EXPLORE, timeout=25):
            return False
        _cho_trang_load(driver, timeout=20)
        delay(2, 5)

        for sel in _TRENDING_SELECTORS:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, sel)
                valids = [i for i in items if i.is_displayed() and i.text.strip()]
                if not valids:
                    continue
                # Hover 3-5 items
                for item in random.sample(valids, min(4, len(valids))):
                    hover_element(driver, item)
                    delay(0.4, 1.2)
                # 40%: click vào 1 trending topic
                if random.random() < 0.40 and valids:
                    chosen = random.choice(valids[:6])
                    topic_text = chosen.text.strip()[:30]
                    log(f"    🔥 Trending: {topic_text}")
                    driver.execute_script("arguments[0].click();", chosen)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 5)
                    cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                    delay(2, 4)
                    don_dep_tab_la(driver, handles_goc)
                    driver.back()
                    _cho_trang_load(driver, timeout=10)
                    delay(1, 2)
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def _tim_kiem_twitter(driver, keyword: str) -> bool:
    """Gõ từ khóa vào search box Twitter và xem kết quả."""
    for sel in _SEARCH_BOX_SEL:
        try:
            box = driver.find_element(By.CSS_SELECTOR, sel)
            if not box.is_displayed():
                continue
            hover_element(driver, box)
            delay(0.4, 1.0)
            driver.execute_script("arguments[0].click();", box)
            time.sleep(random.uniform(0.3, 0.6))
            box.clear()
            go_co_loi_chinh_ta(box, keyword)
            delay(0.5, 1.5)
            box.send_keys(Keys.RETURN)
            _cho_trang_load(driver, timeout=15)
            delay(2, 5)
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            delay(2, 4)
            log(f"    🔍 Twitter search: '{keyword}'")
            return True
        except Exception:
            pass
    return False


# ── Main function ─────────────────────────────────────────────────

def luot_twitter(driver, so_bai: int, mood: SessionMood) -> int:
    """Duyệt X (Twitter) — timeline, trending, đọc bài từ link tweet. Returns # bài đọc."""
    log(f"  🐦 Twitter | {so_bai} bài | mood={mood.name}")

    if not kiem_tra_ket_noi(driver):
        log("  ❌ Browser đã đóng, bỏ qua Twitter")
        return 0

    # ── Vào trang chủ X ──────────────────────────────────────────
    if not _safe_get(driver, _TWITTER_HOME, timeout=25):
        log("  ⚠️ Không vào được X (timeout/proxy chậm) — bỏ qua Twitter")
        return 0
    try:
        _cho_trang_load(driver, timeout=20)
        delay(3, 6)
    except Exception as e:
        log(f"  ⚠️ Lỗi sau khi vào X: {str(e)[:60]}")
        return 0

    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)

    # ── Kiểm tra login wall ───────────────────────────────────────
    if _co_login_wall(driver):
        log("  ⚠️ X yêu cầu đăng nhập — profile chưa login Twitter/X")
        return 0

    handles_goc = set(driver.window_handles)

    # ── Scroll timeline + hover tweets ───────────────────────────
    cuon_tu_nhien(driver, "xuong", random.randint(3, 7))
    nghi_ngau_nhien(ty_le=0.3)

    try:
        tweets = []
        for sel in _TWEET_SELECTORS:
            tweets = driver.find_elements(By.CSS_SELECTOR, sel)
            if tweets:
                break
        for tw in random.sample(tweets, min(4, len(tweets))):
            if tw.is_displayed():
                _tuong_tac_tweet(driver, tw, mood)
    except Exception:
        pass

    delay(1, 3)

    # ── Mood-driven optional behaviors ───────────────────────────
    # Trending: người tò mò (related_prob)
    if random.random() < max(0.30, mood.related_prob * 2):
        try:
            _luot_trending_twitter(driver, handles_goc)
            don_dep_tab_la(driver, handles_goc)
        except Exception:
            pass
        # Quay về timeline sau trending
        if _safe_get(driver, _TWITTER_HOME, timeout=20):
            try:
                _cho_trang_load(driver, timeout=15)
                delay(2, 4)
            except Exception:
                pass

    # Search: "tìm kiếm có chủ đích" (channel_visit_prob)
    if TWITTER_KEYWORDS and random.random() < max(0.20, mood.channel_visit_prob * 0.8):
        try:
            kw = random.choice(TWITTER_KEYWORDS)
            _tim_kiem_twitter(driver, kw)
            don_dep_tab_la(driver, handles_goc)
        except Exception:
            pass
        # Quay về timeline sau search
        if _safe_get(driver, _TWITTER_HOME, timeout=20):
            try:
                _cho_trang_load(driver, timeout=15)
                delay(2, 4)
            except Exception:
                pass

    # ── Article reading loop ──────────────────────────────────────
    da_doc = 0
    visited_urls: set = set()
    for _ in range(so_bai * 4):
        if da_doc >= so_bai:
            break
        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash khi duyệt Twitter")
            break

        try:
            links = _tim_link_trong_tweet(driver)
            if not links:
                # Scroll thêm để load tweet mới
                cuon_tu_nhien(driver, "xuong", 2)
                delay(1, 3)
                links = _tim_link_trong_tweet(driver)
            if not links:
                continue

            # Loại bỏ links đã đọc để tránh lặp bài
            chua_doc = [l for l in links[:min(10, len(links))]
                        if (l.get_attribute("href") or "") not in visited_urls]
            if not chua_doc:
                cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                delay(1, 3)
                continue

            chosen = random.choice(chua_doc)
            href   = chosen.get_attribute("href") or ""
            visited_urls.add(href)

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", chosen)
                delay(0.5, 1.2)
                hover_element(driver, chosen)
                delay(0.5, 1.0)
            except Exception:
                pass

            url_truoc = driver.current_url
            if not _safe_get(driver, href, timeout=20):
                delay(1, 2)
                continue

            _cho_trang_load(driver, timeout=15)
            url_sau = driver.current_url

            if url_sau == url_truoc or not url_sau.startswith("http"):
                delay(1, 2)
                continue

            delay(2, 4)
            _doc_bai_tu_tweet(driver)

            don_dep_tab_la(driver, handles_goc)
            try:
                driver.back()
                _cho_trang_load(driver, timeout=10)
            except Exception:
                if _safe_get(driver, _TWITTER_HOME, timeout=20):
                    try:
                        _cho_trang_load(driver, timeout=15)
                    except Exception:
                        pass
            delay(2, 3)
            don_dep_tab_la(driver, handles_goc)

            # Scroll thêm sau khi quay lại để load tweet mới
            cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
            delay(1, 2)

            log(f"  📖 [{da_doc + 1}/{so_bai}] bài Twitter xong")
            da_doc += 1

        except StaleElementReferenceException:
            delay(1, 2)
        except (NoSuchWindowException, WebDriverException) as e:
            if "connection" in str(e).lower() or "marionette" in str(e).lower():
                log("  ❌ Browser crash (Twitter)")
                break
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)
        except Exception as e:
            log(f"  ⚠️ Lỗi bài {da_doc + 1}: {str(e)[:60]}")
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)

    log(f"  ✅ Xong Twitter — đọc {da_doc} bài")
    return da_doc
