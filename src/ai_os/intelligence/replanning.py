from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from ai_os.runtime.contracts import ExecutionPlan


class ReplanningStatus(str, Enum):
    REPLANNED = "replanned"
    LIMIT_REACHED = "limit_reached"


@dataclass(frozen=True, slots=True)
class ReplanRequest:
    """Explicit request to produce one bounded replacement plan."""

    reason: str
    attempt: int
    max_attempts: int
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str):
            raise TypeError(
                "reason must be a string"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty or whitespace"
            )

        if isinstance(self.attempt, bool) or not isinstance(
            self.attempt,
            int,
        ):
            raise TypeError(
                "attempt must be an int"
            )

        if self.attempt < 1:
            raise ValueError(
                "attempt must be >= 1"
            )

        if isinstance(
            self.max_attempts,
            bool,
        ) or not isinstance(
            self.max_attempts,
            int,
        ):
            raise TypeError(
                "max_attempts must be an int"
            )

        if self.max_attempts < 1:
            raise ValueError(
                "max_attempts must be >= 1"
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
class ReplannerContract(Protocol):
    """9.8 contract for producing one replacement ExecutionPlan."""

    def replan(
        self,
        current_plan: ExecutionPlan,
        request: ReplanRequest,
    ) -> ExecutionPlan:
        ...


@dataclass(frozen=True, slots=True)
class ReplanningResult:
    """Immutable result of one bounded replanning attempt."""

    status: ReplanningStatus
    current_plan: ExecutionPlan
    replacement_plan: ExecutionPlan | None = None
    request: ReplanRequest | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            ReplanningStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ReplanningStatus(self.status),
            )

        if not isinstance(
            self.current_plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "current_plan must be an ExecutionPlan"
            )

        if self.replacement_plan is not None and not isinstance(
            self.replacement_plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "replacement_plan must be an ExecutionPlan or None"
            )

        if self.request is not None and not isinstance(
            self.request,
            ReplanRequest,
        ):
            raise TypeError(
                "request must be a ReplanRequest or None"
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

        if (
            self.status is ReplanningStatus.REPLANNED
            and self.replacement_plan is None
        ):
            raise ValueError(
                "REPLANNED result requires a replacement_plan"
            )

        if (
            self.status is ReplanningStatus.LIMIT_REACHED
            and self.replacement_plan is not None
        ):
            raise ValueError(
                "LIMIT_REACHED cannot contain a replacement_plan"
            )


class BoundedReplanningPipeline:
    """
    9.8 bounded replanning boundary.

        Current ExecutionPlan
                +
          ReplanRequest
                ↓
        ReplannerContract
                ↓
        Replacement ExecutionPlan

    The replacement must be validated by 9.6 before execution.
    """

    def __init__(
        self,
        replanner: ReplannerContract,
    ) -> None:
        if not isinstance(
            replanner,
            ReplannerContract,
        ):
            raise TypeError(
                "replanner must implement ReplannerContract"
            )

        self._replanner = replanner

    def run(
        self,
        current_plan: ExecutionPlan,
        request: ReplanRequest,
    ) -> ReplanningResult:
        if not isinstance(
            current_plan,
            ExecutionPlan,
        ):
            raise TypeError(
                "current_plan must be an ExecutionPlan"
            )

        if not isinstance(
            request,
            ReplanRequest,
        ):
            raise TypeError(
                "request must be a ReplanRequest"
            )

        if request.attempt > request.max_attempts:
            return ReplanningResult(
                status=ReplanningStatus.LIMIT_REACHED,
                current_plan=current_plan,
                request=request,
                metadata={
                    "stage": "replanning",
                    "reason": "max_attempts_reached",
                },
            )

        replacement = self._replanner.replan(
            current_plan,
            request,
        )

        if not isinstance(
            replacement,
            ExecutionPlan,
        ):
            raise TypeError(
                "replanner must return an ExecutionPlan"
            )

        if replacement is current_plan:
            raise ValueError(
                "replanner must return a new ExecutionPlan object"
            )

        if replacement.plan_id == current_plan.plan_id:
            raise ValueError(
                "replacement plan must have a different plan_id"
            )

        return ReplanningResult(
            status=ReplanningStatus.REPLANNED,
            current_plan=current_plan,
            replacement_plan=replacement,
            request=request,
            metadata={
                "stage": "replanning",
                "attempt": request.attempt,
            },
        )