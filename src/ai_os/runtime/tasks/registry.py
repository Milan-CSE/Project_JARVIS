from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_os.runtime.tasks.task import Task


@runtime_checkable
class TaskRegistry(Protocol):
    """Contract for capability-to-task resolution and lifecycle control."""

    def register(self, task: Task) -> None:
        ...

    def resolve(self, capability: str) -> Task | None:
        ...

    def freeze(self) -> None:
        ...