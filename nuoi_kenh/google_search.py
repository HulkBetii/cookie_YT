# -*- coding: utf-8 -*-
"""Google Search (google.co.jp) — mô phỏng hành vi tìm kiếm của người Nhật."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException, StaleElementReferenceException,
    TimeoutException,
)

from .config import TU_DONG_DONG_POPUP, GOOGLE_KEYWORDS, TU_KHOA_LIEN_QUAN
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
_GOOGLE_URL = "https://www.google.co.jp"

# ── Selectors ─────────────────────────────────────────────────────

# Organic result links — ordered by stability
_GG_RESULT_SELECTORS = [
    "#search a[href]",     # main results container
    "#rso a[href]",        # result snippet area
    "div.g a[href]",       # classic result cards
    "h3 a[href]",          # result title links
]


# ── Helpers ───────────────────────────────────────────────────────

def _la_link_ket_qua(href: str) -> bool:
    """Chỉ chấp nhận kết quả organic — loại trừ Google internal và YouTube."""
    if not href or href.startswith("javascript") or href == "#":
        return False
    if not href.startswith("http"):
        return False
    # Loại trừ tất cả domain Google và YouTube
    for domain in ("google.", "youtube.com", "youtu.be"):
        if domain in href:
            return False
    return True


def _tim_ket_qua(driver) -> list:
    """Tìm link kết quả organic trên SERP bằng nhiều selector dự phòng."""
    for sel in _GG_RESULT_SELECTORS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            valids = []
            for e in els:
                try:
                    href = e.get_attribute("href") or ""
                    if _la_link_ket_qua(href) and e.is_displayed():
                        valids.append(e)
                except Exception:
                    pass
            if valids:
                return valids
        except Exception:
            pass
    return []


def _doc_trang_ket_qua(driver):
    """Đọc trang kết quả: scroll, highlight text, đôi khi scroll lại."""
    giay = random.randint(15, 40)
    log(f"    📖 Đọc kết quả Google ~{giay}s...")
    for _ in range(random.randint(4, 8)):
        if not kiem_tra_ket_noi(driver):
            return
        cuon_tu_nhien(driver, "xuong", 1)
        nghi_ngau_nhien(ty_le=0.2)
        if random.random() < 0.30:
            chon_van_ban_ngau_nhien(driver)
    if random.random() < 0.15:
        phim_tat_ngau_nhien(driver)
    time.sleep(random.uniform(2, 6))
    nghi_ngau_nhien(ty_le=0.2)
    if random.random() < 0.35:
        cuon_tu_nhien(driver, "len", random.randint(2, 4))
        delay(2, 4)
        cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
    remaining = max(0, giay - 20)
    if remaining > 0:
        time.sleep(remaining)


def _lam_mot_lan_search(driver, keyword: str, handles_goc: set) -> int:
    """
    Một lần search đầy đủ: gõ → SERP → đọc 1-2 kết quả → quay lại Google.
    Returns số trang đã đọc (0-2).
    """
    da_doc = 0
    try:
        # Tìm search box và gõ từ khóa
        try:
            box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
        except TimeoutException:
            log("  ⚠️ Google search box không xuất hiện")
            return 0

        hover_element(driver, box)
        delay(0.4, 1.0)
        driver.execute_script("arguments[0].click();", box)
        time.sleep(random.uniform(0.3, 0.6))
        box.clear()
        go_co_loi_chinh_ta(box, keyword)
        delay(0.5, 1.5)
        box.send_keys(Keys.RETURN)

        _cho_trang_load(driver, timeout=15)
        delay(2, 4)

        if TU_DONG_DONG_POPUP:
            dong_popup_tu_dong(driver)

        # Scroll SERP — đọc snippet trước khi click
        cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
        nghi_ngau_nhien(ty_le=0.3)

        # Hover qua vài kết quả trước khi chọn
        try:
            kets = driver.find_elements(By.CSS_SELECTOR, "h3")
            for h in random.sample(kets, min(3, len(kets))):
                if h.is_displayed():
                    hover_element(driver, h)
                    delay(0.4, 1.2)
        except Exception:
            pass

        # Click 1-2 kết quả organic
        so_click = random.randint(1, 2)
        da_thu = set()  # tránh click trùng

        for _ in range(so_click * 3):
            if da_doc >= so_click:
                break
            if not kiem_tra_ket_noi(driver):
                break

            results = _tim_ket_qua(driver)
            if not results:
                break

            candidates = [r for r in results[:8] if id(r) not in da_thu]
            if not candidates:
                break

            chosen = random.choice(candidates)
            da_thu.add(id(chosen))
            href = chosen.get_attribute("href") or ""

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", chosen)
                delay(0.5, 1.2)
                hover_element(driver, chosen)
                delay(0.5, 1.0)
            except Exception:
                pass

            url_truoc = driver.current_url
            try:
                driver.get(href)
            except Exception:
                delay(1, 2)
                continue

            _cho_trang_load(driver, timeout=15)
            url_sau = driver.current_url

            if url_sau == url_truoc or not url_sau.startswith("http"):
                delay(1, 2)
                continue

            delay(2, 4)
            _doc_trang_ket_qua(driver)

            don_dep_tab_la(driver, handles_goc)
            try:
                driver.back()
                _cho_trang_load(driver, timeout=10)
            except Exception:
                try:
                    driver.get(_GOOGLE_URL)
                    _cho_trang_load(driver, timeout=15)
                except Exception:
                    return da_doc
            delay(2, 3)
            don_dep_tab_la(driver, handles_goc)

            da_doc += 1
            cuon_tu_nhien(driver, "xuong", random.randint(1, 2))
            delay(1, 3)

    except StaleElementReferenceException:
        delay(1, 2)
    except (NoSuchWindowException, WebDriverException) as e:
        if "connection" in str(e).lower() or "marionette" in str(e).lower():
            log("  ❌ Browser crash (Google Search)")
            raise
        don_dep_tab_la(driver, handles_goc)
        delay(1, 3)
    except Exception as e:
        log(f"  ⚠️ Lỗi search '{keyword[:20]}': {str(e)[:60]}")
        don_dep_tab_la(driver, handles_goc)
        delay(1, 3)

    return da_doc


def _chon_keyword() -> str:
    """Chọn từ khóa: 70% từ GOOGLE_KEYWORDS, 30% từ TU_KHOA_LIEN_QUAN."""
    if GOOGLE_KEYWORDS and (not TU_KHOA_LIEN_QUAN or random.random() < 0.70):
        return random.choice(GOOGLE_KEYWORDS)
    if TU_KHOA_LIEN_QUAN:
        return random.choice(TU_KHOA_LIEN_QUAN)
    return "最新ニュース"


# ── Main function ─────────────────────────────────────────────────

def tim_kiem_google(driver, so_lan: int, mood: SessionMood) -> int:
    """Tìm kiếm Google co.jp — đọc kết quả organic. Returns # trang đã đọc."""
    log(f"  🔍 Google Search | {so_lan} lần | mood={mood.name}")

    if not kiem_tra_ket_noi(driver):
        log("  ❌ Browser đã đóng, bỏ qua Google Search")
        return 0

    # ── Vào Google ────────────────────────────────────────────────
    try:
        driver.get(_GOOGLE_URL)
        _cho_trang_load(driver, timeout=20)
        delay(2, 5)
    except Exception as e:
        log(f"  ⚠️ Không vào được Google: {str(e)[:60]}")
        return 0

    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)

    handles_goc = set(driver.window_handles)
    da_doc = 0

    # ── Search loop ───────────────────────────────────────────────
    for i in range(so_lan):
        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash trong Google Search loop")
            break

        keyword = _chon_keyword()
        log(f"  🔎 [{i+1}/{so_lan}] Search: '{keyword}'")

        try:
            ket_qua = _lam_mot_lan_search(driver, keyword, handles_goc)
            da_doc += ket_qua
            log(f"  ✅ Search xong — đọc {ket_qua} trang")
        except (NoSuchWindowException, WebDriverException) as e:
            if "connection" in str(e).lower() or "marionette" in str(e).lower():
                break
            delay(2, 4)
            continue
        except Exception as e:
            log(f"  ⚠️ Lỗi search loop: {str(e)[:60]}")
            delay(2, 4)
            continue

        # Mood-driven: rabbit hole — search thêm 1 lần với từ khóa liên quan
        if i + 1 < so_lan and random.random() < mood.rabbit_hole_prob * 0.5:
            try:
                extra_kw = random.choice(TU_KHOA_LIEN_QUAN) if TU_KHOA_LIEN_QUAN else keyword
                log(f"  🐇 Rabbit hole search: '{extra_kw}'")
                da_doc += _lam_mot_lan_search(driver, extra_kw, handles_goc)
            except Exception:
                pass

        # Nghỉ giữa các lần search
        if i + 1 < so_lan:
            delay(3, 8)

    log(f"  ✅ Xong Google Search — đọc {da_doc} trang")
    return da_doc
