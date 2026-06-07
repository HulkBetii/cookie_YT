# -*- coding: utf-8 -*-
"""Yahoo! Japan — tin tức, thời tiết, trending. Mô phỏng hành vi người Nhật."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException, StaleElementReferenceException,
)

from .config import TU_DONG_DONG_POPUP, YAHOO_KEYWORDS
from .logger import log
from .selenium_utils import _cho_trang_load, safe_window_handles, safe_get
from .human_behavior import (
    delay, nghi_ngau_nhien, kiem_tra_ket_noi,
    cuon_tu_nhien, hover_element,
    chon_van_ban_ngau_nhien, phim_tat_ngau_nhien,
    go_co_loi_chinh_ta, SessionMood,
)
from .tab_guard import don_dep_tab_la
from .news import dong_popup_tu_dong

# ── URLs ──────────────────────────────────────────────────────────
_YAHOO_HOME      = "https://yahoo.co.jp"
_YAHOO_NEWS_HOME = "https://news.yahoo.co.jp"

# ── Selectors ─────────────────────────────────────────────────────

# Bài báo — ưu tiên href-pattern (bền vững hơn class name)
_YJ_ARTICLE_SELECTORS = [
    "a[href*='news.yahoo.co.jp/articles/']",
    "a[href*='news.yahoo.co.jp/pickup/']",
    "li.newsFeed_item a[href*='news.yahoo.co.jp']",
    ".newsFeed_item_title a",
    "article a[href*='news.yahoo.co.jp']",
]

# Hover targets trên homepage (chỉ hover, không click)
_YJ_TOPIC_HOVER_SEL = "li.newsFeed_item, .sc-hhIiOg, .Topics_main_tD"

# Thời tiết (天気)
_YJ_TENKI_CSS = [
    "a[href*='weather.yahoo.co.jp']",
    "a[href*='tenki.yahoo.co.jp']",
    "a[data-ylk*='weather']",
]
_YJ_TENKI_XPATH = "//a[contains(text(),'天気')]"

# Trending / ranking
_YJ_TRENDING_SELECTORS = [
    ".trendList_item a",
    ".Topics_list li a",
    ".rankList_item a",
    "[data-ylk*='trending'] a",
]

# Search box
_YJ_SEARCH_BOX = [
    "input[name='p']",        # stable — Yahoo Japan search param
    "input[type='search']",
    "#srchbox",
    "form[action*='search.yahoo.co.jp'] input[type='text']",
]


# ── Helpers ───────────────────────────────────────────────────────

def _la_link_bai_yahoo(href: str) -> bool:
    """Lọc URL — chỉ chấp nhận article/pickup của Yahoo News."""
    if not href or href.startswith("javascript") or href == "#":
        return False
    if "rd.listing.yahoo.co.jp" in href:  # shopping/listing ads
        return False
    if "news.yahoo.co.jp/articles/" in href:
        return True
    if "news.yahoo.co.jp/pickup/" in href:
        return True
    return False


def _tim_bai_yahoo(driver) -> list:
    """Tìm link bài báo trên Yahoo! Japan bằng nhiều selector dự phòng."""
    for sel in _YJ_ARTICLE_SELECTORS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            valids = []
            for e in els:
                try:
                    href = e.get_attribute("href") or ""
                    if _la_link_bai_yahoo(href) and e.is_displayed():
                        valids.append(e)
                except Exception:
                    pass
            if valids:
                return valids
        except Exception:
            pass
    return []


def _doc_bai_yahoo(driver):
    """Đọc bài Yahoo News: cuộn tự nhiên, bôi đen, đọc lại."""
    giay = random.randint(15, 45)
    log(f"    📖 Đọc bài Yahoo ~{giay}s...")
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


def _xem_thoi_tiet(driver, handles_goc: set) -> bool:
    """Xem trang thời tiết Yahoo — click 天気, scroll, quay lại."""
    # Thử CSS selectors
    for sel in _YJ_TENKI_CSS:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                hover_element(driver, el)
                delay(0.5, 1.2)
                driver.execute_script("arguments[0].click();", el)
                _cho_trang_load(driver, timeout=15)
                delay(2, 4)
                cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                delay(3, 8)
                don_dep_tab_la(driver, handles_goc)
                driver.back()
                _cho_trang_load(driver, timeout=10)
                delay(1, 2)
                log("    🌤 Xem thời tiết Yahoo xong")
                return True
        except Exception:
            pass
    # Fallback XPath
    try:
        el = driver.find_element(By.XPATH, _YJ_TENKI_XPATH)
        if el.is_displayed():
            hover_element(driver, el)
            delay(0.5, 1.2)
            driver.execute_script("arguments[0].click();", el)
            _cho_trang_load(driver, timeout=15)
            delay(2, 4)
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            delay(3, 8)
            don_dep_tab_la(driver, handles_goc)
            driver.back()
            _cho_trang_load(driver, timeout=10)
            delay(1, 2)
            log("    🌤 Xem thời tiết Yahoo xong")
            return True
    except Exception:
        pass
    return False


def _luot_trending(driver, handles_goc: set) -> bool:
    """Hover và đôi khi click trending topics trên Yahoo."""
    for sel in _YJ_TRENDING_SELECTORS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            valids = [e for e in els if e.is_displayed() and e.text.strip()]
            if not valids:
                continue
            for item in random.sample(valids, min(3, len(valids))):
                hover_element(driver, item)
                delay(0.5, 1.5)
            # 40% thực sự click vào 1 topic
            if random.random() < 0.40:
                chosen = random.choice(valids[:5])
                log(f"    🔥 Trending: {chosen.text.strip()[:30]}")
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
    return False


def _tim_kiem_yahoo(driver, keyword: str) -> bool:
    """Gõ từ khóa vào ô tìm kiếm Yahoo với typo simulation."""
    for sel in _YJ_SEARCH_BOX:
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
            log(f"    🔍 Yahoo search: '{keyword}'")
            return True
        except Exception:
            pass
    return False


# ── Main function ─────────────────────────────────────────────────

def luot_yahoo_japan(driver, so_bai: int, mood: SessionMood) -> int:
    """Duyệt Yahoo! Japan — tin tức, thời tiết, trending. Returns # bài đã đọc."""
    log(f"  🟡 Yahoo! Japan | {so_bai} bài | mood={mood.name}")

    if not kiem_tra_ket_noi(driver):
        log("  ❌ Browser đã đóng, bỏ qua Yahoo! Japan")
        return 0

    # ── Vào trang chủ Yahoo! Japan ───────────────────────────────
    if not safe_get(driver, _YAHOO_HOME, timeout=25):
        log("  ⚠️ Không vào được Yahoo! Japan (timeout/proxy chậm)")
        return 0
    try:
        _cho_trang_load(driver, timeout=20)
        delay(3, 6)
    except Exception as e:
        log(f"  ⚠️ Lỗi sau khi vào Yahoo! Japan: {str(e)[:60]}")
        return 0

    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)

    handles_goc = safe_window_handles(driver)

    # ── Duyệt trang chủ: scroll + hover topics ───────────────────
    cuon_tu_nhien(driver, "xuong", random.randint(3, 6))
    nghi_ngau_nhien(ty_le=0.3)
    try:
        topics = driver.find_elements(By.CSS_SELECTOR, _YJ_TOPIC_HOVER_SEL)
        for t in random.sample(topics, min(3, len(topics))):
            hover_element(driver, t)
            delay(0.4, 1.2)
    except Exception:
        pass
    delay(1, 3)

    # ── Mood-driven optional behaviors ───────────────────────────
    # Thời tiết: "người tò mò, đọc kỹ" (desc_expand_prob)
    if random.random() < max(0.30, mood.desc_expand_prob):
        try:
            _xem_thoi_tiet(driver, handles_goc)
            don_dep_tab_la(driver, handles_goc)
        except Exception:
            pass

    # Trending: "dễ bị distract bởi nội dung liên quan" (related_prob)
    if random.random() < max(0.25, mood.related_prob * 2):
        try:
            _luot_trending(driver, handles_goc)
            don_dep_tab_la(driver, handles_goc)
        except Exception:
            pass

    # Search: "tìm kiếm có chủ đích" (channel_visit_prob)
    if YAHOO_KEYWORDS and random.random() < max(0.20, mood.channel_visit_prob * 0.7):
        try:
            kw = random.choice(YAHOO_KEYWORDS)
            _tim_kiem_yahoo(driver, kw)
            don_dep_tab_la(driver, handles_goc)
            # Quay về trang chủ sau khi search
            if safe_get(driver, _YAHOO_HOME, timeout=20):
                _cho_trang_load(driver, timeout=15)
                delay(2, 4)
        except Exception:
            pass

    # ── Vào Yahoo News để đọc bài ────────────────────────────────
    if not safe_get(driver, _YAHOO_NEWS_HOME, timeout=20):
        log("  ⚠️ Không vào news.yahoo.co.jp (timeout/proxy chậm)")
        return 0
    try:
        _cho_trang_load(driver, timeout=15)
        delay(2, 4)
    except Exception as e:
        log(f"  ⚠️ Lỗi sau khi vào Yahoo News: {str(e)[:60]}")
        return 0

    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)

    # Tìm bài — retry tối đa 5 lần nếu danh sách rỗng
    articles = []
    for _ in range(5):
        articles = _tim_bai_yahoo(driver)
        if articles:
            break
        time.sleep(3)
        try:
            driver.execute_script("window.scrollBy(0, 400);")
        except Exception:
            pass

    if not articles:
        log("  ⚠️ Yahoo News không tìm được bài báo")
        return 0

    log(f"  ✅ Tìm thấy {len(articles)} bài Yahoo News")
    cuon_tu_nhien(driver, "xuong", random.randint(2, 5))
    nghi_ngau_nhien(ty_le=0.3)

    # ── Article reading loop ──────────────────────────────────────
    da_doc = 0
    for _ in range(so_bai * 4):
        if da_doc >= so_bai:
            break
        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash khi đọc Yahoo")
            break

        try:
            articles = _tim_bai_yahoo(driver)
            if not articles:
                cuon_tu_nhien(driver, "xuong", 2)
                articles = _tim_bai_yahoo(driver)
            if not articles:
                break

            bai  = random.choice(articles[:min(20, len(articles))])
            href = bai.get_attribute("href") or ""

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", bai)
            delay(0.5, 1.5)
            hover_element(driver, bai)
            delay(0.5, 1.0)

            url_truoc = driver.current_url
            if not safe_get(driver, href, timeout=20):
                delay(1, 2)
                continue

            _cho_trang_load(driver, timeout=15)
            url_sau = driver.current_url

            if url_sau == url_truoc or "yahoo.co.jp" not in url_sau:
                delay(1, 2)
                continue

            delay(2, 4)
            _doc_bai_yahoo(driver)

            don_dep_tab_la(driver, handles_goc)
            try:
                driver.back()
                _cho_trang_load(driver, timeout=10)
            except Exception:
                if safe_get(driver, _YAHOO_NEWS_HOME, timeout=20):
                    _cho_trang_load(driver, timeout=15)
            delay(2, 3)
            don_dep_tab_la(driver, handles_goc)

            log(f"  📖 [{da_doc + 1}/{so_bai}] bài Yahoo xong")
            da_doc += 1
            cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
            delay(1, 3)

        except StaleElementReferenceException:
            delay(1, 2)
        except (NoSuchWindowException, WebDriverException) as e:
            if "connection" in str(e).lower() or "marionette" in str(e).lower():
                log("  ❌ Browser crash (Yahoo)")
                break
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)
        except Exception as e:
            log(f"  ⚠️ Lỗi bài {da_doc + 1}: {str(e)[:60]}")
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)

    log(f"  ✅ Xong Yahoo! Japan — đọc {da_doc} bài")
    return da_doc
