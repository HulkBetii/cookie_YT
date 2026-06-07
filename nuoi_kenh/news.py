# -*- coding: utf-8 -*-
"""Đọc báo — Google News + popup handling + login check."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException, StaleElementReferenceException,
)

from .config import TU_DONG_DONG_POPUP, SU_DUNG_GOOGLE_NEWS, NEWS_SITES, GMAIL_ACCOUNTS
from .logger import log
from .selenium_utils import _cho_trang_load
from .human_behavior import (
    delay, nghi_ngau_nhien, kiem_tra_ket_noi,
    cuon_tu_nhien, hover_element,
    chon_van_ban_ngau_nhien, phim_tat_ngau_nhien,
)
from .tab_guard import don_dep_tab_la

# ── Popup selectors ───────────────────────────────────────────────
_POPUP_SELECTORS = [
    "button[aria-label='Accept all']",
    "button[aria-label='Agree to the use of cookies']",
    "#dialog button.yt-spec-button-shape-next--filled",
    "ytd-consent-bump-v2-lightbox button.yt-spec-button-shape-next--call-to-action",
    "#L2AGLb", "button#W0wltc",
    "button[id*='accept']", "button[class*='accept']",
    "button[id*='agree']",  "button[class*='agree']",
    "button[id*='consent']","button[class*='consent']",
    "button[id*='cookie']", "button[class*='cookie']",
    "a[id*='accept']",      "a[class*='accept']",
    "button[aria-label='Close']", "button[aria-label='Dismiss']",
    "button[class*='close']",     "button[class*='dismiss']",
    "[role='dialog'] button:last-child",
]

_POPUP_TEXTS = [
    "同意する", "すべて同意", "同意", "受け入れる", "承認",
    "Accept all", "Accept All", "Accept", "Agree", "I agree",
    "OK", "Got it", "Continue", "Close", "Dismiss",
    "Tout accepter", "Aceptar", "Akzeptieren",
]

# ── Google News selectors ─────────────────────────────────────────
_GN_ARTICLE_SELECTORS = [
    "article a[href]",
    "div[role='article'] a[href]",
    "c-wiz article a[href]",
    "a.WwrzSb", "a.gPFEn", "a.JtKRv",
    "[data-n-tid] a[href]",
    "h4 a[href], h3 a[href]",
    ".IBr9hb a[href]", ".NiLAwe a[href]",
]

_GN_NAV_PATTERNS = (
    "news.google.com/home", "news.google.com/topics",
    "news.google.com/search", "news.google.com/following",
    "news.google.com/for-you", "news.google.com/saved",
    "news.google.com/u/", "accounts.google.com",
    "policies.google.com", "support.google.com",
)


# ── Popup ─────────────────────────────────────────────────────────

def dong_popup_tu_dong(driver, lan_thu=3):
    """Tự động đóng popup cookie/GDPR. Bỏ qua nếu browser đã crash."""
    if not kiem_tra_ket_noi(driver):
        return

    for _ in range(lan_thu):
        bam_duoc = False

        for sel in _POPUP_SELECTORS:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        log(f"  🍪 Đóng popup: [{sel[:40]}]")
                        time.sleep(0.6)
                        bam_duoc = True
                        break
            except Exception:
                pass
            if bam_duoc:
                break

        if bam_duoc:
            time.sleep(0.8)
            continue

        for txt in _POPUP_TEXTS:
            try:
                els = driver.find_elements(
                    By.XPATH,
                    f"//*[self::button or self::a][contains(translate(normalize-space(.),"
                    f"'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),"
                    f"'{txt.upper()}')]"
                )
                for el in els:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].click();", el)
                        log(f"  🍪 Đóng popup text: [{txt}]")
                        time.sleep(0.6)
                        bam_duoc = True
                        break
            except Exception:
                pass
            if bam_duoc:
                break

        if not bam_duoc:
            break
        time.sleep(0.5)


# ── Login check ───────────────────────────────────────────────────

def xu_ly_yeu_cau_dang_nhap(driver, profile_name: str = "") -> bool:
    """
    Kiểm tra trạng thái đăng nhập.
    - Nếu bị redirect sang trang login Google → thử tự đăng nhập bằng GMAIL_ACCOUNTS.
    - Nếu không có credentials → bỏ qua profile (hành vi cũ).
    - Bỏ qua banner "Sign in" nhẹ (YouTube gợi ý login, không bắt buộc).
    """
    try:
        url = driver.current_url.lower()

        _LOGIN_WALLS = (
            "accounts.google.com/signin",
            "accounts.google.com/v3/signin",
            "accounts.google.com/servicelogin",
            "accounts.google.com/servicologin",
        )

        if any(p in url for p in _LOGIN_WALLS):
            creds = GMAIL_ACCOUNTS.get(profile_name, ())
            if creds and len(creds) == 2:
                log(f"  🔐 Session hết hạn — tự đăng nhập ({profile_name})")
                from .gmail_login import dang_nhap_google
                ok = dang_nhap_google(driver, creds[0], creds[1])
                if not ok:
                    log("  ❌ Đăng nhập thất bại — bỏ qua profile")
                return ok
            else:
                log("  ⚠️ Profile chưa đăng nhập Google, không có credentials — bỏ qua")
                return False

        # Banner "Sign in" nhẹ (không bắt buộc) — bỏ qua
        for sel in ["ytd-button-renderer#dismiss-button button",
                    "button[aria-label='No thanks']", "#dismiss-button"]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    log("  🔕 Bỏ qua banner đăng nhập")
                    time.sleep(0.5)
            except Exception:
                pass
        return True
    except Exception:
        return True


# ── Google News helpers ───────────────────────────────────────────

def _la_link_bai_bao(href: str) -> bool:
    if not href or href.startswith("javascript") or href == "#":
        return False
    for pat in _GN_NAV_PATTERNS:
        if pat in href:
            return False
    if "news.google.com/read/" in href:
        return True
    if "news.google.com/articles/" in href:
        return True
    if href.startswith("http") and "google.com" not in href:
        return True
    return False


def _tim_bai_google_news(driver) -> list:
    """Tìm bài báo trên Google News bằng nhiều selector dự phòng."""
    for sel in _GN_ARTICLE_SELECTORS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            valids = []
            for e in els:
                try:
                    href = e.get_attribute("href") or ""
                    if _la_link_bai_bao(href) and e.is_displayed():
                        valids.append(e)
                except Exception:
                    pass
            if valids:
                return valids
        except Exception:
            pass
    return []


def doc_noi_dung_bai(driver):
    """Đọc bài báo giống người thật: cuộn, bôi đen, Ctrl+F, đọc lại."""
    giay_doc = random.randint(15, 45)
    log(f"    📖 Đọc bài ~{giay_doc}s...")

    for _ in range(random.randint(4, 10)):
        if not kiem_tra_ket_noi(driver):
            return
        cuon_tu_nhien(driver, "xuong", 1)
        nghi_ngau_nhien(ty_le=0.2)
        if random.random() < 0.35:
            chon_van_ban_ngau_nhien(driver)

    if random.random() < 0.2:
        phim_tat_ngau_nhien(driver)

    time.sleep(random.uniform(2, 8))
    nghi_ngau_nhien(ty_le=0.2)

    if random.random() < 0.4:
        cuon_tu_nhien(driver, "len", random.randint(2, 4))
        delay(2, 5)
        cuon_tu_nhien(driver, "xuong", random.randint(1, 3))

    if random.random() < 0.3:
        driver.execute_script(
            "window.scrollTo({top: document.body.scrollHeight * 0.7, behavior: 'smooth'});"
        )
        delay(2, 5)

    time.sleep(max(0, giay_doc - 20))


# ── doc_bao ───────────────────────────────────────────────────────

def doc_bao_google_news(driver, so_bai: int) -> int:
    """Đọc báo từ Google News — mô phỏng hành vi người thật."""
    log(f"  📰 Google News | {so_bai} bài...")

    try:
        driver.get("https://news.google.com/")
        delay(3, 6)
    except Exception as e:
        log(f"  ⚠️ Không vào Google News: {str(e)[:60]}")
        return 0

    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)

    articles = []
    for _ in range(5):
        articles = _tim_bai_google_news(driver)
        if articles:
            break
        time.sleep(3)
        try:
            driver.execute_script("window.scrollBy(0, 200);")
        except Exception:
            pass

    if not articles:
        log("  ⚠️ Google News không tìm được bài báo (proxy chậm hoặc đổi selector)")
        return 0

    log(f"  ✅ Tìm thấy {len(articles)} bài báo")
    cuon_tu_nhien(driver, "xuong", random.randint(3, 6))
    nghi_ngau_nhien(ty_le=0.3)

    handles_goc = set(driver.window_handles)
    da_doc = 0

    for _ in range(so_bai * 4):
        if da_doc >= so_bai:
            break
        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash khi đọc Google News")
            break

        try:
            articles = _tim_bai_google_news(driver)
            if not articles:
                cuon_tu_nhien(driver, "xuong", 2)
                articles = _tim_bai_google_news(driver)
            if not articles:
                break

            bai      = random.choice(articles[:min(30, len(articles))])
            href_bai = bai.get_attribute("href") or ""

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", bai)
            delay(0.5, 1.5)
            hover_element(driver, bai)
            delay(0.5, 1.0)

            url_truoc = driver.current_url
            try:
                driver.get(href_bai)
            except Exception:
                delay(1, 2)
                continue

            _cho_trang_load(driver, timeout=15)
            url_sau = driver.current_url

            if "news.google.com/home" in url_sau or url_sau == url_truoc:
                log("  ⚠️ Không mở được bài, thử bài khác...")
                delay(1, 2)
                continue

            delay(2, 4)
            doc_noi_dung_bai(driver)

            don_dep_tab_la(driver, handles_goc)
            try:
                driver.back()
                _cho_trang_load(driver, timeout=10)
            except Exception:
                driver.get("https://news.google.com/")
                _cho_trang_load(driver, timeout=15)
            delay(2, 3)
            don_dep_tab_la(driver, handles_goc)

            log(f"  📖 [{da_doc+1}/{so_bai}] bài báo xong")
            da_doc += 1
            cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
            delay(1, 3)

        except StaleElementReferenceException:
            delay(1, 2)
        except (NoSuchWindowException, WebDriverException) as e:
            if "connection" in str(e).lower() or "marionette" in str(e).lower():
                log("  ❌ Browser crash")
                break
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)
        except Exception as e:
            log(f"  ⚠️ Lỗi bài {da_doc+1}: {str(e)[:60]}")
            don_dep_tab_la(driver, handles_goc)
            delay(1, 3)

    log(f"  ✅ Đọc xong {da_doc} bài (Google News)")
    return da_doc


def doc_bao(driver, so_bai: int) -> int:
    log(f"  📰 Đọc {so_bai} bài báo...")

    if not kiem_tra_ket_noi(driver):
        log("  ❌ Browser đã đóng, bỏ qua đọc báo")
        return 0

    if SU_DUNG_GOOGLE_NEWS:
        return doc_bao_google_news(driver, so_bai)

    da_doc = 0
    while da_doc < so_bai:
        if not kiem_tra_ket_noi(driver):
            log("  ❌ Browser crash, dừng đọc báo")
            break
        site = random.choice(NEWS_SITES)
        try:
            log(f"  📖 [{da_doc+1}/{so_bai}] {site}")
            driver.get(site)
            delay(2, 5)
            cuon_tu_nhien(driver, "xuong", random.randint(3, 6))
            try:
                links  = driver.find_elements(
                    By.CSS_SELECTOR, "article a, h2 a, h3 a, .news-item a"
                )
                valids = [l for l in links if l.text.strip()][:10]
                if valids:
                    lien_ket = random.choice(valids)
                    hover_element(driver, lien_ket)
                    delay(0.3, 0.8)
                    driver.execute_script("arguments[0].click();", lien_ket)
                    _cho_trang_load(driver, timeout=15)
                    delay(2, 4)
                    doc_noi_dung_bai(driver)
            except Exception:
                pass
            da_doc += 1
            delay(1, 3)
        except (NoSuchWindowException, WebDriverException) as e:
            if "connection" in str(e).lower() or "marionette" in str(e).lower():
                log("  ❌ Browser crash khi đọc báo")
                break
            log(f"  ⚠️ Lỗi bài {da_doc+1}: {str(e)[:60]}")
            da_doc += 1
        except Exception as e:
            log(f"  ⚠️ Lỗi bài {da_doc+1}: {str(e)[:60]}")
            da_doc += 1

    log(f"  ✅ Đọc xong {da_doc} bài")
    return da_doc
