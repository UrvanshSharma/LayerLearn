"""
Communication Tools
===================
Draft and send emails/messages. Sending requires confirmation.
"""

from core.tools import Tool, ToolResult, register_tool
from core.logger import get_logger

log = get_logger(__name__)


class DraftEmailTool(Tool):
    name = "draft_email"
    description = (
        "Draft an email. ⚠️ Sending requires confirmation. "
        "Arguments: 'to' (recipient), 'subject', 'body'."
    )
    requires_confirmation = True  # ⚠️

    def execute(self, **kwargs) -> ToolResult:
        to = kwargs.get("to", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")

        if not to:
            return ToolResult(success=False, output="Missing 'to' argument")

        # For now, we draft locally (open in default mail client on macOS)
        import subprocess
        import urllib.parse

        mailto = f"mailto:{to}?"
        params = {}
        if subject:
            params["subject"] = subject
        if body:
            params["body"] = body
        mailto += urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

        try:
            subprocess.run(["open", mailto], check=True)
            preview = f"To: {to}\nSubject: {subject}\n\n{body[:200]}"
            log.info("Email draft opened for: {}", to)
            return ToolResult(
                success=True,
                output=f"Email draft opened in your mail client:\n{preview}",
            )
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to open mail client: {e}")


# ── Register ─────────────────────────────────────────────────────────────
register_tool(DraftEmailTool())
