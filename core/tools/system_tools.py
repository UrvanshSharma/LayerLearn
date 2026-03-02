"""
System & Automation Tools
==========================
Run commands, open apps/URLs, automate desktop tasks, and inspect git state.
"""

from __future__ import annotations

import subprocess
import urllib.parse
from pathlib import Path

from core.platform_utils import (
    IS_MAC,
    IS_WINDOWS,
    command_exists,
    open_url_in_browser,
)
from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────

def _open_url_in_chrome(url: str, browser: str | None = None) -> ToolResult:
    preferred_browser = browser or "Google Chrome"
    ok, msg = open_url_in_browser(url, preferred_browser)
    if ok:
        log.info("Opened URL: {}", msg)
        return ToolResult(success=True, output=msg)
    return ToolResult(success=False, output=msg)


def _import_pyautogui():
    try:
        import pyautogui  # type: ignore
        return pyautogui
    except Exception:
        return None


def _run_windows_start(target: str) -> bool:
    try:
        subprocess.run(
            ["cmd", "/c", "start", "", target],
            check=True,
            capture_output=True,
            timeout=6,
        )
        return True
    except Exception:
        return False


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
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=kwargs.get("cwd", "."),
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
        "Open an application on the current OS. "
        "Argument: 'name' (e.g. 'Google Chrome', 'Visual Studio Code', 'Terminal')."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult(success=False, output="Missing app 'name'")

        # Normalize common app aliases
        common_map = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "code": "Visual Studio Code",
            "terminal": "Terminal" if IS_MAC else "Windows Terminal",
            "iterm": "iTerm",
            "iterm2": "iTerm",
            "whatsapp": "WhatsApp",
            "spotify": "Spotify",
            "slack": "Slack",
            "discord": "Discord",
            "firefox": "Firefox",
            "brave": "Brave Browser" if IS_MAC else "Brave",
            "edge": "Microsoft Edge",
            "notepad": "Notepad",
            "explorer": "File Explorer",
        }
        resolved = common_map.get(name.lower().strip(), name)

        if IS_MAC:
            for candidate in [resolved, name]:
                try:
                    subprocess.run(
                        ["open", "-a", candidate],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=6,
                    )
                    log.info("Opened app: {}", candidate)
                    return ToolResult(success=True, output=f"Opened {candidate}")
                except Exception:
                    pass

            # Fuzzy fallback with Spotlight index
            try:
                result = subprocess.run(
                    ["mdfind", "kMDItemKind == 'Application'", "-name", name],
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
                app_paths = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                if app_paths:
                    subprocess.run(["open", app_paths[0]], check=True, capture_output=True, timeout=6)
                    return ToolResult(success=True, output=f"Opened {Path(app_paths[0]).stem}")
            except Exception:
                pass
            return ToolResult(success=False, output=f"Could not open '{name}'.")

        if IS_WINDOWS:
            windows_exec_map = {
                "Google Chrome": "chrome.exe",
                "Microsoft Edge": "msedge.exe",
                "Firefox": "firefox.exe",
                "Brave": "brave.exe",
                "Visual Studio Code": "Code.exe",
                "Windows Terminal": "wt.exe",
                "Notepad": "notepad.exe",
                "File Explorer": "explorer.exe",
            }

            # Try Start-Process with app name
            for candidate in [resolved, windows_exec_map.get(resolved, ""), name]:
                if not candidate:
                    continue
                safe = candidate.replace("'", "''")
                cmd = f"Start-Process -FilePath '{safe}'"
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True,
                    timeout=6,
                )
                if result.returncode == 0:
                    return ToolResult(success=True, output=f"Opened {candidate}")

            # Try via cmd start fallback
            for candidate in [resolved, name]:
                if _run_windows_start(candidate):
                    return ToolResult(success=True, output=f"Opened {candidate}")

            # Try executable lookup
            exe_candidate = windows_exec_map.get(resolved)
            if exe_candidate:
                where_result = subprocess.run(
                    ["where", exe_candidate],
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
                path = where_result.stdout.splitlines()[0].strip() if where_result.stdout.strip() else ""
                if path and _run_windows_start(path):
                    return ToolResult(success=True, output=f"Opened {resolved}")

            return ToolResult(success=False, output=f"Could not open '{name}'.")

        # Linux best effort
        try:
            subprocess.Popen([resolved])
            return ToolResult(success=True, output=f"Opened {resolved}")
        except Exception:
            if command_exists("xdg-open"):
                result = subprocess.run(["xdg-open", resolved], capture_output=True, timeout=6)
                if result.returncode == 0:
                    return ToolResult(success=True, output=f"Opened {resolved}")
            return ToolResult(success=False, output=f"Could not open '{name}'.")


class OpenURLTool(Tool):
    name = "open_url"
    description = (
        "Open a URL in browser. "
        "Arguments: 'url', optional 'browser'. "
        "Use for: 'open google.com', 'open youtube', 'go to whatsapp.com'."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        browser = kwargs.get("browser")
        if not url:
            return ToolResult(success=False, output="Missing 'url'")
        return _open_url_in_chrome(url, browser)


class SearchWebTool(Tool):
    name = "search_web"
    description = (
        "Search the web using Google. "
        "Argument: 'query'. "
        "Use for: 'search for X', 'google X', 'find X'."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        browser = kwargs.get("browser")
        if not query:
            return ToolResult(success=False, output="Missing 'query'")
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return _open_url_in_chrome(url, browser)


class TypeTextTool(Tool):
    name = "type_text"
    description = (
        "Type text using keyboard automation. ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'text'."
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        if not text:
            return ToolResult(success=False, output="Missing 'text'")

        if IS_MAC:
            try:
                escaped = text.replace("\\", "\\\\").replace('"', '\\"')
                script = f'tell application "System Events" to keystroke "{escaped}"'
                subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=5)
                return ToolResult(success=True, output=f"Typed: {text[:100]}")
            except Exception as e:
                return ToolResult(success=False, output=f"Failed to type: {e}")

        pyautogui = _import_pyautogui()
        if pyautogui is None:
            return ToolResult(success=False, output="pyautogui is required for typing on this OS.")

        try:
            pyautogui.write(text, interval=0.01)
            return ToolResult(success=True, output=f"Typed: {text[:100]}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to type: {e}")


class KeyPressTool(Tool):
    name = "key_press"
    description = (
        "Press a keyboard shortcut. ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'keys' (like 'cmd+c', 'ctrl+v', 'enter', 'cmd+s')."
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        keys = kwargs.get("keys", "")
        if not keys:
            return ToolResult(success=False, output="Missing 'keys'")

        if IS_MAC:
            try:
                parts = [k.strip().lower() for k in keys.replace("+", " ").split()]
                modifiers = []
                key = None
                mod_map = {
                    "cmd": "command down",
                    "command": "command down",
                    "ctrl": "control down",
                    "control": "control down",
                    "alt": "option down",
                    "option": "option down",
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
                        "enter": 36,
                        "return": 36,
                        "tab": 48,
                        "escape": 53,
                        "esc": 53,
                        "delete": 51,
                        "space": 49,
                        "up": 126,
                        "down": 125,
                        "left": 123,
                        "right": 124,
                    }
                    if key in special:
                        script = f'tell application "System Events" to key code {special[key]}'
                    else:
                        script = f'tell application "System Events" to keystroke "{key}"'

                subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=5)
                return ToolResult(success=True, output=f"Pressed: {keys}")
            except Exception as e:
                return ToolResult(success=False, output=f"Failed: {e}")

        pyautogui = _import_pyautogui()
        if pyautogui is None:
            return ToolResult(success=False, output="pyautogui is required for key press on this OS.")

        try:
            raw_parts = [k.strip().lower() for k in keys.replace("+", " ").split() if k.strip()]
            if not raw_parts:
                return ToolResult(success=False, output=f"Could not parse: {keys}")

            key_map = {
                "command": "ctrl",
                "cmd": "ctrl",
                "control": "ctrl",
                "option": "alt",
                "return": "enter",
                "escape": "esc",
                "win": "winleft",
            }
            parts = [key_map.get(p, p) for p in raw_parts]

            if len(parts) == 1:
                pyautogui.press(parts[0])
            else:
                pyautogui.hotkey(*parts)

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
                ["git", "diff"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=kwargs.get("path", "."),
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
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=kwargs.get("path", "."),
            )
            return ToolResult(success=True, output=result.stdout or "(clean)")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class SetVolumeTool(Tool):
    name = "set_volume"
    description = "Set system volume (0-100). Use for: 'set volume to 50', 'mute'."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        level = kwargs.get("level", 50)
        try:
            level = max(0, min(100, int(level)))

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {level}"],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output=f"Volume set to {level}%")

            if IS_WINDOWS:
                import ctypes

                vol = int((level / 100.0) * 65535)
                packed = (vol & 0xFFFF) | ((vol & 0xFFFF) << 16)
                rc = ctypes.windll.winmm.waveOutSetVolume(0xFFFFFFFF, packed)  # type: ignore[attr-defined]
                if rc != 0:
                    return ToolResult(success=False, output="Failed to set system volume")
                return ToolResult(success=True, output=f"Volume set to {level}%")

            # Linux best-effort
            if command_exists("pactl"):
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    check=True, capture_output=True, timeout=4,
                )
                return ToolResult(success=True, output=f"Volume set to {level}%")
            if command_exists("amixer"):
                subprocess.run(
                    ["amixer", "sset", "Master", f"{level}%"],
                    check=True, capture_output=True, timeout=4,
                )
                return ToolResult(success=True, output=f"Volume set to {level}%")
            return ToolResult(success=False, output="No supported volume backend found on this OS.")
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
    description = "Send a desktop notification. Arguments: 'title', 'message'."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        title = kwargs.get("title", "LayerLearn")
        message = kwargs.get("message", "")
        if not message:
            return ToolResult(success=False, output="Missing 'message'")

        # Primary backend: plyer (cross-platform)
        try:
            from plyer import notification  # type: ignore

            notification.notify(
                title=title,
                message=message,
                app_name="LayerLearn",
                timeout=5,
            )
            return ToolResult(success=True, output=f"Notification sent: {message[:50]}")
        except Exception:
            pass

        try:
            if IS_MAC:
                safe_title = title.replace('"', '\\"')
                safe_msg = message.replace('"', '\\"')
                script = f'display notification "{safe_msg}" with title "{safe_title}"'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True,
                    capture_output=True,
                    timeout=3,
                )
                return ToolResult(success=True, output=f"Notification sent: {message[:50]}")

            if IS_WINDOWS:
                safe_title = title.replace("'", "''")
                safe_msg = message.replace("'", "''")
                script = (
                    "[void][Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); "
                    f"[System.Windows.Forms.MessageBox]::Show('{safe_msg}', '{safe_title}') | Out-Null"
                )
                subprocess.Popen(["powershell", "-NoProfile", "-Command", script])
                return ToolResult(success=True, output=f"Notification shown: {message[:50]}")

            if command_exists("notify-send"):
                subprocess.run(["notify-send", title, message], check=True, capture_output=True, timeout=3)
                return ToolResult(success=True, output=f"Notification sent: {message[:50]}")

            return ToolResult(success=False, output="No notification backend available.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class ScreenshotAndOpenTool(Tool):
    name = "open_website_in_chrome"
    description = (
        "Open a website in browser. "
        "Argument: 'url' (like 'whatsapp.com', 'youtube.com', 'twitter.com')."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        if not url:
            return ToolResult(success=False, output="Missing 'url'")
        return _open_url_in_chrome(url)


# ── Register ─────────────────────────────────────────────────────────────
for _cls in [
    RunCommandTool,
    OpenAppTool,
    OpenURLTool,
    SearchWebTool,
    TypeTextTool,
    KeyPressTool,
    GitDiffTool,
    GitStatusTool,
    SetVolumeTool,
    GetTimeTool,
    NotificationTool,
    ScreenshotAndOpenTool,
]:
    register_tool(_cls())
