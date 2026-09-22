# -*- coding: utf-8 -*-
"""Pydantic schemas for REST API & WebSocket models."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProfileModel(BaseModel):
    id: str
    name: str
    proxy: Optional[str] = ""
    note: Optional[str] = ""
    is_running: bool = False
    current_activity: str = "Idle"
    current_detail: str = ""
    cookie_score: int = 85
    last_run: str = "Never"
    raw: Optional[Dict[str, Any]] = None


class ProxyCheckRequest(BaseModel):
    proxy: str


class ProxyCheckResponse(BaseModel):
    ok: bool
    proxy: str
    ping_ms: int = 0
    ip: str = ""
    country: str = ""
    city: str = ""
    error: str = ""


class StartProfileRequest(BaseModel):
    profile_ids: List[str] = Field(default_factory=list)
    loop_count: int = 1
    proxy: Optional[str] = None
    archetype: Optional[str] = None  # QUICK_CHECK, CASUAL_BROWSE, DEEP_DIVE, or None (Random)


class StopProfileRequest(BaseModel):
    profile_ids: List[str] = Field(default_factory=list)


class UpdateProfileProxyRequest(BaseModel):
    profile_id: str
    proxy: str


class UpdateProfileNoteRequest(BaseModel):
    profile_id: str
    note: str


class FarmConfigSchema(BaseModel):
    # GPM & Threading
    GPM_API_URL: str = "http://127.0.0.1:19955"
    SO_LUONG_CHAY_SONG_SONG: int = 1
    MUI_GIO_US: str = "America/New_York"
    TRON_PROFILES: bool = True

    # YouTube
    SO_VIDEO_MIN: int = 2
    SO_VIDEO_MAX: int = 5
    MIN_GIAY_XEM: int = 60
    MAX_GIAY_XEM: int = 130

    # Modules Enabled
    SU_DUNG_GOOGLE_NEWS: bool = True
    SU_DUNG_GOOGLE_MAPS: bool = True
    SU_DUNG_REDDIT: bool = True
    SU_DUNG_WIKIPEDIA: bool = True
    TIM_KIEM_GOOGLE: bool = True
    LUOT_TWITTER: bool = True
    SU_DUNG_GOOGLE_FINANCE: bool = True

    # Datasets
    DANH_SACH_TU_KHOA: List[str] = Field(default_factory=list)
    GOOGLE_KEYWORDS: List[str] = Field(default_factory=list)
    MAPS_CITIES_QUERIES: List[str] = Field(default_factory=list)
    REDDIT_SUBREDDITS: List[str] = Field(default_factory=list)
    WIKIPEDIA_TOPICS: List[str] = Field(default_factory=list)
    FINANCE_TICKERS: List[str] = Field(default_factory=list)


class LogMessage(BaseModel):
    id: str
    timestamp: str
    level: str  # INFO, SUCCESS, WARN, ERROR, SKIP
    text: str
    profile: str = ""


class SystemStatsResponse(BaseModel):
    gpm_connected: bool
    gpm_port: int
    us_time_est: str
    circadian_mode: str  # SLEEP, ACTIVE, NORMAL
    circadian_multiplier: float
    active_bots_count: int
    total_profiles_count: int
    total_videos_watched: int
    total_news_read: int
    total_maps_viewed: int
    total_reddit_read: int
    total_wiki_read: int
    total_search_done: int
