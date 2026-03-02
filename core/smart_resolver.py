"""
Smart Resolver
===============
Human-like reasoning for app/website/browser decisions.
Checks what's actually installed, remembers preferences, asks clarifying questions.
"""

from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Optional

from config import ROOT_DIR
from core.logger import get_logger
from core.platform_utils import IS_MAC, IS_WINDOWS, command_exists

log = get_logger(__name__)

# ── Preferences file ────────────────────────────────────────────────────
PREFS_FILE = ROOT_DIR / "user_prefs.json"


def _load_prefs() -> dict:
    try:
        if PREFS_FILE.exists():
            return json.loads(PREFS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_prefs(prefs: dict) -> None:
    try:
        PREFS_FILE.write_text(json.dumps(prefs, indent=2))
    except Exception as e:
        log.warning("Could not save prefs: {}", e)


def get_pref(key: str, default=None):
    return _load_prefs().get(key, default)


def set_pref(key: str, value) -> None:
    prefs = _load_prefs()
    prefs[key] = value
    _save_prefs(prefs)


# ── App Detection ────────────────────────────────────────────────────────

_installed_apps_cache: Optional[set] = None
_installed_apps_cased: dict[str, str] = {}


def _register_installed_app(name: str, apps: set[str]) -> None:
    clean = (name or "").strip()
    if not clean:
        return
    lower = clean.lower()
    apps.add(lower)
    _installed_apps_cased.setdefault(lower, clean)


def get_installed_apps() -> set:
    """Get installed applications for the current OS (cached)."""
    global _installed_apps_cache
    if _installed_apps_cache is not None:
        return _installed_apps_cache

    apps = set()
    _installed_apps_cased.clear()

    if IS_MAC:
        for app_dir in [Path("/Applications"), Path.home() / "Applications"]:
            if app_dir.exists():
                for item in app_dir.iterdir():
                    if item.suffix == ".app":
                        _register_installed_app(item.stem, apps)

        try:
            result = subprocess.run(
                ["mdfind", "kMDItemKind == 'Application'"],
                capture_output=True, text=True, timeout=6,
            )
            for line in result.stdout.strip().split("\n"):
                if line.endswith(".app"):
                    _register_installed_app(Path(line).stem, apps)
        except Exception:
            pass

    elif IS_WINDOWS:
        # Start menu / app registrations (works on most modern Windows setups)
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-StartApps | Select-Object -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                timeout=8,
            )
            for line in result.stdout.splitlines():
                _register_installed_app(line, apps)
        except Exception:
            pass

        # Add common browser/app executables if found in PATH
        exe_to_name = {
            "chrome.exe": "Google Chrome",
            "msedge.exe": "Microsoft Edge",
            "firefox.exe": "Firefox",
            "brave.exe": "Brave",
            "Code.exe": "Visual Studio Code",
            "wt.exe": "Windows Terminal",
            "notepad.exe": "Notepad",
            "explorer.exe": "File Explorer",
        }
        for exe, display in exe_to_name.items():
            try:
                where_result = subprocess.run(
                    ["where", exe],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if where_result.returncode == 0 and where_result.stdout.strip():
                    _register_installed_app(display, apps)
            except Exception:
                pass

    else:
        # Linux/fallback: detect common desktop binaries
        for cmd, display in {
            "google-chrome": "Google Chrome",
            "firefox": "Firefox",
            "brave-browser": "Brave Browser",
            "code": "Visual Studio Code",
            "xdg-open": "Default Browser",
        }.items():
            if command_exists(cmd):
                _register_installed_app(display, apps)

    _installed_apps_cache = apps
    log.debug("Found {} installed apps", len(apps))
    return apps


def is_app_installed(name: str) -> bool:
    """Check if an app is installed (fuzzy matching)."""
    apps = get_installed_apps()
    name_lower = name.lower().strip()

    # Direct match
    if name_lower in apps:
        return True

    # Common aliases
    aliases = {
        "chrome": "google chrome",
        "vscode": "visual studio code",
        "vs code": "visual studio code",
        "code": "visual studio code",
        "iterm": "iterm",
        "whatsapp": "whatsapp",
        "telegram": "telegram",
        "slack": "slack",
        "discord": "discord",
        "spotify": "spotify",
        "zoom": "zoom.us",
        "notion": "notion",
        "edge": "microsoft edge",
        "terminal": "windows terminal" if IS_WINDOWS else "terminal",
        "file explorer": "file explorer",
        "explorer": "file explorer",
    }
    resolved = aliases.get(name_lower, name_lower)
    if resolved in apps:
        return True

    # Fuzzy: check if any installed app contains the name
    for app in apps:
        if name_lower in app or app in name_lower:
            return True

    return False


def find_app_name(name: str) -> Optional[str]:
    """Find the exact installed app name for a given input."""
    apps = get_installed_apps()
    name_lower = name.lower().strip()

    # Direct match
    if name_lower in apps:
        return _installed_apps_cased.get(name_lower, name.title())

    # Alias match
    aliases = {
        "chrome": "Google Chrome",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "iterm": "iTerm",
        "zoom": "zoom.us",
        "edge": "Microsoft Edge",
        "terminal": "Windows Terminal" if IS_WINDOWS else "Terminal",
        "explorer": "File Explorer",
    }
    if name_lower in aliases:
        resolved = aliases[name_lower]
        if resolved.lower() in apps:
            return resolved

    # Fuzzy match
    for app in apps:
        if name_lower in app:
            return _installed_apps_cased.get(app, app.title())

    return None


def get_installed_browsers() -> list[str]:
    """Get list of installed browsers."""
    browsers = []
    browser_names = [
        "Google Chrome",
        "Safari",
        "Firefox",
        "Brave Browser",
        "Brave",
        "Microsoft Edge",
        "Arc",
        "Opera",
        "Vivaldi",
    ]
    apps = get_installed_apps()
    for b in browser_names:
        if b.lower() in apps:
            browsers.append(b)

    if IS_WINDOWS:
        for exe, name in [
            ("chrome.exe", "Google Chrome"),
            ("msedge.exe", "Microsoft Edge"),
            ("firefox.exe", "Firefox"),
            ("brave.exe", "Brave"),
        ]:
            try:
                r = subprocess.run(["where", exe], capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and r.stdout.strip() and name not in browsers:
                    browsers.append(name)
            except Exception:
                pass
    return browsers


# ── Smart Resolution ─────────────────────────────────────────────────────

# Things that are primarily web services (not native apps)
WEB_SERVICES = {
    "whatsapp": "web.whatsapp.com",
    "whats app": "web.whatsapp.com",
    "youtube": "youtube.com",
    "twitter": "twitter.com",
    "x": "x.com",
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "github": "github.com",
    "reddit": "reddit.com",
    "linkedin": "linkedin.com",
    "gmail": "mail.google.com",
    "google": "google.com",
    "netflix": "netflix.com",
    "amazon": "amazon.com",
    "chatgpt": "chat.openai.com",
    "stackoverflow": "stackoverflow.com",
    "stack overflow": "stackoverflow.com",
    "notion": "notion.so",
    "figma": "figma.com",
    "pinterest": "pinterest.com",
    "twitch": "twitch.tv",
    "spotify": "open.spotify.com",
    "slack": "app.slack.com",
    "discord": "discord.com/app",
    "zoom": "zoom.us/join",
    "trello": "trello.com",
    "jira": "jira.atlassian.com",
    "canva": "canva.com",
    "medium": "medium.com",
    "hacker news": "news.ycombinator.com",
    "producthunt": "producthunt.com",
    "product hunt": "producthunt.com",
    "maps": "maps.google.com",
    "drive": "drive.google.com",
    "docs": "docs.google.com",
    "sheets": "sheets.google.com",
    "calendar": "calendar.google.com",
    "google docs": "docs.google.com",
    "google drive": "drive.google.com",
    "google maps": "maps.google.com",
    "google sheets": "sheets.google.com",
    "google calendar": "calendar.google.com",
    "google meet": "meet.google.com",
    "meet": "meet.google.com",
    "teams": "teams.microsoft.com",
    "microsoft teams": "teams.microsoft.com",
    "outlook": "outlook.live.com",
    "hotmail": "outlook.live.com",
    "wikipedia": "wikipedia.org",
    "wiki": "wikipedia.org",
}


class ResolveResult:
    """Result of smart resolution."""

    def __init__(
        self,
        action: str,        # "open_app", "open_url", "ask_web_or_app", "ask_browser", "ask_clarify"
        target: str = "",   # app name or URL
        browser: str = "",  # browser to use (if URL)
        message: str = "",  # message to speak to user
        data: dict = None,  # extra data for follow-up handling
    ):
        self.action = action
        self.target = target
        self.browser = browser or get_pref("default_browser", "Google Chrome")
        self.message = message
        self.data = data or {}


def resolve_open_request(target: str) -> ResolveResult:
    """
    Smart resolution: figure out what the user means by "open X".

    Logic:
    1. Is X a URL/domain? → open in preferred browser
    2. Is X a known web service?
       a. Is there a native app installed? → ask: app or web?
       b. No native app? → open in browser (ask which if multiple)
    3. Is X an installed app? → open the app
    4. Not found → ask what they mean
    """
    target_lower = target.lower().strip()

    # ── Is it a URL? ─────────────────────────────────────────────────
    if "." in target_lower and " " not in target_lower:
        browser = get_pref("default_browser", "Google Chrome")
        return ResolveResult(
            action="open_url",
            target=target,
            browser=browser,
        )

    # ── Is it a known web service? ───────────────────────────────────
    if target_lower in WEB_SERVICES:
        url = WEB_SERVICES[target_lower]

        # Check if there's also a native app
        if is_app_installed(target_lower):
            app_name = find_app_name(target_lower)
            return ResolveResult(
                action="ask_web_or_app",
                target=target_lower,
                message=(
                    f"I found {app_name} installed as an app, "
                    f"and it's also available on the web at {url}. "
                    f"Would you like me to open the app or the web version?"
                ),
                data={"app_name": app_name, "url": url},
            )
        else:
            # No native app — open on web
            browser = get_pref("default_browser", "Google Chrome")
            return ResolveResult(
                action="open_url",
                target=url,
                browser=browser,
                message=f"Opening {target_lower} on web in {browser}.",
            )

    # ── Is it an installed app? ──────────────────────────────────────
    app_name = find_app_name(target_lower)
    if app_name:
        return ResolveResult(action="open_app", target=app_name)

    # ── Not found ────────────────────────────────────────────────────
    return ResolveResult(
        action="ask_clarify",
        target=target_lower,
        message=(
            f"I couldn't find '{target}' as an installed app. "
            f"Do you want me to search for it on the web instead?"
        ),
        data={"original": target},
    )
