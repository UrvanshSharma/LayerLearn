"""
Window Utilities
================
Cross-platform helpers for active window/app discovery.
"""

from __future__ import annotations

import ctypes
import subprocess
from typing import Optional

import psutil

from core.platform_utils import IS_MAC, IS_WINDOWS


def get_front_window_bounds() -> Optional[tuple[int, int, int, int]]:
    """
    Returns front window bounds as (x, y, width, height).
    """
    if IS_MAC:
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

    if IS_WINDOWS:
        try:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            rect = RECT()
            ok = user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if not ok:
                return None

            w = int(rect.right - rect.left)
            h = int(rect.bottom - rect.top)
            if w <= 0 or h <= 0:
                return None
            return int(rect.left), int(rect.top), w, h
        except Exception:
            return None

    return None


def get_front_app_name() -> Optional[str]:
    """
    Returns the active app/process name if available.
    """
    if IS_MAC:
        script = """
        tell application "System Events"
            return name of first application process whose frontmost is true
        end tell
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            app = result.stdout.strip()
            return app or None
        except Exception:
            return None

    if IS_WINDOWS:
        try:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc = psutil.Process(pid.value)
            return proc.name().replace(".exe", "")
        except Exception:
            return None

    return None


def list_running_gui_apps() -> list[str]:
    """
    Returns a best-effort list of foreground-capable apps.
    """
    if IS_MAC:
        script = """
        tell application "System Events"
            set appList to name of every application process whose background only is false
            return appList as text
        end tell
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
            raw = result.stdout.strip()
            if not raw:
                return []
            return [a.strip() for a in raw.split(",") if a.strip()]
        except Exception:
            return []

    if IS_WINDOWS:
        cmd = (
            "Get-Process | "
            "Where-Object { $_.MainWindowTitle -ne '' } | "
            "Select-Object -ExpandProperty ProcessName -Unique"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=6,
                check=False,
            )
            apps = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return sorted(set(apps), key=str.lower)
        except Exception:
            return []

    # Generic fallback
    apps: set[str] = set()
    for proc in psutil.process_iter(attrs=["name"]):
        name = (proc.info.get("name") or "").strip()
        if name:
            apps.add(name.replace(".exe", ""))
    return sorted(apps, key=str.lower)
