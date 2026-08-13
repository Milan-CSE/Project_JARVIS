from __future__ import annotations

from collections.abc import Collection

from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionStep,
)
from ai_os.runtime.contracts.errors import InvalidPlanError
from ai_os.runtime.scheduler import Scheduler


class DependencyScheduler:
    """Scheduler implementation based on ExecutionStep dependencies."""

    def get_ready_steps(
        self,
        plan: ExecutionPlan,
        completed_steps: Collection[str],
    ) -> tuple[ExecutionStep, ...]:

        if not isinstance(plan, ExecutionPlan):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if not isinstance(completed_steps, Collection):
            raise TypeError(
                "completed_steps must be a collection of strings"
            )

        if any(
            not isinstance(step_id, str)
            for step_id in completed_steps
        ):
            raise TypeError(
                "completed_steps must contain only strings"
            )

        completed = set(completed_steps)

        step_ids = {
            step.step_id
            for step in plan.steps
        }

        for step in plan.steps:
            for dependency in step.dependencies:
                if dependency not in step_ids:
                    raise InvalidPlanError(
                        f"unknown dependency '{dependency}' "
                        f"for step '{step.step_id}'"
                    )

        ready: list[ExecutionStep] = []

        for step in plan.steps:
            if step.step_id in completed:
                continue

            if all(
                dependency in completed
                for dependency in step.dependencies
            ):
                ready.append(step)

        return tuple(ready)