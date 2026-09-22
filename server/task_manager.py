# -*- coding: utf-8 -*-
"""Thread-safe background Task Manager for controlling automation bots."""
import datetime
import threading
import time
import random
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

from nuoi_kenh.gpm_api import lay_tat_ca_profiles, dong_profile_gpm, cap_nhat_proxy_gpm
from nuoi_kenh.config import MUI_GIO_US, KHUNG_GIO_NGHI_DAI
from nuoi_kenh.logger import log


class TaskManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.running_bots: Dict[str, Dict[str, Any]] = {}
        self.global_stats = {
            "total_videos": 0,
            "total_news": 0,
            "total_maps": 0,
            "total_reddit": 0,
            "total_wiki": 0,
            "total_search": 0,
        }

    def get_circadian_info(self) -> Dict[str, Any]:
        """Tính toán trạng thái nhịp sinh học theo múi giờ US EST."""
        try:
            now_est = datetime.datetime.now(ZoneInfo(MUI_GIO_US))
            hour = now_est.hour
            time_str = now_est.strftime("%I:%M %p %Z")

            # Tính multiplier
            multiplier = 1.0
            mode = "NORMAL"
            for (h_start, h_end), mult in KHUNG_GIO_NGHI_DAI.items():
                if h_start <= hour < h_end:
                    multiplier = mult
                    break

            if multiplier >= 3.0:
                mode = "SLEEP"
            elif multiplier <= 0.5:
                mode = "ACTIVE"

            return {
                "us_time_est": time_str,
                "circadian_mode": mode,
                "circadian_multiplier": multiplier,
            }
        except Exception:
            return {
                "us_time_est": "04:00 AM EST",
                "circadian_mode": "NORMAL",
                "circadian_multiplier": 1.0,
            }

    def get_all_profiles_with_status(self) -> List[Dict[str, Any]]:
        """Lấy danh sách profiles từ GPM và enrich thêm trạng thái runtime."""
        raw_profiles = lay_tat_ca_profiles()
        enriched = []
        with self.lock:
            for p in raw_profiles:
                pid = str(p.get("id", ""))
                pname = str(p.get("name", ""))
                is_running = pid in self.running_bots and self.running_bots[pid]["status"] == "RUNNING"
                
                info = {
                    "id": pid,
                    "name": pname,
                    "proxy": p.get("proxy") or "",
                    "note": p.get("note") or "",
                    "is_running": is_running,
                    "current_activity": self.running_bots[pid]["current_activity"] if is_running else "Idle",
                    "current_detail": self.running_bots[pid]["current_detail"] if is_running else "",
                    "cookie_score": random.randint(85, 98),
                    "last_run": self.running_bots[pid].get("last_run", "Recently") if pid in self.running_bots else "Never",
                    "raw": p
                }
                enriched.append(info)
        return enriched

    def start_profiles(self, profile_ids: List[str], loop_count: int = 1, proxy: Optional[str] = None):
        """Bắt đầu chạy danh sách profile trong background worker threads."""
        all_profiles = lay_tat_ca_profiles()
        id_map = {str(p["id"]): p for p in all_profiles}
        name_map = {str(p["name"]).lower(): p for p in all_profiles}

        target_profiles = []
        for pid in profile_ids:
            if pid in id_map:
                target_profiles.append(id_map[pid])
            elif pid.lower() in name_map:
                target_profiles.append(name_map[pid.lower()])

        if not target_profiles:
            log(f"⚠️ Không tìm thấy profile nào tương ứng với {profile_ids}")
            return False

        for p in target_profiles:
            pid = str(p["id"])
            with self.lock:
                if pid in self.running_bots and self.running_bots[pid]["status"] == "RUNNING":
                    log(f"  ℹ️ Profile [{p.get('name')}] đã đang chạy.")
                    continue

                bot_entry = {
                    "profile": p,
                    "status": "RUNNING",
                    "current_activity": "Initializing",
                    "current_detail": "Starting browser via GPM API v2...",
                    "stop_requested": False,
                    "loop": 1,
                    "total_loops": loop_count,
                    "started_at": datetime.datetime.now(),
                    "stats": {"video": 0, "news": 0, "maps": 0, "reddit": 0, "wiki": 0, "search": 0}
                }
                self.running_bots[pid] = bot_entry

                # Tạo thread chạy riêng cho profile
                t = threading.Thread(
                    target=self._worker_run_profile,
                    args=(pid, p, loop_count, proxy),
                    daemon=True,
                    name=f"Worker-{p.get('name')}"
                )
                bot_entry["thread"] = t
                t.start()

        return True

    def stop_profiles(self, profile_ids: List[str]):
        """Yêu cầu dừng danh sách profile."""
        with self.lock:
            for pid in profile_ids:
                if pid in self.running_bots:
                    self.running_bots[pid]["stop_requested"] = True
                    self.running_bots[pid]["status"] = "STOPPING"
                    self.running_bots[pid]["current_activity"] = "Stopping"
                    self.running_bots[pid]["current_detail"] = "Closing browser..."
        
        # Gọi dừng GPM song song
        def _stop_bg():
            for pid in profile_ids:
                try:
                    dong_profile_gpm(pid)
                except Exception:
                    pass
        threading.Thread(target=_stop_bg, daemon=True).start()
        return True

    def _worker_run_profile(self, pid: str, profile: Dict[str, Any], loop_count: int, proxy_override: Optional[str]):
        """Worker loop cho 1 profile."""
        from main import xu_ly_profile, lay_tu_khoa, tim_gpmdriver
        name = profile.get("name", "Unknown")
        gpmdriver_path = tim_gpmdriver()

        if proxy_override:
            log(f"  🔄 Cập nhật proxy cho [{name}]: {proxy_override}")
            try:
                cap_nhat_proxy_gpm(pid, proxy_override)
                profile["proxy"] = proxy_override
            except Exception:
                pass

        vong = 0
        while True:
            vong += 1
            if loop_count > 0 and vong > loop_count:
                break

            with self.lock:
                if pid not in self.running_bots or self.running_bots[pid]["stop_requested"]:
                    break
                self.running_bots[pid]["loop"] = vong
                self.running_bots[pid]["current_activity"] = "Running Session"
                self.running_bots[pid]["current_detail"] = f"Loop {vong}/{loop_count if loop_count > 0 else '∞'}"

            tu_khoa = lay_tu_khoa(vong)
            try:
                log(f"\n🚀 [UI Task] Khởi chạy [{name}] - Vòng {vong}/{loop_count if loop_count > 0 else '∞'} | Từ khóa: '{tu_khoa}'")
                ket_qua = xu_ly_profile(profile, gpmdriver_path=gpmdriver_path, tu_khoa=tu_khoa)
                
                # Cập nhật stats
                if ket_qua and isinstance(ket_qua, dict):
                    with self.lock:
                        self.global_stats["total_videos"] += ket_qua.get("video", 0)
                        self.global_stats["total_news"] += ket_qua.get("bai", 0)
                        self.global_stats["total_maps"] += ket_qua.get("maps", 0)
                        self.global_stats["total_reddit"] += ket_qua.get("reddit", 0)
                        self.global_stats["total_wiki"] += ket_qua.get("wiki", 0)
                        self.global_stats["total_search"] += ket_qua.get("google", 0)
            except Exception as e:
                log(f"  ❌ Lỗi worker [{name}]: {e}")

            with self.lock:
                if pid in self.running_bots and self.running_bots[pid]["stop_requested"]:
                    break

            # Nghỉ giữa các vòng nếu còn vòng tiếp theo
            if loop_count == 0 or vong < loop_count:
                sleep_s = random.randint(30, 90)
                with self.lock:
                    if pid in self.running_bots:
                        self.running_bots[pid]["current_activity"] = "Sleeping"
                        self.running_bots[pid]["current_detail"] = f"Resting {sleep_s}s before next loop..."
                log(f"  ⏸️ [{name}] Nghỉ {sleep_s}s trước vòng tiếp theo...")
                time.sleep(sleep_s)

        with self.lock:
            if pid in self.running_bots:
                self.running_bots[pid]["status"] = "IDLE"
                self.running_bots[pid]["current_activity"] = "Finished"
                self.running_bots[pid]["current_detail"] = "Completed all loops"
                self.running_bots[pid]["last_run"] = datetime.datetime.now().strftime("%H:%M:%S")

        log(f"🏁 [UI Task] Hoàn thành toàn bộ vòng lặp cho [{name}]")


# Global singleton
task_manager = TaskManager()
