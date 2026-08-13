from __future__ import annotations

from collections.abc import Collection
from typing import Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionPlan, ExecutionStep


@runtime_checkable
class Scheduler(Protocol):
    """Contract for determining which execution steps are ready."""

    def get_ready_steps(
        self,
        plan: ExecutionPlan,
        completed_steps: Collection[str],
    ) -> tuple[ExecutionStep, ...]:
        ...