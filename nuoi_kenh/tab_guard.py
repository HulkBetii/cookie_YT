# -*- coding: utf-8 -*-
"""Bảo vệ tab — phát hiện và đóng tab quảng cáo bật lên."""
import time
from selenium.webdriver.support.ui import WebDriverWait

from .config import DOMAINS_QUANG_CAO
from .logger import log
from .selenium_utils import selenium_call
from .human_behavior import kiem_tra_ket_noi


def la_url_quang_cao(url: str) -> bool:
    """Kiểm tra URL có phải quảng cáo không."""
    if not url or url.strip() == "":
        return True
    if url.startswith("data:"):
        return True
    url_lower = url.lower()
    if url_lower in ("about:blank", "about:newtab", "about:home"):
        return True
    for domain in DOMAINS_QUANG_CAO:
        if domain in url_lower:
            return True
    return False


def _dong_tab_phu(driver, handles_goc):
    """Đóng tất cả tab phụ và quay về tab gốc."""
    try:
        for h in list(driver.window_handles):
            if h not in handles_goc:
                driver.switch_to.window(h)
                driver.close()
        driver.switch_to.window(list(handles_goc)[0])
    except Exception:
        pass


def don_dep_tab_la(driver, handles_cho_phep: set, tab_quay_ve: str = None) -> int:
    """Đóng tab nằm ngoài handles_cho_phep. Trả về số tab đã đóng."""
    so_dong = 0
    try:
        handles_hien_tai = set(driver.window_handles)
        tab_la = handles_hien_tai - handles_cho_phep
        for h in list(tab_la):
            try:
                driver.switch_to.window(h)
                url = ""
                try:
                    WebDriverWait(driver, 1.5).until(
                        lambda d: d.current_url not in ("about:blank", "")
                    )
                    url = driver.current_url
                except Exception:
                    url = driver.current_url
                log(f"    🚫 Đóng tab lạ [{url[:55]}]")
                driver.close()
                so_dong += 1
            except Exception:
                pass
        con_lai = set(driver.window_handles)
        if tab_quay_ve and tab_quay_ve in con_lai:
            driver.switch_to.window(tab_quay_ve)
        elif handles_cho_phep & con_lai:
            driver.switch_to.window(list(handles_cho_phep & con_lai)[0])
    except Exception:
        pass
    if so_dong:
        log(f"    ✅ Đã đóng {so_dong} tab quảng cáo/lạ")
    return so_dong


def click_an_toan(driver, element, handles_cho_phep: set,
                  cho_tab_moi: bool = False, timeout_tab: float = 1.5):
    """
    Click element, tự động đóng tab quảng cáo bật ra.
    cho_tab_moi=True → giữ lại tab hợp lệ và trả về handle.
    """
    tab_hien_tai = driver.current_window_handle
    handles_truoc = set(driver.window_handles)
    try:
        driver.execute_script("arguments[0].click();", element)
    except Exception:
        return None

    time.sleep(timeout_tab)
    handles_sau = set(driver.window_handles)
    tab_moi_xuat_hien = handles_sau - handles_truoc

    if not tab_moi_xuat_hien:
        return None

    if not cho_tab_moi:
        don_dep_tab_la(driver, handles_cho_phep, tab_hien_tai)
        return None

    tab_hop_le = None
    for h in list(tab_moi_xuat_hien):
        try:
            driver.switch_to.window(h)
            try:
                WebDriverWait(driver, 2.0).until(
                    lambda d: d.current_url not in ("about:blank", "")
                )
            except Exception:
                pass
            url = driver.current_url
            if la_url_quang_cao(url):
                log(f"    🚫 Đóng tab quảng cáo: [{url[:55]}]")
                driver.close()
            else:
                tab_hop_le = h
        except Exception:
            try:
                driver.close()
            except Exception:
                pass

    don_dep_tab_la(
        driver,
        handles_cho_phep | ({tab_hop_le} if tab_hop_le else set()),
        tab_hop_le or tab_hien_tai
    )
    return tab_hop_le


def watchdog_tabs(driver, handles_cho_phep: set, tab_hien_tai: str) -> bool:
    """
    Phát hiện và đóng tab lạ trong vòng lặp dài.
    Trả về True nếu browser OK, False nếu crash.
    """
    if not kiem_tra_ket_noi(driver):
        return False

    handles_hien_tai = selenium_call(
        lambda: set(driver.window_handles), timeout=15, default=None
    )
    if handles_hien_tai is None:
        return False

    tab_la = handles_hien_tai - handles_cho_phep
    if tab_la:
        don_dep_tab_la(driver, handles_cho_phep, tab_hien_tai)

    try:
        current = driver.current_window_handle
        if current not in handles_cho_phep:
            driver.close()
            if tab_hien_tai in driver.window_handles:
                driver.switch_to.window(tab_hien_tai)
            elif handles_cho_phep & set(driver.window_handles):
                driver.switch_to.window(
                    list(handles_cho_phep & set(driver.window_handles))[0]
                )
    except Exception:
        pass

    return kiem_tra_ket_noi(driver)
