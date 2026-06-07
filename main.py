#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuôi Kênh YouTube — GPM Login
Entry point: chạy file này để bắt đầu.
"""
import sys
import time
import datetime
import random
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
    LUOT_YAHOO, SO_YAHOO_MIN, SO_YAHOO_MAX,
    TIM_KIEM_GOOGLE, SO_GOOGLE_MIN, SO_GOOGLE_MAX,
    LUOT_TWITTER, SO_TWITTER_MIN, SO_TWITTER_MAX,
)
from nuoi_kenh.logger import log
from nuoi_kenh.gpm_api import (
    tim_gpmdriver, lay_tat_ca_profiles,
    mo_profile_gpm, dong_profile_gpm, kiem_tra_proxy_nhanh,
)
from nuoi_kenh.cdp import cdp_setup
from nuoi_kenh.human_behavior import delay, draw_session_mood
from nuoi_kenh.news import (
    dong_popup_tu_dong, xu_ly_yeu_cau_dang_nhap, doc_bao,
)
from nuoi_kenh.youtube import xem_youtube
from nuoi_kenh.yahoo import luot_yahoo_japan
from nuoi_kenh.google_search import tim_kiem_google
from nuoi_kenh.twitter import luot_twitter
from nuoi_kenh.gmail_login import can_kiem_tra_login, dang_nhap_google
from nuoi_kenh.config import GMAIL_ACCOUNTS


# ── Keyword rotation ─────────────────────────────────────────────
# Chọn ngẫu nhiên có "bộ nhớ ngắn hạn" — tránh chu kỳ tuần hoàn dự đoán được
# (người thật không quan tâm chủ đề theo đúng vòng lặp cố định) và tránh
# lặp lại ngay từ khóa vừa dùng gần đây.
_TU_KHOA_GAN_DAY: list = []


def lay_tu_khoa(vong: int) -> str:
    if not DANH_SACH_TU_KHOA:
        return "偉人の教え"
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
    log(f"    🎬 Video đã xem: {stats['video']} video")
    log(f"    📰 Bài đã đọc : {stats['bai']} bài")
    if stats.get("yahoo", 0) > 0:
        log(f"    🟡 Yahoo duyệt : {stats['yahoo']} bài")
    if stats.get("google", 0) > 0:
        log(f"    🔍 Google search: {stats['google']} trang")
    if stats.get("twitter", 0) > 0:
        log(f"    🐦 Twitter duyệt: {stats['twitter']} bài")
    if stats["chi_tiet_loi"]:
        log("    Chi tiết lỗi:")
        for ten, ly_do in stats["chi_tiet_loi"]:
            log(f"      • {ten}: {ly_do}")
    log("=" * 55)


# ── Helpers ───────────────────────────────────────────────────────

def _spread_weights(n: int, peak_right: bool = True) -> list:
    """
    Sinh weights hình chuông cho n phần tử — peak ở 60-70% từ trái.
    peak_right=True  → thiên về nửa trên (dùng cho video count).
    peak_right=False → thiên về giữa  (dùng cho article count).
    Không bao giờ crash vì luôn trả về đúng n phần tử.
    """
    if n == 1:
        return [1]
    peak = max(0, min(n - 1, int(n * (0.65 if peak_right else 0.50))))
    w = []
    for i in range(n):
        dist = abs(i - peak)
        w.append(max(1, 10 - dist * 2))
    return w


# ── Circadian rhythm — nhịp sinh học theo giờ trong ngày ──────────

def _he_so_theo_gio(bang: dict, gio: int = None) -> float:
    """Tra hệ số nhân theo khung giờ hiện tại (giờ địa phương máy chạy)."""
    gio = datetime.datetime.now().hour if gio is None else gio
    for (bd, kt), he_so in bang.items():
        if bd <= gio < kt or (bd > kt and (gio >= bd or gio < kt)):
            return he_so
    return 1.0


# ── Session planner ───────────────────────────────────────────────

# Xác suất từng hoạt động được chọn vào session, theo mood
_XS_HOAT_DONG = {
    #           passive  normal  engaged
    "yahoo":   (0.82,    0.70,   0.52),   # passive: lướt Yahoo thoải mái; engaged: bỏ qua để search thẳng
    "google":  (0.20,    0.55,   0.83),   # engaged: tìm kiếm có chủ đích
    "news":    (0.42,    0.63,   0.74),   # engaged: đọc tin nhiều hơn
    "twitter": (0.28,    0.58,   0.80),   # passive ít dùng social; engaged chủ động browse
}


def _ke_hoach_session(mood, so_tin: int) -> list:
    """
    Xây dựng danh sách hoạt động ngẫu nhiên cho session này.
    YouTube luôn có mặt; phần còn lại phụ thuộc mood + xác suất.
    """
    mi = {"passive": 0, "normal": 1, "engaged": 2}.get(mood.name, 1)
    # Ban đêm/giờ làm việc → ít hoạt động phụ hơn; buổi tối → nhiều hơn
    he_so_gio = _he_so_theo_gio(HE_SO_HOAT_DONG_THEO_GIO)

    pool = ["youtube"]   # luôn xem YouTube

    if LUOT_YAHOO and random.random() < min(0.95, _XS_HOAT_DONG["yahoo"][mi] * he_so_gio):
        pool.append("yahoo")
    if TIM_KIEM_GOOGLE and random.random() < min(0.95, _XS_HOAT_DONG["google"][mi] * he_so_gio):
        pool.append("google")
    if LUOT_TWITTER and random.random() < min(0.95, _XS_HOAT_DONG["twitter"][mi] * he_so_gio):
        pool.append("twitter")
    if so_tin > 0 and random.random() < min(0.95, _XS_HOAT_DONG["news"][mi] * he_so_gio):
        pool.append("news")

    random.shuffle(pool)
    return pool


def _nghi_giua_hoat_dong(driver, mood):
    """Nghỉ ngẫu nhiên giữa 2 hoạt động — bắt chước cảm xúc người thật."""
    r = random.random()
    if r < 0.04:
        # Người hứng khởi — chuyển ngay không nghỉ
        delay(0.5, 2.0)
        return
    if r < 0.13:
        # Bị phân tâm (lấy nước, nhìn điện thoại khác, v.v.) — nghỉ dài
        nghi = random.randint(22, 60)
        log(f"  ☕ Nghỉ dài {nghi}s...")
        time.sleep(nghi)
    else:
        # Bình thường — nghỉ 3-20s
        nghi = random.randint(3, 20)
        log(f"  ⏸ Nghỉ {nghi}s...")
        time.sleep(nghi)
    if TU_DONG_DONG_POPUP:
        dong_popup_tu_dong(driver)


# ── Profile runner ────────────────────────────────────────────────

def xu_ly_profile(profile: dict, gpmdriver_path: str, tu_khoa: str) -> dict:
    """Chạy 1 profile: GPM start → xem YouTube → đọc báo → GPM stop."""
    pid      = profile["id"]
    name     = profile["name"]
    proxy_ip = (profile.get("proxy") or "").split(":")[0] or "no proxy"
    ket_qua  = {"ok": False, "video": 0, "bai": 0, "yahoo": 0, "google": 0, "twitter": 0, "ly_do": ""}

    # ── Draw session personality (1 lần/profile) ──────────────────
    mood = draw_session_mood()

    # ── Dynamic video/article count (weighted random) ─────────────
    _vid_range = list(range(SO_VIDEO_MIN, SO_VIDEO_MAX + 1))
    so_video_session = random.choices(
        _vid_range,
        weights=_spread_weights(len(_vid_range), peak_right=True)
    )[0]
    _tin_range = list(range(SO_TIN_DOC_MIN, SO_TIN_DOC_MAX + 1))
    so_tin_session = random.choices(
        _tin_range,
        weights=_spread_weights(len(_tin_range), peak_right=False)
    )[0]

    log(f"\n{'='*55}")
    log(f"🚀  Profile: {name}  |  Proxy: {proxy_ip}")
    log(f"    mood={mood.name} | video={so_video_session} | bài={so_tin_session}")
    log(f"{'='*55}")

    dong_profile_gpm(pid)
    delay(2, 3)

    log("  ⏳ GPM đang mở profile...")
    driver = mo_profile_gpm(pid, gpmdriver_path)

    if not driver:
        ket_qua["ly_do"] = "connect_failed"
        return ket_qua

    log("  ✅ Kết nối thành công!")
    cdp_setup(driver)
    log("  🛡️  CDP: ad blocking + anti-detect + YT ad-skip script đã kích hoạt")
    delay(2, 4)

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

        # ── Lên kế hoạch session ngẫu nhiên ──────────────────────
        ke_hoach = _ke_hoach_session(mood, so_tin_session)
        log(f"    Kế hoạch: {' → '.join(ke_hoach)}")

        # ── Thực hiện từng hoạt động theo thứ tự ngẫu nhiên ──────
        for idx, hoat_dong in enumerate(ke_hoach):
            # Mid-session: Google có thể đá ra trang login bất kỳ lúc nào
            if can_kiem_tra_login(driver):
                creds = GMAIL_ACCOUNTS.get(name, ())
                if creds and len(creds) == 2:
                    log(f"  🔐 Bị đăng xuất giữa session — login lại ({hoat_dong})")
                    if not dang_nhap_google(driver, creds[0], creds[1]):
                        log("  ❌ Login lại thất bại — dừng session")
                        break
                else:
                    log("  ❌ Bị đăng xuất giữa session, không có credentials — dừng")
                    break

            if hoat_dong == "yahoo":
                so_yahoo_session = random.randint(SO_YAHOO_MIN, SO_YAHOO_MAX)
                ket_qua["yahoo"] = luot_yahoo_japan(driver, so_yahoo_session, mood)

            elif hoat_dong == "google":
                so_google_session = random.randint(SO_GOOGLE_MIN, SO_GOOGLE_MAX)
                ket_qua["google"] = tim_kiem_google(driver, so_google_session, mood)

            elif hoat_dong == "youtube":
                ket_qua["video"] = xem_youtube(
                    driver, tu_khoa, so_video_session,
                    MIN_GIAY_XEM, MAX_GIAY_XEM, mood
                )

            elif hoat_dong == "twitter":
                so_twitter_session = random.randint(SO_TWITTER_MIN, SO_TWITTER_MAX)
                ket_qua["twitter"] = luot_twitter(driver, so_twitter_session, mood)

            elif hoat_dong == "news":
                ket_qua["bai"] = doc_bao(driver, so_tin_session) or 0

            # Nghỉ trước hoạt động kế tiếp (không nghỉ sau hoạt động cuối)
            if idx < len(ke_hoach) - 1:
                _nghi_giua_hoat_dong(driver, mood)
        else:
            # for/else: chỉ chạy khi loop kết thúc tự nhiên (không bị break)
            ket_qua["ok"] = True

        if ket_qua["ok"]:
            log(
                f"  🎉 Hoàn thành [{name}]"
                f" | video={ket_qua['video']}"
                f" | bài={ket_qua['bai']}"
                + (f" | yahoo={ket_qua['yahoo']}" if ket_qua["yahoo"] else "")
                + (f" | google={ket_qua['google']}" if ket_qua["google"] else "")
                + (f" | twitter={ket_qua['twitter']}" if ket_qua["twitter"] else "")
            )

    except Exception as e:
        log(f"  ❌ Lỗi: {e}")
        ket_qua["ly_do"] = str(e)[:80]

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        dong_profile_gpm(pid)
        delay(2, 4)
        log(f"  🔒 Đã đóng profile [{name}]")

    return ket_qua


# ── Main loop ────────────────────────────────────────────────────

def main():
    log("=" * 55)
    log("🤖  Script Nuôi Kênh YouTube — AUTO FULL")
    log(f"🔄  Vòng lặp  : {'∞ vô hạn' if SO_VONG_LAP == 0 else SO_VONG_LAP}")
    log(f"🎬  Video/pro : {SO_VIDEO}  ({MIN_GIAY_XEM}–{MAX_GIAY_XEM}s/video)")
    log(f"📰  Tin/pro   : {SO_TIN_DOC}")
    log(f"🍪  Auto popup: {'Bật' if TU_DONG_DONG_POPUP else 'Tắt'}")
    log(f"🔍  Proxy check: {'Bật' if KIEM_TRA_PROXY else 'Tắt'}")
    log(f"📝  Log file  : {LOG_FILE or 'Tắt'}")
    log("=" * 55)

    gpmdriver_path = tim_gpmdriver()
    if not gpmdriver_path:
        log("❌ Không tìm thấy gpmdriver.exe! Kiểm tra GPM_BROWSER_DIR")
        log(f"   Đang tìm trong: {GPM_BROWSER_DIR}")
        sys.exit(1)
    log(f"✅ gpmdriver: {gpmdriver_path}\n")

    vong        = 0
    tong_tat_ca = {"ok": 0, "loi": 0, "video": 0, "bai": 0, "yahoo": 0, "google": 0, "twitter": 0}

    while True:
        vong += 1
        if SO_VONG_LAP > 0 and vong > SO_VONG_LAP:
            break

        tu_khoa           = lay_tu_khoa(vong)
        thoi_diem_bat_dau = time.time()

        log(f"\n{'█'*55}")
        log(f"  VÒNG {vong}{f'/{SO_VONG_LAP}' if SO_VONG_LAP > 0 else ' (∞)'}  |  Từ khóa: {tu_khoa}")
        log(f"{'█'*55}")

        profiles = lay_tat_ca_profiles()
        if not profiles:
            log("❌ Không có profile nào — thử lại sau 60s...")
            time.sleep(60)
            continue

        if TRON_PROFILES:
            random.shuffle(profiles)

        log(f"📋 {len(profiles)} profile: {[p['name'] for p in profiles]}\n")

        stats_vong = {"ok": 0, "loi": 0, "video": 0, "bai": 0, "yahoo": 0, "google": 0, "twitter": 0, "chi_tiet_loi": []}

        for i, profile in enumerate(profiles, 1):
            log(f"\n▶  [{i}/{len(profiles)}] Profile: {profile['name']}")
            ket_qua = None

            for lan in range(max(1, THU_LAI_KHI_LOI + 1)):
                if lan > 0:
                    cho = random.randint(10, 30)
                    log(f"  🔁 Thử lại lần {lan}/{THU_LAI_KHI_LOI} sau {cho}s...")
                    time.sleep(cho)
                try:
                    ket_qua = xu_ly_profile(profile, gpmdriver_path, tu_khoa)
                except Exception as e:
                    log(f"  ❌ Exception không bắt được: {e}")
                    ket_qua = {"ok": False, "video": 0, "bai": 0, "ly_do": str(e)[:60]}
                if ket_qua["ok"]:
                    break
                if ket_qua.get("ly_do") in ("proxy_dead", "not_logged_in",
                                             "profile_path_not_found"):
                    break

            if ket_qua and ket_qua["ok"]:
                stats_vong["ok"]    += 1
                stats_vong["video"] += ket_qua.get("video", 0)
                stats_vong["bai"]   += ket_qua.get("bai", 0)
                stats_vong["yahoo"]   += ket_qua.get("yahoo", 0)
                stats_vong["google"]  += ket_qua.get("google", 0)
                stats_vong["twitter"] += ket_qua.get("twitter", 0)
                tong_tat_ca["ok"]    += 1
                tong_tat_ca["video"] += ket_qua.get("video", 0)
                tong_tat_ca["bai"]   += ket_qua.get("bai", 0)
                tong_tat_ca["yahoo"] += ket_qua.get("yahoo", 0)
                tong_tat_ca["google"] += ket_qua.get("google", 0)
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

        _in_thong_ke(vong, stats_vong, tu_khoa, time.time() - thoi_diem_bat_dau)

        if SO_VONG_LAP > 0 and vong >= SO_VONG_LAP:
            break

        # Session timing variation — người thật không nghỉ đều đặn,
        # và càng không nghỉ đều bất kể giờ giấc trong ngày (circadian gate)
        he_so_nghi = _he_so_theo_gio(KHUNG_GIO_NGHI_DAI)
        xs_nghi_dai = min(0.95, NGHI_DAI_XAC_SUAT * he_so_nghi)

        t = random.random()
        if t < xs_nghi_dai:
            # Nghỉ dài 2-4 tiếng (đi ngủ / đi làm việc khác) — xác suất
            # tăng mạnh vào ban đêm (1h-6h) và giảm vào giờ cao điểm tối
            nghi_vong = random.randint(NGHI_DAI_MIN, NGHI_DAI_MAX)
            h = nghi_vong // 3600; m = (nghi_vong % 3600) // 60
            log(f"\n💤 Nghỉ dài {h}h {m}p trước vòng {vong+1}...\n")
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
    log(f"    📰 Tổng bài đọc   : {tong_tat_ca['bai']} bài")
    log(f"    🟡 Tổng Yahoo      : {tong_tat_ca['yahoo']} bài")
    log(f"    🔍 Tổng Google     : {tong_tat_ca['google']} trang")
    log(f"    🐦 Tổng Twitter    : {tong_tat_ca['twitter']} bài")
    log("█" * 55)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⛔  Dừng theo yêu cầu người dùng (Ctrl+C)")
