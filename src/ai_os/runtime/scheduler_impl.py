from __future__ import annotations

from collections.abc import Collection

from ai_os.runtime.contracts import ExecutionPlan, ExecutionStep
from ai_os.runtime.scheduler import Scheduler


class DefaultScheduler:
    """Minimal Scheduler implementation.

    Dependency-graph scheduling is intentionally deferred to 8.5.
    """

    def get_ready_steps(
        self,
        plan: ExecutionPlan,
        completed_steps: Collection[str],
    ) -> tuple[ExecutionStep, ...]:
        completed = set(completed_steps)

        return tuple(
            step
            for step in plan.steps
            if step.step_id not in completed
            and all(
                dependency in completed
                for dependency in step.dependencies
            )
        )