"""
Utility Tools
==============
Calculator, translate, timer, system info, explain, summarize.
"""

import subprocess
import platform
import psutil

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger
from core.platform_utils import IS_MAC, IS_WINDOWS
from core.window_utils import get_front_app_name, list_running_gui_apps

log = get_logger(__name__)


class CalculatorTool(Tool):
    name = "calculator"
    description = (
        "Evaluate a math expression. Argument: 'expression'. "
        "Use for: 'calculate 5+3', 'what is 100/7', 'sqrt of 144'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        expr = kwargs.get("expression", "")
        if not expr:
            return ToolResult(success=False, output="Missing 'expression'")
        try:
            import math
            # Safe eval with math functions
            allowed = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "int": int, "float": float,
                "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "log": math.log, "log10": math.log10,
                "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
            }
            result = eval(expr, allowed)
            return ToolResult(success=True, output=f"{expr} = {result}")
        except Exception as e:
            return ToolResult(success=False, output=f"Math error: {e}")


class SystemInfoTool(Tool):
    name = "system_info"
    description = (
        "Get system information: CPU, memory, disk, battery. "
        "Use for: 'how much battery', 'system info', 'how much RAM', 'disk space'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        info = []
        try:
            if IS_MAC:
                os_label = f"macOS {platform.mac_ver()[0]}"
            elif IS_WINDOWS:
                os_label = f"Windows {platform.release()} ({platform.version()})"
            else:
                os_label = f"{platform.system()} {platform.release()}"

            info.append(f"OS: {os_label}")
            info.append(f"CPU: {psutil.cpu_percent()}% usage, {psutil.cpu_count()} cores")
            mem = psutil.virtual_memory()
            info.append(f"RAM: {mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB ({mem.percent}%)")
            disk_root = "C:\\" if IS_WINDOWS else "/"
            disk = psutil.disk_usage(disk_root)
            info.append(f"Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)")
            battery = psutil.sensors_battery()
            if battery:
                info.append(f"Battery: {battery.percent}% {'(charging)' if battery.power_plugged else '(on battery)'}")
        except Exception as e:
            info.append(f"Error getting some info: {e}")
        return ToolResult(success=True, output="\n".join(info))


class ActiveWindowTool(Tool):
    name = "active_window"
    description = (
        "Get the name of the currently focused/active application. "
        "Use for: 'what app am I using', 'what's the active window'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            app_name = get_front_app_name() or ""
            if not app_name:
                return ToolResult(success=False, output="Could not detect active app")
            return ToolResult(success=True, output=f"Active app: {app_name}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class BrightnessControlTool(Tool):
    name = "set_brightness"
    description = (
        "Set screen brightness (0-100). "
        "Use for: 'brighten screen', 'dim screen', 'set brightness to 50'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        level = kwargs.get("level", 50)
        try:
            level = max(0, min(100, int(level)))
            if IS_WINDOWS:
                cmd = (
                    f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                    f".WmiSetBrightness(1,{level})"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    check=True, capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output=f"Brightness set to {level}%")

            if IS_MAC:
                fraction = level / 100.0
                subprocess.run(
                    ["osascript", "-e", f'do shell script "brightness {fraction}"'],
                    capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output=f"Brightness set to {level}%")

            return ToolResult(
                success=False,
                output="Brightness control is not implemented for this OS.",
            )
        except Exception:
            return ToolResult(
                success=True,
                output=(
                    f"Brightness control attempted at {level}%. "
                    "You may need OS-specific brightness tooling."
                ),
            )


class SleepMacTool(Tool):
    name = "sleep_mac"
    description = "Put the computer to sleep. ⚠️ REQUIRES CONFIRMATION."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_WINDOWS:
                subprocess.run(
                    ["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"],
                    check=True, capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output="PC is going to sleep.")

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to sleep'],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output="Mac is going to sleep.")

            return ToolResult(success=False, output="Sleep is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class LockScreenTool(Tool):
    name = "lock_screen"
    description = "Lock the screen. ⚠️ REQUIRES CONFIRMATION."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_WINDOWS:
                subprocess.run(
                    ["rundll32.exe", "user32.dll,LockWorkStation"],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output="Screen locked.")

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to keystroke "q" using {command down, control down}'],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output="Screen locked.")

            return ToolResult(success=False, output="Lock screen is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class EmptyTrashTool(Tool):
    name = "empty_trash"
    description = "Empty Trash/Recycle Bin. ⚠️ REQUIRES CONFIRMATION (permanent!)."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_WINDOWS:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force"],
                    check=True, capture_output=True, timeout=10,
                )
                return ToolResult(success=True, output="Recycle Bin emptied.")

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e",
                     'tell application "Finder" to empty the trash'],
                    check=True, capture_output=True, timeout=10,
                )
                return ToolResult(success=True, output="Trash emptied.")

            return ToolResult(success=False, output="Empty trash is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class ToggleDarkModeTool(Tool):
    name = "toggle_dark_mode"
    description = (
        "Toggle dark mode on/off. "
        "Use for: 'turn on dark mode', 'switch to light mode', 'toggle dark mode'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_WINDOWS:
                query = subprocess.run(
                    [
                        "reg", "query",
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                        "/v", "AppsUseLightTheme",
                    ],
                    capture_output=True, text=True, timeout=4,
                )
                currently_light = "0x1" in query.stdout.lower()
                next_light_value = "0" if currently_light else "1"
                for key in ["AppsUseLightTheme", "SystemUsesLightTheme"]:
                    subprocess.run(
                        [
                            "reg", "add",
                            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                            "/v", key,
                            "/t", "REG_DWORD",
                            "/d", next_light_value,
                            "/f",
                        ],
                        check=True, capture_output=True, timeout=4,
                    )
                mode = "Dark" if next_light_value == "0" else "Light"
                return ToolResult(success=True, output=f"{mode} mode enabled.")

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e",
                     'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output="Dark mode toggled!")

            return ToolResult(success=False, output="Dark mode toggle is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class DoNotDisturbTool(Tool):
    name = "do_not_disturb"
    description = (
        "Toggle Do Not Disturb / Focus mode. "
        "Use for: 'turn on do not disturb', 'focus mode', 'no notifications'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_MAC:
                subprocess.run(
                    ["shortcuts", "run", "Toggle Focus"],
                    capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output="Do Not Disturb toggled!")

            if IS_WINDOWS:
                candidates = [
                    (
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications",
                        "ToastEnabled",
                    ),
                    (
                        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings",
                        "NOC_GLOBAL_SETTING_TOASTS_ENABLED",
                    ),
                ]

                key_path = ""
                key_name = ""
                current_enabled = True

                for path, name in candidates:
                    query = subprocess.run(
                        ["reg", "query", path, "/v", name],
                        capture_output=True,
                        text=True,
                        timeout=4,
                    )
                    if query.returncode == 0 and query.stdout:
                        key_path = path
                        key_name = name
                        current_enabled = "0x1" in query.stdout.lower()
                        break

                if not key_path:
                    key_path, key_name = candidates[0]

                next_enabled = not current_enabled
                next_val = "1" if next_enabled else "0"
                subprocess.run(
                    ["reg", "add", key_path, "/v", key_name, "/t", "REG_DWORD", "/d", next_val, "/f"],
                    check=True,
                    capture_output=True,
                    timeout=4,
                )
                mode = "Notifications enabled" if next_enabled else "Do Not Disturb enabled"
                return ToolResult(success=True, output=f"{mode}.")

            return ToolResult(success=False, output="Do Not Disturb is not implemented for this OS.")
        except Exception:
            return ToolResult(success=True, output="Focus mode toggle attempted. You may need to set up a 'Toggle Focus' Shortcut.")


class WordCountTool(Tool):
    name = "word_count"
    description = (
        "Count words, characters, and lines in text. "
        "Argument: 'text' or 'file' (path). "
        "Use for: 'count words', 'how many words in this text'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        file_path = kwargs.get("file", "")

        if file_path:
            try:
                with open(file_path, "r") as f:
                    text = f.read()
            except Exception as e:
                return ToolResult(success=False, output=f"Can't read file: {e}")

        if not text:
            return ToolResult(success=False, output="No text provided. Use 'text' or 'file' argument.")

        words = len(text.split())
        chars = len(text)
        lines = text.count("\n") + 1
        return ToolResult(
            success=True,
            output=f"Words: {words}, Characters: {chars}, Lines: {lines}",
        )


class ListRunningAppsTool(Tool):
    name = "list_running_apps"
    description = (
        "List all currently running applications. "
        "Use for: 'what apps are running', 'show running apps', 'what's open'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            apps_list = list_running_gui_apps()
            apps = ", ".join(apps_list) if apps_list else "(none detected)"
            return ToolResult(success=True, output=f"Running apps: {apps}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class QuitAppTool(Tool):
    name = "quit_app"
    description = (
        "Quit/close an application. ⚠️ REQUIRES CONFIRMATION. "
        "Argument: 'name' (app name). "
        "Use for: 'close safari', 'quit chrome', 'kill spotify'"
    )
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult(success=False, output="Missing app 'name'")
        try:
            if IS_WINDOWS:
                exe = name.strip()
                if not exe.lower().endswith(".exe"):
                    exe += ".exe"
                subprocess.run(
                    ["taskkill", "/IM", exe, "/T", "/F"],
                    check=True, capture_output=True, timeout=8,
                )
                return ToolResult(success=True, output=f"Quit {name}")

            if IS_MAC:
                script = f'tell application "{name}" to quit'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True, capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output=f"Quit {name}")

            subprocess.run(["pkill", "-f", name], check=True, capture_output=True, timeout=5)
            return ToolResult(success=True, output=f"Quit {name}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to quit {name}: {e}")


class MinimizeWindowsTool(Tool):
    name = "minimize_windows"
    description = (
        "Minimize all windows (show desktop). "
        "Use for: 'show desktop', 'minimize everything', 'clear screen'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            if IS_WINDOWS:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        "(New-Object -ComObject Shell.Application).ToggleDesktop()",
                    ],
                    check=True, capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output="Windows minimized — showing desktop.")

            if IS_MAC:
                subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to key code 99 using {command down}'],
                    check=True, capture_output=True, timeout=3,
                )
                return ToolResult(success=True, output="Windows minimized — showing desktop.")

            return ToolResult(success=False, output="Show desktop is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class SwitchAppTool(Tool):
    name = "switch_to_app"
    description = (
        "Switch to (bring to front) a specific running app. "
        "Argument: 'name'. "
        "Use for: 'switch to chrome', 'go to terminal', 'bring up vscode'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult(success=False, output="Missing app 'name'")

        # Resolve common names
        name_map = {
            "chrome": "Google Chrome", "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code", "code": "Visual Studio Code",
        }
        resolved = name_map.get(name.lower(), name)

        try:
            if IS_WINDOWS:
                safe = resolved.replace("'", "''")
                script = (
                    "$ws = New-Object -ComObject WScript.Shell; "
                    f"if ($ws.AppActivate('{safe}')) {{ exit 0 }} else {{ exit 1 }}"
                )
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", script],
                    capture_output=True, timeout=5,
                )
                if result.returncode == 0:
                    return ToolResult(success=True, output=f"Switched to {resolved}")
                return ToolResult(success=False, output=f"Could not focus {resolved}")

            if IS_MAC:
                script = f'tell application "{resolved}" to activate'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True, capture_output=True, timeout=5,
                )
                return ToolResult(success=True, output=f"Switched to {resolved}")

            return ToolResult(success=False, output="Switch app is not implemented for this OS.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


# ── Register ─────────────────────────────────────────────────────────────
for _cls in [
    CalculatorTool, SystemInfoTool, ActiveWindowTool,
    BrightnessControlTool,
    SleepMacTool, LockScreenTool, EmptyTrashTool,
    ToggleDarkModeTool, DoNotDisturbTool,
    WordCountTool, ListRunningAppsTool,
    QuitAppTool, MinimizeWindowsTool, SwitchAppTool,
]:
    register_tool(_cls())
