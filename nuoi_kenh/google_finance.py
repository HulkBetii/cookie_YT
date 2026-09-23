# -*- coding: utf-8 -*-
"""Google Finance US — tra cứu cổ phiếu, tương tác biểu đồ, đọc tin tài chính & tăng Cookie Trust Score."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException, NoSuchWindowException, StaleElementReferenceException,
)

from .config import TU_DONG_DONG_POPUP, FINANCE_TICKERS
from .logger import log
from .selenium_utils import _cho_trang_load, safe_get, selenium_call
from .human_behavior import (
    delay, nghi_ngau_nhien, kiem_tra_ket_noi,
    cuon_tu_nhien, hover_element, hover_vi_tri_ngau_nhien,
    SessionMood,
)
from .cdp import bezier_mouse_move, cdp_click
from .tab_guard import don_dep_tab_la
from .news import dong_popup_tu_dong


_FINANCE_BASE = "https://www.google.com/finance"
_TIMEFRAME_BTNS = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"]


def _tuong_tac_bieu_do(driver, mood: SessionMood = None):
    """Di chuột dọc theo biểu đồ giá để kích hoạt tooltip hiển thị giá (Price Inspector)."""
    try:
        # Tìm element biểu đồ trên Google Finance
        chart_els = driver.find_elements(By.CSS_SELECTOR, "svg, canvas, div[data-chart-name], div[jsname*='Chart'], [role='region']")
        target_chart = None
        for el in chart_els:
            rect = selenium_call(
                lambda: driver.execute_script("""
                    var r = arguments[0].getBoundingClientRect();
                    return {x: r.left, y: r.top, w: r.width, h: r.height, ok: r.width > 200 && r.height > 100};
                """, el),
                driver=driver,
                timeout=5,
                default=None,
            )
            if rect and rect.get("ok"):
                target_chart = rect
                break

        if target_chart:
            cx = target_chart["x"]
            cy = target_chart["y"]
            cw = target_chart["w"]
            ch = target_chart["h"]

            # Di chuột từ trái sang phải dọc theo chart với 4-7 điểm mốc
            num_points = random.randint(4, 7)
            y_mid = cy + ch * random.uniform(0.3, 0.7)
            for i in range(num_points):
                x_pos = cx + (cw * (i + 1) / (num_points + 1)) + random.uniform(-10, 10)
                y_pos = y_mid + random.uniform(-20, 20)
                bezier_mouse_move(driver, int(x_pos), int(y_pos))
                time.sleep(random.uniform(0.4, 1.2))

            log("    📈 Tương tác hover biểu đồ giá cổ phiếu")
    except Exception:
        pass


def _chuyen_timeframe(driver):
    """Click ngẫu nhiên các nút khung thời gian (1D, 5D, 1M, 1Y)."""
    if random.random() > 0.65:
        return
    try:
        tf_btns = driver.find_elements(By.CSS_SELECTOR, "button, [role='tab'], span[jsname]")
        candidates = []
        for btn in tf_btns:
            txt = (btn.text or "").strip()
            if txt in _TIMEFRAME_BTNS:
                candidates.append(btn)

        if candidates:
            chosen = random.choice(candidates)
            hover_element(driver, chosen)
            time.sleep(random.uniform(0.3, 0.8))
            selenium_call(lambda: chosen.click(), driver=driver, timeout=5)
            log(f"    ⏱️ Đổi khung thời gian chart: {chosen.text}")
            time.sleep(random.uniform(1.2, 2.5))
    except Exception:
        pass


def _doc_tin_tuc_tai_chinh(driver, mood: SessionMood = None):
    """Lướt và xem các tiêu đề tin tức tài chính bên dưới chart."""
    if random.random() > 0.50:
        return
    try:
        cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
        time.sleep(random.uniform(1.0, 2.5))

        news_cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='news'], div[role='heading'], [data-article-id] a")
        if news_cards:
            target_news = random.choice(news_cards[:6])
            hover_element(driver, target_news)
            time.sleep(random.uniform(1.5, 3.5))

            # 30% click mở bài báo tài chính
            if random.random() < 0.30:
                main_handle = driver.current_window_handle
                init_handles = set(driver.window_handles)
                selenium_call(lambda: driver.execute_script("arguments[0].click();", target_news), driver=driver, timeout=6)
                time.sleep(random.uniform(2.0, 4.0))

                new_handles = set(driver.window_handles) - init_handles
                if new_handles:
                    news_tab = list(new_handles)[0]
                    driver.switch_to.window(news_tab)
                    log("    📰 Mở bài báo tài chính trong tab mới...")
                    cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                    time.sleep(random.uniform(3.0, 7.0))
                    driver.close()
                    driver.switch_to.window(main_handle)
                    log("    🔙 Đóng tab tin tài chính, quay lại Google Finance")
    except Exception:
        try:
            if main_handle in driver.window_handles:
                driver.switch_to.window(main_handle)
        except Exception:
            pass


def luot_google_finance(driver, so_ticker: int = 1, mood: SessionMood = None) -> int:
    """
    Duyệt Google Finance US:
    - Tra cứu các mã cổ phiếu phổ biến (Apple, Nvidia, Microsoft, Google, Tesla, S&P500).
    - Tương tác với biểu đồ tài chính, đổi timeframe.
    - Lướt tin tức tài chính thị trường.
    """
    if not kiem_tra_ket_noi(driver):
        return 0

    tickers = list(FINANCE_TICKERS)
    if not tickers:
        tickers = ["AAPL:NASDAQ", "NVDA:NASDAQ", "MSFT:NASDAQ", "GOOGL:NASDAQ", "SPY:NYSEARCA"]

    random.shuffle(tickers)
    tickers_to_visit = tickers[:max(1, so_ticker)]
    thanh_cong = 0

    for idx, ticker in enumerate(tickers_to_visit, 1):
        if not kiem_tra_ket_noi(driver):
            break

        quote_url = f"{_FINANCE_BASE}/quote/{ticker}?hl=en"
        log(f"  💹 [{idx}/{len(tickers_to_visit)}] Google Finance: Tra cứu '{ticker}'...")

        if not safe_get(driver, quote_url, timeout=20):
            continue

        _cho_trang_load(driver, timeout=8)
        if TU_DONG_DONG_POPUP:
            dong_popup_tu_dong(driver)

        time.sleep(random.uniform(1.5, 3.0))

        # 1. Tương tác với biểu đồ
        _tuong_tac_bieu_do(driver, mood)

        # 2. Đổi timeframe chart
        _chuyen_timeframe(driver)

        # 3. Cuộn trang & đọc tin tức tài chính
        _doc_tin_tuc_tai_chinh(driver, mood)

        # 4. Cuộn tự nhiên và nghỉ đọc
        cuon_tu_nhien(driver, "len", 1)
        thoi_gian_xem = random.randint(8, 20)
        time.sleep(thoi_gian_xem)

        don_dep_tab_la(driver)
        thanh_cong += 1

    return thanh_cong
