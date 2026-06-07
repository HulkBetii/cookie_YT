# -*- coding: utf-8 -*-
"""
Tự động đăng nhập Google / Gmail.
Được gọi khi xu_ly_yeu_cau_dang_nhap phát hiện session cookie hết hạn.
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .logger import log
from .selenium_utils import _cho_trang_load
from .human_behavior import delay, go_co_loi_chinh_ta, hover_element

_GOOGLE_SIGNIN_URL = "https://accounts.google.com/signin"

# Các URL pattern cho thấy đang ở màn hình login/challenge
_LOGIN_PATTERNS    = ("accounts.google.com/signin", "accounts.google.com/v3/signin",
                      "accounts.google.com/ServiceLogin")
_CHALLENGE_PATTERNS = ("challenge", "2fa", "totp", "mfa", "phone", "recovery",
                        "selectchallenge", "checkyourdevice")


# ── Internal helpers ──────────────────────────────────────────────

def _dang_o_trang_login(url: str) -> bool:
    return any(p in url for p in _LOGIN_PATTERNS)


def _dang_o_challenge(url: str) -> bool:
    return any(p in url.lower() for p in _CHALLENGE_PATTERNS)


def _nhap_email(driver, email: str) -> bool:
    """Điền email vào ô và click Next. Returns True nếu thành công."""
    selectors = [
        "input[type='email']",
        "#identifierId",
        "input[name='identifier']",
    ]
    for sel in selectors:
        try:
            box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            hover_element(driver, box)
            delay(0.3, 0.8)
            driver.execute_script("arguments[0].click();", box)
            time.sleep(random.uniform(0.2, 0.5))
            box.clear()
            go_co_loi_chinh_ta(box, email)
            delay(0.5, 1.2)

            # Click Next
            for next_sel in ["#identifierNext button",
                             "button[jsname='LgbsSe']",
                             "div[id='identifierNext'] button"]:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, next_sel)
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        return True
                except Exception:
                    pass
            return False
        except TimeoutException:
            pass
        except Exception:
            pass
    return False


def _nhap_password(driver, password: str) -> bool:
    """Điền password vào ô và click Next. Returns True nếu thành công."""
    selectors = [
        "input[type='password']",
        "input[name='Passwd']",
        "input[name='password']",
    ]
    for sel in selectors:
        try:
            box = WebDriverWait(driver, 12).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            hover_element(driver, box)
            delay(0.3, 0.8)
            driver.execute_script("arguments[0].click();", box)
            time.sleep(random.uniform(0.2, 0.5))
            box.clear()
            go_co_loi_chinh_ta(box, password)
            delay(0.5, 1.5)

            # Click Next
            for next_sel in ["#passwordNext button",
                             "button[jsname='LgbsSe']",
                             "div[id='passwordNext'] button"]:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, next_sel)
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        return True
                except Exception:
                    pass
            return False
        except TimeoutException:
            pass
        except Exception:
            pass
    return False


def _xu_ly_sau_login(driver, cho_toi_da: int = 30):
    """
    Xử lý các màn hình xuất hiện sau khi nhập password:
    - 2FA / challenge → chờ thủ công tối đa `cho_toi_da` giây
    - "Stay signed in?" → bấm Yes
    - "Protect your account" / "I agree" → bấm Confirm
    - Màn hình chọn account → chọn account đầu tiên
    """
    deadline = time.time() + cho_toi_da

    while time.time() < deadline:
        try:
            url = driver.current_url.lower()
        except Exception:
            return

        # Đã qua login page — xong
        if not _dang_o_trang_login(url) and "accounts.google.com" not in url:
            return

        # Challenge / 2FA — thông báo và chờ
        if _dang_o_challenge(url):
            log("  ⚠️  Google yêu cầu xác thực 2FA — chờ xử lý thủ công...")
            time.sleep(5)
            continue

        # "Stay signed in?" — bấm Yes / Có
        for sel in ["#trustthisdevice-checkbox",
                    "button[data-action='yes']",
                    "button[jsname='LgbsSe']",
                    "#confirm"]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                txt = (btn.text or "").lower()
                if btn.is_displayed() and any(k in txt for k in
                        ("yes", "có", "はい", "confirm", "i agree", "continue", "tiếp")):
                    driver.execute_script("arguments[0].click();", btn)
                    delay(1, 2)
                    break
            except Exception:
                pass

        # Chọn account (account picker)
        try:
            accounts = driver.find_elements(By.CSS_SELECTOR,
                "[data-email], .VV3oRb, div[data-identifier]")
            if accounts:
                driver.execute_script("arguments[0].click();", accounts[0])
                delay(1, 2)
        except Exception:
            pass

        time.sleep(2)


# ── Public API ────────────────────────────────────────────────────

def dang_nhap_google(driver, email: str, password: str) -> bool:
    """
    Tự động đăng nhập Google với email/password cho trước.
    Returns True nếu login thành công (browser không còn ở trang login).
    """
    log(f"  🔐 Đăng nhập Google: {email}")
    try:
        cur = driver.current_url
    except WebDriverException:
        log("  ❌ Browser đã đóng — không thể login")
        return False

    # Nếu chưa ở trang login thì navigate sang
    if not _dang_o_trang_login(cur):
        try:
            driver.get(_GOOGLE_SIGNIN_URL)
            _cho_trang_load(driver, timeout=20)
            delay(2, 4)
        except Exception as e:
            log(f"  ❌ Không vào được trang đăng nhập: {str(e)[:60]}")
            return False

    # Bước 1 — Email
    if not _nhap_email(driver, email):
        log("  ❌ Không tìm được ô nhập email")
        return False

    _cho_trang_load(driver, timeout=15)
    delay(2, 4)

    # Bước 2 — Password
    if not _nhap_password(driver, password):
        log("  ❌ Không tìm được ô nhập password")
        return False

    _cho_trang_load(driver, timeout=20)
    delay(3, 5)

    # Bước 3 — Xử lý màn hình phụ (2FA, Stay signed in, v.v.)
    _xu_ly_sau_login(driver, cho_toi_da=60)

    # Kiểm tra kết quả
    try:
        final_url = driver.current_url.lower()
    except Exception:
        return False

    if _dang_o_trang_login(final_url):
        log("  ❌ Đăng nhập thất bại — vẫn ở trang login")
        return False

    log(f"  ✅ Đăng nhập Google thành công ({email})")
    return True


def can_kiem_tra_login(driver) -> bool:
    """
    Trả về True nếu browser đang hiển thị trang yêu cầu đăng nhập Google.
    Dùng để phát hiện login wall giữa chừng session.
    """
    try:
        url = driver.current_url.lower()
        return _dang_o_trang_login(url)
    except Exception:
        return False
