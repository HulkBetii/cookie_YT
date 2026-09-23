# -*- coding: utf-8 -*-
"""FastAPI Backend Server & WebSocket Broadcaster for Control Dashboard."""
import asyncio
import os
import sys
import threading
import time
import webbrowser

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Thêm project root vào path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.log_streamer import log_streamer
from server.task_manager import task_manager
from server.scheduler import scheduler_engine
from server.schemas import (
    ProfileModel, ProxyCheckRequest, ProxyCheckResponse,
    StartProfileRequest, StopProfileRequest, UpdateProfileProxyRequest,
    FarmConfigSchema, SystemStatsResponse, ScheduleJobModel,
    CreateScheduleRequest
)
import nuoi_kenh.config as cfg
from nuoi_kenh.gpm_api import kiem_tra_proxy_nhanh, cap_nhat_proxy_gpm, lay_tat_ca_profiles
from nuoi_kenh.logger import register_log_hook, log


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo hook log stream
    loop = asyncio.get_running_loop()
    log_streamer.set_event_loop(loop)
    register_log_hook(lambda text: log_streamer.emit(text))
    
    # Khởi chạy Scheduler Engine
    scheduler_engine.start()
    
    log("🚀 [Server] FastAPI Control Dashboard Backend đã sẵn sàng!")
    yield
    scheduler_engine.stop()


