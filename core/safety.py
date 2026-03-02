"""
Safety Layer
============
Confirmation flow for destructive actions + audit log.
"""

from __future__ import annotations

import json
from datetime import datetime

from config import settings, LOGS_DIR
from core.logger import get_logger

log = get_logger(__name__)

_AUDIT_LOG = LOGS_DIR / "safety_audit.jsonl"


def requires_confirmation(tool) -> bool:
    return getattr(tool, "requires_confirmation", False) and settings.agent.confirm_destructive


def format_confirmation_prompt(tool_name: str, args: dict) -> str:
    """Human-readable confirmation prompt."""
    summaries = {
        "write_file": lambda a: f"write to file '{a.get('path', '?')}'",
        "run_command": lambda a: f"run the command: {a.get('command', '?')}",
        "draft_email": lambda a: f"draft an email to {a.get('to', '?')}",
        "type_text": lambda a: f"type the text: \"{a.get('text', '?')[:60]}\"",
        "key_press": lambda a: f"press the keys: {a.get('keys', '?')}",
    }

    desc_fn = summaries.get(tool_name, lambda a: f"execute {tool_name}")
    return f"⚠️  I'm about to {desc_fn(args)}. Should I go ahead? Say yes or no."


def parse_confirmation(response: str) -> bool:
    """Parse yes/no from voice or text input."""
    r = response.strip().lower()
    yes_words = {"yes", "yeah", "yep", "sure", "ok", "okay", "do it",
                 "go ahead", "confirm", "y", "go", "proceed", "affirmative", "absolutely"}
    no_words = {"no", "nope", "nah", "stop", "cancel", "abort", "don't", "n", "deny", "negative"}

    if r in yes_words:
        return True
    if r in no_words:
        return False
    for w in yes_words:
        if w in r:
            return True
    return False


def log_audit(tool_name: str, args: dict, confirmed: bool, user_response: str) -> None:
    entry = {
        "ts": datetime.now().isoformat(),
        "tool": tool_name,
        "args": args,
        "ok": confirmed,
        "said": user_response,
    }
    try:
        with open(_AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log.error("Audit log write failed: {}", e)

    status = "CONFIRMED ✓" if confirmed else "DENIED ✗"
    log.info("🔒 {} — {} (said: '{}')", tool_name, status, user_response)
