# -*- coding: utf-8 -*-
"""Chrome DevTools Protocol — ad blocking, anti-detect, native events."""
import random
import time
from .logger import log

# ── Ad network blocking ───────────────────────────────────────────
_CDP_BLOCKED = [
    "*doubleclick.net*", "*googlesyndication.com*", "*googleadservices.com*",
    "*adservice.google.*", "*pagead2.googlesyndication*",
    "*securepubads.g.doubleclick*", "*pubads.g.doubleclick*",
    "*cm.g.doubleclick*", "*ad.doubleclick*",
    "*taboola.com*", "*outbrain.com*", "*mgid.com*", "*criteo.com*",
    "*adnxs.com*", "*amazon-adsystem.com*", "*adsrvr.org*",
    "*rubiconproject.com*", "*openx.net*", "*pubmatic.com*",
]

# ── JavaScript injected on every new page ────────────────────────
# CHỈ click Skip/Close — KHÔNG tua currentTime (gây YouTube detect bot)
_YT_AD_SKIP_SCRIPT = """
(function() {
    'use strict';
    var _lastSkip = 0;

    var SKIP_TEXTS = [
        'skip', 'b\\u1ecf qua', '\\u30b9\\u30ad\\u30c3\\u30d7',
        '\\uac74\\ub108\\ub6f0\\uae30', '\\u8df3\\u8fc7', '\\u8df3\\u904e',
        '\\xfcberspringen', 'passer', 'saltar', 'sla over',
    ];

    function containsSkipText(el) {
        var t = (el.textContent || el.innerText || el.getAttribute('aria-label') || '').toLowerCase().trim();
        for (var i = 0; i < SKIP_TEXTS.length; i++) {
            if (t.indexOf(SKIP_TEXTS[i]) >= 0) return true;
        }
        return false;
    }

    function tryClick(el) {
        if (!el) return false;
        try { el.click(); return true; } catch(e) { return false; }
    }

    function skipAd() {
        var now = Date.now();
        if (now - _lastSkip < 600) return;

        var SELS = [
            '.ytp-skip-ad-button', '.ytp-ad-skip-button',
            'button.ytp-ad-skip-button-modern', '.ytp-ad-skip-button-slot button',
            '.ytp-skip-ad-button-modern', '[class*="skip-ad"]',
            '[class*="skipAd"]', '[class*="SkipAd"]', 'button[id*="skip"]',
        ];
        for (var i = 0; i < SELS.length; i++) {
            var el = document.querySelector(SELS[i]);
            if (el && tryClick(el)) { _lastSkip = now; return; }
        }

        var allEls = document.querySelectorAll('button[aria-label], .ytp-button[aria-label]');
        for (var j = 0; j < allEls.length; j++) {
            if (containsSkipText(allEls[j]) && tryClick(allEls[j])) {
                _lastSkip = now; return;
            }
        }

        var playerBtns = document.querySelectorAll('.html5-video-player button, #movie_player button');
        for (var k = 0; k < playerBtns.length; k++) {
            var btn = playerBtns[k];
            if (containsSkipText(btn)) {
                var rect = btn.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && tryClick(btn)) {
                    _lastSkip = now; return;
                }
            }
        }

        var banner = document.querySelector(
            '.ytp-ad-overlay-close-button, .ytp-ad-text-overlay .ytp-ad-overlay-close-button'
        );
        if (banner && tryClick(banner)) { _lastSkip = now; }
    }

    setInterval(skipAd, 600);
})();
"""

