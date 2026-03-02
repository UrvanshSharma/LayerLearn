"""
Agent Memory
============
Short-term conversation memory + current task state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from config import settings


@dataclass
class Turn:
    role: str          # "user" | "assistant" | "tool"
    content: str
    tool_name: Optional[str] = None
    screenshot_path: Optional[str] = None


@dataclass
class AgentMemory:
    """Holds the rolling conversation context and current task state."""

    turns: list[Turn] = field(default_factory=list)
    current_task: Optional[str] = None
    last_screenshot_path: Optional[str] = None
    last_screen_analysis: Optional[str] = None

    # ── Helpers ──────────────────────────────────────────────────────────

    def add_user(self, content: str, screenshot_path: str | None = None) -> None:
        self.turns.append(Turn(role="user", content=content, screenshot_path=screenshot_path))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self.turns.append(Turn(role="assistant", content=content))
        self._trim()

    def add_tool(self, tool_name: str, result: str) -> None:
        self.turns.append(Turn(role="tool", content=result, tool_name=tool_name))
        self._trim()

    def to_messages(self) -> list[dict]:
        """Convert to Ollama-compatible message list."""
        msgs: list[dict] = []
        for t in self.turns:
            if t.role == "tool":
                msgs.append({"role": "assistant", "content": f"[Tool: {t.tool_name}] {t.content}"})
            else:
                msgs.append({"role": t.role, "content": t.content})
        return msgs

    def clear(self) -> None:
        self.turns.clear()
        self.current_task = None
        self.last_screenshot_path = None
        self.last_screen_analysis = None

    def _trim(self) -> None:
        max_turns = settings.agent.max_memory_turns
        if len(self.turns) > max_turns:
            self.turns = self.turns[-max_turns:]
