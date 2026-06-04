# -*- coding: utf-8 -*-
"""Mô phỏng hành vi người thật: cuộn, hover, gõ, chọn text, phím tắt."""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException

from .logger import log
from .selenium_utils import selenium_call
from .cdp import cdp_scroll


def delay(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))


def nghi_ngau_nhien(ty_le=0.25):
    """Ngẫu nhiên dừng lại như đang suy nghĩ."""
    if random.random() < ty_le:
        time.sleep(random.uniform(2.0, 8.0))


def kiem_tra_ket_noi(driver) -> bool:
    """Kiểm tra browser còn sống — thread timeout tránh hang vô hạn."""
    try:
        url = selenium_call(lambda: driver.current_url, timeout=15, default=None)
        return url is not None
    except Exception:
        return False


def cuon_tu_nhien(driver, huong="xuong", so_lan=None):
    """Cuộn tự nhiên qua CDP mouseWheel — native OS event."""
    so_lan = so_lan or random.randint(4, 10)
    for _ in range(so_lan):
        if not kiem_tra_ket_noi(driver):
            break
        if huong == "xuong" and random.random() < 0.15:
            px = -random.randint(50, 150)
        elif huong == "len":
            px = -random.randint(150, 400)
        else:
            px = random.randint(120, 500)
        try:
            buoc = random.randint(2, 5)
            for _ in range(buoc):
                cdp_scroll(driver, px // buoc)
                time.sleep(random.uniform(0.04, 0.14))
        except Exception:
            break
        time.sleep(random.uniform(0.4, 2.5))
        nghi_ngau_nhien(ty_le=0.1)


def hover_element(driver, element):
    """Di chuột lên phần tử qua CDP mouseMoved event."""
    try:
        rect = driver.execute_script("""
            var r = arguments[0].getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2, ok: r.width > 0};
        """, element)
        if not rect or not rect.get("ok"):
            return
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseMoved",
            "x": rect["x"] + random.randint(-5, 5),
            "y": rect["y"] + random.randint(-5, 5),
            "modifiers": 0, "buttons": 0, "button": "none",
        })
        time.sleep(random.uniform(0.3, 0.9))
    except Exception:
        try:
            ActionChains(driver).move_to_element(element).perform()
        except Exception:
            pass


def hover_vi_tri_ngau_nhien(driver):
    """Di chuột đến vị trí ngẫu nhiên trên trang."""
    try:
        w = driver.execute_script("return window.innerWidth;")
        h = driver.execute_script("return window.innerHeight;")
        x = random.randint(100, max(101, w - 100))
        y = random.randint(100, max(101, h - 100))
        ActionChains(driver).move_by_offset(x, y).perform()
        time.sleep(random.uniform(0.2, 0.7))
    except Exception:
        pass


def go_co_loi_chinh_ta(element, text):
    """Gõ từng ký tự, 8% xác suất gõ sai rồi xóa lại."""
    i = 0
    while i < len(text):
        ch = text[i]
        if random.random() < 0.08 and i < len(text) - 1:
            element.send_keys(random.choice("abcdefghijklmnoprstuvwxyz"))
            time.sleep(random.uniform(0.1, 0.3))
            element.send_keys(Keys.BACK_SPACE)
            time.sleep(random.uniform(0.1, 0.25))
        element.send_keys(ch)
        time.sleep(random.uniform(0.04, 0.22))
        if random.random() < 0.05:
            time.sleep(random.uniform(0.4, 1.2))
        i += 1


def chon_van_ban_ngau_nhien(driver):
    """Bôi đen đoạn văn ngẫu nhiên như đang đọc kỹ."""
    try:
        paras = driver.find_elements(By.CSS_SELECTOR, "p, h2, h3, li, span")
        valids = [p for p in paras if p.text.strip() and len(p.text) > 20]
        if not valids:
            return
        para = random.choice(valids[:15])
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", para)
        time.sleep(random.uniform(0.5, 1.0))
        actions = ActionChains(driver)
        actions.double_click(para).perform()
        time.sleep(random.uniform(0.3, 0.8))
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass


def phim_tat_ngau_nhien(driver):
    """Thỉnh thoảng dùng Ctrl+F hoặc cuộn lên đầu trang."""
    hd = random.random()
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        if hd < 0.15:
            body.send_keys(Keys.CONTROL, "f")
            time.sleep(random.uniform(1.0, 2.5))
            body.send_keys(Keys.ESCAPE)
        elif hd < 0.25:
            driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(random.uniform(0.5, 1.5))
    except Exception:
        pass
