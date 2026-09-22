# -*- coding: utf-8 -*-
"""Wikipedia US/EN — đọc bài viết tri thức và duyệt liên kết nội bộ tự nhiên."""
import time
import random
import urllib.parse
from selenium.webdriver.common.by import By

from .config import WIKIPEDIA_TOPICS, TU_DONG_DONG_POPUP
from .logger import log
from .selenium_utils import _cho_trang_load, safe_get, focus_content_tab, safe_window_handles
from .human_behavior import delay, cuon_tu_nhien, SessionMood
from .news import dong_popup_tu_dong
from .tab_guard import don_dep_tab_la


def luot_wikipedia(driver, so_bai: int = 1, mood: SessionMood = None) -> int:
    """
    Truy cập Wikipedia tiếng Anh, đọc bài viết kiến thức và click liên kết nội bộ.
    Giúp tạo hành vi duyệt web tự nhiên có chiều sâu (rabbit-hole surfing).
    """
    log(f"  📚  Wikipedia EN | {so_bai} chủ đề | mood={mood.name if mood else 'normal'}")
    da_doc = 0
    handles_goc = safe_window_handles(driver)

    topics = random.sample(WIKIPEDIA_TOPICS, min(so_bai, len(WIKIPEDIA_TOPICS)))

    for i, topic in enumerate(topics, 1):
        try:
            encoded_topic = urllib.parse.quote(topic.replace(" ", "_"))
            wiki_url = f"https://en.wikipedia.org/wiki/{encoded_topic}"
            log(f"  📖 [{i}/{len(topics)}] Đọc Wikipedia: '{topic}'")

            if not safe_get(driver, wiki_url, timeout=30):
                log(f"    ⚠️ Không tải được Wikipedia: {topic}")
                continue

            delay(2, 5)
            focus_content_tab(driver)

            if TU_DONG_DONG_POPUP:
                dong_popup_tu_dong(driver)

            # Cuộn đọc bài viết đầu tiên
            thoi_gian_doc = random.randint(15, 30)
            log(f"    👀 Đọc nội dung ~{thoi_gian_doc}s...")
            for _ in range(random.randint(2, 4)):
                cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
                time.sleep(random.uniform(3.0, 6.0))

            da_doc += 1

            # 60% xác suất: click 1 link nội bộ trong bài để đọc sâu thêm
            if random.random() < 0.60:
                try:
                    internal_links = driver.find_elements(
                        By.CSS_SELECTOR,
                        "#mw-content-text p a[href^='/wiki/']:not([href*=':'])"
                    )
                    valid_links = [
                        a for a in internal_links
                        if not a.get_attribute("href").endswith(("/Main_Page", "/Help:", "/Special:"))
                    ]
                    if valid_links:
                        chosen_link = random.choice(valid_links[:min(8, len(valid_links))])
                        link_text = chosen_link.text.strip() or "related topic"
                        log(f"    🔗 Đọc tiếp liên kết: '{link_text}'")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_link)
                        delay(1, 2)
                        chosen_link.click()
                        delay(3, 5)
                        focus_content_tab(driver)

                        # Cuộn đọc bài thứ 2
                        cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
                        delay(8, 15)
                        da_doc += 1
                except Exception as e:
                    log(f"    ⚠️ Không click được link liên quan: {e}")

            don_dep_tab_la(driver, handles_goc)

            if i < len(topics):
                delay(3, 6)

        except Exception as e:
            log(f"    ❌ Lỗi khi đọc Wikipedia: {e}")

    log(f"  ✅ Hoàn thành Wikipedia — đã đọc {da_doc} bài")
    return da_doc
