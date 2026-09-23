# -*- coding: utf-8 -*-
"""Thread-safe background Task Manager for controlling automation bots with realistic Heuristic Cookie Scoring."""
import os
import json
import datetime
import threading
import time
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo
from pathlib import Path

from nuoi_kenh.gpm_api import lay_tat_ca_profiles, dong_profile_gpm, cap_nhat_proxy_gpm
from nuoi_kenh.config import MUI_GIO_US, KHUNG_GIO_NGHI_DAI
from nuoi_kenh.logger import log

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "profile_history.json"


class TaskManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.running_bots: Dict[str, Dict[str, Any]] = {}
        self.global_stats = {
            "total_videos": 0,
            "total_shorts": 0,
            "total_news": 0,
            "total_maps": 0,
            "total_reddit": 0,
            "total_wiki": 0,
            "total_search": 0,
            "total_twitter": 0,
            "total_finance": 0,
        }
        self.profile_history: Dict[str, Dict[str, Any]] = self._load_profile_history()

    def _load_profile_history(self) -> Dict[str, Dict[str, Any]]:
        """Tải lịch sử hoạt động của từng profile từ disk."""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_profile_history(self):
        """Lưu lịch sử hoạt động ra file JSON."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profile_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"⚠️ Không thể lưu profile history: {e}")

    def calculate_cookie_score(self, pid: str, proxy: str = "") -> int:
        """
        Tính điểm Cookie Trust Score Heuristic dựa trên dữ liệu thật:
        - Base: 65 điểm
        - Có proxy sống/gán proxy: +10 điểm
        - Số sessions đã hoàn thành: +3 điểm/session (tối đa +15)
        - Video & Shorts đã xem: +1.5 điểm/video (tối đa +10)
        - Đa dạng nền tảng (News, Maps, Reddit, Wiki, Finance, Twitter): +2 điểm mỗi nền tảng (tối đa +12)
        - Khung giờ hoạt động chuẩn US (6h - 24h EST): +5 điểm
        - Capped max 99.
        """
        score = 65
        if proxy and len(proxy.strip()) > 6:
            score += 10

        hist = self.profile_history.get(pid, {})
        sessions = hist.get("sessions_completed", 0)
        score += min(15, sessions * 3)

        videos = hist.get("videos_watched", 0) + hist.get("shorts_watched", 0)
        score += min(10, int(videos * 1.5))

        # Đa dạng nền tảng
        diversity = 0
        for act in ["news", "maps", "reddit", "wiki", "finance", "twitter", "search"]:
            if hist.get(f"{act}_count", 0) > 0:
                diversity += 2
        score += min(12, diversity)

        # Circadian bonus
        try:
            now_est = datetime.datetime.now(ZoneInfo(MUI_GIO_US))
            if 6 <= now_est.hour <= 23:
                score += 5
        except Exception:
            pass

        return min(99, max(60, score))

    def get_circadian_info(self) -> Dict[str, Any]:
        """Tính toán trạng thái nhịp sinh học theo múi giờ US EST."""
        try:
            now_est = datetime.datetime.now(ZoneInfo(MUI_GIO_US))
            hour = now_est.hour
            time_str = now_est.strftime("%I:%M %p %Z")

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
        """Lấy danh sách profiles từ GPM và enrich thêm trạng thái runtime & trust score thật."""
        raw_profiles = lay_tat_ca_profiles()
        enriched = []
        with self.lock:
            for p in raw_profiles:
                pid = str(p.get("id", ""))
                pname = str(p.get("name", ""))
                is_running = pid in self.running_bots and self.running_bots[pid]["status"] == "RUNNING"
                proxy_str = p.get("proxy") or ""

                score = self.calculate_cookie_score(pid, proxy_str)
                last_run = self.profile_history.get(pid, {}).get("last_run_time", "Never")
                if pid in self.running_bots and self.running_bots[pid].get("last_run"):
                    last_run = self.running_bots[pid]["last_run"]

                info = {
                    "id": pid,
                    "name": pname,
                    "proxy": proxy_str,
                    "note": p.get("note") or "",
                    "is_running": is_running,
                    "current_activity": self.running_bots[pid]["current_activity"] if is_running else "Idle",
                    "current_detail": self.running_bots[pid]["current_detail"] if is_running else "",
                    "cookie_score": score,
                    "last_run": last_run,
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
                    "stats": {"video": 0, "shorts": 0, "news": 0, "maps": 0, "reddit": 0, "wiki": 0, "search": 0, "finance": 0, "twitter": 0}
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
                
                # Cập nhật stats & profile history
                if ket_qua and isinstance(ket_qua, dict) and ket_qua.get("ok"):
                    with self.lock:
                        self.global_stats["total_videos"] += ket_qua.get("video", 0)
                        self.global_stats["total_shorts"] += ket_qua.get("shorts", 0)
                        self.global_stats["total_news"] += ket_qua.get("bai", 0)
                        self.global_stats["total_maps"] += ket_qua.get("maps", 0)
                        self.global_stats["total_reddit"] += ket_qua.get("reddit", 0)
                        self.global_stats["total_wiki"] += ket_qua.get("wiki", 0)
                        self.global_stats["total_search"] += ket_qua.get("google", 0)
                        self.global_stats["total_twitter"] += ket_qua.get("twitter", 0)
                        self.global_stats["total_finance"] += ket_qua.get("finance", 0)

                        # Update persistent history
                        hist = self.profile_history.setdefault(pid, {
                            "name": name,
                            "sessions_completed": 0,
                            "videos_watched": 0,
                            "shorts_watched": 0,
                            "news_count": 0,
                            "maps_count": 0,
                            "reddit_count": 0,
                            "wiki_count": 0,
                            "search_count": 0,
                            "finance_count": 0,
                            "twitter_count": 0,
                            "last_run_time": ""
                        })
                        hist["sessions_completed"] += 1
                        hist["videos_watched"] += ket_qua.get("video", 0)
                        hist["shorts_watched"] += ket_qua.get("shorts", 0)
                        hist["news_count"] += ket_qua.get("bai", 0)
                        hist["maps_count"] += ket_qua.get("maps", 0)
                        hist["reddit_count"] += ket_qua.get("reddit", 0)
                        hist["wiki_count"] += ket_qua.get("wiki", 0)
                        hist["search_count"] += ket_qua.get("google", 0)
                        hist["finance_count"] += ket_qua.get("finance", 0)
                        hist["twitter_count"] += ket_qua.get("twitter", 0)
                        hist["last_run_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self._save_profile_history()

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
