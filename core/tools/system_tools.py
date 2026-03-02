"""
System & Automation Tools
==========================
Run commands, open apps/URLs in Chrome, automate macOS tasks, git operations.
"""

import subprocess
import urllib.parse
from pathlib import Path

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────

def _open_url_in_chrome(url: str) -> ToolResult:
    """Open a URL specifically in Google Chrome on macOS."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        subprocess.run(
            ["open", "-a", "Google Chrome", url],
            check=True, capture_output=True, timeout=5,
        )
        log.info("Opened in Chrome: {}", url)
        return ToolResult(success=True, output=f"Opened {url} in Chrome")
    except subprocess.CalledProcessError:
        # Fallback: try just "open" (uses default browser)
        try:
            subprocess.run(["open", url], check=True, capture_output=True, timeout=5)
            return ToolResult(success=True, output=f"Opened {url}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to open URL: {e}")
    except Exception as e:
        return ToolResult(success=False, output=f"Failed: {e}")


# ── Tools ────────────────────────────────────────────────────────────────

class RunCommandTool(Tool):
    name = "run_command"
    description = (
        "Execute a shell command. ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'command' (shell command to run)."
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        cmd = kwargs.get("command", "")
        if not cmd:
            return ToolResult(success=False, output="Missing 'command'")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=kwargs.get("cwd", "."),
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr] {result.stderr}"
            if len(output) > 5000:
                output = output[:5000] + "\n… [truncated]"
            return ToolResult(success=result.returncode == 0, output=output or "(no output)")
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="Command timed out (30s)")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class OpenAppTool(Tool):
    name = "open_app"
    description = (
        "Open an application on macOS. "
        "Argument: 'name' (app name like 'Google Chrome', 'Notes', 'Terminal', 'Spotify', 'WhatsApp'). "
        "Common app names: 'Google Chrome', 'Safari', 'Spotify', 'Slack', 'Discord', 'Finder', "
        "'Terminal', 'Notes', 'Messages', 'Mail', 'Calendar', 'VS Code' (use 'Visual Studio Code')"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult(success=False, output="Missing app 'name'")

        # Normalise common app name variations (expanded)
        name_map = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "code": "Visual Studio Code",
            "iterm": "iTerm",
            "iterm2": "iTerm",
            "whatsapp": "WhatsApp",
            "wechat": "WeChat",
            "telegram": "Telegram",
            "spotify": "Spotify",
            "slack": "Slack",
            "discord": "Discord",
            "zoom": "zoom.us",
            "notion": "Notion",
            "figma": "Figma",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "edge": "Microsoft Edge",
            "arc": "Arc",
            "finder": "Finder",
            "terminal": "Terminal",
            "notes": "Notes",
            "messages": "Messages",
            "mail": "Mail",
            "calendar": "Calendar",
            "calculator": "Calculator",
            "preview": "Preview",
            "music": "Music",
            "apple music": "Music",
            "photos": "Photos",
            "safari": "Safari",
            "system preferences": "System Preferences",
            "settings": "System Preferences",
            "system settings": "System Settings",
            "activity monitor": "Activity Monitor",
            "xcode": "Xcode",
            "pages": "Pages",
            "numbers": "Numbers",
            "keynote": "Keynote",
            "maps": "Maps",
            "facetime": "FaceTime",
        }
        resolved = name_map.get(name.lower(), name)

        # Try resolved name first
        try:
            subprocess.run(
                ["open", "-a", resolved],
                check=True, capture_output=True, text=True, timeout=5,
            )
            log.info("Opened app: {} (resolved: {})", name, resolved)
            return ToolResult(success=True, output=f"Opened {resolved}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Try original name
        try:
            subprocess.run(
                ["open", "-a", name],
                check=True, capture_output=True, text=True, timeout=5,
            )
            return ToolResult(success=True, output=f"Opened {name}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Last resort: fuzzy search with mdfind
        try:
            result = subprocess.run(
                ["mdfind", "kMDItemKind == 'Application'", "-name", name],
                capture_output=True, text=True, timeout=3,
            )
            apps = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            if apps:
                app_path = apps[0]
                subprocess.run(
                    ["open", app_path],
                    check=True, capture_output=True, timeout=5,
                )
                app_name = Path(app_path).stem
                log.info("Opened via mdfind: {}", app_name)
                return ToolResult(success=True, output=f"Opened {app_name}")
        except Exception:
            pass

        return ToolResult(
            success=False,
            output=f"Could not find app '{name}'. Try the exact name from /Applications.",
        )


class OpenURLTool(Tool):
    name = "open_url"
    description = (
        "Open a URL in Google Chrome (NOT Safari). "
        "Argument: 'url' (the web address). "
        "Use for: 'open google.com', 'open youtube', 'go to whatsapp.com', etc."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        if not url:
            return ToolResult(success=False, output="Missing 'url'")
        return _open_url_in_chrome(url)


class SearchWebTool(Tool):
    name = "search_web"
    description = (
        "Search the web using Google in Chrome. "
        "Argument: 'query'. "
        "Use for: 'search for X', 'google X', 'find X'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, output="Missing 'query'")
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return _open_url_in_chrome(url)


class TypeTextTool(Tool):
    name = "type_text"
    description = (
        "Type text using the keyboard (simulates typing). ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'text'. "
        "Use for: 'type this', 'write this message', 'type in the field'"
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        if not text:
            return ToolResult(success=False, output="Missing 'text'")
        try:
            escaped = text.replace("\\", "\\\\").replace('"', '\\"')
            script = f'tell application "System Events" to keystroke "{escaped}"'
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=5)
            return ToolResult(success=True, output=f"Typed: {text[:100]}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to type: {e}")


class KeyPressTool(Tool):
    name = "key_press"
    description = (
        "Press a keyboard shortcut. ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'keys' (like 'cmd+c', 'cmd+v', 'cmd+tab', 'enter', 'cmd+s'). "
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        keys = kwargs.get("keys", "")
        if not keys:
            return ToolResult(success=False, output="Missing 'keys'")
        try:
            parts = [k.strip().lower() for k in keys.replace("+", " ").split()]
            modifiers = []
            key = None
            mod_map = {
                "cmd": "command down", "command": "command down",
                "ctrl": "control down", "control": "control down",
                "alt": "option down", "option": "option down",
                "shift": "shift down",
            }
            for p in parts:
                if p in mod_map:
                    modifiers.append(mod_map[p])
                else:
                    key = p

            if key is None:
                return ToolResult(success=False, output=f"Could not parse: {keys}")

            if modifiers:
                mod_str = ", ".join(modifiers)
                script = f'tell application "System Events" to keystroke "{key}" using {{{mod_str}}}'
            else:
                special = {
                    "enter": 36, "return": 36, "tab": 48, "escape": 53, "esc": 53,
                    "delete": 51, "space": 49,
                    "up": 126, "down": 125, "left": 123, "right": 124,
                }
                if key in special:
                    script = f'tell application "System Events" to key code {special[key]}'
                else:
                    script = f'tell application "System Events" to keystroke "{key}"'

            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=5)
            return ToolResult(success=True, output=f"Pressed: {keys}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class GitDiffTool(Tool):
    name = "git_diff"
    description = "Show current git diff."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "diff"], capture_output=True, text=True,
                timeout=10, cwd=kwargs.get("path", "."),
            )
            output = result.stdout or "(no changes)"
            if len(output) > 5000:
                output = output[:5000] + "\n… [truncated]"
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class GitStatusTool(Tool):
    name = "git_status"
    description = "Show git status."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "status", "--short"], capture_output=True, text=True,
                timeout=10, cwd=kwargs.get("path", "."),
            )
            return ToolResult(success=True, output=result.stdout or "(clean)")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class SetVolumeTool(Tool):
    name = "set_volume"
    description = "Set macOS volume (0-100). Use for: 'set volume to 50', 'mute'"
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        level = kwargs.get("level", 50)
        try:
            level = max(0, min(100, int(level)))
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {level}"],
                check=True, capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output=f"Volume set to {level}%")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class GetTimeTool(Tool):
    name = "get_time"
    description = "Get current date and time."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from datetime import datetime
        now = datetime.now()
        return ToolResult(
            success=True,
            output=now.strftime("It's %A, %B %d, %Y at %I:%M %p"),
        )


class NotificationTool(Tool):
    name = "send_notification"
    description = "Send a macOS notification. Arguments: 'title', 'message'."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        title = kwargs.get("title", "LayerLearn")
        message = kwargs.get("message", "")
        if not message:
            return ToolResult(success=False, output="Missing 'message'")
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=3)
            return ToolResult(success=True, output=f"Notification sent: {message[:50]}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class ScreenshotAndOpenTool(Tool):
    name = "open_website_in_chrome"
    description = (
        "Open a specific website in Google Chrome. "
        "Argument: 'url' (like 'whatsapp.com', 'youtube.com', 'twitter.com'). "
        "Use for: 'open whatsapp', 'open youtube in chrome', 'go to twitter'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        if not url:
            return ToolResult(success=False, output="Missing 'url'")
        return _open_url_in_chrome(url)


# ── Register ─────────────────────────────────────────────────────────────
for _cls in [
    RunCommandTool, OpenAppTool, OpenURLTool, SearchWebTool,
    TypeTextTool, KeyPressTool,
    GitDiffTool, GitStatusTool,
    SetVolumeTool, GetTimeTool, NotificationTool,
    ScreenshotAndOpenTool,
]:
    register_tool(_cls())
