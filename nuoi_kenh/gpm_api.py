# -*- coding: utf-8 -*-
"""GPM Login API — khởi động/đóng profile, kết nối Selenium."""
import os
import re
import time
import ctypes
import ctypes.wintypes
import threading
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from .config import GPM_API_URL, GPM_BROWSER_DIR
from .logger import log


# ── Auto-dismiss "Timeout (APP)" dialog ──────────────────────────

_user32 = ctypes.windll.user32
_BM_CLICK = 0x00F5
_EnumWinProc   = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
_EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)


def _get_win_text(hwnd: int) -> str:
    n = _user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    _user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _scan_and_dismiss() -> None:
    """Quét tất cả cửa sổ, tìm dialog có chứa 'Timeout' và click OK."""
    dismissed: list[int] = []

    def on_win(hwnd, _):
        if not _user32.IsWindowVisible(hwnd):
            return True

        has_timeout = [False]

        def on_child_check(ch, _):
            if "Timeout" in _get_win_text(ch) or "timeout" in _get_win_text(ch):
                has_timeout[0] = True
                return False
            return True

        _user32.EnumChildWindows(hwnd, _EnumChildProc(on_child_check), 0)

        if not has_timeout[0]:
            return True

        def on_child_click(ch, _):
            if _get_win_text(ch) in ("OK", "Ok"):
                _user32.SendMessageW(ch, _BM_CLICK, 0, 0)
                dismissed.append(hwnd)
                log(f"[GPM] ✅ Đã tự động bấm OK trên dialog Timeout")
                return False
            return True

        _user32.EnumChildWindows(hwnd, _EnumChildProc(on_child_click), 0)
        return True

    _user32.EnumWindows(_EnumWinProc(on_win), 0)


def _dialog_watcher_loop() -> None:
    while True:
        try:
            _scan_and_dismiss()
        except Exception:
            pass
        time.sleep(0.8)


def start_gpm_dialog_watcher() -> None:
    """Khởi động background thread tự động đóng dialog Timeout (APP)."""
    t = threading.Thread(target=_dialog_watcher_loop, daemon=True, name="gpm-dialog-watcher")
    t.start()
    log("[GPM] 🔄 Dialog watcher đã khởi động (tự động bấm OK khi Timeout)")


# ── Tìm gpmdriver ────────────────────────────────────────────────

def tim_gpmdriver() -> str | None:
    """Tìm gpmdriver.exe trong thư mục GPM."""
    if not os.path.exists(GPM_BROWSER_DIR):
        return None
    prefixes     = ["gpm_browser_chromium_core", "gpm_browser_chrome_core"]
    driver_names = ["gpmdriver.exe", "chromedriver.exe"]
    for prefix in prefixes:
        folders = sorted(
            [f for f in os.listdir(GPM_BROWSER_DIR) if f.startswith(prefix)],
            reverse=True
        )
        for folder in folders:
            for drv in driver_names:
                p = os.path.join(GPM_BROWSER_DIR, folder, drv)
                if os.path.exists(p):
                    return p
    return None


# ── GPM Profile API ───────────────────────────────────────────────

def lay_tat_ca_profiles() -> list:
    try:
        resp = requests.get(f"{GPM_API_URL}/v2/profiles?limit=100", timeout=10)
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        log(f"❌ Không lấy được profiles: {e}")
        return []


def dong_profile_gpm(profile_id: str):
    try:
        requests.get(f"{GPM_API_URL}/v2/stop?profile_id={profile_id}", timeout=10)
    except Exception:
        pass


# ── Parse response ────────────────────────────────────────────────

def _trich_debug_addr(data: dict) -> str | None:
    """Trích remote debugging address từ GPM API response."""
    if not isinstance(data, dict):
        return None

    KEY_CANDIDATES = [
        "selenium_remote_debug_address",
        "remote_debugging_address",
        "debuggerAddress", "debugger_address",
        "ws_endpoint", "wsEndpoint",
        "debug_address", "debug_port",
        "remote_debug_address", "remote_debugging_port",
    ]

    search_targets = [data]
    if isinstance(data.get("data"), dict):
        search_targets.append(data["data"])

    for target in search_targets:
        for key in KEY_CANDIDATES:
            val = target.get(key)
            if val:
                val = str(val).strip()
                if val.isdigit():
                    return f"127.0.0.1:{val}"
                val = re.sub(r"^ws://", "", val)
                val = val.split("/")[0]
                if ":" in val:
                    return val

    raw = str(data)
    m = re.search(r"127\.0\.0\.1:(\d{4,5})", raw)
    if m:
        return f"127.0.0.1:{m.group(1)}"
    return None


