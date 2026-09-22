# -*- coding: utf-8 -*-
"""
Tự động bấm OK khi GPM-Login hiển thị dialog "Timeout (APP)".
Chạy script này trước khi khởi động GPM-Login.
"""
import ctypes
import ctypes.wintypes
import time

user32 = ctypes.windll.user32
BM_CLICK = 0x00F5
EnumWindowsProc  = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
EnumChildProc    = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)


def _get_text(hwnd: int) -> str:
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _click_ok_in_window(parent_hwnd: int) -> bool:
    """Tìm nút OK trong cửa sổ parent và click. Trả về True nếu đã click."""
    clicked = [False]

    def on_child(hwnd, _):
        if clicked[0]:
            return False
        txt = _get_text(hwnd)
        if txt in ("OK", "Ok"):
            user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
            clicked[0] = True
            return False
        return True

    user32.EnumChildWindows(parent_hwnd, EnumChildProc(on_child), 0)
    return clicked[0]


_dismissed = set()


def scan_once():
    def on_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        if hwnd in _dismissed:
            return True

        found_timeout = [False]

        def on_child(child_hwnd, _):
            txt = _get_text(child_hwnd)
            if "Timeout" in txt or "timeout" in txt:
                found_timeout[0] = True
                return False
            return True

        user32.EnumChildWindows(hwnd, EnumChildProc(on_child), 0)

        if found_timeout[0]:
            if _click_ok_in_window(hwnd):
                title = _get_text(hwnd) or "(no title)"
                print(f"[{time.strftime('%H:%M:%S')}] ✅ Đã bấm OK trên dialog '{title}'")
                _dismissed.add(hwnd)

        return True

    user32.EnumWindows(EnumWindowsProc(on_window), 0)


if __name__ == "__main__":
    print("=" * 50)
    print("GPM Timeout Auto-Dismiss")
    print("Đang theo dõi dialog 'Timeout (APP)'...")
    print("Nhấn Ctrl+C để dừng.")
    print("=" * 50)
    while True:
        try:
            scan_once()
        except Exception:
            pass
        time.sleep(0.8)
