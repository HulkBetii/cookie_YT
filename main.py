#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuôi Kênh YouTube — GPM Login
Entry point: chạy file này để bắt đầu.
"""
import sys
import time
import random
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from nuoi_kenh.config import (
    SO_VIDEO, MIN_GIAY_XEM, MAX_GIAY_XEM, SO_TIN_DOC,
    SO_VONG_LAP, NGHI_GIUA_VONG_MIN, NGHI_GIUA_VONG_MAX,
    TRON_PROFILES, DANH_SACH_TU_KHOA, TU_DONG_DONG_POPUP,
    KIEM_TRA_PROXY, THU_LAI_KHI_LOI, LOG_FILE, GPM_BROWSER_DIR,
)
from nuoi_kenh.logger import log
from nuoi_kenh.gpm_api import (
    tim_gpmdriver, lay_tat_ca_profiles,
    mo_profile_gpm, dong_profile_gpm, kiem_tra_proxy_nhanh,
)
from nuoi_kenh.cdp import cdp_setup
from nuoi_kenh.human_behavior import delay
from nuoi_kenh.news import (
    dong_popup_tu_dong, xu_ly_yeu_cau_dang_nhap, doc_bao,
)
from nuoi_kenh.youtube import xem_youtube


# ── Keyword rotation ─────────────────────────────────────────────

def lay_tu_khoa(vong: int) -> str:
    if not DANH_SACH_TU_KHOA:
        return "偉人の教え"
    return DANH_SACH_TU_KHOA[(vong - 1) % len(DANH_SACH_TU_KHOA)]


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
    if stats["chi_tiet_loi"]:
        log("    Chi tiết lỗi:")
        for ten, ly_do in stats["chi_tiet_loi"]:
            log(f"      • {ten}: {ly_do}")
    log("=" * 55)


# ── Profile runner ────────────────────────────────────────────────

def xu_ly_profile(profile: dict, gpmdriver_path: str, tu_khoa: str) -> dict:
    """Chạy 1 profile: GPM start → xem YouTube → đọc báo → GPM stop."""
    pid      = profile["id"]
    name     = profile["name"]
    proxy_ip = (profile.get("proxy") or "").split(":")[0] or "no proxy"
    ket_qua  = {"ok": False, "video": 0, "bai": 0, "ly_do": ""}

    log(f"\n{'='*55}")
    log(f"🚀  Profile: {name}  |  Proxy: {proxy_ip}")
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

        if not xu_ly_yeu_cau_dang_nhap(driver):
            ket_qua["ly_do"] = "not_logged_in"
            return ket_qua

        so_video_xem = xem_youtube(driver, tu_khoa, SO_VIDEO, MIN_GIAY_XEM, MAX_GIAY_XEM)
        ket_qua["video"] = so_video_xem

        if TU_DONG_DONG_POPUP:
            dong_popup_tu_dong(driver)

        nghi = random.randint(5, 15)
        log(f"  ⏸ Nghỉ {nghi}s trước khi đọc báo...")
        time.sleep(nghi)

        so_bai_doc = doc_bao(driver, SO_TIN_DOC) or 0
        ket_qua["bai"] = so_bai_doc

        ket_qua["ok"] = True
        log(f"  🎉 Hoàn thành [{name}] | {so_video_xem} video | {so_bai_doc} bài")

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
    tong_tat_ca = {"ok": 0, "loi": 0, "video": 0, "bai": 0}

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

        stats_vong = {"ok": 0, "loi": 0, "video": 0, "bai": 0, "chi_tiet_loi": []}

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
                tong_tat_ca["ok"]   += 1
                tong_tat_ca["video"]+= ket_qua.get("video", 0)
                tong_tat_ca["bai"]  += ket_qua.get("bai", 0)
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
    log("█" * 55)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⛔  Dừng theo yêu cầu người dùng (Ctrl+C)")