# ── Kết nối Selenium ─────────────────────────────────────────────

def mo_profile_gpm(profile_id: str, gpmdriver_path: str) -> webdriver.Chrome | None:
    """
    Nhờ GPM start profile (GPM lo proxy + fingerprint),
    rồi kết nối Selenium qua remote debugging port.
    """
    try:
        resp = requests.get(
            f"{GPM_API_URL}/v2/start?profile_id={profile_id}",
            timeout=60
        )
        data = resp.json()
    except Exception as e:
        log(f"  ❌ GPM API start lỗi: {e}")
        return None

    log(f"  📥 GPM response keys: {list(data.keys()) if isinstance(data, dict) else data}")

    remote_addr = _trich_debug_addr(data)
    if not remote_addr:
        log("  ❌ Không tìm thấy debug address. Full response:")
        log(f"     {data}")
        return None

    driver_path = gpmdriver_path
    if isinstance(data, dict):
        gpm_driver = (data.get("selenium_driver_location")
                      or (data.get("data") or {}).get("selenium_driver_location"))
        if gpm_driver and os.path.exists(gpm_driver):
            driver_path = gpm_driver

    log(f"  🔗 Debug: {remote_addr}  |  Driver: {os.path.basename(driver_path)}")

    for attempt in range(10):
        time.sleep(3)
        try:
            r = requests.get(f"http://{remote_addr}/json/version", timeout=3)
            if r.status_code == 200:
                log(f"  ✅ Browser sẵn sàng (sau {(attempt+1)*3}s)")
                break
        except Exception:
            pass
        if attempt == 9:
            log("  ❌ Browser không phản hồi sau 30s")
            return None

    options = ChromeOptions()
    options.debugger_address = remote_addr
    service = ChromeService(executable_path=driver_path, log_output=os.devnull)

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        try:
            driver.command_executor._timeout = 60
        except Exception:
            pass
        try:
            driver.command_executor.client_config.timeout = 60
        except Exception:
            pass
        # Selenium 4.44.0 creates the urllib3 PoolManager during __init__ using
        # ClientConfig.timeout at that moment (which may be None if
        # socket.getdefaulttimeout() was None). The pool is already built by the
        # time we reach here — setting client_config.timeout above only affects
        # future pools. We must patch the existing pool so every HTTP call to
        # GPMDriver has an explicit read timeout; without it, execute_script /
        # send_keys / WebDriverWait hang forever when Chromium is frozen but
        # GPMDriver's TCP socket stays alive (keepalive suppresses socket errors).
        try:
            from urllib3.util.timeout import Timeout as _Timeout
            _pool_mgr = driver.command_executor._conn
            _t = _Timeout(connect=15, read=60)
            if hasattr(_pool_mgr, 'connection_pool_kw'):
                _pool_mgr.connection_pool_kw['timeout'] = _t
            if hasattr(_pool_mgr, 'pools'):
                for _p in list(_pool_mgr.pools.values()):
                    if hasattr(_p, 'timeout'):
                        _p.timeout = _t
        except Exception:
            pass
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
            )
        except Exception:
            pass
        return driver
    except Exception as e:
        log(f"  ❌ Không kết nối Selenium: {e}")
        return None


# ── Kiểm tra proxy ────────────────────────────────────────────────

def kiem_tra_proxy_nhanh(driver, timeout=12) -> bool:
    """Load Google để kiểm tra proxy còn sống không."""
    try:
        driver.set_page_load_timeout(timeout)
        driver.get("https://www.google.com")
        ok = ("google" in driver.current_url.lower() or
              driver.execute_script("return document.title") != "")
        driver.set_page_load_timeout(60)
        return ok
    except Exception:
        try:
            driver.set_page_load_timeout(60)
        except Exception:
            pass
        return False
