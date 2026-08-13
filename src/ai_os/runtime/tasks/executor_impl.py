from __future__ import annotations

from typing import Any

from ai_os.runtime.contracts import ExecutionStep
from ai_os.runtime.tasks.registry import TaskRegistry
from ai_os.runtime.tasks.task import Task


class UnknownCapabilityError(LookupError):
    """Raised when no Task is registered for a capability."""


class DefaultTaskExecutor:
    """Concrete executor for a single Runtime task step."""

    def __init__(self, registry: TaskRegistry) -> None:
        if not isinstance(registry, TaskRegistry):
            raise TypeError(
                "registry must implement TaskRegistry protocol"
            )

        self._registry = registry

    def execute_step(
        self,
        step: ExecutionStep,
    ) -> Any:
        if not isinstance(step, ExecutionStep):
            raise TypeError(
                "step must be an ExecutionStep"
            )

        task = self._registry.resolve(
            step.capability
        )

        if task is None:
            raise UnknownCapabilityError(
                f"no Task registered for capability: "
                f"{step.capability}"
            )

        if not isinstance(task, Task):
            raise TypeError(
                "TaskRegistry returned an invalid Task"
            )

        return task.execute(step)