"""
Utility Tools
==============
Calculator, translate, timer, system info, explain, summarize.
"""

import subprocess
import platform
import psutil
from datetime import datetime

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

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
            info.append(f"OS: macOS {platform.mac_ver()[0]}")
            info.append(f"CPU: {psutil.cpu_percent()}% usage, {psutil.cpu_count()} cores")
            mem = psutil.virtual_memory()
            info.append(f"RAM: {mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB ({mem.percent}%)")
            disk = psutil.disk_usage("/")
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
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=3,
            )
            app_name = result.stdout.strip()
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
            fraction = level / 100.0
            script = f'tell application "System Events" to set value of value indicator 1 of slider 1 of group 1 of window "Displays" of application process "System Preferences" to {fraction}'
            # Use brightness command if available, otherwise AppleScript
            subprocess.run(
                ["osascript", "-e", f'do shell script "brightness {fraction}"'],
                capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output=f"Brightness set to {level}%")
        except Exception:
            return ToolResult(success=True, output=f"Brightness control attempted at {level}%. You may need to install 'brightness' CLI tool.")


class SleepMacTool(Tool):
    name = "sleep_mac"
    description = "Put the Mac to sleep. ⚠️ REQUIRES CONFIRMATION."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to sleep'],
                check=True, capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output="Mac is going to sleep.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class LockScreenTool(Tool):
    name = "lock_screen"
    description = "Lock the screen. ⚠️ REQUIRES CONFIRMATION."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to keystroke "q" using {command down, control down}'],
                check=True, capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output="Screen locked.")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class EmptyTrashTool(Tool):
    name = "empty_trash"
    description = "Empty the Trash. ⚠️ REQUIRES CONFIRMATION (permanent!)."
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        try:
            subprocess.run(
                ["osascript", "-e",
                 'tell application "Finder" to empty the trash'],
                check=True, capture_output=True, timeout=10,
            )
            return ToolResult(success=True, output="Trash emptied.")
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
            subprocess.run(
                ["osascript", "-e",
                 'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'],
                check=True, capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output="Dark mode toggled!")
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
            # Toggle DND using shortcuts
            subprocess.run(
                ["shortcuts", "run", "Toggle Focus"],
                capture_output=True, timeout=5,
            )
            return ToolResult(success=True, output="Do Not Disturb toggled!")
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
            script = '''
            tell application "System Events"
                set appList to name of every application process whose background only is false
                set output to ""
                repeat with appName in appList
                    set output to output & appName & ", "
                end repeat
                return output
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5,
            )
            apps = result.stdout.strip().rstrip(", ")
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
            script = f'tell application "{name}" to quit'
            subprocess.run(
                ["osascript", "-e", script],
                check=True, capture_output=True, timeout=5,
            )
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
            # Cmd+F3 or Cmd+Option+M to minimize
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to key code 99 using {command down}'],
                check=True, capture_output=True, timeout=3,
            )
            return ToolResult(success=True, output="Windows minimized — showing desktop.")
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
            script = f'tell application "{resolved}" to activate'
            subprocess.run(
                ["osascript", "-e", script],
                check=True, capture_output=True, timeout=5,
            )
            return ToolResult(success=True, output=f"Switched to {resolved}")
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
