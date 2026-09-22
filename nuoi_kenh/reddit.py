# -*- coding: utf-8 -*-
"""Reddit US — duyệt subreddit, đọc bài viết và xem thảo luận comments."""
import time
import random
from selenium.webdriver.common.by import By

from .config import REDDIT_SUBREDDITS, TU_DONG_DONG_POPUP
from .logger import log
from .selenium_utils import _cho_trang_load, safe_get, focus_content_tab, safe_window_handles
from .human_behavior import delay, cuon_tu_nhien, SessionMood
from .news import dong_popup_tu_dong
from .tab_guard import don_dep_tab_la


def luot_reddit(driver, so_bai: int = 1, mood: SessionMood = None) -> int:
    """
    Truy cập Reddit US, duyệt subreddit phổ biến, đọc bài viết và thảo luận.
    Reddit là nền tảng hàng đầu tại Mỹ có gắn Google Analytics & Ads tags.
    """
    log(f"  👽  Reddit US | {so_bai} bài | mood={mood.name if mood else 'normal'}")
    da_doc = 0
    handles_goc = safe_window_handles(driver)

    subreddits = random.sample(REDDIT_SUBREDDITS, min(so_bai, len(REDDIT_SUBREDDITS)))

    for i, sub in enumerate(subreddits, 1):
        try:
            log(f"  📱 [{i}/{len(subreddits)}] Duyệt r/{sub}")
            reddit_url = f"https://www.reddit.com/r/{sub}/"

            if not safe_get(driver, reddit_url, timeout=30):
                log(f"    ⚠️ Không tải được r/{sub}")
                continue

            delay(3, 6)
            focus_content_tab(driver)

            if TU_DONG_DONG_POPUP:
                dong_popup_tu_dong(driver)

            # Cuộn lướt feed subreddit
            cuon_tu_nhien(driver, "xuong", random.randint(2, 4))
            delay(2, 4)

            # Tìm các bài viết
            post_links = driver.find_elements(
                By.CSS_SELECTOR,
                "a[data-testid='post-title'], a[slot='full-post-link'], a[href*='/comments/'], shreddit-post a"
            )

            valid_posts = []
            for p in post_links:
                try:
                    href = p.get_attribute("href") or ""
                    if "/comments/" in href and not href.endswith("/comments/"):
                        valid_posts.append((p, href))
                except Exception:
                    continue

            if valid_posts:
                chosen_post, href = random.choice(valid_posts[:min(5, len(valid_posts))])
                log(f"    📖 Mở bài viết: {href.split('/comments/')[-1][:50]}...")

                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chosen_post)
                    delay(1, 2)
                    chosen_post.click()
                except Exception:
                    driver.get(href)

                delay(3, 6)
                focus_content_tab(driver)

                # Cuộn đọc nội dung bài viết và comments
                thoi_gian_doc = random.randint(15, 35)
                log(f"    💬 Đọc bài và thảo luận ~{thoi_gian_doc}s...")

                # Cuộn nhiều đợt như người thật đọc comments
                for _ in range(random.randint(2, 4)):
                    cuon_tu_nhien(driver, "xuong", random.randint(1, 3))
                    time.sleep(random.uniform(3.0, 7.0))

                da_doc += 1
            else:
                log("    👀 Đọc lướt danh sách bài trên feed...")
                delay(8, 15)
                da_doc += 1

            don_dep_tab_la(driver, handles_goc)

            if i < len(subreddits):
                delay(4, 8)

        except Exception as e:
            log(f"    ❌ Lỗi khi duyệt Reddit: {e}")

    log(f"  ✅ Hoàn thành Reddit — đã đọc {da_doc} bài")
    return da_doc
