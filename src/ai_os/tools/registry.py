from __future__ import annotations

from typing import Protocol, runtime_checkable

from .tool import Tool


@runtime_checkable
class ToolRegistry(Protocol):
    """Contract for Tool identity/capability discovery."""

    def register(self, tool: Tool) -> None:
        ...

    def resolve(self, tool_id: str) -> Tool | None:
        ...

    def resolve_capability(
        self,
        capability: str,
    ) -> tuple[Tool, ...]:
        ...

    def contains(self, tool_id: str) -> bool:
        ...

    def list_tools(self) -> tuple[Tool, ...]:
        ...

    def freeze(self) -> None:
        ...
