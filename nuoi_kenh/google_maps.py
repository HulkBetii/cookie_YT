# -*- coding: utf-8 -*-
"""Google Maps US — tìm kiếm địa điểm, lướt bản đồ, xem review địa phương."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import MAPS_CITIES_QUERIES, TU_DONG_DONG_POPUP
from .logger import log
from .selenium_utils import _cho_trang_load, safe_get, selenium_call, focus_content_tab, safe_window_handles
from .human_behavior import delay, cuon_tu_nhien, hover_element, go_co_loi_chinh_ta, SessionMood
from .cdp import cdp_click, cdp_drag_mouse, idle_drift
from .news import dong_popup_tu_dong
from .tab_guard import don_dep_tab_la


def keo_tha_ban_do(driver):
    """Kéo thả bản đồ tự nhiên bằng CDP drag mouse."""
    try:
        # Tìm canvas bản đồ
        canvas_els = driver.find_elements(By.CSS_SELECTOR, "#scene canvas, canvas.widget-scene-canvas, #content-container canvas")
        canvas = None
        for c in canvas_els:
            if c.is_displayed():
                canvas = c
                break

        if canvas:
            rect = canvas.rect
            cx = rect.get("x", 400) + rect.get("width", 400) / 2.0
            cy = rect.get("y", 300) + rect.get("height", 300) / 2.0
        else:
            cx, cy = 600.0, 450.0

        # Kéo bản đồ 1-2 lần theo hướng ngẫu nhiên
        for _ in range(random.randint(1, 2)):
            dx = random.uniform(-180, 180)
            dy = random.uniform(-120, 120)
            cdp_drag_mouse(driver, start_x=cx, start_y=cy, end_x=cx + dx, end_y=cy + dy, duration_ms=random.randint(500, 1000))
            time.sleep(random.uniform(0.8, 1.8))
            cx = cx + dx * 0.3
            cy = cy + dy * 0.3
        log("    🗺️ Kéo thả di chuyển bản đồ")
    except Exception:
        pass


def luot_google_maps(driver, so_lan: int = 1, mood: SessionMood = None) -> int:
    """
    Truy cập Google Maps US, tìm kiếm địa điểm địa phương (quán cafe, nhà hàng, công viên),
    kéo/phóng to bản đồ và click xem chi tiết/review của 1 địa điểm.
    Tạo tín hiệu vị trí và Local Trust mạnh mẽ cho tài khoản Google.
    """
    log(f"  🗺️  Google Maps US | {so_lan} địa điểm | mood={mood.name if mood else 'normal'}")
    da_xem = 0
    handles_goc = safe_window_handles(driver)

    queries = random.sample(MAPS_CITIES_QUERIES, min(so_lan, len(MAPS_CITIES_QUERIES)))

    for i, query in enumerate(queries, 1):
        try:
            log(f"  📍 [{i}/{len(queries)}] Tìm kiếm Maps: '{query}'")

            # 1. Điều hướng vào Google Maps US
            maps_url = "https://www.google.com/maps?hl=en"
            if not safe_get(driver, maps_url, timeout=30):
                log("    ⚠️ Không tải được Google Maps")
                continue

            delay(3, 5)
            focus_content_tab(driver)

            if TU_DONG_DONG_POPUP:
                dong_popup_tu_dong(driver)

            # 2. Tìm ô search box trên Google Maps
            search_input = None
            selectors = [
                "input#searchboxinput",
                "input[name='q']",
                "#searchboxinput",
                "input[aria-label*='Search']",
            ]
            for sel in selectors:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    if el.is_displayed():
                        search_input = el
                        break
                except Exception:
                    continue

            if not search_input:
                log("    ⚠️ Không tìm thấy ô tìm kiếm Google Maps")
                continue

            # 3. Gõ từ khóa tìm kiếm
            hover_element(driver, search_input)
            delay(0.2, 0.5)
            search_input.click()
            delay(0.5, 1.2)
            search_input.clear()
            delay(0.3, 0.8)
            go_co_loi_chinh_ta(search_input, query)
            delay(0.5, 1.5)
            search_input.send_keys(Keys.RETURN)

            # 4. Chờ kết quả tải ra
            time.sleep(random.uniform(4.0, 7.0))
            if TU_DONG_DONG_POPUP:
                dong_popup_tu_dong(driver)

            # 5. Kéo bản đồ trước khi chọn điểm
            keo_tha_ban_do(driver)

            # 6. Tương tác cuộn danh sách kết quả hoặc xem chi tiết
            result_items = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc, div.Nv2PK, div[role='article']")

            if result_items:
                log(f"    ✅ Tìm thấy {len(result_items)} địa điểm trên Maps")
                cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
                delay(1, 3)

                # Click vào 1 địa điểm ngẫu nhiên trong top 3
                chosen_item = random.choice(result_items[:min(3, len(result_items))])
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_item)
                    delay(0.5, 1.2)
                    hover_element(driver, chosen_item)
                    delay(0.3, 0.8)
                    chosen_item.click()
                    delay(3, 6)
                    log("    🏢 Đã mở chi tiết địa điểm (địa chỉ, hình ảnh, đánh giá)")

                    # Cuộn xem thông tin chi tiết / reviews
                    cuon_tu_nhien(driver, "xuong", random.randint(2, 4))

                    # 30% click xem ảnh của địa điểm
                    if random.random() < 0.30:
                        try:
                            photo_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Photo'], button.aoRNLd")
                            if photo_btn.is_displayed():
                                hover_element(driver, photo_btn)
                                delay(0.3, 0.7)
                                photo_btn.click()
                                time.sleep(random.uniform(3.0, 6.0))
                                cuon_tu_nhien(driver, "xuong", random.randint(1, 2))
                                time.sleep(random.uniform(2.0, 4.0))
                                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                                log("    📸 Xem bộ ảnh địa điểm")
                        except Exception:
                            pass

                    thoi_gian_xem = random.randint(8, 20)
                    log(f"    👀 Xem thông tin và review ~{thoi_gian_xem}s...")
                    time.sleep(thoi_gian_xem)
                    da_xem += 1
                except Exception as e:
                    log(f"    ⚠️ Không click được chi tiết: {e}")
                    da_xem += 1
            else:
                log("    🗺️ Đang khám phá bản đồ khu vực...")
                keo_tha_ban_do(driver)
                delay(6, 12)
                da_xem += 1

            don_dep_tab_la(driver, handles_goc)

            if i < len(queries):
                delay(3, 7)

        except Exception as e:
            log(f"    ❌ Lỗi khi lướt Google Maps: {e}")

    log(f"  ✅ Hoàn thành Google Maps — đã xem {da_xem} địa điểm")
    return da_xem
