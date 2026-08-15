from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.runtime.contracts import (
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
)


class ResultInterpretationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True, slots=True)
class ResultInterpretation:
    """Immutable semantic interpretation of execution results."""

    status: ResultInterpretationStatus

    total_steps: int
    completed_steps: int
    failed_steps: int
    cancelled_steps: int
    pending_steps: int
    missing_steps: tuple[str, ...]

    replan_recommended: bool

    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ResultInterpretationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ResultInterpretationStatus(self.status),
            )

        integer_fields = (
            "total_steps",
            "completed_steps",
            "failed_steps",
            "cancelled_steps",
            "pending_steps",
        )

        for name in integer_fields:
            value = getattr(self, name)

            if isinstance(value, bool) or not isinstance(
                value,
                int,
            ):
                raise TypeError(
                    f"{name} must be an int"
                )

            if value < 0:
                raise ValueError(
                    f"{name} must be >= 0"
                )

        if not isinstance(
            self.missing_steps,
            tuple,
        ):
            object.__setattr__(
                self,
                "missing_steps",
                tuple(self.missing_steps),
            )

        if not all(
            isinstance(step_id, str)
            and step_id.strip()
            for step_id in self.missing_steps
        ):
            raise TypeError(
                "missing_steps must contain "
                "non-empty strings"
            )

        if not isinstance(
            self.replan_recommended,
            bool,
        ):
            raise TypeError(
                "replan_recommended must be a bool"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class ResultInterpretationResult:
    """Immutable output of the 9.9 interpretation boundary."""

    plan: ExecutionPlan
    results: tuple[ExecutionResult, ...]
    interpretation: ResultInterpretation

    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if not isinstance(
            self.results,
            tuple,
        ):
            object.__setattr__(
                self,
                "results",
                tuple(self.results),
            )

        if not all(
            isinstance(
                result,
                ExecutionResult,
            )
            for result in self.results
        ):
            raise TypeError(
                "results must contain only "
                "ExecutionResult instances"
            )

        if not isinstance(
            self.interpretation,
            ResultInterpretation,
        ):
            raise TypeError(
                "interpretation must be a ResultInterpretation"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@runtime_checkable
class ResultInterpreterContract(Protocol):
    """9.9 contract for interpreting execution results."""

    def interpret(
        self,
        plan: ExecutionPlan,
        results: Iterable[ExecutionResult],
    ) -> ResultInterpretation:
        ...


class DefaultResultInterpreter:
    """
    Deterministic 9.9 result interpreter.

    This class only interprets results. It never executes,
    retries, replans, or mutates execution state.
    """

    def interpret(
        self,
        plan: ExecutionPlan,
        results: Iterable[ExecutionResult],
    ) -> ResultInterpretation:
        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        if isinstance(
            results,
            (str, bytes),
        ):
            raise TypeError(
                "results must be an iterable of "
                "ExecutionResult objects"
            )

        try:
            normalized_results = tuple(results)
        except TypeError as exc:
            raise TypeError(
                "results must be an iterable"
            ) from exc

        if not all(
            isinstance(
                result,
                ExecutionResult,
            )
            for result in normalized_results
        ):
            raise TypeError(
                "results must contain only "
                "ExecutionResult instances"
            )

        known_step_ids = {
            step.step_id
            for step in plan.steps
        }

        seen_step_ids: set[str] = set()

        for result in normalized_results:
            if result.plan_id != plan.plan_id:
                raise ValueError(
                    "execution result plan_id does not "
                    "match the supplied plan"
                )

            if result.step_id not in known_step_ids:
                raise ValueError(
                    "execution result references an "
                    "unknown plan step"
                )

            if result.step_id in seen_step_ids:
                raise ValueError(
                    "duplicate execution result for step: "
                    + result.step_id
                )

            seen_step_ids.add(
                result.step_id
            )

        completed_steps = sum(
            result.status is ExecutionStatus.COMPLETED
            for result in normalized_results
        )

        failed_steps = sum(
            result.status is ExecutionStatus.FAILED
            for result in normalized_results
        )

        cancelled_steps = sum(
            result.status is ExecutionStatus.CANCELLED
            for result in normalized_results
        )

        pending_steps = sum(
            result.status in {
                ExecutionStatus.PENDING,
                ExecutionStatus.RUNNING,
            }
            for result in normalized_results
        )

        missing_steps = tuple(
            step.step_id
            for step in plan.steps
            if step.step_id not in seen_step_ids
        )

        if failed_steps > 0:
            status = ResultInterpretationStatus.FAILED
            replan_recommended = True

        elif cancelled_steps > 0:
            status = ResultInterpretationStatus.CANCELLED
            replan_recommended = False

        elif pending_steps > 0 or missing_steps:
            status = ResultInterpretationStatus.INCOMPLETE
            replan_recommended = False

        elif completed_steps == len(plan.steps):
            status = ResultInterpretationStatus.COMPLETED
            replan_recommended = False

        else:
            status = ResultInterpretationStatus.INCOMPLETE
            replan_recommended = False

        return ResultInterpretation(
            status=status,
            total_steps=len(plan.steps),
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            cancelled_steps=cancelled_steps,
            pending_steps=pending_steps,
            missing_steps=missing_steps,
            replan_recommended=replan_recommended,
            metadata={
                "stage": "result_interpretation",
                "result_count": len(
                    normalized_results
                ),
            },
        )


class ResultInterpretationPipeline:
    """
    9.9 boundary:

        ExecutionPlan + ExecutionResult(s)
                      ↓
              ResultInterpreterContract
                      ↓
                Interpretation
    """

    def __init__(
        self,
        interpreter: ResultInterpreterContract | None = None,
    ) -> None:
        if interpreter is None:
            interpreter = DefaultResultInterpreter()

        if not isinstance(
            interpreter,
            ResultInterpreterContract,
        ):
            raise TypeError(
                "interpreter must implement "
                "ResultInterpreterContract"
            )

        self._interpreter = interpreter

    def run(
        self,
        plan: ExecutionPlan,
        results: Iterable[ExecutionResult],
    ) -> ResultInterpretationResult:
        if not isinstance(
            plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "plan must be an ExecutionPlan"
            )

        interpreted = self._interpreter.interpret(
            plan,
            results,
        )

        if not isinstance(
            interpreted,
            ResultInterpretation,
        ):
            raise TypeError(
                "interpreter must return "
                "ResultInterpretation"
            )

        normalized_results = tuple(results)

        return ResultInterpretationResult(
            plan=plan,
            results=normalized_results,
            interpretation=interpreted,
            metadata={
                "stage": "result_interpretation",
            },
        )