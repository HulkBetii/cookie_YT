# -*- coding: utf-8 -*-
"""
Selenium utilities — timeout protection và helpers cấp thấp.
Không chứa business logic.
"""
import socket
import concurrent.futures
from selenium.webdriver.support.ui import WebDriverWait

# ── Timeout toàn cục ─────────────────────────────────────────────
# Proxy JP 800-900ms latency: page load cần 30-45s → tăng socket timeout lên 60s
socket.setdefaulttimeout(60)

try:
    from selenium.webdriver.remote.remote_connection import RemoteConnection
    RemoteConnection._timeout = 60
except Exception:
    pass

# ── Thread pool cho selenium_call() ──────────────────────────────
_SEL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=8, thread_name_prefix="sel"
)


def selenium_call(func, *args, timeout=25, default=None):
    """
    Chạy Selenium call với hard timeout qua thread.
    Call nào hang quá `timeout` giây → trả `default` ngay lập tức.
    """
    try:
        future = _SEL_EXECUTOR.submit(func, *args)
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        return default
    except Exception as e:
        raise e


def _cho_trang_load(driver, timeout=40):
    """Chờ trang load xong dùng document.readyState."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        # TimeoutException (WebDriverWait expired) OR WebDriverException
        # (urllib3 read timeout fired when Chromium is frozen mid-execute_script)
        pass


def safe_get(driver, url: str, timeout: int = 45) -> bool:
    """
    driver.get() với page_load_timeout giới hạn ngắn.
    Nhiều trang (X.com, YouTube, Yahoo News...) tải RẤT chậm/hay treo trên
    proxy Nhật — driver.get() không giới hạn có thể block hàng phút, khiến
    HTTP connection giữa Selenium↔GPMDriver time out và crash CẢ session
    (ReadTimeoutError/WebDriverException không bắt được ở tầng gọi thường).
    Đặt page_load_timeout biến lỗi không bắt được (connection timeout)
    thành TimeoutException có thể catch — bảo vệ session.
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
            driver.set_page_load_timeout(90)
        except Exception:
            pass


def safe_window_handles(driver, default=None):
    """
    driver.window_handles gọi qua HTTP tới GPMDriver — trên proxy Nhật chậm,
    request này có thể treo quá read-timeout (30s) và raise
    WebDriverException/ReadTimeoutError KHÔNG bắt được bằng try/except thường
    ở tầng gọi (vì nhiều nơi gọi raw `set(driver.window_handles)` ngay đầu
    luồng, chưa vào try). Một lần raise như vậy phá luôn cả session.
    Bọc lại ở đây để luôn trả về an toàn (set rỗng / default) thay vì crash.
    """
    try:
        return set(driver.window_handles)
    except Exception:
        return default if default is not None else set()
