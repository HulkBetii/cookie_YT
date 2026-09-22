# -*- coding: utf-8 -*-
"""WebSocket Log Streamer & Broadcaster with in-memory ring buffer."""
import asyncio
import datetime
import re
import uuid
from typing import List, Set, Dict, Any
from starlette.websockets import WebSocket


class LogStreamer:
    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.connections: Set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        # Gửi toàn bộ lịch sử log gần đây
        if self.history:
            try:
                await websocket.send_json({
                    "type": "HISTORY",
                    "data": self.history
                })
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    def _determine_level(self, text: str) -> str:
        t = text.lower()
        if "✅" in text or "pass" in t or "hoàn thành" in t or "sẵn sàng" in t:
            return "SUCCESS"
        elif "❌" in text or "fail" in t or "lỗi" in t or "exception" in t or "crash" in t:
            return "ERROR"
        elif "⚠️" in text or "warn" in t or "timeout" in t:
            return "WARN"
        elif "⏭" in text or "skip" in t:
            return "SKIP"
        return "INFO"

    def emit(self, text: str, profile: str = ""):
        """Nhận log string từ logger.py và broadcast ra các WebSocket."""
        # Trích xuất timestamp nếu có dạng [HH:MM:SS]
        ts_match = re.match(r"^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)", text)
        if ts_match:
            timestamp = ts_match.group(1)
            clean_text = ts_match.group(2)
        else:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            clean_text = text

        level = self._determine_level(clean_text)
        log_entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": timestamp,
            "level": level,
            "text": clean_text,
            "profile": profile,
        }

        self.history.append(log_entry)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Broadcast tới tất cả WebSocket đang kết nối
        if self.connections:
            msg = {
                "type": "LOG",
                "data": log_entry
            }
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._broadcast_async(msg), self._loop)

    async def _broadcast_async(self, msg: Dict[str, Any]):
        dead_ws = set()
        for ws in list(self.connections):
            try:
                await ws.send_json(msg)
            except Exception:
                dead_ws.add(ws)
        for ws in dead_ws:
            self.connections.discard(ws)


# Global singleton
log_streamer = LogStreamer()
