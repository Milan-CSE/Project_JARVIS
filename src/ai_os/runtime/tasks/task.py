from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionStep


@runtime_checkable
class Task(Protocol):
    """Contract for a Runtime task."""

    @property
    def capability(self) -> str:
        ...

    def execute(
        self,
        step: ExecutionStep,
    ) -> Any:
        ...