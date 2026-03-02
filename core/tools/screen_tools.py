"""
Screen & Vision Tools — General Purpose
=========================================
"""

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)


class CaptureScreenTool(Tool):
    name = "capture_screen"
    description = (
        "Capture a screenshot and describe EVERYTHING on the screen. "
        "Use for: 'what's on my screen', 'look at my screen', 'what do you see', etc."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from core.vision import analyze_screen
        try:
            result = analyze_screen(kwargs.get("prompt"))
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Screen capture failed: {e}")


class ScreenQuestionTool(Tool):
    name = "screen_question"
    description = (
        "Answer a specific question about what's on the screen. "
        "Use for: 'what app is open', 'read the error message', 'what does this say', etc."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from core.vision import analyze_screen_with_question
        question = kwargs.get("question", "What's on the screen?")
        try:
            result = analyze_screen_with_question(question)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class AnalyzeCodeTool(Tool):
    name = "analyze_code"
    description = (
        "Look at code on screen and provide step-by-step help. "
        "Use for: 'help me with this code', 'debug this', 'explain this code', 'I'm stuck'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from core.vision import analyze_code_on_screen
        try:
            result = analyze_code_on_screen(kwargs.get("instruction", "Help me"))
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class GenerateCodeTool(Tool):
    name = "generate_code"
    description = (
        "Look at screen and generate a code fix or patch. "
        "Use for: 'fix this', 'generate code', 'write the fix', 'correct the code'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from core.vision import generate_code_from_screen
        try:
            result = generate_code_from_screen(kwargs.get("instruction", "Fix it"))
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class ReadScreenTextTool(Tool):
    name = "read_screen_text"
    description = (
        "Extract and read all visible text from the screen. "
        "Use for: 'read this', 'what does it say', 'read the text on screen'"
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        from core.vision import read_screen_text
        try:
            result = read_screen_text()
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class ReadClipboardTool(Tool):
    name = "read_clipboard"
    description = "Read the current clipboard contents."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        try:
            import pyperclip
            content = pyperclip.paste()
            return ToolResult(success=True, output=content or "(clipboard empty)")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


class CopyToClipboardTool(Tool):
    name = "copy_to_clipboard"
    description = "Copy text to the clipboard. Argument: 'text'."
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        if not text:
            return ToolResult(success=False, output="Nothing to copy")
        try:
            import pyperclip
            pyperclip.copy(text)
            return ToolResult(success=True, output=f"Copied {len(text)} chars to clipboard")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed: {e}")


# ── Register ─────────────────────────────────────────────────────────────
for _cls in [CaptureScreenTool, ScreenQuestionTool, AnalyzeCodeTool,
             GenerateCodeTool, ReadScreenTextTool, ReadClipboardTool, CopyToClipboardTool]:
    register_tool(_cls())
