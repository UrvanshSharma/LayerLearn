"""
Tool System — Base + Registry
==============================
Every agent tool inherits from `Tool` and registers itself via the registry.
Tools that can cause side-effects must set `requires_confirmation = True`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolResult:
    """Standardised return value from every tool execution."""
    success: bool
    output: str
    data: Any = None  # optional structured data


class Tool(ABC):
    """Base class for all agent tools."""

    name: str = ""
    description: str = ""
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Run the tool with the given arguments."""
        ...

    def to_schema(self) -> dict:
        """Return a JSON-serialisable description for the LLM system prompt."""
        return {
            "name": self.name,
            "description": self.description,
            "requires_confirmation": self.requires_confirmation,
        }


# ── Global Registry ─────────────────────────────────────────────────────

_registry: dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    _registry[tool.name] = tool


def get_tool(name: str) -> Optional[Tool]:
    return _registry.get(name)


def all_tools() -> list[Tool]:
    return list(_registry.values())


def tool_schemas() -> list[dict]:
    return [t.to_schema() for t in _registry.values()]


def _auto_register() -> None:
    """Import submodules so their tools get registered at import time."""
    from core.tools import screen_tools   # noqa: F401
    from core.tools import file_tools     # noqa: F401
    from core.tools import system_tools   # noqa: F401
    from core.tools import communication_tools  # noqa: F401
    from core.tools import utility_tools  # noqa: F401


_auto_register()
