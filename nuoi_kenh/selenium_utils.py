# -*- coding: utf-8 -*-
"""
Selenium utilities — timeout protection và helpers cấp thấp.
Không chứa business logic.
"""
import socket
import concurrent.futures
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# ── Timeout toàn cục ─────────────────────────────────────────────
socket.setdefaulttimeout(30)

try:
    from selenium.webdriver.remote.remote_connection import RemoteConnection
    RemoteConnection._timeout = 30
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


def _cho_trang_load(driver, timeout=15):
    """Chờ trang load xong dùng document.readyState."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
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
