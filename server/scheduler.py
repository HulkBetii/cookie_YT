# -*- coding: utf-8 -*-
"""Cron Scheduler Engine — Quản lý lịch chạy tự động theo múi giờ US EST và Local time."""
import json
import time
import uuid
import datetime
import threading
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from pathlib import Path

from nuoi_kenh.config import MUI_GIO_US
from nuoi_kenh.logger import log
from server.task_manager import task_manager

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
SCHEDULES_FILE = DATA_DIR / "schedules.json"

# Giờ US EST mặc định cho các preset
US_PRESET_HOURS = {
    "us_morning": (9, 0, "09:00 AM EST (US Work Start)"),
    "us_afternoon": (14, 0, "02:00 PM EST (US Afternoon Break)"),
    "us_evening": (20, 0, "08:00 PM EST (US Prime Time Entertainment)"),
}


class ScheduleEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs: Dict[str, Dict[str, Any]] = self._load_schedules()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def _load_schedules(self) -> Dict[str, Dict[str, Any]]:
        if SCHEDULES_FILE.exists():
            try:
                with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Tính lại next_run cho các job
                    for j in loaded.values():
                        j["next_run"] = self._calculate_next_run(j)
                    return loaded
            except Exception as e:
                log(f"⚠️ Lỗi load schedules: {e}")
        return self._get_default_presets()

    def _get_default_presets(self) -> Dict[str, Dict[str, Any]]:
        """Tạo sẵn 2 preset mặc định giờ Mỹ."""
        jobs = {}
        # Preset 1: Giờ giải trí tối Mỹ (8h tối EST)
        j1_id = str(uuid.uuid4())[:8]
        j1 = {
            "id": j1_id,
            "name": "US Prime Time (08:00 PM EST)",
            "enabled": False,
            "profile_ids": [],
            "schedule_type": "us_preset",
            "preset_name": "us_evening",
            "time_str": "20:00",
            "interval_minutes": 0,
            "timezone_mode": "US_EST",
            "loop_count": 1,
            "last_run": "Never",
            "next_run": "",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        j1["next_run"] = self._calculate_next_run(j1)
        jobs[j1_id] = j1

        # Preset 2: Giờ sáng Mỹ (9h sáng EST)
        j2_id = str(uuid.uuid4())[:8]
        j2 = {
            "id": j2_id,
            "name": "US Morning Routine (09:00 AM EST)",
            "enabled": False,
            "profile_ids": [],
            "schedule_type": "us_preset",
            "preset_name": "us_morning",
            "time_str": "09:00",
            "interval_minutes": 0,
            "timezone_mode": "US_EST",
            "loop_count": 1,
            "last_run": "Never",
            "next_run": "",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        j2["next_run"] = self._calculate_next_run(j2)
        jobs[j2_id] = j2
        return jobs

    def _save_schedules(self):
        try:
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"⚠️ Không thể lưu schedules: {e}")

    def _calculate_next_run(self, job: Dict[str, Any]) -> str:
        """Tính thời điểm chạy tiếp theo theo định dạng chuẩn."""
        if not job.get("enabled", True):
            return "Disabled"

        stype = job.get("schedule_type", "us_preset")
        tz_name = MUI_GIO_US if job.get("timezone_mode") == "US_EST" else None

        try:
            now = datetime.datetime.now(ZoneInfo(tz_name) if tz_name else None)

            if stype == "interval":
                minutes = job.get("interval_minutes", 60)
                if minutes <= 0:
                    minutes = 60
                next_dt = now + datetime.timedelta(minutes=minutes)
                return next_dt.strftime("%Y-%m-%d %H:%M:%S") + (" EST" if tz_name else " Local")

            target_hour = 9
            target_min = 0

            if stype == "us_preset":
                pname = job.get("preset_name", "us_evening")
                if pname in US_PRESET_HOURS:
                    target_hour, target_min, _ = US_PRESET_HOURS[pname]
            elif stype == "daily_time":
                t_str = job.get("time_str", "09:00")
                parts = t_str.split(":")
                target_hour = int(parts[0])
                target_min = int(parts[1]) if len(parts) > 1 else 0

            target_dt = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)

            return target_dt.strftime("%Y-%m-%d %H:%M:%S") + (" EST" if tz_name else " Local")
        except Exception:
            return "Pending Calculation"

    def start(self):
        """Khởi chạy background scheduler watcher."""
        with self.lock:
            if self.is_running:
                return
            self.is_running = True
            self._thread = threading.Thread(target=self._loop, daemon=True, name="Scheduler-Engine")
            self._thread.start()
            log("📅 [Scheduler] Engine lập lịch tự động đã khởi động!")

    def stop(self):
        with self.lock:
            self.is_running = False

    def _loop(self):
        while self.is_running:
            try:
                self._check_triggers()
            except Exception as e:
                log(f"⚠️ [Scheduler] Lỗi loop: {e}")
            time.sleep(15)

    def _check_triggers(self):
        with self.lock:
            jobs_to_run = []
            for jid, job in self.jobs.items():
                if not job.get("enabled"):
                    continue

                tz_name = MUI_GIO_US if job.get("timezone_mode") == "US_EST" else None
                try:
                    now = datetime.datetime.now(ZoneInfo(tz_name) if tz_name else None)
                    stype = job.get("schedule_type", "us_preset")

                    should_trigger = False

                    if stype in ("us_preset", "daily_time"):
                        target_h = 9
                        target_m = 0
                        if stype == "us_preset":
                            pname = job.get("preset_name", "us_evening")
                            if pname in US_PRESET_HOURS:
                                target_h, target_m, _ = US_PRESET_HOURS[pname]
                        else:
                            parts = job.get("time_str", "09:00").split(":")
                            target_h = int(parts[0])
                            target_m = int(parts[1]) if len(parts) > 1 else 0

                        # Kích hoạt nếu đúng giờ, phút và chưa chạy trong 60 giây qua
                        if now.hour == target_h and now.minute == target_m:
                            last_run_str = job.get("last_run", "")
                            # Kiểm tra xem hôm nay đã chạy chưa
                            today_str = now.strftime("%Y-%m-%d")
                            if today_str not in last_run_str:
                                should_trigger = True

                    elif stype == "interval":
                        last_ts = job.get("_last_trigger_ts", 0)
                        interval_s = max(60, job.get("interval_minutes", 60) * 60)
                        if time.time() - last_ts >= interval_s:
                            should_trigger = True

                    if should_trigger:
                        job["_last_trigger_ts"] = time.time()
                        job["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S") + (" EST" if tz_name else " Local")
                        job["next_run"] = self._calculate_next_run(job)
                        jobs_to_run.append(dict(job))
                except Exception as e:
                    log(f"⚠️ [Scheduler] Lỗi check trigger job {jid}: {e}")

            if jobs_to_run:
                self._save_schedules()

        # Thực thi jobs ngoài lock
        for j in jobs_to_run:
            self._execute_job(j)

    def _execute_job(self, job: Dict[str, Any]):
        pids = job.get("profile_ids") or []
        loops = job.get("loop_count", 1)
        name = job.get("name", "Unnamed Schedule")
        log(f"\n⏰ [Scheduler Trigger] Kích hoạt lịch: '{name}' | Profiles: {pids or 'Tất cả'} | Vòng lặp: {loops}")
        task_manager.start_profiles(pids, loop_count=loops)

    # ── CRUD APIs ─────────────────────────────────────────────────────

    def get_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            # Refresh next_run
            for j in self.jobs.values():
                j["next_run"] = self._calculate_next_run(j)
            return list(self.jobs.values())

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            jid = str(uuid.uuid4())[:8]
            job = {
                "id": jid,
                "name": data.get("name") or "New Schedule",
                "enabled": data.get("enabled", True),
                "profile_ids": data.get("profile_ids") or [],
                "schedule_type": data.get("schedule_type") or "us_preset",
                "preset_name": data.get("preset_name") or "us_evening",
                "time_str": data.get("time_str") or "20:00",
                "interval_minutes": data.get("interval_minutes") or 60,
                "timezone_mode": data.get("timezone_mode") or "US_EST",
                "loop_count": data.get("loop_count") or 1,
                "last_run": "Never",
                "next_run": "",
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            job["next_run"] = self._calculate_next_run(job)
            self.jobs[jid] = job
            self._save_schedules()
            log(f"📅 [Scheduler] Đã tạo lịch mới: '{job['name']}' (ID: {jid})")
            return job

    def toggle(self, jid: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if jid in self.jobs:
                self.jobs[jid]["enabled"] = not self.jobs[jid]["enabled"]
                self.jobs[jid]["next_run"] = self._calculate_next_run(self.jobs[jid])
                self._save_schedules()
                status_str = "BẬT" if self.jobs[jid]["enabled"] else "TẮT"
                log(f"📅 [Scheduler] Đã {status_str} lịch: '{self.jobs[jid]['name']}'")
                return self.jobs[jid]
        return None

    def delete(self, jid: str) -> bool:
        with self.lock:
            if jid in self.jobs:
                name = self.jobs[jid]["name"]
                del self.jobs[jid]
                self._save_schedules()
                log(f"📅 [Scheduler] Đã xóa lịch: '{name}'")
                return True
        return False

    def run_now(self, jid: str) -> bool:
        with self.lock:
            if jid in self.jobs:
                job_copy = dict(self.jobs[jid])
                # Async run
                threading.Thread(target=self._execute_job, args=(job_copy,), daemon=True).start()
                return True
        return False


# Global singleton
scheduler_engine = ScheduleEngine()
