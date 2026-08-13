from __future__ import annotations

from ai_os.runtime.tasks.registry import TaskRegistry
from ai_os.runtime.tasks.task import Task


class DuplicateCapabilityError(ValueError):
    """Raised when a capability is already registered."""


class RegistryFrozenError(RuntimeError):
    """Raised when modifying a frozen task registry."""


class DefaultTaskRegistry:
    """Concrete implementation of TaskRegistry."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._frozen = False

    def register(self, task: Task) -> None:
        if self._frozen:
            raise RegistryFrozenError(
                "task registry is frozen"
            )

        if not isinstance(task, Task):
            raise TypeError(
                "task must implement Task protocol"
            )

        capability = task.capability

        if not isinstance(capability, str) or not capability.strip():
            raise ValueError(
                "task capability must be a non-empty string"
            )

        if capability in self._tasks:
            raise DuplicateCapabilityError(
                f"capability already registered: {capability}"
            )

        self._tasks[capability] = task

    def resolve(self, capability: str) -> Task | None:
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError(
                "capability must be a non-empty string"
            )

        return self._tasks.get(capability)

    def freeze(self) -> None:
        self._frozen = True