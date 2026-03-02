"""
Screen Capture — Fast
=====================
Optimised for speed: JPEG compression, in-memory, auto-cleanup.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime
from typing import Optional, Tuple

import mss
from PIL import Image

from config import settings, ASSETS_DIR
from core.logger import get_logger

log = get_logger(__name__)

# ── Cached screenshotter ─────────────────────────────────────────────────
_sct: mss.mss | None = None


def _get_sct() -> mss.mss:
    """Reuse mss instance for speed (avoid re-init overhead)."""
    global _sct
    if _sct is None:
        _sct = mss.mss()
    return _sct


def _default_monitor(sct: mss.mss) -> dict:
    if len(sct.monitors) > 1:
        return sct.monitors[1]
    return sct.monitors[0]


def _point_in_monitor(x: int, y: int, monitor: dict) -> bool:
    left = monitor["left"]
    top = monitor["top"]
    right = left + monitor["width"]
    bottom = top + monitor["height"]
    return left <= x < right and top <= y < bottom


def _front_window_bounds() -> Optional[Tuple[int, int, int, int]]:
    """
    Get the frontmost window bounds from macOS as (x, y, width, height).
    Returns None when unavailable (permissions, no front window, etc.).
    """
    script = """
    tell application "System Events"
        set frontProc to first application process whose frontmost is true
        tell front window of frontProc
            set {xPos, yPos} to position
            set {w, h} to size
        end tell
        return (xPos as text) & "," & (yPos as text) & "," & (w as text) & "," & (h as text)
    end tell
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
        )
        raw = result.stdout.strip()
        if not raw:
            return None

        parts = [p.strip() for p in raw.split(",")]
        if len(parts) != 4:
            return None
        x, y, w, h = (int(float(p)) for p in parts)
        if w <= 0 or h <= 0:
            return None
        return x, y, w, h
    except Exception:
        return None


def _active_monitor(sct: mss.mss) -> Optional[dict]:
    """
    Resolve which monitor currently contains the active/frontmost window.
    Falls back to None when unavailable.
    """
    bounds = _front_window_bounds()
    if not bounds:
        return None

    x, y, w, h = bounds
    center_x = x + (w // 2)
    center_y = y + (h // 2)

    monitors = sct.monitors[1:]
    if not monitors:
        return None

    # AppleScript can return points while mss uses pixels on HiDPI displays.
    # Try several scale variants for robust matching.
    candidate_points = [
        (center_x, center_y),
        (center_x * 2, center_y * 2),
        (center_x // 2, center_y // 2),
    ]

    for px, py in candidate_points:
        for mon in monitors:
            if _point_in_monitor(px, py, mon):
                return mon

    return None


def capture_screen(
    region: Optional[Tuple[int, int, int, int]] = None,
    save: bool = True,
    active_monitor: bool = False,
) -> tuple[Image.Image, Optional[str]]:
    """
    Capture screen — fast.
    Returns (PIL Image, optional save path).
    """
    sct = _get_sct()

    if region:
        monitor = {
            "left": region[0], "top": region[1],
            "width": region[2] - region[0], "height": region[3] - region[1],
        }
    elif active_monitor:
        monitor = _active_monitor(sct) or _default_monitor(sct)
    else:
        monitor = _default_monitor(sct)

    screenshot = sct.grab(monitor)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    path: Optional[str] = None
    if save:
        cleanup_old_screenshots()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(ASSETS_DIR / f"screenshot_{ts}.png")
        img.save(path, optimize=True)
        log.debug("📸 Screenshot → {}", path)

    return img, path


def capture_full_screen() -> tuple[Image.Image, str]:
    """Capture the monitor containing the active window and save."""
    img, path = capture_screen(region=None, save=True, active_monitor=True)
    assert path is not None
    return img, path


def cleanup_old_screenshots() -> None:
    """Remove old screenshots."""
    cutoff = time.time() - settings.agent.max_screenshot_age_secs
    for f in ASSETS_DIR.glob("screenshot_*.png"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass
