# -*- coding: utf-8 -*-
"""GPM Login API — khởi động/đóng profile, kết nối Selenium."""
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from .config import GPM_API_URL, GPM_BROWSER_DIR
from .logger import log


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
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(15)
        try:
            driver.command_executor._timeout = 30
        except Exception:
            pass
        try:
            driver.command_executor.client_config.timeout = 30
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
        driver.set_page_load_timeout(30)
        return ok
    except Exception:
        try:
            driver.set_page_load_timeout(30)
        except Exception:
            pass
        return False
