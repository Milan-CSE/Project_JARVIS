from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionStep


@runtime_checkable
class TaskExecutor(Protocol):
    """Contract for executing a single Runtime task step."""

    def execute_step(
        self,
        step: ExecutionStep,
    ) -> Any:
        ...