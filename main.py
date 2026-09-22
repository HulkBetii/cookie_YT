#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuôi Kênh YouTube & Nâng Cao Cookie Trust Score — Thị Trường US (Mỹ)
Entry point: chạy file này để bắt đầu.
"""
import sys
import time
import datetime
import random
import argparse
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from nuoi_kenh.config import (
    SO_VIDEO, MIN_GIAY_XEM, MAX_GIAY_XEM, SO_TIN_DOC,
    SO_VIDEO_MIN, SO_VIDEO_MAX, SO_TIN_DOC_MIN, SO_TIN_DOC_MAX,
    SO_VONG_LAP, NGHI_GIUA_VONG_MIN, NGHI_GIUA_VONG_MAX,
    NGHI_DAI_XAC_SUAT, NGHI_NGAN_XAC_SUAT,
    NGHI_DAI_MIN, NGHI_DAI_MAX, NGHI_NGAN_MIN, NGHI_NGAN_MAX,
    KHUNG_GIO_NGHI_DAI, HE_SO_HOAT_DONG_THEO_GIO,
    TRON_PROFILES, DANH_SACH_TU_KHOA, TU_DONG_DONG_POPUP,
    KIEM_TRA_PROXY, THU_LAI_KHI_LOI, LOG_FILE, GPM_BROWSER_DIR,
    SO_LUONG_CHAY_SONG_SONG, GPM_ADDITIONAL_ARGS,
    TIM_KIEM_GOOGLE, SO_GOOGLE_MIN, SO_GOOGLE_MAX,
    SU_DUNG_GOOGLE_NEWS,
    SU_DUNG_GOOGLE_MAPS, SO_MAPS_MIN, SO_MAPS_MAX,
    SU_DUNG_REDDIT, SO_REDDIT_MIN, SO_REDDIT_MAX,
    SU_DUNG_WIKIPEDIA, SO_WIKI_MIN, SO_WIKI_MAX,
    LUOT_TWITTER, SO_TWITTER_MIN, SO_TWITTER_MAX,
    MUI_GIO_US, GMAIL_ACCOUNTS,
)
from nuoi_kenh.logger import log
from nuoi_kenh.gpm_api import (
    tim_gpmdriver, lay_tat_ca_profiles,
    mo_profile_gpm, dong_profile_gpm, kiem_tra_proxy_nhanh,
    start_gpm_dialog_watcher, cap_nhat_proxy_gpm,
)
from nuoi_kenh.cdp import cdp_setup
from nuoi_kenh.human_behavior import (
    delay, draw_session_mood, kiem_tra_ket_noi,
    SessionArchetype, SessionMood, go_co_loi_chinh_ta, cuon_tu_nhien,
)
from nuoi_kenh.selenium_utils import driver_failure_reason, safe_quit
from nuoi_kenh.news import (
    dong_popup_tu_dong, xu_ly_yeu_cau_dang_nhap, doc_bao,
)
from nuoi_kenh.youtube import xem_youtube, luot_youtube_shorts
from nuoi_kenh.google_search import tim_kiem_google
from nuoi_kenh.google_maps import luot_google_maps
from nuoi_kenh.reddit import luot_reddit
from nuoi_kenh.wikipedia import luot_wikipedia
from nuoi_kenh.twitter import luot_twitter
from nuoi_kenh.gmail_login import can_kiem_tra_login, dang_nhap_google


# ── Keyword rotation ─────────────────────────────────────────────
_TU_KHOA_GAN_DAY: list = []


def lay_tu_khoa(vong: int) -> str:
    if not DANH_SACH_TU_KHOA:
        return "Huberman Lab productivity hacks"
    so_nho = min(3, max(1, len(DANH_SACH_TU_KHOA) - 2))
    ung_vien = [k for k in DANH_SACH_TU_KHOA if k not in _TU_KHOA_GAN_DAY[-so_nho:]]
    if not ung_vien:
        ung_vien = DANH_SACH_TU_KHOA
    chon = random.choice(ung_vien)
    _TU_KHOA_GAN_DAY.append(chon)
    if len(_TU_KHOA_GAN_DAY) > so_nho:
        _TU_KHOA_GAN_DAY.pop(0)
    return chon


# ── Statistics ───────────────────────────────────────────────────

def _in_thong_ke(vong: int, stats: dict, tu_khoa: str, thoi_gian: float):
    phut = int(thoi_gian // 60)
    giay = int(thoi_gian % 60)
    log("=" * 55)
    log(f"📊  KẾT QUẢ VÒNG {vong}  |  Từ khóa: {tu_khoa}")
    log(f"    ⏱  Thời gian   : {phut}p {giay}s")
    log(f"    ✅ Thành công  : {stats['ok']} profile")
    log(f"    ❌ Lỗi / bỏ   : {stats['loi']} profile")
    log(f"    🎬 Video YouTube : {stats['video']} video")
    if stats.get("shorts", 0) > 0:
        log(f"    📱 YouTube Shorts: {stats['shorts']} shorts")
    log(f"    📰 Google News  : {stats['bai']} bài")
    if stats.get("maps", 0) > 0:
        log(f"    🗺️  Google Maps : {stats['maps']} địa điểm")
    if stats.get("reddit", 0) > 0:
        log(f"    👽 Reddit US    : {stats['reddit']} bài")
    if stats.get("wiki", 0) > 0:
        log(f"    📚 Wikipedia EN : {stats['wiki']} bài")
    if stats.get("google", 0) > 0:
        log(f"    🔍 Google Search: {stats['google']} trang")
    if stats.get("twitter", 0) > 0:
        log(f"    🐦 Twitter / X  : {stats['twitter']} bài")
    if stats["chi_tiet_loi"]:
        log("    Chi tiết lỗi:")
        for ten, ly_do in stats["chi_tiet_loi"]:
            log(f"      • {ten}: {ly_do}")
    log("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────

def _spread_weights(n: int, peak_right: bool = True) -> list:
    """Sinh weights hình chuông cho n phần tử."""
    if n == 1:
        return [1]
    peak = max(0, min(n - 1, int(n * (0.65 if peak_right else 0.50))))
    w = []
    for i in range(n):
        dist = abs(i - peak)
        w.append(max(1, 10 - dist * 2))
    return w


# ── Circadian rhythm — nhịp sinh học theo múi giờ US ──────────────

def _he_so_theo_gio(bang: dict, gio: int = None) -> float:
    """Tra hệ số nhân theo khung giờ hiện tại theo múi giờ US (EST/EDT)."""
    if gio is None:
        try:
            gio = datetime.datetime.now(ZoneInfo(MUI_GIO_US)).hour
        except Exception:
            gio = datetime.datetime.now().hour
    for (bd, kt), he_so in bang.items():
        if bd <= gio < kt or (bd > kt and (gio >= bd or gio < kt)):
            return he_so
    return 1.0


# ── Markov Decision Process (Ma Trận Chuyển Trạng Thái) ───────────

MARKOV_TRANSITIONS = {
    "start": {
        "google": 0.25,
        "youtube": 0.35,
        "news": 0.18,
        "maps": 0.12,
        "reddit": 0.10,
    },
    "google": {
        "youtube": 0.38,
        "news": 0.22,
        "reddit": 0.18,
        "wiki": 0.12,
        "maps": 0.10,
    },
    "youtube": {
        "shorts": 0.30,
        "reddit": 0.25,
        "google": 0.20,
        "news": 0.15,
        "wiki": 0.10,
    },
    "shorts": {
        "youtube": 0.40,
        "reddit": 0.25,
        "twitter": 0.20,
        "news": 0.15,
    },
    "news": {
        "google": 0.30,
        "youtube": 0.25,
        "reddit": 0.20,
        "wiki": 0.15,
        "maps": 0.10,
    },
    "reddit": {
        "youtube": 0.35,
        "google": 0.25,
        "wiki": 0.20,
        "news": 0.10,
        "twitter": 0.10,
    },
    "maps": {
        "google": 0.35,
        "news": 0.25,
        "youtube": 0.25,
        "reddit": 0.15,
    },
    "wiki": {
        "google": 0.35,
        "youtube": 0.30,
        "reddit": 0.20,
        "news": 0.15,
    },
    "twitter": {
        "youtube": 0.40,
        "reddit": 0.25,
        "news": 0.20,
        "google": 0.15,
    },
}


def _lay_dich_vu_kha_dung(so_tin: int) -> dict:
    """Kiểm tra dịch vụ nào được bật theo cấu hình config."""
    return {
        "youtube": True,
        "shorts": True,
        "google": TIM_KIEM_GOOGLE,
        "news": SU_DUNG_GOOGLE_NEWS and (so_tin > 0),
        "maps": SU_DUNG_GOOGLE_MAPS,
        "reddit": SU_DUNG_REDDIT,
        "wiki": SU_DUNG_WIKIPEDIA,
        "twitter": LUOT_TWITTER,
    }


def _chon_hoat_dong_markov(hien_tai: str, enabled_services: dict, da_chay: list) -> str:
    """Lấy hoạt động kế tiếp theo phân phối xác suất Markov có lọc dịch vụ đã bật."""
    transitions = MARKOV_TRANSITIONS.get(hien_tai, MARKOV_TRANSITIONS["start"])
    available = {}
    for act, prob in transitions.items():
        if enabled_services.get(act, False):
            available[act] = prob

    if not available:
        return "youtube"

    # Giảm nhẹ xác suất nếu hoạt động vừa mới chạy ngay trước đó
    for act in list(available.keys()):
        if da_chay and da_chay[-1] == act:
            available[act] *= 0.3

    states = list(available.keys())
    weights = list(available.values())
    return random.choices(states, weights=weights)[0]


def _nghi_giua_hoat_dong(driver, mood: SessionMood):
    """Nghỉ ngẫu nhiên giữa 2 hoạt động — bắt chước cảm xúc người thật."""
    r = random.random()
    if r < 0.05:
        delay(0.5, 2.0)
        return
    if r < 0.15:
        nghi = random.randint(20, 45)
        log(f"  ☕ Nghỉ ngắn giữa phiên {nghi}s...")
        time.sleep(nghi)
    else:
        nghi = random.randint(3, 16)
        log(f"  ⏸ Nghỉ {nghi}s...")
        time.sleep(nghi)
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)


def _thuc_hien_multi_tab(driver, mood: SessionMood):
    """
    Giả lập mở tab phụ tra cứu đa nhiệm (Multitasking),
    xem 10-25s rồi đóng tab phụ và quay về tab chính.
    """
    if random.random() > 0.22:
        return
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from .config import GOOGLE_SEARCH_QUERIES

        main_handle = driver.current_window_handle
        initial_handles = set(driver.window_handles)

        driver.execute_script("window.open('https://www.google.com?hl=en', '_blank');")
        time.sleep(random.uniform(1.2, 2.5))

        new_handles = set(driver.window_handles) - initial_handles
        if not new_handles:
            return

        tab_phu = list(new_handles)[0]
        driver.switch_to.window(tab_phu)
        log("  📑 Mở tab phụ đa nhiệm tra cứu Google...")

        box = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.NAME, "q")))
        q = random.choice(GOOGLE_SEARCH_QUERIES)
        go_co_loi_chinh_ta(box, q)
        box.send_keys(Keys.RETURN)
        time.sleep(random.uniform(6.0, 15.0))
        cuon_tu_nhien(driver, "xuong", random.randint(1, 2))
        time.sleep(random.uniform(2.0, 5.0))

        driver.close()
        driver.switch_to.window(main_handle)
        log("  🔙 Đóng tab phụ, quay về tab chính")
        time.sleep(random.uniform(1.0, 2.0))
    except Exception:
        try:
            if main_handle in driver.window_handles:
                driver.switch_to.window(main_handle)
        except Exception:
            pass


# ── Profile runner ────────────────────────────────────────────────

def xu_ly_profile(profile: dict, gpmdriver_path: str = None, tu_khoa: str = "") -> dict:
    """Chạy 1 profile với Markov Chain Dispatcher & Session Archetype."""
    pid      = profile["id"]
    name     = profile["name"]
    proxy_ip = (profile.get("proxy") or "").split(":")[0] or "no proxy"
    ket_qua  = {
        "ok": False, "video": 0, "shorts": 0, "bai": 0, "google": 0,
        "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0, "ly_do": ""
    }

    # ── Draw session personality & archetype ──────────────────────
    mood = draw_session_mood()

    # Xác định ngân sách thời gian cho session này dựa trên Archetype
    if mood.archetype == SessionArchetype.QUICK_CHECK:
        thoi_luong_max_s = random.randint(300, 720)    # 5 - 12 phút
        max_steps = random.randint(2, 3)
    elif mood.archetype == SessionArchetype.CASUAL_BROWSE:
        thoi_luong_max_s = random.randint(900, 1800)   # 15 - 30 phút
        max_steps = random.randint(4, 6)
    else:  # DEEP_DIVE
        thoi_luong_max_s = random.randint(2100, 3600)  # 35 - 60 phút
        max_steps = random.randint(6, 10)

    _tin_range = list(range(SO_TIN_DOC_MIN, SO_TIN_DOC_MAX + 1))
    so_tin_session = random.choices(
        _tin_range,
        weights=_spread_weights(len(_tin_range), peak_right=False)
    )[0]

    log(f"\n{'='*55}")
    log(f"🚀  Profile: {name}  |  Proxy: {proxy_ip}")
    log(f"    Mood: {mood.name} | Archetype: {mood.archetype.name} (~{thoi_luong_max_s//60} phút)")
    log(f"{'='*55}")

    dong_profile_gpm(pid)
    delay(2, 3)

    log("  ⏳ GPM đang mở profile...")
    driver = mo_profile_gpm(
        pid,
        gpmdriver_path=gpmdriver_path,
        addination_args=GPM_ADDITIONAL_ARGS,
    )

    if not driver:
        ket_qua["ly_do"] = "connect_failed"
        return ket_qua

    log("  ✅ Kết nối thành công!")
    cdp_setup(driver)
    log("  🛡️  CDP: ad blocking + anti-detect + YT ad-skip script đã kích hoạt")
    delay(2, 4)

    t_session_start = time.time()

    try:
        if KIEM_TRA_PROXY:
            log("  🔍 Kiểm tra proxy...")
            if not kiem_tra_proxy_nhanh(driver):
                log("  ❌ Proxy chết — bỏ qua profile")
                ket_qua["ly_do"] = "proxy_dead"
                return ket_qua
            log("  ✅ Proxy OK")

        if TU_DONG_DONG_POPUP:
            dong_popup_tu_dong(driver)

        if not xu_ly_yeu_cau_dang_nhap(driver, profile_name=name):
            ket_qua["ly_do"] = "not_logged_in"
            return ket_qua

        enabled_services = _lay_dich_vu_kha_dung(so_tin_session)
        da_chay = []
        state_hien_tai = "start"

        log(f"  🎲 Khởi động Markov Decision Process (Max {max_steps} bước)...")

        step = 0
        while step < max_steps:
            da_qua = time.time() - t_session_start
            if da_qua >= thoi_luong_max_s:
                log(f"  ⏱️ Đã đạt giới hạn thời gian Archetype ({int(da_qua)}s / {thoi_luong_max_s}s)")
                break

            step += 1
            hoat_dong = _chon_hoat_dong_markov(state_hien_tai, enabled_services, da_chay)
            state_hien_tai = hoat_dong
            da_chay.append(hoat_dong)

            log(f"\n  👉 [Bước {step}/{max_steps}] Thực hiện: {hoat_dong.upper()}")

            # Đảm bảo login
            if can_kiem_tra_login(driver):
                creds = GMAIL_ACCOUNTS.get(name, ())
                if creds and len(creds) == 2:
                    log(f"  🔐 Bị đăng xuất — login lại ({hoat_dong})")
                    if not dang_nhap_google(driver, creds[0], creds[1]):
                        log("  ❌ Login lại thất bại — dừng session")
                        ket_qua["ly_do"] = "relogin_failed"
                        break
                else:
                    log("  ❌ Bị đăng xuất giữa session, không có credentials — dừng")
                    ket_qua["ly_do"] = "logged_out_no_credentials"
                    break

            if hoat_dong == "google":
                so_google = random.randint(SO_GOOGLE_MIN, SO_GOOGLE_MAX)
                ket_qua["google"] += tim_kiem_google(driver, so_google, mood)

            elif hoat_dong == "maps":
                so_maps = random.randint(SO_MAPS_MIN, SO_MAPS_MAX)
                ket_qua["maps"] += luot_google_maps(driver, so_maps, mood)

            elif hoat_dong == "reddit":
                so_reddit = random.randint(SO_REDDIT_MIN, SO_REDDIT_MAX)
                ket_qua["reddit"] += luot_reddit(driver, so_reddit, mood)

            elif hoat_dong == "wiki":
                so_wiki = random.randint(SO_WIKI_MIN, SO_WIKI_MAX)
                ket_qua["wiki"] += luot_wikipedia(driver, so_wiki, mood)

            elif hoat_dong == "youtube":
                so_vid = random.randint(1, 3) if mood.archetype == SessionArchetype.QUICK_CHECK else random.randint(SO_VIDEO_MIN, SO_VIDEO_MAX)
                v_done = xem_youtube(driver, tu_khoa, so_vid, MIN_GIAY_XEM, MAX_GIAY_XEM, mood)
                ket_qua["video"] += v_done
                if v_done == 0 and ket_qua["video"] == 0:
                    log("  ⚠️ YouTube không xem được video nào")

            elif hoat_dong == "shorts":
                so_shorts = random.randint(3, 7)
                ket_qua["shorts"] += luot_youtube_shorts(driver, so_shorts)

            elif hoat_dong == "twitter":
                so_tw = random.randint(SO_TWITTER_MIN, SO_TWITTER_MAX)
                ket_qua["twitter"] += luot_twitter(driver, so_tw, mood)

            elif hoat_dong == "news":
                ket_qua["bai"] += (doc_bao(driver, random.randint(1, 3)) or 0)

            if not kiem_tra_ket_noi(driver):
                log(f"  ❌ Browser đã đóng sau '{hoat_dong}' — dừng session")
                failure = driver_failure_reason(driver)
                ket_qua["ly_do"] = f"browser_crash_after_{hoat_dong}: {failure}"[:120]
                break

            # 22% xác suất multitasking mở tab phụ
            _thuc_hien_multi_tab(driver, mood)

            # Nghỉ ngơi giữa các bước
            if step < max_steps and (time.time() - t_session_start < thoi_luong_max_s):
                _nghi_giua_hoat_dong(driver, mood)

        # Nếu thực hiện được ít nhất 1 hoạt động và không có lỗi crash fatal
        if not ket_qua["ly_do"]:
            ket_qua["ok"] = True

        if ket_qua["ok"]:
            log(
                f"  🎉 Hoàn thành session [{name}] ({' → '.join(da_chay)})"
                f" | video={ket_qua['video']}"
                + (f" | shorts={ket_qua['shorts']}" if ket_qua["shorts"] else "")
                + (f" | news={ket_qua['bai']}" if ket_qua["bai"] else "")
                + (f" | maps={ket_qua['maps']}" if ket_qua["maps"] else "")
                + (f" | reddit={ket_qua['reddit']}" if ket_qua["reddit"] else "")
                + (f" | wiki={ket_qua['wiki']}" if ket_qua["wiki"] else "")
                + (f" | google={ket_qua['google']}" if ket_qua["google"] else "")
                + (f" | twitter={ket_qua['twitter']}" if ket_qua["twitter"] else "")
            )

    except Exception as e:
        log(f"  ❌ Lỗi: {e}")
        ket_qua["ly_do"] = str(e)[:80]

    finally:
        safe_quit(driver)
        dong_profile_gpm(pid)
        delay(2, 4)
        log(f"  🔒 Đã đóng profile [{name}]")

    return ket_qua


def _chay_profile_co_thu_lai(profile: dict, gpmdriver_path: str, tu_khoa: str) -> dict:
    """Chạy 1 profile với cơ chế thử lại tự động khi gặp sự cố."""
    name = profile.get("name", "unknown")
    ket_qua = None
    for lan in range(max(1, THU_LAI_KHI_LOI + 1)):
        if lan > 0:
            cho = random.randint(10, 30)
            log(f"  🔁 [{name}] Thử lại lần {lan}/{THU_LAI_KHI_LOI} sau {cho}s...")
            time.sleep(cho)
        try:
            ket_qua = xu_ly_profile(profile, gpmdriver_path=gpmdriver_path, tu_khoa=tu_khoa)
        except Exception as e:
            log(f"  ❌ [{name}] Exception không bắt được: {e}")
            ket_qua = {
                "ok": False, "video": 0, "bai": 0, "google": 0,
                "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0, "ly_do": str(e)[:60]
            }
        if ket_qua["ok"]:
            break
        if ket_qua.get("ly_do") in ("proxy_dead", "not_logged_in", "profile_path_not_found"):
            break
    return ket_qua or {
        "ok": False, "video": 0, "bai": 0, "google": 0,
        "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0, "ly_do": "no_result"
    }


# ── Main loop ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Script Nuôi Kênh YouTube US & Tối Ưu Cookie Google (GPM API v2)")
    parser.add_argument("-p", "--profile", type=str, default=None, help="Chỉ chạy profile có tên hoặc ID chỉ định")
    parser.add_argument("--proxy", type=str, default=None, help="Cập nhật proxy mới cho profile trước khi chạy")
    parser.add_argument("-l", "--loops", type=int, default=None, help="Số vòng lặp (ghi đè SO_VONG_LAP)")
    args, _ = parser.parse_known_args()

    so_vong_max = args.loops if args.loops is not None else SO_VONG_LAP

    us_hour = datetime.datetime.now(ZoneInfo(MUI_GIO_US)).strftime('%H:%M %Z')
    log("=" * 55)
    log("🤖  Script Nuôi Kênh YouTube — THỊ TRƯỜNG US (GPM API v2)")
    log(f"🌎  Múi giờ US: {MUI_GIO_US} (Hiện tại: {us_hour})")
    log(f"🔄  Vòng lặp  : {'∞ vô hạn' if so_vong_max == 0 else so_vong_max}")
    if args.profile:
        log(f"🎯  Chỉ định  : Profile [{args.profile}]")
    if args.proxy:
        log(f"🌐  Proxy mới : {args.proxy}")
    log(f"⚡  Luồng chạy: {'1 (tuần tự)' if SO_LUONG_CHAY_SONG_SONG <= 1 else f'{SO_LUONG_CHAY_SONG_SONG} (song song)'}")
    log(f"🎬  Video/pro : {SO_VIDEO}  ({MIN_GIAY_XEM}–{MAX_GIAY_XEM}s/video)")
    log(f"📰  Google News: {'Bật' if SU_DUNG_GOOGLE_NEWS else 'Tắt'}")
    log(f"🗺️  Google Maps: {'Bật' if SU_DUNG_GOOGLE_MAPS else 'Tắt'}")
    log(f"👽  Reddit US : {'Bật' if SU_DUNG_REDDIT else 'Tắt'}")
    log(f"📚  Wiki EN   : {'Bật' if SU_DUNG_WIKIPEDIA else 'Tắt'}")
    log(f"🍪  Auto popup: {'Bật' if TU_DONG_DONG_POPUP else 'Tắt'}")
    log(f"🔍  Proxy check: {'Bật' if KIEM_TRA_PROXY else 'Tắt'}")
    log(f"📝  Log file  : {LOG_FILE or 'Tắt'}")
    log("=" * 55)

    start_gpm_dialog_watcher()

    gpmdriver_path = tim_gpmdriver()
    if not gpmdriver_path:
        log("⚠️  Không tìm thấy gpmdriver.exe trong GPM_BROWSER_DIR — sẽ dùng driver do API v2 cấp.")
    else:
        log(f"✅ gpmdriver fallback: {gpmdriver_path}\n")

    vong        = 0
    tong_tat_ca = {
        "ok": 0, "loi": 0, "video": 0, "bai": 0, "google": 0,
        "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0
    }

    while True:
        vong += 1
        if so_vong_max > 0 and vong > so_vong_max:
            break

        tu_khoa           = lay_tu_khoa(vong)
        thoi_diem_bat_dau = time.time()

        log(f"\n{'█'*55}")
        log(f"  VÒNG {vong}{f'/{so_vong_max}' if so_vong_max > 0 else ' (∞)'}  |  Từ khóa: {tu_khoa}")
        log(f"{'█'*55}")

        profiles = lay_tat_ca_profiles()
        if not profiles:
            log("❌ Không có profile nào — thử lại sau 60s...")
            time.sleep(60)
            continue

        if args.profile:
            query = args.profile.strip().lower()
            profiles = [p for p in profiles if query in p.get("name", "").lower() or query == p.get("id", "").lower()]
            if not profiles:
                log(f"❌ Không tìm thấy profile nào khớp với '{args.profile}'!")
                return

        if args.proxy:
            for p in profiles:
                log(f"  🔄 Cập nhật proxy cho [{p.get('name')}]: {args.proxy}")
                cap_nhat_proxy_gpm(p["id"], args.proxy)
                p["proxy"] = args.proxy

        if TRON_PROFILES and not args.profile:
            random.shuffle(profiles)

        log(f"📋 {len(profiles)} profile: {[p['name'] for p in profiles]}\n")

        stats_vong = {
            "ok": 0, "loi": 0, "video": 0, "bai": 0, "google": 0,
            "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0, "chi_tiet_loi": []
        }

        if SO_LUONG_CHAY_SONG_SONG <= 1 or len(profiles) <= 1:
            # ── Chạy tuần tự ───────────────────────────────────────
            for i, profile in enumerate(profiles, 1):
                log(f"\n▶  [{i}/{len(profiles)}] Profile: {profile['name']}")
                ket_qua = _chay_profile_co_thu_lai(profile, gpmdriver_path, tu_khoa)

                if ket_qua and ket_qua["ok"]:
                    stats_vong["ok"]      += 1
                    stats_vong["video"]   += ket_qua.get("video", 0)
                    stats_vong["bai"]     += ket_qua.get("bai", 0)
                    stats_vong["google"]  += ket_qua.get("google", 0)
                    stats_vong["maps"]    += ket_qua.get("maps", 0)
                    stats_vong["reddit"]  += ket_qua.get("reddit", 0)
                    stats_vong["wiki"]    += ket_qua.get("wiki", 0)
                    stats_vong["twitter"] += ket_qua.get("twitter", 0)

                    tong_tat_ca["ok"]      += 1
                    tong_tat_ca["video"]   += ket_qua.get("video", 0)
                    tong_tat_ca["bai"]     += ket_qua.get("bai", 0)
                    tong_tat_ca["google"]  += ket_qua.get("google", 0)
                    tong_tat_ca["maps"]    += ket_qua.get("maps", 0)
                    tong_tat_ca["reddit"]  += ket_qua.get("reddit", 0)
                    tong_tat_ca["wiki"]    += ket_qua.get("wiki", 0)
                    tong_tat_ca["twitter"] += ket_qua.get("twitter", 0)
                else:
                    stats_vong["loi"]  += 1
                    tong_tat_ca["loi"] += 1
                    ly_do = ket_qua.get("ly_do", "unknown") if ket_qua else "exception"
                    stats_vong["chi_tiet_loi"].append((profile["name"], ly_do))

                if i < len(profiles):
                    nghi = random.randint(15, 45)
                    log(f"\n  ⏳ Nghỉ {nghi}s trước profile tiếp theo...")
                    time.sleep(nghi)
        else:
            # ── Chạy đa luồng song song (ThreadPoolExecutor) ──────
            log(f"🚀 Bắt đầu chạy song song {min(SO_LUONG_CHAY_SONG_SONG, len(profiles))} profiles cùng lúc...")
            futures_map = {}
            with ThreadPoolExecutor(max_workers=SO_LUONG_CHAY_SONG_SONG) as executor:
                for idx, profile in enumerate(profiles):
                    if idx > 0:
                        time.sleep(3)  # Giãn cách 3s giữa các lệnh start để tránh nghẽn GPM API
                    f = executor.submit(_chay_profile_co_thu_lai, profile, gpmdriver_path, tu_khoa)
                    futures_map[f] = profile

                for f in as_completed(futures_map):
                    p = futures_map[f]
                    try:
                        ket_qua = f.result()
                    except Exception as e:
                        ket_qua = {
                            "ok": False, "video": 0, "bai": 0, "google": 0,
                            "maps": 0, "reddit": 0, "wiki": 0, "twitter": 0, "ly_do": str(e)[:60]
                        }

                    if ket_qua and ket_qua["ok"]:
                        stats_vong["ok"]      += 1
                        stats_vong["video"]   += ket_qua.get("video", 0)
                        stats_vong["bai"]     += ket_qua.get("bai", 0)
                        stats_vong["google"]  += ket_qua.get("google", 0)
                        stats_vong["maps"]    += ket_qua.get("maps", 0)
                        stats_vong["reddit"]  += ket_qua.get("reddit", 0)
                        stats_vong["wiki"]    += ket_qua.get("wiki", 0)
                        stats_vong["twitter"] += ket_qua.get("twitter", 0)

                        tong_tat_ca["ok"]      += 1
                        tong_tat_ca["video"]   += ket_qua.get("video", 0)
                        tong_tat_ca["bai"]     += ket_qua.get("bai", 0)
                        tong_tat_ca["google"]  += ket_qua.get("google", 0)
                        tong_tat_ca["maps"]    += ket_qua.get("maps", 0)
                        tong_tat_ca["reddit"]  += ket_qua.get("reddit", 0)
                        tong_tat_ca["wiki"]    += ket_qua.get("wiki", 0)
                        tong_tat_ca["twitter"] += ket_qua.get("twitter", 0)
                    else:
                        stats_vong["loi"]  += 1
                        tong_tat_ca["loi"] += 1
                        ly_do = ket_qua.get("ly_do", "unknown") if ket_qua else "exception"
                        stats_vong["chi_tiet_loi"].append((p["name"], ly_do))

        _in_thong_ke(vong, stats_vong, tu_khoa, time.time() - thoi_diem_bat_dau)

        if so_vong_max > 0 and vong >= so_vong_max:
            break

        # Session timing variation — tính theo nhịp sinh học US
        he_so_nghi = _he_so_theo_gio(KHUNG_GIO_NGHI_DAI)
        xs_nghi_dai = min(0.95, NGHI_DAI_XAC_SUAT * he_so_nghi)

        t = random.random()
        if t < xs_nghi_dai:
            # Nghỉ dài 2-4 tiếng (đi ngủ / đi làm việc khác)
            nghi_vong = random.randint(NGHI_DAI_MIN, NGHI_DAI_MAX)
            h = nghi_vong // 3600; m = (nghi_vong % 3600) // 60
            log(f"\n💤 Nghỉ dài {h}h {m}p trước vòng {vong+1} (Giờ US: {_he_so_theo_gio(KHUNG_GIO_NGHI_DAI)}x)...\n")
        elif t < xs_nghi_dai + NGHI_NGAN_XAC_SUAT:
            # 15%: nghỉ rất ngắn 1-3 phút (xem liên tục)
            nghi_vong = random.randint(NGHI_NGAN_MIN, NGHI_NGAN_MAX)
            log(f"\n⚡ Nghỉ ngắn {nghi_vong}s trước vòng {vong+1}...\n")
        else:
            # 77%: nghỉ bình thường 5-15 phút
            nghi_vong = random.randint(NGHI_GIUA_VONG_MIN, NGHI_GIUA_VONG_MAX)
            phut = nghi_vong // 60
            log(f"\n⏸  Nghỉ {phut}p {nghi_vong%60}s trước vòng {vong+1}...\n")
        time.sleep(nghi_vong)

    log("\n" + "█" * 55)
    log("🏁  HOÀN THÀNH TẤT CẢ VÒNG LẶP")
    log(f"    ✅ Tổng thành công : {tong_tat_ca['ok']} profile")
    log(f"    ❌ Tổng lỗi / bỏ  : {tong_tat_ca['loi']} profile")
    log(f"    🎬 Tổng video xem  : {tong_tat_ca['video']} video")
    log(f"    📰 Tổng Google News: {tong_tat_ca['bai']} bài")
    log(f"    🗺️  Tổng Maps       : {tong_tat_ca['maps']} địa điểm")
    log(f"    👽 Tổng Reddit     : {tong_tat_ca['reddit']} bài")
    log(f"    📚 Tổng Wikipedia  : {tong_tat_ca['wiki']} bài")
    log(f"    🔍 Tổng Google     : {tong_tat_ca['google']} trang")
    log(f"    🐦 Tổng Twitter    : {tong_tat_ca['twitter']} bài")
    log("█" * 55)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⛔  Dừng theo yêu cầu người dùng (Ctrl+C)")
