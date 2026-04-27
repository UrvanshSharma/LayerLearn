"""
Context Memory — Screen Context Cache
=======================================
Stores the last screen analysis result so follow-up questions
("what was that error?", "explain the code you just saw")
work without re-capturing the screen.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class ScreenContext:
    """Cached screen analysis result."""
    description: str
    active_app: str
    timestamp: float = field(default_factory=time.time)

    @property
    def age_secs(self) -> float:
        return time.time() - self.timestamp

    @property
    def is_fresh(self) -> bool:
        """Context is fresh if less than 60 seconds old."""
        return self.age_secs < 60.0

    def summary(self) -> str:
        """Short summary for context injection."""
        lines = self.description.strip().split("\n")
        first_lines = "\n".join(lines[:5])
        return f"[Recent screen ({self.active_app}, {self.age_secs:.0f}s ago)]: {first_lines}"


class ContextMemory:
    """
    Manages contextual memory beyond conversation history.
    Stores screen captures, user preferences, recent actions.
    """

    def __init__(self) -> None:
        self._last_screen: Optional[ScreenContext] = None
        self._recent_tools: list[str] = []  # last N tool calls
        self._max_recent = 10

    @property
    def last_screen(self) -> Optional[ScreenContext]:
        """Get last screen analysis if it's still fresh."""
        if self._last_screen and self._last_screen.is_fresh:
            return self._last_screen
        return None

    def store_screen(self, description: str, active_app: str = "") -> None:
        """Cache a screen analysis result."""
        self._last_screen = ScreenContext(
            description=description,
            active_app=active_app,
        )
        log.debug("Cached screen context: {} chars, app={}", len(description), active_app)

    def record_tool(self, tool_name: str) -> None:
        """Record a tool call for context."""
        self._recent_tools.append(tool_name)
        if len(self._recent_tools) > self._max_recent:
            self._recent_tools = self._recent_tools[-self._max_recent:]

    @property
    def recent_tools(self) -> list[str]:
        return list(self._recent_tools)

    def clear(self) -> None:
        self._last_screen = None
        self._recent_tools.clear()

    def get_context_injection(self) -> str:
        """
        Build context string to inject into LLM calls.
        Only injects if there's relevant recent context.
        """
        parts = []
        if self._last_screen and self._last_screen.is_fresh:
            parts.append(self._last_screen.summary())
        if self._recent_tools:
            parts.append(f"[Recent tools: {', '.join(self._recent_tools[-5:])}]")
        return "\n".join(parts)
