# -*- coding: utf-8 -*-
"""Logging — ghi stdout + file."""
import time
from .config import LOG_FILE


_log_hooks = []


def register_log_hook(hook_fn):
    """Đăng ký hook nhận log stream (dùng cho WebSocket Server)."""
    if hook_fn not in _log_hooks:
        _log_hooks.append(hook_fn)


def log(msg: str):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    for hook in _log_hooks:
        try:
            hook(line)
        except Exception:
            pass

