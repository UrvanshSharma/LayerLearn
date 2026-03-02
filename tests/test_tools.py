"""
Tests — Tool Registry, Safety, Intent Detection, and Smart Resolver (36 tools)
"""

import pytest
from core.tools import all_tools, get_tool, tool_schemas
from core.safety import parse_confirmation, format_confirmation_prompt
from core.agent import detect_intent, _expand_abbreviations


class TestToolRegistry:
    def test_minimum_tools_registered(self):
        tools = all_tools()
        names = {t.name for t in tools}
        expected = {
            # Screen/Vision (5)
            "capture_screen", "screen_question", "analyze_code", "generate_code",
            "read_screen_text",
            # Clipboard (2)
            "read_clipboard", "copy_to_clipboard",
            # Files (2)
            "open_file", "write_file",
            # System (6)
            "run_command", "open_app", "open_url", "search_web",
            "type_text", "key_press",
            # Git (2)
            "git_diff", "git_status",
            # Utility (8)
            "set_volume", "get_time", "send_notification",
            "calculator", "system_info", "active_window",
            "toggle_dark_mode", "list_running_apps",
            # App control (3)
            "quit_app", "minimize_windows", "switch_to_app",
            # Communication (1)
            "draft_email",
            # Other (1)
            "open_website_in_chrome",
        }
        missing = expected - names
        assert not missing, f"Missing tools: {missing}"
        assert len(tools) >= 36, f"Expected 36+ tools, got {len(tools)}"

    def test_get_tool(self):
        for name in ["open_file", "capture_screen", "open_app", "calculator",
                      "system_info", "toggle_dark_mode", "quit_app", "switch_to_app"]:
            assert get_tool(name) is not None, f"Tool {name} not found"

    def test_unknown_tool(self):
        assert get_tool("nonexistent") is None

    def test_schemas_have_required_fields(self):
        for s in tool_schemas():
            assert "name" in s
            assert "description" in s
            assert "requires_confirmation" in s

    def test_destructive_tools_require_confirmation(self):
        destructive = {"write_file", "run_command", "draft_email", "type_text",
                       "key_press", "sleep_mac", "lock_screen", "empty_trash", "quit_app"}
        for name in destructive:
            tool = get_tool(name)
            assert tool is not None, f"Tool {name} not registered"
            assert tool.requires_confirmation, f"{name} should require confirmation"

    def test_safe_tools_no_confirmation(self):
        safe = {"capture_screen", "open_file", "git_diff", "read_clipboard",
                "open_app", "open_url", "search_web", "get_time", "set_volume",
                "calculator", "system_info", "active_window", "toggle_dark_mode",
                "list_running_apps", "minimize_windows", "switch_to_app"}
        for name in safe:
            tool = get_tool(name)
            assert tool is not None, f"Tool {name} not registered"
            assert not tool.requires_confirmation, f"{name} should NOT require confirmation"


class TestSafety:
    @pytest.mark.parametrize("response", ["yes", "yeah", "yep", "sure", "ok", "do it", "go ahead", "y", "proceed"])
    def test_affirmative(self, response):
        assert parse_confirmation(response) is True

    @pytest.mark.parametrize("response", ["no", "nope", "nah", "stop", "cancel", "abort", "n"])
    def test_negative(self, response):
        assert parse_confirmation(response) is False

    def test_confirmation_prompt_write(self):
        prompt = format_confirmation_prompt("write_file", {"path": "/tmp/x.py"})
        assert "write" in prompt.lower()

    def test_confirmation_prompt_command(self):
        prompt = format_confirmation_prompt("run_command", {"command": "ls"})
        assert "ls" in prompt

    def test_confirmation_prompt_type(self):
        prompt = format_confirmation_prompt("type_text", {"text": "hello"})
        assert "hello" in prompt


