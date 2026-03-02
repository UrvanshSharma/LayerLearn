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

from config import settings, ROOT_DIR
from core.logger import get_logger

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


def get_installed_apps() -> set:
    """Get all installed macOS applications (cached)."""
    global _installed_apps_cache
    if _installed_apps_cache is not None:
        return _installed_apps_cache

    apps = set()
    for app_dir in [Path("/Applications"), Path.home() / "Applications"]:
        if app_dir.exists():
            for item in app_dir.iterdir():
                if item.suffix == ".app":
                    name = item.stem.lower()
                    apps.add(name)

    # Also check for apps via system_profiler (catches more apps)
    try:
        result = subprocess.run(
            ["mdfind", "kMDItemKind == 'Application'"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            if line.endswith(".app"):
                name = Path(line).stem.lower()
                apps.add(name)
    except Exception:
        pass

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
        for app_dir in [Path("/Applications"), Path.home() / "Applications"]:
            for item in app_dir.iterdir():
                if item.suffix == ".app" and item.stem.lower() == name_lower:
                    return item.stem
        return name.title()

    # Alias match
    aliases = {
        "chrome": "Google Chrome",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "iterm": "iTerm",
        "zoom": "zoom.us",
    }
    if name_lower in aliases:
        resolved = aliases[name_lower]
        if resolved.lower() in apps:
            return resolved

    # Fuzzy match
    for app in apps:
        if name_lower in app:
            # Find the properly-cased name
            for app_dir in [Path("/Applications"), Path.home() / "Applications"]:
                for item in app_dir.iterdir():
                    if item.suffix == ".app" and item.stem.lower() == app:
                        return item.stem
            return app.title()

    return None


def get_installed_browsers() -> list[str]:
    """Get list of installed browsers."""
    browsers = []
    browser_names = ["Google Chrome", "Safari", "Firefox", "Brave Browser",
                     "Microsoft Edge", "Arc", "Opera", "Vivaldi"]
    apps = get_installed_apps()
    for b in browser_names:
        if b.lower() in apps:
            browsers.append(b)
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
