"""
File Tools
==========
Read, write, and patch files. Write operations require confirmation.
"""

from pathlib import Path

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)


class OpenFileTool(Tool):
    name = "open_file"
    description = (
        "Read the contents of a file on disk. "
        "Requires a 'path' argument (absolute or relative)."
    )
    requires_confirmation = False

    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        if not path:
            return ToolResult(success=False, output="Missing 'path' argument")

        p = Path(path).expanduser()
        if not p.exists():
            return ToolResult(success=False, output=f"File not found: {p}")
        if not p.is_file():
            return ToolResult(success=False, output=f"Not a file: {p}")

        try:
            content = p.read_text(errors="replace")
            # Truncate very large files
            if len(content) > 10_000:
                content = content[:10_000] + "\n\n… [truncated — file is very large]"
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to read: {e}")


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Write content to a file on disk. ⚠️ DESTRUCTIVE — requires confirmation. "
        "Arguments: 'path' (file path), 'content' (text to write)."
    )
    requires_confirmation = True  # ⚠️

    def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        if not path:
            return ToolResult(success=False, output="Missing 'path' argument")

        p = Path(path).expanduser()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            log.info("Wrote {} bytes → {}", len(content), p)
            return ToolResult(success=True, output=f"File written: {p}")
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to write: {e}")


# ── Register ─────────────────────────────────────────────────────────────
register_tool(OpenFileTool())
register_tool(WriteFileTool())
