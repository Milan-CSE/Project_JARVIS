from __future__ import annotations

from ai_os.runtime.cancellation import CancellationToken
from ai_os.runtime.contracts import (
    ExecutionError,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
)
from ai_os.runtime.scheduler import Scheduler
from ai_os.runtime.tasks.executor import TaskExecutor


class ExecutionStalledError(RuntimeError):
    """Raised when execution cannot make further progress."""


class DefaultRuntimeExecutor:
    """Orchestrates scheduling, task execution, failure and cancellation."""

    def __init__(
        self,
        scheduler: Scheduler,
        task_executor: TaskExecutor,
    ) -> None:
        if not isinstance(scheduler, Scheduler):
            raise TypeError(
                "scheduler must implement Scheduler protocol"
            )

        if not isinstance(task_executor, TaskExecutor):
            raise TypeError(
                "task_executor must implement TaskExecutor protocol"
            )

        self._scheduler = scheduler
        self._task_executor = task_executor

    def execute(
        self,
        plan: ExecutionPlan,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[ExecutionResult, ...]:
        if not isinstance(plan, ExecutionPlan):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if (
            cancellation_token is not None
            and not isinstance(
                cancellation_token,
                CancellationToken,
            )
        ):
            raise TypeError(
                "cancellation_token must implement "
                "CancellationToken protocol"
            )

        results_by_step: dict[str, ExecutionResult] = {}
        completed_steps: set[str] = set()

        while len(results_by_step) < len(plan.steps):
            # Explicit cancellation always wins for work that
            # has not started yet.
            if (
                cancellation_token is not None
                and cancellation_token.is_cancelled
            ):
                self._cancel_all_unfinished(
                    plan,
                    results_by_step,
                    reason="explicit_cancellation",
                )
                break

            # A failed/cancelled dependency makes the dependent
            # step impossible to execute.
            self._propagate_dependency_cancellation(
                plan,
                results_by_step,
            )

            if len(results_by_step) == len(plan.steps):
                break

            ready_steps = self._scheduler.get_ready_steps(
                plan,
                completed_steps,
            )

            executable_steps = tuple(
                step
                for step in ready_steps
                if step.step_id not in results_by_step
            )

            if not executable_steps:
                # Dependency propagation may have made additional
                # steps terminal. Check once more before declaring
                # a genuine stall.
                before = len(results_by_step)

                self._propagate_dependency_cancellation(
                    plan,
                    results_by_step,
                )

                if len(results_by_step) > before:
                    continue

                raise ExecutionStalledError(
                    "execution cannot make further progress"
                )

            for step in executable_steps:
                # Cancellation requested before this step starts:
                # do not execute it.
                if (
                    cancellation_token is not None
                    and cancellation_token.is_cancelled
                ):
                    self._cancel_all_unfinished(
                        plan,
                        results_by_step,
                        reason="explicit_cancellation",
                    )
                    break

                try:
                    output = self._task_executor.execute_step(
                        step
                    )
                except Exception as exc:
                    # A Task-level execution failure becomes a
                    # terminal FAILED result. We intentionally do
                    # not expose arbitrary exception messages.
                    results_by_step[step.step_id] = (
                        ExecutionResult(
                            plan_id=plan.plan_id,
                            step_id=step.step_id,
                            status=ExecutionStatus.FAILED,
                            error=ExecutionError(
                                code="TASK_EXECUTION_FAILED",
                                message="task execution failed",
                                details={
                                    "exception_type": type(
                                        exc
                                    ).__name__,
                                },
                            ),
                        )
                    )

                    # Important:
                    # the failed step is NOT added to
                    # completed_steps.
                    continue

                # Actual Task outcome wins if cancellation was
                # requested while this Task was already running.
                results_by_step[step.step_id] = (
                    ExecutionResult(
                        plan_id=plan.plan_id,
                        step_id=step.step_id,
                        status=ExecutionStatus.COMPLETED,
                        output=output,
                    )
                )

                completed_steps.add(step.step_id)

                # If cancellation arrived while the Task was
                # running, the Task's actual terminal outcome
                # remains COMPLETED. Remaining unstarted work will
                # be cancelled on the next loop.
                if (
                    cancellation_token is not None
                    and cancellation_token.is_cancelled
                ):
                    self._cancel_all_unfinished(
                        plan,
                        results_by_step,
                        reason="explicit_cancellation",
                    )
                    break

        return tuple(
            results_by_step[step.step_id]
            for step in plan.steps
        )

    @staticmethod
    def _propagate_dependency_cancellation(
        plan: ExecutionPlan,
        results_by_step: dict[str, ExecutionResult],
    ) -> None:
        changed = True

        while changed:
            changed = False

            for step in plan.steps:
                if step.step_id in results_by_step:
                    continue

                blocking_dependencies = [
                    dependency
                    for dependency in step.dependencies
                    if (
                        dependency in results_by_step
                        and results_by_step[
                            dependency
                        ].status
                        in (
                            ExecutionStatus.FAILED,
                            ExecutionStatus.CANCELLED,
                        )
                    )
                ]

                if not blocking_dependencies:
                    continue

                dependency_statuses = {
                    results_by_step[
                        dependency
                    ].status
                    for dependency in blocking_dependencies
                }

                reason = (
                    "dependency_failed"
                    if ExecutionStatus.FAILED
                    in dependency_statuses
                    else "dependency_cancelled"
                )

                results_by_step[step.step_id] = (
                    ExecutionResult(
                        plan_id=plan.plan_id,
                        step_id=step.step_id,
                        status=ExecutionStatus.CANCELLED,
                        metadata={
                            "termination_reason": reason,
                            "blocking_dependency_ids": (
                                blocking_dependencies
                            ),
                        },
                    )
                )

                changed = True

    @staticmethod
    def _cancel_all_unfinished(
        plan: ExecutionPlan,
        results_by_step: dict[str, ExecutionResult],
        *,
        reason: str,
    ) -> None:
        for step in plan.steps:
            if step.step_id in results_by_step:
                continue

            results_by_step[step.step_id] = (
                ExecutionResult(
                    plan_id=plan.plan_id,
                    step_id=step.step_id,
                    status=ExecutionStatus.CANCELLED,
                    metadata={
                        "termination_reason": reason,
                    },
                )
            )