class TestIntentDetection:
    """Test that intent detection catches inputs correctly."""

    def test_screen(self):
        assert detect_intent("what's on my screen")["tool"] == "capture_screen"
        assert detect_intent("look at screen")["tool"] == "capture_screen"
        assert detect_intent("look at this")["tool"] == "capture_screen"
        assert detect_intent("A serious problem on the screen.")["tool"] == "analyze_code"
        assert detect_intent("fix this issue on this screen")["tool"] == "analyze_code"
        assert detect_intent("can you do this problem?")["tool"] == "analyze_code"

    def test_time(self):
        assert detect_intent("what time is it")["tool"] == "get_time"

    def test_search(self):
        r = detect_intent("search for python tutorials")
        assert r["tool"] == "search_web"
        assert r["args"]["query"] == "python tutorials"

    def test_volume(self):
        assert detect_intent("set volume to 50")["tool"] == "set_volume"
        assert detect_intent("mute")["tool"] == "set_volume"

    def test_calculator(self):
        r = detect_intent("calculate 5+3")
        assert r["tool"] == "calculator"
        assert r["args"]["expression"] == "5+3"

    def test_system_info(self):
        assert detect_intent("battery")["tool"] == "system_info"
        assert detect_intent("how much ram")["tool"] == "system_info"

    def test_dark_mode(self):
        assert detect_intent("toggle dark mode")["tool"] == "toggle_dark_mode"

    def test_running_apps(self):
        assert detect_intent("what apps are running")["tool"] == "list_running_apps"

    def test_quit_app(self):
        r = detect_intent("quit safari")
        assert r["tool"] == "quit_app"
        assert r["args"]["name"] == "safari"

    def test_switch_app(self):
        r = detect_intent("switch to chrome")
        assert r["tool"] == "switch_to_app"
        assert r["args"]["name"] == "chrome"

    def test_smart_open(self):
        r = detect_intent("open youtube")
        assert "_smart_open" in r
        assert r["_smart_open"] == "youtube"

    def test_open_with_browser(self):
        r = detect_intent("open whatsapp in chrome")
        assert r["tool"] == "open_url"

    def test_greeting_no_match(self):
        assert detect_intent("hello") is None
        assert detect_intent("how are you") is None


class TestAbbreviations:
    """Test abbreviation expansion."""

    def test_youtube(self):
        assert _expand_abbreviations("open yt") == "open youtube"

    def test_whatsapp_typo(self):
        assert _expand_abbreviations("open whtasapp") == "open whatsapp"

    def test_instagram(self):
        assert _expand_abbreviations("open insta") == "open instagram"

    def test_facebook(self):
        assert _expand_abbreviations("open fb") == "open facebook"

    def test_vscode(self):
        assert _expand_abbreviations("open vs") == "open vscode"

    def test_no_expansion(self):
        assert _expand_abbreviations("hello world") == "hello world"


class TestOpenFileTool:
    def test_read_existing(self):
        result = get_tool("open_file").execute(path="requirements.txt")
        assert result.success is True
        assert "ollama" in result.output

    def test_read_nonexistent(self):
        result = get_tool("open_file").execute(path="/nonexistent/xyz.py")
        assert result.success is False

    def test_missing_path(self):
        result = get_tool("open_file").execute()
        assert result.success is False


class TestGetTimeTool:
    def test_returns_time(self):
        result = get_tool("get_time").execute()
        assert result.success is True
        assert ":" in result.output or "at" in result.output


class TestCalculatorTool:
    def test_basic_math(self):
        result = get_tool("calculator").execute(expression="2 + 3")
        assert result.success is True
        assert "5" in result.output

    def test_complex_math(self):
        result = get_tool("calculator").execute(expression="sqrt(144)")
        assert result.success is True
        assert "12" in result.output

    def test_invalid(self):
        result = get_tool("calculator").execute(expression="hello")
        assert result.success is False


class TestSystemInfoTool:
    def test_returns_info(self):
        result = get_tool("system_info").execute()
        assert result.success is True
        assert "CPU" in result.output or "RAM" in result.output
