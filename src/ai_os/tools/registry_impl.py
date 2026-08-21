from __future__ import annotations

from .registry import ToolRegistry
from .tool import Tool


class DuplicateToolError(ValueError):
    """Raised when a Tool ID is already registered."""


class ToolRegistryFrozenError(RuntimeError):
    """Raised when modifying a frozen Tool registry."""


class DefaultToolRegistry:
    """Concrete implementation of the 10.2 Tool Registry contract."""

    def __init__(self) -> None:
        self._tools_by_id: dict[str, Tool] = {}
        self._tools_by_capability: dict[str, list[Tool]] = {}
        self._frozen = False

    def register(self, tool: Tool) -> None:
        if self._frozen:
            raise ToolRegistryFrozenError(
                "tool registry is frozen"
            )

        if not isinstance(tool, Tool):
            raise TypeError(
                "tool must implement Tool protocol"
            )

        tool_id = tool.tool_id
        capability = tool.capability

        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        if not isinstance(capability, str) or not capability.strip():
            raise ValueError(
                "tool capability must be a non-empty string"
            )

        if tool_id in self._tools_by_id:
            raise DuplicateToolError(
                f"tool already registered: {tool_id}"
            )

        self._tools_by_id[tool_id] = tool
        self._tools_by_capability.setdefault(
            capability,
            [],
        ).append(tool)

    def resolve(self, tool_id: str) -> Tool | None:
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        return self._tools_by_id.get(tool_id)

    def resolve_capability(
        self,
        capability: str,
    ) -> tuple[Tool, ...]:
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError(
                "capability must be a non-empty string"
            )

        return tuple(
            self._tools_by_capability.get(capability, ())
        )

    def contains(self, tool_id: str) -> bool:
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        return tool_id in self._tools_by_id

    def list_tools(self) -> tuple[Tool, ...]:
        return tuple(self._tools_by_id.values())

    def freeze(self) -> None:
        self._frozen = True
