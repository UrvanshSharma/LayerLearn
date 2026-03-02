"""
Platform Utilities
==================
Small cross-platform helpers used by tools and agent orchestration.
"""

from __future__ import annotations

import platform
import subprocess
import webbrowser
from shutil import which
from typing import Optional


SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = SYSTEM == "Linux"


def command_exists(cmd: str) -> bool:
    return which(cmd) is not None


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _browser_command(browser: Optional[str]) -> Optional[str]:
    if not browser:
        return None
    key = browser.lower().strip()
    if IS_WINDOWS:
        mapping = {
            "google chrome": "chrome",
            "chrome": "chrome",
            "microsoft edge": "msedge",
            "edge": "msedge",
            "firefox": "firefox",
            "brave": "brave",
            "brave browser": "brave",
            "opera": "opera",
            "vivaldi": "vivaldi",
        }
    elif IS_MAC:
        mapping = {
            "google chrome": "Google Chrome",
            "chrome": "Google Chrome",
            "safari": "Safari",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "brave browser": "Brave Browser",
            "microsoft edge": "Microsoft Edge",
            "edge": "Microsoft Edge",
            "arc": "Arc",
            "opera": "Opera",
            "vivaldi": "Vivaldi",
        }
    else:
        mapping = {
            "google chrome": "google-chrome",
            "chrome": "google-chrome",
            "firefox": "firefox",
            "brave": "brave-browser",
            "brave browser": "brave-browser",
            "microsoft edge": "microsoft-edge",
            "edge": "microsoft-edge",
            "opera": "opera",
            "vivaldi": "vivaldi",
        }
    return mapping.get(key, browser)


def open_url_in_browser(url: str, browser: Optional[str] = None) -> tuple[bool, str]:
    """
    Open URL in a preferred browser with cross-platform fallbacks.
    Returns (success, message).
    """
    url = normalize_url(url)
    if not url:
        return False, "Missing URL"

    browser_cmd = _browser_command(browser)

    try:
        if IS_MAC:
            if browser_cmd:
                subprocess.run(
                    ["open", "-a", browser_cmd, url],
                    check=True,
                    capture_output=True,
                    timeout=6,
                )
                return True, f"Opened {url} in {browser_cmd}"
            subprocess.run(["open", url], check=True, capture_output=True, timeout=6)
            return True, f"Opened {url}"

        if IS_WINDOWS:
            if browser_cmd:
                subprocess.run(
                    ["cmd", "/c", "start", "", browser_cmd, url],
                    check=True,
                    capture_output=True,
                    timeout=6,
                )
                return True, f"Opened {url} in {browser_cmd}"
            subprocess.run(
                ["cmd", "/c", "start", "", url],
                check=True,
                capture_output=True,
                timeout=6,
            )
            return True, f"Opened {url}"

        # Linux / fallback
        if browser_cmd and command_exists(browser_cmd):
            subprocess.Popen([browser_cmd, url])
            return True, f"Opened {url} in {browser_cmd}"
        if command_exists("xdg-open"):
            subprocess.run(["xdg-open", url], check=True, capture_output=True, timeout=6)
            return True, f"Opened {url}"
    except Exception:
        pass

    # Final fallback through Python stdlib
    if webbrowser.open(url):
        return True, f"Opened {url}"
    return False, f"Failed to open {url}"