app = FastAPI(title="YouTube Farm Control Station API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    gpm_ok = False
    try:
        profiles = lay_tat_ca_profiles()
        gpm_ok = isinstance(profiles, list)
    except Exception:
        pass
    return {
        "status": "healthy",
        "gpm_api_connected": gpm_ok,
        "gpm_api_url": cfg.GPM_API_URL
    }


@app.get("/api/system/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    circadian = task_manager.get_circadian_info()
    gpm_ok = False
    total_profiles = 0
    try:
        profiles = lay_tat_ca_profiles()
        gpm_ok = isinstance(profiles, list)
        total_profiles = len(profiles) if gpm_ok else 0
    except Exception:
        pass

    active_count = sum(1 for b in task_manager.running_bots.values() if b["status"] == "RUNNING")
    active_schedules = sum(1 for s in scheduler_engine.get_all() if s.get("enabled"))

    return SystemStatsResponse(
        gpm_connected=gpm_ok,
        gpm_port=19955,
        us_time_est=circadian["us_time_est"],
        circadian_mode=circadian["circadian_mode"],
        circadian_multiplier=circadian["circadian_multiplier"],
        active_bots_count=active_count,
        active_schedules_count=active_schedules,
        total_profiles_count=total_profiles,
        total_videos_watched=task_manager.global_stats["total_videos"],
        total_shorts_watched=task_manager.global_stats["total_shorts"],
        total_news_read=task_manager.global_stats["total_news"],
        total_maps_viewed=task_manager.global_stats["total_maps"],
        total_reddit_read=task_manager.global_stats["total_reddit"],
        total_wiki_read=task_manager.global_stats["total_wiki"],
        total_search_done=task_manager.global_stats["total_search"],
        total_twitter_read=task_manager.global_stats["total_twitter"],
        total_finance_viewed=task_manager.global_stats["total_finance"]
    )


@app.get("/api/profiles", response_model=List[ProfileModel])
async def list_profiles():
    profiles = task_manager.get_all_profiles_with_status()
    return profiles


@app.post("/api/profiles/start")
async def start_profiles(req: StartProfileRequest):
    pids = req.profile_ids
    if not pids:
        # Nếu rỗng, start tất cả
        all_p = lay_tat_ca_profiles()
        pids = [str(p["id"]) for p in all_p]

    ok = task_manager.start_profiles(pids, loop_count=req.loop_count, proxy=req.proxy)
    return {"status": "started" if ok else "failed", "started_count": len(pids)}


@app.post("/api/profiles/stop")
async def stop_profiles(req: StopProfileRequest):
    pids = req.profile_ids
    if not pids:
        # Stop tất cả
        pids = list(task_manager.running_bots.keys())

    task_manager.stop_profiles(pids)
    return {"status": "stopping", "stopped_count": len(pids)}


@app.post("/api/profiles/proxy/update")
async def update_proxy(req: UpdateProfileProxyRequest):
    try:
        cap_nhat_proxy_gpm(req.profile_id, req.proxy)
        return {"ok": True, "profile_id": req.profile_id, "proxy": req.proxy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profiles/proxy/check", response_model=ProxyCheckResponse)
async def check_proxy(req: ProxyCheckRequest):
    proxy_str = req.proxy.strip()
    if not proxy_str:
        return ProxyCheckResponse(ok=False, proxy="", error="Proxy string is empty")

    t0 = time.time()
    ok = kiem_tra_proxy_nhanh(proxy_str, timeout=8)
    ping_ms = int((time.time() - t0) * 1000)

    return ProxyCheckResponse(
        ok=ok,
        proxy=proxy_str,
        ping_ms=ping_ms if ok else 0,
        ip=proxy_str.split(":")[0] if ":" in proxy_str else "",
        country="US" if ok else "",
        city="Fast" if ok else "",
        error="" if ok else "Proxy connection timeout or dead"
    )


# ── Scheduler Endpoints ───────────────────────────────────────────

@app.get("/api/schedules", response_model=List[ScheduleJobModel])
async def list_schedules():
    return scheduler_engine.get_all()


@app.post("/api/schedules", response_model=ScheduleJobModel)
async def create_schedule(req: CreateScheduleRequest):
    job = scheduler_engine.create(req.model_dump())
    return job


@app.put("/api/schedules/{job_id}/toggle", response_model=ScheduleJobModel)
async def toggle_schedule(job_id: str):
    job = scheduler_engine.toggle(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return job


@app.delete("/api/schedules/{job_id}")
async def delete_schedule(job_id: str):
    ok = scheduler_engine.delete(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted", "id": job_id}


@app.post("/api/schedules/{job_id}/run-now")
async def run_schedule_now(job_id: str):
    ok = scheduler_engine.run_now(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "triggered", "id": job_id}


# ── Config Endpoints ──────────────────────────────────────────────

@app.get("/api/config", response_model=FarmConfigSchema)
async def get_config():
    return FarmConfigSchema(
        GPM_API_URL=cfg.GPM_API_URL,
        SO_LUONG_CHAY_SONG_SONG=cfg.SO_LUONG_CHAY_SONG_SONG,
        MUI_GIO_US=cfg.MUI_GIO_US,
        TRON_PROFILES=cfg.TRON_PROFILES,
        SO_VIDEO_MIN=cfg.SO_VIDEO_MIN,
        SO_VIDEO_MAX=cfg.SO_VIDEO_MAX,
        MIN_GIAY_XEM=cfg.MIN_GIAY_XEM,
        MAX_GIAY_XEM=cfg.MAX_GIAY_XEM,
        SU_DUNG_GOOGLE_NEWS=cfg.SU_DUNG_GOOGLE_NEWS,
        SU_DUNG_GOOGLE_MAPS=cfg.SU_DUNG_GOOGLE_MAPS,
        SU_DUNG_REDDIT=cfg.SU_DUNG_REDDIT,
        SU_DUNG_WIKIPEDIA=cfg.SU_DUNG_WIKIPEDIA,
        TIM_KIEM_GOOGLE=cfg.TIM_KIEM_GOOGLE,
        LUOT_TWITTER=cfg.LUOT_TWITTER,
        SU_DUNG_GOOGLE_FINANCE=cfg.SU_DUNG_GOOGLE_FINANCE,
        SO_FINANCE_MIN=cfg.SO_FINANCE_MIN,
        SO_FINANCE_MAX=cfg.SO_FINANCE_MAX,
        DANH_SACH_TU_KHOA=cfg.DANH_SACH_TU_KHOA,
        GOOGLE_KEYWORDS=cfg.GOOGLE_KEYWORDS,
        MAPS_CITIES_QUERIES=cfg.MAPS_CITIES_QUERIES,
        REDDIT_SUBREDDITS=cfg.REDDIT_SUBREDDITS,
        WIKIPEDIA_TOPICS=cfg.WIKIPEDIA_TOPICS,
        FINANCE_TICKERS=cfg.FINANCE_TICKERS,
    )


@app.post("/api/config")
async def update_config(data: FarmConfigSchema):
    # Cập nhật in-memory config
    cfg.SO_LUONG_CHAY_SONG_SONG = data.SO_LUONG_CHAY_SONG_SONG
    cfg.TRON_PROFILES = data.TRON_PROFILES
    cfg.SO_VIDEO_MIN = data.SO_VIDEO_MIN
    cfg.SO_VIDEO_MAX = data.SO_VIDEO_MAX
    cfg.MIN_GIAY_XEM = data.MIN_GIAY_XEM
    cfg.MAX_GIAY_XEM = data.MAX_GIAY_XEM
    cfg.SU_DUNG_GOOGLE_NEWS = data.SU_DUNG_GOOGLE_NEWS
    cfg.SU_DUNG_GOOGLE_MAPS = data.SU_DUNG_GOOGLE_MAPS
    cfg.SU_DUNG_REDDIT = data.SU_DUNG_REDDIT
    cfg.SU_DUNG_WIKIPEDIA = data.SU_DUNG_WIKIPEDIA
    cfg.TIM_KIEM_GOOGLE = data.TIM_KIEM_GOOGLE
    cfg.LUOT_TWITTER = data.LUOT_TWITTER
    cfg.SU_DUNG_GOOGLE_FINANCE = data.SU_DUNG_GOOGLE_FINANCE
    cfg.SO_FINANCE_MIN = data.SO_FINANCE_MIN
    cfg.SO_FINANCE_MAX = data.SO_FINANCE_MAX

    if data.DANH_SACH_TU_KHOA:
        cfg.DANH_SACH_TU_KHOA = data.DANH_SACH_TU_KHOA
    if data.GOOGLE_KEYWORDS:
        cfg.GOOGLE_KEYWORDS = data.GOOGLE_KEYWORDS
        cfg.GOOGLE_SEARCH_QUERIES = data.GOOGLE_KEYWORDS
    if data.MAPS_CITIES_QUERIES:
        cfg.MAPS_CITIES_QUERIES = data.MAPS_CITIES_QUERIES
    if data.REDDIT_SUBREDDITS:
        cfg.REDDIT_SUBREDDITS = data.REDDIT_SUBREDDITS
    if data.WIKIPEDIA_TOPICS:
        cfg.WIKIPEDIA_TOPICS = data.WIKIPEDIA_TOPICS
    if data.FINANCE_TICKERS:
        cfg.FINANCE_TICKERS = data.FINANCE_TICKERS

    log("⚙️ [UI Config] Đã lưu cấu hình mới thành công!")
    return {"status": "saved"}


# ── WebSocket Telemetry ───────────────────────────────────────────

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await log_streamer.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        log_streamer.disconnect(websocket)
    except Exception:
        log_streamer.disconnect(websocket)


# ── Static SPA Mount ──────────────────────────────────────────────

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")


# ── Standalone Launcher ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Farm UI Server")
    parser.add_argument("--port", type=int, default=8088, help="Port to bind server")
    parser.add_argument("--open", action="store_true", help="Automatically open UI in default browser")
    args = parser.parse_args()

    if args.open:
        def _open():
            time.sleep(1.2)
            webbrowser.open(f"http://localhost:{args.port}")
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run("server.app:app", host="127.0.0.1", port=args.port, reload=False)