_ANTI_DETECT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['ja-JP','ja','en-US','en']});
window.chrome = window.chrome || {runtime: {}};
"""


# ── CDP setup ─────────────────────────────────────────────────────

def cdp_setup(driver):
    """Block ads + inject anti-detect + YT ad-skip script."""
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": _CDP_BLOCKED})
    except Exception:
        pass
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": _ANTI_DETECT_SCRIPT + _YT_AD_SKIP_SCRIPT}
        )
    except Exception:
        pass


# ── CDP native events ─────────────────────────────────────────────

def cdp_scroll(driver, delta_y: int):
    """Cuộn trang bằng CDP mouseWheel — native OS event."""
    try:
        w = driver.execute_script("return window.innerWidth;") or 800
        h = driver.execute_script("return window.innerHeight;") or 600
        x = w // 2 + random.randint(-80, 80)
        y = h // 2 + random.randint(-60, 60)
        driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
            "type": "mouseWheel", "x": x, "y": y,
            "deltaX": 0, "deltaY": delta_y, "modifiers": 0,
        })
    except Exception:
        driver.execute_script(f"window.scrollBy(0, {delta_y});")


# ── Bézier mouse movement ──────────────────────────────────────────

_cursor = [400, 300]   # Module-level cursor position tracking


def _bezier_pts(p0, cp1, cp2, p3, n: int) -> list:
    """n+1 điểm trên đường cong Bézier bậc 3."""
    pts = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        x = u**3*p0[0] + 3*u**2*t*cp1[0] + 3*u*t**2*cp2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u**2*t*cp1[1] + 3*u*t**2*cp2[1] + t**3*p3[1]
        pts.append((int(x), int(y)))
    return pts


def bezier_mouse_move(driver, tx: int, ty: int):
    """
    Di chuột theo Bézier curve từ vị trí hiện tại đến (tx, ty).
    - Cubic Bézier với 2 control point ngẫu nhiên
    - Slight overshoot rồi quay về target (giống người thật)
    - Ease-in-out: chậm đầu và cuối, nhanh giữa
    """
    x0, y0 = _cursor
    # Overshoot nhẹ để tự nhiên hơn
    ox = tx + random.randint(-12, 12)
    oy = ty + random.randint(-10, 10)
    dx, dy = tx - x0, ty - y0
    # Control points tạo đường cong lệch
    cp1 = (
        x0 + dx * random.uniform(0.2, 0.4) + random.randint(-40, 40),
        y0 + dy * random.uniform(0.1, 0.3) + random.randint(-35, 35),
    )
    cp2 = (
        x0 + dx * random.uniform(0.6, 0.8) + random.randint(-40, 40),
        y0 + dy * random.uniform(0.7, 0.9) + random.randint(-35, 35),
    )
    pts = _bezier_pts((x0, y0), cp1, cp2, (ox, oy), random.randint(10, 20))
    # Điểm cuối: sửa về đúng target
    pts.append((tx + random.randint(-2, 2), ty + random.randint(-2, 2)))

    for i, (px, py) in enumerate(pts):
        try:
            driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mouseMoved", "x": max(0, px), "y": max(0, py),
                "modifiers": 0, "buttons": 0, "button": "none",
            })
            # Ease-in-out: 4t(1-t) = 0 ở đầu/cuối, 1 ở giữa
            t = i / len(pts)
            base = 0.012 + 0.025 * (1 - 4 * t * (1 - t))
            time.sleep(random.uniform(base * 0.8, base * 1.4))
        except Exception:
            break

    _cursor[0], _cursor[1] = tx, ty


def cdp_click(driver, element):
    """
    Click element: Bézier mouse move → mousePressed → mouseReleased.
    Tự nhiên hơn single-event click vì có full mouse path.
    """
    try:
        rect = driver.execute_script("""
            var r = arguments[0].getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2};
        """, element)
        x = int(rect["x"]) + random.randint(-3, 3)
        y = int(rect["y"]) + random.randint(-3, 3)

        # Di chuột đến target trước (Bézier)
        bezier_mouse_move(driver, x, y)

        # Nhấn và thả
        for evt in ("mousePressed", "mouseReleased"):
            driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": evt, "x": x, "y": y, "modifiers": 0,
                "buttons": 1 if evt == "mousePressed" else 0,
                "button": "left", "clickCount": 1,
            })
            time.sleep(random.uniform(0.04, 0.14))
    except Exception:
        driver.execute_script("arguments[0].click();", element)
