from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Generic, Mapping, TypeVar

from ai_os.runtime.cancellation import CancellationToken


T = TypeVar("T")


class IntelligenceOperationStatus(str, Enum):
    """Operational outcome of one Intelligence stage."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IntelligenceFailure:
    """Immutable diagnostic information for an operational failure."""

    exception_type: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.exception_type,
            str,
        ):
            raise TypeError(
                "exception_type must be a string"
            )

        if not self.exception_type.strip():
            raise ValueError(
                "exception_type must not be empty"
            )

        if not isinstance(
            self.message,
            str,
        ):
            raise TypeError(
                "message must be a string"
            )


@dataclass(frozen=True, slots=True)
class IntelligenceOperationResult(Generic[T]):
    """Immutable normalized result of one Intelligence operation."""

    status: IntelligenceOperationStatus
    value: T | None = None
    failure: IntelligenceFailure | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.status,
            IntelligenceOperationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                IntelligenceOperationStatus(self.status),
            )

        if self.failure is not None and not isinstance(
            self.failure,
            IntelligenceFailure,
        ):
            raise TypeError(
                "failure must be an IntelligenceFailure or None"
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
            self.status is IntelligenceOperationStatus.COMPLETED
            and self.failure is not None
        ):
            raise ValueError(
                "completed result cannot contain failure"
            )

        if (
            self.status is IntelligenceOperationStatus.FAILED
            and self.failure is None
        ):
            raise ValueError(
                "failed result must contain failure"
            )

        if (
            self.status is IntelligenceOperationStatus.CANCELLED
            and self.failure is not None
        ):
            raise ValueError(
                "cancelled result must not contain failure"
            )


class IntelligenceFailureBoundary:
    """
    9.5.7 operational boundary.

    It normalizes:
        success
        cancellation
        unexpected failure

    It does not perform semantic decisions and does not execute
    anything itself.
    """

    def run(
        self,
        operation: Callable[[], T],
        cancellation_token: CancellationToken | None = None,
    ) -> IntelligenceOperationResult[T]:
        if not callable(operation):
            raise TypeError(
                "operation must be callable"
            )

        if cancellation_token is not None and not isinstance(
            cancellation_token,
            CancellationToken,
        ):
            raise TypeError(
                "cancellation_token must be a CancellationToken or None"
            )

        if (
            cancellation_token is not None
            and cancellation_token.is_cancelled
        ):
            return IntelligenceOperationResult(
                status=IntelligenceOperationStatus.CANCELLED,
            )

        try:
            value = operation()

        except Exception as exc:
            if (
                cancellation_token is not None
                and cancellation_token.is_cancelled
            ):
                return IntelligenceOperationResult(
                    status=IntelligenceOperationStatus.CANCELLED,
                )

            return IntelligenceOperationResult(
                status=IntelligenceOperationStatus.FAILED,
                failure=IntelligenceFailure(
                    exception_type=type(exc).__name__,
                    message=str(exc),
                ),
            )

        return IntelligenceOperationResult(
            status=IntelligenceOperationStatus.COMPLETED,
            value=value,
        )