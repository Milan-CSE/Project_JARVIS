from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.tasks.task import Task

from .tool import Tool


@runtime_checkable
class ToolAdapter(Protocol):
    """Contract for adapting one Tool capability into one Runtime Task."""

    @property
    def tool_id(self) -> str:
        ...

    @property
    def capability(self) -> str:
        ...

    def adapt(self) -> Task:
        ...


class DefaultToolAdapter:
    """Validated base implementation for a single Tool-to-Task adapter.

    Subclasses provide the concrete Task through ``_build_task``.
    This class never executes the Tool, invokes Runtime, authorizes
    permissions, or manages lifecycle.
    """

    def __init__(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise TypeError("tool must implement Tool protocol")

        tool_id = tool.tool_id
        capability = tool.capability

        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError("tool.tool_id must be a non-empty string")

        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("tool.capability must be a non-empty string")

        self._tool = tool
        self._tool_id = tool_id
        self._capability = capability

    @property
    def tool_id(self) -> str:
        return self._tool_id

    @property
    def capability(self) -> str:
        return self._capability

    @property
    def tool(self) -> Tool:
        """The exact Tool this adapter is bound to."""
        return self._tool

    def adapt(self) -> Task:
        task = self._build_task()

        if not isinstance(task, Task):
            raise TypeError("adapter must produce a Task")

        task_capability = task.capability

        if task_capability != self.capability:
            raise ValueError(
                "adapted Task capability must match Tool capability"
            )

        return task

    def _build_task(self) -> Task:
        raise NotImplementedError(
            "concrete ToolAdapters must implement _build_task"
        )
